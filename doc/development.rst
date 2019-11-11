.. _bob.devtools.development:

===============================
 Local development of packages
===============================

Very often, developers are confronted with the need to
clone package repositories locally and develop installation/build and runtime code.
It is recommended to create isolated environments to develop new projects using conda_ and zc.buildout_. 
Tools implemented in `bob.devtools` helps automate this process for |project| packages. In the following we talk about how to checkout and build one or several packages from their git_ source and build proper isolated environments to develop them. Then we will describe how to create a new bob package from scratch and develop existing bob packages along side it. 

TLDR
====

Suppose you want to checkout the package ``bob.blitz`` from source and start developing it locally. We will use the tools implemented in ``bob.devtools`` to create a proper developing environment to build and develop ``bob.blitz``. We assume you have ``bob.devtools`` installed on a conda environment named ``bdt`` (Refer to :ref:`bob.devtools.install` for detailed information.) 

* Checkout the source of the package from git:

.. code-block:: sh

   $ git clone https://gitlab.idiap.ch/bob/bob.blitz

* Create a proper conda environment:

.. code-block:: sh

   $ cd bob.blitz
   $ conda activate bdt
   $ bdt create -vv dev
   $ conda deactivate
   $ conda activate dev

* Build the package using buildout:

.. code-block:: sh

   $ buildout
   $ ./bin/python  # you should use this python to run things from now on

for example:

.. code-block:: python

    >>> import bob.blitz
    >>> bob.blitz # should print from '.../bob.blitz/bob/blitz/...'
    <module 'bob.blitz' from '.../bob.blitz/bob/blitz/__init__.py'>
    >>> print(bob.blitz.get_config())
    bob.blitz: 2.0.20b0 [api=0x0202] (.../bob.blitz)
    * C/C++ dependencies:
      - Blitz++: 0.10
      - Boost: 1.67.0
      - Compiler: {'name': 'gcc', 'version': '7.3.0'}
      - NumPy: {'abi': '0x01000009', 'api': '0x0000000D'}
      - Python: 3.6.9
    * Python dependencies:
      - bob.extension: 3.2.1b0 (.../envs/dev/lib/python3.6/site-packages)
      - click: 7.0 (.../envs/dev/lib/python3.6/site-packages)
      - click-plugins: 1.1.1 (.../envs/dev/lib/python3.6/site-packages)
      - numpy: 1.16.4 (.../envs/dev/lib/python3.6/site-packages)
      - setuptools: 41.0.1 (.../envs/dev/lib/python3.6/site-packages)

* You can optionally run the test suit to check your installation:

.. code-block:: sh

   $ ./bin/nosetests -sv



.. * Install dependencies for `bob.extension` and `bob.blitz` using `conda install` command. You can find out the required dependencies by looking at `conda/meta.yaml` file for each package.

 code-block:: sh

..     $ conda install gcc_linux-64 gxx_linux-64 libblitz


.. note::
    
    Sometimes when you are calling a function not interactively it is not acting normally. In that case import ``pkg_resources`` before importing your package. It is a known issue and we are working on it.

    .. code-block:: sh

        $ ./bin/python -c "import pkg_resources; import bob.blitz; print(bob.blitz)"


.. bob.devtools.local_development:

Local development of existing packages
======================================
To develop existing |project| packages you need to checkout their source code and create a proper development environment using `buildout`.


Checking out package sources
----------------------------
|project| packages are developed through gitlab_. Various packages exist
in |project|'s gitlab_ instance. In the following we assume you want to install and build locally the ``bob.blitz`` package. In order to checkout a package, just use git_:


.. code-block:: sh

   $ git clone https://gitlab.idiap.ch/bob/bob.blitz


Create an isolated conda environment
------------------------------------

Now that we have the package checked out we need an isolated environment with proper configuration to develop the package. ``bob.devtools`` provides a tool that automatically creates such environment. 
Before proceeding, you need to make sure that you already have a conda_ environment with ``bob.devtools`` installed in it (Refer to :ref:`bob.devtools.install` for more information). let's assume that you have a conda environment named ``bdt`` with installed ``bob.devtools``.

