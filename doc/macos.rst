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


.. warning::

   Idiap has throttling rules that are typically applied to all machines in the
   lab network.  To avoid issues for newly installed CI nodes, ensure you
   request throttling to be disabled for new CI machines.


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
2. To be able to send e-mails from the command-line (e.g., when completing
   cronjobs), via the Idiap SMTP, you will need to modify the postfix
   configuration:

   - Edit the file ``/etc/postfix/main.cf`` to add a line stating ``relayhost =
     [smtp.lab.idiap.ch]``  (all e-mails should be routed by this SMTP host)
   - Edit the file ``/etc/postfix/generic`` to add a line stating
     ``admin@hostname.lab.idiap.ch hostname@lab.idiap.ch`` (all e-mails leaving
     the lab infrastruture need to have ``@lab.idiap.ch`` addresses)
   - Run ``postmap /etc/postfix/generic`` as root (required to update the
     internal postfix aliases)
3. Create a new user (without administrative priviledges) called ``gitlab``.
   Choose a password to protect access to this user.  In "Login Options",
   select this user to auto-login, type its password to confirm
4. Enable SSH access to the machine by going on ``System Preferences``,
   ``Sharing`` and then selecting ``Remote Login`` (for ssh) and ``Screen
   Sharing`` (for remote desktop connections). Make sure only users on the
   ``Administrators`` group can access the machine.
5. Create as many ``Administrator`` users as required to manage the machine
6. Login as administrator of the machine (so, not on the `gitlab` account).  As
   that user, run the ``admin-install.sh`` script (after copying this repo from
   https://gitlab.idiap.ch/bob/bob.devtools via a zip file download)::

     $ cd
     $ curl -o bob.devtools-master.zip https://gitlab.idiap.ch/bob/bob.devtools/-/archive/master/bob.devtools-master.zip
     $ unzip ~/Downloads/bob.devtools-master.zip
     $ cd bob.devtools-master/doc/macos-ci-install
     $ sudo ./admin-install.sh 10.9 gitlab

   Check that script for details on what is installed and the order.  You may
   execute pieces of the script by hand if something fails.  In that case,
   please investigate why it fails and properly fix the scripts so the next
   install runs more smoothly.
7. Check the maximum number of files that can be opened on a shell session
   with the command ``launchctl limit maxfiles``.  If smaller than 4096, set
   the maximum number of open files to 4096 by creating the file
   ``/Library/LaunchDaemons/limit.maxfiles.plist`` with the following
   contents::

     <?xml version="1.0" encoding="UTF-8"?>
     <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
       <plist version="1.0">
         <dict>
           <key>Label</key>
             <string>limit.maxfiles</string>
           <key>ProgramArguments</key>
             <array>
               <string>launchctl</string>
               <string>limit</string>
               <string>maxfiles</string>
               <string>4096</string>
               <string>unlimited</string>
             </array>
           <key>RunAtLoad</key>
             <true/>
           <key>ServiceIPC</key>
             <false/>
         </dict>
       </plist>

   At this occasion, verify if the kernel limits are not lower than this value
   using::

     $ sysctl kern.maxfilesperproc
     10240  #example output
     $ sysctl kern.maxfiles
     12288  #example output

   If that is the case (i.e., the values are lower than 4096), set those values
   so they are slightly higher than that new limit with ``sudo sysctl -w
   kern.maxfilesperproc=10240`` and ``sudo sysctl -w kern.maxfiles=12288``
   respectively, for example.
8. Install oh-my-zsh_ for both the admin and gitlab users.  Set ZSH theme "ys".
   Add the following bits to ``.zshrc`` to ensure completions work::

     # Enables homebrew auto-completions for zsh (add: right at the top!)
     if type brew &>/dev/null; then
         FPATH=$(brew --prefix)/share/zsh/site-functions:$FPATH
         ZSH_DISABLE_COMPFIX="true"
     fi

     ...

     # plugins (add: just before sourcing oh-my-zsh)
     plugins=()
     plugins+=(docker)
     plugins+=(git)
     plugins+=(gitfast)
     plugins+=(python)
     plugins+=(themes)
     plugins+=(z)
     plugins+=(zsh-syntax-highlighting)
     plugins+=(history-substring-search)
9. Enter as gitlab user and install/configure the `gitlab runner`_:

   Configure the runner for `shell executor`_, with local caching.  As
   ``gitlab`` user, execute on the command-line::

     # notice that running `brew services gitlab-runner start or restart` will
     # break the configuration of the service once more.  Execute the following
     # to correct for it:
     $ /bin/bash <(curl -s https://gitlab.idiap.ch/bob/bob.devtools/raw/master/doc/macos-ci-install/reconfig-gitlab-runner.sh)

   Once that is set, your runner configuration (``~/.gitlab-runner/config.toml``) should look like this (remove comments if gitlab does not like them)::

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
10. So conda works properly on a shared builder, as the ``gitlab`` user, make
    sure to create an empty, read-only file named
    ``~/.conda/environments.txt``.  Failure to create this file and make it
    read-only to the gitlab user, will create a concurrence issue on the shared
    builder, w.r.t. to conda.
11. While at the gitlab user, install `Docker for Mac`_.  Ensure to set it up to
    start at login.  In "Preferences > Filesystem Sharing", ensure that
    `/var/folders` is included in the list (that is the default location for
    temporary files in macOS).
12. Reboot the machine. At this point, the gitlab user should be auto-logged
    and the runner process should be executing.  Congratulations, you're done!


Running regular updates
-----------------------

We recommend that the CI machine to have homebrew and installed pip packages
updated regularly (once a week).  To do so, setup a cronjob like the following:

.. code-block:: text

   MAILTO=""
   00 12 * * 0 /bin/bash /Users/admin/cron.sh


Inside the file ``/Users/admin/cron.sh``, put the following contents:

.. code-block:: sh

   /bin/bash <(curl -s https://gitlab.idiap.ch/bob/bob.devtools/raw/master/doc/macos-ci-install/update-ci.sh) 2>&1 | mailx -s "Software update (hostname|cimacos)" your.email@idiap.ch

.. note::

   Use the program ``mailx`` instead of ``mail`` that works correctly through
   the SMTP gateway (DMARC sign-off).  Disable cron e-mailing using
   ``MAILTO=""`` as instructed above.  See more details in this thread:
   https://secure.idiap.ch/bugzilla5/show_bug.cgi?id=17529

.. include:: links.rst
