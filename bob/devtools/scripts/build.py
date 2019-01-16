#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
logger = logging.getLogger(__name__)

import pkg_resources
import click

from . import bdt
from ..log import verbosity_option
from ..conda import next_build_number, osname
from ..create import get_rendered_metadata, get_parsed_recipe, \
    make_conda_config
from ..constants import CONDARC, CONDA_BUILD_CONFIG, CONDA_RECIPE_APPEND, \
    SERVER, MATPLOTLIB_RCDIR, set_environment


@click.command(epilog='''
Examples:

  1. Builds recipe from one of our build dependencies (inside bob.conda):

     $ cd bob.conda
     $ bdt build -vv conda/libblitz


  2. Builds recipe from one of our packages, for Python 3.6 (if that is not
     already the default for you):

     $ bdt build --python=3.6 -vv path/to/conda/dir


  3. To build multiple recipes, just pass the paths to them:

     $ bdt build --python=3.6 -vv path/to/recipe-dir/1 path/to/recipe-dir/2
''')
@click.argument('recipe-dir', required=False, type=click.Path(file_okay=False,
  dir_okay=True, exists=True), nargs=-1)
@click.option('-p', '--python', default=('%d.%d' % sys.version_info[:2]),
    show_default=True, help='Version of python to build the ' \
        'environment for [default: %(default)s]')
@click.option('-r', '--condarc', default=CONDARC, show_default=True,
    help='overwrites the path leading to the condarc file to use',)
@click.option('-m', '--config', '--variant-config-files', show_default=True,
      default=CONDA_BUILD_CONFIG, help='overwrites the path leading to ' \
          'variant configuration file to use')
@click.option('-c', '--channel', show_default=True,
    default='https://www.idiap.ch/software/bob/conda/label/beta',
    help='Channel URL where this package is meant to be uploaded to, ' \
        'after a successful build - typically, this is a beta channel')
@click.option('-n', '--no-test', is_flag=True,
    help='Do not test the package, only builds it')
@click.option('-a', '--append-file', show_default=True,
      default=CONDA_RECIPE_APPEND, help='overwrites the path leading to ' \
          'appended configuration file to use')
@click.option('-D', '--docserver', show_default=True,
      default=SERVER, help='Server used for uploading artifacts ' \
          'and other goodies')
@click.option('-d', '--dry-run/--no-dry-run', default=False,
    help='Only goes through the actions, but does not execute them ' \
        '(combine with the verbosity flags - e.g. ``-vvv``) to enable ' \
        'printing to help you understand what will be done')
@verbosity_option()
@bdt.raise_on_error
def build(recipe_dir, python, condarc, config, channel, no_test, append_file,
    docserver, dry_run):
  """Builds package through conda-build with stock configuration

  This command wraps the execution of conda-build so that you use the same
  ``condarc`` and ``conda_build_config.yaml`` file we use for our CI.  It
  always set ``--no-anaconda-upload``.

  Note that both files are embedded within bob.devtools - you may need to
  update your environment before trying this.
  """

  # if we are in a dry-run mode, let's let it be known
  if dry_run:
      logger.warn('!!!! DRY RUN MODE !!!!')
      logger.warn('Nothing will be really built')

  recipe_dir = recipe_dir or [os.path.join(os.path.realpath('.'), 'conda')]

  logger.debug("CONDARC=%s", condarc)

  conda_config = make_conda_config(config, python, append_file, condarc)

  set_environment('LANG', 'en_US.UTF-8', os.environ)
  set_environment('LC_ALL', os.environ['LANG'], os.environ)
  set_environment('DOCSERVER', docserver, os.environ)
  set_environment('MATPLOTLIBRC', MATPLOTLIB_RCDIR, os.environ)

  for d in recipe_dir:

    if not os.path.exists(d):
      raise RuntimeError("The directory %s does not exist" % recipe_dir)

    version_candidate = os.path.join(d, '..', 'version.txt')
    if os.path.exists(version_candidate):
      version = open(version_candidate).read().rstrip()
      set_environment('BOB_PACKAGE_VERSION', version, os.environ)

    # pre-renders the recipe - figures out package name and version
    metadata = get_rendered_metadata(d, conda_config)

    # checks we should actually build this recipe
    from ..conda import should_skip_build
    if should_skip_build(metadata):
      logger.warn('Skipping UNSUPPORTED build of "%s" for py%s on %s',
          d, python.replace('.',''), osname())
      return 0

    # converts the metadata output into parsed yaml and continues the process
    rendered_recipe = get_parsed_recipe(metadata)

    # if a channel URL was passed, set the build number
    if channel:
      build_number, _ = next_build_number(channel,
          rendered_recipe['package']['name'],
          rendered_recipe['package']['version'], python)
    else:
      build_number = 0

    set_environment('BOB_BUILD_NUMBER', str(build_number), os.environ)

    # we don't execute the following command, it is just here for logging
    # purposes. we directly use the conda_build API.
    logger.info('Building %s-%s-py%s (build: %d) for %s',
        rendered_recipe['package']['name'],
        rendered_recipe['package']['version'], python.replace('.',''),
        build_number, osname())
    if not dry_run:
      from conda_build.api import build
      build(d, config=conda_config, notest=no_test)
