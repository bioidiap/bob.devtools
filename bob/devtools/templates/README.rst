.. -*- coding: utf-8 -*-

.. image:: https://img.shields.io/badge/docs-stable-yellow.svg
   :target: https://www.idiap.ch/software/bob/docs/{{ package }}/stable/index.html
.. image:: https://img.shields.io/badge/docs-latest-orange.svg
   :target: https://www.idiap.ch/software/bob/docs/{{ package }}/master/index.html
.. image:: https://gitlab.idiap.ch/{{ package }}/badges/master/build.svg
   :target: https://gitlab.idiap.ch/{{ package }}/commits/master
.. image:: https://gitlab.idiap.ch/{{ package }}/badges/master/coverage.svg
   :target: https://www.idiap.ch/software/bob/docs/{{ package }}/master/coverage/index.html
.. image:: https://img.shields.io/badge/gitlab-project-0000c0.svg
   :target: https://gitlab.idiap.ch/{{ package }}
.. image:: https://img.shields.io/pypi/v/{{ name }}.svg
   :target: https://pypi.python.org/pypi/{{ name }}


{{ rst_title }}

This package is part of {% if group == "bob" %}the signal-processing and machine learning toolbox Bob_{% else %}BEAT_, an open-source evaluation platform for data science algorithms and workflows{% endif %}.

.. todo::

   **Complete the sentence above to include one phrase about your
   package!  Once this is done, delete this to-do!**


Installation
------------

Complete {{ group }}'s `installation`_ instructions. Then, to install this
package, run::

  $ conda install {{ name }}


Contact
-------

For questions or reporting issues to this software package, contact our
development `mailing list`_.


.. Place your references here:
.. _{{ group }}: https://www.idiap.ch/software/{{ group }}
.. _installation: https://www.idiap.ch/software/{{ group }}/install
.. _mailing list: https://www.idiap.ch/software/{{ group }}/discuss
