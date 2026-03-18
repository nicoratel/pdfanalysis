# Installation Instructions for PDFanalysis

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- conda (recommended for diffpy installation)

## Method 1: Installation with conda (Recommended)

DiffPy packages are best installed via conda-forge:

```bash
# Create a new conda environment
conda create -n pdfanalysis python=3.10
conda activate pdfanalysis

# Install diffpy-cmi from conda-forge (includes structure + srfit)
conda install -c conda-forge diffpy-cmi

# Install other dependencies
conda install -c conda-forge ase numpy scipy matplotlib tqdm psutil

# Install the pdfanalysis package
cd /path/to/PDFanalysis_streamlit/src
pip install -e .

# Optional: Install Streamlit app dependencies
pip install .[app]

# Optional: Install notebook dependencies
pip install .[notebook]
```

## Method 2: Installation with pip only

If you prefer pip-only installation:

```bash
# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install numpy scipy matplotlib ase tqdm psutil

# Install diffpy-cmi (may require compilation)
pip install diffpy-cmi

# Install the pdfanalysis package
cd /path/to/PDFanalysis_streamlit/src
pip install -e .
```

**Note**: Installing diffpy via pip may require compilation and can be problematic. Using conda is strongly recommended.

## Method 3: Development Installation

For developers who want to modify the code:

```bash
# Clone or navigate to the repository
cd /path/to/PDFanalysis_streamlit/src

# Install in editable mode with all development dependencies
pip install -e .[dev]

# This includes pytest, black, flake8, mypy
```


## Installing Optional Components

### For Streamlit Web App
```bash
pip install .[app]
# or
pip install streamlit plotly
```

### For Jupyter Notebooks
```bash
pip install .[notebook]
# or
pip install ipython jupyter py3Dmol
```

### All Optional Dependencies
```bash
pip install .[all]
```

## Running the Application

### Command Line
```python
from pdfanalysis import perform_automatic_pdf_analysis

results = perform_automatic_pdf_analysis(
    pdf_file="data.gr",
    cif_file="structure.cif",
    r_coh=30.0
)
```

### Streamlit Web Interface
```bash
streamlit run pdfanalysis/app_pdf_analysis.py
```

Or if installed as a script:
```bash
pdfanalysis-app
```

## Troubleshooting

### DiffPy Installation Issues

If diffpy installation fails with pip:
1. Use conda instead: `conda install -c conda-forge diffpy-cmi`
2. Or follow instructions at: https://www.diffpy.org/products/diffpycmi/index.html

### Import Errors

If you get import errors:
```python
# Check if package is correctly installed
pip list | grep pdfanalysis

# Reinstall in editable mode
pip install -e .
```

### ASE Installation Issues

If ASE installation fails:
```bash
# Install via conda
conda install -c conda-forge ase

# Or specific version
pip install ase==3.22.1
```

## Uninstalling

```bash
pip uninstall pdfanalysis
```

## Building Distribution Packages

To create distribution packages for PyPI:

```bash
# Install build tools
pip install build twine

# Build distribution
python -m build

# This creates:
# - dist/pdfanalysis-1.0.0.tar.gz (source distribution)
# - dist/pdfanalysis-1.0.0-py3-none-any.whl (wheel)

# Upload to PyPI (if you have credentials)
twine upload dist/*
```

## System-Wide Installation (Not Recommended)

```bash
# NOT recommended - installs globally
sudo pip install .

# Better: use virtual environment or conda environment
```

## Directory Structure After Installation

```
PDFanalysis_streamlit/src/
├── pdfanalysis/              # Package directory
│   ├── __init__.py
│   ├── pdf_extractor.py
│   ├── structure_generator.py
│   ├── ...
├── pyproject.toml           # Modern config
├── setup.py                 # Legacy setup
├── README.md                # Documentation
├── LICENSE                  # MIT license
├── MANIFEST.in              # Distribution includes
└── INSTALL.md              # This file
```

## Getting Help

- GitHub Issues: https://github.com/nicoratel/pdfanalysis/issues
- Email: nicolas.ratel-ramond@insa-toulouse.fr
