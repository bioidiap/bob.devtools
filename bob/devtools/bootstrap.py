#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Bootstraps a new miniconda installation and prepares it for development."""

import glob
import logging
import os
import platform
import shutil
import subprocess
import sys
import time

_BASE_CONDARC = """\
add_pip_as_python_dependency: false #!final
always_yes: true #!final
anaconda_upload: false #!final
channel_priority: strict #!final
conda_build: #!final
  pkg_format: '2'
default_channels: #!final
  - https://repo.anaconda.com/pkgs/main
channel_alias: https://conda.anaconda.org #!final
quiet: true #!final
remote_connect_timeout_secs: 120.0 #!final
remote_max_retries: 50 #!final
remote_read_timeout_secs: 180.0 #!final
show_channel_urls: true #!final
ssl_verify: false #!final
"""

_SERVER = "http://www.idiap.ch"

_INTERVALS = (
    ("weeks", 604800),  # 60 * 60 * 24 * 7
    ("days", 86400),  # 60 * 60 * 24
    ("hours", 3600),  # 60 * 60
    ("minutes", 60),
    ("seconds", 1),
)
"""Time intervals that make up human readable time slots"""


logger = logging.getLogger(__name__)


def set_environment(name, value, env=os.environ):
    """Function to setup the environment variable and print debug message.

    Args:

      name: The name of the environment variable to set
      value: The value to set the environment variable to
      env: Optional environment (dictionary) where to set the variable at
    """

    env[name] = value
    logger.info('environ["%s"] = %s', name, value)
    return value


def human_time(seconds, granularity=2):
    """Returns a human readable time string like "1 day, 2 hours"."""

    result = []

    for name, count in _INTERVALS:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip("s")
            result.append("{} {}".format(int(value), name))
        else:
            # Add a blank if we're in the middle of other values
            if len(result) > 0:
                result.append(None)

    if not result:
        if seconds < 1.0:
            return "%.2f seconds" % seconds
        else:
            if seconds == 1:
                return "1 second"
            else:
                return "%d seconds" % seconds

    return ", ".join([x for x in result[:granularity] if x is not None])


def run_cmdline(cmd, env=None, **kwargs):
    """Runs a command on a environment, logs output and reports status.

    Parameters:

      cmd (list): The command to run, with parameters separated on a list

      env (dict, Optional): Environment to use for running the program on. If not
        set, use :py:obj:`os.environ`.
    """

    if env is None:
        env = os.environ

    logger.info("(system) %s" % " ".join(cmd))

    start = time.time()

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        bufsize=1,
        universal_newlines=True,
        **kwargs,
    )

    for line in iter(p.stdout.readline, ""):
        sys.stdout.write(line)
        sys.stdout.flush()

    if p.wait() != 0:
        raise RuntimeError(
            "command `%s' exited with error state (%d)"
            % (" ".join(cmd), p.returncode)
        )

    total = time.time() - start

    logger.info("command took %s" % human_time(total))


def touch(path):
    """Python-implementation of the "touch" command-line application."""

    with open(path, "a"):
        os.utime(path, None)


