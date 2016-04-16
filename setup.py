#!/usr/bin/env python
# encoding: utf-8

from setuptools import setup

import re


def get_version():
      with open(u'klag/__version__.py') as version_file:
            return re.search(r"""__version__\s+=\s+(['"])(?P<version>.+?)\1""",
                 version_file.read()).group(u'version')

setup(name=u'klag',
      description=u'A Kafka consumer monitoring CLI.',
      author=u'Andrew Carter',
      author_email=u'andrew.k.carter@gmail.com',
      url=u'https://github.com/andrewkcarter/klag',
      keywords=[u'kafka'],
      license=u'MIT',
      version=get_version(),
      packages=[u'klag'],
      scripts=[u'scripts/klag'],
      install_requires=[u'kafka-python>=1.0.2'],
      )
