# EPUB to PDF Converter - Project Documentation

## Project Overview

A graphical utility for converting EPUB files to high-fidelity PDF format, optimized for Mistral OCR processing. Features drag-and-drop GUI and multiple conversion backends with automatic fallback.

## Architecture

### Project Structure
```
epub_to_pdf/
├── src/epub_to_pdf/           # Main package (modern src layout)
│   ├── __init__.py            # Package exports, version
│   ├── __main__.py            # Entry point for python -m
│   ├── app.py                 # Tkinter GUI with drag-and-drop
│   └── converter.py           # Conversion logic with multiple backends
├── launch_epub_to_pdf.vbs     # Silent Windows launcher
├── launch_epub_to_pdf.bat     # Batch launcher
├── pyproject.toml             # Project config, dependencies
├── README.md                  # User documentation
├── CLAUDE.md                  # This file
├── idea.txt                   # Original requirements analysis
└── .gitignore
```

### Key Components

1. **converter.py**: Core conversion logic
   - `convert_epub_to_pdf()`: Main API function
   - `ConversionMethod`: Enum (WEASYPRINT, PYMUPDF, PANDOC, CALIBRE, AUTO)
   - Auto-fallback chain: WeasyPrint > PyMuPDF > Pandoc > Calibre
   - EPUB spine parsing for WeasyPrint
   - Progress callback support

2. **app.py**: GUI application
   - Uses tkinterdnd2 for drag-and-drop (with fallback)
   - Threading for non-blocking conversion
   - Visual progress feedback

### Conversion Backends

| Backend | Status | Notes |
|---------|--------|-------|
| WeasyPrint | Primary | Pure Python, excellent CSS support |
| PyMuPDF | Fallback | Fast but CSS issues with EPUB3 |
| Pandoc | Fallback | Needs PDF engine (xelatex/pdflatex) |
| Calibre | Fallback | Needs Calibre installation |

## Virtual Environment

Located at: `C:\Users\matti\venvs\epub_to_pdf`

## Dependencies

- **weasyprint**: Primary conversion backend (pure Python)
- **pymupdf**: Fast MuPDF bindings (fallback)
- **tkinterdnd2**: Drag-and-drop support for tkinter

## Development Commands

```bash
# Install in development mode
cd C:\Users\matti\OneDrivePhD\Dev\epub_to_pdf
uv pip install -e . --python C:\Users\matti\venvs\epub_to_pdf\Scripts\python.exe

# Run the application
python -m epub_to_pdf

# Or use desktop shortcut
# Double-click: EPUB to PDF Converter.lnk
```

## Desktop Shortcut

A desktop shortcut is created that launches the app without showing a console window:
- **Shortcut**: `%USERPROFILE%\Desktop\EPUB to PDF Converter.lnk`
- **Target**: `launch_epub_to_pdf.vbs` (runs pythonw.exe)

## Design Decisions

1. **WeasyPrint as primary**: Handles complex EPUB3 CSS that PyMuPDF fails on
2. **Multiple backends**: Fallback support ensures conversion works across environments
3. **EPUB spine parsing**: Properly extracts reading order from EPUB structure
4. **Threading**: GUI remains responsive during conversion
5. **A4 page format**: Standard format for OCR processing

## Conversion Quality Focus

The tool prioritizes:
- Image quality preservation (no recompression)
- Layout fidelity for spatial content
- Proper rendering of embedded fonts
- Clean output for OCR processing
- CSS compatibility (especially EPUB3)

## GitHub Repository

https://github.com/mattiaTagliente/epub_to_pdf
