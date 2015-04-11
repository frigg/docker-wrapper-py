# -*- coding: utf-8 -*-


class DockerUnavailableError(Exception):

    def __init__(self, message=None):
        super(DockerUnavailableError, self).__init__(message or 'Docker is not available')
