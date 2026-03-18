"""
PDFanalysis package for automated PDF structure analysis.

This package provides tools for:
- PDF extraction from experimental data
- Structure generation (nanoparticles)
- Structure customization
- PDF refinement
- Structure screening
- Report generation
"""

from .pdf_extractor import PDFExtractor
from .structure_generator import StructureGenerator
from .structure_custom import StructureCustom
from .structure_report_generator import StructureReportGenerator
from .pdf_refinement import PDFRefinement
from .pdf_refinement_fast import PDFRefinementFast
from .structure_screener import StructureScreener

__all__ = [
    'PDFExtractor',
    'StructureGenerator',
    'StructureCustom',
    'StructureReportGenerator',
    'PDFRefinement',
    'PDFRefinementFast',
    'StructureScreener',
]

__version__ = '1.0.0'
