import logging
import uuid
from collections import OrderedDict
from time import sleep

from docker import errors
from docker.helpers import execute

logger = logging.getLogger(__name__)


class Docker(object):
    """
    Docker manager which can start and stop containers in addition to run commands with docker exec.
    The manager also have a few helper functions for things like listing files and directories.
    """

    def __init__(self, image='ubuntu', name_prefix='dyn', timeout=3600, privilege=False,
                 combine_outputs=False, env_variables=None, ports_mapping=None):
        """
        Creates a docker manager. Each manager has a reference to a unique container name.

        :param image: The image which the manager should use to start the container. It could be
                      a local image or an image from the registry.
        :type image: str
        :param name_prefix: All image names are prefixed with this string.
        :type name_prefix: str
        :param timeout: The time the docker container will live after running ``docker.start()`` in
                        seconds.
        :type timeout: int
        :param privilege: If set to True the docker container will be run with the privilege
                          parameter.
        :type privilege: bool
        :param combine_outputs: Setting this to True will put stderr output in stdout.
        :type combine_outputs: bool
        :param ports_mapping: Map ports from docker container to host machine,
                              format ['4080:40480', '5000:5000']
        :type ports_mapping: list
        :return: A docker manager object.
        :rtype: Docker
        """
        self.container_name = '{0}-{1}'.format(name_prefix, uuid.uuid4())
        self.timeout = timeout
        self.image = image
        self.privilege = privilege
        self.combine_outputs = combine_outputs
        self.env_variables = OrderedDict()
        if env_variables:
            self.env_variables.update(sorted(env_variables.items(), key=lambda t: t[0]))

        self.ports = ''
        if ports_mapping:
            self.ports = ' '.join(['-p {0}'.format(port_mapping) for port_mapping in ports_mapping])

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()
        if exc_value:
            raise exc_value

    def run(self, command, working_directory='', stdin='', login=False, tty=False):
        """
        Runs the command with docker exec in the given working directory.

        :param command: The command that should be run with docker exec. The command will be wrapped
                        in  `bash -c \'command\'".
        :type command: str
        :param working_directory: The path to the directory where the command should be run. This
                                  will be evaluated with ``_get_working_directory``, thus relative
                                  paths will become absolute paths.
        :type working_directory: str
        :type stdin: str
        :param login: Will add --login on the bash call.
        :type login: boolean
        :param tty: Will add -t on the bash call.
        :type tty: boolean
        :return: A ProcessResult object containing information on the result of the command.
        :rtype: ProcessResult
        """
        working_directory = self._get_working_directory(working_directory)
        command = command.replace('\'', '"')
        command_string = 'cd {working_directory} && {envs} {command}'

        if self.combine_outputs:
            command_string += ' 2>&1'

        env_string = ' '.join([
            '{0}={1}'.format(key, self.env_variables[key]) for key in self.env_variables
        ])

        result = execute(
            'docker exec -i{tty} {container} bash{login} -c \'{command}\''.format(
                envs=env_string,
                container=self.container_name,
                login=' --login' if login else '',
                tty=' -t' if tty else '',
                command=command_string.format(
                    working_directory=working_directory,
                    command=command,
                    envs=env_string
                )
            ),
            stdin
        )

        return result

    def read_file(self, path):
        """
        Reads the content of the file on the given path. Returns None if the file does not exist.

        :param path: The path to the file.
        :type path: str
        :return: The content of the file
        :rtype: str
        :raises DockerFileNotFoundError: If given an invalid path
        :raises DockerWrapperBaseError: For other errors
        """
        path = self._get_working_directory(path)
        result = self.run('cat {0}'.format(path))

        if not result.succeeded:
            if errors.FILE_NOT_FOUND_PREDICATE in result.err:
                raise errors.DockerFileNotFoundError(path)

            raise errors.DockerWrapperBaseError(result.err)

        return result.out

    def write_file(self, path, content, append=False):
        """
        Write the given content to path.
        Overwrites the file if append is set to False.

        :param path: The path to the file.
        :type path: str
        :param content: The content of the file.
        :type content: str
        :param append: Set to False to overwrite file, defaults to False.
        :type append: bool
        :return: A object with the result of the create command.
        :rtype: ProcessResult
        """
        path = self._get_working_directory(path)
        modifier = '>>' if append else '>'
        return self.run('cat {0} {1}'.format(modifier, path), stdin=content)

    def file_exist(self, path):
        """
        Checks whether a file exists or not.

        :param path: The path to the file.
        :type path: str
        :rtype: bool
        """
        path = self._get_working_directory(path)
        return self.run('test -f {0}'.format(path)).return_code == 0

    def directory_exist(self, path):
        """
        Checks whether a directory exists or not.

        :param path: The path to the directory.
        :type path: str
        :rtype: bool
        """
        path = self._get_working_directory(path)
        return self.run('test -d {0}'.format(path)).return_code == 0

    def list_files(self, path):
        """
        List files on a given path.

        :param path: The path to the directory.
        :type path: str
        :return: An list of file names
        :rtype: list
        :raises DockerFileNotFoundError: If given an invalid path
        :raises DockerWrapperBaseError: For other errors
        """

        path = self._get_working_directory(path)

        # `grep -v /$` matches everything that doesn't end with a
        # trailing slash, i.e. only files since `ls -p` is used:
        result = self.run('ls -p | grep --color=never -v /$', path)

        if not result.succeeded:
            if errors.FILE_NOT_FOUND_PREDICATE in result.err:
                raise errors.DockerFileNotFoundError(path)

            raise errors.DockerWrapperBaseError(result.err)

        return result.out.strip().split('\n')

    def list_directories(self, path, include_trailing_slash=True):
        """
        List directories on a given path.

        :param path: The path to the directory.
        :type path: str
        :return: An list of directory names
        :rtype: list
        :raises DockerFileNotFoundError: If given an invalid path
        :raises DockerWrapperBaseError: For other errors
        """

        files = []
        path = self._get_working_directory(path)
        result = self.run('ls -dm */', path)

        if not result.succeeded:
            if errors.FILE_NOT_FOUND_PREDICATE in result.err:
                raise errors.DockerFileNotFoundError(path)

            raise errors.DockerWrapperBaseError(result.err)

        for file_path in result.out.strip().split(', '):
            if include_trailing_slash:
                files.append(file_path)
            else:
                files.append(file_path[:-1])

        return files

    def start(self):
        """
        Starts a container based on the parameters passed to __init__.

        :return: The docker object
        """
        if self.privilege:
            command_string = 'docker run -d --privileged {0} --name {1} {2} /bin/sleep {3}'
        else:
            command_string = 'docker run -d {0} --name {1} {2} /bin/sleep {3}'

        result = execute(command_string.format(
            self.ports,
            self.container_name,
            self.image,
            self.timeout
        ))

        if not result.succeeded:
            raise errors.DockerUnavailableError(
                'Starting the docker container failed.\n{0}'.format(result.err)
            )

        return self

    def stop(self):
        """
        Stops the container started by this class instance.

        :return: The docker object
        """
        sleep(2)
        execute('docker kill {0}'.format(self.container_name))
        execute('docker rm {0}'.format(self.container_name))
        return self

    @staticmethod
    def wrap(*wrap_args, **wrap_kwargs):
        """
        Decorator that wraps the function call in a Docker with statement. It
        accepts the same arguments. This decorator adds a docker manager instance
        to the kwargs passed into the decorated function.

        :return: The decorated function.
        """

        def activate(func):
            def wrapper(*args, **kwargs):
                with Docker(*wrap_args, **wrap_kwargs) as docker:
                    kwargs['docker'] = docker
                    return func(*args, **kwargs)

            return wrapper

        return activate

    @staticmethod
    def _get_working_directory(working_directory):
        """
        Gets the path of the working working directory. It takes a path and converts it to an
        appropriate absolute path.

        :param working_directory:
        :type working_directory: str
        :return: An absolute path to the given working directory.
        :rtype str:
        """
        if working_directory.startswith('/') or working_directory.startswith('~/'):
            return working_directory
        return '~/{}'.format(working_directory)
