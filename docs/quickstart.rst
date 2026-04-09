.. _quickstart:

Quick Start
===========

After completing the :doc:`installation`, you can use PDFanalysis either through
the interactive web application or programmatically via Python.

Launching the Web Application
------------------------------

The easiest way to get started is the Streamlit web interface:

.. code-block:: bash

   pdfanalysis-app

This opens a browser-based GUI that guides you through the full analysis workflow
without writing any code.

Using the Automatic Analysis Function
--------------------------------------

For scripted or batch analysis, use :func:`~pdfanalysis.pdfanalysis.perform_automatic_pdf_analysis`:

.. code-block:: python

   from pdfanalysis import perform_automatic_pdf_analysis

   results = perform_automatic_pdf_analysis(
       pdf_file="path/to/data.gr",
       cif_file="path/to/structure.cif",
       r_coh=30.0,            # Coherence length in Ångströms
       tolerance_size_structure=3.0,
       n_spheres=2,
   )

The function automatically:

1. Determines the coherence length if ``r_coh`` is not provided
2. Generates candidate nanoparticle structures
3. Runs a fast screening refinement
4. Performs fine refinement on the best candidates
5. Returns ranked results

Using Individual Classes
------------------------

For more control over each step, use the classes directly:

Step 1 — Generate structures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pdfanalysis import StructureGenerator

   generator = StructureGenerator(
       pdfpath="output_dir",
       cif_file="structure.cif",
       auto_mode=True,
       pdf_file="data.gr",   # used to auto-detect particle size
   )
   strufile_dir = generator.run()

Step 2 — Screen structures
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pdfanalysis import StructureScreener

   screener = StructureScreener(
       strufile_dir=strufile_dir,
       pdffile_dir="pdf_directory",
       fast_screening=True,
   )
   best_results, candidates = screener.run()

Step 3 — Fine refinement
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pdfanalysis import PDFRefinement

   refinement = PDFRefinement(
       strufile=candidates[0],
       pdffile="data.gr",
       rmin=2.0,
       rmax=30.0,
   )
   result = refinement.run()

Step 4 — Extract a PDF from raw data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have raw diffraction data, use :class:`~pdfanalysis.pdf_extractor.PDFExtractor`
to extract the PDF first:

.. code-block:: python

   from pdfanalysis import PDFExtractor

   extractor = PDFExtractor(
       datafilelist=["data/sample.xy"],
       composition="Au",
       qmin=0.8,
       qmax=20.0,
       qmaxinst=25.0,
       wavelength=0.7107,
   )
   extractor.writecfg()
   extractor.run()

Next Steps
----------

- Read the :doc:`workflow` page for a detailed explanation of each analysis step.
- Browse the :doc:`api/index` for complete class and function documentation.
