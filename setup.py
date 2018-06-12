#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import os
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Get the version
version_regex = r'__version__ = ["\']([^"\']*)["\']'
with open('pflow/__init__.py', 'r') as f:
    text = f.read()
    match = re.search(version_regex, text)

    if match:
        version = match.group(1)
    else:
        raise RuntimeError("No version number found!")

# Stealing this from Kenneth Reitz
if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

packages = [
    'pflow',
]

setup(
    name='pflow',
    version=version,
    description='Python Distributed Flow Debugger',
    author='Sudharsan R',
    packages=packages,
    package_dir={'pflow': 'pflow'},
    install_requires=[
        'confluent_kafka',
        'uvloop',
        'ujson',
        'sanic',
    ],
    #extras_require={
    #    ':python_version == "2.7" or python_version == "3.3"': ['enum34>=1.1.6, <2'],
    #}
)
