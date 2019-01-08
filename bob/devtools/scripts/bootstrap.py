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
from ..bootstrap import parse_dependencies, conda_create


DEFAULT_CONDARC = pkg_resources.resource_filename(__name__,
    os.path.join('..', 'data', 'build-condarc'))
DEFAULT_VARIANT = pkg_resources.resource_filename(__name__,
    os.path.join('..', 'data', 'conda_build_config.yaml'))


@click.command(epilog='''
Examples:

  1. Creates an environment called `myenv' for developing the currently checked-out package (N.B.: first activate the base environment):

\b
     $ cd bob.package.foo
     $ bdt bootstrap -vv myenv

     The above command assumes the directory `conda' exists on the current directory and that it contains a file called `meta.yaml' containing the recipe for the package you want to create a development environment for.

     If you get things right by default, the above form is the typical usage scenario of this app. Read-on to tweak special flags and settings.


  2. By default, we use the native python version of your conda installation as the default python version to use for the newly created environment. You may select a different one with `--python=X.Y':

     $ bdt bootstrap -vv --python=3.6 myenv


  3. By default, we use our own condarc and `conda_build_config.yaml` files that are used in creating packages for our CI/CD system. If you wish to use your own, specify them on the command line:

     $ bdt bootstrap -vv --python=3.6 --config=config.yaml --condarc=~/.condarc myenv

     Notice the condarc file **must** end in `condarc', or conda will complain.


  4. You can use the option `--dry-run' to simulate what would be installed
  instead of actually creating a new environment.  Combine with `-vvv` to
  enable debug printing.  Equivalent conda commands you can execute on the
  shell will be printed:


     $ bdt bootstrap -vvv --dry-run myenv
''')
@click.argument('name')
@click.argument('recipe-dir', required=False, type=click.Path(file_okay=False,
  dir_okay=True, exists=True))
@click.option('-p', '--python', default=('%d.%d' % sys.version_info[:2]),
    show_default=True, help='Version of python to build the ' \
        'environment for [default: %(default)s]')
@click.option('-o', '--overwrite/--no-overwrite', default=False,
      help='If set and an environment with the same name exists, ' \
          'deletes it first before creating the new environment',
          show_default=True)
@click.option('-r', '--condarc', default=DEFAULT_CONDARC, show_default=True,
    help='overwrites the path leading to the condarc file to use',)
@click.option('-m', '--config', '--variant-config-files', show_default=True,
      default=DEFAULT_VARIANT, help='overwrites the path leading to ' \
          'variant configuration file to use')
@click.option('-d', '--dry-run/--no-dry-run', default=False,
    help='Only goes through the actions, but does not execute them ' \
        '(combine with the verbosity flags - e.g. ``-vvv``) to enable ' \
        'printing to help you understand what will be done')
@verbosity_option()
@bdt.raise_on_error
def bootstrap(name, recipe_dir, python, overwrite, condarc, config, dry_run):
  """This program uses conda to build a development environment for a recipe

  It uses the conda render API to render a recipe and install an environment
  containing all build/host, run and test dependencies of a package. It does
  **not** build the package itself, just install dependencies so you can build
  the package by hand, possibly using buildout or similar. If you'd like to
  conda-build your package, just use `conda build` instead.

  Once the environment is created, a copy of the used `condarc' file is placed
  on the root of the environment. Installing or updating packages on the newly
  created environment should be possible without further configuration. Notice
  that beta packages quickly get outdated and upgrading may no longer be
  possible for aging development environments. You're advised to always re-use
  this app and use the flag `--overwrite` to re-create from scratch the
  development environment.
  """

  recipe_dir = recipe_dir or os.path.join(os.path.realpath('.'), 'conda')

  if not os.path.exists(recipe_dir):
    raise RuntimeError("The directory %s does not exist" % recipe_dir)

  conda = os.environ.get('CONDA_EXE')
  if conda is None:
    raise RuntimeError("Cannot find `conda' executable (${CONDA_EXEC}) - " \
        "have you activated the build environment containing bob.devtools " \
        "properly?")

  # set condarc before continuing
  logger.debug('$ export CONDARC=%s', condarc)
  os.environ['CONDARC'] = condarc

  deps = parse_dependencies(conda, recipe_dir, python, config)
  status = conda_create(conda, name, overwrite, condarc, deps, dry_run)
  click.echo('Execute on your shell: "conda activate %s"' % name)
