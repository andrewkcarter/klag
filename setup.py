#!/usr/bin/env python
# encoding: utf-8

from setuptools import setup

import re, os


def get_version():
    with open('klag/__version__.py') as version_file:
        return re.search(r"""__version__\s+=\s+(['"])(?P<version>.+?)\1""",
                         version_file.read()).group('version')

## Read in the README file:
with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

setup(name='klag',
      description='A Kafka consumer group monitoring CLI.',
      long_description=README,
      license='MIT',
      author='Andrew Carter',
      author_email='andrew.k.carter@gmail.com',
      url='https://github.com/andrewkcarter/klag',
      keywords=['kafka'],
      version=get_version(),
      packages=[
          'klag'
      ],
      scripts=[
          'scripts/klag'
      ],
      install_requires=[
          'kafka-python>=1.0.2'
      ],
      classifiers=[
          "Environment :: Console",
          "Intended Audience :: Developers",
          "Intended Audience :: System Administrators",
          "License :: OSI Approved :: MIT License",
          "Topic :: System",
          "Topic :: System :: Distributed Computing",
          "Topic :: System :: Logging",
          "Topic :: System :: Monitoring",
          "Topic :: System :: Systems Administration",
          "Topic :: Utilities"
      ])
