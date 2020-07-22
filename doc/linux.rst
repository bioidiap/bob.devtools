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


.. warning::

   Idiap has throttling rules that are typically applied to all machines in the
   lab network.  To avoid issues for newly installed CI nodes, ensure you
   request throttling to be disabled for new CI machines.


Docker and Gitlab-runner setup
------------------------------

Base docker installation:
https://secure.idiap.ch/intranet/system/software/docker

Ensure to add/configure for auto-loading the ``overlay`` kernel module in
``/etc/modules``.  Then update/create ``/etc/docker/daemon.json`` to contain
the entry ``"storage-driver": "overlay2"``.

To ensure that you can control memory and CPU usage for launched docker
containers, you'll need to enable "cgroups" on your machine.  In essence,
change ``/etc/default/grub`` to contain the line
``GRUB_CMDLINE_LINUX="cgroup_enable=memory swapaccount=1"``. Then, re-run
``update-grub`` after such change.

To install docker at Idiap, you also need to follow the security guidelines

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


 Reboot the machine to ensure everything works fine.


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


Access to Idiap's docker registry
=================================

If you want the Idiap docker registry (docker.idiap.ch) to be accessible from
the shell executors, you must also ensure Idiap registry certificates are
available on the host.  You may copy the contents of ``docker.idiap.ch``
directory in this documentation set for that purpose, to the directory
``/etc/docker/certs.d``.  Then, ensure to use something like: ``docker login -u
gitlab-ci-token -p $CI_JOB_TOKEN docker.idiap.ch`` on the (global)
``before_script`` phase in jobs requiring access to the registry.


Repository cloning from CI jobs
===============================

If you'd like to allow the (shell-based) runner to clone repositories other
than the one being built, you need to ensure the following is configured at
``~/.ssh/config`` of the user running the ``gitlab-runner`` process
(typically ``gitlab-runner``):

.. code-block:: text

   Host gitlab.idiap.ch
     ForwardX11 no
     ForwardX11Trusted no
     ForwardAgent yes
     StrictHostKeyChecking no
     ControlMaster auto
     ControlPath /tmp/%r@%h-%p
     ControlPersist 600
     Compression yes

Make sure to use an "https" git-clone strategy in your recipes.


Git
===

The version of git (2.11) shipped with Debian Stretch (9.x) is broken.  The
git-clean command does not honour the ``--exclude`` passed via the
command-line.  I advise you install the most recent version from debian
backports by enabling this repository or configuring it with instructions from
https://backports.debian.org.  To install the newest git version, after an
``apt update``, just run the following command as root:

.. code-block:: sh

   $ apt-get -t stretch-backports install "git"


X11
===

Some utilities such as ``dot`` (graphviz) require X11 support.  If you intend
to make use of the ``shell`` builder and ``graphviz``, you must install basic
X11 support.  Just run the following command as root to fix this:

.. code-block:: sh

   $ apt install libxrender1 libxext6


Crontabs
========

.. code-block:: sh

   # crontab -l
   MAILTO=""
   0 12 * * SUN /usr/share/gitlab-runner/clear-docker-cache


Conda and shared builds
=======================

To avoid problems with conda and using shared builders, consider creating the
directory ``~gitlab-runner/.conda`` and touching the file
``environments.txt`` in that directory, setting a mode of ``444`` (i.e., make
it read-only).


Extra packages
==============

List of extra packages to ensure are installed on the shell environment:

* rsync


Locale
======

Ensure to set the default locale as ``C.UTF-8`` by re-running
``dpkg-reconfigure locales``.  The click (python) package `requires it
<https://click.palletsprojects.com/en/7.x/python3/>`_.
