# EPUB to PDF Converter

A graphical utility for converting EPUB files to high-fidelity PDF format, specifically optimized for subsequent Mistral OCR processing to obtain the best markdown conversion with images.

## Features

- **Drag & Drop Interface**: Simply drag and drop EPUB files onto the application window
- **High-Fidelity Output**: Optimized for OCR processing with preserved image quality
- **Multiple Conversion Backends**:
  - **WeasyPrint** (Recommended): Pure Python, excellent CSS support, no external dependencies
  - **PyMuPDF**: Fast, sub-pixel accurate rendering (may have CSS issues with EPUB3)
  - **Pandoc**: Document conversion expert (requires PDF engine)
  - **Calibre**: ebook-convert with extensive configuration options
- **Automatic Fallback**: Automatically tries conversion methods in order until one succeeds
- **Desktop Shortcut**: Quick launch from Windows desktop

## Quick Start

After installation, simply **double-click the desktop shortcut** "EPUB to PDF Converter" to launch the application.

## Installation

### Prerequisites

- Python 3.11 or later
- Windows 11 (tested), should work on other platforms

### Install with uv (Recommended)

```bash
# Create virtual environment
uv venv C:\Users\matti\venvs\epub_to_pdf

# Activate virtual environment (Windows)
C:\Users\matti\venvs\epub_to_pdf\Scripts\activate

# Install the package
cd C:\Users\matti\OneDrivePhD\Dev\epub_to_pdf
uv pip install -e .

# Install WeasyPrint for best compatibility
uv pip install weasyprint
```

### Create Desktop Shortcut

Run this PowerShell command to create a desktop shortcut:

```powershell
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\EPUB to PDF Converter.lnk')
$Shortcut.TargetPath = 'C:\Users\matti\OneDrivePhD\Dev\epub_to_pdf\launch_epub_to_pdf.vbs'
$Shortcut.WorkingDirectory = 'C:\Users\matti\OneDrivePhD\Dev\epub_to_pdf'
$Shortcut.Description = 'Convert EPUB files to PDF'
$Shortcut.Save()
```

## Usage

### GUI Application

1. **Double-click** the desktop shortcut, or run:
   ```bash
   python -m epub_to_pdf
   ```

2. **Drag & Drop**: Drag an EPUB file onto the drop zone
3. **Or Browse**: Click the drop zone to open a file browser
4. **Select Method**: Choose a conversion method (Auto is recommended)
5. **Convert**: Click "Convert to PDF" and choose the output location

### Programmatic Usage

```python
from pathlib import Path
from epub_to_pdf import convert_epub_to_pdf, ConversionMethod

# Basic usage (auto-selects best available method)
pdf_path = convert_epub_to_pdf("book.epub")

# Specify output path
pdf_path = convert_epub_to_pdf(
    "book.epub",
    "output/book.pdf"
)

# Use specific conversion method
pdf_path = convert_epub_to_pdf(
    "book.epub",
    method=ConversionMethod.WEASYPRINT
)

# With progress callback
def on_progress(message: str):
    print(f"Progress: {message}")

pdf_path = convert_epub_to_pdf(
    "book.epub",
    progress_callback=on_progress
)
```

## Conversion Methods

| Method | Quality | Speed | CSS Support | Notes |
|--------|---------|-------|-------------|-------|
| WeasyPrint | Excellent | Medium | Excellent | Recommended. Pure Python, best compatibility |
| PyMuPDF | Excellent | Fast | Limited | May fail on EPUB3 with complex CSS |
| Pandoc | Good | Medium | Good | Requires PDF engine (xelatex/pdflatex) |
| Calibre | Very Good | Medium | Good | Requires Calibre installation |

The **Auto** mode tries methods in order: WeasyPrint > PyMuPDF > Pandoc > Calibre

## Why This Tool?

When converting EPUBs to PDFs for OCR processing (especially for extracting mathematical equations as LaTeX), the conversion quality is critical. This tool prioritizes:

1. **Image Quality Preservation**: Equations stored as images remain crisp and high-resolution
2. **Layout Fidelity**: Spatial relationships in mathematical content are preserved
3. **CSS Compatibility**: WeasyPrint handles complex CSS that other tools struggle with

The resulting PDFs are optimized for use with Mistral OCR to obtain accurate markdown conversion with proper image extraction.

## Workflow Integration

This tool is designed to fit into a pipeline for processing technical documents:

```
EPUB -> [epub-to-pdf] -> PDF -> [Mistral OCR] -> Markdown + Images
```

## Project Structure

```
epub_to_pdf/
├── src/
│   └── epub_to_pdf/
│       ├── __init__.py      # Package initialization
│       ├── __main__.py      # Module entry point
│       ├── app.py           # GUI application
│       └── converter.py     # Conversion logic
├── launch_epub_to_pdf.vbs   # Silent launcher (no console window)
├── launch_epub_to_pdf.bat   # Batch launcher
├── pyproject.toml           # Project configuration
├── README.md                # This file
└── idea.txt                 # Original requirements/analysis
```

## Requirements

- Python >= 3.11
- weasyprint >= 67.0 (recommended)
- pymupdf >= 1.24.0
- tkinterdnd2 >= 0.3.0 (for drag-and-drop support)

## Troubleshooting

### PyMuPDF CSS Errors
If you see errors like "css syntax error: unexpected token", this means the EPUB uses CSS features that PyMuPDF doesn't support. The Auto mode will automatically fall back to WeasyPrint.

### Pandoc Requires PDF Engine
Pandoc needs a PDF engine (xelatex, pdflatex, or weasyprint) installed. If you don't have LaTeX installed, WeasyPrint is used as Pandoc's PDF engine.

## License

MIT License

## Author

Mattia Tagliente ([@mattiaTagliente](https://github.com/mattiaTagliente))
