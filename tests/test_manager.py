import unittest
from random import randint

import six

from docker.manager import Docker

try:
    from unittest import mock
except ImportError:
    import mock


class DockerManagerTests(unittest.TestCase):
    """
    This test class should contain tests for the docker manager
    that does not invoke docker.
    """

    def test__get_working_directory(self):
        self.assertEqual(Docker._get_working_directory('directory'), '~/directory')
        self.assertEqual(Docker._get_working_directory('/absolute/path'), '/absolute/path')
        self.assertEqual(Docker._get_working_directory('~/home/path'), '~/home/path')

    @mock.patch('docker.manager.Docker.stop')
    @mock.patch('docker.manager.Docker.start')
    def test_with_statement(self, mock_start, mock_stop):
        with Docker() as docker:
            self.assertIsNotNone(docker)

        mock_start.assert_called_once_with()
        mock_stop.assert_called_once_with()

    @mock.patch('docker.manager.Docker.stop')
    @mock.patch('docker.manager.Docker.start')
    def test_wrap(self, mock_start, mock_stop):
        @Docker.wrap()
        def wrapped(test, docker):
            test.assertIsNotNone(docker)
            return True

        self.assertTrue(wrapped(self))
        mock_start.assert_called_once_with()
        mock_stop.assert_called_once_with()

    @mock.patch('docker.manager.Docker.stop')
    @mock.patch('docker.manager.Docker.start')
    def test_with_statement_exception(self, mock_start, mock_stop):
        if six.PY3:
            with self.assertRaisesRegex(RuntimeError, 'something crazy happened'):
                with Docker():
                    raise RuntimeError('something crazy happened')
        else:
            with self.assertRaises(RuntimeError):
                with Docker():
                    raise RuntimeError('something crazy happened')

        mock_start.assert_called_once_with()
        mock_stop.assert_called_once_with()

    @mock.patch('docker.manager.execute')
    @mock.patch('re.search', lambda *x: None)
    def test_quotation_mark_handling(self, mock_run):
        docker = Docker()
        docker.run('echo "hi there"')
        docker.run("echo 'hi there'")
        expected = ('docker exec -i {} bash -c \'cd ~/ && echo "hi there" ;  '
                    'echo "--return-$?--"\''.format(docker.container_name))

        mock_run.assert_has_calls([mock.call(expected), mock.call(expected)])

    @mock.patch('docker.manager.execute')
    @mock.patch('re.search', lambda *x: None)
    def test_env_variables(self, mock_run):
        docker = Docker(env_variables={'CI': 1, 'FRIGG': 1})
        docker.run('ls')
        mock_run.assert_called_once_with('docker exec -i {} bash -c \'CI=1 FRIGG=1 cd ~/ && ls ;'
                                         '  echo "--return-$?--"\''.format(docker.container_name))

    @mock.patch('docker.manager.execute')
    def test_single_port_mappping(self, mock_run):
        with Docker(ports_mapping=["4080:4080"]) as docker:
            mock_run.assert_called_once_with(
                'docker run -d -p 4080:4080 --name {0} {1} /bin/sleep {2}'.format(
                    docker.container_name,
                    docker.image,
                    docker.timeout
                ))

    @mock.patch('docker.manager.execute')
    def test_multiple_port_mapppings(self, mock_run):
        ports = ["4080:4080", "8080:8080", "4443:4443"]
        with Docker(ports_mapping=ports) as docker:
            mock_run.assert_called_once_with(
                'docker run -d {0} --name {1} {2} /bin/sleep {3}'.format(
                    ' '.join(["-p {0}".format(port_mapping) for port_mapping in ports]),
                    docker.container_name,
                    docker.image,
                    docker.timeout
                ))


class DockerInteractionTests(unittest.TestCase):
    def setUp(self):
        self.docker = Docker()
        self.docker.start()

    def tearDown(self):
        self.docker.stop()

    def test_create_files(self):
        self.docker.run('touch file1')
        self.docker.run('touch file2')
        self.assertEqual(self.docker.list_files(''), ['file1', 'file2'])

    def test_create_directories(self):
        self.docker.run('mkdir dir1')
        self.docker.run('mkdir dir1/test')
        self.docker.run('mkdir dir2')
        self.docker.run('mkdir dir3')
        self.assertEqual(
            self.docker.list_directories('', include_trailing_slash=False),
            ['dir1', 'dir2', 'dir3']
        )

    def test_create_and_list_files_in_sub_directory(self):
        self.docker.run('mkdir builds')
        self.docker.run('touch builds/readme.txt')

        self.assertEqual(self.docker.list_files('builds'), ['readme.txt'])

    def test_create_file_with_content(self):
        file_name = 'readme.txt'
        file_content = 'this is a test file'

        self.assertFalse(self.docker.file_exist(file_name))
        self.docker.create_file(file_name, file_content)
        self.assertTrue(self.docker.file_exist(file_name))

    def test_read_file_with_content(self):
        file_name = 'readme.txt'
        file_content = 'this is a test file {0}'.format(randint(5000, 5500))
        self.docker.run('echo \"{0}\" > ~/{1}; cat readme.txt'.format(file_content, file_name))

        self.assertEqual(self.docker.read_file(file_name), file_content)

    def test_read_file_that_dont_exist(self):
        self.assertIsNone(self.docker.read_file('no-file.txt'))

    def test_directory_exist(self):
        self.assertTrue(self.docker.directory_exist('~/'))
        self.assertFalse(self.docker.directory_exist('does-not-exist'))

    def test_file_exist(self):
        self.docker.run('touch file')
        self.assertTrue(self.docker.file_exist('file'))
        self.assertFalse(self.docker.file_exist('does-not-exist'))

    def test_combine_output(self):
        self.docker.combine_outputs = True
        result = self.docker.run('ls does-not-exist')
        self.assertEqual(result.err, '')
        self.assertEqual(result.out, 'ls: cannot access does-not-exist: No such file or directory')

    def test_privilege(self):
        Docker(privilege=True).start()
