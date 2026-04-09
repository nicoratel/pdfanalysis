.. _streamlit_app:

Streamlit Web Application
==========================

PDFanalysis includes an interactive web application built with
`Streamlit <https://streamlit.io>`_ that provides a graphical interface for the
complete analysis workflow.

Launching the App
-----------------

After installation, run:

.. code-block:: bash

   pdfanalysis-app

This starts a local web server and opens the application in your default browser.

.. note::

   On Windows, if the command is not recognized, see ``WINDOWS_INSTALL.md`` in
   the repository for platform-specific instructions.

Features
--------

The Streamlit application provides:

- **File upload** — drag-and-drop PDF files (``.gr``) and CIF structures
- **Parameter control** — interactive sliders and inputs for all analysis parameters
- **Live plots** — interactive Plotly charts updated in real time
- **Progress tracking** — step-by-step progress bars during computation
- **Result export** — download refined structures and fit reports

Workflow in the App
--------------------

The app guides you through the same steps described in the :doc:`workflow` page:

1. Upload your experimental ``.gr`` file
2. Upload the reference CIF structure
3. Adjust analysis parameters (or use defaults)
4. Run the analysis and inspect results interactively
5. Download the generated report

Running in Development Mode
-----------------------------

If you have cloned the repository and want to run the app directly from source:

.. code-block:: bash

   cd pdfanalysis
   streamlit run pdfanalysis/app_pdf_analysis.py
