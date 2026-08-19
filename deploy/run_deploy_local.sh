#!/usr/bin/env bash
set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
  echo "Please set DATABASE_URL, e.g."
  echo "export DATABASE_URL='postgresql://railmind:railmind@localhost:5432/railmind'"
  exit 2
fi

echo "Seeding Postgres at $DATABASE_URL"
python db/init_postgres.py

echo "Testing connection"
python db/check_connection.py

echo "Done. Start the app: DATABASE_URL=$DATABASE_URL streamlit run app.py"
