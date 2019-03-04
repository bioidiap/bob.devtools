#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Deployment utilities for conda packages and documentation via webDAV'''



from .constants import WEBDAV_PATHS, SERVER
from .log import get_logger
logger = get_logger(__name__)


def _setup_webdav_client(server, root, username, password):
  '''Configures and checks the webdav client'''

  # setup webdav connection
  webdav_options = dict(webdav_hostname=server, webdav_root=root,
      webdav_login=username, webdav_password=password)

  from .webdav3 import client as webdav

  retval = webdav.Client(webdav_options)
  assert retval.valid()

  return retval


def deploy_conda_package(package, stable, public, username, password,
    overwrite, dry_run):
  '''Deploys a single conda package on the appropriate path

  Args:

    package (str): Path leading to the conda package to be deployed
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

  '''

  server_info = WEBDAV_PATHS[stable][public]
  davclient = _setup_webdav_client(SERVER, server_info['root'], username,
      password)

  logger.info('Deploying %s to %s%s%s...', package, SERVER,
      server_info['root'], server_info['conda'])

  basename = os.path.basename(package)
  remote_path = '%s/%s/%s' % (server_info['conda'], arch, basename)

  if davclient.check(remote_path):
    if not overwrite:
      raise RuntimeError('The file %s/%s already exists on the server ' \
          '- this can be due to more than one build with deployment ' \
          'running at the same time.  Re-running the broken builds ' \
          'normally fixes it' % (SERVER, remote_path))

    else:
      logger.info('[dav] rm -f %s%s%s', SERVER, server_info['root'],
          remote_path)
      if not dry_run:
        davclient.clean(remote_path)

  logger.info('[dav] %s -> %s%s%s', package, SERVER, server_info['root'],
      remote_path)
  if not dry_run:
    davclient.upload(local_path=package, remote_path=remote_path)

    logger.debug('Removing local copy (%s) to avoid re-uploads', k)
    os.unlink(package)


def deploy_documentation(path, package, stable, public, branch, tag, username,
    password, dry_run):
  '''Deploys sphinx documentation to the appropriate webdav locations

  Args:

    path (str): Path leading to the root of the documentation to be deployed
    package (str): Full name (with namespace) of the package being treated
    stable (bool): Indicates if the documentation corresponds to the latest
      stable build
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

  '''

  # uploads documentation artifacts
  if not os.path.exists(path):
    raise RuntimeError('Documentation is not available at %s - ' \
        'ensure documentation is being produced for your project!' % path)

  server_info = WEBDAV_PATHS[stable][public]
  davclient = _setup_webdav_client(SERVER, server_info['root'], username,
      password)

  remote_path_prefix = '%s/%s' % (server_info['docs'], package)

  # finds out the correct mixture of sub-directories we should deploy to.
  # 1. if ref-name is a tag, don't forget to publish to 'master' as well -
  # all tags are checked to come from that branch
  # 2. if ref-name is a branch name, deploy to it
  # 3. in case a tag is being published, make sure to deploy to the special
  # "stable" subdir as well
  deploy_docs_to = set([branch])
  if stable:
    deploy_docs_to.add('master')
    if tag is not None:
      deploy_docs_to.add(tag)
    deploy_docs_to.add('stable')

  for k in deploy_docs_to:
    remote_path = '%s/%s' % (remote_path_prefix, k)
    logger.info('[dav] %s -> %s%s%s', path, SERVER, server_info['root'],
        remote_path)
    if not dry_run:
      davclient.upload_directory(local_path=path, remote_path=remote_path)
