import logging

logger = logging.getLogger('spacel')


class SystemdUnits(object):
    """
    Interacts with Systemd.
    """

    def __init__(self, manager):
        self._manager = manager

    def start_units(self, manifest):
        """
        Start the services/timers in a manifest.
        :param manifest: Manifest.
        :return: None.
        """
        self._manager.reload()
        for unit in self._get_units(manifest):
            unit_id = unit.properties.Id

            if unit.properties.ActiveState == 'active':
                logger.debug('Service "%s" is already running.', unit_id)
                continue

            try:
                logger.debug('Starting "%s".', unit_id)
                unit.start('replace')
            except:
                logger.warn('Error starting "%s".', unit_id, exc_info=True)

    def stop_units(self, manifest):
        """
        Stop the services/timers in a manifest.
        :param manifest:  Manifest.
        :return:  None.
        """
        for unit in self._get_units(manifest):
            unit_id = unit.properties.Id
            try:
                logger.debug('Stopping "%s".', unit_id)
                unit.stop('replace')
            except:
                logger.warn('Error stopping "%s".', unit_id, exc_info=True)

    def _get_units(self, manifest):
        manifest_units = set(manifest.systemd.keys())

        timers = [unit.replace('.timer', '') for unit in manifest_units
                  if unit.endswith('.timer')]

        # Return hits from loaded units:
        for unit in self._manager.list_units():
            unit_id = unit.properties.Id
            if unit_id in manifest_units:
                manifest_units.remove(unit_id)
                yield unit

        for missing_unit in manifest_units:
            name = missing_unit.replace('.service', '')
            if name in timers:
                continue

            try:
                yield self._manager.load_unit(missing_unit)
            except:
                logger.warn('Error loading "%s".',
                            missing_unit,
                            exc_info=True)
