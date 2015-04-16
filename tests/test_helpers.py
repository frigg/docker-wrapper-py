# -*- coding: utf-8 -*-
import unittest

from docker.helpers import ProcessResult


class ProcessResultTest(unittest.TestCase):

    def test_succeeded(self):
        result = ProcessResult('tox')
        self.assertIsNone(result.succeeded)
        result.return_code = 0
        self.assertTrue(result.succeeded)
        result.return_code = 1
        self.assertFalse(result.succeeded)
        result.return_code = 127
        self.assertFalse(result.succeeded)