.. code-block:: sh

   $ cd bob.blitz
   $ conda activate bdt
   $ bdt create -vv dev
   $ conda deactivate
   $ conda activate dev


Now you have an isolated conda environment named `dev` with proper channels set. For more information about conda channels refer to `conda channel documentation`_.

The `bdt create` command assumes a directory named `conda`, exists on the current directory. The `conda` directory contains a file named `meta.yaml`, that is the recipe required to create a development environment for the package you want to develop.

.. note::

    When developing and testing new features, one often wishes to work against the very latest, *bleeding edge*, available set of changes on dependent packages.

    `bdt create` command adds `Bob beta channels`_ to highest priority which creates an environment with the latest dependencies instead of the latest *stable* versions of each package.

    If you want to create your environment using *stable* channels, you can use this command instead:

      .. code-block:: sh

        $ bdt create --stable -vv dev

    To see which channels you are using run:

    .. code-block:: sh

        $ conda config --get channels



.. note::

    We recommend creating a new conda_ environment for every project or task
    that you work on. This way you can have several isolated development
    environments which can be very different form each other.


Running buildout
----------------

The last step is to create a hooked-up environment so you can quickly test
local changes to your package w/o necessarily creating a conda-package. 
zc.buildout_ takes care of it by modifying the load paths of scripts to find the correct
version of your package sources from the local checkout. It by default uses a file named `buildout.cfg`, in the package directory. For our example package it looks like:

.. code-block:: ini

  ; vim: set fileencoding=utf-8 :
  ; Mon 08 Aug 2016 14:33:54 CEST

  [buildout]
  parts = scripts
  develop = .
  eggs = bob.blitz
  extensions = bob.buildout
  newest = false
  verbose = true

  [scripts]
  recipe = bob.buildout:scripts

To find our more information about different section of this file, refer to :ref:`bob.devtools.buildout`.

Now you just need to run buildout:

.. code-block:: sh

   $ cd bob.blitz #if that is not the case
   $ conda activate dev #if that is not the case
   $ buildout



After running, buildout creates a directory called ``bin`` on your local package checkout. Use
the applications living there to develop your package. For example, if you need
to run the test suite:


.. code-block:: sh

   $ ./bin/nosetests -sv

or build the documentation:

.. code-block:: sh

    $./bin/sphinx-build -aEn doc sphinx  # make sure it finishes without warnings.
    $ firefox sphinx/index.html  # view the docs.

.. note::

    `buildout` by default uses the file `buildout.cfg` but you can specify another file by using -c option. In fact for developing packages especially if they need to be developed along with other packages, another file, namely `develop.cfg` is used like following: 

    .. code-block:: sh

       $ buildout -c develop.cfg


A python interpreter clone can be used to run interactive sessions:

.. code-block:: sh

   $ ./bin/python

You can see what is installed in your environment:

.. code-block:: sh

   $ conda list

And you can install new packages using conda:

.. code-block:: sh

   $ conda install <package>

.. note::

    If you want to debug a package regarding an issues showing on the ci you can use `bob.devtools`. Make sure the conda environment containing `bob.devtools` is activated.

    .. code-block:: sh

       $ cd <package>
       $ conda activate bdt
       $ bdt local build   


One important advantage of using conda_ and zc.buildout_ is that it does
**not** require administrator privileges for setting up any of the above.
Furthermore, you will be able to create distributable environments for each
project you have. This is a great way to release code for laboratory exercises
or for a particular publication that depends on |project|.

Developing multiple existing packages simultaneously
----------------------------------------------------
It so happens that you want to develop several packages against each other for your project. Let's assume you want to develop ``bob.blitz`` and ``bob.extension`` simultaneously. ``bob.blitz`` is dependent on ``bob.devtools``. First we checkout package ``bob.blitz`` and build an isolated conda environment as explained in the previous section. Then edit `buildout.cfg` file (or `develop.cfg`) and add ``bob.extension`` to it as following:


