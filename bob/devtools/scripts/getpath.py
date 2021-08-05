#!/usr/bin/env python

import click

from ..log import get_logger, verbosity_option
from ..release import download_path, get_gitlab_instance
from . import bdt
from .common_options import ref_option

logger = get_logger(__name__)


@click.command(
    epilog="""
Examples:

  1. Get the file ``order.txt`` from nightlies master branch:

     $ bdt gitlab getpath bob/nightlies order.txt


  2. Get the file ``order.txt`` from a different branch ``2.x``:

     $ bdt gitlab getpath --ref=2.x bob/nightlies order.txt


  3. Get the directory ``gitlab`` (and eventual sub-directories) from bob.admin, save outputs in directory ``_ci``:

     $ bdt gitlab getpath bob/bob.admin master gitlab _ci
"""
)
@click.argument("package")
@click.argument("path")
@click.argument("output", type=click.Path(exists=False), required=False)
@ref_option()
@verbosity_option()
@bdt.raise_on_error
def getpath(package, path, output, ref):
    """Downloads files and directories from gitlab.

    Files are downloaded and stored.  Directories are recursed and fully
    downloaded to the client.
    """

    if "/" not in package:
        raise RuntimeError('PACKAGE should be specified as "group/name"')

    gl = get_gitlab_instance()

    # we lookup the gitlab package once
    use_package = gl.projects.get(package)
    logger.info(
        "Found gitlab project %s (id=%d)",
        use_package.attributes["path_with_namespace"],
        use_package.id,
    )
    download_path(use_package, path, output, ref=ref)
