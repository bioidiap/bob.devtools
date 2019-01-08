#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Utilities for deadling with conda packages'''

import re
import logging
import platform
logger = logging.getLogger(__name__)


def osname():
  """Returns the current OS name as recognized by conda"""

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
