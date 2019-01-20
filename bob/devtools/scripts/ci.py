#!/usr/bin/env python

import os
import re
import glob
import logging
logger = logging.getLogger(__name__)

import yaml
import click
import pkg_resources
import conda_build.api
from click_plugins import with_plugins

from . import bdt
from ..log import verbosity_option
from ..constants import SERVER


@with_plugins(pkg_resources.iter_entry_points('bdt.ci.cli'))
@click.group(cls=bdt.AliasedGroup)
def ci():
  """Commands for building packages and handling CI activities

  Commands defined here are supposed to run on our CI, where a number of
  variables that define their behavior is correctly defined.  Do **NOT**
  attempt to run these commands in your own installation.  Unexpected errors
  may occur.
  """
  # ensure messages don't get garbled at the output on the CI logs
  from ..bootstrap import set_environment
  set_environment('PYTHONUNBUFFERED', '1', os.environ)


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
    visible = (os.environ['CI_PROJECT_VISIBILITY'] == 'public')

    # determine if building master branch or tag - and if tag is on master
    from ..ci import is_stable
    stable = is_stable(package,
        os.environ['CI_COMMIT_REF_NAME'],
        os.environ.get('CI_COMMIT_TAG'),
        os.environ['CI_PROJECT_DIR'])

    from ..constants import WEBDAV_PATHS
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
    from ..webdav3 import client as webdav
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
        remote_path = '%s/%s/%s' % (server_info['conda'], arch,
            os.path.basename(k))
        if davclient.check(remote_path):
          raise RuntimeError('The file %s/%s already exists on the server ' \
              '- this can be due to more than one build with deployment ' \
              'running at the same time.  Re-running the broken builds ' \
              'normally fixes it' % (SERVER, remote_path))
        logger.info('[dav] %s -> %s%s%s', k, SERVER, server_info['root'],
            remote_path)
        if not dry_run:
          davclient.upload(local_path=k, remote_path=remote_path)

    # uploads documentation artifacts
    local_docs = os.path.join(os.environ['CI_PROJECT_DIR'], 'sphinx')
    if not os.path.exists(local_docs):
      raise RuntimeError('Documentation is not available at %s - ' \
          'ensure documentation is being produced for your project!' % \
          local_docs)

    remote_path_prefix = '%s/%s' % (server_info['docs'], package)

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
      logger.info('[dav] %s -> %s%s%s', local_docs, SERVER,
          server_info['root'], remote_path)
      if not dry_run:
        davclient.upload_directory(local_path=local_docs,
            remote_path=remote_path)


@ci.command(epilog='''
Examples:

  1. Deploys current build artifacts to the Python Package Index (PyPI):

     $ bdt ci pypi -vv

''')
@click.option('-d', '--dry-run/--no-dry-run', default=False,
    help='Only goes through the actions, but does not execute them ' \
        '(combine with the verbosity flags - e.g. ``-vvv``) to enable ' \
        'printing to help you understand what will be done')
@verbosity_option()
@bdt.raise_on_error
def pypi(dry_run):
    """Deploys build artifacts (python packages to PyPI)

    Deployment is only allowed for packages in which the visibility is
    "public".  This check prevents publishing of private resources to the
    (public) PyPI webserver.
    """

    if dry_run:
        logger.warn('!!!! DRY RUN MODE !!!!')
        logger.warn('Nothing is being deployed to server')

    package = os.environ['CI_PROJECT_PATH']

    # determine project visibility
    visible = (os.environ['CI_PROJECT_VISIBILITY'] == 'public')

    if not visible:
      raise RuntimeError('The repository %s is not public - a package ' \
          'deriving from it therefore, CANNOT be published to PyPI. ' \
          'You must follow the relevant software disclosure procedures ' \
          'and set this repository to "public" before trying again.' % package)

    # finds the package that should be published
    zip_glob = os.path.join(os.environ['CI_PROJECT_DIR'], 'dist', '*-*.zip')
    zip_files = glob.glob(zip_glob)

    if len(zip_files) == 0:
      raise RuntimeError('Cannot find .zip files on the "dist" directory')

    if len(zip_files) > 1:
      raise RuntimeError('There are %d .zip files on the "dist" directory: ' \
          '%s - I\'m confused on what to publish to PyPI...' % \
          (len(zip_files), ', '.join(zip_files)))

    logger.info('Deploying python package %s to PyPI', zip_files[0])
    #twine upload --skip-existing --username ${PYPIUSER} --password ${PYPIPASS}
    #dist/*.zip
    from ..constants import CACERT
    from twine.settings import Settings

    settings = Settings(
        username=os.environ['PYPIUSER'],
        password=os.environ['PYPIPASS'],
        skip_existing=True,
        cacert=CACERT,
        )

    if not dry_run:
      from twine.commands.upload import upload
      upload(settings, zip_files)
      logger.info('Deployment to PyPI successful')


@ci.command(epilog='''
Examples:

  1. Builds the current package

     $ bdt ci build -vv

''')
@click.option('-d', '--dry-run/--no-dry-run', default=False,
    help='Only goes through the actions, but does not execute them ' \
        '(combine with the verbosity flags - e.g. ``-vvv``) to enable ' \
        'printing to help you understand what will be done')
@verbosity_option()
@bdt.raise_on_error
@click.pass_context
def build(ctx, dry_run):
  """Builds packages

  This command builds packages in the CI infrastructure.  It is **not** meant
  to be used outside this context.
  """

  from ..constants import CONDA_BUILD_CONFIG, CONDA_RECIPE_APPEND
  from ..build import git_clean_build
  from ..bootstrap import run_cmdline

  from .build import build
  ctx.invoke(build,
      recipe_dir=[os.path.join(os.path.realpath(os.curdir), 'conda')],
      python=os.environ['PYTHON_VERSION'],  #python version
      condarc=None,  #custom build configuration
      config=CONDA_BUILD_CONFIG,
      no_test=False,
      append_file=CONDA_RECIPE_APPEND,
      server=SERVER,
      private=(os.environ['CI_PROJECT_VISIBILITY'] != 'public'),
      stable='CI_COMMIT_TAG' in os.environ,
      dry_run=dry_run,
      ci=True,
      )

  git_clean_build(run_cmdline, arch)
