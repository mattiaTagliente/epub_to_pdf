# -*- coding: utf-8 -*-
"""
EPUB to PDF conversion module.

Provides high-fidelity EPUB to PDF conversion optimized for OCR processing.
Primary backend: Prince XML (excellent typography and CSS support).
Fallback: Vivliostyle CLI (Node.js based, good quality).
"""

import os
import subprocess
import shutil
import sys
import logging
import tempfile
import zipfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

# Setup logging
LOG_DIR = Path.home() / ".epub_to_pdf" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"conversion_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
    ]
)
logger = logging.getLogger(__name__)


class ConversionMethod(Enum):
    """Available conversion methods."""
    PRINCE = "prince"
    VIVLIOSTYLE = "vivliostyle"
    AUTO = "auto"


class ConversionError(Exception):
    """Raised when EPUB to PDF conversion fails."""
    pass


# Common Prince installation paths on Windows
PRINCE_WINDOWS_PATHS = [
    Path("C:/Program Files/Prince/engine/bin/prince.exe"),
    Path("C:/Program Files (x86)/Prince/engine/bin/prince.exe"),
]

# Common xq installation paths
XQ_PATHS = [
    Path.home() / "bin" / "xq.exe",
    Path("C:/Users/matti/bin/xq.exe"),
]

# CSS for PDF bookmarks from EPUB table of contents
NAV_CSS = '''@namespace epub url("http://www.idpf.org/2007/ops");

/* Don't use Prince's inferred bookmark levels, because we have nav information */
h1 { prince-bookmark-level: none; }
h2 { prince-bookmark-level: none; }
h3 { prince-bookmark-level: none; }
h4 { prince-bookmark-level: none; }
h5 { prince-bookmark-level: none; }
h6 { prince-bookmark-level: none; }

nav[epub|type="landmarks"],
nav[epub|type="page-list"] {
  display: none;
}

nav[epub|type="toc"] {
  max-height: 0;
  overflow: hidden;
}

/* Convert structure of nav toc to bookmarks. */
nav[epub|type="toc"] a {
  prince-bookmark-target: attr(href);
}

nav[epub|type="toc"]
  :is([epub|type="list"], ol, ul)
  a {
  prince-bookmark-level: 1;
}
nav[epub|type="toc"]
  :is([epub|type="list"], ol, ul)
  :is([epub|type="list"], ol, ul)
  a {
  prince-bookmark-level: 2;
}
nav[epub|type="toc"]
  :is([epub|type="list"], ol, ul)
  :is([epub|type="list"], ol, ul)
  :is([epub|type="list"], ol, ul)
  a {
  prince-bookmark-level: 3;
}
nav[epub|type="toc"]
  :is([epub|type="list"], ol, ul)
  :is([epub|type="list"], ol, ul)
  :is([epub|type="list"], ol, ul)
  :is([epub|type="list"], ol, ul)
  a {
  prince-bookmark-level: 4;
}
'''

# Theme CSS for PDF page layout
THEME_CSS = '''@namespace epub url("http://www.idpf.org/2007/ops");

@page {
  size: A4;
  margin: 48pt;
}

body {
  font-size: 12pt;
}

html {
  -prince-hyphenate-character: '\\0000AD';
}

p {
  hyphens: auto;
}
'''


def get_log_file_path() -> Path:
    """Return the path to the current log file."""
    return LOG_FILE


def _find_prince_executable() -> Optional[Path]:
    """Find Prince XML executable."""
    # Check PATH first
    in_path = shutil.which("prince")
    if in_path:
        return Path(in_path)

    in_path = shutil.which("prince-books")
    if in_path:
        return Path(in_path)

    # Check common Windows paths
    if sys.platform == "win32":
        for path in PRINCE_WINDOWS_PATHS:
            if path.exists():
                return path

    return None


def _find_xq_executable() -> Optional[Path]:
    """Find xq (XML query) executable."""
    in_path = shutil.which("xq")
    if in_path:
        return Path(in_path)

    # Check common paths
    for path in XQ_PATHS:
        if path.exists():
            return path

    return None


def _find_vivliostyle_executable() -> Optional[str]:
    """Find Vivliostyle CLI executable."""
    # On Windows, need to look for .cmd file
    if sys.platform == "win32":
        cmd_path = shutil.which("vivliostyle.cmd")
        if cmd_path:
            return cmd_path
    return shutil.which("vivliostyle")


