from mock import MagicMock, patch, ANY
import unittest

from spacel.aws import AwsMeta, CloudFormationSignaller
from spacel.cli.services import start_services


class TestServices(unittest.TestCase):
    def setUp(self):
        self._meta = MagicMock(spec=AwsMeta)
        self._meta.region = 'us-east-1'
        self._meta.az = 'us-east-1a'
        self._meta.instance_id = 'i-123456'
        self._meta.orbit = 'test-orbit'
        self._meta.user_data = {}

        self._signaller = MagicMock(spec=CloudFormationSignaller)

    @patch('spacel.cli.services.AwsMeta')
    @patch('spacel.cli.services.CloudFormationSignaller')
    @patch('spacel.cli.services.Manager')
    def test_start_services_invalid(self, _, cf_factory, aws_meta_factory):
        aws_meta_factory.return_value = self._meta
        cf_factory.return_value = self._signaller
        # The same instance volume is assigned twice:
        self._meta.user_data['volumes'] = {
            'foo': {'instance': 0},
            'bar': {'instance': 0}
        }

        start_services()

        self._signaller.notify.assert_called_with(ANY, status='FAILURE')

    @patch('spacel.cli.services.AwsMeta')
    @patch('spacel.cli.services.CloudFormationSignaller')
    @patch('spacel.cli.services.FileWriter')
    @patch('spacel.cli.services.Manager')
    def test_start_services_valid(self, _, writer_factory, cf_factory,
                                  aws_meta_factory):
        aws_meta_factory.return_value = self._meta
        cf_factory.return_value = self._signaller
        writer_factory.return_value = MagicMock()

        start_services()

        self._signaller.notify.assert_called_with(ANY, status='SUCCESS')

    @patch('spacel.cli.services.AwsMeta')
    @patch('spacel.cli.services.CloudFormationSignaller')
    @patch('spacel.cli.services.FileWriter')
    @patch('spacel.cli.services.Manager')
    @patch('spacel.cli.services.VolumeBinder')
    def test_start_services_valid_volumes(self, volume_factory, _,
                                          writer_factory, cf_factory,
                                          aws_meta_factory):
        aws_meta_factory.return_value = self._meta
        cf_factory.return_value = self._signaller
        writer_factory.return_value = MagicMock()
        volume_binder = MagicMock()
        volume_factory.return_value = volume_binder

        self._meta.user_data['volumes'] = {
            'test-volume': {
                'size': 8
            }
        }

        start_services()

        self.assertEquals(volume_binder.attach.call_count, 1)

    @patch('spacel.cli.services.AwsMeta')
    @patch('spacel.cli.services.CloudFormationSignaller')
    @patch('spacel.cli.services.ElasticIpBinder')
    @patch('spacel.cli.services.FileWriter')
    @patch('spacel.cli.services.Manager')
    def test_start_services_valid_eip_fail(self, _, writer_factory, eip_factory,
                                           cf_factory, aws_meta_factory):
        aws_meta_factory.return_value = self._meta
        cf_factory.return_value = self._signaller
        writer_factory.return_value = MagicMock()
        eip_binder = MagicMock()
        eip_binder.assign_from.return_value = False
        eip_factory.return_value = eip_binder

        self._meta.user_data['eips'] = ['eip-123456']

        start_services()

        self.assertEquals(eip_binder.assign_from.call_count, 1)
        self._signaller.notify.assert_called_with(ANY, status='FAILURE')

    @patch('spacel.cli.services.AwsMeta')
    @patch('spacel.cli.services.CloudFormationSignaller')
    @patch('spacel.cli.services.ElbHealthCheck')
    @patch('spacel.cli.services.FileWriter')
    @patch('spacel.cli.services.Manager')
    def test_start_services_valid_elb_fail(self, _, writer_factory, elb_factory,
                                           cf_factory, aws_meta_factory):
        aws_meta_factory.return_value = self._meta
        cf_factory.return_value = self._signaller
        writer_factory.return_value = MagicMock()
        elb_health_check = MagicMock()
        elb_health_check.health.return_value = False
        elb_factory.return_value = elb_health_check

        start_services()

        self.assertEquals(elb_health_check.health.call_count, 1)
        self._signaller.notify.assert_called_with(ANY, status='FAILURE')

    @patch('spacel.cli.services.AwsMeta')
    @patch('spacel.cli.services.CloudFormationSignaller')
    @patch('spacel.cli.services.SystemdUnits')
    @patch('spacel.cli.services.FileWriter')
    @patch('spacel.cli.services.Manager')
    def test_start_services_valid_systemd_fail(self, _, writer_factory,
                                               systemd_factory, cf_factory,
                                               aws_meta_factory):
        aws_meta_factory.return_value = self._meta
        cf_factory.return_value = self._signaller
        writer_factory.return_value = MagicMock()
        systemd_units = MagicMock()
        systemd_units.start_units.return_value = False
        systemd_factory.return_value = systemd_units

        start_services()

        self.assertEquals(systemd_units.start_units.call_count, 1)
        self._signaller.notify.assert_called_with(ANY, status='FAILURE')

    @patch('spacel.cli.services.AwsMeta')
    @patch('spacel.cli.services.CloudFormationSignaller')
    @patch('spacel.cli.services.FileWriter')
    @patch('spacel.cli.services.InstanceManager')
    @patch('spacel.cli.services.Manager')
    def test_start_services_valid_instance_fail(self, _, instance_factory,
                                                writer_factory, cf_factory,
                                                aws_meta_factory):
        aws_meta_factory.return_value = self._meta
        cf_factory.return_value = self._signaller
        writer_factory.return_value = MagicMock()
        instance_health_check = MagicMock()
        instance_health_check.health.return_value = False
        instance_factory.return_value = instance_health_check

        start_services()

        self.assertEquals(instance_health_check.health.call_count, 1)
        self._signaller.notify.assert_called_with(ANY, status='FAILURE')
