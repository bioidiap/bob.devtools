#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tools to help CI-based builds and artifact deployment."""


import distutils.version

import git

from .build import load_order_file
from .log import echo_info, get_logger

logger = get_logger(__name__)


def is_master(refname, tag, repodir):
    """Tells if we're on the master branch via ref_name or tag.

    This function checks if the name of the branch being built is "master".  If
    a tag is set, then it checks if the tag is on the master branch.  If so,
    then also returns ``True``, otherwise, ``False``.

    Args:

      refname: The value of the environment variable ``CI_COMMIT_REF_NAME``
      tag: The value of the environment variable ``CI_COMMIT_TAG`` - (may be
        ``None``)

    Returns: a boolean, indicating we're building the master branch **or** that
    the tag being built was issued on the master branch.
    """

    if tag is not None:
        repo = git.Repo(repodir)
        _tag = repo.tag("refs/tags/%s" % tag)
        return _tag.commit in repo.iter_commits(rev="master")

    return refname == "master"


def is_private(baseurl, package):
    """Tells if a given package (with a namespace) is public or private

    This function checks if a fully qualified package in the format
    ``<namespace>/<name>`` is publicly accessible.  It does this by trying to
    access ``info/refs?service=git-upload-pack`` from the package in question.

    This method does **not** rely on the fact the user has access to Gitlab.

    .. warning::

       This method only works for fully qualified package names (i.e.,
       containing at least one forward-slash ``/``).

    Args:

      baseurl: The base URL for the gitlab service to consult
      package: Fully qualified (i.e., with a namespace) package name.  For
        example: ``bob/bob.extension``.

    Returns: a boolean, indicating if the package is private (``True``) or not
    (``False``).
    """

    from urllib.error import HTTPError
    from urllib.request import urlopen

    private = True
    try:
        r = urlopen(
            baseurl + "/" + package + "/info/refs?service=git-upload-pack"
        )
        private = r.getcode() != 200
    except HTTPError as e:
        private = e.getcode() == 401

    return private


def is_stable(package, refname, tag, repodir):
    """Determines if the package being published is stable.

    This is done by checking if a tag was set for the package.  If that is the
    case, we still cross-check the tag is on the "master" branch.  If everything
    checks out, we return ``True``.  Else, ``False``.

    Args:

      package: Package name in the format "group/name"
      refname: The current value of the environment ``CI_COMMIT_REF_NAME``
      tag: The current value of the enviroment ``CI_COMMIT_TAG`` (may be
        ``None``)
      repodir: The directory that contains the clone of the git repository

    Returns: a boolean, indicating if the current build is for a stable release
    """

    if tag is not None:
        logger.info('Project %s tag is "%s"', package, tag)
        parsed_tag = distutils.version.LooseVersion(
            tag[1:]
        ).version  # remove 'v'
        is_prerelease = any([isinstance(k, str) for k in parsed_tag])

        if is_prerelease:
            logger.warn(
                "Pre-release detected - not publishing to stable channels"
            )
            return False

        if is_master(refname, tag, repodir):
            return True
        else:
            logger.warn("Tag %s in non-master branch will be ignored", tag)
            return False

    logger.info("No tag information available at build")
    logger.info("Considering this to be a pre-release build")
    return False


def read_packages(filename):
    """Return a python list of tuples (repository, branch), given a file
    containing one package (and branch) per line.

    Comments are excluded
    """

    lines = load_order_file(filename)

    packages = []
    for line in lines:
        if "," in line:  # user specified a branch
            path, branch = [k.strip() for k in line.split(",", 1)]
            packages.append((path, branch))
        else:
            packages.append((line, "master"))

    return packages