.. code-block:: ini

    [buildout]
    parts = scripts

    develop = src/bob.<package-B>
              .

    eggs = bob.<package-B>

    extensions = bob.buildout
                 mr.developer

    auto-checkout = *

    debug = true
    newest = false
    verbose = true

    [scripts]
    recipe = bob.buildout:scripts
    dependent-scripts = true

    [sources]
    bob.<package-B> = git https://gitlab.idiap.ch/bob/bob.<package-B>.git
    ; or
    ; bob.<package-B> = git git@gitlab.idiap.ch:bob/bob.<package-B>.git

Now you can run `buildout` as usual. The `bob.<package-B>` will be checked out on `src` folder on the root of your project.

.. note::
  
  The flag `debug = true` is usually used when in development mode. 


.. _bob.devtools.create_package:

Local development of a new Bob package
======================================

In this section we explain how to create a new bob package from scratch and start developing it. Once again `bob.devtools` is here to help you. You need to activate your conda environment with bob.devtools installed in it.

.. code-block:: sh
    
    $ conda activate bdt
    $ bdt new -vv bob/bob.project.awesome author_name author_email

This command will create a new bob package named "awesome-project" that includes the correct anatomy of a package. Here we briefly explain the purpose of some of the parts:


.. code-block:: text

    bob.<awesome-project>
    +-- bob
      +-- __init__.py #namespace init for "bob"
    +-- conda
      +-- meta.yaml
    +-- doc
      +-- img
      +-- conf.py
      +-- index.rst
      +-- links.rst
    +-- .gitignore
    +-- .gitlab-ci.yml
    +-- buildout.cfg
    +-- COPYING
    +-- MANIFEST.IN
    +-- README.rst
    +-- requirements.txt
    +-- setup.py
    +-- version.txt

For more information about the functionality of each file check :ref:`bob.devtools.anatomy`.  

In the root of your project there is a file `buildout.cfg` used by `buildout` to build your package locally. It should look like:

.. code-block:: ini

    [buildout]
    parts = scripts
    develop = .
    eggs = bob.project.awesome
    extensions = bob.buildout
    newest = false
    verbose = true

    [scripts]
    recipe = bob.buildout:scripts
    dependent-scripts = true


Now you have all the necessary tools available and you can make a development environment using `bdt create` command, run `buildout` in it and start developing your package.

.. code-block:: sh
    
    $ cd bob.project.awesome
    $ conda activate bdt
    $ bdt create --stable -vv awesome-project
    $ conda activate awesome-project
    $ buildout


Developing existing bob packages along with your new package
------------------------------------------------------------

Let's assume you need to develop two packages, `bob.extension` and `bob.blitz`, as part of developing your new `bob.project.awesome` package. 

You need to add these packages to the `buildout.cfg` file in the newly created folder.

.. code-block:: ini

    [buildout]
    parts = scripts

    develop = src/bob.extension
              src/bob.blitz
              .

    eggs = bob.extension
           bob.blitz
           bob.project.awesome

    extensions = bob.buildout
                 mr.developer

    auto-checkout = *
    newest = false
    verbose = true

    [scripts]
    recipe = bob.buildout:scripts
    dependent-scripts = true

    [sources]
    bob.extension = git https://gitlab.idiap.ch/bob/bob.extension
    bob.blitz = git https://gitlab.idiap.ch/bob/bob.blitz
    ; or
    ; bob.extension = git git@gitlab.idiap.ch:bob/bob.extension.git
    ; bob.blitz = git git@gitlab.idiap.ch:bob/bob.blitz.git


When you build your new package the dependent packages (in this example `bob.extension` and `bob.blitz`) will be checked out on folder `src` in the root of your project.

As usual, first create an isolated conda environment using `bdt create` command. Some of bob packages need dependencies that might not be installed on your environment. You can find these dependencies by checking `conda/meta.yaml` of each package. Install the required packages and then run buildout as usual.

.. code-block:: sh
    
    $ buildout

