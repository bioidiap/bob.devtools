#!/usr/bin/env python

from setuptools import setup, find_packages

# Define package version
version = open("version.txt").read().rstrip()

requires = [
    'setuptools',
    'click',
    'click-plugins',
    'conda-build',
    'requests',
    'gitpython',
    'python-gitlab',
    ]

setup(
    name="bob.devtools",
    version=version,
    description="Tools for development and CI integration of Bob packages",
    url='http://gitlab.idiap.ch/bob/bob.devtools',
    license="BSD",
    author='Bob Developers',
    author_email='bob-devel@googlegroups.com',
    long_description=open('README.rst').read(),

    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,

    # when updating these dependencies, update the README too
    install_requires=requires,

    entry_points={
        'console_scripts': [
            'bdt = bob.devtools.scripts.bdt:main',
        ],
        'bdt.cli': [
            'cb-output = bob.devtools.scripts.cb_output:cb_output',
            'release = bob.devtools.scripts.release:release',
            'changelog = bob.devtools.scripts.changelog:changelog',
            'lasttag = bob.devtools.scripts.lasttag:lasttag',
        ],
    },
    classifiers=[
        'Framework :: Bob',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