def select_build_file(basename, paths, branch):
    """Selects the file to use for a build.

    This method will return the name of the most adequate build-accessory file
    (conda_build_config.yaml, recipe_append.yaml) for a given build, in this
    order of priority:

    1. The first file found is returned
    2. We first search for a *specific* file if ``branch`` is set
    3. If that file does not exist, returns the unbranded filename if that exists
       in one of the paths
    4. If no candidates exists, returns ``None``

    The candidate filename is built using
    ``os.path.splitext(os.path.basename(basename))[0]``.

    Args:

      basename: Name of the file to use for the search
      paths (list): A list of paths leading to the location of the variants file
        to use.  Priority is given to paths that come first
      branch (str): Optional key to be set when searching for the variants file
        to use.  This is typically the git-branch name of the current branch of
        the repo being built.


    Returns:

      str: A string containing the full, resolved path of the file to use.
      Returns ``None``, if no candidate is found
    """

    import os

    basename, extension = os.path.splitext(os.path.basename(basename))

    if branch:
        specific_basename = "%s-%s" % (basename, branch)
        for path in paths:
            path = os.path.realpath(path)
            candidate = os.path.join(
                path, "%s%s" % (specific_basename, extension)
            )
            if os.path.exists(candidate):
                return candidate

    for path in paths:
        path = os.path.realpath(path)
        candidate = os.path.join(path, "%s%s" % (basename, extension))
        if os.path.exists(candidate):
            return candidate


def select_conda_build_config(paths, branch):
    """Selects the default conda_build_config.yaml.

    See :py:func:`select_build_file` for implementation details.  If no
    build config file is found by :py:func:`select_build_file`, then
    returns the default ``conda_build_config.yaml`` shipped with this
    package.
    """

    from .constants import CONDA_BUILD_CONFIG as default

    return select_build_file(default, paths, branch) or default


def select_conda_recipe_append(paths, branch):
    """Selects the default recipe_append.yaml.

    See :py:func:`select_build_file` for implementation details.  If no
    recipe append file is found by :py:func:`select_build_file`, then
    returns the default ``recipe_append.yaml`` shipped with this
    package.
    """

    from .constants import CONDA_RECIPE_APPEND as default

    return select_build_file(default, paths, branch) or default


def select_user_condarc(paths, branch):
    """Selects the user condarc file to read (if any)

    See :py:func:`select_build_file` for implementation details.  If no
    recipe condarc is found by :py:func:`select_build_file`, then
    returns ``None``.
    """

    return select_build_file("condarc", paths, branch)


def cleanup(dry_run, username, password, includes):
    """Cleans-up WebDAV resources.  Executes if ``dry_run==False`` only.

    Parameters:

        dry_run (bool): If set, then does not execute any action, just print
          what it would do instead.

        username (str): The user to use for interacting with the WebDAV service

        password (str): Password the the above user

        includes (re.SRE_Pattern): A regular expression that matches the names
          of packages that should be considered for clean-up.  For example: for
          Bob and BATL packages, you may use ``^(bob|batl|gridtk).*`` For BEAT
          packages you may use ``^beat.*``

    """

    from .constants import SERVER, WEBDAV_PATHS
    from .dav import remove_old_beta_packages
    from .deploy import _setup_webdav_client

    for public in (True, False):

        server_info = WEBDAV_PATHS[False][public]
        davclient = _setup_webdav_client(
            SERVER, server_info["root"], username, password
        )

        # go through all possible variants:
        archs = [
            "linux-64",
            "linux-32",
            "linux-armv6l",
            "linux-armv7l",
            "linux-ppc64le",
            "osx-64",
            "osx-32",
            "win-64",
            "win-32",
            "noarch",
        ]

        path = server_info["conda"]

        for arch in archs:

            arch_path = "/".join((path, arch))

            if not (davclient.check(arch_path) and davclient.is_dir(arch_path)):
                # it is normal if the directory does not exist
                continue

            server_path = davclient.get_url(arch_path)
            echo_info("Cleaning beta packages from %s" % server_path)
            remove_old_beta_packages(
                client=davclient,
                path=arch_path,
                dry_run=dry_run,
                pyver=True,
                includes=includes,
            )
