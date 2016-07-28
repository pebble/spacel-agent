import click
import os

from spacel.agent import FileWriter, SystemdUnits, InstanceManager
from spacel.aws import (AwsMeta, ClientCache, CloudFormationSignaller,
                        ElbHealthCheck, ElasticIpBinder)
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
    file_writer = FileWriter()
    systemd = SystemdUnits(Manager())
    instance = InstanceManager()
    eip = ElasticIpBinder(clients, meta)
    cf = CloudFormationSignaller(clients, meta.instance_id)
    ebs = VolumeBinder(clients, meta)
    elb = ElbHealthCheck(clients, meta)

    status = 'SUCCESS'
    manifest = AgentManifest(meta.user_data)

    if manifest.valid:
        # Act on manifest:
        for volume in manifest.volumes.values():
            ebs.attach(volume)
            # TODO: fail if attaching any volume fails.
        if not eip.assign_from(manifest):
            status = 'FAILURE'

        file_writer.write_files(manifest)
        systemd.start_units(manifest)

        if not elb.health(manifest):
            status = 'FAILURE'
        if not instance.health(manifest):
            status = 'FAILURE'
    else:
        status = 'FAILURE'

    cf.notify(manifest, status=status)
