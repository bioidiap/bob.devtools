#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Utilities for calculating package dependencies and drawing graphs"""

import os
import re
import glob
import fnmatch
import tempfile
import tarfile
from io import BytesIO

from .bootstrap import set_environment
from .build import (
    next_build_number,
    get_rendered_metadata,
    get_parsed_recipe,
    get_output_path,
)
from .log import get_logger, echo_info

logger = get_logger(__name__)


def compute_adjencence_matrix(
    gl,
    package,
    conda_config,
    main_channel,
    recurse_regexp="^(bob|beat|batl|gridtk)(\.)?(?!-).*$",
    current={},
    ref="master",
    deptypes=[],
):
    """
    Given a target package, returns an adjacence matrix with its dependencies
    returned via the conda-build API

    Parameters
    ----------

    gl : object
        Pre-instantiated instance of the gitlab server API to use, of type
        :py:class:`gitlab.Gitlab`.

    package : str
        Name of the package, including its group in the format
        ``group/package``

    conda_config : dict
        Dictionary of conda configuration options loaded from command-line and
        read from defaults available.

    main_channel : str
        Main channel to consider when looking for the next build number of
        the target package

    recurse_regexp : str
        Regular expression to use, for determining where to recurse for
        resolving dependencies.  Typically, this should be set to a list of
        packages which exists in gitlab.  If it includes more than that, then
        we may not be able to reach the package repository and an error will be
        raised.  The default expression avoids recursing over bob/beat-devel
        packages.

    current : dict
        Current list of packages already inspected - useful for recurrent calls
        to this function, to avoid potential cyclic dependencies.  Corresponds
        to the current return value of this function.

    ref : str
        Name of the git reference (branch, tag or commit hash) to use

    deptypes : list
        A list of dependence types to preserve when building the graph.  If
        empty, then preserve all.  You may set values "build", "host",
        "run" and "test", in any combination


    Returns
    -------

    adjacence_matrix : dict
        A dictionary that contains the dependencies of all packages considered
        in the recursion.  The keys are the name of the packages, the values,
        correspond to the dependencies (host, build, run and test) as a list of
        strings.

    """

    use_package = gl.projects.get(package)
    deptypes = deptypes if deptypes else ["host", "build", "run", "test"]

    if use_package.attributes["path_with_namespace"] in current:
        return current

    echo_info(
        "Resolving graph for %s@%s"
        % (use_package.attributes["path_with_namespace"], ref)
    )
    with tempfile.TemporaryDirectory() as tmpdir:

        logger.debug("Downloading archive for %s...", ref)
        archive = use_package.repository_archive(ref=ref)  # in memory
        logger.debug("Archive has %d bytes", len(archive))

        with tarfile.open(fileobj=BytesIO(archive), mode="r:gz") as f:
            f.extractall(path=tmpdir)

        # use conda-build API to figure out all dependencies
        recipe_dir = glob.glob(os.path.join(tmpdir, "*", "conda"))[0]
        logger.debug("Resolving conda recipe for package at %s...", recipe_dir)
        if not os.path.exists(recipe_dir):
            raise RuntimeError(
                "The conda recipe directory %s does not " "exist" % recipe_dir
            )

        version_candidate = os.path.join(recipe_dir, "..", "version.txt")
        if os.path.exists(version_candidate):
            version = open(version_candidate).read().rstrip()
            set_environment("BOB_PACKAGE_VERSION", version)

        # pre-renders the recipe - figures out the destination
        metadata = get_rendered_metadata(recipe_dir, conda_config)
        rendered_recipe = get_parsed_recipe(metadata)
        path = get_output_path(metadata, conda_config)

        # gets the next build number
        build_number, _ = next_build_number(
            main_channel, os.path.basename(path)
        )

        # at this point, all elements are parsed, I know the package version,
        # build number and all dependencies
        # exclude stuff we are not interested in

        # host and build should have precise numbers to be used for building
        # this package.
        if "host" not in deptypes:
            host = []
        else:
            host = rendered_recipe["requirements"].get("host", [])

        if "build" not in deptypes:
            build = []
        else:
            build = rendered_recipe["requirements"].get("build", [])

        # run dependencies are more vague
        if "run" not in deptypes:
            run = []
        else:
            run = rendered_recipe["requirements"].get("run", [])

        # test dependencies even more vague
        if "test" not in deptypes:
            test = []
        else:
            test = rendered_recipe.get("test", {}).get("requires", [])

        # for each of the above sections, recurse in figuring out dependencies,
        # if dependencies match a target set of globs
        recurse_compiled = re.compile(recurse_regexp)

        def _re_filter(l):
            return [k for k in l if recurse_compiled.match(k)]

        all_recurse = set()
        all_recurse |= set([z.split()[0] for z in _re_filter(host)])
        all_recurse |= set([z.split()[0] for z in _re_filter(build)])
        all_recurse |= set([z.split()[0] for z in _re_filter(run)])
        all_recurse |= set([z.split()[0] for z in _re_filter(test)])

        # complete the package group, which is not provided by conda-build
        def _add_default_group(p):
            if p.startswith("bob") or p.startswith("gridtk"):
                return "/".join(("bob", p))
            elif p.startswith("beat"):
                return "/".join(("beat", p))
            elif p.startswith("batl"):
                return "/".join(("batl", p))
            else:
                logger.warning(
                    "Do not know how to recurse to package %s "
                    "(to which group does it belong?) - skipping...",
                    p,
                )
                return None

        all_recurse = set([_add_default_group(k) for k in all_recurse])
        if None in all_recurse:
            all_recurse.remove(None)

        # do not recurse for packages we already know
        all_recurse -= set(current.keys())
        logger.info(
            "Recursing over the following packages: %s", ", ".join(all_recurse)
        )

        for dep in all_recurse:
            dep_adjmtx = compute_adjencence_matrix(
                gl,
                dep,
                conda_config,
                main_channel,
                recurse_regexp=recurse_regexp,
                ref=ref,
                deptypes=deptypes,
            )
            current.update(dep_adjmtx)

        current[package] = dict(
            host=host,
            build=build,
            run=run,
            test=test,
            version=rendered_recipe["package"]["version"],
            name=rendered_recipe["package"]["name"],
            build_string=os.path.basename(path).split("-")[-1].split(".")[0],
        )

    return current


