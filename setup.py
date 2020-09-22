#!/usr/bin/env python3

import sys
import numpy

if sys.version_info[0] < 3:
    sys.exit('Sorry, Python < 3.x is not supported')

# Try using setuptools first, if it's installed
from setuptools import setup, find_packages
from setuptools.extension import Extension

# Need to add all dependencies to setup as we go!
setup(name='hermes',
      packages=find_packages(),
      version='0.1',
      description="A stripped down, clean discord poll bot tailored for the classroom",
      long_description=open("README.md").read(),
      author='Michael J. Harms',
      author_email='harmsm@gmail.com',
      url='https://github.com/harmsm/hermes',
      download_url='https://github.com/hermes/tarball/0.1',
        entry_points={
            'console_scripts': ['hermes = hermes.hermes:main'],
        },
      zip_safe=False,
      install_requires=["matplotlib","discord"],
      classifiers=['Programming Language :: Python'])
