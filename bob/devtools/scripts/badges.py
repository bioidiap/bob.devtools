#!/usr/bin/env python

import os

import click
import gitlab

from . import bdt
from ..release import get_gitlab_instance, update_files_at_master

from ..log import verbosity_option, get_logger, echo_normal, echo_warning

logger = get_logger(__name__)


# These show on the gitlab project landing page (not visible on PyPI)
PROJECT_BADGES = [
    {
        "name": "Docs (stable)",
        "link_url": "https://www.idiap.ch/software/{group}/docs/%{{project_path}}/stable/index.html",
        "image_url": "https://img.shields.io/badge/docs-stable-yellow.svg",
    },
    {
        "name": "Docs (latest)",
        "link_url": "https://www.idiap.ch/software/{group}/docs/%{{project_path}}/%{{default_branch}}/index.html",
        "image_url": "https://img.shields.io/badge/docs-latest-orange.svg",
    },
    {
        "name": "Pipeline (status)",
        "link_url": "https://gitlab.idiap.ch/%{{project_path}}/commits/%{{default_branch}}",
        "image_url": "https://gitlab.idiap.ch/%{{project_path}}/badges/%{{default_branch}}/pipeline.svg",
    },
    {
        "name": "Coverage (latest)",
        "link_url": "https://gitlab.idiap.ch/%{{project_path}}/commits/%{{default_branch}}",
        "image_url": "https://gitlab.idiap.ch/%{{project_path}}/badges/%{{default_branch}}/coverage.svg",
    },
    {
        "name": "PyPI (version)",
        "link_url": "https://pypi.python.org/pypi/{name}",
        "image_url": "https://img.shields.io/pypi/v/{name}.svg",
    },
]


# These show on the README and will be visible in PyPI
README_BADGES = [
    {
        "name": "Docs (current)",
        "link_url": "https://www.idiap.ch/software/{group}/docs/{group}/{name}/master/index.html",
        "image_url": "https://img.shields.io/badge/docs-available-orange.svg",
    },
    {
        "name": "Pipeline (current)",
        "link_url": "https://gitlab.idiap.ch/{group}/{name}/commits/master",
        "image_url": "https://gitlab.idiap.ch/{group}/{name}/badges/master/pipeline.svg",
    },
    {
        "name": "Coverage (current)",
        "link_url": "https://gitlab.idiap.ch/{group}/{name}/commits/master",
        "image_url": "https://gitlab.idiap.ch/{group}/{name}/badges/master/coverage.svg",
    },
    {
        "name": "Gitlab project",
        "link_url": "https://gitlab.idiap.ch/{group}/{name}",
        "image_url": "https://img.shields.io/badge/gitlab-project-0000c0.svg",
    },
]


def _update_readme(content, info):
    """Updates the README content provided, replacing badges"""

    import re

    new_badges_text = []
    for badge in README_BADGES:
        data = dict((k, v.format(**info)) for (k,v) in badge.items())
        new_badges_text.append(".. image:: {image_url}".format(**data))
        new_badges_text.append("   :target: {link_url}".format(**data))
    new_badges_text = '\n'.join(new_badges_text) + '\n'
    # matches only 3 or more occurences of ..image::/:target: occurences
    expression = r"(\.\.\s*image.+\n\s+:target:\s*.+\b\n){3,}"
    return re.sub(expression, new_badges_text, content)


@click.command(
    epilog="""
Examples:

  1. Creates (by replacing) all existing badges in a gitlab project
     (bob/bob.devtools):

     $ bdt gitlab badges bob/bob.devtools

     N.B.: This command also affects the README.rst file.

"""
)
@click.argument("package")
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
def badges(package, dry_run):
    """Creates stock badges for a project repository"""

    # if we are in a dry-run mode, let's let it be known
    if dry_run:
        logger.warn("!!!! DRY RUN MODE !!!!")
        logger.warn("Nothing is being changed at Gitlab")

    if "/" not in package:
        raise RuntimeError('PACKAGE should be specified as "group/name"')

    gl = get_gitlab_instance()

    # we lookup the gitlab package once
    try:
        use_package = gl.projects.get(package)
        logger.info(
            "Found gitlab project %s (id=%d)",
            use_package.attributes["path_with_namespace"],
            use_package.id,
        )

        badges = use_package.badges.list()
        for badge in badges:
            logger.info(
                "Removing badge '%s' (id=%d) => '%s'",
                badge.name,
                badge.id,
                badge.link_url,
            )
            if not dry_run: badge.delete()

        # creates all stock badges, preserve positions
        info = dict(zip(("group", "name"), package.split("/", 1)))
        for position, badge in enumerate(PROJECT_BADGES):
            data = dict([(k,v.format(**info)) for (k,v) in badge.items()])
            data["position"] = position
            logger.info(
                "Creating badge '%s' => '%s'",
                data["name"],
                data["link_url"],
            )
            if not dry_run: use_package.badges.create(data)

        # download and edit README to setup badges
        readme_file = use_package.files.get(file_path="README.rst", ref="master")
        readme_content = readme_file.decode().decode()
        readme_content = _update_readme(readme_content, info)
        # commit and push changes
        logger.info("Changing README.rst badges...")
        update_files_at_master(use_package, {"README.rst": readme_content},
            "Updated badges section [ci skip]", dry_run)
        logger.info("All done.")

    except gitlab.GitlabGetError as e:
        logger.warn("Gitlab access error - package %s does not exist?", package)
        echo_warning("%s: unknown" % (package,))