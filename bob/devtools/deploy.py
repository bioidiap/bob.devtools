#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Deployment utilities for conda packages and documentation via webDAV."""


import logging
import os

logger = logging.getLogger(__name__)

# This must be a copy of what is in bootstrap.py.
# Notice this script is also called independently of bob.devtools!
_SERVER = "http://bobconda.lab.idiap.ch"

_WEBDAV_PATHS = {
    True: {  # stable?
        False: {  # visible?
            "root": "/private-upload",
            "conda": "/conda",
            "docs": "/docs",
        },
        True: {  # visible?
            "root": "/public-upload",
            "conda": "/conda",
            "docs": "/docs",
        },
    },
    False: {  # stable?
        False: {  # visible?
            "root": "/private-upload",
            "conda": "/conda/label/beta",
            "docs": "/docs",
        },
        True: {  # visible?
            "root": "/public-upload",
            "conda": "/conda/label/beta",
            "docs": "/docs",
        },
    },
}


def _setup_webdav_client(server, root, username, password):
    """Configures and checks the webdav client."""

    # setup webdav connection
    webdav_options = dict(
        webdav_hostname=server,
        webdav_root=root,
        webdav_login=username,
        webdav_password=password,
    )

    from webdav3 import client as webdav

    retval = webdav.Client(webdav_options)
    assert retval.valid()

    return retval


def deploy_conda_package(
    package, arch, stable, public, username, password, overwrite, dry_run
):
    """Deploys a single conda package on the appropriate path.

    Args:

      package (str): Path leading to the conda package to be deployed
      arch (str): The conda architecture to deploy to (``linux-64``,
        ``linux-aarch64``, ``osx-64``, ``osx-arm64``, ``noarch``, or ``None`` -
        in which case the architecture is going to be guessed from the
        directory where the package sits)
      stable (bool): Indicates if the package should be deployed on a stable
        (``True``) or beta (``False``) channel
      public (bool): Indicates if the package is supposed to be distributed
        publicly or privatly (within Idiap network)
      username (str): The name of the user on the webDAV server to use for
        uploading the package
      password (str): The password of the user on the webDAV server to use for
        uploading the package
      overwrite (bool): If we should overwrite a package with equal name existing
        on the destination directory.  Otherwise, an exception is raised.
      dry_run (bool): If we're supposed to really do the actions, or just log
        messages.
    """

    server_info = _WEBDAV_PATHS[stable][public]
    davclient = _setup_webdav_client(
        _SERVER, server_info["root"], username, password
    )

    basename = os.path.basename(package)
    arch = arch or os.path.basename(os.path.dirname(package))
    remote_path = "%s/%s/%s" % (server_info["conda"], arch, basename)

    if davclient.check(remote_path):
        if not overwrite:
            raise RuntimeError(
                "The file %s/%s already exists on the server "
                "- this can be due to more than one build with deployment "
                "running at the same time.  Re-running the broken builds "
                "normally fixes it" % (_SERVER, remote_path)
            )

        else:
            logger.info(
                "[dav] rm -f %s%s%s", _SERVER, server_info["root"], remote_path
            )
            if not dry_run:
                davclient.clean(remote_path)

    logger.info(
        "[dav] %s -> %s%s%s", package, _SERVER, server_info["root"], remote_path
    )
    if not dry_run:
        davclient.upload(local_path=package, remote_path=remote_path)


def deploy_documentation(
    path,
    package,
    stable,
    latest,
    public,
    branch,
    tag,
    username,
    password,
    dry_run,
):
    """Deploys sphinx documentation to the appropriate webdav locations.

    Args:

      path (str): Path leading to the root of the documentation to be deployed
      package (str): Full name (with namespace) of the package being treated
      stable (bool): Indicates if the documentation corresponds to the latest
        stable build
      latest (bool): Indicates if the documentation being deployed correspond to
        the latest stable for the package or not.  In case the documentation
        comes from a patch release which is not on the master branch, please set
        this flag to ``False``, which will make us avoid deployment of the
        documentation to ``master`` and ``stable`` sub-directories.
      public (bool): Indicates if the documentation is supposed to be distributed
        publicly or privatly (within Idiap network)
      branch (str): The name of the branch for the current build
      tag (str): The name of the tag currently built (may be ``None``)
      username (str): The name of the user on the webDAV server to use for
        uploading the package
      password (str): The password of the user on the webDAV server to use for
        uploading the package
      dry_run (bool): If we're supposed to really do the actions, or just log
        messages.
    """

    # uploads documentation artifacts
    if not os.path.exists(path):
        raise RuntimeError(
            "Documentation is not available at %s - "
            "ensure documentation is being produced for your project!" % path
        )

    server_info = _WEBDAV_PATHS[stable][public]
    davclient = _setup_webdav_client(
        _SERVER, server_info["root"], username, password
    )

    remote_path_prefix = "%s/%s" % (server_info["docs"], package)

    # finds out the correct mixture of sub-directories we should deploy to.
    # 1. if ref-name is a tag, don't forget to publish to 'master' as well -
    # all tags are checked to come from that branch
    # 2. if ref-name is a branch name, deploy to it
    # 3. in case a tag is being published, make sure to deploy to the special
    # "stable" subdir as well
    deploy_docs_to = set([branch])
    if stable:
        if tag is not None:
            deploy_docs_to.add(tag)
        if latest:
            deploy_docs_to.add("master")
            deploy_docs_to.add("stable")

    # creates package directory, and then uploads directory there
    for k in deploy_docs_to:
        if not davclient.check(remote_path_prefix):  # base package directory
            logger.info("[dav] mkdir %s", remote_path_prefix)
            if not dry_run:
                davclient.mkdir(remote_path_prefix)
        remote_path = "%s/%s" % (remote_path_prefix, k)
        logger.info(
            "[dav] %s -> %s%s%s",
            path,
            _SERVER,
            server_info["root"],
            remote_path,
        )
        if not dry_run:
            davclient.upload_directory(local_path=path, remote_path=remote_path)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Deploys documentation from python-only packages"
    )
    parser.add_argument(
        "directory",
        help="Directory containing the sphinx build to deploy",
    )
    parser.add_argument(
        "-p",
        "--package",
        default=os.environ.get("CI_PROJECT_PATH", None),
        help="The package being built [default: %(default)s]",
    )
    parser.add_argument(
        "-x",
        "--visibility",
        default=os.environ.get("CI_PROJECT_VISIBILITY", "private"),
        help="The visibility of the package being built [default: %(default)s]",
    )
    parser.add_argument(
        "-b",
        "--branch",
        default=os.environ.get("CI_COMMIT_REF_NAME", None),
        help="Name of the branch being built [default: %(default)s]",
    )
    parser.add_argument(
        "-t",
        "--tag",
        default=os.environ.get("CI_COMMIT_TAG", None),
        help="If building a tag, pass it with this flag [default: %(default)s]",
    )
    parser.add_argument(
        "-u",
        "--username",
        default=os.environ.get("DOCUSER", None),
        help="Username for webdav deployment [default: %(default)s]",
    )
    parser.add_argument(
        "-P",
        "--password",
        default=os.environ.get("DOCPASS", None),
        help="Password for webdav deployment [default: %(default)s]",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Be verbose (enables INFO logging)",
        action="store_const",
        dest="loglevel",
        default=logging.WARNING,
        const=logging.INFO,
    )

    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    deploy_documentation(
        args.directory,
        package=args.package,
        stable=(args.tag is not None),
        latest=True,
        public=(args.visibility == "public"),
        branch=args.branch,
        tag=args.tag,
        username=args.username,
        password=args.password,
        dry_run=False,
    )
