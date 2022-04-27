.. _bob.devtools.development:

===============================
 Local development of packages
===============================

Very often, developers are confronted with the need to clone package
repositories locally and develop installation/build and runtime code. It is
recommended to create isolated environments using conda_ to develop new
projects. Tools implemented in ``bob.devtools`` help automate this process for
|project| packages. In the following we talk about how to checkout and build
one or several packages from their git_ source and build proper isolated
environments to develop them. Then we will describe how to create a new bob
package from scratch and develop existing bob packages along side it.

TL;DR
=====

Suppose you want to checkout the package ``bob.io.base`` from source and start
developing it locally. We will use the tools implemented in ``bob.devtools`` to
create a proper developing environment to build and develop ``bob.io.base``. We
assume you have ``bob.devtools`` installed on a conda environment named ``bdt``
(Refer to :ref:`bob.devtools.install` for detailed information.)

* Checkout the source of the package from git:

.. code-block:: sh

   $ bdt dev checkout --use-ssh bob.io.base

* Create a proper conda environment:

.. code-block:: sh

   $ cd bob.io.base
   $ bdt dev create -vv dev
   $ conda activate dev

* Build the package using pip:

.. code-block:: sh

   $ bdt dev install . # calls pip with correct arguments
   $ python

for example:

.. code-block:: python

    >>> import bob.io.base
    >>> bob.io.base # should print from '.../bob.io.base/bob/blitz/...'
    <module 'bob.io.base' from '.../bob.io.base/bob/blitz/__init__.py'>
    >>> print(bob.io.base.get_config())
    bob.io.base: 2.0.20b0 [api=0x0202] (.../bob.io.base)
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

   $ pytest -sv ...

* Some packages may come with a pre-commit_ config file (``.pre-commit-config.yaml``).
  Make sure to install pre-commit if the config file exists:

.. code-block:: sh

   $ # check if the configuration file exists:
   $ ls .pre-commit-config.yaml
   $ pip install pre-commit
   $ pre-commit install


.. bob.devtools.local_development:

Local development of existing packages
======================================

To develop existing |project| packages you need to checkout their source code
and install them in your environment.


Checking out package sources
----------------------------

|project| packages are developed through gitlab_. Various packages exist in
|project|'s gitlab_ instance. In the following we assume you want to install
and build locally the ``bob.io.base`` package. In order to checkout a package,
just use git_:


.. code-block:: sh

   $ bdt dev checkout --use-ssh bob.io.base


Create an isolated conda environment
------------------------------------

Now that we have the package checked out we need an isolated environment with
proper configuration to develop the package. ``bob.devtools`` provides a tool
that automatically creates such environment. Before proceeding, you need to
make sure that you already have a conda_ environment with ``bob.devtools``
installed in it (Refer to :ref:`bob.devtools.install` for more information).
let's assume that you have a conda environment named ``bdt`` with installed
``bob.devtools``.

.. code-block:: sh

   $ cd bob.io.base
   $ bdt dev create -vv dev
   $ conda activate dev


Now you have an isolated conda environment named `dev` with proper channels
set. For more information about conda channels refer to `conda channel
documentation`_.

The ``bdt dev create`` command assumes a directory named ``conda``, exists on
the current directory. The ``conda`` directory contains a file named
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
    environments which can be very different form each other.


Installing the package
----------------------

The last step is to install the package:

.. code-block:: sh

   $ cd bob.io.base #if that is not the case
   $ conda activate dev #if that is not the case
   $ bdt dev install .

To run the test suite:

.. code-block:: sh

   $ pytest -sv ...

or build the documentation:

.. code-block:: sh

    $ sphinx-build -aEn doc sphinx  # make sure it finishes without warnings.
    $ xdg-open sphinx/index.html  # view the docs.


You can see what is installed in your environment:

.. code-block:: sh

   $ conda list

And you can install new packages using conda:

.. code-block:: sh

   $ conda install <package>

.. note::

    If you want to debug a package regarding an issues showing on the ci you
    can use ``bob.devtools``. Make sure the conda environment containing
    ``bob.devtools`` is activated (typically, ``base``).

    .. code-block:: sh

       $ cd <package>
       $ bdt local build


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

    $ bdt dev checkout --use-ssh --subfolder src bob.extension
    $ bdt dev install src/bob.extension


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
environment using `bdt dev create` command, run `bdt dev install` in it and
start developing your package.

.. code-block:: sh

    $ cd bob.project.awesome
    $ bdt dev create --stable -vv awesome-project  #here we used the stable channels to make the conda environment.
    $ conda activate awesome-project
    $ bdt dev install .


Developing existing bob packages along with your new package
------------------------------------------------------------

Let's assume you need to develop two packages, ``bob.extension`` and
``bob.io.base``, as part of developing your new ``bob.project.awesome`` package.

You need to checkout and install these packages:

.. code-block:: sh

    $ bdt dev checkout --use-ssh --subfolder src bob.extension bob.io.base
    $ bdt dev install src/bob.extension src/bob.io.base  # the order of installing dependencies matters!

When you build your new package, it is customary to checkout the dependent
packages (in this example ``bob.extension`` and ``bob.io.base``) in the ``src``
folder in the root of your project.

As usual, first create an isolated conda environment using ``bdt dev create``
command. Some of bob packages need dependencies that might not be installed on
your environment. You can find these dependencies by checking
``conda/meta.yaml`` of each package. Install the required packages and then run
``bdt dev install``. For our example you need to do the following:

.. code-block:: sh

    $ conda install gcc_linux-64 gxx_linux-64 libblitz
    $ bdt dev install src/bob.extension src/bob.io.base  # the order of installing dependencies matters!

.. include:: links.rst
