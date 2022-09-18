.. _bob.devtools.development:

===============================
 Local development of packages
===============================

Very often, developers are confronted with the need to clone package
repositories locally and develop installation/build and runtime code. It is
recommended to create isolated environments using mamba_ (or conda_) to develop
new projects. Tools implemented in ``bob.devtools`` help automate this process
for |project| packages. In the following we talk about how to checkout and
build one or several packages from their git_ source and build proper isolated
environments to develop them. Then we will describe how to create a new bob
package from scratch and develop existing bob packages along side it.

TL;DR
=====

The setup process to develop a Bob_ package goes through 3 steps:

1. Checkout the source of the package from git:

   .. code-block:: sh

      $ git clone git@gitlab.idiap.ch:bob/bob.io.base

2. Create a proper conda (development) environment:

   .. code-block:: sh

      $ cd bob.io.base
      $ conda activate base
      (base) $ bdt dev create -vv dev
      # installs all packages required to develop bob.bio.base
      # pip-installs all extra packages defined at your ~/.bdtrc
      $ conda activate dev
      (dev) $

3. Install the package in development mode using pip:

  .. code-block:: sh

     (dev) $ pip install --no-build-isolation --no-dependencies --editable .

After that step, your package will be installed and ready for use inside the
``dev`` environment.  You must activate it everytime you want to further
develop the package, or simply deactivate it when you branch off to another
activity.

With the development environment active, you can optionally test the package
installation by either building its Sphinx documentation, doctests, running its
test suite, or the quality assurance (pre-commit) checks:

.. code-block:: sh

   (dev) $ sphinx-build doc sphinx  # documentation
   (dev) $ sphinx-build doctest doc sphinx  # doctests
   (dev) $ pytest -sv --cov bob.bio.base --cov-report  # test units
   (dev) $ pre-commit run --all-files  # quality assurance

Note quality assurance may only work if a file called
``.pre-commit-config.yaml`` is available within the package.


Installing dependencies for all Bob packages
============================================

If you know that you plan to develop many packages (or even every Bob package),
you can also instead create an environment that contains al external
dependencies. This avoids the need to run ``bdt dev create`` for many packages.
You will need to pick a Python version:

.. code-block:: sh

   $ bdt dev dependencies --python=3.9 dev
   $ conda activate dev
   (dev) $

.. note::

   ``bdt`` might try to install the cuda version of deep learning packages. If
   you don't have cuda drivers installed and face errors such as ``nothing
   provides __cuda``, you might need to run: ``export
   CONDA_OVERRIDE_CUDA=11.6`` where instead of ``11.6`` you should put the
   latest version of cuda. You can also use this trick if you actually want to
   ensure ``bdt`` will install the cuda version of deep learning packages.


.. bob.devtools.local_development:

Local development of existing packages
======================================

To develop existing |project| packages you need to checkout their source code
and install them in a suitable development environment, composed of the
required packages.  The latest (unreleased) version of software dependencies
from the Bob_ ecosystem are installed to simplify integration for the next
unified release.


Checking out package sources
----------------------------

|project| packages are developed through gitlab_. Various packages exist in
|project|'s gitlab_ instance. In the following we assume you want to install
and build locally the ``bob.io.base`` package. In order to checkout a package,
just use git_:

.. code-block:: sh

   $ git clone git@gitlab.idiap.ch:bob/bob.io.base


Create an isolated conda environment
------------------------------------

Now that we have the package checked out we need an isolated environment with
proper configuration (beta channel address for Bob dependencies correctly
setup) to develop the package. ``bob.devtools`` provides a tool that
automatically creates such environment. Before proceeding, you need to make
sure that you already have a mamba_ (or conda_) environment with
``bob.devtools`` installed in it (refer to :ref:`bob.devtools.install` for more
information). We assume you followed our installation instructions and
installed ``bob.devtools`` on the ``base`` environment.  Then, follow these
steps to create a development environment for ``bob.io.base``:

.. code-block:: sh

   $ cd bob.io.base
   $ conda activate base
   (base) $ bdt dev create -vv dev
   (base) $ conda activate dev
   (dev) $

Now you have an isolated conda environment named `dev` with the proper
configuration automatically set up. For more information about conda channels
refer to `conda channel documentation`_.

