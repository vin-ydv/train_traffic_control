Deployment guide — RailMind (Streamlit + Postgres)

Overview
--------
This document explains a recommended deployment flow for the RailMind project:
- Managed Postgres (Railway / Render / RDS)
- Streamlit app hosting (Streamlit Cloud / Render / Railway)

Two-step recommended flow (fast, reliable):
1) Provision a managed Postgres instance (Railway recommended for quick GitHub integration)
2) Deploy the Streamlit app, set DATABASE_URL, and run the seed script

Railway (quick, recommended)
----------------------------
1. Sign in to Railway (https://railway.app) and create a new project.
2. Add a PostgreSQL plugin — Railway provisions a DB and shows DATABASE_URL.
3. In your local repo or on Railway’s console run the seed script:
   - Locally (with DATABASE_URL set):
     $env:DATABASE_URL='postgresql://user:pass@host:port/dbname' ; python db/init_postgres.py
   - Or use Railway’s deploy console to run `python db/init_postgres.py`.
4. Connect the GitHub repo (Settings -> Deploy from GitHub) and create an environment variable DATABASE_URL in Railway to match the DB.
5. Add a service that runs `streamlit run app.py` (Railway can detect the Procfile).
6. Deploy — Railway will build using requirements.txt and start the app.

Streamlit Cloud (app hosting)
-----------------------------
1. Go to https://share.streamlit.io and create a new app from your GitHub repo `vin-ydv/train_traffic_control`.
2. Set the branch to `main` and the start command is already in Procfile (Streamlit Cloud uses streamlit run app.py by default).
3. Add an environment variable DATABASE_URL pointing to your managed Postgres.
4. The app will deploy and be publicly accessible. If you do not set DATABASE_URL, the app will fall back to local SQLite.

Render.com (alternative)
-------------------------
1. Create a Web Service, connect your GitHub repo.
2. Set the Start Command to `streamlit run app.py --server.port $PORT --server.address 0.0.0.0` (Procfile will also work).
3. Add an environment variable DATABASE_URL to Render’s env.
4. Add a Postgres service (Managed DB) in Render or use an external DB.
5. Deploy.

Local Docker approach (developer)
---------------------------------
1. Start Postgres locally: `docker-compose up -d db`
2. Seed DB: `python db/init_postgres.py`
3. Run app (PowerShell):
   $env:DATABASE_URL='postgresql://railmind:railmind@localhost:5432/railmind'
   streamlit run app.py

Notes
-----
- The repo prefers DATABASE_URL when it is present (Postgres) and falls back to a local SQLite `data/railmind.db` for quick testing.
- data/railmind.db is ignored by Git to keep state local.
- The seeding script `db/init_postgres.py` uses psycopg2 and is included in the repository.

If you want, I can:
- Attempt to provision a Railway project and seed it for you (requires access to your Railway account)
- Prepare a Render/Heroku deployment and open the public URL after deployment
- Provide a single CLI script to perform all steps if you provide cloud credentials (not recommended over chat)

