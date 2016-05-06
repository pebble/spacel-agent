import logging
import os

from spacel.aws import (AwsMeta, ClientCache, CloudFormationSignaller,
                        ElbHealthCheck, ElasticIpBinder, VolumeBinder)
from spacel.agent import FileWriter, SystemdUnits
from spacel.model import AgentManifest

try:
    from systemd.manager import Manager
except ImportError:
    import mock

    Manager = mock.MagicMock()


def setup_logging():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')
    logging.getLogger('boto3').setLevel(logging.CRITICAL)
    logging.getLogger('botocore').setLevel(logging.CRITICAL)
    logging.getLogger('spacel').setLevel(logging.DEBUG)


if __name__ == '__main__':
    setup_logging()
    if not os.path.isdir('/files'):
        os.mkdir('/files')

    # Get context:
    meta = AwsMeta()
    clients = ClientCache(meta.region)

    # Dependency injection party!
    file_writer = FileWriter()
    systemd = SystemdUnits(Manager())
    eip = ElasticIpBinder(clients)
    cf = CloudFormationSignaller(clients, meta.instance_id)
    ebs = VolumeBinder(clients, meta)
    elb = ElbHealthCheck(clients, meta)
    status = 'SUCCESS'

    manifest = AgentManifest(meta.instance_id, meta.user_data)

    # Act on manifest:
    for volume in manifest.volumes.values():
        ebs.bind(volume)
    if not eip.assign_from(manifest):
        status = 'FAILURE'

    file_writer.write_files(manifest)
    systemd.start_units(manifest)

    if not elb.health(manifest):
        status = 'FAILURE'

    cf.notify(manifest, status=status)
