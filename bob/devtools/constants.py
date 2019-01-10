#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Constants used for building and more'''

import os
import pkg_resources

import logging
logger = logging.getLogger(__name__)


CONDARC = pkg_resources.resource_filename(__name__,
    os.path.join('data', 'build-condarc'))
'''The .condarc to use for building and creating new environments'''

CONDA_BUILD_CONFIG = pkg_resources.resource_filename(__name__,
    os.path.join('data', 'conda_build_config.yaml'))
'''Configuration variants we like building'''

CONDA_RECIPE_APPEND = pkg_resources.resource_filename(__name__,
    os.path.join('data', 'recipe_append.yaml'))
'''Extra information to be appended to every recipe upon building'''

SERVER = 'http://www.idiap.ch'
'''This is the default server use use to store data and build artifacts'''

CACERT = pkg_resources.resource_filename(__name__,
    os.path.join('data', 'cacert.pem'))
'''We keep a copy of the CA certificates we trust here

   To update this file use: ``curl --remote-name --time-cond cacert.pem https://curl.haxx.se/ca/cacert.pem``

   More information here: https://curl.haxx.se/docs/caextract.html
'''

MATPLOTLIB_RCDIR = pkg_resources.resource_filename(__name__, 'data')
'''Base directory where the file matplotlibrc lives

It is required for certain builds that use matplotlib functionality.
'''


def set_environment(name, value, env=os.environ):
    '''Function to setup the environment variable and print debug message

    Args:

      name: The name of the environment variable to set
      value: The value to set the environment variable to
      env: Optional environment (dictionary) where to set the variable at
    '''

    if name in env:
      logger.warn('Overriding existing environment variable ${%s} (was: "%s")',
          name, env[name])
    env[name] = value
    logger.debug('$ export %s="%s"', name, value)
