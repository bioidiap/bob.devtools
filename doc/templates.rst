.. vim: set fileencoding=utf-8 :

.. _bob.devtools.templates:

===========================
 Additional Considerations
===========================

These instructions describe how create new packages for either Bob_ or BEAT_
and provides information on how to generate a complete, but empty package from
scratch.

.. note::

   If you'd like to update part of your package setup, follow similar
   instructions and then **copy** the relevant files to your **existing**
   setup, overriding portions you know are correct.


.. warning::

   These instructions may change as we get more experience in what needs to be
   changed.  In case that happens, update your package by generating a new
   setup and copying the relevant parts to your existing package(s).


Unit tests
----------

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
---------------------------

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
------------------------

We like to make use of namespaces to define combined sets of functionality that go well together.
Python package namespaces are `explained in details here <http://peak.telecommunity.com/DevCenter/setuptools#namespace-package>`_ together with implementation details.
For bob packages, we usually use the ``bob`` namespace, using several sub-namespaces such as ``bob.io``, ``bob.ip``, ``bob.learn``, ``bob.db`` or (like here) ``bob.example``.


The scripts you created should also somehow contain the namespace of the package. In our example,
the script is named ``bob_example_project_version.py``, reflecting the  namespace ``bob.example``


Distributing your work
----------------------

To distribute a package, we recommend you use PyPI_.
`Python Packaging User Guide <https://packaging.python.org/>`_ contains details
and good examples on how to achieve this.
Moreover, you can provide a conda_ package for your PyPI_ package for easier
installation. In order to create a conda_ package, you need to create a conda_
recipe for that package.

For more detailed instructions on how to achieve this, please see the 
guidelines on `bob.template <https://gitlab.idiap.ch/bob/bob.admin/tree/master/templates>`_.


.. _bob.devtools.buildout:

Buildout.cfg in more details
============================

.. todo::

  This section should include more information about different sections in a buildout.cfg file.



.. _bob.devtools.anatomy:

Anatomy of a new package
========================

There is a folder named `conda` that includes a file `meta.yaml`. As explained earlier this files includes the information used to prepare a proper conda environment.

The folder named `bob` which should only include a file `__init__.py` at this stage is where you will put all your new code and functionality in.

The folder named `doc` includes the minimum necessary information for building package documentation. The file `conf.py` is used by sphinx to build the documentation.

`.gitlab-ci.yml` includes the information about building packages on the ci. We will talk about it later.


COPYING??? MANIFEST.IN???


Continuous Integration and Deployment (CI)
------------------------------------------

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
---------------------------

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
------------

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
=====================================

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
===========================

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
====================

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
====================

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
======================

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
----------------------------------------------

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
---------

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
-------

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
---------------------

The ``setup.py`` should be changed to include eventual ``entry_points`` you
also included in the ``conda/meta.yaml``.  We cannot guess these.


Buildout
--------

The default buildout file ``buildout.cfg`` should buildout from the installed
distribution (use ``bdt create`` for that purpose) and **avoid mr.developer
checkouts**.  If you have one of those, move it to ``develop.cfg`` and create a
new `buildout.cfg` which should be as simple as possible.  The template project
provided by this package takes care of this.


The ``README.rst`` file
-----------------------

You should make the README smaller and easier to maintain.  As of today, many
packages contain outdated installation instructions or outdated links.  More
information can always be found at the documentation, which is automatically
linked from the badges.

You may want to revise the short introduction after automatic template
generation.  Make it short, a single phrase is the most common size.


Sphinx documentation
--------------------

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
-------------------------

In the gitlab Settings / General page of your project, update the logo to use
one of ours:

* For Bob_:

  .. image:: https://gitlab.idiap.ch/bob/bob.devtools/raw/master/bob/devtools/templates/doc/img/bob-128x128.png
     :alt: Bob's logo for gitlab

* Fob BEAT_:

  .. image:: https://gitlab.idiap.ch/bob/bob.devtools/raw/master/bob/devtools/templates/doc/img/beat-128x128.png
     :alt: BEAT's logo for gitlab


.. include:: links.rst
