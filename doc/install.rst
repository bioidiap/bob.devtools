.. vim: set fileencoding=utf-8 :

.. _bob.devtools.install:


==============
 Installation
==============

You can install this package via conda_ or mamba_, simply pointing to our beta channel.
We provide packages for both 64-bit Linux and MacOS, for Python 3.8+.

.. code-block:: sh

   $ mamba install -n base \
      -c https://www.idiap.ch/software/bob/conda/label/beta \
      -c conda-forge \
      bob.devtools

.. warning::

   Some commands from this package will use the ``mamba`` CLI to install
   packages on new environments.

   If you install bob.devtools on another environment which is not ``base``, a
   new conda package-cache will be created on that environment, possibly
   duplicating the size of your conda installation.  For this reason, we
   recommend you install this package on the ``base`` environment.

Installing bob.devtools will create a terminal command called ``bdt`` which you
must create an alias for it because some ``bdt`` commands require another conda
environment to be activated. Moreover, development of Bob packages depend on
pre-commit_ (pre-commit gets installed as a dependency of bob.devtools) so you
will need an alias for that as well:

.. code-block:: sh

   $ conda activate base
   $ echo "alias bdt=$(which bdt)" >> ~/.bashrc
   # you will also need pre-commit which gets installed when you install bob.devtools
   $ echo "alias pre-commit=$(which pre-commit)" >> ~/.bashrc
   $ source ~/.bashrc
   # test if it works
   $ conda deactivate
   $ bdt --help
   $ pre-commit --help

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
