"""Tiny database layer. PostgreSQL in production (DATABASE_URL=postgresql://...),
SQLite otherwise (default, used by the tests). SQL is written once with '?' placeholders."""
import sqlite3
import uuid
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS records (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    category TEXT NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    date TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_records_session ON records(session_id);
"""


class Database:
    def __init__(self, url: str = "sqlite:///:memory:"):
        self.url = url
        self.postgres = url.startswith(("postgres://", "postgresql://"))
        self._memory_conn = None
        if not self.postgres and url.endswith(":memory:"):
            self._memory_conn = self._raw_connect()      # keep one connection alive
        self.init_schema()

    def _raw_connect(self):
        if self.postgres:
            import psycopg2
            return psycopg2.connect(self.url)
        path = self.url.replace("sqlite:///", "", 1)
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _run(self, sql, params=(), fetch=False):
        conn = self._memory_conn or self._raw_connect()
        try:
            cur = conn.cursor()
            cur.execute(sql.replace("?", "%s") if self.postgres else sql, params)
            rows = None
            if fetch:
                cols = [d[0] for d in cur.description]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
            conn.commit()
            return rows
        except Exception:
            conn.rollback()
            raise
        finally:
            if conn is not self._memory_conn:
                conn.close()

    def init_schema(self):
        for stmt in filter(None, (s.strip() for s in SCHEMA.split(";"))):
            self._run(stmt)

    # --- sessions / records -------------------------------------------------
    def create_session(self) -> str:
        sid = str(uuid.uuid4())
        self._run("INSERT INTO sessions (id, created_at) VALUES (?, ?)",
                  (sid, datetime.now(timezone.utc).isoformat()))
        return sid

    def session_exists(self, sid: str) -> bool:
        return bool(self._run("SELECT 1 AS x FROM sessions WHERE id = ?", (sid,), fetch=True))

    def add_records(self, sid: str, records: list[dict]) -> int:
        for r in records:
            self._run("INSERT INTO records (id, session_id, category, amount, date) VALUES (?, ?, ?, ?, ?)",
                      (str(uuid.uuid4()), sid, r["category"], r["amount"], r["date"]))
        return len(records)

    def get_records(self, sid: str) -> list[dict]:
        return self._run("SELECT category, amount, date FROM records WHERE session_id = ? ORDER BY date",
                         (sid,), fetch=True)
