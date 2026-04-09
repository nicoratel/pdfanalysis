# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# -- Path setup --------------------------------------------------------------
# Ajout du répertoire racine au sys.path pour autodoc
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
project = 'PDFanalysis'
copyright = '2024, Nicolas Ratel-Ramond'
author = 'Nicolas Ratel-Ramond'
release = '0.1.10'
version = '0.1.10'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosummary',
    'sphinx_rtd_theme',
]

# Génération automatique des stubs autosummary
autosummary_generate = True

# -- Napoleon settings (NumPy / Google docstrings) ---------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_rtype = True

# -- autodoc settings --------------------------------------------------------
autodoc_default_options = {
    'members': True,
    'undoc-members': False,
    'show-inheritance': True,
    'member-order': 'bysource',
}

# Modules à simuler (non installables facilement via pip)
autodoc_mock_imports = [
    'diffpy',
    'diffpy.srfit',
    'diffpy.srfit.fitbase',
    'diffpy.srfit.pdf',
    'diffpy.structure',
    'diffpy.utils',
]

# -- Intersphinx mapping -----------------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
    'ase': ('https://ase-lib.org/', None),
}

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
}

html_static_path = ['_static']
html_css_files = []

# Titre affiché dans la barre latérale
html_title = 'PDFanalysis'
html_short_title = 'PDFanalysis'

# -- Options for templates ---------------------------------------------------
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Source file settings ----------------------------------------------------
source_suffix = {'.rst': 'restructuredtext'}
master_doc = 'index'
language = 'en'
