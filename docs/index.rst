.. PDFanalysis documentation master file

PDFanalysis Documentation
==========================

**PDFanalysis** is a Python package for automated Pair Distribution Function (PDF)
structure analysis of metallic nanoparticles. It provides a complete workflow from
raw experimental data to structural identification.

.. image:: https://img.shields.io/pypi/v/pdfanalysis.svg
   :target: https://pypi.org/project/pdfanalysis/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/pdfanalysis.svg
   :target: https://pypi.org/project/pdfanalysis/
   :alt: Python versions

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License

----

Overview
--------

PDF analysis is a powerful technique for determining the local atomic structure of
materials, particularly nanoparticles that lack long-range crystalline order. 
**PDFanalysis** automates the complete analysis pipeline:

1. **PDF extraction** from raw synchrotron or laboratory diffraction data
2. **Nanoparticle structure generation** (icosahedra, decahedra, octahedra, spheres)
3. **Fast structure screening** to narrow down candidate structures
4. **Fine PDF refinement** against experimental data
5. **Report generation** with ranked results

.. note::

   This package requires ``diffpy.cmi`` which must be installed via conda.
   See the :doc:`installation` page for detailed instructions.

----

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   workflow
   streamlit_app

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index

.. toctree::
   :maxdepth: 1
   :caption: About

   changelog


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
