#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Tools to help CI-based builds and artifact deployment'''


import logging
logger = logging.getLogger(__name__)

import git
import distutils.version


def is_master(refname, tag, repodir):
  '''Tells if we're on the master branch via ref_name or tag

  This function checks if the name of the branch being built is "master".  If a
  tag is set, then it checks if the tag is on the master branch.  If so, then
  also returns ``True``, otherwise, ``False``.

  Args:

    refname: The value of the environment variable ``CI_COMMIT_REF_NAME``
    tag: The value of the environment variable ``CI_COMMIT_TAG`` - (may be
      ``None``)

  Returns: a boolean, indicating we're building the master branch **or** that
  the tag being built was issued on the master branch.
  '''

  if tag is not None:
    repo = git.Repo(repodir)
    _tag = repo.tag('refs/tags/%s' % tag)
    return _tag.commit in repo.iter_commits(rev='master')

  return refname == 'master'


def is_stable(package, refname, tag, repodir):
  '''Determines if the package being published is stable

  This is done by checking if a tag was set for the package.  If that is the
  case, we still cross-check the tag is on the "master" branch.  If everything
  checks out, we return ``True``.  Else, ``False``.

  Args:

    package: Package name in the format "group/name"
    refname: The current value of the environment ``CI_COMMIT_REF_NAME``
    tag: The current value of the enviroment ``CI_COMMIT_TAG`` (may be
      ``None``)
    repodir: The directory that contains the clone of the git repository

  Returns: a boolean, indicating if the current build is for a stable release
  '''

  if tag is not None:
    logger.info('Project %s tag is "%s"', package, tag)
    parsed_tag = distutils.version.LooseVersion(tag[1:]).version  #remove 'v'
    is_prerelease = any([isinstance(k, str) for k in parsed_tag])

    if is_prerelease:
      logger.warn('Pre-release detected - not publishing to stable channels')
      return False

    if is_master(refname, tag, repodir):
      return True
    else:
      logger.warn('Tag %s in non-master branch will be ignored', tag)
      return False

  logger.info('No tag information available at build')
  logger.info('Considering this to be a pre-release build')
  return False
