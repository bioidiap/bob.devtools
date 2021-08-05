#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import click
import conda_build.api
import yaml

from ..bootstrap import set_environment
from ..build import (
    conda_arch,
    get_docserver_setup,
    get_env_directory,
    make_conda_config,
    root_logger_protection,
)
from ..constants import (
    BASE_CONDARC,
    BOBRC_PATH,
    CONDA_BUILD_CONFIG,
    CONDA_RECIPE_APPEND,
    MATPLOTLIB_RCDIR,
    SERVER,
)
from ..log import get_logger, verbosity_option
from . import bdt

logger = get_logger(__name__)


@click.command(
    epilog="""
Examples:

  1. Tests conda package:

\b
     $ bdt test -vv /path/to/conda-package-v1.0.0.conda


  2. Tests multiple conda packages, one after the other:

\b
     $ bdt test -vv /path/to/conda-package-v1.0.0.conda /path/to/other-conda-package-v2.0.0.conda

"""
)
@click.argument(
    "package",
    required=True,
    type=click.Path(file_okay=True, dir_okay=False, exists=True),
    nargs=-1,
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
    "-g",
    "--group",
    show_default=True,
    default="bob",
    help="Group of packages (gitlab namespace) this package belongs to",
)
@click.option(
    "-P",
    "--private/--no-private",
    default=False,
    help="Set this to **include** private channels on your build - "
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
    "-d",
    "--dry-run/--no-dry-run",
    default=False,
    help="Only goes through the actions, but does not execute them "
    "(combine with the verbosity flags - e.g. ``-vvv``) to enable "
    "printing to help you understand what will be done",
)
@click.option(
    "-C",
    "--ci/--no-ci",
    default=False,
    hidden=True,
    help="Use this flag to indicate the build will be running on the CI",
)
@click.option(
    "-A",
    "--test-mark-expr",
    envvar="TEST_MARK_EXPR",
    default="",
    help="Use this flag to avoid running certain tests during the build.  "
    "It forwards all settings to ``nosetests`` via --eval-attr=<settings>``"
    " and ``pytest`` via -m=<settings>.",
)
@verbosity_option()
@bdt.raise_on_error
def test(
    package,
    condarc,
    config,
    append_file,
    server,
    group,
    private,
    stable,
    dry_run,
    ci,
    test_mark_expr,
):
    """Tests (pre-built) package through conda-build with stock configuration.

    This command wraps the execution of conda-build so that you use the
    same conda configuration we use for our CI.  It always set ``--no-
    anaconda-upload``.
    """

    # if we are in a dry-run mode, let's let it be known
    if dry_run:
        logger.warn("!!!! DRY RUN MODE !!!!")
        logger.warn("Nothing will be really built")

    logger.debug(
        'This package is considered part of group "%s" - tunning '
        "conda package and documentation URLs for this...",
        group,
    )

    if condarc is not None:
        logger.info("Loading CONDARC file from %s...", condarc)
        with open(condarc, "rb") as f:
            condarc_options = yaml.load(f, Loader=yaml.FullLoader)
    else:
        # use default
        condarc_options = yaml.load(BASE_CONDARC, Loader=yaml.FullLoader)

    if "channels" not in condarc_options:
        from ..bootstrap import get_channels

        channels, _ = get_channels(
            public=(not private),
            stable=stable,
            server=server,
            intranet=ci,
            group=group,
            add_dependent_channels=True,
        )
        condarc_options["channels"] = channels

    logger.info(
        "Using the following channels during (potential) build:\n  - %s",
        "\n  - ".join(condarc_options["channels"]),
    )

    # test packages from base environment
    prefix = get_env_directory(os.environ["CONDA_EXE"], "base")
    condarc_options["croot"] = os.path.join(prefix, "conda-bld")

    conda_config = make_conda_config(config, None, append_file, condarc_options)

    set_environment("MATPLOTLIBRC", MATPLOTLIB_RCDIR)
    set_environment("BOBRC", BOBRC_PATH)

    # setup BOB_DOCUMENTATION_SERVER environment variable (used for bob.extension
    # and derived documentation building via Sphinx)
    set_environment("DOCSERVER", server)
    doc_urls = get_docserver_setup(
        public=(not private),
        stable=stable,
        server=server,
        intranet=ci,
        group=group,
    )
    set_environment("BOB_DOCUMENTATION_SERVER", doc_urls)

    # this is for testing and may limit which tests run
    set_environment("NOSE_EVAL_ATTR", test_mark_expr)
    set_environment("PYTEST_ADDOPTS", f"-m '{test_mark_expr}'")

    arch = conda_arch()
    for p in package:
        logger.info("Testing %s at %s", p, arch)
        if not dry_run:
            with root_logger_protection():
                conda_build.api.test(p, config=conda_config)
