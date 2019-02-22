#!/usr/bin/env python

import os

import click

from . import bdt
from ..release import get_gitlab_instance

from ..log import verbosity_option, get_logger, echo_normal
logger = get_logger(__name__)


@click.command(epilog='''
Examples:

  1. List running jobs on a runner defined by its description (macmini):

     $ bdt gitlab jobs -vv macmini

''')
@click.argument('name')
@click.option('-s', '--status', type=click.Choice(['running', 'success',
  'failed', 'canceled']),
    default='running', show_default=True,
    help='The status of jobs we are searching for - one of "running", ' \
        '"success", "failed" or "canceled"')
@verbosity_option()
@bdt.raise_on_error
def jobs(name, status):
    """Lists jobs on a given runner
    """

    gl = get_gitlab_instance()
    gl.auth()
    user_id = gl.user.attributes['id']

    # search for the runner to affect
    the_runner = [k for k in gl.runners.list(all=True) if \
        k.attributes['description'] == name]
    if not the_runner:
      raise RuntimeError('Cannot find runner with description = %s', name)
    the_runner = the_runner[0]
    logger.info('Found runner %s (id=%d)',
        the_runner.attributes['description'], the_runner.attributes['id'])

    jobs = the_runner.jobs.list(all=True, status=status)
    logger.info('There are %d jobs running on %s', len(jobs), name)
    for k in jobs:
      echo_normal('** job %d: %s (%s), since %s, by %s [%s]' % \
          (k.id, k.attributes['project']['path_with_namespace'],
        k.attributes['name'], k.attributes['started_at'],
        k.attributes['user']['username'], k.attributes['web_url']))
