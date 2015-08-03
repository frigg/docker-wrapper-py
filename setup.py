# -*- coding: utf8 -*-
import re
import sys
from setuptools import setup, find_packages


def _read_long_description():
    try:
        import pypandoc
        return pypandoc.convert('README.md', 'rst', format='markdown')
    except Exception:
        return None

with open('docker/__init__.py', 'r') as fd:
    version = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
        fd.read(),
        re.MULTILINE
    ).group(1)

try:
    from semantic_release import setup_hook
    setup_hook(sys.argv)
except ImportError:
    pass

setup(
    name='docker-wrapper',
    version=version,
    url='http://github.com/frigg/docker-wrapper-py',
    author='Fredrik Carlsen',
    author_email='fredrik@carlsen.io',
    description='Docker Wrapper for Python',
    long_description=_read_long_description(),
    packages=find_packages(exclude='tests'),
    license='MIT',
    test_suite='runtests.runtests',
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Operating System :: OS Independent',
        'Natural Language :: English',
    ]
)
