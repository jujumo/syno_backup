import datetime


class ArgDefinition:
    def __init__(self, key, atype=None, required=False, default=None):
        self.key = key
        self.atype = atype
        self.required = required
        self.default = default


def path_timestamps(path, timestamp):
    if not path or not timestamp:
        return path
    elif isinstance(timestamp, datetime.datetime):
        return timestamp.strftime(path)
    else:
        datetime.datetime.now().strftime(path)


class RSyncOption:
    @classmethod
    def members(cls):
        return []

    def __init__(self, js_root):
        for m in self.members():
            if m.key in js_root:
                value = js_root[m.key]
                if m.atype:
                    value = m.atype(value)
            elif m.required:
                raise ValueError('key({}) not found.'.format(m.key))
            else:
                value = m.default
            self.__dict__[m.key] = value

    def __repr__(self):
        r = str(type(self).__name__) + ' : {'
        for m in self.members():
            r += '\n'
            r += m.key + ':'
            value = self.__dict__.get(m.key)
            r += value.__repr__()
        r += '}'
        return r

    # @abstractmethod
    def get_optional_args(self, timestamp):
        args = [a for m in self.members() if m.atype and self.__dict__.get(m.key) for a in self.__dict__[m.key].get_optional_args(timestamp)]
        return args

    # @abstractmethod
    def get_positional_args(self, timestamp):
        args = [a for m in self.members() if m.atype and self.__dict__.get(m.key) for a in self.__dict__[m.key].get_positional_args(timestamp)]
        return args


class Ssh(RSyncOption):
    @staticmethod
    def members():
        return [
            ArgDefinition('url', required=True),
            ArgDefinition('port', default=22),
            ArgDefinition('user'),
            ArgDefinition('key'),
            ArgDefinition('rsync_path', default='/bin/rsync'),
            ArgDefinition('ssh_path', default='/usr/bin/ssh'),
        ]

    def get_optional_args(self, timestamp):
        return [
            '--rsync-path={}'.format(self.rsync_path),
            '-e', '{} -i {} -p {}'.format(self.ssh_path, self.key, self.port)
        ]

    def get_positional_prepend(self):
        args = ''
        if self.user:
            args += '{}@'.format(self.user)
        args += self.url + ':'
        return args


class TargetLocal(RSyncOption):
    @classmethod
    def members(cls):
        return [
            ArgDefinition('dirpath', required=True),
            ArgDefinition('ssh', atype=Ssh)
        ]

    def get_optional_args(self, timestamp):
        args = []
        if self.ssh:
            args += self.ssh.get_optional_args()
        return args

    def get_positional_args(self, timestamp):
        args = ''
        if self.ssh:
            args += self.ssh.get_positional_prepend()
        args += path_timestamps(self.dirpath, timestamp) + '/'
        return [args]


class TargetRemote(RSyncOption):
    @classmethod
    def members(cls):
        return [
            ArgDefinition('dirpath', required=True),
            ArgDefinition('backup'),
            ArgDefinition('ssh', atype=Ssh)
        ]

    def get_optional_args(self, timestamp):
        args = []
        if self.backup:
            args += [
                '--backup',
                '--backup-dir={}'.format(path_timestamps(self.backup, timestamp))
            ]
        if self.ssh:
            args += self.ssh.get_optional_args(timestamp)
        return args

    def get_positional_args(self, timestamp):
        args = ''
        if self.ssh:
            args += self.ssh.get_positional_prepend()
        args += path_timestamps(self.dirpath, timestamp) + '/'
        return [args]


class Options(RSyncOption):
    @classmethod
    def members(cls):
        return [
            ArgDefinition('exclude'),
            ArgDefinition('dryrun', default=False),
            ArgDefinition('timeout', default=800),
        ]

    # @abstractmethod
    def get_optional_args(self, timestamp):
        args = []
        if self.exclude:
            for d in self.exclude:
                args += ['--exclude', d]
        if self.dryrun:
            args += ['--dry-run']
        if self.timeout:
            args += ['--timeout={}'.format(self.timeout)]
        return args


class Log(RSyncOption):
    @classmethod
    def members(cls):
        return [
            ArgDefinition('success'),
            ArgDefinition('progress'),
            ArgDefinition('error'),
        ]

    # @abstractmethod
    def get_optional_args(self, timestamp):
        args = []
        if self.success:
            args += ['--log-file={}'.format(path_timestamps(self.success, timestamp))]
        return args

    def get_sucess_filepath(self, timestamp):
        return path_timestamps(self.success, timestamp)

    def get_progress_filepath(self, timestamp):
        return path_timestamps(self.progress, timestamp)

    def get_error_filepath(self, timestamp):
        return path_timestamps(self.error, timestamp)


class Rule(RSyncOption):
    @classmethod
    def members(cls):
        return [
            ArgDefinition('options', required=True, atype=Options),
            ArgDefinition('log', required=False, atype=Log),
            ArgDefinition('source', required=True, atype=TargetLocal),
            ArgDefinition('dest', required=True, atype=TargetRemote),
        ]



