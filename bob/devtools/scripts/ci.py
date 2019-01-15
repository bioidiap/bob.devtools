#!/usr/bin/env python

import os
import re
import glob
import logging
logger = logging.getLogger(__name__)

import click
import pkg_resources
from click_plugins import with_plugins

from . import bdt
from ..log import verbosity_option
from ..ci import is_stable, is_visible_outside
from ..constants import SERVER, WEBDAV_PATHS
from ..webdav3 import client as webdav


@with_plugins(pkg_resources.iter_entry_points('bdt.ci.cli'))
@click.group(cls=bdt.AliasedGroup)
def ci():
  """Commands for building packages and handling CI activities

  Commands defined here are supposed to run on our CI, where a number of
  variables that define their behavior is correctly defined.  Do **NOT**
  attempt to run these commands in your own installation.  Unexpected errors
  may occur.
  """
  pass


@ci.command(epilog='''
Examples:

  1. Deploys current build artifacts to the appropriate channels:

     $ bdt ci deploy -vv

''')
@click.option('-d', '--dry-run/--no-dry-run', default=False,
    help='Only goes through the actions, but does not execute them ' \
        '(combine with the verbosity flags - e.g. ``-vvv``) to enable ' \
        'printing to help you understand what will be done')
@verbosity_option()
@bdt.raise_on_error
def deploy(dry_run):
    """Deploys build artifacts (conda packages and sphinx documentation)

    Deployment happens at the "right" locations - conda packages which do not
    represent stable releases are deployed to our conda "beta" channel, while
    stable packages to our root channel.  Sphinx documentation from unstable
    builds (typically the master branch) is deployed to the documentation
    server in a subdirectory named after the current branch name, while stable
    documentation is deployed to a special subdirectory named "stable" and to
    the respective tag name.
    """

    if dry_run:
        logger.warn('!!!! DRY RUN MODE !!!!')
        logger.warn('Nothing is being deployed to server')

    package = os.environ['CI_PROJECT_PATH']

    # determine project visibility
    visible = is_visible_outside(package, os.environ['CI_PROJECT_VISIBILITY'])

    # determine if building master branch or tag - and if tag is on master
    tag = os.environ.get('CI_COMMIT_TAG')
    stable = is_stable(package, os.environ['CI_COMMIT_REF_NAME'], tag)

    server_info = WEBDAV_PATHS[stable][visible]

    logger.info('Deploying conda packages to %s%s%s...', SERVER,
        server_info['root'], server_info['conda'])

    # setup webdav connection
    webdav_options = {
        'webdav_hostname': SERVER,
        'webdav_root': server_info['root'],
        'webdav_login': os.environ['DOCUSER'],
        'webdav_password': os.environ['DOCPASS'],
        }
    davclient = webdav.Client(webdav_options)
    assert davclient.valid()

    group, name = package.split('/')

    # uploads conda package artificats
    for arch in ('linux-64', 'osx-64', 'noarch'):
      # finds conda packages and uploads what we can find
      package_path = os.path.join(os.environ['CONDA_ROOT'], 'conda-bld', arch,
          name + '*.tar.bz2')
      deploy_packages = glob.glob(package_path)
      for k in deploy_packages:
        remote_path = '%s%s/%s/%s' % (server_info['root'],
            server_info['conda'], arch, os.path.basename(k))
        if davclient.check(remote_path):
          raise RuntimeError('The file %s/%s already exists on the server ' \
              '- this can be due to more than one build with deployment ' \
              'running at the same time.  Re-running the broken builds ' \
              'normally fixes it' % (SERVER, remote_path))
        logger.info('[dav] %s -> %s%s', k, SERVER, remote_path)
        if not dry_run:
          davclient.upload(local_path=k, remote_path=remote_path)

    # uploads documentation artifacts
    local_docs = os.path.join(os.environ['CI_PROJECT_DIR'], 'sphinx')
    if not os.path.exists(local_docs):
      raise RuntimeError('Documentation is not available at %s - ' \
          'ensure documentation is being produced for your project!' % \
          local_docs)

    remote_path_prefix = '%s%s/%s' % (server_info['root'], server_info['docs'],
        package)

    # finds out the correct mixture of sub-directories we should deploy to.
    # 1. if ref-name is a tag, don't forget to publish to 'master' as well -
    # all tags are checked to come from that branch
    # 2. if ref-name is a branch name, deploy to it
    # 3. in case a tag is being published, make sure to deploy to the special
    # "stable" subdir as well
    deploy_docs_to = set([os.environ['CI_COMMIT_REF_NAME']])
    if stable:
      deploy_docs_to.add('master')
      if os.environ.get('CI_COMMIT_TAG') is not None:
        deploy_docs_to.add(os.environ['CI_COMMIT_TAG'])
      deploy_docs_to.add('stable')

    for k in deploy_docs_to:
      remote_path = '%s/%s' % (remote_path_prefix, k)
      logger.info('[dav] %s -> %s%s', local_docs, SERVER, remote_path)
      if not dry_run:
        client.upload_directory(local_path=local_docs, remote_path=remote_path)
