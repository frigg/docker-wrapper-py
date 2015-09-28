import unittest
from random import randint

import six

from docker.errors import DockerFileNotFoundError, DockerWrapperBaseError
from docker.helpers import ProcessResult
from docker.manager import Docker

try:
    from unittest import mock
except ImportError:
    import mock

unknown_error_result = ProcessResult('test')
unknown_error_result.err = 'Unknown error'


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
        docker.run('echo "hi there"', login=True, tty=True)
        docker.run("echo 'hi there'", login=True, tty=True)
        expected = (
            'docker exec -i -t {} bash --login -c \'cd ~/ &&  echo "hi there"\''.format(
                docker.container_name
            ),
            ''
        )

        mock_run.assert_has_calls([mock.call(*expected), mock.call(*expected)])

    @mock.patch('docker.manager.execute')
    @mock.patch('re.search', lambda *x: None)
    def test_env_variables(self, mock_run):
        docker = Docker(env_variables={'CI': 1, 'FRIGG': 1})
        docker.run('ls')
        mock_run.assert_called_once_with(
            'docker exec -i -t {} bash --login -c \'cd ~/ && CI=1 FRIGG=1 ls\''.format(
                docker.container_name
            ),
            ''
        )

    @mock.patch('docker.manager.execute')
    @mock.patch('re.search', lambda *x: None)
    def test_no_login(self, mock_run):
        docker = Docker()
        docker.run('ls', login=False)
        mock_run.assert_called_once_with(
            'docker exec -i {} bash -c \'cd ~/ &&  ls\''.format(docker.container_name),
            ''
        )

    @mock.patch('docker.manager.execute')
    def test_single_port_mappping(self, mock_run):
        docker = Docker(ports_mapping=['4080:4080'])
        docker.start()
        mock_run.assert_called_once_with(
            'docker run -d -p 4080:4080 --name {0} {1} /bin/sleep {2}'.format(
                docker.container_name,
                docker.image,
                docker.timeout
            ))

    @mock.patch('docker.manager.execute')
    def test_multiple_port_mapppings(self, mock_run):
        ports = ["4080:4080", "8080:8080", "4443:4443"]
        docker = Docker(ports_mapping=ports)
        docker.start()
        mock_run.assert_called_once_with(
            'docker run -d {0} --name {1} {2} /bin/sleep {3}'.format(
                ' '.join(["-p {0}".format(port_mapping) for port_mapping in ports]),
                docker.container_name,
                docker.image,
                docker.timeout
            ))

    @mock.patch('docker.manager.execute')
    @mock.patch('docker.manager.Docker.run', return_value=unknown_error_result)
    def test_read_file_unknown_error(self, mock_run, mock_execute):
        docker = Docker()
        docker.start()
        path = 'test-file'
        self.assertRaisesRegexp(
            DockerWrapperBaseError,
            unknown_error_result.err,
            docker.read_file,
            path
        )

    @mock.patch('docker.manager.execute')
    @mock.patch('docker.manager.Docker.run', return_value=unknown_error_result)
    def test_list_files_unknown_error(self, mock_run, mock_execute):
        docker = Docker()
        docker.start()
        path = 'path'
        self.assertRaisesRegexp(
            DockerWrapperBaseError,
            unknown_error_result.err,
            docker.list_files,
            path
        )

    @mock.patch('docker.manager.execute')
    @mock.patch('docker.manager.Docker.run', return_value=unknown_error_result)
    def test_list_directories_unknown_error(self, mock_run, mock_execute):
        docker = Docker()
        docker.start()
        path = 'path'
        self.assertRaisesRegexp(
            DockerWrapperBaseError,
            unknown_error_result.err,
            docker.list_directories,
            path
        )


