.. vim: set fileencoding=utf-8 :

.. _bob.devtools.templates:

===========================
 Additional Considerations
===========================

These instructions describes some steps that needs to be noted after creating new packages for either Bob_ or BEAT_ to incorporate the package properly in the ecosystem.

.. note::

   If you'd like to update part of your package setup, follow similar
   instructions and then **copy** the relevant files to your **existing**
   setup, overriding portions you know are correct.


.. warning::

   These instructions may change as we get more experience in what needs to be
   changed.  In case that happens, update your package by generating a new
   setup and copying the relevant parts to your existing package(s).


Unit tests
==========

Writing unit tests is an important asset on code that needs to run in different platforms and a great way to make sure all is OK.
Test units are run with nose_.
To run the test units on your package call:

.. code-block:: sh

  $ ./bin/nosetests -v
  bob.example.library.test.test_reverse ... ok

  ----------------------------------------------------------------------
  Ran 1 test in 0.253s

  OK

This example shows the results of the tests in the ``bob.example.project`` package. Ideally, you should
write test units for each function of your package ...

.. note::

   You should put additional packages needed for testing (e.g. ``nosetests``)
   in the ``test-requirements.txt`` file.


Continuous integration (CI)
===========================

.. note::

   This is valid for people at Idiap (or external bob contributors with access to Idiap's gitlab)

.. note::

   Before going into CI, you should make sure that your pacakge has a gitlab repository.
   If not, do the following in your package root folder:

   .. code-block:: sh

      $ git init
      $ git remote add origin git@gitlab.idiap.ch:bob/`basename $(pwd)`
      $ git add bob/ buildout.cfg COPYING doc/ MANIFEST.IN README.rst requirements.txt setup.py version.txt
      $ git commit -m '[Initial commit]'
      $ git push -u origin master


Copy the appropriate yml template for the CI builds:


.. code-block:: sh

  # for pure python
  $ curl -k --silent https://gitlab.idiap.ch/bob/bob.admin/raw/master/templates/ci-for-python-only.yml > .gitlab-ci.yml
  # for c/c++ extensions
  $ curl -k --silent https://gitlab.idiap.ch/bob/bob.admin/raw/master/templates/ci-for-cxx-extensions.yml | tr -d '\r' > .gitlab-ci.yml

Add the file to git:

.. code-block:: sh

  $ git add .gitlab-ci.yml


The ci file should work out of the box. It is long-ish, but generic to any
package in the system.

You also need to enable the following options - through gitlab - on your project:

1. In the project "Settings" page, make sure builds are enabled
2. If you have a private project, check the package settings and make sure that
   the "Deploy Keys" for our builders (all `conda-*` related servers) are
   enabled
3. Visit the "Runners" section of your package settings and enable all conda
   runners, for linux and macosx variants
4. Go into the "Variables" section of your package setup and **add common
   variables** corresponding to the usernames and passwords for uploading
   wheels and documentation tar balls to our (web DAV) server, as well as PyPI
   packages.  You can copy required values from [the "Variables" section of
   bob.admin](https://gitlab.idiap.ch/bob/bob.admin/variables). N.B.: You
   **must** be logged into gitlab to access that page.
5. Make sure to **disable** the service "Build e-mails" (those are very
   annoying)
6. Setup the coverage regular expression under "CI/CD pipelines" to have the
   value `^TOTAL.*\s+(\d+\%)$`, which is adequate for figuring out the output
   of `coverage report`


Python package namespace
========================

We like to make use of namespaces to define combined sets of functionality that go well together.
Python package namespaces are `explained in details here <http://peak.telecommunity.com/DevCenter/setuptools#namespace-package>`_ together with implementation details.
For bob packages, we usually use the ``bob`` namespace, using several sub-namespaces such as ``bob.io``, ``bob.ip``, ``bob.learn``, ``bob.db`` or (like here) ``bob.example``.


The scripts you created should also somehow contain the namespace of the package. In our example,
the script is named ``bob_example_project_version.py``, reflecting the  namespace ``bob.example``


Distributing your work
======================

To distribute a package, we recommend you use PyPI_.
`Python Packaging User Guide <https://packaging.python.org/>`_ contains details
and good examples on how to achieve this.
Moreover, you can provide a conda_ package for your PyPI_ package for easier
installation. In order to create a conda_ package, you need to create a conda_
recipe for that package.

.. note::

    For more detailed instructions on how to distribute your packages at Idiap, please see the 
    guidelines on `Publishing Reproducible Papers at Idiap <https://gitlab.idiap.ch/bob/bob/wikis/Publishing-Reproducible-Papers-at-Idiap>`_.


.. _bob.devtools.buildout:

buildout.cfg in more details
============================
This section briefly explains the different entries in ``buildout.cfg`` file. For better understanding of buildout refer to its
`documentation <http://www.buildout.org>`_ 


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
  extensions can be added.

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
------------------

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

.. _bob.devtools.anatomy:

Anatomy of a new package
========================
A typical package have the following structure:


.. code-block:: text

    .
    +-- bob               # python package (a.k.a. "the code")
    |   +-- project
    |   |   +-- awesome   # your code will go into this folder
    |   |   |   +-- __init__.py  # name space init for "awesome"
    |   |   +-- __init__.py   # name space init for "project"
    |   +-- __init__.py   # name space init for "bob"
    +-- conda
    |   +-- meta.yaml     # recipe for preparing the conda environment
    +-- doc               # documentation directory
    |   +-- img
    |   +-- conf.py       # sphinx configuration
    |   +-- index.rst     # documentation starting point for Sphinx
    |   +-- links.rst
    +-- .gitignore        # some settings for git
    +-- .gitlab-ci.yml    # instruction for ci integration
    +-- buildout.cfg      # buildout configuration
    +-- COPYING           # license information
    +-- MANIFEST.IN       # extras to be installed, besides the Python files
    +-- README.rst        # a minimal description of the package, in reStructuredText format
    +-- requirements.txt  # requirements of your package
    +-- setup.py          # installation instruction for this particular package
    +-- version.txt       # the (current) version of your package


A quick overview of these files:


bob: It is the directory that includes the source code and scripts for your package. The files should be organized in subdirectories that matches the name of your package.

conda: It is the directory includes the recipe (``meta.yaml``) for preparing the base conda environment used for package development.

doc: This is the directory including the minimum necessary information for building package documentation. The file `conf.py` is used by sphinx to build the documentation.

.gitignore: This file includes some settings for git.

.gitlab-ci.yml: It is the file including the information about building packages on the CI.

buildout.cfg: This file contains the basic recipe to create a working environment for developing the package.

COPYING: The file including the licensing information.

MANIFEST.IN: This file contains the list of non python files and packages that are needed to be installed for your package.

README.rst: It includes basic information about the package, in reStructuredText format.

requirements.txt: This file contains the direct dependencies of the package.

setup.py: This file contains the python packaging instructions. For detailed information refer to `setuptools`_.

version.txt: The file shows the current version of the package.

Continuous Integration and Deployment (CI)
==========================================

If you'd like just to update CI instructions, copy the file ``.gitlab-ci.yml``
from ``bob/devtools/templates/.gitlab-ci.yml`` **overriding** your existing
one:


.. code-block:: sh

   $ curl -k --silent https://gitlab.idiap.ch/bob/bob.devtools/raw/master/bob/devtools/templates/.gitlab-ci.yml > .gitlab-ci.yml
   $ git add .gitlab-ci.yml
   $ git commit -m '[ci] Updated CI instructions' .gitlab-ci.yml


The ci file should work out of the box, it is just a reference to a global
configuration file that is adequate for all packages inside the Bob_/BEAT_
ecosystem.

You also remember to enable the following options on your project:

1. In the project "Settings" page, make sure builds are enabled
2. Visit the "Runners" section of your package settings and enable all runners
   with the `docker` and `macosx` tags.
3. Setup the coverage regular expression under "CI/CD pipelines" to have the
   value `^TOTAL.*\s+(\d+\%)$`, which is adequate for figuring out the output
   of `coverage report`


New unexisting dependencies
===========================

If your package depends on **third-party packages** (not Bob_ or BEAT_ existing
resources) that are not in the CI, but exist on the conda ``defaults`` channel,
you should perform some extra steps:

1. Add the package in the ``meta.yml`` file of bob-devel in
   ``bob/bob.conda/conda/bob-devel``:


   .. code-block:: yaml

      requirements:
        host:
          - python {{ python }}
          - {{ compiler('c') }}
          - {{ compiler('cxx') }}
          # Dependency list of bob packages. Everything is pinned to allow for better
          # reproducibility. Please keep this list sorted. It is recommended that you
          # update all dependencies at once (to their latest version) each time you
          # modify the dependencies here. Use ``conda search`` to find the latest
          # version of packages.
          - boost 1.65.1
          - caffe 1.0  # [linux]
          - click 6.7
          - click-plugins 1.0.3
          - ..
          - [your dependency here]

2. At the same file, update the version with the current date, in the format
   preset.

   .. code-block:: yaml

      package:
        name: bob-devel
        version: 2018.05.02  <-- HERE

3. Update the ``beat-devel`` and ``bob-devel`` versions in the ``meta.yml``
   file inside ``bob/bob.conda/conda/beat-devel``:

   .. code-block:: yaml

      package:
        name: beat-devel
        version: 2018.05.02  <-- HERE

      [...]

      requirements:
        host:
          - python {{ python }}
          - bob-devel 2018.05.02  <-- HERE
          - requests 2.18.4

4. Update the ``conda_build_config.yaml`` in
   ``bob/bob.devtools/bob/devtools/data/conda_build_config.yaml`` with your
   dependencies, and with the updated version of bob-devel and beat-devel. See
   `this here <https://gitlab.idiap.ch/bob/bob.conda/merge_requests/363>`_ and
   `this MR here <https://gitlab.idiap.ch/bob/bob.admin/merge_requests/89>`_
   for concrete examples on how to do this.

   .. note::

      **This step should be performed after bob.conda's pipeline on master is
      finished** (i.e. perform steps 1 to 3 in a branch, open a merge request
      and wait for it to be merged, and wait for the new master branch to be
      "green").


Conda recipe
============

The CI system is based on conda recipes to build the package.  The recipes are
located in the ``conda/meta.yaml`` file of each package.  You can start
to modify the recipe of each package from the template generated by ``bdt
template`` command as explained above, for new packages.

The template ``meta.yaml`` file in this package is up-to-date. If you see a
Bob_ or BEAT_ package that does not look similar to this recipe, please let us
know as soon as possible.

You should refrain from modifying the recipe except for the places that you are
asked to modify. We want to keep recipes as similar as possible so that
updating all of them in future would be possible by a script.

Each recipe is unique to the package and need to be further modified by the
package maintainer to work. The reference definition of the ``meta.yaml`` file
is https://conda.io/docs/user-guide/tasks/build-packages/define-metadata.html.
The ``meta.yaml`` file (referred to as the recipe) will contain duplicate
information that is already documented in ``setup.py``, ``requirements.txt``,
and, eventually, in ``test-requirements.txt``. For the time being you have to
maintain both the ``meta.yaml`` file and the other files.

Let's walk through the ``conda/meta.yaml`` file (the recipe) that you just
created and further customize it to your package.  You need to carry out all
the steps below otherwise the template ``meta.yaml`` is not usable as it is.


Entry-points in the ``build`` section
-------------------------------------

You need to check if your package has any ``console_scripts``. These are
documented in ``setup.py`` of each package. You need to list the
``console_scripts`` entry points (only ``console_scripts``; other entry points
**should not** be listed in ``conda/meta.yaml``) in the build section of the
recipe.

* If there are no ``console_scripts``, then you don't need to add anything
* If there are some, list them in the ``conda/meta.yaml`` file as well:
  (`information on entry-points at conda recipes here
  <https://conda.io/docs/user-guide/tasks/build-packages/define-metadata.html#python-entry-points>`_).
  For example, if the ``setup.py`` file contains:

  .. code-block:: python

     entry_points={
       'console_scripts': [
         'jman = gridtk.script.jman:main',
         'jgen = gridtk.script.jgen:main',
       ]

  You would add the following entry-points on ``conda/meta.yaml``:

  .. code-block:: yaml

     build:  # add entry points at the "build" section
       entry_points:
         - jman = gridtk.script.jman:main
         - jgen = gridtk.script.jgen:main


.. note::

   If your conda package runs only on linux, please add this recipe under
   build:

   .. code-block:: yaml

      build:
         skip: true  # [not linux]


Build and host dependencies
---------------------------

This part of the recipe lists the packages that are required during build time
(`information on conda package requirements here
<https://conda.io/docs/user-guide/tasks/build-packages/define-metadata.html#requirements-section>`_).
Having build and host requirements separately enables cross-compiling of the
recipes.  Here are some notes:

* If the packages does not contain C/C++ code, you may skip adding build
  dependencies (pure-python packages do not typically have build dependencies
  (that is, dependencies required for installing the package itself, except for
  ``setuptools`` and ``python`` itself)
* If the package does contain C/C++ code, then you need to augment the entries
  in the section ``requirements / build`` to include:

  .. code-block:: yaml

     requirements:
       build:
         - {{ compiler('c') }}
         - {{ compiler('cxx') }}
         - pkg-config {{ pkg_config }}
         - cmake {{ cmake }}

  The pkg-config and cmake lines are optional. If the package uses them, you
  need to include these as well.

* List all the packages that are in ``requirements.txt`` in the
  ``requirements / host`` section, adding a new line per dependence.  For
  example, here is what ``bob/bob.measure`` has in its host:

  .. code-block:: yaml

     host:
       - python {{ python }}
       - setuptools {{ setuptools }}
       - bob.extension
       - bob.blitz
       - bob.core
       - bob.math
       - bob.io.base
       - matplotlib {{ matplotlib }}
       - libblitz {{ libblitz }}
       - boost {{ boost }}
       - numpy {{ numpy }}
       - docopt {{ docopt }}

  You need to add a jinja variable like `{{ dependence }}` in front of the
  dependencies that we **do not** develop.  The jinja variable name should not
  contain ``.`` or ``-``; replace those with ``_``.  Bob_ and BEAT_ packages
  (and gridtk) should be listed as is.

* Unlike ``pip``, ``conda`` is **not** limited to Python programs. If the
  package depends on some non-python package (like ``boost``), you need to list
  it in the `host` section.


Runtime dependencies
--------------------

In the ``requirements / run`` section of the conda recipe, you will list
dependencies that are needed when a package is used (run-time) dependencies.
Usually, for pure-python packages, you list the same packages as in the host
section also in the run section.  This is simple, **but** conda build version
3.x introduced a new concept named ``run_exports`` (`read more about this
feature here
<https://conda.io/docs/user-guide/tasks/build-packages/define-metadata.html#pin-downstream>`_)
which makes this slightly complicated.  In summary, you put all the run-time
dependencies in the ``requirements / run`` section **unless** this dependency
was listed in the host section **and** the dependency has a ``run_exports`` set
on their own recipe (what a mess!).  The problem is that you cannot easily find
which packages actually do have ``run_exports`` unless you look at their conda
recipe.  Usually, all the C/C++ libraries like ``jpeg``, ``hdf5`` have
``run_exports`` (with exceptions - ``boost``, for instance,  does not have
one!).  All ``bob`` packages have this too.  For example, here is what is
inside the ``requirements / run`` section of ``bob/bob.measure``:

.. code-block:: yaml

   run:
     - setuptools
     - matplotlib
     - boost
     - {{ pin_compatible('numpy') }}
     - docopt

The ``pin_compatible`` jinja function is `explained in here
<https://conda.io/docs/user-guide/tasks/build-packages/define-metadata.html#pin-downstream>`_.
You need to use it on ``numpy`` if and only if you use ``numpy`` in C level.
Otherwise, just list numpy normally. We do not know of any other package
besides numpy used in C level that needs to use the ``pin_compatible`` jinja
function.

Here is a list of packages that we know that they have ``run_exports``:

.. code-block:: yaml

   - bzip2
   - dbus
   - expat
   - ffmpeg
   - fontconfig
   - freetype
   - giflib
   - glib
   - gmp
   - gst-plugins-base
   - gstreamer
   - hdf5
   - icu
   - jpeg
   - kaldi
   - libblitz
   - libboost
   - libffi
   - libmatio
   - libogg
   - libopus
   - libpng
   - libsvm
   - libtiff
   - libvpx
   - libxcb
   - libxml2
   - menpo
   - mkl # not this one but mkl-devel - no need to list mkl if you use mkl-devel in host
   - mkl-devel
   - ncurses
   - openfst
   - openssl
   - readline
   - sox
   - speex
   - speexdsp
   - sqlite
   - tk
   - vlfeat
   - xz
   - yaml
   - zlib


Testing entry-points
--------------------

If you listed some of your ``setup.py`` ``console_sripts`` in the ``build / entry_points`` section of the conda recipe, it is adviseable you test these.  For
example, if you had the examples entry points above, you would test them like:

.. code-block:: yaml

   test:
     imports:
       - {{ name }}
     commands:
       - jman --help
       - jgen --help


Test-time dependencies
----------------------

You need to list the packages here that are required during **test-time only**.
By default, add some packages.  Do not remove them.  The test-time dependencies
are listed in ``test-requirements.txt``, which is an optional file, not
included in the template.   It has the same syntax as ``requirements.txt``, but
list only things that are needed to test the package and are not part of its
runtime.  If you do not need any test-time dependencies, you may skip these
instructions.

You may read more information about `conda test-time dependencies here <https://conda.io/docs/user-guide/tasks/build-packages/define-metadata.html#test-requirements>`_.


Left-over conda build files
---------------------------

The conda build command may create a temporary file named ``record.txt`` in the
project directory. Please make sure it is added in the ``.gitignore`` file so
that is not committed to the project repository by mistake.


Database packages and packages with extra data
==============================================

Sometimes databases or other packages require an extra download command after
installation. If this extra data is downloaded from Idiap severs, you can
include this data in the conda package itself to avoid downloading it two
times. If the data is supposed to be downloaded from somewhere other than Idiap
servers, do not include it in its conda package. For example, the database
packages typically require this download command to be added in the
``build:script`` section:


.. code-block:: yaml

   - python setup.py install --single-version-externally-managed --record record.txt # this line is already in the recipe. Do not add.
   - bob_dbmanage.py {{ name.replace('bob.db.', '') }} download --missing


Licensing
=========

There are 2 possible cases for the majority of packages in our ecosystem:

1. If the package is supposed to be licensed under (a 3-clause) BSD license,
   ensure a file called ``LICENSE`` exists at the root of your package and has
   the correct authorship information.
2. If the package is supposed to be licensed under GPLv3 license, then ensure a
   file called ``COPYING`` exists on the root of your package

The templating generation has an option to address this.

More info about Idiap's `open-source policy here
<https://secure.idiap.ch/intranet/services/technology-transfer/idiap-open-source-policy>`.


Headers
=======

Sometimes people add headers with licensing terms to their files. You should
inspect your library to make sure you don't have those. The Idiap TTO says this
strategy is OK and simplifies our lives. Make the headers of each file you have
as simple as possible, so they don't get outdated in case things change.

Here is a minimal example (adapt to the language comment style if needed):

```text
#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
```

It is OK to also have your author name on the file if you wish to do so.
**Don't repeat licensing terms** already explained on the root of your package
and on the `setup.py` file.  If we need to change the license, it is painful to
go through all the headers.


The ``setup.py`` file
=====================

The ``setup.py`` should be changed to include eventual ``entry_points`` you
also included in the ``conda/meta.yaml``.  We cannot guess these.


Buildout
========

The default buildout file ``buildout.cfg`` should buildout from the installed
distribution (use ``bdt create`` for that purpose) and **avoid mr.developer
checkouts**.  If you have one of those, move it to ``develop.cfg`` and create a
new `buildout.cfg` which should be as simple as possible.  The template project
provided by this package takes care of this.


The ``README.rst`` file
=======================

You should make the README smaller and easier to maintain.  As of today, many
packages contain outdated installation instructions or outdated links.  More
information can always be found at the documentation, which is automatically
linked from the badges.

You may want to revise the short introduction after automatic template
generation.  Make it short, a single phrase is the most common size.


Sphinx documentation
====================

Sphinx documentation configuration goes to a file named ``doc/conf.py``.  The
file ``doc/index.rst`` is the root of the documentation for your package.

The new documentation configuration allows for two *optional* configuration
text files to be placed inside the ``doc/`` directory, alongside the ``conf.py`` file:

* ``extra-intersphinx.txt``, which lists extra packages that should be
  cross-linked to the documentation (as with `Sphinx's intersphinx extension
  <http://www.sphinx-doc.org/en/stable/ext/intersphinx.html>`_. The format of
  this text file is simple: it contains the PyPI names of packages to
  cross-reference. One per line.
* ``nitpick-exceptions.txt``, which lists which documentation objects to ignore
  (for warnings and errors). The format of this text file is two-column. On the
  first column, you should refer to `Sphinx the object
  type <http://www.sphinx-doc.org/en/stable/domains.html#the-python-domain>`_,
  e.g. ``py:class``, followed by a space and then the name of the that should be
  ignored. E.g.: ``bob.bio.base.Database``.  The file may optionally contain
  empty lines. Lines starting with ``#`` are ignored (so you can comment on why
  you're ignoring these objects).  Ignoring errors should be used only as a
  **last resource**.  You should first try to fix the errors as best as you can,
  so your documentation links are properly working.


.. tip::

   You may use ``bdt dumpsphinx`` to list *documented* objects in remote sphinx
   documentations.  This resource can be helpful to fix issues during sphinx
   documentation building.


Project logo and branding
=========================

In the gitlab Settings / General page of your project, update the logo to use
one of ours:

* For Bob_:

  .. image:: https://gitlab.idiap.ch/bob/bob.devtools/raw/master/bob/devtools/templates/doc/img/bob-128x128.png
     :alt: Bob's logo for gitlab

* Fob BEAT_:

  .. image:: https://gitlab.idiap.ch/bob/bob.devtools/raw/master/bob/devtools/templates/doc/img/beat-128x128.png
     :alt: BEAT's logo for gitlab


.. include:: links.rst
