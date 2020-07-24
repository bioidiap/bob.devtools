#!/usr/bin/env python
# vim: set fileencoding=utf-8 :


"""Mirroring functionality for conda channels

Some constructs are bluntly copied from
https://github.com/valassis-digital-media/conda-mirror
"""

import bz2
import fnmatch
import hashlib
import json
import os
import random
import tempfile
import time

import requests

from .log import get_logger

logger = get_logger(__name__)


def _download(url, target_directory):
    """Download `url` to `target_directory`

    Parameters
    ----------
    url : str
        The url to download
    target_directory : str
        The path to a directory where `url` should be downloaded

    Returns
    -------
    file_size: int
        The size in bytes of the file that was downloaded
    """

    file_size = 0
    chunk_size = 1024  # 1KB chunks
    logger.info("Download %s -> %s", url, target_directory)
    # create a temporary file
    target_filename = url.split("/")[-1]
    download_filename = os.path.join(target_directory, target_filename)
    with open(download_filename, "w+b") as tf:
        ret = requests.get(url, stream=True)
        size = ret.headers.get("Content-length", "??")
        logger.debug("Saving to %s (%s bytes)", download_filename, size)
        for data in ret.iter_content(chunk_size):
            tf.write(data)
        file_size = os.path.getsize(download_filename)
    return file_size


def _list_conda_packages(local_dir):
    """List the conda packages (*.tar.bz2 or *.conda files) in `local_dir`

    Parameters
    ----------
    local_dir : str
        Some local directory with (hopefully) some conda packages in it

    Returns
    -------
    list
        List of conda packages in `local_dir`
    """
    contents = os.listdir(local_dir)
    return fnmatch.filter(contents, "*.conda") + fnmatch.filter(contents, "*.tar.bz2")


def get_json(channel, platform, name):
    """Get a JSON file for a channel/platform combo on conda channel

    Parameters
    ----------
    channel : str
        Complete channel URL
    platform : {'linux-64', 'osx-64', 'noarch'}
        The platform of interest
    name : str
        The name of the file to retrieve.  If the name ends in '.bz2', then it
        is auto-decompressed

    Returns
    -------
    repodata : dict
        contents of repodata.json
    """

    url = channel + "/" + platform + "/" + name
    logger.debug("[checking] %s...", url)
    r = requests.get(url, allow_redirects=True, stream=True)
    size = r.headers.get("Content-length", "??")
    logger.info("[download] %s (%s bytes)...", url, size)

    if name.endswith(".bz2"):
        # just in case transport encoding was applied
        r.raw.decode_content = True
        data = bz2.decompress(r.raw.read())
        return json.loads(data)

    # else, just decodes the response
    return r.json()


def get_local_contents(path, arch):
    """Returns the local package contents as a set"""

    path_arch = os.path.join(path, arch)
    if not os.path.exists(path_arch):
        return set()

    # path exists, lists currently available packages
    logger.info("Listing package contents of %s...", path_arch)
    contents = os.listdir(path_arch)
    return set(
        fnmatch.filter(contents, "*.tar.bz2") + fnmatch.filter(contents, "*.conda")
    )


def load_glob_list(path):
    """Loads a list of globs from a configuration file

    Excludes comments and empty lines
    """

    retval = [str(k.strip()) for k in open(path, "rt")]
    return [k for k in retval if k and k[0] not in ("#", "-")]


def blacklist_filter(packages, globs):
    """Filters **out** the input package set with the glob list"""

    to_remove = set()
    for k in globs:
        to_remove |= set(fnmatch.filter(packages, k))
    return packages - to_remove


def whitelist_filter(packages, globs):
    """Filters **in** the input package set with the glob list"""

    to_keep = set()
    for k in globs:
        to_keep |= set(fnmatch.filter(packages, k))
    return to_keep


