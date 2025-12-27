# -*- coding: utf-8 -*-
"""
EPUB to PDF Converter - A graphical utility for converting EPUB files to PDF.

Optimized for subsequent Mistral OCR processing with high-fidelity output.
"""

__version__ = "1.0.0"
__author__ = "Mattia Tagliente"

from .converter import convert_epub_to_pdf, ConversionMethod

__all__ = ["convert_epub_to_pdf", "ConversionMethod", "__version__"]
