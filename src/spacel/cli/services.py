import click
import os
import sys

from spacel.agent import (ApplicationEnvironment, FileWriter, SystemdUnits,
                          InstanceManager)
from spacel.aws import (AwsMeta, ClientCache, CloudFormationSignaller,
                        ElbHealthCheck, ElasticIpBinder, KmsCrypto, TagWriter)
from spacel.log import setup_logging
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

    # Dependency injection party!
    kms = KmsCrypto(clients)
    app_env = ApplicationEnvironment(clients)
    file_writer = FileWriter(app_env, kms)
    systemd = SystemdUnits(Manager())
    instance = InstanceManager()
    eip = ElasticIpBinder(clients, meta)
    cf = CloudFormationSignaller(clients, meta.instance_id)
    ebs = VolumeBinder(clients, meta)
    elb = ElbHealthCheck(clients, meta)
    tag = TagWriter(clients, meta)

    status = 'SUCCESS'
    manifest = AgentManifest(meta.user_data)

    if manifest.valid:
        # Act on manifest:
        tag.update(manifest)
        for volume in manifest.volumes.values():
            ebs.attach(volume)
            # TODO: fail if attaching any volume fails.
        if not eip.assign_from(manifest):
            status = 'FAILURE'

        file_writer.write_files(manifest)
        if not systemd.start_units(manifest):
            status = 'FAILURE'

        if not elb.health(manifest):
            status = 'FAILURE'
        if not instance.health(manifest):
            status = 'FAILURE'
    else:
        status = 'FAILURE'

    cf.notify(manifest, status=status)

    if status != 'SUCCESS':
        systemd.log_units(manifest)
        sys.exit(1)
