#!/usr/bin/env python
# encoding: utf-8

from setuptools import setup

import re


def get_version():
      with open('klag/__version__.py') as version_file:
            return re.search(r"""__version__\s+=\s+(['"])(?P<version>.+?)\1""",
                 version_file.read()).group('version')

setup(name='klag',
      description="Kafka consumer topic lag monitor.",
      author="Andrew Carter",
      author_email="andrew.k.carter@gmail.com",
      url="https://github.com/andrewkcarter/klag",
      keywords=['extraction', 'pipeline'],
      license='MIT',
      version=get_version(),
      packages=['klag'],
      scripts=['scripts/klag'],
      install_requires=['kafka-python>=1.0.2'],
      )
