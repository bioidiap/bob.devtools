#!/usr/bin/env python

import os
import sys

import click
import gitlab
import pkg_resources

from click_plugins import with_plugins

from ..log import get_logger, verbosity_option
from . import bdt, ci

logger = get_logger(__name__)


def set_up_environment_variables(python, name_space, project_dir):
    """This function sets up the proper environment variables when user wants
    to run the commands usually run on ci locally."""
    project_dir = os.path.abspath(project_dir)
    project_name = os.path.basename(project_dir)
    gl = gitlab.Gitlab.from_config("idiap")
    package_name = f"{name_space}/{project_name}"
    logger.info("Inferred this package name: %s", package_name)
    try:
        use_package = gl.projects.get(package_name)
    except Exception:
        print(
            f"Could not find {package_name} on Gitlab! "
            "Did you specify the correct group?"
        )
        raise
    project_visibility = use_package.attributes["visibility"]
    os.environ["CI_JOB_TOKEN"] = gl.private_token
    os.environ["CI_PROJECT_DIR"] = project_dir
    os.environ["CI_PROJECT_NAMESPACE"] = name_space
    os.environ["CI_PROJECT_VISIBILITY"] = project_visibility
    if python:
        os.environ["PYTHON_VERSION"] = python


@with_plugins(pkg_resources.iter_entry_points("bdt.local.cli"))
@click.group(cls=bdt.AliasedGroup)
def local():
    """Commands for building packages and handling certain activities locally
    it requires a proper set up for ~/.python-gitlab.cfg.

    Commands defined here can be run in your own installation.
    """
    pass


@local.command(
    epilog="""
Examples:

  1. Prepares the docs locally:

     $ bdt local docs -vv requirements.txt

"""
)
@click.argument(
    "requirement",
    required=True,
    type=click.Path(file_okay=True, dir_okay=False, exists=True),
    nargs=1,
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
    "-p",
    "--python",
    default=("%d.%d" % sys.version_info[:2]),
    show_default=True,
    help="Version of python to build the environment for",
)
@click.option(
    "-g",
    "--group",
    show_default=True,
    default="bob",
    help="Group of packages (gitlab namespace) this package belongs to",
)
@verbosity_option()
@bdt.raise_on_error
@click.pass_context
def docs(ctx, requirement, dry_run, python, group):
    """Prepares documentation build.

    This command:
      \b

      1. Clones all the necessary packages necessary to build the bob/beat
         documentation

      \b

      2. Generates the `extra-intersphinx.txt` and `nitpick-exceptions.txt` file

      \b
    """
    set_up_environment_variables(
        python=python,
        name_space=group,
        project_dir=os.path.dirname(requirement),
    )

    ctx.invoke(ci.docs, requirement=requirement, dry_run=dry_run)


@local.command(
    epilog="""
Examples:

  1. Runs the CI build steps locally:

     $ bdt local build -vv

"""
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
    "-r",
    "--recipe-dir",
    default=os.path.join(os.path.realpath(os.curdir), "conda"),
    help="Custom recipe folder for build.",
)
@click.option(
    "-p",
    "--python",
    default=("%d.%d" % sys.version_info[:2]),
    show_default=True,
    help="Version of python to build the environment for",
)
@click.option(
    "-g",
    "--group",
    show_default=True,
    default="bob",
    help="Group of packages (gitlab namespace) this package belongs to",
)
@verbosity_option()
@bdt.raise_on_error
@click.pass_context
def build(ctx, dry_run, recipe_dir, python, group):
    """Run the CI build step locally."""
    set_up_environment_variables(
        python=python,
        name_space=group,
        project_dir=os.path.join(recipe_dir, ".."),
    )

    ctx.invoke(ci.build, dry_run=dry_run, recipe_dir=recipe_dir)


@local.command(
    epilog="""
Examples:

  1. Runs the CI build steps locally:

     $ bdt local base-build -vv nopython.txt

"""
)
@click.argument(
    "order",
    required=True,
    type=click.Path(file_okay=True, dir_okay=False, exists=True),
    nargs=1,
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
    "-p",
    "--python",
    default=("%d.%d" % sys.version_info[:2]),
    show_default=True,
    help="Version of python to build the environment for",
)
@click.option(
    "-g",
    "--group",
    show_default=True,
    default="bob",
    help="Group of packages (gitlab namespace) this package belongs to",
)
@verbosity_option()
@bdt.raise_on_error
@click.pass_context
def base_build(ctx, order, dry_run, python, group):
    """Run the CI build step locally."""
    set_up_environment_variables(
        python=python, name_space=group, project_dir=os.path.dirname(order)
    )
    ctx.invoke(ci.base_build, order=order, dry_run=dry_run, group=group)
