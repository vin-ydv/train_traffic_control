"""Simple ingestion service: accept canonical events and append to data/external_events.jsonl

Run: python ingest_service.py
POST /events with JSON body. Example payloads documented in the README.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
import json
from pathlib import Path

app = FastAPI(title="RailMind Ingest Gateway")
DATA_DIR = Path(__file__).resolve().parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
QUEUE_FILE = DATA_DIR / 'external_events.jsonl'

class Event(BaseModel):
    event_type: str
    timestamp: Optional[str] = None
    source: Optional[str] = None
    block_id: Optional[str] = None
    train_id: Optional[str] = None
    direction: Optional[str] = None
    status: Optional[str] = None
    progress_km: Optional[float] = None
    speed_kmh: Optional[float] = None
    speed: Optional[float] = None
    duration_min: Optional[int] = None
    minutes: Optional[int] = None
    reason: Optional[str] = None
    details: Optional[Any] = None

@app.post("/events")
async def post_event(ev: Event):
    # validate event_type
    if not ev.event_type:
        raise HTTPException(status_code=400, detail="event_type is required")
    rec = ev.dict()
    # normalise timestamp
    if rec.get('timestamp') is None:
        rec['timestamp'] = datetime.utcnow().isoformat() + 'Z'
    # append as JSON line
    with open(QUEUE_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, default=str) + "\n")
    return {"status": "accepted", "event_type": ev.event_type}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=9000)