.. note::

    Sometimes you may need some of bob packages available in your local `bin` directory without necessarily developing them. 

    If you knew beforehand what are those packages, you can add them to "requirements/host" section of the `conda/meta.yaml` file and then create a conda environment using `bdt create`. Like this those packages will be installed automatically. Otherwise, if you already have your conda environment, install them using `conda install` command.
    
    When done, add those packages to the `eggs` section in your `buildout.cfg` file and then run `buildout`.


.. _bob.devtools.buildout:

Some notes on buildout
======================

To be able to develop a package, we first need to build and install it locally.
While developing a package, you need to install your package in *development*
mode so that you do not have to re-install your package after every change that
you do in the source. zc.buildout_ allows you to exactly do that.

.. note::
    zc.buildout_ will create another local environment from your conda_
    environment but unlike conda_ environments this environment is not isolated
    rather it inherits from your conda_ environment. This means you can still
    use the libraries that are installed in your conda_ environment.
    zc.buildout_ also allows you to install PyPI_ packages into your
    environment. You can use it to install some Python library if it is not
    available using conda_. Keep in mind that to install a library you should
    always prefer conda_ but to install your package from source in
    *development* mode, you should use zc.buildout_.

zc.buildout_ provides a ``buildout`` command. ``buildout`` takes as input a
"recipe" that explains how to build a local working environment. The recipe, by
default, is stored in a file called ``buildout.cfg``. 
.. note::

    Buildout by default looks for ``buildout.cfg`` in your current folder and
    uses that configuration file. You can specify a different config file with
    the ``-c`` option:

    .. code:: sh

        $ buildout -c develop.cfg


.. important::
    Once ``buildout`` runs, it creates several executable scripts in a local
    ``bin`` folder. Each executable is programmed to use Python from the conda
    environment, but also to consider (prioritarily) your package checkout.
    This means that you need to use the scripts from the ``bin`` folder instead
    of using its equivalence from your conda environment. For example, use
    ``./bin/python`` instead of ``python``.

``buildout`` will examine the ``setup.py`` file of packages using setuptools_
and will ensure all build and run-time dependencies of packages are available
either through the conda installation or it will install them locally without
changing your conda environment.

The configuration file is organized in several *sections*, which are indicated
by ``[]``, where the default section ``[buildout]`` is always required. Some of
the entries need attention.

* The first entry are the ``eggs``. In there, you can list all python packages
  that should be installed. These packages will then be available to be used in
  your environment. Dependencies for those packages will be automatically
  managed, **as long as you keep** ``bob.buildout`` **in your list of**
  ``extensions``. At least, the current package needs to be in the ``eggs``
  list.

* The ``extensions`` list includes all extensions that are required in the
  buildout process. By default, only ``bob.buildout`` is required, but more
  extensions can be added (more on that later).

* The next entry is the ``develop`` list. These packages will be installed
  *development mode* from the specified folder.

The remaining options define how the (dependent) packages are built. For
example, the ``debug`` flag defined, how the *C++ code* in
all the (dependent) packages is built. For more information refer to *C/C++ modules in your package* in `bob.extension <https://www.idiap.ch/software/bob/docs/bob/bob.extension/master/index.html>`_ documentation. The ``verbose`` options handles the
verbosity of the build. When the ``newest`` flag is set to ``true``, buildout
will install all packages in the latest versions, even if an older version is
already available.

.. note::

    We normally set ``newest = False`` to avoid downloading already installed
    dependencies. Also, it installs by default the latest stable version of the
    package, unless ``prefer-final = False``, in which case the latest
    available on PyPI, including betas, will be installed.


.. warning::

    Compiling packages in debug mode (``debug = true``) will make them very
    slow. You should only use this option when you are developing and not for
    running experiments or production.

When the buildout command is invoked it will perform the following steps:

1. It goes through the list of ``eggs``, searched for according packages and
   installed them *locally*.
2. It  populates the ``./bin`` directory with all the ``console_scripts`` that
   you have specified in the ``setup.py``.

