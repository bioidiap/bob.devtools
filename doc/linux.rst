.. vim: set fileencoding=utf-8 :

.. _bob.devtools.ci.linux:

============================
 Deploying a Linux-based CI
============================

This document contains instructions to build and deploy a new bare-OS CI for
Linux.  Instructions for deployment assume a freshly installed machine, with
Idiap's latest Debian distribution running.  Our builds use Docker images.  We
also configure docker-in-docker to enable to run docker builds (and other
tests) within docker images.


Docker and Gitlab-runner setup
------------------------------

Base docker installation:
https://docs.docker.com/install/linux/docker-ce/debian/

Ensure to add/configure for auto-loading the ``overlay`` kernel module in
``/etc/modules``.  Then update/create ``/etc/docker/daemon.json`` to contain
the entry ``"storage-driver": "overlay2"``.  Restart the daemon.  Eventually
reboot the machine to ensure everything works fine.

To install docker at Idiap, you also need to follow the security guidelines
from Cédric at https://secure.idiap.ch/intranet/system/software/docker.  If you
do not follow such guidelines, the machine will not be acessible from outside
via the login gateway, as the default docker installation conflicts with
Idiap's internal setup.  You may also find other network connectivity issues.

Also, you want to place ``/var/lib/docker`` on a **fast** disk.  Normally, we
have a scratch partition for this.  Follow the instructions at
https://linuxconfig.org/how-to-move-docker-s-default-var-lib-docker-to-another-directory-on-ubuntu-debian-linux
for this step:

.. code-block:: sh

   $ mkdir /scratch/docker
   $ chmod g-rw,o-rw /scratch/docker
   $ service docker stop
   $ rsync -aqxP /var/lib/docker/ /scratch/docker
   $ rm -rf /var/lib/docker
   $ vim /etc/docker/daemon.json  # add data-root -> /scratch/docker
   $ service docker start


Hosts section
=============

We re-direct calls to www.idiap.ch to our internal server, for speed.  Just add
this to `/etc/hosts`:

.. code-block:: sh

   $ echo "" >> /etc/hosts
   $ echo "#We fake www.idiap.ch to keep things internal" >> /etc/hosts
   $ echo "What is the internal server IPv4 address?"
   $ read ipv4add
   $ echo "${ipv4add} www.idiap.ch" >> /etc/hosts
   $ echo "What is the internal server IPv6 address?"
   $ read ipv6add
   $ echo "${ipv6add} www.idiap.ch" >> /etc/hosts


.. note::

   You should obtain the values of the internal IPv4 and IPv6 addresses from
   inside the Idiap network.  We cannot replicate them in this manual for
   security reasons.


Gitlab runner configuration
===========================

Once that is setup, install gitlab-runner from https://docs.gitlab.com/runner/install/linux-repository.html, and then register it https://docs.gitlab.com/runner/register/.

We are currently using this kind of configuration (notice you need to replace
the values of ``<internal.ipv4.address>`` and ``<token>`` on the template below):

.. code-block:: ini

   concurrent = 20
   check_interval = 10

   [session_server]
     session_timeout = 1800

   [[runners]]
     name = "<machine-name>"
     output_limit = 102400
     url = "https://gitlab.idiap.ch/"
     token = "<token>"
     executor = "shell"
     shell = "bash"
     builds_dir = "/scratch/builds"
     cache_dir = "/scratch/cache"

   [[runners]]
     name = "bp-srv01"
     output_limit = 102400
     url = "https://gitlab.idiap.ch/"
     token = "<token>"
     executor = "docker"
     builds_dir = "/scratch/builds"
     cache_dir = "/scratch/cache"
     [runners.docker]
       tls_verify = false
       image = "continuumio/conda-concourse-ci"
       privileged = false
       disable_entrypoint_overwrite = false
       oom_kill_disable = false
       disable_cache = false
       volumes = ["/scratch/cache"]
       shm_size = 0
       extra_hosts = ["www.idiap.ch:<internal.ipv4.address>"]
     [runners.cache]
       Insecure = false


.. note::

   You must make both ``/scratch/builds`` and ``/scratch/cache`` owned by the
   user running the ``gitlab-runner`` process.  Typically, it is
   ``gitlab-runner``.  These commands, in this case, are in order to complete
   the setup::

   .. code-block:: sh

      $ mkdir /scratch/builds
      $ chown gitlab-runner:gitlab-runner /scratch/builds
      $ mkdir /scratch/cache
      $ chown gitlab-runner:gitlab-runner /scratch/cache


Crontabs
========

.. code-block:: sh

   # crontab -l
   MAILTO=""
   @reboot /root/docker-cleanup-service.sh
   0 0 * * * /root/docker-cleanup.sh


The `docker-cleanup-service.sh` is:

.. code-block:: sh

   #!/usr/bin/env sh

   # Continuously running image to ensure minimal space is available

   docker run -d \
       -e LOW_FREE_SPACE=30G \
       -e EXPECTED_FREE_SPACE=50G \
       -e LOW_FREE_FILES_COUNT=2097152 \
       -e EXPECTED_FREE_FILES_COUNT=4194304 \
       -e DEFAULT_TTL=60m \
       -e USE_DF=1 \
       --restart always \
       -v /var/run/docker.sock:/var/run/docker.sock \
       --name=gitlab-runner-docker-cleanup \
       quay.io/gitlab/gitlab-runner-docker-cleanup

The `docker-cleanup.sh` is:

.. code-block:: sh

   #!/usr/bin/env sh

   # Cleans-up docker stuff which is not being used

   # Exited machines which are still dangling
   #Caches are containers that we do not want to delete here
   #echo "Cleaning exited machines..."
   #docker rm -v $(docker ps -a -q -f status=exited)

   # Unused image leafs
   echo "Removing unused image leafs..."
   docker rmi $(docker images --filter "dangling=true" -q --no-trunc)


Conda and shared builds
=======================

To avoid problems with conda and using shared builders, consider creating the
directory ``~gitlab-runner/.conda`` and touching the file
``environments.txt`` in that directory, setting a mode of ``444`` (i.e., make
it read-only).
