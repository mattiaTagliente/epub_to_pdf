@echo off
REM EPUB to PDF Converter Launcher
REM This script launches the EPUB to PDF converter GUI

REM Activate the virtual environment and run the application
call "C:\Users\matti\venvs\epub_to_pdf\Scripts\activate.bat"
python -m epub_to_pdf