def _sha256sum(filename):
    """Calculates and returns the sha-256 sum given a file name"""

    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(filename, "rb", buffering=0) as f:
        for n in iter(lambda: f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()


def _md5sum(filename):
    """Calculates and returns the md5 sum given a file name"""

    h = hashlib.md5()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(filename, "rb", buffering=0) as f:
        for n in iter(lambda: f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()


def download_packages(packages, repodata, channel_url, dest_dir, arch, dry_run):
    """Downloads remote packages to a download directory

    Packages are downloaded first to a temporary directory, then validated
    according to the expected sha256/md5 sum and then moved, one by one, to the
    destination directory.  An error is raised if the package cannot be
    correctly downloaded.

    Parameters
    ----------
    packages : list of str
        List of packages to download from the remote channel
    repodata: dict
        A dictionary containing the remote repodata.json contents
    channel_url: str
        The complete channel URL
    dest_dir: str
        The local directory where the channel is being mirrored
    arch: str
        The current architecture which we are mirroring
    dry_run: bool
        A boolean flag indicating if this is just a dry-run (simulation),
        flagging so we don't really do anything (set to ``True``).

    """

    # download files into temporary directory, that is removed by the end of
    # the procedure, or if something bad occurs
    with tempfile.TemporaryDirectory() as download_dir:

        total = len(packages)
        for k, p in enumerate(packages):

            k += 1  # adjust to produce correct order on printouts

            # checksum to verify
            if p.endswith(".tar.bz2"):
                expected_hash = repodata["packages"][p].get(
                    "sha256", repodata["packages"][p]["md5"]
                )
            else:
                expected_hash = repodata["packages.conda"][p].get(
                    "sha256", repodata["packages.conda"][p]["md5"]
                )

            # download package to file in our temporary directory
            url = channel_url + "/" + arch + "/" + p
            temp_dest = os.path.join(download_dir, p)
            logger.info("[download: %d/%d] %s -> %s", k, total, url, temp_dest)

            package_retries = 10
            while package_retries:

                if not dry_run:
                    logger.debug("[checking: %d/%d] %s", k, total, url)
                    r = requests.get(url, stream=True, allow_redirects=True)
                    size = r.headers.get("Content-length", "??")
                    logger.info(
                        "[download: %d/%d] %s -> %s (%s bytes)",
                        k,
                        total,
                        url,
                        temp_dest,
                        size,
                    )
                    open(temp_dest, "wb").write(r.raw.read())

                # verify that checksum matches
                if len(expected_hash) == 32:  # md5
                    logger.info(
                        "[verify: %d/%d] md5(%s) == %s?",
                        k,
                        total,
                        temp_dest,
                        expected_hash,
                    )
                else:  # sha256
                    logger.info(
                        "[verify: %d/%d] sha256(%s) == %s?",
                        k,
                        total,
                        temp_dest,
                        expected_hash,
                    )

                if not dry_run:
                    if len(expected_hash) == 32:  # md5
                        actual_hash = _md5sum(temp_dest)
                    else:  # sha256
                        actual_hash = _sha256sum(temp_dest)

                    if actual_hash != expected_hash:
                        wait_time = random.randint(10, 61)
                        logger.warning(
                            "Checksum of locally downloaded "
                            "version of %s does not match "
                            "(actual:%r != %r:expected) - retrying "
                            "after %d seconds",
                            url,
                            actual_hash,
                            expected_hash,
                            wait_time,
                        )
                        os.unlink(temp_dest)
                        time.sleep(wait_time)
                        package_retries -= 1
                        continue
                    else:
                        break

            # final check, before we continue
            assert actual_hash == expected_hash, (
                "Checksum of locally "
                "downloaded version of %s does not match "
                "(actual:%r != %r:expected)" % (url, actual_hash, expected_hash)
            )

            # move
            local_dest = os.path.join(dest_dir, arch, p)
            logger.info("[move: %d/%d] %s -> %s", k, total, temp_dest, local_dest)

            # check local directory is available before moving
            dirname = os.path.dirname(local_dest)
            if not os.path.exists(dirname):
                logger.info("[mkdir] %s", dirname)
                if not dry_run:
                    os.makedirs(dirname)

            if not dry_run:
                os.rename(temp_dest, local_dest)


def remove_packages(packages, dest_dir, arch, dry_run):
    """Removes local packages that no longer matter"""

    total = len(packages)
    for k, p in enumerate(packages):
        k += 1  # adjust to produce correct order on printouts
        path = os.path.join(dest_dir, arch, p)
        logger.info("[remove: %d/%d] %s", k, total, path)
        if not dry_run:
            os.unlink(path)


def _cleanup_json(data, packages):
    """Cleans-up the contents of conda JSON looking at existing packages"""

    # only keys to clean-up here, othere keys remain unchanged
    for key in ("packages", "packages.conda"):
        if key not in data:
            continue
        data[key] = dict((k, v) for k, v in data[key].items() if k in packages)

    return data


def _save_json(data, dest_dir, arch, name, dry_run):
    """Saves contents of conda JSON"""

    destfile = os.path.join(dest_dir, arch, name)
    if not dry_run:
        with open(destfile, "w") as outfile:
            json.dump(data, outfile, ensure_ascii=True, indent=2)
    return destfile


def copy_and_clean_json(url, dest_dir, arch, name, dry_run):
    """Copies and cleans conda JSON file"""

    data = get_json(url, arch, name)
    packages = get_local_contents(dest_dir, arch)
    data = _cleanup_json(data, packages)
    return _save_json(data, dest_dir, arch, name, dry_run)


def copy_and_clean_patch(url, dest_dir, arch, name, dry_run):
    """Copies and cleans conda patch_instructions JSON file"""

    data = get_json(url, arch, name)
    packages = get_local_contents(dest_dir, arch)
    data = _cleanup_json(data, packages)

    # cleanup specific patch_instructions.json fields
    for key in ["remove", "revoke"]:
        data[key] = [k for k in data[key] if k in packages]

    return _save_json(data, dest_dir, arch, name, dry_run)


def checksum_packages(repodata, dest_dir, arch, packages):
    """Checksums packages on the local mirror and compare to remote repository

    Parameters
    ----------
    repodata : dict
        Data loaded from `repodata.json` on the remote repository
    dest_dir : str
        Path leading to local mirror
    arch : str
        Current architecture being considered (e.g. noarch, linux-64 or osx-64)
    packages : list
        List of packages that are available locally, by name

    Returns
    -------
    issues : list
        List of matching errors
    """

    issues = set()
    total = len(packages)
    for k, p in enumerate(packages):

        path_to_package = os.path.join(dest_dir, arch, p)

        # checksum to verify
        if p.endswith(".tar.bz2"):
            expected_hash = repodata["packages"][p].get(
                "sha256", repodata["packages"][p]["md5"]
            )
        else:
            expected_hash = repodata["packages.conda"][p].get(
                "sha256", repodata["packages.conda"][p]["md5"]
            )

        # verify that checksum matches
        if len(expected_hash) == 32:  # md5
            logger.debug(
                "[verify: %d/%d] md5(%s) == %s?",
                k,
                total,
                path_to_package,
                expected_hash,
            )
        else:  # sha256
            logger.debug(
                "[verify: %d/%d] sha256(%s) == %s?",
                k,
                total,
                path_to_package,
                expected_hash,
            )

        if len(expected_hash) == 32:  # md5
            actual_hash = _md5sum(path_to_package)
        else:  # sha256
            actual_hash = _sha256sum(path_to_package)

        if actual_hash != expected_hash:
            logger.warning(
                "Checksum of %s does not match remote "
                "repository description (actual:%r != %r:expected)",
                path_to_package,
                actual_hash,
                expected_hash,
            )
            issues.add(p)

    return issues
