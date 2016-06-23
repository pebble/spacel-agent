import os

from spacel.aws import (AwsMeta, ClientCache, CloudFormationSignaller,
                        ElbHealthCheck, ElasticIpBinder)

from spacel.agent import FileWriter, SystemdUnits, InstanceManager
from spacel.log import setup_logging
from spacel.model import AgentManifest
from spacel.volumes import VolumeBinder

try:
    from systemd.manager import Manager
except ImportError:
    import mock

    Manager = mock.MagicMock()

if __name__ == '__main__':
    logger = setup_logging()
    if not os.path.isdir('/files'):
        os.mkdir('/files')

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
        if not eip.assign_from(manifest):
            status = 'FAILURE'

        file_writer.write_files(manifest)
        systemd.start_units(manifest)

        if not elb.health(manifest):
            status = 'FAILURE'
        if not instance.health(manifest):
            status = 'FAILURE'
    else:
        logger.warn('Invalid manifest.')
        status = 'FAILURE'

    cf.notify(manifest, status=status)
