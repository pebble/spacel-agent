from botocore.exceptions import ClientError
from mock import MagicMock, patch
from spacel.model import SpaceVolume
from spacel.volumes.ebs import EbsAttachment
from test.aws import MockedClientTest, INSTANCE_ID, AVAILABILITY_ZONE
from test.volumes import LABEL, DEVICE

VOLUME_ID = 'vol-111111'
SNAPSHOT_ID = 'snap-123456'


class TestEbsAttachment(MockedClientTest):
    def setUp(self):
        super(TestEbsAttachment, self).setUp()
        self.volume = SpaceVolume(LABEL, {
            'count': 3
        })
        self.volume_item = {
            'label': {'S': LABEL},
            'index': {'N': 0}
        }
        self.ebs_attachment = EbsAttachment(self.clients, self.meta)

    def test_attach_existing(self):
        self.volume_item['volume_id'] = {'S': VOLUME_ID}

        self.ec2.describe_volumes.return_value = {'Volumes': [{
            'Attachments': [{
                'InstanceId': INSTANCE_ID,
                'Device': DEVICE
            }]
        }]}

        volume_item = self.ebs_attachment.attach_volume(self.volume,
                                                        self.volume_item)

        self.assertEqual({'S': DEVICE}, volume_item['device'])

        self.ec2.create_snapshot.assert_not_called()
        self.ec2.create_volume.assert_not_called()
        self.ec2.attach_volume.assert_not_called()
        self.ec2.get_waiter.assert_not_called()

    def test_attach_existing_same_az(self):
        self.volume_item['volume_id'] = {'S': VOLUME_ID}
        self.ec2.describe_volumes.return_value = {'Volumes': [{
            'AvailabilityZone': AVAILABILITY_ZONE,
            'Attachments': [{
                'InstanceId': 'i-654321',
                'Device': DEVICE
            }]
        }]}
        self.ebs_attachment._next_volume = MagicMock(return_value=DEVICE)
        self.ebs_attachment._attach_volume = MagicMock()

        self.ebs_attachment.attach_volume(self.volume, self.volume_item)

        self.ec2.create_snapshot.assert_not_called()
        self.ec2.create_volume.assert_not_called()
        self.ec2.attach_volume.assert_not_called()
        self.ec2.get_waiter.assert_called_with('volume_available')

    def test_attach_existing_different_az(self):
        self.volume_item['volume_id'] = {'S': VOLUME_ID}
        self.ec2.describe_volumes.return_value = {'Volumes': [{
            'AvailabilityZone': 'us-west-2a',
            'Attachments': [{
                'InstanceId': 'i-654321',
                'Device': '/dev/xvdb'
            }]
        }]}
        self.ec2.create_snapshot.return_value = {'SnapshotId': SNAPSHOT_ID}
        self.ebs_attachment._next_volume = MagicMock(return_value=DEVICE)
        self.ebs_attachment._attach_volume = MagicMock()

        self.ebs_attachment.attach_volume(self.volume, self.volume_item)

        self.ec2.create_snapshot.assert_called_with(VolumeId=VOLUME_ID)
        self.ec2.create_volume.assert_called_with(
                AvailabilityZone=AVAILABILITY_ZONE,
                Size=4,
                VolumeType='gp2',
                SnapshotId=SNAPSHOT_ID
        )
        self.ec2.attach_volume.assert_not_called()
        self.ec2.delete_volume.assert_called_with(VolumeId=VOLUME_ID)

    def test_attach_create_volume(self):
        self.volume.iops = 400
        self.volume.encrypted = True
        self.volume_item['snapshot_id'] = {'S': SNAPSHOT_ID}
        self.ebs_attachment._next_volume = MagicMock(return_value=DEVICE)
        self.ebs_attachment._attach_volume = MagicMock()

        self.ebs_attachment.attach_volume(self.volume, self.volume_item)

        self.ec2.describe_volumes.assert_not_called()
        self.ec2.create_snapshot.assert_not_called()
        self.ec2.create_volume.assert_called_with(
                Size=4, VolumeType='gp2', AvailabilityZone=AVAILABILITY_ZONE,
                Iops=400, Encrypted=True, SnapshotId=SNAPSHOT_ID)

    def test_describe_volume_error(self):
        client_error = ClientError({'Error': {'Code': 0}}, 'DescribeVolumes')
        self.ec2.describe_volumes.side_effect = client_error

        self.assertRaises(ClientError, self.ebs_attachment._describe_volume,
                          VOLUME_ID)

    def test_describe_volume_not_found(self):
        client_error = ClientError({'Error': {
            'Code': 'InvalidVolume.NotFound'}}, 'DescribeVolumes')
        self.ec2.describe_volumes.side_effect = client_error

        volume = self.ebs_attachment._describe_volume(VOLUME_ID)
        self.assertIsNone(volume)

    @patch('spacel.volumes.ebs.check_output')
    def test_next_volume(self, mock_lsblk):
        mock_lsblk.return_value = '''NAME   MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
/dev/xvda                                                  8:0    0 8.0G  0 disk
/dev/xvdb                                                  8:1    0 16.0G  0 disk
'''
        next_device = self.ebs_attachment._next_volume()
        self.assertEqual('/dev/xvdc', next_device)

    @patch('spacel.volumes.ebs.check_output')
    def test_next_volume_none_available(self, mock_lsblk):
        devices = ['/dev/xvd%s' % chr(ord('a') + dev) for dev in range(26)]

        mock_lsblk.return_value = '\n'.join(devices)
        next_device = self.ebs_attachment._next_volume()
        self.assertIsNone(next_device)

    @patch('spacel.volumes.ebs.check_output')
    def test_attach_volume(self, _):
        volume_item = {'volume_id': {'S': VOLUME_ID}}
        self.ebs_attachment._attach_volume(volume_item)
