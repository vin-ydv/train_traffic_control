param(
  [Parameter(Mandatory=$false)][string]$DatabaseUrl
)

if (-not $DatabaseUrl) {
  Write-Host "Please provide DATABASE_URL, for example:`n$env:DATABASE_URL='postgresql://railmind:railmind@localhost:5432/railmind'`nOr call: .\run_deploy_local.ps1 -DatabaseUrl 'postgresql://...'
"
  exit 2
}

Write-Host "Seeding Postgres at: $DatabaseUrl"
$env:DATABASE_URL = $DatabaseUrl
python .\db\init_postgres.py
if ($LASTEXITCODE -ne 0) { Write-Error "Seeding failed"; exit $LASTEXITCODE }

Write-Host "Checking DB connection"
python .\db\check_connection.py
if ($LASTEXITCODE -ne 0) { Write-Error "DB check failed"; exit $LASTEXITCODE }

Write-Host "Ready — run the app with:`n$env:DATABASE_URL='$DatabaseUrl' ; streamlit run app.py"
