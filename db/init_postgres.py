"""Initialize a PostgreSQL database for RailMind and seed it from JSON files.

Usage:
  - Ensure a Postgres server is reachable at DATABASE_URL or use defaults.
  - Run: python db/init_postgres.py

This script uses psycopg2 to create tables and seed stations/blocks/trains.
"""
from __future__ import annotations
import os
import json
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
DEFAULT_URL = "postgresql://railmind:railmind@localhost:5432/railmind"
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_URL)

SCHEMA_STMTS = [
    """
    CREATE TABLE IF NOT EXISTS stations (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        x DOUBLE PRECISION NOT NULL,
        y DOUBLE PRECISION NOT NULL,
        loops INTEGER NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS blocks (
        id TEXT PRIMARY KEY,
        from_station TEXT NOT NULL,
        to_station TEXT NOT NULL,
        length_km DOUBLE PRECISION NOT NULL,
        max_speed DOUBLE PRECISION NOT NULL,
        double_line BOOLEAN NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS trains (
        id TEXT PRIMARY KEY,
        number TEXT NOT NULL,
        name TEXT NOT NULL,
        direction TEXT NOT NULL,
        priority INTEGER NOT NULL,
        type TEXT NOT NULL,
        pax INTEGER NOT NULL,
        speed DOUBLE PRECISION NOT NULL,
        origin TEXT NOT NULL,
        dest TEXT NOT NULL,
        dep_min DOUBLE PRECISION NOT NULL,
        dwell_min DOUBLE PRECISION NOT NULL
    );
    """,
]


def connect():
    return psycopg2.connect(DATABASE_URL)


def seed():
    conn = connect()
    cur = conn.cursor()
    for s in SCHEMA_STMTS:
        cur.execute(s)
    # seed stations and blocks from section.json
    section = json.loads((DATA / "section.json").read_text(encoding="utf-8"))
    stations = [(st["id"], st["name"], st["x"], st["y"], st["loops"]) for st in section.get("stations", [])]
    if stations:
        execute_values(cur, "INSERT INTO stations (id, name, x, y, loops) VALUES %s ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, x=EXCLUDED.x, y=EXCLUDED.y, loops=EXCLUDED.loops", stations)
    blocks = [(b["id"], b["from"], b["to"], b["length_km"], b["max_speed"], b["double_line"]) for b in section.get("blocks", [])]
    if blocks:
        execute_values(cur, "INSERT INTO blocks (id, from_station, to_station, length_km, max_speed, double_line) VALUES %s ON CONFLICT (id) DO UPDATE SET from_station=EXCLUDED.from_station, to_station=EXCLUDED.to_station, length_km=EXCLUDED.length_km, max_speed=EXCLUDED.max_speed, double_line=EXCLUDED.double_line", blocks)
    # seed trains
    timetable = json.loads((DATA / "timetable.json").read_text(encoding="utf-8"))
    trains = [(
        t["id"], t["number"], t["name"], t["direction"], t["priority"], t["type"], t["pax"], t["speed"], t["origin"], t["dest"], t["dep_min"], t["dwell_min"]
    ) for t in timetable.get("trains", [])]
    if trains:
        execute_values(cur, "INSERT INTO trains (id, number, name, direction, priority, type, pax, speed, origin, dest, dep_min, dwell_min) VALUES %s ON CONFLICT (id) DO UPDATE SET number=EXCLUDED.number, name=EXCLUDED.name, direction=EXCLUDED.direction, priority=EXCLUDED.priority, type=EXCLUDED.type, pax=EXCLUDED.pax, speed=EXCLUDED.speed, origin=EXCLUDED.origin, dest=EXCLUDED.dest, dep_min=EXCLUDED.dep_min, dwell_min=EXCLUDED.dwell_min", trains)
    conn.commit()
    cur.close()
    conn.close()
    print("Postgres seed complete")


if __name__ == '__main__':
    try:
        seed()
    except Exception as e:
        print("Failed to seed Postgres:", e)
        sys.exit(2)