def _check_prince_available() -> bool:
    """Check if Prince XML is available."""
    return _find_prince_executable() is not None and _find_xq_executable() is not None


def _check_vivliostyle_available() -> bool:
    """Check if Vivliostyle CLI is available."""
    return _find_vivliostyle_executable() is not None


def _run_xq(xq_exe: Path, xml_file: Path, xpath: str) -> str:
    """Run xq to extract data from XML file using XPath."""
    cmd = [str(xq_exe), str(xml_file), "-x", xpath]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return result.stdout.strip()


def _convert_with_prince(
    epub_path: Path,
    pdf_path: Path,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Path:
    """
    Convert EPUB to PDF using Prince XML.

    This method unpacks the EPUB, parses its structure using xq,
    and uses Prince for high-quality PDF generation with proper
    typography, hyphenation, and CSS support.
    """
    prince_exe = _find_prince_executable()
    xq_exe = _find_xq_executable()

    if not prince_exe:
        raise ConversionError(
            "Prince XML is not installed. "
            "Install from: https://www.princexml.com/"
        )

    if not xq_exe:
        raise ConversionError(
            "xq (XML query tool) is not installed. "
            "Install from: https://github.com/sibprogrammer/xq/releases"
        )

    logger.info(f"Starting Prince conversion: {epub_path} -> {pdf_path}")
    logger.info(f"Prince executable: {prince_exe}")
    logger.info(f"xq executable: {xq_exe}")

    if progress_callback:
        progress_callback("Analyzing EPUB structure...")

    try:
        # Create temp directory for unpacking
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Verify it's a valid EPUB
            try:
                with zipfile.ZipFile(epub_path, 'r') as zf:
                    try:
                        mimetype = zf.read('mimetype').decode('utf-8').strip()
                        if mimetype != 'application/epub+zip':
                            raise ConversionError(f"Invalid EPUB mimetype: {mimetype}")
                    except KeyError:
                        logger.warning("EPUB missing mimetype file, continuing anyway")

                    # Extract all files
                    zf.extractall(tmpdir)
            except zipfile.BadZipFile:
                raise ConversionError("Input file is not a valid ZIP/EPUB file")

            if progress_callback:
                progress_callback("Parsing EPUB metadata...")

            # Find container.xml
            container_xml = tmpdir / "META-INF" / "container.xml"
            if not container_xml.exists():
                raise ConversionError("EPUB missing container.xml - not a valid EPUB3 file")

            # Get path to package.opf
            package_opf_path = _run_xq(xq_exe, container_xml, "//rootfile/@full-path")
            if not package_opf_path:
                raise ConversionError("Could not find OPF package path in container.xml")

            package_opf = tmpdir / package_opf_path
            if not package_opf.exists():
                raise ConversionError(f"OPF package file not found: {package_opf_path}")

            package_dir = package_opf.parent
            logger.info(f"Package directory: {package_dir}")

            # Create CSS files in temp directory
            css_dir = tmpdir / ".prince_css"
            css_dir.mkdir(exist_ok=True)

            nav_css_file = css_dir / "nav.css"
            nav_css_file.write_text(NAV_CSS, encoding="utf-8")

            theme_css_file = css_dir / "theme.css"
            theme_css_file.write_text(THEME_CSS, encoding="utf-8")

            # Build Prince arguments
            prince_args = [
                str(prince_exe),
                "--style", str(nav_css_file),
                "--style", str(theme_css_file),
            ]

            # Get spine items (content files in reading order)
            spine_idrefs = _run_xq(xq_exe, package_opf, "//spine/itemref/@idref")
            spine_items = []

            if spine_idrefs:
                for idref in spine_idrefs.strip().split('\n'):
                    idref = idref.strip()
                    if idref:
                        # Look up the href for this id in the manifest
                        href = _run_xq(xq_exe, package_opf, f'//manifest/item[@id="{idref}"]/@href')
                        if href:
                            spine_items.append(href.strip())

            logger.info(f"Found {len(spine_items)} spine items")

            if not spine_items:
                raise ConversionError("No spine items found in EPUB - cannot determine content order")

            # Add spine items to Prince args
            for item in spine_items:
                item_path = package_dir / item
                if item_path.exists():
                    prince_args.append(str(item_path))
                else:
                    logger.warning(f"Spine item not found: {item}")

            # Find nav.html (table of contents)
            # XPath to find item with properties containing "nav"
            nav_href = _run_xq(
                xq_exe, package_opf,
                '//manifest/item[contains(concat(" ", normalize-space(@properties), " "), " nav ")]/@href'
            )

            if nav_href:
                nav_html = package_dir / nav_href.strip()
                if nav_html.exists():
                    prince_args.append(str(nav_html))
                    logger.info(f"Found nav.html: {nav_href}")
                else:
                    logger.warning(f"Nav file not found: {nav_href}")
            else:
                logger.warning("No nav.html found - PDF will have no bookmarks")

            # Extract title and author for PDF metadata
            title = _run_xq(xq_exe, package_opf, "//metadata/dc:title")
            if title:
                prince_args.extend(["--pdf-title", title.strip()])
                logger.info(f"Title: {title}")

            author = _run_xq(xq_exe, package_opf, "//metadata/dc:creator")
            if author:
                prince_args.extend(["--pdf-author", author.strip()])
                logger.info(f"Author: {author}")

            # Add output path
            prince_args.extend(["--output", str(pdf_path)])

            if progress_callback:
                progress_callback("Generating PDF with Prince (this may take a while)...")

            logger.info(f"Running Prince with {len(spine_items)} content files")
            logger.debug(f"Prince command: {' '.join(prince_args)}")

            # Run Prince from the package directory
            result = subprocess.run(
                prince_args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                cwd=str(package_dir),
                timeout=900  # 15 minute timeout
            )

            # Log output
            if result.stdout:
                logger.info(f"Prince stdout:\n{result.stdout}")
            if result.stderr:
                # Prince logs to stderr even on success
                logger.info(f"Prince stderr:\n{result.stderr}")

            logger.info(f"Prince return code: {result.returncode}")

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.error(f"Prince conversion failed: {error_msg}")
                raise ConversionError(f"Prince conversion failed: {error_msg}")

            if not pdf_path.exists() or pdf_path.stat().st_size == 0:
                logger.error("Prince produced empty or no output")
                raise ConversionError("Prince produced empty or no output")

            logger.info(f"Conversion successful! Output: {pdf_path} ({pdf_path.stat().st_size} bytes)")

            if progress_callback:
                progress_callback("Conversion complete!")

            return pdf_path

    except subprocess.TimeoutExpired:
        logger.error("Prince conversion timed out (>15 minutes)")
        raise ConversionError("Prince conversion timed out (>15 minutes)")
    except ConversionError:
        raise
    except Exception as e:
        logger.exception(f"Prince conversion failed with exception: {e}")
        raise ConversionError(f"Prince conversion failed: {e}")


def _convert_with_vivliostyle(
    epub_path: Path,
    pdf_path: Path,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Path:
    """
    Convert EPUB to PDF using Vivliostyle CLI.

    Vivliostyle uses Chromium for rendering, providing excellent
    CSS support and high-fidelity output suitable for OCR processing.
    """
    vivliostyle_exe = _find_vivliostyle_executable()
    if not vivliostyle_exe:
        raise ConversionError(
            "Vivliostyle CLI is not installed. Install with: npm install -g @vivliostyle/cli"
        )

    logger.info(f"Starting Vivliostyle conversion: {epub_path} -> {pdf_path}")
    logger.info(f"Vivliostyle executable: {vivliostyle_exe}")

    if progress_callback:
        progress_callback("Converting with Vivliostyle CLI...")

    try:
        # Set CI=true to avoid TTY detection issues on Windows
        env = os.environ.copy()
        env["CI"] = "true"

        # On Windows, build command string for shell execution
        if sys.platform == "win32":
            # Quote paths with spaces properly for cmd.exe
            # Use output file for logs to avoid stdout capture interfering with puppeteer
            log_output_file = pdf_path.parent / f".vivliostyle_log_{pdf_path.stem}.txt"
            cmd_str = f'"{vivliostyle_exe}" build "{epub_path}" -o "{pdf_path}" --size A4 --timeout 900 --log-level verbose > "{log_output_file}" 2>&1'
            logger.info(f"Running command: {cmd_str}")

            result = subprocess.run(
                cmd_str,
                timeout=900,  # 15 minute timeout for large EPUBs
                shell=True,
                env=env
            )

            # Read the log file
            stdout_content = ""
            if log_output_file.exists():
                stdout_content = log_output_file.read_text(encoding="utf-8", errors="replace")
                log_output_file.unlink()  # Clean up

            # Create a mock result with stdout
            class MockResult:
                def __init__(self, returncode, stdout):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = ""

            result = MockResult(result.returncode, stdout_content)
        else:
            cmd = [
                vivliostyle_exe, "build",
                str(epub_path),
                "-o", str(pdf_path),
                "--size", "A4",
                "--timeout", "900",
                "--log-level", "verbose",
            ]
            logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=900,  # 15 minute timeout for large EPUBs
                env=env
            )

        # Log all output
        if result.stdout:
            logger.info(f"Vivliostyle stdout:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"Vivliostyle stderr:\n{result.stderr}")

        logger.info(f"Vivliostyle return code: {result.returncode}")

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            logger.error(f"Vivliostyle conversion failed: {error_msg}")
            raise ConversionError(f"Vivliostyle conversion failed: {error_msg}")

        if not pdf_path.exists() or pdf_path.stat().st_size == 0:
            logger.error("Vivliostyle produced empty or no output")
            raise ConversionError("Vivliostyle produced empty or no output")

        logger.info(f"Conversion successful! Output: {pdf_path} ({pdf_path.stat().st_size} bytes)")

        if progress_callback:
            progress_callback("Conversion complete!")

        return pdf_path

    except subprocess.TimeoutExpired:
        logger.error("Vivliostyle conversion timed out (>15 minutes)")
        raise ConversionError("Vivliostyle conversion timed out (>15 minutes)")
    except ConversionError:
        raise
    except Exception as e:
        logger.exception(f"Vivliostyle conversion failed with exception: {e}")
        raise ConversionError(f"Vivliostyle conversion failed: {e}")


def get_available_methods() -> list[ConversionMethod]:
    """
    Get list of available conversion methods on this system.

    Returns:
        List of available ConversionMethod values
    """
    available = []

    if _check_prince_available():
        available.append(ConversionMethod.PRINCE)
        logger.debug("Prince is available")

    if _check_vivliostyle_available():
        available.append(ConversionMethod.VIVLIOSTYLE)
        logger.debug("Vivliostyle is available")

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
        method: Conversion method to use. AUTO will try Prince first,
                then Vivliostyle as fallback.
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

    logger.info(f"=== Starting conversion ===")
    logger.info(f"Input: {epub_path}")
    logger.info(f"Method: {method.value}")

    if not epub_path.exists():
        logger.error(f"EPUB file not found: {epub_path}")
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")

    if not epub_path.suffix.lower() == ".epub":
        logger.error(f"File is not an EPUB: {epub_path}")
        raise ValueError(f"File is not an EPUB: {epub_path}")

    # Determine output path
    if pdf_path is None:
        pdf_path = epub_path.with_suffix(".pdf")
    else:
        pdf_path = Path(pdf_path)

    logger.info(f"Output: {pdf_path}")

    # Ensure output directory exists
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    if method == ConversionMethod.AUTO:
        errors = []

        # 1. Try Prince first (best typography)
        if _check_prince_available():
            try:
                if progress_callback:
                    progress_callback("Using Prince XML...")
                return _convert_with_prince(epub_path, pdf_path, progress_callback)
            except ConversionError as e:
                errors.append(f"Prince: {e}")
                logger.warning(f"Prince failed, trying next method...")
                if progress_callback:
                    progress_callback("Prince failed, trying Vivliostyle...")

        # 2. Try Vivliostyle as fallback
        if _check_vivliostyle_available():
            try:
                if progress_callback:
                    progress_callback("Using Vivliostyle CLI...")
                return _convert_with_vivliostyle(epub_path, pdf_path, progress_callback)
            except ConversionError as e:
                errors.append(f"Vivliostyle: {e}")

        if errors:
            error_msg = "All conversion methods failed:\n" + "\n".join(errors)
            logger.error(error_msg)
            raise ConversionError(error_msg)
        else:
            error_msg = (
                "No conversion tools available. Please install:\n"
                "- Prince XML: https://www.princexml.com/\n"
                "- Or Vivliostyle CLI: npm install -g @vivliostyle/cli"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

    elif method == ConversionMethod.PRINCE:
        return _convert_with_prince(epub_path, pdf_path, progress_callback)

    elif method == ConversionMethod.VIVLIOSTYLE:
        return _convert_with_vivliostyle(epub_path, pdf_path, progress_callback)

    else:
        raise ValueError(f"Unknown conversion method: {method}")
