.. vim: set fileencoding=utf-8 :

.. _bob.devtools.install:


==============
 Installation
==============

You can install this package via conda_, simply pointing to our stable or beta
channels::

  $ conda create -n bdt -c https://www.idiap.ch/software/bob/conda bob.devtools
  # or, for beta releases:
  $ conda create -n bdt -c https://www.idiap.ch/software/bob/conda/label/beta bob.devtools

We provide packages for both 64-bit Linux and MacOS.  Once installed, you can
use these tools within the created environment like this::

  $ conda activate bdt
  (bdt) $ bdt --help



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

We recommend you set ``chmod 600`` to this file to avoid prying us to read out
your personal token. Once you have your token set up, communication should work
transparently between these gitlab clients and the server.


.. include:: links.rst