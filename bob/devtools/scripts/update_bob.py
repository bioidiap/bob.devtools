#!/usr/bin/env python


import click

from . import bdt
from .common_options import ref_option

from ..log import verbosity_option, get_logger

logger = get_logger(__name__)


@click.command(
    epilog="""
Examples:

bdt gitlab update-bob -vv
"""
)
@ref_option()
@verbosity_option()
@bdt.raise_on_error
def update_bob(ref):
    """Updates the Bob meta package with new packages.
    """
    import tempfile
    from ..ci import read_packages
    from ..release import get_gitlab_instance, download_path

    gl = get_gitlab_instance()

    # download order.txt form bob.nightlies and get the list of packages
    nightlies = gl.projects.get("bob/bob.nightlies")

    with tempfile.NamedTemporaryFile() as f:
        download_path(nightlies, "order.txt", f.name, ref=ref)
        packages = read_packages(f.name)

    # find the list of public packages
    public_packages, private_packages = [], []
    for n, (package, branch) in enumerate(packages):

        if package == "bob/bob":
            continue

        # determine package visibility
        use_package = gl.projects.get(package)
        is_public = use_package.attributes["visibility"] == "public"

        if is_public:
            public_packages.append(package.replace("bob/", ""))
        else:
            private_packages.append(package.replace("bob/", ""))

        logger.debug("%s is %s", package, "public" if is_public else "not public")

    logger.info("Found %d public packages", len(public_packages))
    logger.info(
        "The following packages were not public:\n%s", "\n".join(private_packages)
    )

    # modify conda/meta.yaml and requirements.txt in bob/bob

    logger.info("Updating conda/meta.yaml")
    start_tag = "# LIST OF BOB PACKAGES - START"
    end_tag = "# LIST OF BOB PACKAGES - END"

    with open("conda/meta.yaml", "r+") as f:
        lines = f.read()
        i1 = lines.find(start_tag) + len(start_tag)
        i2 = lines.find(end_tag)

        lines = (
            lines[:i1] + "\n    - ".join([""] + public_packages) + "\n    " + lines[i2:]
        )

        f.seek(0)
        f.write(lines)

    logger.info("Updating requirements.txt")
    with open("requirements.txt", "w") as f:
        f.write("\n".join(public_packages) + "\n")

    click.echo(
        "You may need to add the `  # [linux]` tag in front of linux only "
        "packages in conda/meta.yaml"
    )
