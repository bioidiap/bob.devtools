#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
logger = logging.getLogger(__name__)

import yaml
import click
import pkg_resources
import conda_build.api

from . import bdt
from ..log import verbosity_option
from ..build import next_build_number, conda_arch, should_skip_build, \
    get_rendered_metadata, get_parsed_recipe, make_conda_config, \
    get_docserver_setup, get_env_directory
from ..constants import CONDA_BUILD_CONFIG, CONDA_RECIPE_APPEND, \
    SERVER, MATPLOTLIB_RCDIR, BASE_CONDARC
from ..bootstrap import set_environment, get_channels


@click.command(epilog='''
Examples:

  1. Builds recipe from one of our build dependencies (inside bob.conda):

\b
     $ cd bob.conda
     $ bdt build -vv conda/libblitz


  2. Builds recipe from one of our packages, for Python 3.6 (if that is not already the default for you):

     $ bdt build --python=3.6 -vv path/to/conda/dir


  3. To build multiple recipes, just pass the paths to them:

     $ bdt build --python=3.6 -vv path/to/recipe-dir1 path/to/recipe-dir2
''')
@click.argument('recipe-dir', required=False, type=click.Path(file_okay=False,
  dir_okay=True, exists=True), nargs=-1)
@click.option('-p', '--python', default=('%d.%d' % sys.version_info[:2]),
    show_default=True, help='Version of python to build the environment for')
@click.option('-r', '--condarc',
    help='Use custom conda configuration file instead of our own',)
@click.option('-m', '--config', '--variant-config-files', show_default=True,
    default=CONDA_BUILD_CONFIG, help='overwrites the path leading to ' \
        'variant configuration file to use')
@click.option('-n', '--no-test', is_flag=True,
    help='Do not test the package, only builds it')
@click.option('-a', '--append-file', show_default=True,
    default=CONDA_RECIPE_APPEND, help='overwrites the path leading to ' \
        'appended configuration file to use')
@click.option('-S', '--server', show_default=True,
    default='https://www.idiap.ch/software/bob', help='Server used for ' \
    'downloading conda packages and documentation indexes of required packages')
@click.option('-P', '--private/--no-private', default=False,
    help='Set this to **include** private channels on your build - ' \
        'you **must** be at Idiap to execute this build in this case - ' \
        'you **must** also use the correct server name through --server - ' \
        'notice this option has no effect if you also pass --condarc')
@click.option('-X', '--stable/--no-stable', default=False,
    help='Set this to **exclude** beta channels from your build - ' \
        'notice this option has no effect if you also pass --condarc')
@click.option('-d', '--dry-run/--no-dry-run', default=False,
    help='Only goes through the actions, but does not execute them ' \
        '(combine with the verbosity flags - e.g. ``-vvv``) to enable ' \
        'printing to help you understand what will be done')
@verbosity_option()
@bdt.raise_on_error
def build(recipe_dir, python, condarc, config, no_test, append_file,
    server, private, stable, dry_run):
  """Builds package through conda-build with stock configuration

  This command wraps the execution of conda-build so that you use the same
  conda configuration we use for our CI.  It always set
  ``--no-anaconda-upload``.

  Note that both files are embedded within bob.devtools - you may need to
  update your environment before trying this.
  """

  # if we are in a dry-run mode, let's let it be known
  if dry_run:
      logger.warn('!!!! DRY RUN MODE !!!!')
      logger.warn('Nothing will be really built')

  recipe_dir = recipe_dir or [os.path.join(os.path.realpath('.'), 'conda')]

  # get potential channel upload and other auxiliary channels
  channels = get_channels(public=(not private), stable=stable, server=server,
      intranet=private)

  if condarc is not None:
    logger.info('Loading CONDARC file from %s...', condarc)
    with open(condarc, 'rb') as f:
      condarc_options = yaml.load(f)
  else:
    # use default and add channels
    condarc_options = yaml.load(BASE_CONDARC)  #n.b.: no channels
    logger.info('Using the following channels during build:\n  - %s',
        '\n  - '.join(channels + ['defaults']))
    condarc_options['channels'] = channels + ['defaults']

  # dump packages at base environment
  prefix = get_env_directory(os.environ['CONDA_EXE'], 'base')
  condarc_options['croot'] = os.path.join(prefix, 'conda-bld')

  conda_config = make_conda_config(config, python, append_file,
      condarc_options)

  set_environment('MATPLOTLIBRC', MATPLOTLIB_RCDIR, verbose=True)

  # setup BOB_DOCUMENTATION_SERVER environment variable (used for bob.extension
  # and derived documentation building via Sphinx)
  set_environment('DOCSERVER', server, verbose=True)
  doc_urls = get_docserver_setup(public=(not private), stable=stable,
      server=server, intranet=private)
  set_environment('BOB_DOCUMENTATION_SERVER', doc_urls, verbose=True)

  for d in recipe_dir:

    if not os.path.exists(d):
      raise RuntimeError("The directory %s does not exist" % recipe_dir)

    version_candidate = os.path.join(d, '..', 'version.txt')
    if os.path.exists(version_candidate):
      version = open(version_candidate).read().rstrip()
      set_environment('BOB_PACKAGE_VERSION', version, verbose=True)

    # pre-renders the recipe - figures out package name and version
    metadata = get_rendered_metadata(d, conda_config)

    # checks we should actually build this recipe
    arch = conda_arch()
    if should_skip_build(metadata):
      logger.warn('Skipping UNSUPPORTED build of "%s" for py%s on %s',
          d, python.replace('.',''), arch)
      return 0

    # converts the metadata output into parsed yaml and continues the process
    rendered_recipe = get_parsed_recipe(metadata)

    # if a channel URL was passed, set the build number
    build_number, _ = next_build_number(channels[0],
        rendered_recipe['package']['name'],
        rendered_recipe['package']['version'], python)

    set_environment('BOB_BUILD_NUMBER', str(build_number), verbose=True)

    logger.info('Building %s-%s-py%s (build: %d) for %s',
        rendered_recipe['package']['name'],
        rendered_recipe['package']['version'], python.replace('.',''),
        build_number, arch)
    if not dry_run:
      conda_build.api.build(d, config=conda_config, notest=no_test)
