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
from ..ci import is_stable, is_visible_outside
from ..webdav3 import client as webdav

from ..constants import SERVER, WEBDAV_PATHS, CACERT, CONDA_BUILD_CONFIG, \
    CONDA_RECIPE_APPEND, MATPLOTLIB_RCDIR, BASE_CONDARC
from ..build import next_build_number, conda_arch, should_skip_build, \
    get_rendered_metadata, get_parsed_recipe, make_conda_config, \
    get_docserver_setup, check_version, git_clean_build
from ..bootstrap import set_environment, get_channels, run_cmdline


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
    visible = is_visible_outside(package, os.environ['CI_PROJECT_VISIBILITY'])

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
def build(dry_run):
  """Builds packages

  This command builds packages in the CI infrastructure.  It is **not** meant
  to be used outside this context.
  """

  if dry_run:
      logger.warn('!!!! DRY RUN MODE !!!!')
      logger.warn('Nothing is being built')

  prefix = os.environ['CONDA_ROOT']
  logger.info('os.environ["%s"] = %s', 'CONDA_ROOT', prefix)

  workdir = os.environ['CI_PROJECT_DIR']
  logger.info('os.environ["%s"] = %s', 'CI_PROJECT_DIR', workdir)

  name = os.environ['CI_PROJECT_NAME']
  logger.info('os.environ["%s"] = %s', 'CI_PROJECT_NAME', name)

  pyver = os.environ['PYTHON_VERSION']
  logger.info('os.environ["%s"] = %s', 'PYTHON_VERSION', pyver)

  set_environment('MATPLOTLIBRC', MATPLOTLIB_RCDIR, verbose=True)

  # get information about the version of the package being built
  version, is_prerelease = check_version(workdir,
      os.environ.get('CI_COMMIT_TAG'))
  set_environment('BOB_PACKAGE_VERSION', version, verbose=True)

  # setup BOB_DOCUMENTATION_SERVER environment variable (used for bob.extension
  # and derived documentation building via Sphinx)
  set_environment('DOCSERVER', SERVER, os.environ, verbose=True)
  public = ( os.environ['CI_PROJECT_VISIBILITY']=='public' )
  doc_urls = get_docserver_setup(public=public, stable=(not is_prerelease),
      server=SERVER, intranet=True)
  set_environment('BOB_DOCUMENTATION_SERVER', doc_urls, verbose=True)

  condarc = os.path.join(prefix, 'condarc')
  logger.info('Loading (this build\'s) CONDARC file from %s...', condarc)
  with open(condarc, 'rb') as f:
    condarc_options = yaml.load(f)

  # notice this condarc typically will only contain the defaults channel - we
  # need to boost this up with more channels to get it right.
  channels = get_channels(public=public, stable=(not is_prerelease),
      server=SERVER, intranet=True)
  logger.info('Using the following channels during build:\n  - %s',
      '\n  - '.join(channels + ['defaults']))
  condarc_options['channels'] = channels + ['defaults']

  # create the build configuration
  logger.info('Merging conda configuration files...')
  conda_config = make_conda_config(CONDA_BUILD_CONFIG, pyver,
      CONDA_RECIPE_APPEND, condarc_options)

  # retrieve the current build number for this build
  build_number, _ = next_build_number(channels[0], name, version, pyver)
  set_environment('BOB_BUILD_NUMBER', str(build_number), verbose=True)

  # runs the build using the conda-build API
  arch = conda_arch()
  logger.info('Building %s-%s-py%s (build: %d) for %s',
      name, version, pyver.replace('.',''), build_number, arch)

  if not dry_run:
    conda_build.api.build(os.path.join(workdir, 'conda'), config=conda_config)

  git_clean_build(run_cmdline, arch)
