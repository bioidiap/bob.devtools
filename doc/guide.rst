.. bob.buildout.guide:

=========================================
 Local development of |project| packages
=========================================

Very often, developers of |project| packages are confronted with the need to
clone repositories locally and develop installation/build and runtime code.
While it is possible to use conda_ for such, the use of `zc.buildout`_ offers
an quick and easy alternative to achieve this. It allows the creation of
isolated, directory-based python development environments that can be modulated
based on the development needs of the current package(s) one needs to work on.

The steps involved in creating a development environment are the following:

1. Checkout from gitlab_ the package the user wants to develop
2. Create a conda installation containing base packages that the current
   package being developed requires
3. *Optionally*, create a buildout configuration that allows the
   cross-development of packages
4. Run the application ``buildout`` to set-up the desired development
   environment

This guide is a step-by-step guide in performing these.


Checking out |project| package sources
--------------------------------------

|project| packages are developed through Gitlab_. In order to checkout a
package, just use git_:


.. code-block:: sh

   $ git clone https://gitlab.idiap.ch/bob/<package>


Where ``<package>`` is the package you want to develop. Various packages exist
in |project|'s gitlab_ instance.


Create a base conda-installation
--------------------------------

The base conda installation should contemplate all packages that you want to
develop against. This is typically listed in the package's
``requirements.txt``, but may also include test dependencies listed in
``test-requirements.txt`` depending on the package. The file
``conda/meta.yaml`` should be considered the canonical source for information
concerning package installation and deployment. After following `Bob's
installation`_ instructions, install all packages listed on the ``meta.yaml``
file using a single conda installation command.

For example, if the package one needs to develop lists build dependencies
``A``, ``B`` and ``C`` and test dependencies ``T`` and ``U``, the following
command-line should suffice once you followed `Bob's installation`_
instructions:


.. code-block:: sh

   $ cd <package>
   $ cat conda/meta.yaml #inspect contents and decide what to install
   ...
   $ conda create -n dev A B C T U bob.buildout
   ...
   $ conda activate dev #ready to develop your package


**Optional** Use of not-yet-released conda packages
===================================================

When developing and testing new features, one often wishes to work against the
very latest, *bleeding edge*, available set of changes on dependent packages.
If that is the case, consider adding our `conda beta channel`_ alongside conda
channels available for download in your condarc_ file.

The location of ``.condarc`` is configurable, but it is often set in
``${HOME}/.condarc``. Read about condarc_ online if you are in doubt.

After our `conda beta channel`_ is included on your configuration, proceed as
above to create an environment with the latest dependencies instead of the
latest *stable* versions of each package.


**Optional** Automated environment creation
===========================================

It is possible to automate the above procedure using a script that tries to
automatically parse build and test requirements in ``conda/meta.yaml`` and
create the required development environment from scratch. This script lives in
the package ``bob.admin``. The first step is to checkout ``bob.admin``
alongside the package you're developing:


.. code-block:: sh

   $ cd ..
   $ ls
   <PACKAGE>
   $ git clone https://gitlab.idiap.ch/bob/bob.admin
   $ ls
   <PACKAGE>
   bob.admin
   $ cd <PACKAGE>


.. note::

   If you already have checked out ``bob.admin``, make sure to update it with
   ``git pull``. We're constantly making improvements to this package.


Once ``bob.admin`` is available alongside your package, make sure both
``conda`` and ``conda-build`` are installed **and updated** on the base
environment of your conda_ installation. The automated script requires conda_
version 4.4 or above and ``conda-build`` version 3 or above. It also requires
the package ``pyyaml`` to be installed on the base of your conda installation.
Follow this recipe to get all up-to-date and ready:


.. code-block:: sh

   $ conda update -n base conda conda-build
   ...
   $ conda install -n base pyyaml
   ...


.. note::

   Notice the application ``conda`` is in my ``${PATH}`` and therefore the
   shell can find it easily. **Make sure you do the same**.


Now that you're all set, just call the script
``bob.admin/conda/conda-bootstrapy`` and pass the name of the resulting
environment you'd like to create:


.. code-block:: sh

   $ cd <PACKAGE>
   $ conda activate base
   $ ../bob.admin/conda/conda-bootstrap.py dev
   ...


This will parse the conda recipe from your package and create a new conda
environment on your conda installation called ``dev``. The environment ``dev``
contains all build *and* test dependencies required for your package. Activate
this environment and you're ready.

.. note::

   By default, our script **will include** our `conda beta channel`_ while
   creating your environment. You may modify the file
   ``bob.admin/conda/build-condarc`` if you'd like to include or remove
   channels.

   In this setup, we bypass your own condarc_ setup and use a stock version
   provided with ``bob.admin``.


Running buildout
----------------

The last step is to create a hooked-up environment so you can quickly test
local changes to your package w/o necessarily creating a conda-package. This
step is the easiest:


.. code-block:: sh

   $ cd <PACKAGE> #if that is not the case
   $ conda activate dev
   $ buildout
   ...

zc.buildout_ works by modifying the load paths of scripts to find the correct
version of your package sources from the local checkout. After running,
buildout creates a directory called ``bin`` on your local package checkout. Use
the applications living there to develop your package. For example, if you need
to run the test suite:


.. code-block:: sh

   $ ./bin/nosetests -sv


A python interpreter clone can be used to run interactive sessions:


.. code-block:: sh

   $ ./bin/python


**Optional** Cross-development of dependencies
----------------------------------------------

From time to time, you may wish to cross-develop multiple projects at once. For
example, you may wish to develop ``bob.bio.face``, while *also* making
modifications to ``bob.bio.base``. In this case, you'll need to create a
buildout recipe (i.e., a new ``.cfg``) file that instructs buildout to also
checkout the sources for ``bob.bio.base`` while setting up the local structure
for ``bob.bio.face``. Follow our development guide from ``bob.extension`` at
:ref:`bob.extension` for more instructions on this step. Once your new ``.cfg``
is ready, use it like this setup:


.. code-block:: sh

   $ buildout -c newrecipe.cfg


.. include:: links.rst
