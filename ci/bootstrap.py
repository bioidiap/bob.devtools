#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Bootstraps a new conda installation and prepares base environment

If "local" is passed as parameter, then self installs an already built version
of bob.devtools available on your conda-bld directory. If you pass "beta", then
it bootstraps from the package installed on our conda beta channel.  If you
pass "stable", then it bootstraps installing the package available on the
stable channel.

If bootstrapping anything else than "build", then provide a second argument
with the name of the environment that one wants to create with an
installation of bob.devtools.
'''

import os
import sys
import glob
import shutil
import platform
import subprocess

import logging
logger = logging.getLogger('bootstrap')


def run_cmdline(cmd, env=None):
  '''Runs a command on a environment, logs output and reports status


  Parameters:

    cmd (list): The command to run, with parameters separated on a list

    env (dict, Optional): Environment to use for running the program on. If not
      set, use :py:obj:`os.environ`.


  Returns:

    str: The standard output and error of the command being executed

  '''

  if env is None: env = os.environ

  logger.info('$ %s' % ' '.join(cmd))

  start = time.time()
  out = b''

  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
      env=env)

  chunk_size = 1 << 13
  lineno = 0
  for chunk in iter(lambda: p.stdout.read(chunk_size), b''):
    decoded = chunk.decode()
    while '\n' in decoded:
      pos = decoded.index('\n')
      print('%03d: %s' % (lineno, decoded[:pos]))
      decoded = decoded[pos+1:]
      lineno += 1
    out += chunk

  if p.wait() != 0:
    logger.error('Command output is:\n%s', out.decode())
    raise RuntimeError("command `%s' exited with error state (%d)" % \
        (' '.join(cmd_log), p.returncode))

  total = time.time() - start

  logger.info('command took %s' % human_time(total))

  out = out.decode()

  return out


def touch(path):
  '''Python-implementation of the "touch" command-line application'''

  with open(path, 'a'):
    os.utime(path, times)


def merge_conda_cache(cache, prefix):
  '''Merges conda pkg caches and conda-bld folders'''

  pkgs_dir = os.path.join(prefix, 'pkgs')
  if not os.path.exists(pkgs_dir):
    logger.info('mkdir -p %s', pkgs_dir)
    os.makedirs(pkgs_dir)
    pkgs_urls_txt = os.path.join(pkgs_dir, 'urls.txt')
    logger.info('touch %s', pkgs_urls_txt)
    touch(pkgs_urls_txt)

  # move packages on cache/pkgs to pkgs_dir
  cached_pkgs_dir = os.path.join(cache, 'pkgs')
  cached_packages = glob.glob(os.path.join(cache_pkgs_dir, '*.tar.bz2'))
  cached_packages = [k for k in cached_packages if not \
      k.startswith(os.environ['CI_PROJECT_NAME'] + '-')]
  logger.info('Merging %d cached conda packages', len(cached_packages))
  for k in cached_packages:
    dst = os.path.join(pkgs_dir, os.path.basename(k))
    logger.debug('(move) %s -> %s', k, dst)
    os.rename(k, dst)

  # merge urls.txt files
  logger.info('Merging urls.txt files from cache...')
  urls = []
  cached_pkgs_urls_txt = os.path.join(cached_pkgs_dir, 'urls.txt')
  with open(pkgs_urls_txt, 'rb') as f1, \
      open(cached_pkgs_urls_txt, 'rb') as f2:
    data = set(f1.readlines() + f2.readlines())
    data = sorted(list(data))
  with open(pkgs_urls_txt, 'wb') as f:
    f.writelines(data)

  pkgs_urls = os.path.join(pkgs_dir, 'urls')
  touch(pkgs_urls)

  # move conda-bld build results
  cached_conda_bld = os.path.join(cache, 'conda-bld')
  if os.path.exists(cached_conda_bld):
    dst = os.path.join(prefix, 'conda-bld')
    logger.info('(move) %s -> %s', cached_conda_bld, dst)
    os.rename(cached_conda_bld, dst)


def get_miniconda_sh():
  '''Retrieves the miniconda3 installer for the current system'''

  import http.client

  server = 'https://repo.continuum.io'
  path = '/miniconda/Miniconda3-latest-%s-x86_64.sh'
  if platform.system() == 'Darwin':
    path = path % 'MacOSX'
  else:
    path = path % 'Linux'

  logger.info('Requesting for %s%s...', server, path)
  conn = http.client.HTTPSConnection(server)
  conn.request("GET", path)
  r1 = conn.getresponse()

  assert r1.status == 200, 'Request for %s%s - returned status %d (%s)' % \
      (server, path, r1.status, r1.reason)

  dst = 'miniconda.sh'
  logger.info('(download) %s%s -> %s...', server, path, dst)
  with open(dst, 'wb') as f:
    f.write(r1.read())


def install_miniconda(prefix):
  '''Creates a new miniconda installation'''

  logger.info("Installing miniconda in %s...", prefix)

  if not os.path.exists('miniconda.sh'):  #re-downloads installer
    get_miniconda_sh()
  else:
    logger.info("Re-using cached miniconda3 installer")

  if os.path.exists(prefix):  #this is the previous cache, move it
    cached = prefix + '.cached'
    logger.info('(move) %s -> %s', prefix, cached)
    os.rename(prefix, cached)

  run_cmdline(['bash', 'miniconda.sh', '-b', '-p', prefix])
  merge_conda_cache(cached, prefix)
  shutil.rmtree(cached)


def get_local_channels():
  '''Returns the relevant conda channels to consider if building project'''

  # add channels
  public = os.environ['CI_PROJECT_VISIBILITY'] == 'public'
  stable = os.environ.get('CI_COMMIT_TAG') is not None

  server = "http://www.idiap.ch"
  channels = []

  if not public:
    if not stable:  #allowed private channels
      channels += [server + '/private/conda/label/beta']  #allowed betas
    channels += [server + '/private/conda']
  if not stable:
    channels += [server + '/public/conda/label/beta']  #allowed betas
  channels += [server + '/public/conda']

  return channels


def add_channels_condarc(channels, condarc):
  '''Appends passed channel list to condarc file, print contents'''

  with open(condarc, 'at') as f:
    f.write('channels:\n')
    for k in channels:
      f.write('  - %s\n' % k)

  with open(condarc, 'rt') as f:
    logger.info('Contents of $CONDARC:\n%s', f.read())


if __name__ == '__main__':

  if len(sys.argv) == 1:
    print('usage: python3 %s build|local|beta|stable [name]' % sys.argv[0])
    print('  build   to build bob.devtools')
    print('  local   to bootstrap deploy|pypi stages for bob.devtools builds')
    print('  beta    to bootstrap CI environment for beta builds')
    print('  stable  to bootstrap CI environment for stable builds')
    print('  [name]  (optional) if command is one of local|beta|stable, ')
    print('          provide the name of env for bob.devtools installation')
    sys.exit(1)

  prefix = os.environ['CONDA_ROOT']
  logger.info('os.environ["%s"] = %s', 'CONDA_ROOT', prefix)

  workdir = os.environ['CI_PROJECT_DIR']
  logger.info('os.environ["%s"] = %s', 'CI_PROJECT_DIR', workdir)

  condarc = os.path.join(prefix, 'condarc')
  os.environ['CONDARC'] = condarc
  logger.info('os.environ["%s"] = %s', 'CONDARC', condarc)

  conda_bin = os.path.join(prefix, 'bin', 'conda')
  if not os.path.exists(conda_bin):
    install_miniconda(prefix)

  # creates the condarc file
  baserc = os.path.join(workdir, 'bob', 'devtools', 'data', 'base-condarc')
  logger.info('(copy) %s -> %s', baserc, condarc)
  shutil.copy2(baserc, condarc)

  conda_version = '4'
  conda_build_version = '3'

  if sys.argv[1] == 'build':

    # simple - just use the defaults channels when self building
    add_channels_condarc(['defaults'], condarc)
    run_cmdline([conda_bin, 'install', '-n', 'base',
      'python',
      'conda=%s' % conda_version,
      'conda-build=%s' % conda_build_version,
      ])

  elif sys.argv[1] == 'local':

    # index the locally built packages
    run_cmdline([conda_bin, 'install', '-n', 'base',
      'python',
      'conda=%s' % conda_version,
      'conda-build=%s' % conda_build_version,
      ])
    conda_bld_path = os.path.join(prefix, 'conda-bld')
    run_cmdline([conda_bin, 'index', conda_bld_path])
    # add the locally build directory before defaults, boot from there
    add_channels_condarc([conda_bld_path, 'defaults'], condarc)
    run_cmdline([conda_bin, 'create', '-n', sys.argv[2], 'bob.devtools'])

  elif sys.argv[1] in ('beta', 'stable'):

    # installs from channel
    channels = get_local_channels()
    add_channels_condarc(channels + ['defaults'], condarc)
    run_cmdline([conda_bin, 'create', '-n', sys.argv[2], 'bob.devtools'])

  else:

    logger.error("Bootstrap with 'build', or 'local|beta|stable <name>'")
    logger.error("The value '%s' is not currently supported", sys.argv[1])
    sys.exit(1)

  # clean up
  run_cmdline([conda_bin, 'clean', '--lock'])

  # print conda information for debugging purposes
  run_cmdline([conda_bin, 'info'])