def generate_graph(adjacence_matrix, deptypes, whitelist):
    """
    Computes a graphviz/dot representation of the build graph

    Parameters
    ----------

        adjacence_matrix : dict
            A dictionary containing the adjacence matrix, that states the
            dependencies for each package in the build, to other packages

        deptypes : list
            A list of dependence types to preserve when building the graph.  If
            empty, then preserve all.  You may set values "build", "host",
            "run" and "test", in any combination

        whitelist : str
            Regular expression for matching strings to preserve while building
            the graph


    Returns
    -------

        graph : graphviz.Digraph
            The generated graph

    """

    from graphviz import Digraph

    whitelist_compiled = re.compile(whitelist)
    deptypes = deptypes if deptypes else ["host", "build", "run", "test"]

    graph = Digraph()
    nodes = {}

    # generate nodes for all packages we want to track explicitly
    for package, values in adjacence_matrix.items():
        if not whitelist_compiled.match(values["name"]):
            logger.debug(
                "Skipping main package %s (did not match whitelist)",
                values["name"],
            )
            continue
        name = (
            values["name"]
            + "\n"
            + values["version"]
            + "\n"
            + values["build_string"]
        )
        nodes[values["name"]] = graph.node(
            values["name"], name, shape="box", color="blue"
        )

    # generates nodes for all dependencies
    for package, values in adjacence_matrix.items():

        # ensures we only have the most complete dependence in the our list
        deps = {}
        to_consider = set()
        for k in deptypes:
            to_consider |= set(values[k])
        for dep in to_consider:
            name = dep.split()[0]
            if name not in deps or (name in deps and not deps[name]):
                deps[name] = dep.split()[1:]

        for ref, parts in deps.items():
            if not whitelist_compiled.match(ref):
                logger.debug(
                    "Skipping dependence %s (did not match whitelist)", ref
                )
                continue

            if not any([k == ref for k in nodes.keys()]):
                # we do not have a node for that dependence, create it
                name = str(ref)  # new string
                if len(parts) >= 1:
                    name += "\n" + parts[0]  # dep version
                if len(parts) >= 2:
                    name += "\n" + parts[1]  # dep build
                nodes[ref] = graph.node(ref, name)

            # connects package -> dep
            graph.edge(values["name"], ref)

    return graph
