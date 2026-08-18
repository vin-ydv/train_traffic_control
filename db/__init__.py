"""SQLite-backed data layer for RailMind.

The project keeps a lightweight SQLite database in data/railmind.db and seeds it
from the existing JSON files so the app remains compatible while gaining a real
persistent backend for static rail data and operational records.
"""

from .models import (
    DB_PATH,
    init_db,
    load_blocks_from_db,
    load_stations_from_db,
    load_trains_from_db,
    log_event,
    save_run_metrics,
)

__all__ = [
    "DB_PATH",
    "init_db",
    "load_stations_from_db",
    "load_blocks_from_db",
    "load_trains_from_db",
    "log_event",
    "save_run_metrics",
]
