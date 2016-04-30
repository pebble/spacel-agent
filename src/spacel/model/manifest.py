class AgentManifest(object):
    def __init__(self, instance_id, params={}):
        self.instance_id = instance_id
        self.eips = params.get('eips', ())
        self.volumes = params.get('volumes', ())
        self.files = params.get('files', {})
        self.systemd = params.get('systemd', {})
        self.cf_signal = params.get('cloudformation_signal', {})

    @property
    def all_files(self):
        every_file = {}
        every_file.update(self.files)
        every_file.update(self.systemd)
        return every_file
