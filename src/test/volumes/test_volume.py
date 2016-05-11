from mock import MagicMock
from spacel.model import SpaceVolume
from spacel.volumes import (DeviceMount, EbsAttachment, VolumeDb, VolumeBinder)
from test.aws import MockedClientTest
from test.volumes import LABEL


class TestVolumeBinder(MockedClientTest):
    def setUp(self):
        super(TestVolumeBinder, self).setUp()
        self.volume = SpaceVolume(LABEL, {
            'count': 3
        })
        self.db = MagicMock(spec=VolumeDb)
        self.db.get_assignment.return_value = {
            'label': {'S': LABEL}
        }
        self.ebs = MagicMock(spec=EbsAttachment)
        self.fs = MagicMock(spec=DeviceMount)

        self.volume_binder = VolumeBinder(self.clients, self.meta)
        self.volume_binder._db = self.db
        self.volume_binder._ebs = self.ebs
        self.volume_binder._fs = self.fs

    def test_attach_no_assignment(self):
        self.db.get_assignment.return_value = None

        self.volume_binder.attach(self.volume)

    def test_attach(self):
        self.volume_binder.attach(self.volume)

        self.db.save.assert_not_called()

    def test_attach_update(self):
        def mock_update(_, volume_item):
            volume_item['volume_id'] = 'vol-123456'

        self.ebs.attach_volume.side_effect = mock_update
        self.volume_binder.attach(self.volume)

    def test_attach_instance(self):
        self.volume.instance = 0
        self.volume_binder._attach_ebs = MagicMock()

        self.volume_binder.attach(self.volume)

        self.volume_binder._attach_ebs.assert_not_called()
