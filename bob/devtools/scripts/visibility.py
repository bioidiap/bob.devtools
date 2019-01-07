#!/usr/bin/env python

import os
import sys

import click
import gitlab

import logging
logger = logging.getLogger(__name__)

from . import bdt
from ..log import verbosity_option
from ..release import get_gitlab_instance


@click.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True,
    ),
    epilog='''
Examples:

  1. Check the visibility of a package you can access

     $ bdt visibility bob/bob.extension


  2. Checks the visibility of all packages in a file list:

\b
     $ curl -o order.txt https://gitlab.idiap.ch/bob/bob.nightlies/raw/master/order.txt
     $ bdt visibility order.txt
''')
@click.argument('target')
@click.option('-g', '--group', default='bob', show_default=True,
    help='Gitlab default group name where packages are located (if not ' \
        'specified using a "/" on the package name - e.g. ' \
        '"bob/bob.extension")')
@verbosity_option()
@bdt.raise_on_error
def visibility(target, group):
    """Checks if the gitlab repository is visible to the current user

    This command checks if the named package is visible to the currently logged
    in user, and reports its visibility level ('public', 'internal',
    'private').  If the package does not exist or it is private to the current
    user, it says 'unknown' instead.
    """

    gl = get_gitlab_instance()

    # reads package list or considers name to be a package name
    if os.path.exists(target) and os.path.isfile(target):
        logger.info('Reading package names from file %s...', target)
        with open(target, 'rt') as f:
            packages = [k.strip() for k in f.readlines() if k.strip() and not \
                k.strip().startswith('#')]
    else:
        logger.info('Assuming %s is a package name (file does not ' \
            'exist)...', target)
        packages = [target]

    # iterates over the packages and dumps required information
    for package in packages:

        if '/' not in package:
            package = '/'.join((group, package))

        # retrieves the gitlab package object
        try:
          use_package = gl.projects.get(package)
          logger.info('Found gitlab project %s (id=%d)',
              use_package.attributes['path_with_namespace'], use_package.id)
          click.echo('%s: %s' % (package,
            use_package.attributes['visibility'].lower()))
        except gitlab.GitlabGetError as e:
          logger.warn('Gitlab access error - package %s does not exist?',
              package)
          click.echo('%s: unknown' % (package,))
