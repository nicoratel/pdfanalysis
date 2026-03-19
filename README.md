# PDFanalysis

Automated PDF (Pair Distribution Function) structure analysis for small metallic nanoparticles.

## Description

PDFanalysis is a comprehensive Python package for analyzing nanoparticle structures using pair distribution function (PDF) analysis. It provides tools for:

- **PDF extraction** from experimental data
- **Structure generation** (icosahedra, decahedra, octahedra, spheres)
- **Structure customization** (zoomscale, element substitution)
- **PDF refinement** using diffpy.srfit
- **Structure screening** against experimental PDFs
- **Report generation** with detailed analysis results

The recommended workflow for a single pdf is the following:
- **Estimation of particle size** from experimental pdf data. Determines the r value at which the pdf signal is dominated by noise
- **Structure generation**: icosahedra, octahedra, spheres and decahedra are generated with the size determined above (or specified by the user)
- **Fast structure screening**: each structure is roughly refined against experimental data. Best results within a given confidence interval are considered for the fine refinement
- **Fine strucutre screening**: structures who have passed the first refinement cycle are refined against experimental pdf. 


## Installation

**Important:** This package requires `diffpy.cmi` which cannot be installed via pip. You must use conda.

### Recommended method: Using environment.yml

```bash
# Download the environment file from GitHub or clone the repository
conda env create -f environment.yml
conda activate pdfanalysis
```

### Alternative: Manual installation

```bash
# 1. Create and activate conda environment
conda create -n pdfanalysis python=3.11
conda activate pdfanalysis

# 2. Install diffpy.cmi and other scientific dependencies via conda
conda install -c conda-forge diffpy.cmi ase spglib

# 3. Install pdfanalysis from PyPI
pip install pdfanalysis
```

### Optional dependencies

```bash
# For Jupyter notebooks with 3D visualization
pip install pdfanalysis[notebook]

# For development tools
pip install pdfanalysis[dev]

# Install everything
pip install pdfanalysis[all]
```

### Install from source

```bash
# Clone the repository
git clone https://github.com/nicoratel/pdfanalysis.git
cd pdfanalysis

# Install diffpy.cmi via conda first
conda install -c conda-forge diffpy.cmi ase spglib

# Then install the package
pip install .
```

## Dependencies

### Required (must be installed via conda)
- `diffpy.cmi` - PDF calculation and fitting framework

### Core dependencies (installed automatically via pip)
- `numpy` - Numerical computations
- `scipy` - Scientific computing and optimization
- `matplotlib` - Plotting and visualization
- `ase` - Atomic Simulation Environment
- `diffpy-cmi` - DiffPy suite (structure manipulation + PDF refinement)
- `tqdm` - Progress bars
- `psutil` - CPU/memory management

### Optional dependencies
- `streamlit` - Web application framework
- `plotly` - Interactive plots
- `ipython` - Enhanced Python shell
- `jupyter` - Notebook interface
- `py3Dmol` - 3D molecular visualization

## Quick Start

### Running the Streamlit app

After installation, launch the web interface with:

```bash
pdfanalysis-app
```

This will automatically start the Streamlit server and open the app in your default browser.

**Note for Windows users:** If the command doesn't work, see [WINDOWS_INSTALL.md](WINDOWS_INSTALL.md) for troubleshooting steps.

### Using the main analysis function

```python
from pdfanalysis import perform_automatic_pdf_analysis

results = perform_automatic_pdf_analysis(
    pdf_file="path/to/data.gr",
    cif_file="path/to/structure.cif",
    r_coh=30.0,  # Coherence length in Angstroms
    tolerance_size_structure=3.0,
    n_spheres=2
)
```

### Using individual classes

```python
from pdfanalysis import (
    PDFExtractor,
    StructureGenerator,
    PDFRefinement,
    StructureScreener
)

# Generate structures
generator = StructureGenerator(
    pdfpath="output_dir",
    cif_file="structure.cif",
    auto_mode=True,
    pdf_file="data.gr"
)
strufile_dir = generator.run()

# Screen structures
screener = StructureScreener(
    strufile_dir=strufile_dir,
    pdffile_dir="pdf_directory",
    fast_screening=True
)
best_results, candidates = screener.run()

# Refine best structure
refinement = PDFRefinement(
    pdffile="data.gr",
    strufile=best_results["data.gr"]["strufile"],
    save_tag=True
)
rw = refinement.refine()
```



## Package Structure

```
pdfanalysis/
├── __init__.py                      # Package initialization
├── pdf_extractor.py                 # PDF extraction from experimental data
├── structure_generator.py           # Nanoparticle structure generation
├── structure_custom.py              # Structure transformation
├── structure_report_generator.py    # PDF report generation
├── pdf_refinement.py               # Full PDF refinement
├── pdf_refinement_fast.py          # Fast refinement for screening
├── structure_screener.py           # Structure screening
├── pdfanalysis.py                  # Main analysis workflow
└── app_pdf_analysis.py             # Streamlit web interface
```

## Features

### Automatic Structure Generation
- Auto-detection of coherence length from PDF
- Multiple structure types: icosahedra, decahedra, octahedra, spheres
- Parallel processing for fast generation
- Automatic filtering based on size range

### Fast Screening
- Two-pass screening: fast initial screening + full refinement
- Automatic candidate selection (min(Rw) ± threshold%)
- Progress tracking with tqdm
- Multiprocessing support

### Comprehensive Reports
- PDF reports with fit curves, structure thumbnails
- Top N results tables
- 3D structure visualizations
- Complete refinement statistics

## Examples

See the `examples/` directory for Jupyter notebooks demonstrating:
- Basic PDF analysis workflow
- Custom structure generation
- Advanced refinement options
- Batch processing

## Citation

If you use this package in your research, please cite:

```
@software{pdfanalysis,
  author = {Ratel-Ramond, Nicolas},
  title = {PDFanalysis: Automated PDF structure analysis for nanoparticles},
  year = {2026},
  url = {https://github.com/nicoratel/pdfanalysis}
}
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For bugs and feature requests, please open an issue on GitHub:
https://github.com/nicoratel/pdfanalysis/issues

## Acknowledgments

This package uses:
- DiffPy-CMI for PDF refinement
- ASE for structure manipulation
- The Scientific Python ecosystem (NumPy, SciPy, Matplotlib)
