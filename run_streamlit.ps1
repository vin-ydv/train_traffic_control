# Run Streamlit app (PowerShell)
Set-Location $PSScriptRoot
py -3 -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
