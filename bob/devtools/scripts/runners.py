#!/usr/bin/env python

import os

import click

from ..log import echo_normal, get_logger, verbosity_option
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


def _get_project(gl, name):

    retval = gl.projects.get(name)
    logger.debug(
        "Found gitlab project %s (id=%d)",
        retval.attributes["path_with_namespace"],
        retval.id,
    )
    return retval


def _get_projects_from_group(gl, name):

    group = gl.groups.get(name)
    logger.debug(
        "Found gitlab group %s (id=%d)",
        group.attributes["path"],
        group.id,
    )
    projects = group.projects.list(all=True, simple=True)
    logger.info(
        "Retrieving details for %d projects in group %s (id=%d). "
        "This may take a while...",
        len(projects),
        group.attributes["path"],
        group.id,
    )
    packages = []
    for k, proj in enumerate(projects):
        packages.append(_get_project(gl, proj.id))
        logger.debug("Got data from project %d/%d", k + 1, len(projects))
    return packages


def _get_projects_from_runner(gl, runner):

    the_runner = gl.runners.get(runner.id)
    logger.info(
        "Retrieving details for %d projects using runner %s (id=%d). "
        "This may take a while...",
        len(the_runner.projects),
        the_runner.description,
        the_runner.id,
    )
    packages = []
    for k, proj in enumerate(the_runner.projects):
        packages.append(_get_project(gl, proj["id"]))
        logger.debug(
            "Got data from project %d/%d", k + 1, len(the_runner.projects)
        )
    return packages


def _get_projects_from_file(gl, filename):

    packages = []
    with open(filename, "rt") as f:
        lines = [k.strip() for k in f.readlines()]
        lines = [k for k in lines if k and not k.startswith("#")]
        logger.info("Loaded %d entries from file %s", len(lines), filename)
        for k, proj in enumerate(lines):
            packages.append(_get_project(gl, proj))
            logger.debug("Got data from project %d/%d", k + 1, len(lines))
    return packages


@click.group(cls=bdt.AliasedGroup)
def runners():
    """Commands for handling runners."""
    pass


@runners.command(
    epilog="""
Examples:

  1. Enables the runner with description "linux-srv01" on all projects inside groups "beat" and "bob":

     $ bdt gitlab runners enable -vv linux-srv01 beat bob


  2. Enables the runner with description "linux-srv02" on a specific project:

     $ bdt gitlab runners enable -vv linux-srv02 bob/bob.extension

"""
)
@click.argument("name")
@click.argument("targets", nargs=-1, required=True)
@click.option(
    "-g",
    "--group/--no-group",
    default=False,
    help="If set, consider the the provided name as a group name",
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
def enable(name, targets, group, dry_run):
    """Enables runners on whole gitlab groups or single projects.

    You may provide project names (like "group/project"), whole groups, and
    files containing list of projects to enable at certain runner at.
    """

    gl = get_gitlab_instance()
    gl.auth()

    the_runner = _get_runner_from_description(gl, name)

    packages = []
    for target in targets:

        if os.path.exists(target):  # it is a file with project names
            packages += _get_projects_from_file(gl, target)

        elif not group:  # it is a specific project
            packages.append(_get_project(gl, target))

        else:  # it is a group - get all projects
            packages += _get_projects_from_group(gl, target)

    for k in packages:

        try:

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
                else:
                    logger.info(
                        "Would enable runner %s (id=%d) for project %s",
                        the_runner.attributes["description"],
                        the_runner.id,
                        k.attributes["path_with_namespace"],
                    )

        except Exception as e:
            logger.error(
                "Ignoring project %s (id=%d): %s",
                k.attributes["path_with_namespace"],
                k.id,
                str(e),
            )


@runners.command(
    epilog="""
Examples:

  1. Disables the runner with description "macmini" in project bob/bob and bob/conda:

\b
     $ bdt gitlab runners disable -vv macmini bob/bob bob/conda


  1. Disables the runner with description "macmini" for all projects in group bob:

\b
     $ bdt gitlab runners disable -vv macmini bob


  2. Disables the runner with description "macpro" on all projects it is associated to.  Notice this command effectively deletes the runner from the gitlab instance:

\b
     $ bdt gitlab runners disable -vv pro

"""
)
@click.argument("name")
@click.argument("targets", nargs=-1, required=False)
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
def disable(name, targets, dry_run):
    """Disables runners on whole gitlab groups or single projects.

    You may provide project names (like "group/project"), whole groups, files
    containing list of projects to load or omit the last argument, in which
    case all projects using this runner will be affected.
    """

    gl = get_gitlab_instance()
    gl.auth()

    the_runner = _get_runner_from_description(gl, name)

    packages = []
    for target in targets:
        if "/" in target:  # it is a specific project
            packages.append(_get_project(gl, target))

        elif os.path.exists(target):  # it is a file with project names
            packages += _get_projects_from_file(gl, target)

        elif isinstance(target, str) and target:  # it is a group
            packages += _get_projects_from_group(gl, target)

    if not targets:
        logger.info("Retrieving all runner associated projects...")
        packages += _get_projects_from_runner(gl, the_runner)

    for k in packages:
        try:

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

            if not disabled:  # disable it
                if not dry_run:
                    k.runners.delete(the_runner.id)
                    logger.info(
                        "Disabled runner %s (id=%d) for project %s",
                        the_runner.attributes["description"],
                        the_runner.id,
                        k.attributes["path_with_namespace"],
                    )
                else:
                    logger.info(
                        "Would disable runner %s (id=%d) for project %s",
                        the_runner.attributes["description"],
                        the_runner.id,
                        k.attributes["path_with_namespace"],
                    )

        except Exception as e:
            logger.error(
                "Ignoring project %s (id=%d): %s",
                k.attributes["path_with_namespace"],
                k.id,
                str(e),
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