def merge_conda_cache(cache, prefix, name):
    """Merges conda pkg caches and conda-bld folders.

    Args:

      cache: The cached directory (from previous builds)
      prefix: The current prefix (root of conda installation)
      name: The name of the current package
    """

    pkgs_dir = os.path.join(prefix, "pkgs")
    pkgs_urls_txt = os.path.join(pkgs_dir, "urls.txt")
    if not os.path.exists(pkgs_dir):
        logger.info("mkdir -p %s", pkgs_dir)
        os.makedirs(pkgs_dir)
        logger.info("touch %s", pkgs_urls_txt)
        touch(pkgs_urls_txt)

    # move packages on cache/pkgs to pkgs_dir
    cached_pkgs_dir = os.path.join(cache, "pkgs")
    cached_packages = glob.glob(os.path.join(cached_pkgs_dir, "*.tar.bz2"))
    cached_packages.extend(glob.glob(os.path.join(cached_pkgs_dir, "*.conda")))

    cached_packages = [
        k for k in cached_packages if not k.startswith(name + "-")
    ]
    logger.info("Merging %d cached conda packages", len(cached_packages))
    for k in cached_packages:
        dst = os.path.join(pkgs_dir, os.path.basename(k))
        logger.debug("(move) %s -> %s", k, dst)
        os.rename(k, dst)

    # merge urls.txt files
    logger.info("Merging urls.txt files from cache...")
    cached_pkgs_urls_txt = os.path.join(cached_pkgs_dir, "urls.txt")

    if not os.path.exists(cached_pkgs_urls_txt):
        with open(pkgs_urls_txt, "rb") as f1:
            data = set(f1.readlines())
            data = sorted(list(data))
    else:
        # use both cached and actual conda package caches
        with open(pkgs_urls_txt, "rb") as f1, open(
            cached_pkgs_urls_txt, "rb"
        ) as f2:
            data = set(f1.readlines() + f2.readlines())
            data = sorted(list(data))

    with open(pkgs_urls_txt, "wb") as f:
        f.writelines(data)

    pkgs_urls = os.path.join(pkgs_dir, "urls")
    touch(pkgs_urls)

    # move conda-bld build results
    cached_conda_bld = os.path.join(cache, "conda-bld")
    if os.path.exists(cached_conda_bld):
        dst = os.path.join(prefix, "conda-bld")
        logger.info("(move) %s -> %s", cached_conda_bld, dst)
        os.rename(cached_conda_bld, dst)


def ensure_miniconda_sh():
    """Retrieves the miniconda3 installer for the current system.

    Checks the hash of the miniconda3 installer against the expected version,
    if that does not match, erase existing installer and re-downloads new
    installer.
    """

    # WARNING: if you update this version, remember to update hashes below
    # AND our "mirror" in the internal webserver
    path = "/miniconda/Miniconda3-py39_4.10.3-%s-x86_64.sh"
    if platform.system() == "Darwin":
        md5sum = "09bb30a9204ced74ce3c06762cb442fc"
        path = path % "MacOSX"
    else:
        md5sum = "8c69f65a4ae27fb41df0fe552b4a8a3b"
        path = path % "Linux"

    if os.path.exists("miniconda.sh"):
        logger.info("(check) miniconda.sh md5sum (== %s?)", md5sum)
        import hashlib

        actual_md5 = hashlib.md5(open("miniconda.sh", "rb").read()).hexdigest()
        if actual_md5 == md5sum:
            logger.info("Re-using cached miniconda3 installer (hash matches)")
            return
        else:
            logger.info(
                "Erasing cached miniconda3 installer (%s does NOT " "match)",
                actual_md5,
            )
            os.unlink("miniconda.sh")

    # re-downloads installer
    import http.client

    server = ("bobconda.lab.idiap.ch", 8000)  # http

    logger.info("Connecting to http://%s:%d...", *server)
    conn = http.client.HTTPConnection(server[0], port=server[1])
    conn.request("GET", path)
    r1 = conn.getresponse()

    assert (
        r1.status == 200
    ), "Request for http://%s:%d%s - returned status %d " "(%s)" % (
        server[0],
        server[1],
        path,
        r1.status,
        r1.reason,
    )

    dst = "miniconda.sh"
    logger.info(
        "(download) http://%s:%d%s -> %s...", server[0], server[1], path, dst
    )
    with open(dst, "wb") as f:
        f.write(r1.read())


def install_miniconda(prefix, name):
    """Creates a new miniconda installation.

    Args:

      prefix: The path leading to the (new) root of the miniconda installation
      name: The name of this package
    """

    logger.info("Installing miniconda in %s...", prefix)
    ensure_miniconda_sh()

    cached = None
    if os.path.exists(prefix):  # this is the previous cache, move it
        cached = prefix + ".cached"
        if os.path.exists(cached):
            logger.info("(rmtree) %s", cached)
            shutil.rmtree(cached)
        logger.info("(move) %s -> %s", prefix, cached)
        os.rename(prefix, cached)

    run_cmdline(["bash", "miniconda.sh", "-b", "-p", prefix])
    if cached is not None:
        merge_conda_cache(cached, prefix, name)
        shutil.rmtree(cached)


