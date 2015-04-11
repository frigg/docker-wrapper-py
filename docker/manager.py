import datetime
import os
import subprocess
from time import sleep

from docker.errors import DockerUnavailableError


def _execute(cmd):
    result = ProcessResult(command=cmd)

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
    result.succeeded = result.return_code == 0

    return result


class ProcessResult(object):
    def __init__(self, command):
        self.command = command


class Docker(object):
    def __init__(self, image="ubuntu", timeout=3600):
        self.container_name = "dyn-{0}".format(int(datetime.datetime.now().strftime("%s")) * 1000)
        self.timeout = timeout
        self.image = image

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.stop()

    def run(self, cmd, working_directory=""):
        working_directory = self._get_working_directory(working_directory)
        return _execute('docker exec -i -t {container} bash -c "{command}"'.format(
            container=self.container_name,
            command="cd {0} && {1}".format(working_directory, cmd)
        ))

    def read_file(self, path):
        path = self._get_working_directory(path)
        return self.run("cat {0}".format(path)).out

    def create_file(self, path, content):
        path = self._get_working_directory(path)
        return self.run("echo '{0}' >> {1}".format(content, path))

    def file_exist(self, path):
        path = self._get_working_directory(path)
        return self.run("test -f {0}".format(path)).return_code == 0

    def directory_exist(self, path):
        path = self._get_working_directory(path)
        return self.run("test -d {0}".format(path)).return_code == 0

    def list_files(self, path):
        result = []

        path = self._get_working_directory(path)

        for file_path in self.run("ls -m {0}".format(path)).out.split(", "):
            full_path = os.path.join(path, file_path)
            if self.file_exist(full_path) and not self.directory_exist(full_path):
                result.append(file_path)

        return result

    def list_directories(self, path, include_trailing_slash=True):
        result = []

        working_directory = self._get_working_directory(path)

        for file_path in self.run("ls -dm */".format(path), working_directory).out.split(", "):
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
    def _get_working_directory(working_directory):
        if not working_directory.startswith('/'):
            working_directory = '~/{}'.format(working_directory)
        return working_directory
