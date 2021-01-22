#!/usr/bin/env python

import click
from click_plugins import with_plugins
import pkg_resources

from ..log import get_logger
from ..log import verbosity_option
from ..log import echo_normal
from ..release import get_gitlab_instance
from . import bdt

logger = get_logger(__name__)


def _get_runner_from_description(gl, descr):

    # search for the runner to affect
    the_runner = [
        k
        for k in gl.runners.list(all=True)
        if k.attributes["description"] == descr
    ]
    if not the_runner:
        raise RuntimeError("Cannot find runner with description = %s", descr)
    the_runner = the_runner[0]
    logger.info(
        "Found runner %s (id=%d)",
        the_runner.attributes["description"],
        the_runner.attributes["id"],
    )

    return the_runner


@with_plugins(pkg_resources.iter_entry_points("bdt.gitlab.cli"))
@click.group(cls=bdt.AliasedGroup)
def runners():
    """Commands for handling runners."""
    pass


@runners.command(
    epilog="""
Examples:

  1. Enables the runner with description "linux-srv01" on all projects inside group "beat":

     $ bdt gitlab runners enable -vv beat linux-srv01


  2. Enables the runner with description "linux-srv02" on a specific project:

     $ bdt gitlab runners enable -vv bob/bob.extension linux-srv02

"""
)
@click.argument("target")
@click.argument("name")
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
def enable(target, name, dry_run):
    """Enables runners on whole gitlab groups or single projects."""

    gl = get_gitlab_instance()
    gl.auth()

    the_runner = _get_runner_from_description(gl, name)

    if "/" in target:  # it is a specific project
        packages = [gl.projects.get(target)]
        logger.debug(
            "Found gitlab project %s (id=%d)",
            packages[0].attributes["path_with_namespace"],
            packages[0].id,
        )

    else:  # it is a group - get all projects
        logger.warn("Retrieving group by name - may take long...")
        group = gl.groups.get(target)
        logger.debug(
            "Found gitlab group %s (id=%d)", group.attributes["path"], group.id
        )
        logger.warn(
            "Retrieving all projects (with details) from group "
            "%s (id=%d)...",
            group.attributes["path"],
            group.id,
        )
        packages = [
            gl.projects.get(k.id)
            for k in group.projects.list(all=True, simple=True)
        ]
        logger.info(
            "Found %d projects under group %s",
            len(packages),
            group.attributes["path"],
        )

    for k in packages:
        logger.info(
            "Processing project %s (id=%d)",
            k.attributes["path_with_namespace"],
            k.id,
        )

        # checks if runner is not enabled first
        enabled = False
        for ll in k.runners.list(all=True):
            if ll.id == the_runner.id:  # it is there already
                logger.warn(
                    "Runner %s (id=%d) is already enabled for project %s",
                    ll.attributes["description"],
                    ll.id,
                    k.attributes["path_with_namespace"],
                )
                enabled = True
                break

        if not enabled:  # enable it
            if not dry_run:
                k.runners.create({"runner_id": the_runner.id})
            logger.info(
                "Enabled runner %s (id=%d) for project %s",
                the_runner.attributes["description"],
                the_runner.id,
                k.attributes["path_with_namespace"],
            )


@runners.command(
    epilog="""
Examples:

  1. Disables the runner with description "macmini" for all active projects in group "bob":

     $ bdt gitlab runners disable -vv bob macmini


  2. Disables the runner with description "macmini" on all projects it is associated to:

     $ bdt gitlab runners disable -vv __all__ macmini


"""
)
@click.argument("target")
@click.argument("name")
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
def disable(target, name, dry_run):
    """Disables runners on whole gitlab groups or single projects."""

    gl = get_gitlab_instance()
    gl.auth()

    the_runner = _get_runner_from_description(gl, name)

    if "/" in target:  # it is a specific project
        packages = [gl.projects.get(target)]
        logger.debug(
            "Found gitlab project %s (id=%d)",
            packages[0].attributes["path_with_namespace"],
            packages[0].id,
        )

    elif target != "__all__":  # it is a group - get all projects
        logger.warn("Retrieving group by name - may take long...")
        group = gl.groups.get(target)
        logger.debug(
            "Found gitlab group %s (id=%d)", group.attributes["path"], group.id
        )
        logger.warn(
            "Retrieving all projects (with details) from group "
            "%s (id=%d)...",
            group.attributes["path"],
            group.id,
        )
        packages = [
            gl.projects.get(k.id)
            for k in group.projects.list(all=True, simple=True)
        ]
        logger.info(
            "Found %d projects under group %s",
            len(packages),
            group.attributes["path"],
        )

    else:  # disables from everywhere
        logger.warn("Retrieving all runner associated projects...")
        # gets extended version of object
        the_runner = gl.runners.get(the_runner.id)
        packages = [gl.projects.get(k['id']) for k in the_runner.projects]
        logger.info(
            "Found %d projects using runner %s",
            len(packages),
            the_runner.description,
        )

    for k in packages:
        logger.info(
            "Processing project %s (id=%d)",
            k.attributes["path_with_namespace"],
            k.id,
        )

        # checks if runner is not already disabled first
        disabled = True
        for ll in k.runners.list(all=True):
            if ll.id == the_runner.id:  # it is there already
                logger.debug(
                    "Runner %s (id=%d) is enabled for project %s",
                    ll.attributes["description"],
                    ll.id,
                    k.attributes["path_with_namespace"],
                )
                disabled = False
                break

        if not disabled:  # enable it
            if not dry_run:
                k.runners.delete(the_runner.id)
            logger.info(
                "Disabled runner %s (id=%d) for project %s",
                the_runner.attributes["description"],
                the_runner.id,
                k.attributes["path_with_namespace"],
            )


@runners.command(
    epilog="""
Examples:

  1. Lists all projects a runner is associated to

     $ bdt gitlab runners list -vv macmini

"""
)
@click.argument("name")
@verbosity_option()
@bdt.raise_on_error
def list(name):
    """Lists projects a runner is associated to"""

    gl = get_gitlab_instance()
    gl.auth()

    the_runner = _get_runner_from_description(gl, name)

    logger.info("Retrieving all runner associated projects...")
    # gets extended version of object
    the_runner = gl.runners.get(the_runner.id)
    logger.info(
        "Found %d projects using runner %s",
        len(the_runner.projects),
        the_runner.description,
    )

    for k in the_runner.projects:
        echo_normal(k["path_with_namespace"])
