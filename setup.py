#!/usr/bin/env python3
"""
Setup script for pdfanalysis package.

For modern installations, prefer using pyproject.toml:
    pip install .
    pip install -e .  # editable/development mode

This setup.py is provided for backwards compatibility.
"""

from setuptools import setup, find_packages
import os

# Read long description from README 
long_description = ""
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="pdfanalysis",
    version="0.1.1",
    description="Automated PDF structure analysis for nanoparticles",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Nicolas Ratel-Ramond",
    author_email="nicolas.ratel-ramond@insa-toulouse.fr",
    url="https://github.com/nicoratel/pdfanalysis",
    packages=find_packages(),
    python_requires=">=3.8",
    
    # Core dependencies
    install_requires=[
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "matplotlib>=3.3.0",
        "ase>=3.22.0",
        "diffpy-cmi>=3.0.0",
        "tqdm>=4.60.0",
        "psutil>=5.8.0",
    ],
    
    # Optional dependencies
    extras_require={
        # Streamlit app
        "app": [
            "streamlit>=1.20.0",
            "plotly>=5.0.0",
        ],
        # Jupyter notebooks
        "notebook": [
            "ipython>=7.0.0",
            "jupyter>=1.0.0",
            "py3Dmol>=2.0.0",
        ],
        # Development tools
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        # All optional dependencies
        "all": [
            "streamlit>=1.20.0",
            "plotly>=5.0.0",
            "ipython>=7.0.0",
            "jupyter>=1.0.0",
            "py3Dmol>=2.0.0",
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    
    # Entry points for command-line scripts
    entry_points={
        "console_scripts": [
            "pdfanalysis-app=app_pdf_analysis:main",
        ],
    },
    
    # Package data
    package_data={
        "pdfanalysis": ["*.md", "*.txt"],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    
    keywords="PDF pair-distribution-function nanoparticles structure-analysis crystallography",
    
    project_urls={
        "Source": "https://github.com/nicoratel/pdfanalysis",
        "Bug Tracker": "https://github.com/nicoratel/pdfanalysis/issues",
    },
)
