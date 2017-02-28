#!/usr/bin/env python

import os
import sys

import setuptools


# Utility function to read the README file
def readfile(filename):
    with open(filename) as f:
        return f.read()


# Utility function to read requirements.txt files
def readreq(filename):
    result = []
    with open(filename) as f:
        for line in f:
            line = line.strip()

            # Process requirement file references
            if line.startswith('-r '):
                subfilename = line.split(None, 1)[-1].split('#', 1)[0].strip()
                if subfilename:
                    result += readreq(subfilename)
                continue

            # Strip out "-e" prefixes
            if line.startswith('-e '):
                line = line.split(None, 1)[-1]

            # Detect URLs in the line
            idx = line.find('#egg=')
            if idx >= 0:
                line = line[idx + 5:]

            # Strip off any comments
            line = line.split('#', 1)[0].strip()

            # Save the requirement
            if line:
                result.append(line.split('#', 1)[0].strip())

    return result


# Invoke setup
setuptools.setup(
    name='hypocrite',
    version='0.0.1',
    author='Kevin L. Mitchell',
    author_email='klmitch@mit.edu',
    url='https://github.com/klmitch/hypocrite',
    description='C Unit Test Generator',
    long_description=readfile('README.rst'),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: C',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Testing',
    ],
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    install_requires=readreq('requirements.txt'),
    tests_require=readreq('test-requirements.txt'),
    entry_points={
        'console_scripts': [
            'hypocrite = hypocrite.main:main.console',
        ],
    },
)
