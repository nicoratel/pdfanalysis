@echo off
REM Launcher script for pdfanalysis-app on Windows
REM This provides a fallback if the .exe wrapper doesn't work

python -m app_pdf_analysis %*
