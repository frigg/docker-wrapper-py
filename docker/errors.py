# -*- coding: utf-8 -*-
FILE_NOT_FOUND_PREDICATE = 'No such file or directory'


class DockerWrapperBaseError(Exception):
    pass


class DockerUnavailableError(DockerWrapperBaseError):
    def __init__(self, message=None):
        super(DockerUnavailableError, self).__init__(message or 'Docker is not available')


class DockerFileNotFoundError(DockerWrapperBaseError):
    def __init__(self, path):
        message = 'Could not find the file or directory at path {0}'.format(path)
        super(DockerFileNotFoundError, self).__init__(message)
