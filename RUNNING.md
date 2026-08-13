Quick start — RailMind

Requirements
- Python 3.10+
- Install dependencies: py -3 -m pip install -r requirements.txt

Run locally
- From project root: py -3 -m streamlit run app.py
- Or use the provided scripts:
  - PowerShell: .\run_streamlit.ps1
  - Windows CMD: .\run_streamlit.bat

Streamlit defaults
- App will be served on http://127.0.0.1:8501
- First-run telemetry is disabled via .streamlit/config.toml

Development notes
- Tests: py -3 -m pytest
- To build or package, create a virtual environment and pin dependencies with pip freeze > requirements.txt

If you encounter ERR_CONNECTION_REFUSED:
- Ensure the Streamlit process is running and printed a Local URL in the terminal.
- Confirm firewall/antivirus is not blocking Python.
- Try a different port: py -3 -m streamlit run app.py --server.port 8502

Contact
- Project maintained for SIH 2025 — reach maintainers in TEAM.md