.. important::

    One thing to note in package development is that when you change the entry
    points in ``setup.py`` of a package, you need to run ``buildout`` again.


.. _bob.devtools.mr.developer:

Using mr.developer
==================

One extension that may be useful is `mr.developer`_. It allows to develop
*several packages* at the same time. This extension will allow
buildout to automatically check out packages from git repositories, and places
them into the ``./src`` directory. It can be simply set up by adding
``mr.developer`` to the extensions section.

In this case, the develop section should be augmented with the packages you
would like to develop. There, you can list directories that contain Python
packages, which will be build in exactly the order that you specified. With
this option, you can tell buildout particularly, in which directories it should
look for some packages.

.. code-block:: ini

    [buildout]
    parts = scripts

    extensions = bob.buildout
                 mr.developer

    newest = false
    verbose = true
    debug = false

    auto-checkout = *

    develop = src/bob.extension
              src/bob.blitz

    eggs = bob.extension
           bob.blitz

    [scripts]
    recipe = bob.buildout:scripts
    dependent-scripts = true

    [sources]
    bob.extension = git https://gitlab.idiap.ch/bob/bob.extension
    bob.blitz = git https://gitlab.idiap.ch/bob/bob.blitz

A new section called ``[sources]`` appears, where the package information for
`mr.developer`_ is initialized. For more details, please read `its
documentation <https://pypi.python.org/pypi/mr.developer>`_. mr.developer does
not automatically place the packages into the ``develop`` list (and neither in
the ``eggs``), so you have to do that yourself.

With this augmented ``buildout.cfg``, the ``buildout`` command will perform the
following steps:



1.  It checks out the packages that you specified using ``mr.developer``.

2.  It develops all packages in the ``develop`` section
    (it links the source of the packages to your local environment).

3.  It will go through the list of ``eggs`` and search for according packages
    in the following order:

    #. In one of the already developed directories.
    #. In the python environment, e.g., packages installed with ``pip``.
    #. Online, i.e. on PyPI_.

4.  It will populate the ``./bin`` directory with all the ``console_scripts``
    that you have specified in the ``setup.py``. In our example, this is
    ``./bin/bob_new_version.py``.

The order of packages that you list in ``eggs`` and ``develop`` are important
and dependencies should be listed first. Especially, when you want to use a
private package and which not available through `pypi`_. If you do not specify
them in order, you might face with some errors like this::

   Could not find index page for 'a.bob.package' (maybe misspelled?)

If you see such errors, you may need to add the missing package to ``eggs`` and
``develop`` and ``sources`` (**of course, respecting the order of
dependencies**).


Your local environment
======================

After buildout has finished, you should now be able to execute
``./bin/python``. When using the newly generated ``./bin/python`` script, you
can access all packages that you have developed, including your own package:

.. code-block:: sh

    $ ./bin/python

.. code-block:: python

    >>> import bob.blitz
    >>> bob.blitz # should print from '.../awesome-project/src/bob.blitz/...'
    <module 'bob.blitz' from 'awesome-project/src/bob.blitz/bob/blitz/__init__.py'>
    >>> print(bob.blitz.get_config())
    bob.blitz: 2.0.15b0 [api=0x0202] (awesome-project/src/bob.blitz)
    * C/C++ dependencies:
      - Blitz++: 0.10
      - Boost: 1.61.0
      - Compiler: {'version': '4.8.5', 'name': 'gcc'}
      - NumPy: {'abi': '0x01000009', 'api': '0x0000000A'}
      - Python: 2.7.13
    * Python dependencies:
      - bob.extension: 2.4.6b0 (awesome-project/src/bob.extension)
      - numpy: 1.12.1 (miniconda/envs/bob3py27/lib/python2.7/site-packages)
      - setuptools: 36.4.0 (miniconda/envs/bob3py27/lib/python2.7/site-packages)


Everything is now setup for you to continue the development of the packages.
Moreover, you can learn more about |project| packages and learn to create new
ones in .

.. include:: links.rst
