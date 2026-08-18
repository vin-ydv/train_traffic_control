# Helper: start local postgres via docker-compose and seed it for RailMind
cd $PSScriptRoot
Write-Host "Starting docker-compose services..."
docker-compose up -d db
Write-Host "Waiting 5s for Postgres to become ready..."
Start-Sleep -s 5
Write-Host "Seeding Postgres with project data..."
python .\db\init_postgres.py
Write-Host "Done. You can now run the app against Postgres by setting DATABASE_URL."
Write-Host "Example: $env:DATABASE_URL='postgresql://railmind:railmind@localhost:5432/railmind' ; streamlit run app.py"