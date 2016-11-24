import os


class BaseMixinWriter(object):
    """
    Shared functionality for writing Systemd mixins.
    """

    def __init__(self, systemd, systemd_path='/etc/systemd/system'):
        self._systemd = systemd
        self._systemd_path = systemd_path

    def _write_mixin(self, service, label, environment=()):
        mixin = '[Service]\n'

        if environment:
            for key, value in environment.items():
                mixin += 'Environment="%s=%s"\n' % (key, value)

        service_dir = os.path.join(self._systemd_path, '%s.d' % service)
        if not os.path.isdir(service_dir):
            os.mkdir(service_dir)

        mixin_path = os.path.join(service_dir, '%s.conf' % label)
        with open(mixin_path, 'w') as mixin_out:
            mixin_out.write(mixin)
