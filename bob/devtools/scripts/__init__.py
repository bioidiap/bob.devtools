#!/usr/bin/env python

def read_packages(filename):
  """
  Return a python list given file containing one package per line

  """
  # loads dirnames from order file (accepts # comments and empty lines)
  packages = []
  with open(filename, 'rt') as f:
    for line in f:
      line = line.partition('#')[0].strip()
      if line:
        if ',' in line:  #user specified a branch
          path, branch = [k.strip() for k in line.split(',', 1)]
          packages.append((path, branch))
        else:
          packages.append((line, 'master'))

  return packages

