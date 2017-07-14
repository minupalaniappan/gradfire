#!/usr/bin/env python

from setuptools import setup, find_packages

install_requires=['psycopg2', 'eventlet', 'flask']

setup(name='daviscoursesearch',
      version='0.1',
      description='Search engine for UC Davis',
      author='Andy Haden',
      author_email='achaden@ucdavis.edu',
      install_requires=install_requires,
      packages=find_packages(),
      zip_safe=False
     )
