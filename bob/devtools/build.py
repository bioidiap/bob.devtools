#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Tools for self-building and other utilities'''


import os
import re
import sys
import glob
import json
import shutil
import platform
import subprocess

import logging
logger = logging.getLogger(__name__)

import yaml
import distutils.version
import conda_build.api


def conda_arch():
  """Returns the current OS name and architecture as recognized by conda"""

  r = 'unknown'
  if platform.system().lower() == 'linux':
    r = 'linux'
  elif platform.system().lower() == 'darwin':
    r = 'osx'
  else:
    raise RuntimeError('Unsupported system "%s"' % platform.system())

  if platform.machine().lower() == 'x86_64':
    r += '-64'
  else:
    raise RuntimeError('Unsupported machine type "%s"' % platform.machine())

  return r


def should_skip_build(metadata_tuples):
  """Takes the output of render_recipe as input and evaluates if this
  recipe's build should be skipped.
  """

  return all(m[0].skip() for m in metadata_tuples)


def next_build_number(channel_url, name, version, python):
  """Calculates the next build number of a package given the channel

  This function returns the next build number (integer) for a package given its
  recipe, dependencies, name, version and python version.  It looks on the
  channel URL provided and figures out if any clash would happen and what would
  be the highest build number available for that configuration.


  Args:

    channel_url: The URL where to look for packages clashes (normally a beta
      channel)
    name: The name of the package
    version: The version of the package
    python: The version of python as 2 digits (e.g.: "2.7" or "3.6")

  Returns: The next build number with the current configuration.  Zero (0) is
  returned if no match is found.  Also returns the URLs of the packages it
  finds with matches on the name, version and python-version.

  """

  from conda.exports import get_index

  # no dot in py_ver
  py_ver = python.replace('.', '')

  # get the channel index
  logger.debug('Downloading channel index from %s', channel_url)
  index = get_index(channel_urls=[channel_url], prepend=False)

  # search if package with the same version exists
  build_number = 0
  urls = []
  for dist in index:

    if dist.name == name and dist.version == version:
      match = re.match('py[2-9][0-9]+', dist.build_string)

      if match and match.group() == 'py{}'.format(py_ver):
        logger.debug("Found match at %s for %s-%s-py%s", index[dist].url,
            name, version, py_ver)
        build_number = max(build_number, dist.build_number + 1)
        urls.append(index[dist].url)

  urls = [url.replace(channel_url, '') for url in urls]

  return build_number, urls


def make_conda_config(config, python, append_file, condarc_options):
  '''Creates a conda configuration for a build merging various sources

  This function will use the conda-build API to construct a configuration by
  merging different sources of information.

  Args:

    config: Path leading to the ``conda_build_config.yaml`` to use
    python: The version of python to use for the build as ``x.y`` (e.g.
      ``3.6``)
    append_file: Path leading to the ``recipe_append.yaml`` file to use
    condarc_options: A dictionary (typically read from a condarc YAML file)
      that contains build and channel options

  Returns: A dictionary containing the merged configuration, as produced by
  conda-build API's ``get_or_merge_config()`` function.
  '''

  from conda_build.api import get_or_merge_config
  from conda_build.conda_interface import url_path

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
  '''Get the directory of a particular conda environment or fail silently'''

  cmd = [conda, 'env', 'list', '--json']
  output = subprocess.check_output(cmd)
  data = json.loads(output)
  paths = data.get('envs', [])

  if not paths:
    # real error condition, reports it at least, but no exception raising...
    logger.error('No environments in conda (%s) installation?', conda)
    return None

  if name in ('base', 'root'):
    return paths[0]  #first environment is base

  # else, must search for the path ending in ``/name``
  retval = [k for k in paths if k.endswith(os.sep + name)]
  if retval:
    return retval[0]

  # if no environment with said name is found, return ``None``
  return None


def conda_create(conda, name, overwrite, condarc, packages, dry_run, use_local):
  '''Creates a new conda environment following package specifications

  This command can create a new conda environment following the list of input
  packages.  It will overwrite an existing environment if indicated.

  Args:
    conda: path to the main conda executable of the installation
    name: the name of the environment to create or overwrite
    overwrite: if set to ```True``, overwrite potentially existing environments
      with the same name
    condarc: a dictionary of options for conda, including channel urls
    packages: the package list specification
    dry_run: if set, then don't execute anything, just print stuff
    use_local: include the local conda-bld directory as a possible installation
      channel (useful for testing multiple interdependent recipes that are
      built locally)
  '''

  from .bootstrap import run_cmdline

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
        run_cmdline(cmd)
    else:
      raise RuntimeError('environment `%s\' exists in `%s\' - use '
                         '--overwrite to overwrite' % (name, envdir))

  cmdline_channels = ['--channel=%s' % k for k in condarc['channels']]
  cmd = [conda, 'create', '--yes', '--name', name, '--override-channels'] + \
      cmdline_channels
  if dry_run:
    cmd.append('--dry-run')
  if use_local:
     cmd.append('--use-local')
  cmd.extend(sorted(specs))
  run_cmdline(cmd)

  # creates a .condarc file to sediment the just created environment
  if not dry_run:
    # get envdir again - it may just be created!
    envdir = get_env_directory(conda, name)
    destrc = os.path.join(envdir, '.condarc')
    logger.info('Creating %s...', destrc)
    with open(destrc, 'w') as f:
      yaml.dump(condarc, f, indent=2)


