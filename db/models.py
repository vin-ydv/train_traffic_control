"""SQLite schema and persistence helpers for RailMind.

This module provides a small but production-minded SQLite backend for the rail
control app. The schema is intentionally simple and PostgreSQL-friendly so it can
later be migrated with minimal changes.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "railmind.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS stations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    x REAL NOT NULL,
    y REAL NOT NULL,
    loops INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS blocks (
    id TEXT PRIMARY KEY,
    from_station TEXT NOT NULL,
    to_station TEXT NOT NULL,
    length_km REAL NOT NULL,
    max_speed REAL NOT NULL,
    double_line INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS trains (
    id TEXT PRIMARY KEY,
    number TEXT NOT NULL,
    name TEXT NOT NULL,
    direction TEXT NOT NULL,
    priority INTEGER NOT NULL,
    type TEXT NOT NULL,
    pax INTEGER NOT NULL,
    speed REAL NOT NULL,
    origin TEXT NOT NULL,
    dest TEXT NOT NULL,
    dep_min REAL NOT NULL,
    dwell_min REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS simulation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id TEXT NOT NULL,
    mode TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    throughput INTEGER,
    avg_delay REAL,
    punctuality REAL,
    safety_violations INTEGER
);

CREATE TABLE IF NOT EXISTS dispatch_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    time_min INTEGER NOT NULL,
    block_id TEXT NOT NULL,
    released_train TEXT NOT NULL,
    held_trains TEXT,
    decision_reason TEXT,
    confidence REAL,
    FOREIGN KEY (run_id) REFERENCES simulation_runs(id)
);

CREATE TABLE IF NOT EXISTS event_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    time_min INTEGER NOT NULL,
    kind TEXT NOT NULL,
    train_id TEXT,
    block_id TEXT,
    detail TEXT,
    FOREIGN KEY (run_id) REFERENCES simulation_runs(id)
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    conn = _connect()
    conn.executescript(SCHEMA)
    _seed_if_empty(conn)
    conn.commit()
    conn.close()
    return _connect()


def _seed_if_empty(conn: sqlite3.Connection) -> None:
    station_count = conn.execute("SELECT COUNT(*) FROM stations").fetchone()[0]
    if station_count == 0:
        section_raw = json.loads((DATA_DIR / "section.json").read_text(encoding="utf-8"))
        for station in section_raw.get("stations", []):
            conn.execute(
                "INSERT OR REPLACE INTO stations(id, name, x, y, loops) VALUES (?, ?, ?, ?, ?)",
                (station["id"], station["name"], station["x"], station["y"], station["loops"]),
            )
        for block in section_raw.get("blocks", []):
            conn.execute(
                "INSERT OR REPLACE INTO blocks(id, from_station, to_station, length_km, max_speed, double_line) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    block["id"],
                    block["from"],
                    block["to"],
                    block["length_km"],
                    block["max_speed"],
                    int(bool(block["double_line"])),
                ),
            )

    train_count = conn.execute("SELECT COUNT(*) FROM trains").fetchone()[0]
    if train_count == 0:
        timetable_raw = json.loads((DATA_DIR / "timetable.json").read_text(encoding="utf-8"))
        for train in timetable_raw.get("trains", []):
            conn.execute(
                "INSERT OR REPLACE INTO trains(id, number, name, direction, priority, type, pax, speed, origin, dest, dep_min, dwell_min) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    train["id"],
                    train["number"],
                    train["name"],
                    train["direction"],
                    train["priority"],
                    train["type"],
                    train["pax"],
                    train["speed"],
                    train["origin"],
                    train["dest"],
                    train["dep_min"],
                    train["dwell_min"],
                ),
            )


def load_stations_from_db() -> list[dict[str, Any]]:
    conn = _connect()
    rows = conn.execute("SELECT id, name, x, y, loops FROM stations ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def load_blocks_from_db() -> list[dict[str, Any]]:
    conn = _connect()
    rows = conn.execute(
        "SELECT id, from_station AS from_id, to_station AS to_id, length_km, max_speed, double_line FROM blocks ORDER BY id"
    ).fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "from": row["from_id"],
            "to": row["to_id"],
            "length_km": row["length_km"],
            "max_speed": row["max_speed"],
            "double_line": bool(row["double_line"]),
        }
        for row in rows
    ]


def load_trains_from_db() -> list[dict[str, Any]]:
    conn = _connect()
    rows = conn.execute(
        "SELECT id, number, name, direction, priority, type, pax, speed, origin, dest, dep_min, dwell_min FROM trains ORDER BY dep_min, number"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_run_metrics(scenario_id: str, mode: str, **metrics: Any) -> int:
    conn = _connect()
    cur = conn.execute(
        "INSERT INTO simulation_runs (scenario_id, mode, started_at, finished_at, throughput, avg_delay, punctuality, safety_violations) VALUES (?, ?, datetime('now'), datetime('now'), ?, ?, ?, ?)",
        (
            scenario_id,
            mode,
            metrics.get("throughput"),
            metrics.get("avg_delay"),
            metrics.get("punctuality"),
            metrics.get("safety_violations"),
        ),
    )
    conn.commit()
    run_id = cur.lastrowid
    conn.close()
    return run_id


def log_event(run_id: int, time_min: int, kind: str, train_id: str | None = None, block_id: str | None = None, detail: str = "") -> None:
    conn = _connect()
    conn.execute(
        "INSERT INTO event_logs (run_id, time_min, kind, train_id, block_id, detail) VALUES (?, ?, ?, ?, ?, ?)",
        (run_id, time_min, kind, train_id, block_id, detail),
    )
    conn.commit()
    conn.close()


def ensure_db_ready() -> None:
    init_db()
