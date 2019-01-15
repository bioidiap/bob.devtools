#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Tools to help CI-based builds and artifact deployment'''


import os

import logging
logger = logging.getLogger(__name__)

import git
import packaging.version


def is_master(refname, tag):
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
    repo = git.Repo(os.environ['CI_PROJECT_DIR'])
    _tag = repo.tag('refs/tags/%s' % tag)
    return _tag.commit in repo.iter_commits(rev='master')

  return refname == 'master'


def is_visible_outside(package, visibility):
  '''Determines if the project is visible outside Idiap'''

  logger.info('Project %s visibility is "%s"', package, visibility)

  if visibility == 'internal':
    visibility = 'private' #the same thing for this command
    logger.warn('Project %s visibility switched to "%s".  ' \
        'For this command, it all boils down to the same...', package,
        visibility)

  return visibility == 'public'


def is_stable(package, refname, tag):
  '''Determines if the package being published is stable

  This is done by checking if a tag was set for the package.  If that is the
  case, we still cross-check the tag is on the "master" branch.  If everything
  checks out, we return ``True``.  Else, ``False``.

  Args:

    package: Package name in the format "group/name"
    refname: The current value of the environment ``CI_COMMIT_REF_NAME``
    tag: The current value of the enviroment ``CI_COMMIT_TAG`` (may be
      ``None``)

  Returns: a boolean, indicating if the current build is for a stable release
  '''

  if tag is not None:
    logger.info('Project %s tag is "%s"', package, tag)
    parsed_tag = packaging.version.Version(tag)

    if parsed_tag.is_prerelease:
      logger.warn('Pre-release detected - not publishing to stable channels')
      return False

    if is_master(os.environ['CI_COMMIT_REF_NAME'], tag):
      return True
    else:
      logger.warn('Tag %s in non-master branch will be ignored', tag)
      return False

  logger.info('No tag information available at build')
  logger.info('Considering this to be a pre-release build')
  return False
