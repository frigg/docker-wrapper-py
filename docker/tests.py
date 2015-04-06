import unittest
from random import randint
from manager import Docker


class DockerBasicInteraction(unittest.TestCase):
    def test_create_files(self):
        with Docker() as docker:
            docker.run("touch file1")
            docker.run("touch file2")
            self.assertEqual(docker.list_files(""), ["file1", "file2"])

    def test_create_directories(self):
        with Docker() as docker:
            docker.run("mkdir dir1")
            docker.run("mkdir dir1/test")
            docker.run("mkdir dir2")
            docker.run("mkdir dir3")
            self.assertEqual(docker.list_directories("", include_trailing_slash=False),
                             ["dir1", "dir2", "dir3"])

    def test_create_and_list_files_in_sub_directory(self):
        with Docker() as docker:
            docker.run("mkdir builds")
            docker.run("touch builds/readme.txt")

            self.assertEqual(docker.list_files("builds"), ["readme.txt"])

    def test_create_file_with_content(self):
        with Docker() as docker:
            file_name = "readme.txt"
            file_content = "this is a test file"

            self.assertFalse(docker.file_exist(file_name))
            docker.create_file(file_name, file_content)
            self.assertTrue(docker.file_exist(file_name))

    def test_read_file_with_content(self):
        with Docker() as docker:
            file_name = "readme.txt"
            file_content = "this is a test file {0}".format(randint(5000, 5500))
            docker.create_file(file_name, file_content)

            self.assertEqual(docker.read_file(file_name), file_content)


if __name__ == '__main__':
    unittest.main()
