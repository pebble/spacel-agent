import os
import sys

import click

from spacel.agent import (ApplicationEnvironment, FileWriter, SystemdUnits,
                          InstanceManager)
from spacel.aws import (AwsMeta, ClientCache, CloudFormationSignaller,
                        ElbHealthCheck, ElasticIpBinder, KmsCrypto, TagWriter)
from spacel.log import setup_logging, setup_watchtower
from spacel.model import AgentManifest
from spacel.volumes import VolumeBinder

try:
    from systemd.manager import Manager
except ImportError:  # pragma: no cover
    import mock

    Manager = mock.MagicMock()


@click.group()
def services_cmd():  # pragma: no cover
    pass


@services_cmd.command(help='Bootstrap instance and start services.')
def services():  # pragma: no cover
    start_services()


def start_services():
    setup_logging()
    if not os.path.isdir('/files'):
        try:
            os.mkdir('/files')
        except OSError:  # pragma: no cover
            pass

    # Get context:
    meta = AwsMeta()
    clients = ClientCache(meta.region)
    manifest = AgentManifest(meta.user_data)
    setup_watchtower(clients, manifest)
    cf = CloudFormationSignaller(clients, meta.instance_id)


    if manifest.valid:
        systemd = SystemdUnits(Manager())
        status = process_manifest(clients, meta, systemd, manifest)
        if not status:
            systemd.log_units(manifest)
    else:
        status = False

    cf_status = status and 'SUCCESS' or 'FAILURE'
    cf.notify(manifest, status=cf_status)

    if not status:
        sys.exit(1)


def process_manifest(clients, meta, systemd, manifest):
    # Dependency injection party!
    kms = KmsCrypto(clients)
    app_env = ApplicationEnvironment(clients)
    file_writer = FileWriter(app_env, kms)
    instance = InstanceManager()
    eip = ElasticIpBinder(clients, meta)
    ebs = VolumeBinder(clients, meta)
    elb = ElbHealthCheck(clients, meta)
    tag = TagWriter(clients, meta)

    # Act on manifest:
    tag.update(manifest)
    for volume in manifest.volumes.values():
        ebs.attach(volume)
        # TODO: fail if attaching any volume fails.
    if not eip.assign_from(manifest):
        return False

    file_writer.write_files(manifest)
    if not systemd.start_units(manifest):
        return False

    if not elb.health(manifest):
        return False
    if not instance.health(manifest):
        return False

    return True
