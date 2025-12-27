' EPUB to PDF Converter - Silent Launcher
' This script launches the application without showing a command window

Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """C:\Users\matti\venvs\epub_to_pdf\Scripts\pythonw.exe"" -m epub_to_pdf", 0, False
