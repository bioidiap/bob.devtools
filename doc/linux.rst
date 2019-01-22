.. vim: set fileencoding=utf-8 :

.. _bob.devtools.ci.linux:

============================
 Deploying a Linux-based CI
============================

This document contains instructions to build and deploy a new bare-OS CI for
Linux.  Instructions for deployment assume a freshly installed machine, with
Debian 9.x running.  Our builds use Docker images.  We also configure
docker-in-docker to enable to run docker builds (and other tests) within docker
images.


Docker and Gitlab-runner setup
------------------------------

Just follow the advices from https://medium.com/@tonywooster/docker-in-docker-in-gitlab-runners-220caeb708ca


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

We are currently using this (notice you need to replace the values of
``<internal.ipv4.address>`` and ``<token>`` on the template below):

.. code-block:: ini

   concurrent = 4
   check_interval = 10

   [[runners]]
     name = "docker"
     output_limit = 102400
     url = "https://gitlab.idiap.ch/ci"
     token = "<token>"
     executor = "docker"
     limit = 4
     builds_dir = "/local/builds"
     cache_dir = "/local/cache"
     [runners.docker]
       tls_verify = false
       image = "continuumio/conda-concourse-ci"
       privileged = false
       disable_cache = false
       volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/local/cache"]
       extra_hosts = ["www.idiap.ch:<internal.ipv4.address>"]
     [runners.cache]
        Insecure = false

   [[runners]]
     name = "docker-build"
     output_limit = 102400
     executor = "shell"
     shell = "bash"
     url = "https://gitlab.idiap.ch/ci"
     token = "<token>"
     limit = 4
     builds_dir = "/local/builds"
     cache_dir = "/local/cache"


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