def get_docserver_setup(public, stable, server, intranet):
  '''Returns a setup for BOB_DOCUMENTATION_SERVER

  What is available to build the documentation depends on the setup of
  ``public`` and ``stable``:

  * public and stable: only returns the public stable channel(s)
  * public and not stable: returns both public stable and beta channels
  * not public and stable: returns both public and private stable channels
  * not public and not stable: returns all channels

  Beta channels have priority over stable channels, if returned.  Private
  channels have priority over public channles, if turned.


  Args:

    public: Boolean indicating if we're supposed to include only public
      channels
    stable: Boolean indicating if we're supposed to include only stable
      channels
    server: The base address of the server containing our conda channels
    intranet: Boolean indicating if we should add "private"/"public" prefixes
      on the returned paths


  Returns: a string to be used by bob.extension to find dependent
  documentation projects.

  '''

  if (not public) and (not intranet):
    raise RuntimeError('You cannot request for private channels and set' \
        ' intranet=False (server=%s) - these are conflicting options' % server)

  entries = []

  # public documentation: always can access
  prefix = '/software/bob'
  if server.endswith(prefix):  # don't repeat yourself...
    prefix = ''
  if stable:
    entries += [
        server + prefix + '/docs/bob/%(name)s/%(version)s/',
        server + prefix + '/docs/bob/%(name)s/stable/',
        ]
  else:
    entries += [
        server + prefix + '/docs/bob/%(name)s/master/',
        ]

  if not public:
    # add private channels, (notice they are not accessible outside idiap)
    prefix = '/private' if intranet else ''
    if stable:
      entries += [
          server + prefix + '/docs/bob/%(name)s/%(version)s/',
          server + prefix + '/docs/bob/%(name)s/stable/',
          ]
    else:
      entries += [
          server + prefix + '/docs/bob/%(name)s/master/',
          ]

  return '|'.join(entries)


def check_version(workdir, envtag):
  '''Checks if the version being built and the value reported match

  This method will read the contents of the file ``version.txt`` and compare it
  to the potentially set ``envtag`` (may be ``None``).  If the value of
  ``envtag`` is different than ``None``, ensure it matches the value in
  ``version.txt`` or raises an exception.


  Args:

    workdir: The work directory where the repo of the package being built was
      checked-out
    envtag: (optional) tag provided by the environment


  Returns: A tuple with the version of the package that we're currently
  building and a boolean flag indicating if the version number represents a
  pre-release or a stable release.
  '''

  version = open(os.path.join(workdir, "version.txt"), 'rt').read().rstrip()

  # if we're building a stable release, ensure a tag is set
  parsed_version = distutils.version.LooseVersion(version).version
  is_prerelease = any([isinstance(k, str) for k in parsed_version])
  if is_prerelease:
    if envtag is not None:
      raise EnvironmentError('"version.txt" indicates version is a ' \
          'pre-release (v%s) - but environment provided tag "%s", ' \
          'which indicates this is a **stable** build. ' \
          'Have you created the tag using ``bdt release``?' % (version,
          envtag))
  else:  #it is a stable build
    if envtag is None:
      raise EnvironmentError('"version.txt" indicates version is a ' \
          'stable build (v%s) - but there is **NO** tag environment ' \
          'variable defined, which indicates this is **not** ' \
          'a tagged build. Use ``bdt release`` to create stable releases' % \
          (version,))
    if envtag[1:] != version:
      raise EnvironmentError('"version.txt" and the value of ' \
          'the provided tag do **NOT** agree - the former ' \
          'reports version %s, the latter, %s' % (version, envtag[1:]))

  return version, is_prerelease


def git_clean_build(runner, verbose):
  '''Runs git-clean to clean-up build products

  Args:

    runner: A pointer to the ``run_cmdline()`` function
    verbose: A boolean flag indicating if the git command should report erased
      files or not

  '''

  # glob wild card entries we'd like to keep
  exclude_from_cleanup = [
      "miniconda.sh",   #the installer, cached
      "miniconda/pkgs/urls.txt",  #download index, cached
      "sphinx",  #build artifact -- documentation
      ]

  # cache
  exclude_from_cleanup += glob.glob("miniconda/pkgs/*.tar.bz2")

  # artifacts
  exclude_from_cleanup += glob.glob("miniconda/conda-bld/*/*.tar.bz2")
  exclude_from_cleanup += glob.glob("dist/*.zip")

  logger.debug('Excluding the following paths from git-clean:\n  - %s',
      '  - '.join(exclude_from_cleanup))

  # decide on verbosity
  flags = '-ffdx'
  if not verbose: flags += 'q'

  runner(['git', 'clean', flags] + \
      ['--exclude=%s' % k for k in exclude_from_cleanup])


