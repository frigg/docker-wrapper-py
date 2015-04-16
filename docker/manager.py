import datetime
import logging
import os
import re
import subprocess
from time import sleep

from docker.errors import DockerUnavailableError

logger = logging.getLogger(__name__)


def _execute(cmd):
    result = ProcessResult(command=cmd)

    logger.debug('Running command: "{0}"'.format(cmd))
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True
    )

    (stdout, stderr) = process.communicate()
    result.out = stdout.decode('utf-8').strip() if stdout else ''
    result.err = stderr.decode('utf-8').strip() if stderr else ''
    result.return_code = process.returncode
    logger.debug('Finished running of: {0}'.format(result.__dict__))
    return result


class ProcessResult(object):
    return_code = None
    out = ''
    err = ''

    def __init__(self, command):
        self.command = command

    @property
    def succeeded(self):
        if self.return_code is None:
            return None
        return self.return_code == 0


class Docker(object):
    def __init__(self, image='ubuntu', timeout=3600, combine_outputs=False):
        self.container_name = 'dyn-{0}'.format(int(datetime.datetime.now().strftime('%s')) * 1000)
        self.timeout = timeout
        self.image = image
        self.combine_outputs = combine_outputs

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.stop()

    def run(self, cmd, working_directory=''):
        working_directory = self._get_working_directory(working_directory)
        command_string = 'cd {working_directory} && {command}'
        if self.combine_outputs:
            command_string += ' 2>&1'
        result = _execute(
            'docker exec -i {container} bash -c \'{command} ;  echo "--return-$?--"\''.format(
                container=self.container_name,
                command=command_string.format(working_directory=working_directory, command=cmd)
            )
        )

        return_code_match = re.search(r'(?:\\n)?--return-(\d+)--$', result.out)
        if return_code_match:
            result.return_code = int(return_code_match.group(1))
            result.out = result.out.replace(return_code_match.group(0), '')
            if result.out.endswith('\n'):
                result.out = result.out[:len(result.out) - 1]
        return result

    def read_file(self, path):
        path = self._get_working_directory(path)
        result = self.run('cat {0}'.format(path))
        if result.succeeded:
            return result.out
        return None

    def create_file(self, path, content):
        path = self._get_working_directory(path)
        return self.run('echo "{0}" >> {1}'.format(content, path))

    def file_exist(self, path):
        path = self._get_working_directory(path)
        return self.run('test -f {0}'.format(path)).return_code == 0

    def directory_exist(self, path):
        path = self._get_working_directory(path)
        return self.run('test -d {0}'.format(path)).return_code == 0

    def list_files(self, path):
        result = []

        path = self._get_working_directory(path)

        for file_path in self.run('ls -m {0}'.format(path)).out.split(', '):
            full_path = os.path.join(path, file_path)
            if self.file_exist(full_path) and not self.directory_exist(full_path):
                result.append(file_path)

        return result

    def list_directories(self, path, include_trailing_slash=True):
        result = []

        working_directory = self._get_working_directory(path)

        for file_path in self.run('ls -dm */'.format(path), working_directory).out.split(', '):
            if self.directory_exist(os.path.join(path, file_path)):

                if include_trailing_slash:
                    result.append(file_path)
                else:
                    result.append(file_path[:-1])

        return result

    def start(self):
        """
        Starts a container based on the parameters passed to __init__.

        :return: The docker object
        """
        result = _execute('docker run -d --name {0} {1} /bin/sleep {2}'.format(
            self.container_name,
            self.image,
            self.timeout
        ))
        if not result.succeeded:
            raise DockerUnavailableError('Starting the docker container failed.')
        return self

    def stop(self):
        """
        Stops the container started by this class instance.

        :return: The docker object
        """
        sleep(2)
        _execute('docker kill {0}'.format(self.container_name))
        _execute('docker rm {0}'.format(self.container_name))
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
        if working_directory.startswith('/') or working_directory.startswith('~/'):
            return working_directory
        return '~/{}'.format(working_directory)
