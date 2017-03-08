#!/usr/bin/env python

'''
@copyright: (c) 2014 SynergyLabs
@license:   UCSD License. See License file for details.
'''

'''The setup and build script for the python-building-depot 2.0 library.'''

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

__author__ = 'SynergyLabs'
__version__ = '0.2'

setup(
    name="python-building-depot",
    version=__version__,
    packages=['building_depot'],
    author=__author__,
    description='A Python wrapper around the Building Depot 2.0 API',
    zip_safe=False,
    install_requires=['setuptools', 'requests', ],
    include_package_data=True,
    classifiers=(
        'Development Status :: 1 - Planning'
        'Intended Audience :: Developers',
    ),
    test_suite='building_depot_test.suite',
)
