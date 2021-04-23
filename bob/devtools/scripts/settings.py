#!/usr/bin/env python


import os
import click

from ..log import echo_info, echo_normal
from ..log import get_logger
from ..log import verbosity_option
from ..release import get_gitlab_instance
from . import bdt
from .runners import (
    _get_project,
    _get_projects_from_file,
    _get_projects_from_group,
)

logger = get_logger(__name__)


def _change_settings(project, info, dry_run):
    """Updates the project settings using ``info``"""

    name = f"{project.namespace['name']}/{project.name}"
    echo_normal(f"Changing {name}...")

    if info.get("archive") is not None:
        if info["archive"]:
            echo_info("  -> archiving")
            if not dry_run:
                project.archive()
        else:
            echo_info("  -> unarchiving")
            if not dry_run:
                project.unarchive()

    if info.get("description") is not None:
        echo_info(f"  -> set description to '{info['description']}'")
        if not dry_run:
            project.description = info["description"]
            project.save()

    if info.get("avatar") is not None:
        echo_info(f"  -> setting avatar to '{info['avatar']}'")
        if not dry_run:
            project.avatar = open(info["avatar"], "rb")
            project.save()


@click.command(
    epilog="""
Examples:

  1. List settings in a gitlab project (bob/bob.devtools):

     $ bdt gitlab settings bob/bob.devtools


  2. Simulates an update to the project description:

     $ bdt gitlab settings --description="new description" --dry-run bob/bob.devtools

"""
)
@click.argument("projects", nargs=-1, required=True)
@click.option(
    "-a",
    "--avatar",
    default=None,
    type=click.Path(file_okay=True, dir_okay=False, exists=True),
    help="Set this to update the project icon (avatar)",
)
@click.option(
    "-D",
    "--description",
    default=None,
    type=str,
    help="Set this to update the project description",
)
@click.option(
    "-A",
    "--archive/--unarchive",
    default=None,
    help="Set this to archive or unarchive a project",
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
def settings(projects, avatar, description, archive, dry_run):
    """Updates project settings"""

    # if we are in a dry-run mode, let's let it be known
    if dry_run:
        logger.warn("!!!! DRY RUN MODE !!!!")
        logger.warn("Nothing is being changed at Gitlab")

    gl = get_gitlab_instance()
    gl_projects = []

    for target in projects:

        if "/" in target:  # it is a specific project
            gl_projects.append(_get_project(gl, target))

        elif os.path.exists(target):  # it is a file with project names
            gl_projects += _get_projects_from_file(gl, target)

        else:  # it is a group - get all projects
            gl_projects += _get_projects_from_group(gl, target)

        for k in gl_projects:

            try:

                logger.info(
                    "Processing project %s (id=%d)",
                    k.attributes["path_with_namespace"],
                    k.id,
                )

                info_to_update = {}

                if avatar is not None:
                    info_to_update["avatar"] = avatar

                if archive is not None:
                    info_to_update["archive"] = archive

                if description is not None:
                    info_to_update["description"] = description

                if not info_to_update:
                    # list current settings
                    s = f"{k.namespace['name']}/{k.name}"
                    if k.archived:
                        s += " [archived]"
                    s += f": {k.description}"
                    echo_normal(s)

                else:
                    _change_settings(k, info_to_update, dry_run)

            except Exception as e:
                logger.error(
                    "Ignoring project %s (id=%d): %s",
                    k.attributes["path_with_namespace"],
                    k.id,
                    str(e),
                )
