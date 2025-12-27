# EPUB to PDF Converter

A graphical utility for converting EPUB files to high-fidelity PDF format, specifically optimized for subsequent Mistral OCR processing to obtain the best markdown conversion with images.

## Features

- **Drag & Drop Interface**: Simply drag and drop EPUB files onto the application window
- **High-Fidelity Output**: Optimized for OCR processing with preserved image quality
- **Multiple Conversion Backends**:
  - **Prince** (Recommended): Professional PDF generator with excellent typography, hyphenation, and PDF bookmark support
  - **Vivliostyle CLI** (Fallback): Node.js-based, uses Chromium for excellent CSS support and high-fidelity rendering
- **Automatic Fallback**: Automatically tries conversion methods in order until one succeeds
- **Desktop Shortcut**: Quick launch from Windows desktop
- **Integrated Log Viewer**: Real-time conversion log display in the GUI
- **Log File**: Conversion logs are saved to `~/.epub_to_pdf/logs/`

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
```

### Install Prince (Required)

Download and install Prince from [https://www.princexml.com/download/](https://www.princexml.com/download/).

Prince is a professional PDF generator with excellent typography and hyphenation support.

### Install xq (Required for Prince)

xq is used for parsing EPUB metadata. Download from [https://github.com/sibprogrammer/xq/releases](https://github.com/sibprogrammer/xq/releases) and place in your PATH (e.g., `C:\Users\<username>\bin\xq.exe`).

### Install Vivliostyle CLI (Optional Fallback)

Vivliostyle CLI is used as a fallback if Prince is not available. It requires Node.js:

```bash
npm install -g @vivliostyle/cli
```

Verify installation:
```bash
vivliostyle --version
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
    method=ConversionMethod.PRINCE
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

| Method | Quality | Speed | Typography | Notes |
|--------|---------|-------|------------|-------|
| Prince | Excellent | Fast | Excellent | Recommended. Professional PDF generator with hyphenation and PDF bookmarks |
| Vivliostyle | Excellent | Medium | Good | Fallback. Uses Chromium for high-fidelity rendering |

The **Auto** mode tries methods in order: Prince > Vivliostyle

## Why This Tool?

When converting EPUBs to PDFs for OCR processing (especially for extracting mathematical equations as LaTeX), the conversion quality is critical. This tool prioritizes:

1. **Image Quality Preservation**: Equations stored as images remain crisp and high-resolution
2. **Layout Fidelity**: Spatial relationships in mathematical content are preserved
3. **Typography Excellence**: Prince provides professional typography with hyphenation and proper PDF bookmarks
4. **CSS Compatibility**: Both backends provide excellent CSS support for accurate rendering

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
- Prince: [https://www.princexml.com/download/](https://www.princexml.com/download/)
- xq: [https://github.com/sibprogrammer/xq/releases](https://github.com/sibprogrammer/xq/releases)
- Node.js and Vivliostyle CLI (optional fallback): `npm install -g @vivliostyle/cli`
- tkinterdnd2 >= 0.3.0 (for drag-and-drop support)

## Troubleshooting

### Prince Not Found
If you see "Prince is not installed", download and install Prince from [https://www.princexml.com/download/](https://www.princexml.com/download/). On Windows, the installer typically places it at `C:\Program Files\Prince\engine\bin\prince.exe`.

### xq Not Found
If you see "xq is not installed", download xq from [https://github.com/sibprogrammer/xq/releases](https://github.com/sibprogrammer/xq/releases) and place it in your PATH (e.g., `C:\Users\<username>\bin\xq.exe`).

### Vivliostyle Not Found
If Prince fails and Vivliostyle is needed as fallback, install it globally:
```bash
npm install -g @vivliostyle/cli
```

### Log Files
Conversion logs are saved to `~/.epub_to_pdf/logs/` (e.g., `C:\Users\<username>\.epub_to_pdf\logs\` on Windows). Check these logs for detailed error information.

## License

MIT License

## Author

Mattia Tagliente ([@mattiaTagliente](https://github.com/mattiaTagliente))
