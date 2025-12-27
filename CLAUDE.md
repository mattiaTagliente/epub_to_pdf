# EPUB to PDF Converter - Project Documentation

## Project Overview

A graphical utility for converting EPUB files to high-fidelity PDF format, optimized for Mistral OCR processing. The tool provides drag-and-drop functionality and supports multiple conversion backends.

## Architecture

### Project Structure
```
epub_to_pdf/
├── src/epub_to_pdf/        # Main package (modern src layout)
│   ├── __init__.py         # Package exports, version
│   ├── __main__.py         # Entry point for python -m
│   ├── app.py              # Tkinter GUI with drag-and-drop
│   └── converter.py        # Conversion logic with multiple backends
├── pyproject.toml          # Project config, dependencies
├── README.md               # User documentation
├── CLAUDE.md               # This file
├── idea.txt                # Original requirements analysis
└── .gitignore
```

### Key Components

1. **converter.py**: Core conversion logic
   - `convert_epub_to_pdf()`: Main API function
   - `ConversionMethod`: Enum for backend selection (PYMUPDF, MUTOOL, CALIBRE, AUTO)
   - Auto-fallback chain: PyMuPDF → mutool → Calibre
   - Progress callback support

2. **app.py**: GUI application
   - Uses tkinterdnd2 for drag-and-drop (with fallback)
   - Threading for non-blocking conversion
   - Visual progress feedback

## Dependencies

- **pymupdf**: Primary conversion backend (MuPDF bindings)
- **tkinterdnd2**: Drag-and-drop support for tkinter

Optional external tools:
- **mutool**: MuPDF CLI (fallback)
- **ebook-convert**: Calibre CLI (fallback)

## Virtual Environment

Located at: `C:\Users\matti\venvs\epub_to_pdf`

## Development Commands

```bash
# Install in development mode
uv pip install -e .

# Run the application
python -m epub_to_pdf
# or
epub-to-pdf

# Run linting
ruff check src/
```

## Design Decisions

1. **PyMuPDF as primary**: Chosen for sub-pixel rendering accuracy and speed
2. **Multiple backends**: Fallback support ensures conversion works across environments
3. **Threading**: GUI remains responsive during conversion
4. **A4 page format**: Standard format for OCR processing (595x842 points)

## Conversion Quality Focus

The tool prioritizes:
- Image quality preservation (no recompression)
- Layout fidelity for spatial content
- Proper rendering of embedded fonts
- Clean output for OCR processing

## GitHub Repository

https://github.com/mattiaTagliente/epub_to_pdf
