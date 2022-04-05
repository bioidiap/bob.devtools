.. vim: set fileencoding=utf-8 :

.. _bob.devtools.install:


==============
 Installation
==============

You can install this package via conda_, simply pointing to our stable or beta
channels:

.. code-block:: sh

   $ conda install -n base -c https://www.idiap.ch/software/bob/conda bob.devtools
   # or, for beta releases:
   $ conda install -n base -c https://www.idiap.ch/software/bob/conda/label/beta -c https://www.idiap.ch/software/bob/conda bob.devtools

.. warning::

   Some commands from this package will use the ``conda`` CLI to install
   packages on new environments.

   If you install bob.devtools on another environment which is not ``base``, a
   new conda package-cache will be created on that environment, possibly
   duplicating the size of your conda installation.  For this reason, we
   recommend you install this package on the ``base`` environment.

We provide packages for both 64-bit Linux and MacOS, for Python 3.8+.  Once
installed, you can use these tools within the created environment like this:

.. code-block:: sh

   $ conda activate base
   (base) $ bdt --help


You may also hook ``bdt`` on your global ``PATH`` variable, and avoid having to
activate ``base`` to use the command like this:

.. code-block:: sh

   $ ln -s $(which bdt) ~/.local/bin
   # make sure ~/.local/bin is in your $PATH
   $ export PATH=$HOME/.local/bin:$PATH
   # use bdt any time now no matter which conda env is activated
   $ bdt --help


.. _bob.devtools.install.setup:

Setup
=====

Some of the commands in the ``bdt`` command-line application require access to
your gitlab private token, which you can pass at every iteration, or setup at
your ``~/.python-gitlab.cfg``.  Please note that in case you don't set it up,
it will request for your API token on-the-fly, what can be cumbersome and
repeatitive.  Your ``~/.python-gitlab.cfg`` should roughly look like this
(there must be an "idiap" section on it, at least):

.. code-block:: ini

   [global]
   default = idiap
   ssl_verify = true
   timeout = 15

   [idiap]
   url = https://gitlab.idiap.ch
   private_token = <obtain token at your settings page in gitlab>
   api_version = 4

We recommend you set ``chmod 600`` to this file to avoid prying eyes to read
out your personal token. Once you have your token set up, communication should
work transparently between the built-in gitlab client and the server.

If you would like to use the WebDAV interface to our web service for manually
uploading contents, you may also setup the address, username and password for
that server inside the file ``~/.bdtrc``.  Here is a skeleton:

.. code-block:: ini


   [webdav]
   server = http://example.com
   username = username
   password = password

You may obtain these parameters from our internal page explaining the `WebDAV
configuration`_.  For security reasons, you should also set ``chmod 600`` to
this file.

To increment your development environments created with ``bdt dev create`` using
pip-installable packages, create a section named ``create`` in the file
``~/.bdtrc`` with the following contents, e.g.:

.. code-block:: ini

   [create]
   pip_extras = pre-commit

Then, by default, ``bdt dev create`` will automatically pip install
``pre-commit`` at environment creation time.  You may reset this list to your
liking.

.. include:: links.rst
