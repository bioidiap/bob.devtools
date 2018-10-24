#!/usr/bin/env python
"""A package that contains tools to maintain Bob
"""

from setuptools import setup, find_packages

# Define package version
version = open("version.txt").read().rstrip()

setup(
    name="bob_tools",
    version=version,
    description="Tools to maintain Bob packages",
    url='http://gitlab.idiap.ch/bob/bob_tools',
    license="BSD",
    author='Bob Developers',
    author_email='bob-devel@googlegroups.com',
    long_description=open('README.rst').read(),

    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,

    # when updating these dependencies, update the README too
    install_requires=['setuptools', 'click', 'click-plugins', 'conda_build'],

    entry_points={
        'console_scripts': [
            'bob-tools = bob_tools.scripts.main:main',
        ],
        'bob_tools.cli': [
            'cb-output = bob_tools.scripts.cb_output:cb_output',
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
