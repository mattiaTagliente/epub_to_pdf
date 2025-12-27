# -*- coding: utf-8 -*-
"""
EPUB to PDF conversion module.

Provides high-fidelity EPUB to PDF conversion optimized for OCR processing.
Supports multiple backends: WeasyPrint (recommended), PyMuPDF, Pandoc, and Calibre.
"""

import subprocess
import shutil
import sys
import zipfile
import tempfile
import xml.etree.ElementTree as ET
from enum import Enum
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import unquote


class ConversionMethod(Enum):
    """Available conversion methods."""
    WEASYPRINT = "weasyprint"
    PYMUPDF = "pymupdf"
    PANDOC = "pandoc"
    CALIBRE = "calibre"
    AUTO = "auto"


class ConversionError(Exception):
    """Raised when EPUB to PDF conversion fails."""
    pass


# Common Calibre installation paths on Windows
CALIBRE_WINDOWS_PATHS = [
    Path("C:/Program Files/Calibre2/ebook-convert.exe"),
    Path("C:/Program Files (x86)/Calibre2/ebook-convert.exe"),
    Path("C:/Program Files/Calibre/ebook-convert.exe"),
    Path("C:/Program Files (x86)/Calibre/ebook-convert.exe"),
]

# XML namespaces for EPUB parsing
NAMESPACES = {
    'container': 'urn:oasis:names:tc:opendocument:xmlns:container',
    'opf': 'http://www.idpf.org/2007/opf',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'ncx': 'http://www.daisy.org/z3986/2005/ncx/',
    'xhtml': 'http://www.w3.org/1999/xhtml',
}


def _find_calibre_executable() -> Optional[Path]:
    """Find Calibre's ebook-convert executable."""
    in_path = shutil.which("ebook-convert")
    if in_path:
        return Path(in_path)

    if sys.platform == "win32":
        for path in CALIBRE_WINDOWS_PATHS:
            if path.exists():
                return path

    return None


def _check_weasyprint_available() -> bool:
    """Check if WeasyPrint is available."""
    try:
        import weasyprint  # noqa: F401
        return True
    except ImportError:
        return False


def _check_pymupdf_available() -> bool:
    """Check if PyMuPDF is available."""
    try:
        import fitz  # noqa: F401
        return True
    except ImportError:
        return False


def _check_pandoc_available() -> bool:
    """Check if Pandoc is available in PATH."""
    return shutil.which("pandoc") is not None


def _check_calibre_available() -> bool:
    """Check if Calibre's ebook-convert is available."""
    return _find_calibre_executable() is not None


def _get_epub_spine_items(epub_path: Path) -> list[tuple[str, Path]]:
    """
    Extract the reading order (spine) from an EPUB file.

    Returns list of (item_id, relative_path) tuples in reading order.
    """
    with zipfile.ZipFile(epub_path, 'r') as zf:
        # Read container.xml to find OPF file
        container = ET.fromstring(zf.read('META-INF/container.xml'))
        rootfile = container.find('.//container:rootfile', NAMESPACES)
        if rootfile is None:
            raise ConversionError("Cannot find rootfile in container.xml")

        opf_path = rootfile.get('full-path')
        opf_dir = str(Path(opf_path).parent)
        if opf_dir == '.':
            opf_dir = ''

        # Parse OPF file
        opf = ET.fromstring(zf.read(opf_path))

        # Build manifest dict (id -> href)
        manifest = {}
        for item in opf.findall('.//opf:manifest/opf:item', NAMESPACES):
            item_id = item.get('id')
            href = item.get('href')
            media_type = item.get('media-type', '')
            if media_type in ('application/xhtml+xml', 'text/html'):
                if opf_dir:
                    manifest[item_id] = f"{opf_dir}/{href}"
                else:
                    manifest[item_id] = href

        # Get spine order
        spine_items = []
        for itemref in opf.findall('.//opf:spine/opf:itemref', NAMESPACES):
            idref = itemref.get('idref')
            if idref in manifest:
                spine_items.append((idref, manifest[idref]))

        return spine_items


