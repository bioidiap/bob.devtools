#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''This is a copy of bob/devtools/conda:next_build_number with a CLI'''

import os
import re
import sys

from conda.exports import get_index


if __name__ == '__main__':

  channel_url = sys.argv[1]
  name = sys.argv[2]
  version = sys.argv[3]
  python = sys.argv[4]

  # no dot in py_ver
  py_ver = python.replace('.', '')

  # get the channel index
  index = get_index(channel_urls=[channel_url], prepend=False)

  # search if package with the same version exists
  build_number = 0
  urls = []
  for dist in index:

    if dist.name == name and dist.version == version:
      match = re.match('py[2-9][0-9]+', dist.build_string)

      if match and match.group() == 'py{}'.format(py_ver):
        build_number = max(build_number, dist.build_number + 1)
        urls.append(index[dist].url)

  urls = [url.replace(channel_url, '') for url in urls]

  print(build_number)
