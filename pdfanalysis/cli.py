from pathlib import Path
import sys
import streamlit.web.cli as stcli

def main():
    app_path = Path(__file__).parent / "app_pdf_analysis.py"

    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
    ]

    sys.exit(stcli.main())
