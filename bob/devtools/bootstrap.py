#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import os
import json
import shutil
import subprocess

import logging
logger = logging.getLogger(__name__)

import yaml


def make_conda_config(config, python, append_file, condarc):

  from conda_build.api import get_or_merge_config
  from conda_build.conda_interface import url_path

  with open(condarc, 'rb') as f:
    condarc_options = yaml.load(f)

  retval = get_or_merge_config(None, variant_config_files=config,
      python=python, append_sections_file=append_file, **condarc_options)

  retval.channel_urls = []

  for url in condarc_options['channels']:
    # allow people to specify relative or absolute paths to local channels
    #    These channels still must follow conda rules - they must have the
    #    appropriate platform-specific subdir (e.g. win-64)
    if os.path.isdir(url):
      if not os.path.isabs(url):
        url = os.path.normpath(os.path.abspath(os.path.join(os.getcwd(), url)))
      url = url_path(url)
    retval.channel_urls.append(url)

  return retval


def get_rendered_metadata(recipe_dir, config):
  '''Renders the recipe and returns the interpreted YAML file'''

  from conda_build.api import render
  return render(recipe_dir, config=config)


def get_parsed_recipe(metadata):
  '''Renders the recipe and returns the interpreted YAML file'''

  from conda_build.api import output_yaml
  output = output_yaml(metadata[0][0])
  return yaml.load(output)


def remove_pins(deps):
  return [l.split()[0] for l in deps]


def parse_dependencies(recipe_dir, config):

  metadata = get_rendered_metadata(recipe_dir, config)
  recipe = get_parsed_recipe(metadata)
  return remove_pins(recipe['requirements'].get('build', [])) + \
      remove_pins(recipe['requirements'].get('host', [])) + \
      recipe['requirements'].get('run', []) + \
      recipe.get('test', {}).get('requires', []) + \
      ['bob.buildout', 'mr.developer', 'ipdb']
      # by last, packages required for local dev


def get_env_directory(conda, name):

  cmd = [conda, 'env', 'list', '--json']
  output = subprocess.check_output(cmd)
  data = json.loads(output)
  retval = [k for k in data.get('envs', []) if k.endswith(os.sep + name)]
  if retval:
    return retval[0]
  return None


def conda_create(conda, name, overwrite, condarc, packages, dry_run, use_local):

  specs = []
  for k in packages:
    k = ' '.join(k.split()[:2])  # remove eventual build string
    if any(elem in k for elem in '><|'):
      specs.append(k.replace(' ', ''))
    else:
      specs.append(k.replace(' ', '='))

  # if the current environment exists, delete it first
  envdir = get_env_directory(conda, name)
  if envdir is not None:
    if overwrite:
      cmd = [conda, 'env', 'remove', '--yes', '--name', name]
      logger.debug('$ ' + ' '.join(cmd))
      if not dry_run:
        status = subprocess.call(cmd)
        if status != 0:
          return status
    else:
      raise RuntimeError('environment `%s\' exists in `%s\' - use '
                         '--overwrite to overwrite' % (name, envdir))

  cmd = [conda, 'create', '--yes', '--name', name]
  if dry_run:
    cmd.append('--dry-run')
  if use_local:
     cmd.append('--use-local')
  cmd.extend(sorted(specs))
  logger.debug('$ ' + ' '.join(cmd))
  status = subprocess.call(cmd)
  if status != 0:
    return status

  # copy the used condarc file to the just created environment
  if not dry_run:
    # get envdir again - it may just be created!
    envdir = get_env_directory(conda, name)
    destrc = os.path.join(envdir, '.condarc')
    logger.debug('$ cp %s -> %s' % (condarc, destrc))
    shutil.copy2(condarc, destrc)

  return status
