#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import configparser

from distutils.version import StrictVersion

from .log import get_logger, echo_warning, echo_info
from .deploy import _setup_webdav_client

logger = get_logger(__name__)


def _get_config():
    """Returns a dictionary with server parameters, or ask them to the user"""

    # tries to figure if we can authenticate using a configuration file
    cfgs = ["~/.bdt.cfg"]
    cfgs = [os.path.expanduser(k) for k in cfgs]
    for k in cfgs:
        if os.path.exists(k):
            data = configparser.ConfigParser()
            data.read(k)
            if (
                "webdav" not in data
                or "server" not in data["webdav"]
                or "username" not in data["webdav"]
                or "password" not in data["webdav"]
            ):
                assert KeyError, (
                    "The file %s should contain a single "
                    '"dav" section with 3 variables defined inside: '
                    '"server", "username", "password".' % (k,)
                )
            return data["dav"]

    # ask the user for the information, cache credentials for future use
    retval = dict()
    retval["server"] = input("The base address of the server: ")
    retval["username"] = input("Username: ")
    retval["password"] = input("Password: ")

    # record file for the user
    data = configparser.ConfigParser()
    data["webdav"] = retval
    with open(cfgs[0], "w") as f:
        logger.warn('Recorded "%s" configuration file for next queries')
        data.write(f)
    os.chmod(cfgs[0], 0o600)
    logger.warn('Changed mode of "%s" to be read-only to you')

    return retval


def setup_webdav_client(private):
    """Returns a ready-to-use WebDAV client"""

    config = _get_config()
    root = "/private-upload" if private else "/public-upload"
    c = _setup_webdav_client(
        config["server"], root, config["username"], config["password"]
    )
    return c


def remove_old_beta_packages(client, path, dry_run, pyver=True):
    """Removes old conda packages from a conda channel.

    What is an old package depends on how the packages are produced.  In
    BEAT/Bob, we build new beta packages with every commit in the CI and we
    want to delete the old ones using this script so that we do not run out of
    space.

    The core idea is to remove packages that are not (the latest version AND
    the latest build number) for each package name.

    Our CI distributes its build into several jobs.  Since each job runs
    independently of each other (per OS and per Python version), the build
    numbers are estimated independently and they will end up to be different
    between jobs.

    So the core idea is needed to be applied on each CI job independently.


    Parameters:

        client (object): The WebDAV client with a preset public/private path

        path (str): A path, within the preset root of the client, where to
        search for beta packages.  Beta packages are searched in the directory
        itself.

        dry_run (bool): A flag indicating if we should just list what we will
        be doing, or really execute the deletions

        pyver (:py:class:`bool`, Optional): If ``True``, the python version of
        a package will be a part of a package's name. This is need to account
        for the fact that our CI jobs run per Python version.

    """

    server_path = client.get_url(path)

    if not client.is_dir(path):
        echo_warning("Path %s is not a directory - ignoring...", server_path)
        return

    betas = dict()
    # python version regular expression:
    pyver_finder = re.compile("py[1-9][0-9]h.*")

    for f in client.list(path):

        if f.startswith("."):
            continue
        if not f.endswith(".tar.bz2"):
            continue

        name, version, build_string = f[:-8].rsplit("-", 2)
        hash_, build = build_string.rsplit("_", 1)

        if pyver:
            # try to find the python version if it exists
            result = pyver_finder.match(hash_)
            if result is not None:
                name += "/" + result.string[:4]

        target = '/'.join((path, f))
        info = client.info(target)

        betas.setdefault(name, []).append(
            (
                StrictVersion(version),
                int(build),  # build number
                info['modified'],
                target,
            )
        )

    import ipdb; ipdb.set_trace()

    count = sum([len(k) for k in betas.values()]) - len(betas)
    echo_info(" - %d variants" % len(betas))
    echo_info(" - %d packages found" % count)
    echo_info(" --------------------")

    for name in sorted(betas.keys()):
        echo_info(" - packages for %s (%d) ====" % (name, len(betas[name])))
        sorted_packages = sorted(betas[name])
        keep_version, keep_build, _, _ = sorted_packages[-1]
        for version, build, mtime, target in sorted_packages:
            if version == keep_version and build == keep_build:
                echo_info("[keep] %s (time=%u)" % (target, mtime))
            else:
                echo_info("rm %s (time=%u)" % (target, mtime))
                if not dry_run:
                    #client.clean(target)
                    echo_info("boooom")
