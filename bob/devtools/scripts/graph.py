#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

import click
import yaml

from ..bootstrap import get_channels
from ..bootstrap import set_environment
from ..build import make_conda_config
from ..constants import BASE_CONDARC
from ..constants import CONDA_BUILD_CONFIG
from ..constants import CONDA_RECIPE_APPEND
from ..constants import MATPLOTLIB_RCDIR
from ..constants import SERVER
from ..graph import compute_adjencence_matrix
from ..graph import generate_graph
from ..log import get_logger
from ..log import verbosity_option
from ..release import get_gitlab_instance
from . import bdt

logger = get_logger(__name__)


@click.command(
    epilog="""
Examples:

  1. Calculates and draws the graph of a package:

     $ bdt gitlab graph bob/bob.blitz

  2. Calculates and draws only the runtime dependencies of a package

     $ bdt gitlab graph bob/bob.blitz --deptypes=run

\b
  3. Calculates run and test dependencies of package, but only draws a subset
     defined by a regular expression

\b
     $ bdt gitlab graph beat/beat.editor --deptypes=run --deptypes=test --whitelist='^beat\\.(editor|cmdline).*$'

"""
)
@click.argument("package", required=True)
@click.option(
    "-p",
    "--python",
    default=("%d.%d" % sys.version_info[:2]),
    show_default=True,
    help="Version of python to build the environment for",
)
@click.option(
    "-r",
    "--condarc",
    help="Use custom conda configuration file instead of our own",
)
@click.option(
    "-m",
    "--config",
    "--variant-config-files",
    show_default=True,
    default=CONDA_BUILD_CONFIG,
    help="overwrites the path leading to " "variant configuration file to use",
)
@click.option(
    "-a",
    "--append-file",
    show_default=True,
    default=CONDA_RECIPE_APPEND,
    help="overwrites the path leading to " "appended configuration file to use",
)
@click.option(
    "-S",
    "--server",
    show_default=True,
    default=SERVER,
    help="Server used for downloading conda packages and documentation "
    "indexes of required packages",
)
@click.option(
    "-P",
    "--private/--no-private",
    default=False,
    help="Set this to **include** private channels on your search - "
    "you **must** be at Idiap to execute this build in this case - "
    "you **must** also use the correct server name through --server - "
    "notice this option has no effect to conda if you also pass --condarc",
)
@click.option(
    "-X",
    "--stable/--no-stable",
    default=False,
    help="Set this to **exclude** beta channels from your build - "
    "notice this option has no effect if you also pass --condarc",
)
@click.option(
    "-C",
    "--ci/--no-ci",
    default=False,
    hidden=True,
    help="Use this flag to indicate the graph will be running on the CI",
)
@click.option(
    "-n",
    "--name",
    show_default=True,
    default="graph",
    help="set the graph name",
)
@click.option(
    "-f",
    "--format",
    show_default=True,
    default="svg",
    help="determines the type of output to expect",
)
@click.option(
    "-w",
    "--whitelist",
    show_default=True,
    default="^(bob|beat|batl|gridtk)(\\.)?(?!-).*$",
    help="package regular expression to preserve in the graph, "
    "use .* for keeping all packages, including non-maintained ones.  The "
    "current expression accepts most of our packages, excluding "
    "bob/beat-devel.  This flag only affects the graph generation - we still "
    "recurse over all packages to calculate dependencies.",
)
@click.option(
    "-d",
    "--deptypes",
    show_default=True,
    default=[],
    multiple=True,
    help="types of dependencies to consider.  Pass multiple times to include "
    "more types.  Valid types are 'host', 'build', 'run' and 'test'.  An "
    "empty set considers all dependencies to the graph",
)
@verbosity_option()
@bdt.raise_on_error
def graph(
    package,
    python,
    condarc,
    config,
    append_file,
    server,
    private,
    stable,
    ci,
    name,
    format,
    whitelist,
    deptypes,
):
    """
    Computes the dependency graph of a gitlab package (via its conda recipe)
    and outputs an dot file that can be used by graphviz to draw a direct
    acyclic graph (DAG) of package dependencies.

    This command uses the conda-build API to resolve the package dependencies.
    """

    if "/" not in package:
        raise RuntimeError('PACKAGE should be specified as "group/name"')

    package_group, package_name = package.split("/", 1)

    gl = get_gitlab_instance()

    # get potential channel upload and other auxiliary channels
    channels, upload_channel = get_channels(
        public=(not private),
        stable=stable,
        server=server,
        intranet=ci,
        group=package_group,
    )

    if condarc is not None:
        logger.info("Loading CONDARC file from %s...", condarc)
        with open(condarc, "rb") as f:
            condarc_options = yaml.load(f, Loader=yaml.FullLoader)
    else:
        # use default
        condarc_options = yaml.load(BASE_CONDARC, Loader=yaml.FullLoader)

    if "channels" not in condarc_options:
        condarc_options["channels"] = channels + ["defaults"]

    logger.info(
        "Using the following channels during graph operation:\n  - %s",
        "\n  - ".join(condarc_options["channels"]),
    )

    conda_config = make_conda_config(config, python, append_file, condarc_options)

    set_environment("MATPLOTLIBRC", MATPLOTLIB_RCDIR)

    # setup BOB_DOCUMENTATION_SERVER environment variable (used for bob.extension
    # and derived documentation building via Sphinx)
    set_environment("DOCSERVER", server)
    set_environment("BOB_DOCUMENTATION_SERVER", "/not/set")

    # avoids conda-build complaints
    set_environment("NOSE_EVAL_ATTR", "")
    set_environment("PYTEST_ADDOPTS", "")

    adj_matrix = compute_adjencence_matrix(
        gl, package, conda_config, upload_channel, deptypes=deptypes
    )

    graph = generate_graph(adj_matrix, deptypes=deptypes, whitelist=whitelist)
    graph.render(name, format=format, cleanup=True)
