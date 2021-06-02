#!/usr/bin/env python
# vim: set fileencoding=utf-8 :


import datetime
import os
import tempfile

import click
import conda_build.api

from ..log import echo_info
from ..log import echo_warning
from ..log import get_logger
from ..log import verbosity_option
from ..mirror import blacklist_filter
from ..mirror import checksum_packages
from ..mirror import copy_and_clean_patch
from ..mirror import download_packages
from ..mirror import get_json
from ..mirror import get_local_contents
from ..mirror import load_glob_list
from ..mirror import remove_packages
from ..mirror import whitelist_filter
from . import bdt

logger = get_logger(__name__)


@click.command(
    epilog="""
Examples:

  1. Mirrors a conda channel:

\b
     $ bdt mirror -vv https://www.idiap.ch/software/bob/conda/label/beta mirror

    """
)
@click.argument(
    "channel-url",
    required=True,
)
@click.argument(
    "dest-dir",
    type=click.Path(
        exists=False,
        dir_okay=True,
        file_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
    ),
    required=True,
)
@click.option(
    "-b",
    "--blacklist",
    type=click.Path(
        exists=True,
        dir_okay=False,
        file_okay=True,
        readable=True,
        resolve_path=True,
    ),
    help="A file containing a list of globs to exclude from local "
    "mirroring, one per line",
)
@click.option(
    "-w",
    "--whitelist",
    type=click.Path(
        exists=True,
        dir_okay=False,
        file_okay=True,
        readable=True,
        resolve_path=True,
    ),
    help="A file containing a list of globs to include at local "
    "mirroring, one per line.  This is considered *after* "
    "the blacklisting.  It is here just for testing purposes",
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
@click.option(
    "-t",
    "--tmpdir",
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=False,
        readable=True,
        writable=True,
        resolve_path=True,
    ),
    help="A directory where to store temporary files",
)
@click.option(
    "-p",
    "--patch/--no-patch",
    default=False,
    help="If set, then consider we are mirroring the defaults channel "
    "where a patch_instructions.json exists and must be downloaded and "
    "prunned so the mirror works adequately",
)
@click.option(
    "-c",
    "--checksum/--no-checksum",
    default=False,
    help="If set, then packages that are supposed to be kept locally "
    "will be checksummed against the remote repository repodata.json "
    "expectations.  Errors will be reported and packages will be "
    "removed from the local repository",
)
@click.option(
    "-s",
    "--start-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="To filter packages to mirror by date, supply a starting date "
    "in isoformat (yyyy-mm-dd, e.g. 2019-03-30).  If you do so, then only "
    "packages that were recorded at the date or later will be downloaded "
    "to your mirror",
)
@verbosity_option()
@bdt.raise_on_error
def mirror(
    channel_url,
    dest_dir,
    blacklist,
    whitelist,
    check_md5,
    dry_run,
    tmpdir,
    patch,
    checksum,
    start_date,
):
    """Mirrors a conda channel to a particular local destination

    This command is capable of completely mirroring a valid conda channel,
    excluding packages that you may not be interested on via globs.  It works
    to minimize channel usage by first downloading the channel repository data
    (in compressed format), analysing what is available locally and what is
    available on the channel, and only downloading the missing files.
    """

    # creates a self destructing temporary directory that will act as temporary
    # directory for the rest of this program
    tmpdir2 = tempfile.TemporaryDirectory(prefix="bdt-mirror-tmp", dir=tmpdir)
    tempfile.tempdir = tmpdir2.name
    os.environ["TMPDIR"] = tmpdir2.name
    logger.info("Setting $TMPDIR and `tempfile.tempdir` to %s", tmpdir2.name)

    # if we are in a dry-run mode, let's let it be known
    if dry_run:
        logger.warn("!!!! DRY RUN MODE !!!!")
        logger.warn("Nothing will be really mirrored")

    DEFAULT_SUBDIRS = ["noarch", "linux-64", "osx-64"]

    noarch = os.path.join(dest_dir, "noarch")
    if not os.path.exists(noarch):  # first time
        # calls conda index to create basic infrastructure
        logger.info("Creating conda channel at %s...", dest_dir)
        if not dry_run:
            conda_build.api.update_index(
                [dest_dir],
                subdir=DEFAULT_SUBDIRS,
                progress=False,
                verbose=False,
            )

    if start_date is not None:
        start_date = start_date.date()  # only interested on the day itself

    for arch in DEFAULT_SUBDIRS:

        remote_repodata = get_json(channel_url, arch, "repodata_from_packages.json.bz2")

        # merge all available packages into one single dictionary
        remote_package_info = {}
        remote_package_info.update(remote_repodata.get("packages", {}))
        remote_package_info.update(remote_repodata.get("packages.conda", {}))

        logger.info("%d packages available in remote index", len(remote_package_info))
        local_packages = get_local_contents(dest_dir, arch)
        logger.info("%d packages available in local mirror", len(local_packages))

        remote_packages = set(remote_package_info.keys())

        if blacklist is not None and os.path.exists(blacklist):
            globs_to_remove = set(load_glob_list(blacklist))
        else:
            globs_to_remove = set()

        # in the remote packages, subset those that need to be downloaded
        # according to our own interest
        to_download = blacklist_filter(
            remote_packages - local_packages, globs_to_remove
        )

        if whitelist is not None and os.path.exists(whitelist):
            globs_to_consider = set(load_glob_list(whitelist))
            to_download = whitelist_filter(to_download, globs_to_consider)

        # if the user passed a cut date, only download packages that are newer
        # or at the same date than the proposed date
        if start_date is not None:
            too_old = set()
            for k in to_download:
                pkgdate = datetime.datetime.fromtimestamp(
                    remote_package_info[k]["timestamp"] / 1000.0
                ).date()
                if pkgdate < start_date:
                    logger.debug(
                        "Package %s, from %s is older than %s, not downloading",
                        k,
                        pkgdate.isoformat(),
                        start_date.isoformat(),
                    )
                    too_old.add(k)
            logger.info(
                "Filtering out %d older packages from index (older than %s)",
                len(too_old),
                start_date.isoformat(),
            )
            to_download -= too_old

        # in the local packages, subset those that we no longer need, be it
        # because they have been removed from the remote repository, or because
        # we decided to blacklist them.
        disappeared_remotely = local_packages - remote_packages
        to_keep = blacklist_filter(local_packages, globs_to_remove)
        to_delete_locally = (local_packages - to_keep) | disappeared_remotely

        # execute the transaction
        if checksum:
            # double-check if, among packages I should keep, everything looks
            # already with respect to expected checksums from the remote repo
            issues = checksum_packages(remote_repodata, dest_dir, arch, to_keep)
            if issues:
                echo_warning(
                    "Detected %d packages with checksum issues - "
                    "re-downloading after erasing..." % len(issues)
                )
            else:
                echo_info("All local package checksums match expected values")
            remove_packages(issues, dest_dir, arch, dry_run)
            to_download |= issues

        if to_download:
            download_packages(
                to_download,
                remote_repodata,
                channel_url,
                dest_dir,
                arch,
                dry_run,
            )
        else:
            echo_info(
                "Mirror at %s/%s is up-to-date w.r.t. %s/%s. "
                "No packages to download." % (dest_dir, arch, channel_url, arch)
            )

        if to_delete_locally:
            echo_warning(
                "%d packages will be removed at %s/%s"
                % (len(to_delete_locally), dest_dir, arch)
            )
            remove_packages(to_delete_locally, dest_dir, arch, dry_run)
        else:
            echo_info(
                "Mirror at %s/%s is up-to-date w.r.t. blacklist. "
                "No packages to be removed." % (dest_dir, arch)
            )

        if patch:
            # download/cleanup patch instructions, otherwise conda installs may
            # go crazy.  Do this before the indexing, that will use that file
            # to do its magic.
            patch_file = "patch_instructions.json"
            name = copy_and_clean_patch(
                channel_url, dest_dir, arch, patch_file, dry_run
            )
            echo_info(
                "Cleaned copy of %s/%s/%s installed at %s"
                % (channel_url, arch, patch_file, name)
            )

    # re-indexes the channel to produce a conda-compatible setup
    echo_info("Re-indexing %s..." % dest_dir)
    if not dry_run:
        from conda_build.index import MAX_THREADS_DEFAULT

        conda_build.api.update_index(
            [dest_dir],
            check_md5=check_md5,
            progress=True,
            verbose=False,
            subdir=DEFAULT_SUBDIRS,
            threads=MAX_THREADS_DEFAULT,
        )
