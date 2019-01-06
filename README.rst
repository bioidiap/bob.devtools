.. vim: set fileencoding=utf-8 :

===============================================
 A package that contains tools to maintain Bob
===============================================

This package is part of the signal-processing and machine learning toolbox
Bob_. It provides tools to help maintain Bob_.


Installation
------------

This package needs to be installed in a conda environment. To install
this package, run::

  $ conda env create -f env.yml
  $ conda activate bdt
  (bdt) $ buildout
  (bdt) $ ./bin/bdt --help
  ...

To build the documentation, just do::

  (bdt) $ ./bin/sphinx-build doc sphinx


Contact
-------

For questions or reporting issues to this software package, contact our
development `mailing list`_.


.. Place your references here:
.. _bob: https://www.idiap.ch/software/bob
.. _mailing list: https://www.idiap.ch/software/bob/discuss