class DockerInteractionTests(unittest.TestCase):
    def setUp(self):
        self.docker = Docker()
        self.docker.start()

    def tearDown(self):
        self.docker.stop()

    def test_list_files(self):
        self.docker.run('touch file1')
        self.docker.run('touch file2')
        self.assertEqual(self.docker.list_files(''), ['file1', 'file2'])

    def test_list_files_bad_path(self):
        path = '/bad/path'
        self.assertRaisesRegexp(
            DockerFileNotFoundError,
            'Could not find the file or directory at path {0}'.format(path),
            self.docker.list_files,
            path
        )

    def test_list_directories(self):
        self.docker.run('mkdir dir1')
        self.docker.run('mkdir dir1/test')
        self.docker.run('mkdir dir2')
        self.docker.run('mkdir dir3')
        self.assertEqual(
            self.docker.list_directories('', include_trailing_slash=False),
            ['dir1', 'dir2', 'dir3']
        )

    def test_list_directories_trailing_slash(self):
        self.docker.run('mkdir dir1')
        self.docker.run('mkdir dir1/test')
        self.docker.run('mkdir dir2')
        self.docker.run('mkdir dir3')
        self.assertEqual(
            self.docker.list_directories('', include_trailing_slash=True),
            ['dir1/', 'dir2/', 'dir3/']
        )

    def test_list_directories_bad_path(self):
        path = '/bad/path'
        self.assertRaisesRegexp(
            DockerFileNotFoundError,
            'Could not find the file or directory at path {0}'.format(path),
            self.docker.list_directories,
            path
        )

    def test_create_and_list_files_in_sub_directory(self):
        self.docker.run('mkdir builds')
        self.docker.run('touch builds/readme.txt')

        self.assertEqual(self.docker.list_files('builds'), ['readme.txt'])

    def test_read_file_with_content(self):
        file_name = 'readme.txt'
        file_content = 'this is a test file {0}\n'.format(randint(5000, 5500))
        self.docker.write_file(file_name, file_content)
        self.assertEqual(self.docker.read_file(file_name), file_content)

    def test_read_file_that_dont_exist(self):
        path = '/bad/path'
        self.assertRaisesRegexp(
            DockerFileNotFoundError,
            'Could not find the file or directory at path {0}'.format(path),
            self.docker.read_file,
            path
        )

    def test_read_file_eof_newline(self):
        path = '/etc/hostname'
        content = self.docker.read_file(path)
        self.assertTrue(content.endswith('\n'))

    def test_write_file_read_file(self):
        path = 'testfile'
        content = 'this is a nice file\n'
        self.docker.write_file(path, content)
        self.assertEqual(content, self.docker.read_file(path))

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
        self.assertEqual(result.out,
                         'ls: cannot access does-not-exist: No such file or directory\n')

    def test_privilege(self):
        Docker(privilege=True).start()

    def test_write_file_append(self):
        path = 'readme.txt'
        old_content = 'hi\n'
        content = 'this is a readme\n'
        self.docker.run('echo "{0}" > {1}'.format(old_content, path))

        self.docker.write_file(path, content, append=True)
        written_content = self.docker.read_file(path)
        self.assertEqual(written_content, '{0}\n{1}'.format(old_content, content))

    def test_write_file_no_append(self):
        path = 'readme.txt'
        old_content = 'hi'
        content = 'this is a readme\n'
        self.docker.run('echo "{0}" > {1}'.format(old_content, path))

        self.docker.write_file(path, content, append=False)
        written_content = self.docker.read_file(path)
        self.assertEqual(written_content, content)

    def test_write_file_quotes(self):
        path = 'readme.txt'
        content = 'this is a "readme"\n'

        self.docker.write_file(path, content, append=False)
        written_content = self.docker.read_file(path)
        self.assertEqual(written_content, content)

    def test_run_return_code(self):
        code = 4
        path = 'testfile'
        content = 'exit {0}\n'.format(code)
        self.docker.write_file(path, content)
        result = self.docker.run('bash {0}'.format(path))
        self.assertEqual(code, result.return_code)
