import logging

from spacel.aws import AwsMeta, ClientCache, ElasticIpBinder
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

    # Get context:
    meta = AwsMeta()
    instance_id = meta.get_instance_id()
    region = meta.get_region()

    # Build manifest:
    params = meta.get_user_data()
    manifest = AgentManifest(params)

    # Act on manifest:
    clients = ClientCache()

    if manifest.eips:
        eip = ElasticIpBinder(clients.ec2(region), instance_id)
        eip.assign_from(manifest.eips)

    if manifest.volumes:
        # TODO: query+attach volumes
        pass

    file_writer = FileWriter()
    manager = Manager()
    systemd = SystemdUnits(manager)

    file_writer.write_files(manifest)
    systemd.start_units(manifest)
