"""Small script to check the DATABASE_URL and connectivity to Postgres.

Usage:
  python db/check_connection.py

It will print the resolved DATABASE_URL and whether a simple SELECT 1 succeeds.
"""
from __future__ import annotations
import os
import sys
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("No DATABASE_URL set in environment. Exiting.")
    sys.exit(2)

print(f"Testing connection to: {DATABASE_URL}")
try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT 1")
    r = cur.fetchone()
    print("SELECT 1 ->", r)
    cur.close()
    conn.close()
    print("Connection OK")
except Exception as e:
    print("Connection failed:", e)
    sys.exit(3)
