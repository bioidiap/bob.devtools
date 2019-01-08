.. vim: set fileencoding=utf-8 :

.. image:: https://img.shields.io/badge/docs-stable-yellow.svg
   :target: https://www.idiap.ch/software/bob/docs/bob/bob.devtools/stable/index.html
.. image:: https://img.shields.io/badge/docs-latest-orange.svg
   :target: https://www.idiap.ch/software/bob/docs/bob/bob.devtools/master/index.html
.. image:: https://gitlab.idiap.ch/bob/bob.devtools/badges/master/build.svg
   :target: https://gitlab.idiap.ch/bob/bob.devtools/commits/master
.. image:: https://gitlab.idiap.ch/bob/bob.devtools/badges/master/coverage.svg
   :target: https://gitlab.idiap.ch/bob/bob.devtools/commits/master
.. image:: https://img.shields.io/badge/gitlab-project-0000c0.svg
   :target: https://gitlab.idiap.ch/bob/bob.devtools
.. image:: https://img.shields.io/pypi/v/bob.devtools.svg
   :target: https://pypi.python.org/pypi/bob.devtools


==================================
 Bob/BEAT Development Tools (bdt)
==================================

This package is part of the signal-processing and machine learning toolbox
Bob_ and the BEAT_ framework. It provides tools to help maintain Bob_ and
BEAT_ packages through Gitlab and conda_.


Installation
------------

You can install this package via conda_, simply pointing to our stable or beta
channels::

  $ conda create -n bdt -c https://www.idiap.ch/software/bob/conda bob.devtools
  # or, for beta releases:
  $ conda create -n bdt -c https://www.idiap.ch/software/bob/conda/label/beta bob.devtools

We provide packages for both 64-bit Linux and MacOS. Once installed, you can
use these tools within the created environment like this::

  $ conda activate bdt
  (bdt) $ bdt --help


Contact
-------

For questions or reporting issues to this software package, contact our
development `mailing list`_.


.. Place your references here:
.. _conda: https://conda.io
.. _bob: https://www.idiap.ch/software/bob
.. _beat: https://www.idiap.ch/software/beat
.. _mailing list: https://www.idiap.ch/software/bob/discuss
