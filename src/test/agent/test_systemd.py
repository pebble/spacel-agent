import unittest
from mock import MagicMock
from spacel.model import AgentManifest
from spacel.agent.systemd import SystemdUnits

INSTANCE_ID = 'i-123456'
SYSTEMD_SERVICE = 'foo.service'


class TestSystemdUnits(unittest.TestCase):
    def setUp(self):
        self.unit = MagicMock()
        self.unit.properties.Id = SYSTEMD_SERVICE

        self.manager = MagicMock()
        self.manifest = AgentManifest({
            'systemd': {
                SYSTEMD_SERVICE: ''
            }
        })

        self.systemd = SystemdUnits(self.manager)

    def test_start_units(self):
        self.systemd._get_units = MagicMock(return_value=[self.unit])

        self.systemd.start_units(self.manifest)
        self.unit.start.assert_called_with('replace')

    def test_start_units_error(self):
        self.systemd._get_units = MagicMock(return_value=[self.unit])
        self.unit.start.side_effect = Exception()

        self.systemd.start_units(self.manifest)

    def test_start_units_already_running(self):
        self.systemd._get_units = MagicMock(return_value=[self.unit])
        self.unit.properties.ActiveState = 'active'

        self.systemd.start_units(self.manifest)
        self.unit.start.assert_not_called()

    def test_stop_units(self):
        self.systemd._get_units = MagicMock(return_value=[self.unit])
        self.systemd.stop_units(self.manifest)
        self.unit.stop.assert_called_with('replace')

    def test_stop_units_error(self):
        self.systemd._get_units = MagicMock(return_value=[self.unit])
        self.unit.stop.side_effect = Exception()
        self.systemd.stop_units(self.manifest)

    def test_get_units_loaded(self):
        self.manager.list_units.return_value = [self.unit]

        units = [u for u in self.systemd._get_units(self.manifest)]
        self.assertEquals(1, len(units))
        self.assertEquals(self.unit, units[0])

    def test_get_units_load(self):
        self.manager.list_units.return_value = []
        self.manager.load_unit.return_value = self.unit

        units = [u for u in self.systemd._get_units(self.manifest)]
        self.assertEquals(1, len(units))
        self.assertEquals(self.unit, units[0])

    def test_get_units_load_error(self):
        self.manager.list_units.return_value = []
        self.manager.load_unit.side_effect = Exception()

        units = [u for u in self.systemd._get_units(self.manifest)]
        self.assertEquals(0, len(units))