def _convert_with_weasyprint(
    epub_path: Path,
    pdf_path: Path,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Path:
    """
    Convert EPUB to PDF using WeasyPrint.

    WeasyPrint is a pure Python solution that renders HTML/CSS to PDF
    with excellent CSS support and no external dependencies.
    """
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
    except ImportError:
        raise ConversionError(
            "WeasyPrint is not installed. Install with: uv pip install weasyprint"
        )

    if progress_callback:
        progress_callback("Extracting EPUB content...")

    try:
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Extract EPUB
            with zipfile.ZipFile(epub_path, 'r') as zf:
                zf.extractall(temp_path)

            # Get spine items (reading order)
            spine_items = _get_epub_spine_items(epub_path)

            if not spine_items:
                raise ConversionError("No content found in EPUB spine")

            if progress_callback:
                progress_callback(f"Converting {len(spine_items)} chapters...")

            font_config = FontConfiguration()

            # Base CSS for better PDF rendering
            base_css = CSS(string='''
                @page {
                    size: A4;
                    margin: 1in;
                }
                body {
                    font-family: serif;
                    font-size: 11pt;
                    line-height: 1.5;
                }
                img {
                    max-width: 100%;
                    height: auto;
                }
            ''', font_config=font_config)

            # Convert each chapter and collect documents
            documents = []
            for i, (item_id, href) in enumerate(spine_items):
                html_path = temp_path / unquote(href)

                if not html_path.exists():
                    continue

                if progress_callback:
                    progress_callback(f"Processing chapter {i+1}/{len(spine_items)}...")

                try:
                    doc = HTML(filename=str(html_path), base_url=str(html_path.parent))
                    documents.append(doc.render(stylesheets=[base_css], font_config=font_config))
                except Exception as e:
                    # Skip problematic chapters but continue
                    if progress_callback:
                        progress_callback(f"Warning: Skipped chapter {i+1}: {e}")
                    continue

            if not documents:
                raise ConversionError("No chapters could be converted")

            if progress_callback:
                progress_callback("Merging chapters into PDF...")

            # Merge all documents
            all_pages = []
            for doc in documents:
                all_pages.extend(doc.pages)

            # Use the first document's metadata and write all pages
            if documents:
                documents[0].copy(all_pages).write_pdf(str(pdf_path))

            if not pdf_path.exists() or pdf_path.stat().st_size == 0:
                raise ConversionError("WeasyPrint produced empty output")

            if progress_callback:
                progress_callback("Conversion complete!")

            return pdf_path

    except ConversionError:
        raise
    except Exception as e:
        if pdf_path.exists():
            pdf_path.unlink()
        raise ConversionError(f"WeasyPrint conversion failed: {e}")


def _convert_with_pymupdf(
    epub_path: Path,
    pdf_path: Path,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Path:
    """
    Convert EPUB to PDF using PyMuPDF.

    Note: PyMuPDF may fail on EPUBs with complex CSS (e.g., EPUB3-specific selectors).
    """
    try:
        import fitz
    except ImportError:
        raise ConversionError("PyMuPDF is not installed. Install with: uv pip install pymupdf")

    if progress_callback:
        progress_callback("Opening EPUB file with PyMuPDF...")

    try:
        doc = fitz.open(epub_path)

        if progress_callback:
            progress_callback(f"Converting {doc.page_count} pages...")

        doc.save(str(pdf_path))
        doc.close()

        # Verify output was created and has content
        if not pdf_path.exists() or pdf_path.stat().st_size == 0:
            raise ConversionError("PyMuPDF produced empty or no output")

        if progress_callback:
            progress_callback("Conversion complete!")

        return pdf_path

    except Exception as e:
        # Clean up partial output
        if pdf_path.exists():
            pdf_path.unlink()
        error_msg = str(e)
        if "css syntax error" in error_msg.lower() or "syntax error" in error_msg.lower():
            raise ConversionError(
                "PyMuPDF failed due to CSS parsing errors in the EPUB. "
                "This is common with EPUB3 files."
            )
        raise ConversionError(f"PyMuPDF conversion failed: {e}")


def _convert_with_pandoc(
    epub_path: Path,
    pdf_path: Path,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Path:
    """
    Convert EPUB to PDF using Pandoc.

    Requires a PDF engine (pdflatex, xelatex, or weasyprint).
    """
    if not _check_pandoc_available():
        raise ConversionError("Pandoc is not installed or not in PATH")

    if progress_callback:
        progress_callback("Converting with Pandoc...")

    # Try different PDF engines in order of preference
    engines = ["xelatex", "pdflatex", "weasyprint", None]

    for engine in engines:
        try:
            cmd = [
                "pandoc",
                str(epub_path),
                "-o", str(pdf_path),
            ]

            if engine:
                cmd.extend(["--pdf-engine", engine])

            cmd.extend(["-V", "geometry:margin=1in", "-V", "papersize=a4"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8"
            )

            if result.returncode == 0 and pdf_path.exists() and pdf_path.stat().st_size > 0:
                if progress_callback:
                    progress_callback("Conversion complete!")
                return pdf_path

        except Exception:
            continue

    raise ConversionError(
        "Pandoc conversion failed. No working PDF engine found. "
        "Install one of: xelatex, pdflatex, or weasyprint"
    )


def _convert_with_calibre(
    epub_path: Path,
    pdf_path: Path,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Path:
    """
    Convert EPUB to PDF using Calibre's ebook-convert.

    Uses 'tablet' output profile to prevent image downscaling.
    """
    calibre_exe = _find_calibre_executable()
    if not calibre_exe:
        raise ConversionError(
            "Calibre's ebook-convert is not installed. "
            "Install Calibre from: https://calibre-ebook.com/download"
        )

    if progress_callback:
        progress_callback("Running Calibre ebook-convert...")

    try:
        result = subprocess.run(
            [
                str(calibre_exe),
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

    if _check_weasyprint_available():
        available.append(ConversionMethod.WEASYPRINT)

    if _check_pymupdf_available():
        available.append(ConversionMethod.PYMUPDF)

    if _check_pandoc_available():
        available.append(ConversionMethod.PANDOC)

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
                order of preference: WeasyPrint > PyMuPDF > Pandoc > Calibre
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

        # 1. Try WeasyPrint first (best compatibility, pure Python)
        if _check_weasyprint_available():
            try:
                if progress_callback:
                    progress_callback("Trying WeasyPrint...")
                return _convert_with_weasyprint(epub_path, pdf_path, progress_callback)
            except ConversionError as e:
                errors.append(f"WeasyPrint: {e}")
                if progress_callback:
                    progress_callback("WeasyPrint failed, trying PyMuPDF...")

        # 2. Try PyMuPDF (fast but CSS issues)
        if _check_pymupdf_available():
            try:
                if progress_callback:
                    progress_callback("Trying PyMuPDF...")
                return _convert_with_pymupdf(epub_path, pdf_path, progress_callback)
            except ConversionError as e:
                errors.append(f"PyMuPDF: {e}")
                if progress_callback:
                    progress_callback("PyMuPDF failed, trying Pandoc...")

        # 3. Try Pandoc
        if _check_pandoc_available():
            try:
                if progress_callback:
                    progress_callback("Trying Pandoc...")
                return _convert_with_pandoc(epub_path, pdf_path, progress_callback)
            except ConversionError as e:
                errors.append(f"Pandoc: {e}")
                if progress_callback:
                    progress_callback("Pandoc failed, trying Calibre...")

        # 4. Try Calibre
        if _check_calibre_available():
            try:
                if progress_callback:
                    progress_callback("Trying Calibre...")
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
                "- WeasyPrint: uv pip install weasyprint\n"
                "- PyMuPDF: uv pip install pymupdf\n"
                "- Pandoc: https://pandoc.org/installing.html\n"
                "- Calibre: https://calibre-ebook.com/download"
            )

    elif method == ConversionMethod.WEASYPRINT:
        return _convert_with_weasyprint(epub_path, pdf_path, progress_callback)

    elif method == ConversionMethod.PYMUPDF:
        return _convert_with_pymupdf(epub_path, pdf_path, progress_callback)

    elif method == ConversionMethod.PANDOC:
        return _convert_with_pandoc(epub_path, pdf_path, progress_callback)

    elif method == ConversionMethod.CALIBRE:
        return _convert_with_calibre(epub_path, pdf_path, progress_callback)

    else:
        raise ValueError(f"Unknown conversion method: {method}")