def get_channels(
    public, stable, server, intranet, group, add_dependent_channels=False
):
    """Returns the relevant conda channels to consider if building project.

    The subset of channels to be returned depends on the visibility and
    stability of the package being built.  Here are the rules:

    * public and stable: only returns the public stable channel(s)
    * public and not stable: returns both public stable and beta channels
    * not public and stable: returns both public and private stable channels
    * not public and not stable: returns all channels

    Beta channels have priority over stable channels, if returned.  Public
    channels have priority over private channles, if turned.


    Args:

      public: Boolean indicating if we're supposed to include only public
        channels
      stable: Boolean indicating if we're supposed to include only stable
        channels
      server: The base address of the server containing our conda channels
      intranet: Boolean indicating if we should add "private"/"public" prefixes
        on the conda paths
      group: The group of packages (gitlab namespace) the package we're
        compiling is part of.  Values should match URL namespaces currently
        available on our internal webserver.  Currently, only "bob" or "beat"
        will work.
      add_dependent_channels: If True, will add the defaults and conda-forge
        channels to the list


    Returns: a list of channels that need to be considered.
    """

    if (not public) and (not intranet):
        raise RuntimeError(
            "You cannot request for private channels and set"
            " intranet=False (server=%s) - these are conflicting options"
            % server
        )

    channels = []
    channels_dict = {}

    # do not use '/public' urls for public channels
    prefix = "/software/" + group
    if not stable:
        channels += [server + prefix + "/conda/label/beta"]  # allowed betas
        channels_dict["public/beta"] = channels[-1]

    channels += [server + prefix + "/conda"]
    channels_dict["public/stable"] = channels[-1]

    if not public:
        prefix = "/private"
        if not stable:  # allowed private channels
            channels += [server + prefix + "/conda/label/beta"]  # allowed betas
            channels_dict["private/beta"] = channels[-1]
        channels += [server + prefix + "/conda"]
        channels_dict["private/stable"] = channels[-1]

    upload_channel = channels_dict[
        "{}/{}".format(
            "public" if public else "private", "stable" if stable else "beta"
        )
    ]

    if add_dependent_channels:
        channels += ["defaults", "conda-forge"]

    return channels, upload_channel


