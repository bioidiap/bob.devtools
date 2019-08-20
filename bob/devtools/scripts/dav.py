#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import click
import pkg_resources
from click_plugins import with_plugins

from . import bdt

from ..dav import setup_webdav_client
from ..log import verbosity_option, get_logger, echo_normal, echo_info, \
    echo_warning

logger = get_logger(__name__)


@with_plugins(pkg_resources.iter_entry_points("bdt.dav.cli"))
@click.group(cls=bdt.AliasedGroup)
def dav():
    """Commands for reading/listing/renaming/copying content to a WebDAV server

    Commands defined here may require a username and a password to operate
    properly.
    """
    pass


@dav.command(
    epilog="""
Examples:

  1. List contents of 'public':

     $ bdt dav -vv list


  2. List contents of 'public/databases/latest':

     $ bdt dav -vv list databases/latest


  3. List contents of 'private/docs':

     $ bdt dav -vv list -p docs

"""
)
@click.option(
    "-p",
    "--private/--no-private",
    default=False,
    help="If set, use the 'private' area instead of the public one",
)
@click.option(
    "-l",
    "--long-format/--no-long-format",
    default=False,
    help="If set, print details about each listed file",
)
@click.argument(
    "path",
    default="/",
    required=False,
)
@verbosity_option()
@bdt.raise_on_error
def list(private, long_format, path):
    """List the contents of a given WebDAV directory.
    """

    if not path.startswith('/'): path = '/' + path
    cl = setup_webdav_client(private)
    contents = cl.list(path)
    remote_path = cl.get_url(path)
    echo_info('ls %s' % (remote_path,))
    for k in contents:
        if long_format:
            info = cl.info('/'.join((path, k)))
            echo_normal('%-20s  %-10s  %s' % (info['created'], info['size'], k))
        else:
            echo_normal(k)


@dav.command(
    epilog="""
Examples:

  1. Creates directory 'foo/bar' on the remote server:

     $ bdt dav -vv mkdir foo/bar

"""
)
@click.option(
    "-p",
    "--private/--no-private",
    default=False,
    help="If set, use the 'private' area instead of the public one",
)
@click.argument(
    "path",
    required=True,
)
@verbosity_option()
@bdt.raise_on_error
def makedirs(private, path):
    """Creates a given directory, recursively (if necessary)

    Gracefully exists if the directory is already there.
    """

    if not path.startswith('/'): path = '/' + path
    cl = setup_webdav_client(private)
    remote_path = cl.get_url(path)

    if cl.check(path):
        echo_warning('directory %s already exists' % (remote_path,))

    rpath = ''
    for k in path.split('/'):
        rpath = '/'.join((rpath, k)) if rpath else k
        if not cl.check(rpath):
            echo_info('mkdir %s' % (rpath,))
            cl.mkdir(rpath)


@dav.command(
    epilog="""
Examples:

  1. Removes (recursively), everything under the 'remote/path/foo/bar' path:

     $ bdt dav -vv rmtree remote/path/foo/bar

     Notice this does not do anything for security.  It just displays what it
     would do.  To actually run the rmtree comment pass the --execute flag (or
     -x)


  2. Realy removes (recursively), everything under the 'remote/path/foo/bar'
     path:

     $ bdt dav -vv rmtree --execute remote/path/foo/bar


"""
)
@click.option(
    "-p",
    "--private/--no-private",
    default=False,
    help="If set, use the 'private' area instead of the public one",
)
@click.option(
    "-x",
    "--execute/--no-execute",
    default=False,
    help="If this flag is set, then execute the removal",
)
@click.argument(
    "path",
    required=True,
)
@verbosity_option()
@bdt.raise_on_error
def rmtree(private, execute, path):
    """Removes a whole directory tree from the WebDAV server

    ATTENTION: There is no undo!  Use --execute to execute.
    """

    if not execute:
        echo_warning("!!!! DRY RUN MODE !!!!")
        echo_warning("Nothing is being executed on server.  Use -x to execute.")

    if not path.startswith('/'): path = '/' + path
    cl = setup_webdav_client(private)
    remote_path = cl.get_url(path)

    if not cl.check(path):
        echo_warning('resource %s does not exist' % (remote_path,))
        return

    echo_info('rm -rf %s' % (remote_path,))
    if execute:
        cl.clean(path)


@dav.command(
    epilog="""
Examples:

  1. Uploads a single file to a specific location:

     $ bdt dav -vv copy local/file remote


  2. Uploads various resources at once:

     $ bdt dav -vv copy local/file1 local/dir local/file2 remote

"""
)
@click.option(
    "-p",
    "--private/--no-private",
    default=False,
    help="If set, use the 'private' area instead of the public one",
)
@click.option(
    "-x",
    "--execute/--no-execute",
    default=False,
    help="If this flag is set, then execute the removal",
)
@click.argument(
    "local",
    required=True,
    type=click.Path(file_okay=True, dir_okay=True, exists=True),
    nargs=-1,
)
@click.argument(
    "remote",
    required=True,
)
@verbosity_option()
@bdt.raise_on_error
def upload(private, execute, local, remote):
    """Uploads a local resource (file or directory) to a remote destination

    If the local resource is a directory, it is uploaded recursively.  If the
    remote resource with the same name already exists, an error is raised (use
    rmtree to remove it first).

    If the remote location does not exist, it is an error as well.  As a
    consequence, you cannot change the name of the resource being uploaded with
    this command.

    ATTENTION: There is no undo!  Use --execute to execute.
    """

    if not execute:
        echo_warning("!!!! DRY RUN MODE !!!!")
        echo_warning("Nothing is being executed on server.  Use -x to execute.")

    if not remote.startswith('/'): remote = '/' + remote
    cl = setup_webdav_client(private)

    if not cl.check(remote):
      echo_warning('base remote directory for upload %s does not exist' %
          (remote,))
      return 1

    for k in local:
        actual_remote = remote + os.path.basename(k)
        remote_path = cl.get_url(actual_remote)

        if cl.check(actual_remote):
            echo_warning('resource %s already exists' % (remote_path,))
            echo_warning('remove it first before uploading a new copy')
            continue

        if os.path.isdir(k):
            echo_info('cp -r %s %s' % (k, remote_path))
            if execute:
                cl.upload_directory(local_path=k, remote_path=actual_remote)
        else:
            echo_info('cp %s %s' % (k, remote_path))
            if execute:
                cl.upload_file(local_path=k, remote_path=actual_remote)
