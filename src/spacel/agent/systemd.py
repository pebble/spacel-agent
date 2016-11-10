import logging
import os
import subprocess
import time

logger = logging.getLogger('spacel.agent.systemd')


class SystemdUnits(object):
    """
    Interacts with Systemd.
    """

    def __init__(self, manager):
        self._manager = manager

    def start_units(self, manifest, max_wait=300, poll_interval=0.5):
        """
        Start the services/timers in a manifest.
        :param manifest: Manifest.
        :param max_wait: Time to wait for units to start (in seconds).
        :param poll_interval: Time between polling unit status (in seconds).
        :return: None.
        """
        self._manager.reload()
        timers = self._get_timers(manifest)
        waiting_units = {}
        wait_start = time.time()
        for unit in self._get_units(manifest):
            unit_id = str(unit.properties.Id)

            if unit.properties.ActiveState == 'active':
                logger.debug('Service "%s" is already running.', unit_id)
                continue

            name, ext = os.path.splitext(unit_id)
            if name in timers and ext != '.timer':
                logger.debug('Skipping "%s" due to related timer.', unit_id)
                continue

            try:
                logger.info('Starting "%s".', unit_id)
                unit.start('replace')
                waiting_units[unit_id] = time.time()
            except:
                logger.warn('Error starting "%s".', unit_id, exc_info=True)
                return False

        while waiting_units:
            for unit_name, unit_start in list(waiting_units.items()):
                unit = self._manager.get_unit(unit_name)
                unit_props = unit.properties

                # Dump info to debug:
                logger.debug('Service "%s" is: %s/%s', unit_name,
                             unit_props.ActiveState, unit_props.SubState)

                # Remove if completed:
                if unit_props.ActiveState == 'active':
                    duration = round(time.time() - unit_start, 2)
                    logger.info('Started "%s" in %ss.', unit_name, duration)
                    del waiting_units[unit_name]

            if waiting_units:
                if (time.time() - wait_start) > max_wait:
                    logger.error('Units failed to start after %ss: %s',
                                 max_wait, ', '.join(sorted(waiting_units.keys())))
                    return False
                else:
                    time.sleep(poll_interval)

        return True

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

    @staticmethod
    def log_units(manifest):
        """
        Log `systemctl status` for each service/timer in a manifest.
        :param manifest: Manifest.
        :return: None
        """
        for unit in manifest.systemd.keys():
            status_cmd = 'systemctl status -l --no-pager %s || exit 0' % unit
            status = subprocess.check_output(status_cmd, shell=True)
            logger.info('Systemd status:\n%s', status)

    def _get_units(self, manifest):
        manifest_units = set(manifest.systemd.keys())

        # Return hits from loaded units:
        for unit in self._manager.list_units():
            unit_id = unit.properties.Id
            if unit_id in manifest_units:
                manifest_units.remove(unit_id)
                logger.debug('Found loaded unit: "%s".', unit_id)
                yield unit

        for missing_unit in manifest_units:
            try:
                logger.debug('Loading unit: "%s".', missing_unit)
                yield self._manager.load_unit(missing_unit)
            except:
                logger.warn('Error loading "%s".', missing_unit,
                            exc_info=True)

    @staticmethod
    def _get_timers(manifest):
        timers = set()
        for unit in manifest.systemd.keys():
            name, ext = os.path.splitext(unit)
            if ext == '.timer':
                timers.add(name)
        return timers
