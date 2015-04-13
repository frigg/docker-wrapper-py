import unittest
from random import randint

from docker.manager import Docker

try:
    from unittest import mock
except ImportError:
    import mock


class DockerBasicInteractionTests(unittest.TestCase):

    def test_create_files(self):
        with Docker() as docker:
            docker.run('touch file1')
            docker.run('touch file2')
            self.assertEqual(docker.list_files(''), ['file1', 'file2'])

    def test_create_directories(self):
        with Docker() as docker:
            docker.run('mkdir dir1')
            docker.run('mkdir dir1/test')
            docker.run('mkdir dir2')
            docker.run('mkdir dir3')
            self.assertEqual(
                docker.list_directories('', include_trailing_slash=False),
                ['dir1', 'dir2', 'dir3']
            )

    def test_create_and_list_files_in_sub_directory(self):
        with Docker() as docker:
            docker.run('mkdir builds')
            docker.run('touch builds/readme.txt')

            self.assertEqual(docker.list_files('builds'), ['readme.txt'])

    def test_create_file_with_content(self):
        with Docker() as docker:
            file_name = 'readme.txt'
            file_content = 'this is a test file'

            self.assertFalse(docker.file_exist(file_name))
            docker.create_file(file_name, file_content)
            self.assertTrue(docker.file_exist(file_name))

    def test_read_file_with_content(self):
        with Docker() as docker:
            file_name = 'readme.txt'
            file_content = 'this is a test file {0}'.format(randint(5000, 5500))
            docker.create_file(file_name, file_content)

            self.assertEqual(docker.read_file(file_name), file_content)

    def test__get_working_directory(self):
        self.assertEqual(Docker._get_working_directory('directory'), '~/directory')
        self.assertEqual(Docker._get_working_directory('/absolute/path'), '/absolute/path')

    @mock.patch('docker.manager.Docker.stop')
    @mock.patch('docker.manager.Docker.start')
    def test_with_statement(self, mock_start, mock_stop):
        with Docker() as docker:
            self.assertIsInstance(docker, Docker)

        mock_start.assert_called_once_with()
        mock_stop.assert_called_once_with()

    @mock.patch('docker.manager.Docker.stop')
    @mock.patch('docker.manager.Docker.start')
    def test_wrap(self, mock_start, mock_stop):
        @Docker.wrap()
        def wrapped(docker):
            self.assertIsInstance(docker, Docker)

        wrapped()
        mock_start.assert_called_once_with()
        mock_stop.assert_called_once_with()
