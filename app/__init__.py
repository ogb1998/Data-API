"""Flask application factory."""
import os

from flask import Flask, jsonify, request

from .db import Database
from .services import parser, reporting


def create_app(database_url: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config["DB"] = Database(database_url or os.environ.get("DATABASE_URL", "sqlite:///:memory:"))

    def db() -> Database:
        return app.config["DB"]

    def error(msg, code):
        return jsonify({"error": msg}), code

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/sessions")
    def new_session():
        return jsonify({"session_id": db().create_session()}), 201

    @app.post("/sessions/<sid>/upload")
    def upload(sid):
        if not db().session_exists(sid):
            return error("session not found", 404)
        try:
            if request.is_json:
                rows = (request.get_json(silent=True) or {}).get("rows")
                if not isinstance(rows, list):
                    return error("JSON body must contain a 'rows' list", 400)
                records = parser.parse_rows(rows)
            else:
                records = parser.parse_csv(request.get_data(as_text=True))
        except parser.ParseError as e:
            return jsonify({"error": "validation failed", "details": e.errors}), 422
        return jsonify({"session_id": sid, "added": db().add_records(sid, records)}), 201

    @app.get("/sessions/<sid>/report")
    def report(sid):
        if not db().session_exists(sid):
            return error("session not found", 404)
        return jsonify(reporting.build_report(sid, db().get_records(sid)))

    return app
