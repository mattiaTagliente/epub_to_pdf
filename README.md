# EPUB to PDF Converter

A graphical utility for converting EPUB files to high-fidelity PDF format, specifically optimized for subsequent Mistral OCR processing to obtain the best markdown conversion with images.

## Features

- **Drag & Drop Interface**: Simply drag and drop EPUB files onto the application window
- **High-Fidelity Output**: Optimized for OCR processing with preserved image quality
- **Multiple Conversion Backends**:
  - **PyMuPDF** (Primary): Sub-pixel accurate rendering, fastest option
  - **mutool**: MuPDF command-line tool for maximum control
  - **Calibre**: ebook-convert with extensive configuration options
- **Automatic Fallback**: Automatically uses the best available conversion method
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Why This Tool?

When converting EPUBs to PDFs for OCR processing (especially for extracting mathematical equations as LaTeX), the conversion quality is critical. This tool prioritizes:

1. **Image Quality Preservation**: Equations stored as images remain crisp and high-resolution
2. **Layout Fidelity**: Spatial relationships in mathematical content are preserved
3. **No Rasterization Degradation**: Images are not recompressed or downscaled

The resulting PDFs are optimized for use with Mistral OCR to obtain accurate markdown conversion with proper image extraction.

## Installation

### Prerequisites

Ensure you have Python 3.11 or later installed.

### Install with uv (Recommended)

```bash
# Create virtual environment
uv venv C:\Users\matti\venvs\epub_to_pdf

# Activate virtual environment (Windows)
C:\Users\matti\venvs\epub_to_pdf\Scripts\activate

# Install the package
uv pip install -e .
```

### Install with pip

```bash
# Create virtual environment
python -m venv C:\Users\matti\venvs\epub_to_pdf

# Activate virtual environment (Windows)
C:\Users\matti\venvs\epub_to_pdf\Scripts\activate

# Install the package
pip install -e .
```

### Optional: Install Additional Conversion Backends

While PyMuPDF is the recommended and default backend (installed automatically), you can also install these optional backends:

#### MuPDF (mutool)

Windows (via Chocolatey):
```bash
choco install mupdf
```

Or download from: https://mupdf.com/releases/

#### Calibre (ebook-convert)

Windows (via Chocolatey):
```bash
choco install calibre
```

Or download from: https://calibre-ebook.com/download

## Usage

### GUI Application

Run the graphical interface:

```bash
# Using the installed command
epub-to-pdf

# Or run as a Python module
python -m epub_to_pdf
```

1. **Drag & Drop**: Drag an EPUB file onto the drop zone
2. **Or Browse**: Click the drop zone to open a file browser
3. **Select Method**: Choose a conversion method (Auto is recommended)
4. **Convert**: Click "Convert to PDF" and choose the output location

### Programmatic Usage

Use the converter in your Python code:

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
    method=ConversionMethod.PYMUPDF
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

| Method | Quality | Speed | Notes |
|--------|---------|-------|-------|
| PyMuPDF | Excellent | Fast | Recommended. Sub-pixel accuracy |
| mutool | Excellent | Fast | CLI tool, requires MuPDF installation |
| Calibre | Very Good | Medium | Most configurable, requires Calibre |

The **Auto** mode tries methods in order of preference: PyMuPDF → mutool → Calibre

## Workflow Integration

This tool is designed to fit into a pipeline for processing technical documents:

```
EPUB → [epub-to-pdf] → PDF → [Mistral OCR] → Markdown + Images
```

The high-fidelity PDF output ensures that:
- Mathematical equations (stored as images) are preserved at full quality
- Layout information aids OCR accuracy
- Images can be extracted cleanly for the markdown output

## Project Structure

```
epub_to_pdf/
├── src/
│   └── epub_to_pdf/
│       ├── __init__.py      # Package initialization
│       ├── __main__.py      # Module entry point
│       ├── app.py           # GUI application
│       └── converter.py     # Conversion logic
├── pyproject.toml           # Project configuration
├── README.md                # This file
└── idea.txt                 # Original requirements/analysis
```

## Requirements

- Python >= 3.11
- PyMuPDF >= 1.24.0
- tkinterdnd2 >= 0.3.0 (for drag-and-drop support)

## License

MIT License

## Author

Mattia Tagliente ([@mattiaTagliente](https://github.com/mattiaTagliente))

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
