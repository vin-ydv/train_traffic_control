Integration guide — Feeding live data into RailMind

This project includes a lightweight ingestion gateway and a simple file-backed queue for demos and pilots.

Components
- ingest_service.py: FastAPI service that accepts canonical JSON events (POST /events) and appends them to data/external_events.jsonl.
- app.py: the Streamlit UI will process events from data/external_events.jsonl on each run and convert them into Simulation pending events.

How it works (demo-mode)
1. Start the ingestion service:
   py -3 ingest_service.py
   (or run_ingest.ps1)
2. Start the Streamlit app:
   py -3 -m streamlit run app.py
3. Post an event (example using curl):
   curl -X POST http://127.0.0.1:9000/events -H "Content-Type: application/json" -d \
     '{"event_type":"departure_delay","train_id":"T1","minutes":20}'

Supported event mappings (demo-mode)
- departure_delay -> creates a pending departure_delay at current sim time
- speed_restriction -> creates a pending speed_restriction at current sim time
- network_speed -> creates a pending network_speed at current sim time
- train_hold -> creates a pending train_hold at current sim time

Production notes
- Replace the file-backed queue with a message bus (Kafka) for robust production ingestion.
- Implement authentication, mTLS and validation for ingest_service in production.
- Consider an edge adapter for vendor protocols (OPC-UA, MQTT, SCADA) that posts canonical JSON to this gateway.

Next steps
- Add a Kafka adapter and a consumer if you want durable streaming replay.
- Add schema validation and a heartbeat/health-check for each source.
