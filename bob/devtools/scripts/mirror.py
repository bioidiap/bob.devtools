#!/usr/bin/env python
# vim: set fileencoding=utf-8 :


import os
import click

import conda_build.api

from . import bdt
from ..mirror import (
        get_json,
        get_local_contents,
        load_glob_list,
        blacklist_filter,
        download_packages,
        remove_packages,
        )
from ..log import verbosity_option, get_logger, echo_info, echo_warning

logger = get_logger(__name__)


@click.command(
    epilog="""
Examples:

  1. Mirrors a conda channel:

\b
     $ bdt mirror -vv https://www.idiap.ch/software/bob/label/beta

    """
)
@click.argument(
    "channel-url",
    required=True,
)
@click.argument(
    "dest-dir",
    type=click.Path(exists=False, dir_okay=True, file_okay=False,
        writable=True, readable=True, resolve_path=True),
    required=True,
)
@click.option(
    "-b",
    "--blacklist",
    type=click.Path(exists=True, dir_okay=False, file_okay=True,
        readable=True, resolve_path=True),
    help="A file containing a list of globs to exclude from local " \
            "mirroring, one per line",
)
@click.option(
    "-m",
    "--check-md5/--no-check-md5",
    default=False,
    help="If set, then check MD5 sums of all packages during conda-index",
)
@click.option(
    "-d",
    "--dry-run/--no-dry-run",
    default=False,
    help="Only goes through the actions, but does not execute them "
    "(combine with the verbosity flags - e.g. ``-vvv``) to enable "
    "printing to help you understand what will be done",
)
@verbosity_option()
@bdt.raise_on_error
def mirror(
        channel_url,
        dest_dir,
        blacklist,
        check_md5,
        dry_run,
        ):
    """Mirrors a conda channel to a particular local destination

    This command is capable of completely mirroring a valid conda channel,
    excluding packages that you may not be interested on via globs.  It works
    to minimize channel usage by first downloading the channel repository data
    (in compressed format), analysing what is available locally and what is
    available on the channel, and only downloading the missing files.
    """

    # if we are in a dry-run mode, let's let it be known
    if dry_run:
        logger.warn("!!!! DRY RUN MODE !!!!")
        logger.warn("Nothing will be really mirrored")


    DEFAULT_SUBDIRS = ['noarch', 'linux-64', 'osx-64']

    noarch = os.path.join(dest_dir, 'noarch')
    if not os.path.exists(noarch):  #first time
        # calls conda index to create basic infrastructure
        logger.info("Creating conda channel at %s...", dest_dir)
        if not dry_run:
            conda_build.api.update_index([dest_dir], subdir=DEFAULT_SUBDIRS,
                    progress=False)


    for arch in DEFAULT_SUBDIRS:

        remote_repodata = get_json(channel_url, arch, 'repodata.json.bz2')
        logger.info('%d packages available in remote index',
                len(remote_repodata.get('packages', {})))
        local_packages = get_local_contents(dest_dir, arch)
        logger.info('%d packages available in local mirror', len(local_packages))

        remote_packages = set(list(remote_repodata.get('packages', {}).keys()) +
                list(remote_repodata.get('packages.conda', {}).keys()))

        if blacklist is not None and os.path.exists(blacklist):
            globs_to_remove = set(load_glob_list(blacklist))
        else:
            globs_to_remove = set()

        # in the remote packages, subset those that need to be downloaded
        # according to our own interest
        to_download = blacklist_filter(remote_packages - local_packages,
                globs_to_remove)

        # in the local packages, subset those that we no longer need, be it
        # because they have been removed from the remote repository, or because
        # we decided to blacklist them.
        disappeared_remotely = local_packages - remote_packages
        to_keep = blacklist_filter(local_packages, globs_to_remove)
        to_delete_locally = (local_packages - to_keep) | disappeared_remotely

        # execute the transaction
        if to_download:
            download_packages(to_download, remote_repodata, channel_url, dest_dir,
                    arch, dry_run)
        else:
            echo_info("Mirror at %s/%s is up-to-date w.r.t. %s/%s. " \
                    "No packages to download." % (dest_dir, arch, channel_url,
                        arch))

        if to_delete_locally:
            echo_warning("%d packages will be removed at %s/%s" % \
                    (len(to_delete_locally), dest_dir, arch))
            remove_packages(to_delete_locally, dest_dir, arch, dry_run)
        else:
            echo_info("Mirror at %s/%s is up-to-date w.r.t. blacklist. " \
                    "No packages to be removed." % (dest_dir, arch))

    # re-indexes the channel to produce a conda-compatible setup
    echo_info("Re-indexing %s..." % dest_dir)
    if not dry_run:
        conda_build.api.update_index([dest_dir], check_md5=check_md5,
                progress=True)
