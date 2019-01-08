#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import os
import json
import shutil
import subprocess

import logging
logger = logging.getLogger(__name__)

import yaml
from conda_build.api import get_or_merge_config, render, output_yaml


def get_rendered_recipe(conda, recipe_dir, python, config):
  '''Renders the recipe and returns the interpreted YAML file'''

  # equivalent command execute - in here we use the conda API
  cmd = [
      conda, 'render',
      '--variant-config-files', config,
      '--python', python,
      recipe_dir,
      ]
  logger.debug('$ ' + ' '.join(cmd))

  # do the real job
  config = get_or_merge_config(None, variant_config_files=config,
                               python=python)
  metadata = render(recipe_dir, config=config)
  output = output_yaml(metadata[0][0])
  return yaml.load(output)


def remove_pins(deps):
  return [l.split()[0] for l in deps]


def parse_dependencies(conda, recipe_dir, python, config):

  recipe = get_rendered_recipe(conda, recipe_dir, python, config)
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


def conda_create(conda, name, overwrite, condarc, packages, dry_run):

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

  cmd = [conda, 'create', '--yes', '--name', name] + sorted(specs)
  if dry_run:
    cmd.insert(2, '--dry-run')
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
