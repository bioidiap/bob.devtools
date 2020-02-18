#!/usr/bin/env python

import click

from . import bdt
from ..log import verbosity_option, get_logger

logger = get_logger(__name__)


@click.command(
    epilog="""
Examples:

  1. Generates the changelog for a single package using merge requests:

     $ bdt gitlab changelog -vvv group/package.xyz changelog.md


  2. The same as above, but dumps the changelog to stdout instead of a file:

     $ bdt gitlab changelog -vvv group/package.xyz


  3. Generates the changelog for a single package looking at commits
     (not merge requests):

     $ bdt gitlab changelog -vvv --mode=commits group/package.xyz changelog.md


  4. Generates the changelog for a single package looking at merge requests starting from a given date of January 1, 2016:

\b
     $ bdt gitlab changelog -vvv --mode=mrs --since=2016-01-01 group/package.xyz changelog.md


  5. Generates a complete list of changelogs for a list of packages (one per line):

\b
     $ bdt gitlab getpath bob/bob.nightlies order.txt
     $ bdt gitlab lasttag bob/bob
     # copy and paste date to next command
     $ bdt gitlab changelog -vvv --since="2018-07-17 10:23:40" order.txt changelog.md
"""
)
@click.argument("target")
@click.argument(
    "changelog",
    type=click.Path(exists=False, dir_okay=False, file_okay=True, writable=True),
    required=False,
)
@click.option(
    "-g",
    "--group",
    default="bob",
    show_default=True,
    help="Gitlab default group name where packages are located (if not "
    'specified using a "/" on the package name - e.g. '
    '"bob/bob.extension")',
)
@click.option(
    "-m",
    "--mode",
    type=click.Choice(["mrs", "tags", "commits"]),
    default="mrs",
    show_default=True,
    help="Changes the way we produce the changelog.  By default, uses the "
    'text in every merge request (mode "mrs"). To use tag annotations, '
    'use mode "tags". If you use "commits" as mode, we use the text '
    "in commits to produce the changelog",
)
@click.option(
    "-s",
    "--since",
    help="A starting date in any format accepted by dateutil.parser.parse() "
    "(see https://dateutil.readthedocs.io/en/stable/parser.html) from "
    "which you want to generate the changelog.  If not set, the package's"
    "last release date will be used",
)
@verbosity_option()
@bdt.raise_on_error
def changelog(target, changelog, group, mode, since):
    """Generates changelog file for package(s) from the Gitlab server.

    This script generates changelogs for either a single package or multiple
    packages, depending on the value of TARGET.  The changelog (in markdown
    format) is written to the output file CHANGELOG.

    There are two modes of operation: you may provide the package name in the
    format ``<gitlab-group>/<package-name>`` (or simply ``<package-name>``, in
    which case the value of ``--group`` will be used). Or, optionally, provide
    an existing file containing a list of packages that will be iterated on.

    For each package, we will contact the Gitlab server and create a changelog
    using merge-requests (default), tags or commits since a given date.  If a
    starting date is not passed, we'll use the date of the last tagged value or
    the date of the first commit, if no tags are available in the package.
    """
    import os
    import sys
    import datetime

    from ..changelog import (
        get_last_tag_date,
        write_tags_with_commits,
        parse_date,
        get_changes_since,
        get_last_tag,
    )
    from ..release import get_gitlab_instance

    gl = get_gitlab_instance()

    # reads package list or considers name to be a package name
    if os.path.exists(target) and os.path.isfile(target):
        logger.info("Reading package names from file %s...", target)
        with open(target, "rt") as f:
            packages = [
                k.strip()
                for k in f.readlines()
                if k.strip() and not k.strip().startswith("#")
            ]
    else:
        logger.info("Assuming %s is a package name (file does not exist)...", target)
        packages = [target]

    # if the user passed a date, convert it
    if since:
        since = parse_date(since)

    # Since tagging packages requires bob.devtools to be tagged first. Add that to the
    # list as well if bob.devtools has changed. Note that bob.devtools can release
    # itself.
    def bdt_has_changes():
        gitpkg = gl.projects.get("bob/bob.devtools")
        tag = get_last_tag(gitpkg)
        last_tag_date = parse_date(tag.commit["committed_date"])
        _, _, commits = get_changes_since(gitpkg, last_tag_date)
        return len(commits)

    if bdt_has_changes():
        packages.insert(0, "bob/bob.devtools")

    # iterates over the packages and dumps required information
    for package in packages:

        if "/" not in package:
            package = "/".join((group, package))

        # retrieves the gitlab package object
        use_package = gl.projects.get(package)
        logger.info(
            "Found gitlab project %s (id=%d)",
            use_package.attributes["path_with_namespace"],
            use_package.id,
        )

        last_release_date = since or get_last_tag_date(use_package)
        logger.info(
            "Retrieving data (mode=%s) since %s",
            mode,
            last_release_date.strftime("%b %d, %Y %H:%M"),
        )

        # add 1s to avoid us retrieving previous release data
        last_release_date += datetime.timedelta(seconds=1)

        if mode == "tags":
            visibility = ("public",)
        else:
            visibility = ("public", "private", "internal")

        if use_package.attributes["namespace"] == use_package.name:
            # skip system meta-package
            logger.warn(
                "Skipping meta package %s...",
                use_package.attributes["path_with_namespace"],
            )
            continue

        if use_package.attributes["visibility"] not in visibility:
            logger.warn(
                'Skipping package %s (visibility not in "%s")...',
                use_package.attributes["path_with_namespace"],
                "|".join(visibility),
            )
            continue

        if (not changelog) or (changelog == "-"):
            changelog_file = sys.stdout
        else:
            changelog_file = open(changelog, "at")

        # write_tags(f, use_package, last_release_date)
        write_tags_with_commits(changelog_file, use_package, last_release_date, mode)
        changelog_file.flush()
