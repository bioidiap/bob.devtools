#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
from click_plugins import with_plugins

from ..graph import compute_dependency_graph, get_graphviz_dependency_graph

from ..log import verbosity_option, get_logger, echo_info

logger = get_logger(__name__)


@click.command(
    epilog="""
Example:

   bdt graph bob.bio.face graph


"""
)
@click.argument("package_name", required=True)
@click.argument("output_file", required=True)
@click.option(
    "-c",
    "--channel",
    default=None,
    help="Define a target channel for conda serch. If not set, will use what is set in .condarc",
)
@click.option(
    "-p",
    "--prefix",
    default="bob.",
    help="It will recursivelly look into dependencies whose package name matches the prefix. Default 'bob.'",
)
@verbosity_option()
def graph(package_name, output_file, channel, prefix):
    """
    Compute the dependency graph of a conda package and save it in an SVG file using graphviz.
    """
    logger.info(f"Computing dependency graph")
    graph_dict = compute_dependency_graph(package_name, channel=channel, prefix=prefix)
    logger.info("Generating SVG")
    get_graphviz_dependency_graph(graph_dict, output_file, prefix=prefix)
