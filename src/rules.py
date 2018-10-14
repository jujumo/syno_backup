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

    def get_children(self):
        return [self.__dict__.get(c.key) for c in self.members() if isinstance(self.__dict__.get(c.key), RSyncOption)]

    # @abstractmethod
    def get_optional_args(self, timestamp):
        args = [arg for c in self.get_children() for arg in c.get_optional_args(timestamp)]
        return args

    # @abstractmethod
    def get_positional_args(self, timestamp):
        args = [arg for c in self.get_children() for arg in c.get_positional_args(timestamp)]
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


class Source(RSyncOption):
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
        source_dirpath = self.dirpath
        # replace date wildcard
        source_dirpath = path_timestamps(source_dirpath, timestamp)
        # make sur there is a trailing / to copy only content
        if not source_dirpath.endswith('/'):
            source_dirpath = source_dirpath + '/'
        args += source_dirpath
        return [args]


class Destination(RSyncOption):
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
        source_dirpath = self.dirpath
        # replace date wildcard
        source_dirpath = path_timestamps(source_dirpath, timestamp)
        args += source_dirpath
        return [args]


class Options(RSyncOption):
    @classmethod
    def members(cls):
        return [
            ArgDefinition('exclude'),
            ArgDefinition('timeout', default=800),
            ArgDefinition('dry-run', atype=bool, default=False),
            ArgDefinition('force', atype=bool, default=True),
            ArgDefinition('archive', atype=bool, default=True),             # = -rlptgoD
            ArgDefinition('compress', atype=bool, default=True),            # compress for remote transfer
            ArgDefinition('delete', atype=bool, default=True),              # remove deleted dirs
            ArgDefinition('delete-excluded', atype=bool, default=True),     # also delete the excluded files
            ArgDefinition('no-owner', atype=bool, default=True),            # do not check ownership changes  TODO: move it to some FAT32 related thing
            ArgDefinition('no-group', atype=bool, default=True),            # do not check ownership changes  TODO: move it to some FAT32 related thing
            ArgDefinition('no-perms', atype=bool, default=True),            # do not check permission changes  TODO: move it to some FAT32 related thing
            ArgDefinition('one-file-system', atype=bool, default=True),     # Do not cross filesystem boundaries when recursing: for security reasons
        ]

    # @abstractmethod
    def get_optional_args(self, timestamp):
        args = []
        if self.exclude:
            for d in self.exclude:
                args += ['--exclude', d]

        if self.timeout:
            args += ['--timeout={}'.format(self.timeout)]

        # retrieve all boolean options
        activations = (m for m in self.members() if m.atype is bool) # get bool members
        activations = (m.key for m in activations if self.__dict__.get(m.key, False))  # filter the ones to true
        activations = [f'--{m}' for m in activations]  # format with --
        args += activations
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
        if self.progress:
            args += ['--progress']
        if self.success:
            args += ['--itemize-changes']  # display the actions to be taken before starting
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
            ArgDefinition('source', required=True, atype=Source),
            ArgDefinition('dest', required=True, atype=Destination),
        ]