Notice, the ``bdt dev create`` command assumes a directory named ``conda``,
exists on the current directory.  The ``conda`` directory contains a file named
``meta.yaml``, that is the recipe required to create a development environment
for the package you want to develop.

.. note::

   When developing and testing new features, one often wishes to work against
   the very latest, *bleeding edge*, available set of changes on dependent
   packages.

   ``bdt dev create`` command adds `Bob beta channels`_ to highest priority
   which creates an environment with the latest dependencies instead of the
   latest *stable* versions of each package.

   If you want to create your environment using *stable* channels, you can use
   this command instead:

     .. code-block:: sh

       $ bdt dev create --stable -vv dev

   To see which channels you are using run:

   .. code-block:: sh

       $ conda config --get channels


.. note::

   We recommend creating a new conda_ environment for every project or task
   that you work on. This way you can have several isolated development
   environments which can be very different from each other.


Installing the package
----------------------

The last step is to install the package.  We simply do this using pip_:

.. code-block:: sh

   (dev) $ pip install --no-build-isolation --no-dependencies --editable .

To run the test suite:

.. code-block:: sh

   $ pytest -sv ...

or build the documentation:

.. code-block:: sh

    $ sphinx-build -aEn doc sphinx  # make sure it finishes without warnings.

You can see what is installed in your environment:

.. code-block:: sh

   $ mamba list

And you can install new packages using mamba:

.. code-block:: sh

   $ mamba install <package>

.. note::

    If you want to debug a package regarding an issues showing on the ci you
    can use ``bob.devtools``. Make sure the conda environment containing
    ``bob.devtools`` is activated (typically, ``base``).

    .. code-block:: sh

       (base) $ cd <package>
       (base) $ bdt local build


One important advantage of using conda_ is that it does **not** require
administrator privileges for setting up any of the above. Furthermore, you will
be able to create distributable environments for each project you have. This is
a great way to release code for laboratory exercises or for a particular
publication that depends on |project|.


Developing multiple existing packages simultaneously
----------------------------------------------------

It so happens that you want to develop several packages against each other for
your project. Let's assume you want to develop ``bob.io.base`` and
``bob.extension`` simultaneously. ``bob.io.base`` is dependent on
``bob.extension``. First we checkout package ``bob.io.base`` and build an
isolated conda environment as explained in the previous section. Then checkout
and install ``bob.extension`` as following:


.. code-block:: sh

   $ cd bob.io.base
   # we place dependencies in the "src/" subdirectory
   $ git clone git@gitlab.idiap.ch:bob/bob.extension src/bob.extension
   $ conda activate dev
   (dev) $ pip install --no-build-isolation --no-dependencies --editable src/bob.extension

If you want to develop many packages, or even all Bob packages at once, you can
proceed a bit differently. First, create an environment containing all external
Bob dependencies.

.. code-block:: sh

    $ conda activate base
    (base) $ bdt dev dependencies --python=3.9 alldeps
    (base) $ conda activate alldeps
    (alldeps) $ mkdir -pv bob_beta/src
    (alldeps) $ cd bob_beta/src
    # checkout and install everything you need, in order:
    (alldeps) $ for p in bob.extension bob.io.base bob.pipelines; do
    ... git clone git@gitlab.idiap.ch:bob/$p;
    ... pip install --no-build-isolation --no-dependencies --editable $p;
    ... done


.. _bob.devtools.create_package:

Local development of a new package
==================================

In this section we explain how to create a new bob package from scratch and
start developing it. Once again ``bob.devtools`` is here to help you. You need
to activate your conda environment with ``bob.devtools`` installed in it.

.. code-block:: sh

    $ bdt dev new -vv bob/bob.project.awesome author_name author_email

This command will create a new bob package named "bob.project.awesome" that
includes the correct anatomy of a package. For more information about the
functionality of each file check :ref:`bob.devtools.anatomy`.

Now you have all the necessary tools available and you can make a development
environment using `bdt dev create` command, run `pip` in it and start
developing your package.

.. code-block:: sh

    $ cd bob.project.awesome
    $ conda activate base
    (base) $ bdt dev create -vv awesome-project
    (base) $ conda activate awesome-project
    (awesome-project) $ pip install --no-build-isolation --no-dependencies --editable .


.. include:: links.rst
