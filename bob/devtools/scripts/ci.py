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
  pass


@ci.command(epilog='''
Examples:

  1. Deploys base build artifacts (dependencies) to the appropriate channels:

     $ bdt ci base-deploy -vv

''')
@click.option('-d', '--dry-run/--no-dry-run', default=False,
    help='Only goes through the actions, but does not execute them ' \
        '(combine with the verbosity flags - e.g. ``-vvv``) to enable ' \
        'printing to help you understand what will be done')
@verbosity_option()
@bdt.raise_on_error
def base_deploy(dry_run):
    """Deploys dependencies not available at the defaults channel

    Deployment happens to our public channel directly, as these are
    dependencies are required for proper bob/beat package runtime environments.
    """

    if dry_run:
        logger.warn('!!!! DRY RUN MODE !!!!')
        logger.warn('Nothing is being deployed to server')

    package = os.environ['CI_PROJECT_PATH']

    from ..constants import WEBDAV_PATHS
    server_info = WEBDAV_PATHS[True][True]  #stable=True, visible=True

    logger.info('Deploying dependence packages to %s%s%s...', SERVER,
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
      # finds conda dependencies and uploads what we can find
      package_path = os.path.join(os.environ['CONDA_ROOT'], 'conda-bld', arch,
          '*.tar.bz2')
      deploy_packages = glob.glob(package_path)
      for k in deploy_packages:
        basename = os.path.basename(k)
        if basename.startswith(name):
          logger.debug('Skipping deploying of %s - not a base package', k)
          continue

        remote_path = '%s/%s/%s' % (server_info['conda'], arch, basename)
        if davclient.check(remote_path):
          raise RuntimeError('The file %s/%s already exists on the server ' \
              '- this can be due to more than one build with deployment ' \
              'running at the same time.  Re-running the broken builds ' \
              'normally fixes it' % (SERVER, remote_path))
        logger.info('[dav] %s -> %s%s%s', k, SERVER, server_info['root'],
            remote_path)
        if not dry_run:
          davclient.upload(local_path=k, remote_path=remote_path)


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

    # determine if building branch or tag
    stable = ('CI_COMMIT_TAG' in os.environ)

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

  1. Checks the long description of setup.py (correctly parseable and will
     display nicely at PyPI).  Notice this step requires the zip python
     packages:

     $ bdt ci readme -vv dist/*.zip

''')
@click.argument('package', required=True, type=click.Path(file_okay=True,
  dir_okay=False, exists=True), nargs=-1)
@verbosity_option()
@bdt.raise_on_error
def readme(package):
    """Checks setup.py's ``long_description`` syntax

    This program checks the syntax of the contents of the ``long_description``
    field at the package's ``setup()`` function.  It verifies it will be
    correctly displayed at PyPI.
    """

    for k in package:

      logger.info('Checking python package %s', k)
      #twine check dist/*.zip

      from twine.commands.check import check
      failed = check([k])

      if failed:
        raise RuntimeError('twine check (a.k.a. readme check) %s: FAILED' % k)
      else:
        logger.info('twine check (a.k.a. readme check) %s: OK', k)

@ci.command(epilog='''
Examples:

  1. Deploys current build artifacts to the Python Package Index (PyPI):

     $ bdt ci pypi -vv dist/*.zip

''')
@click.argument('package', required=True, type=click.Path(file_okay=True,
  dir_okay=False, exists=True), nargs=-1)
@click.option('-d', '--dry-run/--no-dry-run', default=False,
    help='Only goes through the actions, but does not execute them ' \
        '(combine with the verbosity flags - e.g. ``-vvv``) to enable ' \
        'printing to help you understand what will be done')
@verbosity_option()
@bdt.raise_on_error
def pypi(package, dry_run):
    """Deploys build artifacts (python packages to PyPI)

    Deployment is only allowed for packages in which the visibility is
    "public".  This check prevents publishing of private resources to the
    (public) PyPI webserver.
    """

    if dry_run:
        logger.warn('!!!! DRY RUN MODE !!!!')
        logger.warn('Nothing is being deployed to server')

    # determine project visibility
    visible = (os.environ['CI_PROJECT_VISIBILITY'] == 'public')

    if not visible:
      raise RuntimeError('The repository %s is not public - a package ' \
          'deriving from it therefore, CANNOT be published to PyPI. ' \
          'You must follow the relevant software disclosure procedures ' \
          'and set this repository to "public" before trying again.' % \
          os.environ['CI_PROJECT_PATH'])

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

      for k in package:

        logger.info('Deploying python package %s to PyPI', k)
        upload(settings, [k])
        logger.info('%s: Deployed to PyPI - OK', k)


@ci.command(epilog='''
Examples:

  1. Builds a list of packages (base dependencies) defined in a text file

     $ bdt ci base-build -vv order.txt

''')
@click.argument('order', required=True, type=click.Path(file_okay=True,
  dir_okay=False, exists=True), nargs=1)
@click.option('-d', '--dry-run/--no-dry-run', default=False,
    help='Only goes through the actions, but does not execute them ' \
        '(combine with the verbosity flags - e.g. ``-vvv``) to enable ' \
        'printing to help you understand what will be done')
@verbosity_option()
@bdt.raise_on_error
def base_build(order, dry_run):
  """Builds base (dependence) packages

  This command builds dependence packages (packages that are not Bob/BEAT
  packages) in the CI infrastructure.  It is **not** meant to be used outside
  this context.
  """

  from ..constants import CONDA_BUILD_CONFIG
  from ..build import base_build as _build

  condarc = os.path.join(os.environ['CONDA_ROOT'], 'condarc')
  logger.info('Loading (this build\'s) CONDARC file from %s...', condarc)
  with open(condarc, 'rb') as f:
    condarc_options = yaml.load(f)

  # dump packages at conda_root
  condarc_options['croot'] = os.path.join(os.environ['CONDA_ROOT'],
      'conda-bld')

  # loads dirnames from order file (accepts # comments and empty lines)
  recipes = []
  with open(order, 'rt') as f:
    for line in f:
      line = line.partition('#')[0].strip()
      if line: recipes.append(line)

  for recipe in recipes:
    if not os.path.exists(os.path.join(recipe, 'meta.yaml')):
      # ignore - not a conda package
      continue
    base_build(SERVER, True, recipe, CONDA_BUILD_CONFIG,
        os.environ['PYTHON_VERSION'], args.python_version, condarc_options)


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


@ci.command(epilog='''
Examples:

  1. Cleans the current build (and prints what it cleans)

     $ bdt ci clean -vv

''')
@verbosity_option()
@bdt.raise_on_error
@click.pass_context
def clean(ctx):
  """Cleans builds

  This command cleans builds in the CI infrastructure.  It is **not** meant
  to be used outside this context.
  """

  from ..build import git_clean_build
  from ..bootstrap import run_cmdline

  git_clean_build(run_cmdline, verbose=(ctx.meta['verbosity']>=3))
