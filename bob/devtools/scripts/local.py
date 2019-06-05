#!/usr/bin/env python

import os
import sys
import re
import glob
import shutil

import gitlab

import yaml
import click
import pkg_resources
from click_plugins import with_plugins

from . import bdt
from . import ci
from ..constants import SERVER, CONDA_BUILD_CONFIG, CONDA_RECIPE_APPEND, \
    WEBDAV_PATHS, BASE_CONDARC
from ..deploy import deploy_conda_package, deploy_documentation
from ..ci import read_packages, comment_cleanup, uniq

from ..log import verbosity_option, get_logger, echo_normal
logger = get_logger(__name__)


def set_up_environment_variables(python, name_space, project_dir='.', project_visibility='public'):
  """
  This function sets up the proper environment variables when user wants to run the commands usually run on ci
  locally
  """
  os.environ['CI_JOB_TOKEN'] = gitlab.Gitlab.from_config('idiap').private_token
  os.environ['CI_PROJECT_DIR'] = project_dir
  os.environ['CI_PROJECT_NAMESPACE'] = name_space
  os.environ['CI_PROJECT_VISIBILITY'] = project_visibility
  os.environ['PYTHON_VERSION']= python



@with_plugins(pkg_resources.iter_entry_points('bdt.local.cli'))
@click.group(cls=bdt.AliasedGroup)
def local():
  """Commands for building packages and handling certain activities locally
  it requires a proper set up for ~/.python-gitlab.cfg

  Commands defined here can be run in your own installation.
  """
  pass


@local.command(epilog='''
Examples:

  1. Prepares the docs locally:

     $ bdt local docs -vv requirements.txt

''')
@click.argument('requirement', required=True, type=click.Path(file_okay=True,
  dir_okay=False, exists=True), nargs=1)
@click.option('-d', '--dry-run/--no-dry-run', default=False,
    help='Only goes through the actions, but does not execute them ' \
        '(combine with the verbosity flags - e.g. ``-vvv``) to enable ' \
        'printing to help you understand what will be done')
@click.option('-p', '--python', default=('%d.%d' % sys.version_info[:2]),
    show_default=True, help='Version of python to build the environment for')
@click.option('-g', '--group', show_default=True, default='bob',
    help='Group of packages (gitlab namespace) this package belongs to')
@verbosity_option()
@bdt.raise_on_error
@click.pass_context
def docs(ctx, requirement, dry_run, python, group):
  """Prepares documentation build

  This command:
    1. Clones all the necessary packages necessary to build the bob/beat
       documentation
    2. Generates the `extra-intersphinx.txt` and `nitpick-exceptions.txt` file

  """
  set_up_environment_variables(python=python, name_space=group)  

  ctx.invoke(ci.docs, requirement=requirement, dry_run=dry_run)