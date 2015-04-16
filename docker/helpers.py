# -*- coding: utf-8 -*-
import logging
import subprocess

logger = logging.getLogger(__name__)


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


def execute(cmd):
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
