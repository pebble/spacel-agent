import logging
import os
import time

from spacel.aws import (AwsMeta, ClientCache, CloudFormationSignaller,
                        ElasticIpBinder)
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
    instance_id = meta.get_instance_id()
    region = meta.get_region()
    user_data = meta.get_user_data()

    file_writer = FileWriter()
    manager = Manager()
    systemd = SystemdUnits(manager)
    clients = ClientCache(region)
    eip = ElasticIpBinder(clients)
    cf = CloudFormationSignaller(clients)

    # Build manifest:
    manifest = AgentManifest(instance_id, user_data)

    # Act on manifest:
    eip.assign_from(manifest)
    if manifest.volumes:
        # TODO: query+attach volumes
        pass

    file_writer.write_files(manifest)
    systemd.start_units(manifest)

    # TODO: local health check
    # TODO: ELB health check

    cf.notify(manifest)