if __name__ == '__main__':

  import argparse

  parser = argparse.ArgumentParser(description='Builds bob.devtools on the CI')
  parser.add_argument('-n', '--name',
      default=os.environ.get('CI_PROJECT_NAME', 'bob.devtools'),
      help='The name of the project being built [default: %(default)s]')
  parser.add_argument('-c', '--conda-root',
      default=os.environ.get('CONDA_ROOT',
        os.path.realpath(os.path.join(os.curdir, 'miniconda'))),
      help='The location where we should install miniconda ' \
          '[default: %(default)s]')
  parser.add_argument('-V', '--visibility',
      choices=['public', 'internal', 'private'],
      default=os.environ.get('CI_PROJECT_VISIBILITY', 'public'),
      help='The visibility level for this project [default: %(default)s]')
  parser.add_argument('-t', '--tag',
      default=os.environ.get('CI_COMMIT_TAG', None),
      help='If building a tag, pass it with this flag [default: %(default)s]')
  parser.add_argument('-w', '--work-dir',
      default=os.environ.get('CI_PROJECT_DIR', os.path.realpath(os.curdir)),
      help='The directory where the repo was cloned [default: %(default)s]')
  parser.add_argument('-p', '--python-version',
      default=os.environ.get('PYTHON_VERSION', '%d.%d' % sys.version_info[:2]),
      help='The version of python to build for [default: %(default)s]')
  parser.add_argument('--verbose', '-v', action='count',
      help='Increases the verbosity level.  We always prints error and ' \
          'critical messages. Use a single ``-v`` to enable warnings, ' \
          'two ``-vv`` to enable information messages and three ``-vvv`` ' \
          'to enable debug messages')

  args = parser.parse_args()

  # loads the "adjacent" bootstrap module
  import importlib.util
  mydir = os.path.dirname(os.path.realpath(sys.argv[0]))
  bootstrap_file = os.path.join(mydir, 'bootstrap.py')
  spec = importlib.util.spec_from_file_location("bootstrap", bootstrap_file)
  bootstrap = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(bootstrap)

  bootstrap.setup_logger(logger, args.verbose)

  VERB = (verbose >= 2)

  bootstrap.set_environment('DOCSERVER', bootstrap._SERVER, verbose=VERB)
  bootstrap.set_environment('LANG', 'en_US.UTF-8', verbose=VERB)
  bootstrap.set_environment('LC_ALL', os.environ['LANG'], verbose=VERB)

  # get information about the version of the package being built
  version, is_prerelease = check_version(args.work_dir, args.tag)
  bootstrap.set_environment('BOB_PACKAGE_VERSION', version, verbose=VERB)

  # create the build configuration
  conda_build_config = os.path.join(mydir, 'data', 'conda_build_config.yaml')
  recipe_append = os.path.join(mydir, 'data', 'recipe_append.yaml')

  condarc = os.path.join(args.conda_root, 'condarc')
  logger.info('Loading (this build\'s) CONDARC file from %s...', condarc)
  with open(condarc, 'rb') as f:
    condarc_options = yaml.load(f)

  # notice this condarc typically will only contain the defaults channel - we
  # need to boost this up with more channels to get it right.
  public = ( args.visibility == 'public' )
  channels = bootstrap.get_channels(public=public, stable=(not is_prerelease),
      server=bootstrap._SERVER, intranet=True)
  logger.info('Using the following channels during build:\n  - %s',
      '\n  - '.join(channels + ['defaults']))
  condarc_options['channels'] = channels + ['defaults']

  # dump packages at conda_root
  condarc_options['croot'] = os.path.join(args.conda_root, 'conda-bld')

  logger.info('Merging conda configuration files...')
  conda_config = make_conda_config(conda_build_config, args.python_version,
      recipe_append, condarc_options)

  # retrieve the current build number for this build
  build_number, _ = next_build_number(channels[0], args.name, version,
      args.python_version)
  bootstrap.set_environment('BOB_BUILD_NUMBER', str(build_number),
      verbose=VERB)

  # runs the build using the conda-build API
  arch = conda_arch()
  logger.info('Building %s-%s-py%s (build: %d) for %s',
      args.name, version, args.python_version.replace('.',''), build_number,
      arch)
  conda_build.api.build(os.path.join(args.work_dir, 'conda'),
      config=conda_config)

  git_clean_build(bootstrap.run_cmdline, verbose=VERB)
