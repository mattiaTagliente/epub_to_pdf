# -*- coding: utf-8 -*-
"""
EPUB to PDF conversion module.

Provides high-fidelity EPUB to PDF conversion optimized for OCR processing.
Supports PyMuPDF (primary) and Calibre ebook-convert (fallback) backends.
"""

import subprocess
import shutil
from enum import Enum
from pathlib import Path
from typing import Callable, Optional


class ConversionMethod(Enum):
    """Available conversion methods."""
    PYMUPDF = "pymupdf"
    MUTOOL = "mutool"
    CALIBRE = "calibre"
    AUTO = "auto"


class ConversionError(Exception):
    """Raised when EPUB to PDF conversion fails."""
    pass


def _check_pymupdf_available() -> bool:
    """Check if PyMuPDF is available."""
    try:
        import fitz  # noqa: F401
        return True
    except ImportError:
        return False


def _check_mutool_available() -> bool:
    """Check if mutool is available in PATH."""
    return shutil.which("mutool") is not None


def _check_calibre_available() -> bool:
    """Check if Calibre's ebook-convert is available in PATH."""
    return shutil.which("ebook-convert") is not None


def _convert_with_pymupdf(
    epub_path: Path,
    pdf_path: Path,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Path:
    """
    Convert EPUB to PDF using PyMuPDF.

    PyMuPDF uses MuPDF as backend, providing high-fidelity rendering
    with sub-pixel accuracy essential for OCR processing.

    Args:
        epub_path: Path to input EPUB file
        pdf_path: Path for output PDF file
        progress_callback: Optional callback for progress updates

    Returns:
        Path to the created PDF file

    Raises:
        ConversionError: If conversion fails
    """
    try:
        import fitz
    except ImportError:
        raise ConversionError("PyMuPDF is not installed. Install with: uv pip install pymupdf")

    if progress_callback:
        progress_callback("Opening EPUB file...")

    try:
        doc = fitz.open(epub_path)

        if progress_callback:
            progress_callback(f"Converting {doc.page_count} pages...")

        # Save as PDF - PyMuPDF handles the conversion automatically
        doc.save(str(pdf_path))
        doc.close()

        if progress_callback:
            progress_callback("Conversion complete!")

        return pdf_path

    except Exception as e:
        raise ConversionError(f"PyMuPDF conversion failed: {e}")


def _convert_with_mutool(
    epub_path: Path,
    pdf_path: Path,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Path:
    """
    Convert EPUB to PDF using mutool command-line tool.

    Uses A4 page dimensions (595 x 842 points) for optimal layout.

    Args:
        epub_path: Path to input EPUB file
        pdf_path: Path for output PDF file
        progress_callback: Optional callback for progress updates

    Returns:
        Path to the created PDF file

    Raises:
        ConversionError: If conversion fails
    """
    if not _check_mutool_available():
        raise ConversionError("mutool is not installed or not in PATH")

    if progress_callback:
        progress_callback("Running mutool convert...")

    try:
        result = subprocess.run(
            [
                "mutool", "convert",
                "-o", str(pdf_path),
                "-O", "width=595,height=842",  # A4 dimensions in points
                "-O", "em=12",  # Base font size
                str(epub_path)
            ],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8"
        )

        if progress_callback:
            progress_callback("Conversion complete!")

        return pdf_path

    except subprocess.CalledProcessError as e:
        raise ConversionError(f"mutool conversion failed: {e.stderr}")
    except Exception as e:
        raise ConversionError(f"mutool conversion failed: {e}")


def _convert_with_calibre(
    epub_path: Path,
    pdf_path: Path,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Path:
    """
    Convert EPUB to PDF using Calibre's ebook-convert.

    Uses 'tablet' output profile to prevent image downscaling,
    essential for preserving equation image quality.

    Args:
        epub_path: Path to input EPUB file
        pdf_path: Path for output PDF file
        progress_callback: Optional callback for progress updates

    Returns:
        Path to the created PDF file

    Raises:
        ConversionError: If conversion fails
    """
    if not _check_calibre_available():
        raise ConversionError(
            "Calibre's ebook-convert is not installed or not in PATH. "
            "Install Calibre from: https://calibre-ebook.com/download"
        )

    if progress_callback:
        progress_callback("Running Calibre ebook-convert...")

    try:
        result = subprocess.run(
            [
                "ebook-convert",
                str(epub_path),
                str(pdf_path),
                "--output-profile", "tablet",
                "--paper-size", "a4",
                "--preserve-cover-aspect-ratio",
                "--embed-all-fonts",
                "--pdf-page-margin-left", "72",
                "--pdf-page-margin-right", "72",
                "--pdf-page-margin-top", "72",
                "--pdf-page-margin-bottom", "72",
            ],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8"
        )

        if progress_callback:
            progress_callback("Conversion complete!")

        return pdf_path

    except subprocess.CalledProcessError as e:
        raise ConversionError(f"Calibre conversion failed: {e.stderr}")
    except Exception as e:
        raise ConversionError(f"Calibre conversion failed: {e}")


def get_available_methods() -> list[ConversionMethod]:
    """
    Get list of available conversion methods on this system.

    Returns:
        List of available ConversionMethod values
    """
    available = []

    if _check_pymupdf_available():
        available.append(ConversionMethod.PYMUPDF)

    if _check_mutool_available():
        available.append(ConversionMethod.MUTOOL)

    if _check_calibre_available():
        available.append(ConversionMethod.CALIBRE)

    return available


def convert_epub_to_pdf(
    epub_path: Path | str,
    pdf_path: Optional[Path | str] = None,
    method: ConversionMethod = ConversionMethod.AUTO,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Path:
    """
    Convert an EPUB file to PDF format.

    The conversion is optimized for subsequent OCR processing,
    preserving image quality and layout fidelity.

    Args:
        epub_path: Path to the input EPUB file
        pdf_path: Path for the output PDF file. If None, uses same
                  directory and name as EPUB with .pdf extension.
        method: Conversion method to use. AUTO will try methods in
                order of preference: PyMuPDF > mutool > Calibre
        progress_callback: Optional callback function that receives
                          progress messages as strings

    Returns:
        Path to the created PDF file

    Raises:
        FileNotFoundError: If EPUB file doesn't exist
        ConversionError: If conversion fails with all available methods
        ValueError: If no conversion tools are available
    """
    epub_path = Path(epub_path)

    if not epub_path.exists():
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")

    if not epub_path.suffix.lower() == ".epub":
        raise ValueError(f"File is not an EPUB: {epub_path}")

    # Determine output path
    if pdf_path is None:
        pdf_path = epub_path.with_suffix(".pdf")
    else:
        pdf_path = Path(pdf_path)

    # Ensure output directory exists
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    if method == ConversionMethod.AUTO:
        # Try methods in order of preference
        errors = []

        # 1. Try PyMuPDF first (fastest, best quality)
        if _check_pymupdf_available():
            try:
                if progress_callback:
                    progress_callback("Using PyMuPDF for conversion...")
                return _convert_with_pymupdf(epub_path, pdf_path, progress_callback)
            except ConversionError as e:
                errors.append(f"PyMuPDF: {e}")

        # 2. Try mutool
        if _check_mutool_available():
            try:
                if progress_callback:
                    progress_callback("Using mutool for conversion...")
                return _convert_with_mutool(epub_path, pdf_path, progress_callback)
            except ConversionError as e:
                errors.append(f"mutool: {e}")

        # 3. Try Calibre
        if _check_calibre_available():
            try:
                if progress_callback:
                    progress_callback("Using Calibre for conversion...")
                return _convert_with_calibre(epub_path, pdf_path, progress_callback)
            except ConversionError as e:
                errors.append(f"Calibre: {e}")

        if errors:
            raise ConversionError(
                "All conversion methods failed:\n" + "\n".join(errors)
            )
        else:
            raise ValueError(
                "No conversion tools available. Please install one of:\n"
                "- PyMuPDF: uv pip install pymupdf\n"
                "- MuPDF: https://mupdf.com/releases/\n"
                "- Calibre: https://calibre-ebook.com/download"
            )

    elif method == ConversionMethod.PYMUPDF:
        return _convert_with_pymupdf(epub_path, pdf_path, progress_callback)

    elif method == ConversionMethod.MUTOOL:
        return _convert_with_mutool(epub_path, pdf_path, progress_callback)

    elif method == ConversionMethod.CALIBRE:
        return _convert_with_calibre(epub_path, pdf_path, progress_callback)

    else:
        raise ValueError(f"Unknown conversion method: {method}")
