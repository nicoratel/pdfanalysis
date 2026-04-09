.. _workflow:

Analysis Workflow
=================

This page describes the recommended analysis workflow for PDF structure analysis
of nanoparticles using PDFanalysis.

.. contents:: Contents
   :local:
   :depth: 2


Overview
--------

The complete workflow consists of five main steps:

.. code-block:: text

   Raw diffraction data
          │
          ▼
   ┌─────────────────────┐
   │  Step 0 (optional)  │  PDF Extraction (PDFExtractor)
   │  .xy → .gr          │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │       Step 1        │  Coherence length estimation
   │  Determine r_coh    │  (auto-detected or user-supplied)
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │       Step 2        │  Structure Generation (StructureGenerator)
   │  Generate structures│  icosahedra, decahedra, octahedra, spheres
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │       Step 3        │  Fast Screening (PDFRefinementFast)
   │  Fast refinement    │  Rough fits, select best candidates
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │       Step 4        │  Fine Refinement (PDFRefinement)
   │  Full refinement    │  Detailed fits on candidates
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │       Step 5        │  Report Generation (StructureReportGenerator)
   │  Generate report    │  Ranked results, plots, summary
   └─────────────────────┘


Step 0: PDF Extraction (optional)
----------------------------------

If you have raw diffraction data (e.g., ``.xy`` or ``.chi`` files from synchrotron
experiments), you first need to extract the PDF using ``PDFgetX3``.

**Class:** :class:`~pdfanalysis.pdf_extractor.PDFExtractor`

Key parameters:

- ``datafilelist`` — list of raw data file paths
- ``composition`` — chemical formula of the sample (e.g., ``"Au"``, ``"Pt3Fe"``)
- ``qmin``, ``qmax`` — Q-range used for the Fourier transform (Å\ :sup:`-1`)
- ``qmaxinst`` — maximum Q of the instrument (Å\ :sup:`-1`)
- ``wavelength`` — X-ray wavelength in Å (default: ``0.7107`` Å for 17 keV)

.. code-block:: python

   from pdfanalysis import PDFExtractor

   extractor = PDFExtractor(
       datafilelist=["data/sample_00001.xy"],
       composition="Au",
       qmin=0.8,
       qmax=20.0,
       qmaxinst=25.0,
       wavelength=0.7107,
       bgscale=0.95,
   )
   extractor.writecfg()
   extractor.run()


Step 1: Coherence Length Estimation
-------------------------------------

The coherence length ``r_coh`` (in Å) represents the approximate maximum particle
diameter — the ``r`` value beyond which the PDF signal is dominated by noise.

It can be:

- **Automatically detected** from the experimental PDF (default when ``r_coh=None``)
- **Manually specified** by the user

.. code-block:: python

   # Automatic detection
   results = perform_automatic_pdf_analysis(
       pdf_file="data.gr",
       cif_file="Au.cif",
       r_coh=None,  # auto-detect
   )

   # Manual specification
   results = perform_automatic_pdf_analysis(
       pdf_file="data.gr",
       cif_file="Au.cif",
       r_coh=35.0,  # 35 Å particle diameter
   )


Step 2: Structure Generation
------------------------------

**Class:** :class:`~pdfanalysis.structure_generator.StructureGenerator`

PDFanalysis generates candidate nanoparticle structures based on the coherence
length. Supported morphologies:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Morphology
     - Description
   * - **Icosahedra**
     - High-symmetry icosahedral clusters (magic number sizes)
   * - **Decahedra**
     - Marks decahedral particles (pentagonal symmetry)
   * - **Octahedra**
     - FCC-based truncated octahedra
   * - **Spheres**
     - Spherical cuts from the bulk crystal structure

When ``auto_mode=True``, the generator automatically determines appropriate sizes
from ``r_coh`` and generates multiple structures near that diameter.

Key parameters:

- ``cif_file`` — bulk crystal structure (CIF format); use an Fm-3m CIF for icosahedra
- ``r_coh`` — target coherence length (Å)
- ``n_sizes`` — number of different sizes to generate for spheres
- ``tolerance`` — size tolerance around ``r_coh`` (±Å)
- ``n_jobs`` — number of parallel CPU cores to use (``-1`` = all cores)


Step 3: Fast Structure Screening
----------------------------------

**Class:** :class:`~pdfanalysis.pdf_refinement_fast.PDFRefinementFast`

A rapid refinement is performed on all generated structures to quickly identify
the most promising candidates. Parameters are refined over a limited ``r`` range
with coarser bins.

Key parameters:

- ``rmax_fast`` — maximum ``r`` for fast refinement (default: 15 Å)
- ``threshold_percent_fast`` — percentage above best R\ :sub:`w` to keep candidates
- ``rbins_fast`` — number of ``r`` bins per Å in fast mode


Step 4: Fine PDF Refinement
-----------------------------

**Class:** :class:`~pdfanalysis.pdf_refinement.PDFRefinement`

Full refinement over the complete ``r`` range is performed on the candidates
selected in Step 3. Refined parameters typically include lattice parameter,
isotropic displacement parameters (``delta1``, ``delta2``), scale factor, and
particle envelope.

Key parameters:

- ``rmin`` — minimum ``r`` for refinement (default: 2.0 Å)
- ``rmax`` — maximum ``r`` for refinement
- ``rbins_fine`` — number of ``r`` bins per Å in fine mode


Step 5: Report Generation
--------------------------

**Class:** :class:`~pdfanalysis.structure_report_generator.StructureReportGenerator`

The report generator produces:

- A ranked summary table of all refined structures (sorted by R\ :sub:`w`)
- Individual fit plots (experimental vs. calculated PDF with difference curve)
- A JSON results file for further processing
- 3D structure visualizations (in Jupyter notebooks with ``py3Dmol``)


Structure Customization
-----------------------

**Class:** :class:`~pdfanalysis.structure_custom.StructureCustom`

Optional step to modify generated structures before refinement:

- **Zoom/scale** — uniformly scale atomic positions
- **Element substitution** — replace one element with another (e.g., Au → Pt)

.. code-block:: python

   from pdfanalysis import StructureCustom

   custom = StructureCustom(strufile="structure.xyz")
   custom.substitute_element(old_element="Au", new_element="Pt")
   custom.save("structure_Pt.xyz")
