#!/usr/bin/env python
# -*- coding: utf-8 -*-

import conda.cli.python_api
import json

from .log import verbosity_option, get_logger, echo_info

logger = get_logger(__name__)


from graphviz import Digraph


def get_graphviz_dependency_graph(
    graph_dict,
    file_name,
    prefix="bob.",
    black_list=["python", "setuptools", "libcxx", "numpy", "libblitz", "boost"],
):
    """
    Given a dictionary with the dependency graph, compute the graphviz DAG and save it
    in SVG
    """

    d = Digraph(format="svg", engine="dot")

    for i in graph_dict:
        for j in graph_dict[i]:
            # Conections to python, setuptools....gets very messy
            if j in black_list:
                continue

            if prefix in j:
                d.attr("node", shape="box")
            else:
                d.attr("node", shape="ellipse")
            d.edge(i, j)
    d.render(file_name)


def compute_dependency_graph(
    package_name, channel=None, selected_packages=[], prefix="bob.", dependencies=dict()
):
    """
    Given a target package, returns an adjacency matrix with its dependencies returned via the command `conda search xxxx --info` 

    **Parameters**
       
       package_name:
          Name of the package
       
       channel:
          Name of the channel to be sent via `-c` option. If None `conda search` will use what is in .condarc

       selected_packages:
          List of target packages. If set, the returned adjacency matrix will be in terms of this list.

       prefix:
          Only seach for deep dependencies under the prefix. This would avoid to go deeper in 
          dependencies not maintained by us, such as, numpy, matplotlib, etc..

       dependencies:
          Dictionary controlling the state of each search

    """

    if package_name in dependencies:
        return dependencies

    dependencies[package_name] = fetch_dependencies(
        package_name, channel, selected_packages
    )
    logger.info(f"  >> Searching dependencies of {package_name}")
    for d in dependencies[package_name]:
        if prefix in d:
            compute_dependency_graph(
                d, channel, selected_packages, prefix, dependencies
            )
    return dependencies


def fetch_dependencies(package_name, channel=None, selected_packages=[]):
    """
    conda search the dependencies of a package

    **Parameters**
        packge_name:
        channel:
        selected_packages:
    """

    # Running conda search and returns to a json file
    if channel is None:
        package_description = conda.cli.python_api.run_command(
            conda.cli.python_api.Commands.SEARCH, package_name, "--info", "--json"
        )
    else:
        package_description = conda.cli.python_api.run_command(
            conda.cli.python_api.Commands.SEARCH,
            package_name,
            "--info",
            "-c",
            channel,
            "--json",
        )

    # TODO: Fix that
    package_description = json.loads(package_description[0])

    # Fetching the dependencies of the most updated package
    all_dependencies = [
        p.split(" ")[0] for p in package_description[package_name][-1]["depends"]
    ]

    if len(selected_packages) > 0:
        # Filtering the dependencies
        return [d for d in selected_packages if d in all_dependencies]

    return all_dependencies
