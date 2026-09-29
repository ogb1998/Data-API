# Data Processing API

A modular Flask backend that accepts tabular data (CSV or JSON) in **sessions**, validates it, stores it, and produces summary reports. Sessions persist between requests, so a client can upload data in several turns and request a report at any point.

## Architecture
```
app/
  __init__.py          Flask app factory + HTTP routes (thin: no business logic)
  db.py                storage layer: PostgreSQL in production, SQLite for tests/dev
  services/
    parser.py          parsing & validation (collects ALL row errors, not just the first)
    logic.py           pure functions: totals, monthly totals, stats, MAD outlier flags
    reporting.py       assembles logic output into the JSON report
tests/                 service unit tests + API integration tests (Flask test client)
Dockerfile, docker-compose.yml   API + PostgreSQL
```
Each layer only talks to the next: routes -> parser -> db -> logic -> reporting. Logic and parsing are pure, so they're tested without HTTP or a database.

## Endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness check |
| POST | `/sessions` | create a session, returns `session_id` |
| POST | `/sessions/<id>/upload` | body: CSV text (`category,amount,date`) or JSON `{"rows": [...]}`; 422 with per-row `details` if invalid |
| GET | `/sessions/<id>/report` | summary stats, totals by category and month, flagged outliers |

## Run locally (SQLite, no setup)
```bash
pip install flask
python -m unittest discover -s tests -v
flask --app wsgi run
```
```bash
SID=$(curl -s -X POST localhost:5000/sessions | python -c "import sys,json;print(json.load(sys.stdin)['session_id'])")
curl -X POST localhost:5000/sessions/$SID/upload -H "Content-Type: text/csv" \
     --data-binary $'category,amount,date\nfood,12.5,2024-01-03\nrent,900,2024-02-01'
curl localhost:5000/sessions/$SID/report
```

## Run with PostgreSQL
```bash
docker compose up --build        # API on :8000, DATABASE_URL points at the postgres service
```

## Measuring test coverage
```bash
pip install coverage
coverage run -m unittest discover -s tests && coverage report -m
```
Quote the number this actually prints; don't assume one.

## Known limitations
- No authentication; session IDs are unguessable UUIDs but are the only access control.
- Records are inserted one at a time (fine for demos; use `executemany`/`COPY` for large uploads).
- The PostgreSQL code path (`psycopg2`) is exercised by `docker compose`, while the automated tests run against SQLite.
