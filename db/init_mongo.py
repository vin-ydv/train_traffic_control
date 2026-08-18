"""Seed MongoDB from the project's JSON data files.

Usage:
  Set MONGODB_URI environment variable and run:
    python db/init_mongo.py

This creates collections: stations, blocks, trains
"""
from __future__ import annotations
import os
import json
import sys
from pathlib import Path

from pymongo import MongoClient

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
MONGO_URI = os.environ.get("MONGODB_URI")
if not MONGO_URI:
    print("MONGODB_URI not set. Set it and try again.")
    sys.exit(2)

client = MongoClient(MONGO_URI)
db = client.get_default_database()

def seed():
    section = json.loads((DATA / "section.json").read_text(encoding="utf-8"))
    timetable = json.loads((DATA / "timetable.json").read_text(encoding="utf-8"))

    stations = section.get("stations", [])
    blocks = section.get("blocks", [])
    trains = timetable.get("trains", [])

    if stations:
        db.stations.delete_many({})
        db.stations.insert_many(stations)
    if blocks:
        db.blocks.delete_many({})
        # store blocks with consistent keys
        db.blocks.insert_many(blocks)
    if trains:
        db.trains.delete_many({})
        db.trains.insert_many(trains)

    print("MongoDB seed complete")

if __name__ == '__main__':
    try:
        seed()
    except Exception as e:
        print("Seeding failed:", e)
        sys.exit(3)
