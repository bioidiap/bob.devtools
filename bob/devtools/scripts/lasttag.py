#!/usr/bin/env python

import os
import logging
logger = logging.getLogger(__name__)

import click

from . import bdt
from ..log import verbosity_option
from ..changelog import get_last_tag, parse_date
from ..release import get_gitlab_instance


@click.command(epilog='''
Examples:

  1. Get the last tag information of the bob/bob package

     $ bdt lasttag bob/bob


  2. Get the last tag information of the beat/beat.core package

     $ bdt lasttag beat/beat.core

''')
@click.argument('package')
@verbosity_option()
@bdt.raise_on_error
def lasttag(package):
    """Returns the last tag information on a given PACKAGE
    """

    if '/' not in package:
        raise RuntimeError('PACKAGE should be specified as "group/name"')

    gl = get_gitlab_instance()

    # we lookup the gitlab group once
    use_package = gl.projects.get(package)
    logger.info('Found gitlab project %s (id=%d)',
        use_package.attributes['path_with_namespace'], use_package.id)

    tag = get_last_tag(use_package)
    date = parse_date(tag.commit['committed_date'])
    click.echo('Lastest tag for %s is %s (%s)' % \
        (package, tag.name, date.strftime('%Y-%m-%d %H:%M:%S')))
