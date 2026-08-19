"""Check MongoDB connectivity using MONGODB_URI environment variable."""
from __future__ import annotations
import os
import sys
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGODB_URI")
if not MONGO_URI:
    print("MONGODB_URI not set. Exiting.")
    sys.exit(2)

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('MongoDB ping succeeded')
    db = client.get_default_database()
    print('Database:', db.name)
except Exception as e:
    print('Connection failed:', e)
    sys.exit(3)