def setup_logger(logger, level):
    """Sets-up the logging for this command at level ``INFO``"""

    warn_err = logging.StreamHandler(sys.stderr)
    warn_err.setLevel(logging.WARNING)
    logger.addHandler(warn_err)

    # debug and info messages are written to sys.stdout

    class _InfoFilter:
        def filter(self, record):
            return record.levelno <= logging.INFO

    debug_info = logging.StreamHandler(sys.stdout)
    debug_info.setLevel(logging.DEBUG)
    debug_info.addFilter(_InfoFilter())
    logger.addHandler(debug_info)

    formatter = logging.Formatter("%(levelname)s@%(asctime)s: %(message)s")

    for handler in logger.handlers:
        handler.setFormatter(formatter)

    if level not in range(0, 4):
        raise ValueError(
            "The verbosity level %d does not exist. Please reduce the number of "
            "'--verbose' parameters in your command line" % level
        )
    # set up the verbosity level of the logging system
    log_level = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
    }[level]

    logger.setLevel(log_level)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Bootstraps a new miniconda "
        "installation and prepares it for development"
    )
    parser.add_argument(
        "command",
        choices=["build", "local", "channel"],
        help="How to prepare the current environment. Use: ``build``, to "
        "build bob.devtools, ``local``, to bootstrap deploy or pypi "
        "stages for bob.devtools builds, ``channel`` channel to bootstrap "
        "CI environment for beta/stable builds",
    )
    parser.add_argument(
        "envname",
        nargs="?",
        default="bdt",
        help="The name of the conda environment that will host bdt "
        "[default: %(default)s]",
    )
    parser.add_argument(
        "-n",
        "--name",
        default=os.environ.get("CI_PROJECT_NAME", "bob.devtools"),
        help="The name of the project being built [default: %(default)s]",
    )
    parser.add_argument(
        "-c",
        "--conda-root",
        default=os.environ.get(
            "CONDA_ROOT", os.path.realpath(os.path.join(os.curdir, "miniconda"))
        ),
        help="The location where we should install miniconda "
        "[default: %(default)s]",
    )
    parser.add_argument(
        "-t",
        "--tag",
        default=os.environ.get("CI_COMMIT_TAG", None),
        help="If building a tag, pass it with this flag [default: %(default)s]",
    )
    parser.add_argument(
        "-p",
        "--python",
        default=os.environ.get("PYTHON_VERSION", None),
        help="If a specific python version must be used, "
        "bootstraps a new environment with it [default: %(default)s]",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increases the verbosity level.  We always prints error and "
        "critical messages. Use a single ``-v`` to enable warnings, "
        "two ``-vv`` to enable information messages and three ``-vvv`` "
        "to enable debug messages [default: %(default)s]",
    )

    args = parser.parse_args()

    setup_logger(logger, args.verbose)

    condarc = os.path.join(args.conda_root, "condarc")

    install_miniconda(args.conda_root, args.name)
    conda_bin = os.path.join(args.conda_root, "bin", "conda")

    # creates the condarc file
    condarc = os.path.join(args.conda_root, "condarc")
    logger.info("(create) %s", condarc)
    with open(condarc, "wt") as f:
        # Replaces https://repo.anaconda.com and https://conda.anaconda.org by
        # our proxies, so it is optimized for a CI build.  Notice we consider
        # this script is only executed in this context.  The URL should NOT
        # work outside of Idiap's network.
        f.write(
            _BASE_CONDARC.replace(
                "https://repo.anaconda.com",
                "http://bobconda.lab.idiap.ch:8000",
            ).replace(
                "https://conda.anaconda.org",
                "http://bobconda.lab.idiap.ch:9000",
            )
        )

    conda_version = "4"
    conda_build_version = "3"
    conda_verify_version = "3"

    conda_verbosity = []
    # if args.verbose >= 2:
    #  conda_verbosity = ['-v']
    if args.verbose >= 3:
        conda_verbosity = ["-vv"]

    # print conda information for debugging purposes
    run_cmdline([conda_bin, "info"] + conda_verbosity)

    if args.command == "build":

        # simple - just use the defaults channels when self building
        run_cmdline(
            [conda_bin, "install", "--yes"]
            + conda_verbosity
            + [
                "-n",
                "base",
                "python",
                "conda=%s" % conda_version,
                "conda-build=%s" % conda_build_version,
                "conda-verify=%s" % conda_verify_version,
                "click",
                "twine",  # required for checking readme of python (zip) distro
            ]
        )

    elif args.command == "local":

        # index the locally built packages
        run_cmdline(
            [conda_bin, "install", "--yes"]
            + conda_verbosity
            + [
                "-n",
                "base",
                "python",
                "conda=%s" % conda_version,
                "conda-build=%s" % conda_build_version,
                "conda-verify=%s" % conda_verify_version,
                "twine",  # required for checking readme of python (zip) distro
            ]
        )
        conda_bld_path = os.path.join(args.conda_root, "conda-bld")
        run_cmdline([conda_bin, "index", conda_bld_path])
        channels, _ = get_channels(
            public=True,
            stable=True,
            server=_SERVER,
            intranet=True,
            group="bob",
            add_dependent_channels=True,
        )
        channels = (
            ["--override-channels"]
            + ["--channel=" + conda_bld_path]
            + ["--channel=%s" % k for k in channels]
        )
        conda_cmd = "install" if args.envname in ("base", "root") else "create"
        run_cmdline(
            [conda_bin, conda_cmd, "--yes"]
            + conda_verbosity
            + channels
            + ["-n", args.envname, "bob.devtools"]
        )

    elif args.command == "channel":

        # installs from channel
        channels, _ = get_channels(
            public=True,
            stable=(args.tag is not None),
            server=_SERVER,
            intranet=True,
            group="bob",
            add_dependent_channels=True,
        )

        channels = ["--override-channels"] + [
            "--channel=%s" % k for k in channels
        ]
        conda_cmd = "install" if args.envname in ("base", "root") else "create"
        cmd = (
            [conda_bin, conda_cmd, "--yes"]
            + conda_verbosity
            + channels
            + ["-n", args.envname]
        )
        # can only enforce python version on newly created environments
        if conda_cmd == "create" and args.python is not None:
            cmd += [f"python={args.python}"]
        cmd += ["bob.devtools"]
        if conda_cmd == "install":
            cmd += ["--update-specs"]
        run_cmdline(cmd)
