#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import configparser

from .log import get_logger
from .deploy import _setup_webdav_client

logger = get_logger(__name__)


def _get_config():
    """Returns a dictionary with server parameters, or ask them to the user"""

    # tries to figure if we can authenticate using a global configuration
    cfgs = ["~/.bdt-webdav.cfg"]
    cfgs = [os.path.expanduser(k) for k in cfgs]
    for k in cfgs:
        if os.path.exists(k):
            data = configparser.ConfigParser()
            data.read(k)
            if 'global' not in data or \
                'server' not in data['global'] or \
                'username' not in data['global'] or \
                'password' not in data['global']:
                assert KeyError, 'The file %s should contain a single ' \
                    '"global" section with 3 variables defined inside: ' \
                    '"server", "username", "password".' % (k,)
            return data['global']

    # ask the user for the information, cache credentials for future use
    retval = dict()
    retval['server'] = input("The base address of the server: ")
    retval['username'] = input("Username: ")
    retval['password'] = input("Password: ")

    # record file for the user
    data = configparser.ConfigParser()
    data['global'] = retval
    with open(cfgs[0], 'w') as f:
        logger.warn('Recorded "%s" configuration file for next queries')
        data.write(f)
    os.chmod(cfgs[0], 0o600)
    logger.warn('Changed mode of "%s" to be read-only to you')

    return retval


def setup_webdav_client(private):
    """Returns a ready-to-use WebDAV client"""

    config = _get_config()
    root = '/private-upload' if private else '/public-upload'
    c = _setup_webdav_client(config['server'], root, config['username'],
        config['password'])
    return c
