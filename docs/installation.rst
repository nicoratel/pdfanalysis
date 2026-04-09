.. _installation:

Installation
============

.. important::

   PDFanalysis requires ``diffpy.cmi``, which **cannot be installed via pip alone**.
   You must use ``conda`` to install this dependency first.

Recommended Method: conda environment
--------------------------------------

The simplest approach is to use the provided ``environment.yml`` file, which
installs all dependencies including ``diffpy.cmi``.

.. code-block:: bash

   # Clone the repository or download the environment file
   git clone https://github.com/nicoratel/pdfanalysis.git
   cd pdfanalysis

   # Create the conda environment
   conda env create -f environment.yml
   conda activate pdfanalysis

Manual Installation
-------------------

If you prefer to set up the environment manually:

.. code-block:: bash

   # 1. Create a new conda environment
   conda create -n pdfanalysis python=3.11
   conda activate pdfanalysis

   # 2. Install diffpy.cmi and other scientific dependencies via conda
   conda install -c conda-forge diffpy.cmi ase spglib

   # 3. Install pdfanalysis from PyPI
   pip install pdfanalysis

Install from Source
-------------------

.. code-block:: bash

   git clone https://github.com/nicoratel/pdfanalysis.git
   cd pdfanalysis

   # Install diffpy.cmi via conda first
   conda install -c conda-forge diffpy.cmi ase spglib

   # Then install the package in editable mode
   pip install -e .

Optional Dependencies
---------------------

.. code-block:: bash

   # For Jupyter notebooks with 3D visualization
   pip install pdfanalysis[notebook]

   # For development tools (pytest, black, flake8, mypy)
   pip install pdfanalysis[dev]

   # Install everything
   pip install pdfanalysis[all]

Windows Users
-------------

If you are on Windows and encounter issues with the ``pdfanalysis-app`` command,
please refer to the ``WINDOWS_INSTALL.md`` file included in the repository.

Dependencies Overview
---------------------

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Package
     - Install via
     - Purpose
   * - ``diffpy.cmi``
     - conda
     - PDF calculation and fitting framework (**required**)
   * - ``numpy``
     - pip
     - Numerical computations
   * - ``scipy``
     - pip
     - Scientific computing and optimization
   * - ``matplotlib``
     - pip
     - Plotting and visualization
   * - ``ase``
     - conda/pip
     - Atomic Simulation Environment
   * - ``spglib``
     - conda/pip
     - Space group analysis
   * - ``tqdm``
     - pip
     - Progress bars
   * - ``psutil``
     - pip
     - CPU/memory management
   * - ``streamlit``
     - pip
     - Web application interface
   * - ``plotly``
     - pip
     - Interactive plots
