.. vim: set fileencoding=utf-8 :

.. _bob.devtools.ci.macos:


============================
 Deploying a macOS-based CI
============================

This document contains instructions to build and deploy a new bare-OS CI for
macOS.  Instructions for deployment assume a freshly installed machine.


.. note::

   For sanity, don't use an OS with lower version number than the macOS SDK
   code that will be installed (currently 10.9).  There may be undesired
   consequences.  You may use the latest OS version in case of doubt, but by
   default we recommend the one before the last stable version, for stability.
   So, if the current version is 10.14, a good base install would use 10.13.


Building the reference setup
----------------------------

0. Make sure the computer name is correctly set or execute the following on the
   command-line, as an admin user::

     $ sudo scutil --get LocalHostName
     ...
     $ sudo scutil --get HostName
     ...
     $ sudo scutil --get ComputerName
     ...

     # if applicable, run the following commands

     $ sudo scutil --set LocalHostName "<hostname-without-domain-name>"
     $ sudo scutil --set HostName "<fully-qualified-domain-name>"
     $ sudo scutil --set ComputerName "<fully-qualified-domain-name>"

1. Disable all energy saving features. Go to "System Preferences" then "Energy
   Saver":

   - Enable "Prevent computer from sleeping..."
   - Disable "Put hard disks to sleep when possible"
   - Leave "Wake for network access" enabled
   - You may leave the display on sleep to 10 minutes
2. Create a new user (without administrative priviledges) called ``gitlab``.
   Choose a password to protect access to this user.  In "Login Options",
   select this user to auto-login, type its password to confirm
3. Enable SSH access to the machine by going on ``System Preferences``,
   ``Sharing`` and then selecting ``Remote Login``. Make sure only users on the
   ``Administrators`` group can access the machine.
4. Create as many ``Administrator`` users as required to manage the machine
5. Login as administrator of the machine (so, not on the `gitlab` account).  As
   that user, run the ``admin-install.sh`` script (after copying this repo from
   https://gitlab.idiap.ch/bob/bob.devtools via a zip file download)::

     $ cd
     $ unzip ~/Downloads/bob.devtools-master.zip
     $ cd bob.devtools-master/doc/macos-ci-install
     $ sudo ./admin-install.sh 10.9 gitlab

   Check that script for details on what is installed and the order.  You may
   execute pieces of the script by hand if something fails.  In that case,
   please investigate why it fails and properly fix the scripts so the next
   install runs more smoothly.
6. Enter as gitlab user and install/configure the `gitlab runner`_:

   Configure the runner for `shell executor`_, with local caching.  As
   ``gitlab`` user, execute on the command-line::

     $ gitlab-runner stop
     $ vi .gitlab-runner/config.toml
     $ gitlab-runner start

   Once that is set, your runner configuration should look like this (remove
   comments if gitlab does not like them)::

      concurrent = 8  # set this to the number of cores available
      check_interval = 10  # do **not** leave this to zero

      [[runners]]
        name = "<runner-name>"  # use a suggestive name
        output_limit = 102400  # this value is in kb, so we mean 100 mb
        url = "https://gitlab.idiap.ch"  # this is our gitlab service
        token = "abcdefabcdefabcdefabcdefabcdef"  # this is specific to the conn.
        executor = "shell"  # select this
        builds_dir = "/Users/gitlab/builds"  # set this or bugs occur
        cache_dir = "/Users/gitlab/caches"  # this is optional, but desirable
        shell = "bash"
7. While at the gitlab user, install `Docker for Mac`_.  Ensure to set it up to
   start at login.  In "Preferences > Filesystem Sharing", ensure that
   `/var/folders` is included in the list (that is the default location for
   temporary files in macOS).
8. Reboot the machine. At this point, the gitlab user should be auto-logged and
   the runner process should be executing.  Congratulations, you're done!


.. include:: links.rst