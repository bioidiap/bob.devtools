.. vim: set fileencoding=utf-8 :

.. _bob.devtools.install:


==============
 Installation
==============

You can install this package via mamba_ (advised, but also works with conda_),
simply pointing to our beta channel. We provide packages for both 64-bit Linux
and MacOS, for Python 3.9+.

.. code-block:: sh

   $ mamba install -n base \
      -c https://www.idiap.ch/software/bob/conda/label/beta \
      -c conda-forge \
      bob.devtools

.. tip:: **Alternative install command**

   To avoid long command-lines prefixing the channel list above, it is also
   possible to setup a ``condarc`` file, on the root of your mamba_ (or conda_)
   installation, to contain the following:

   .. code-block:: sh

      $ cat ~/mamba/condarc
      show_channel_urls: true
      channel_priority: strict
      channels:
        - https://www.idiap.ch/software/bob/conda/label/beta
        - https://www.idiap.ch/software/bob/conda
        - conda-forge

   This allows one to issue a simplified installation command-line like the
   following, instead of the long command-line above:

   .. code-block:: sh

      $ mamba install -n base bob.devtools

.. warning::

   Some commands from this package will use the ``mamba`` CLI to install
   packages on new environments.

   If you install bob.devtools on another environment which is not ``base``, a
   new conda package-cache will be created on that environment, possibly
   duplicating the size of your conda installation.  For this reason, we
   recommend you install this package on the ``base`` environment.

Installing bob.devtools will create a terminal command called ``bdt``, which
you can access by first activating the base environment.  You can test this by
running:

.. code-block:: sh

   $ conda activate base
   (base) $ bdt --help
   ...


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
   pip_extras = logging-tree

Then, by default, ``bdt dev create`` will automatically pip install the package
``logging-tree`` at environment creation time.  You may reset this list to your
liking.  Packages for documentation building (Sphinx), testing (pytest), and
quality-assurance (pre-commit) are installed by default and you do not need to
further specify them here.

.. include:: links.rst
