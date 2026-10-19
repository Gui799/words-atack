"""API Flask + SQLite; também serve o site para apresentação local."""

import math
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ("id", "nickname", "score", "words", "accuracy", "duration", "level")


def validate_score(data):
    if not isinstance(data, dict) or any(field not in data for field in FIELDS):
        raise ValueError("Envie id, nickname, score, words, accuracy, duration e level.")
    if not isinstance(data["id"], str) or str(UUID(data["id"])) != data["id"]:
        raise ValueError("ID deve ser um UUID canônico.")
    nickname = data["nickname"]
    if not isinstance(nickname, str) or not 1 <= len(nickname.strip()) <= 18 or not nickname.isprintable():
        raise ValueError("Nickname deve ter de 1 a 18 caracteres visíveis.")
    for field, minimum, maximum in (("score", 0, 10000000), ("words", 0, 100000), ("level", 1, 20001)):
        value = data[field]
        if type(value) is not int or not minimum <= value <= maximum:
            raise ValueError(f"Valor inválido: {field}.")
    for field, maximum in (("accuracy", 100), ("duration", 86400)):
        value = data[field]
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= maximum:
            raise ValueError(f"Valor inválido: {field}.")
    if data["level"] != 1 + data["words"] // 5:
        raise ValueError("Nível inconsistente com a quantidade de palavras.")
    result = {field: data[field] for field in FIELDS}
    result["nickname"] = nickname.strip()
    return result


def create_app(test_config=None):
    app = Flask(__name__, static_folder=None)
    app.config.update(
        DATABASE=os.environ.get("WORDS_ATACK_DB", str(ROOT / "data" / "ranking.sqlite3")),
        ALLOWED_ORIGINS=os.environ.get("WORDS_ATACK_ORIGINS", "http://127.0.0.1:5000,http://localhost:5000").split(","),
        MAX_CONTENT_LENGTH=4096,
    )
    if test_config:
        app.config.update(test_config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect():
        db = sqlite3.connect(app.config["DATABASE"], timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    with connect() as db:
        db.executescript((Path(__file__).with_name("schema.sql")).read_text(encoding="utf-8"))
        db.execute("PRAGMA journal_mode=WAL")

    @app.after_request
    def response_headers(response):
        origin = request.headers.get("Origin")
        allowed = [item.strip().rstrip("/") for item in app.config["ALLOWED_ORIGINS"]]
        if origin and origin.rstrip("/") in allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.vary.add("Origin")
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(HTTPException)
    def http_error(error):
        if request.path.startswith("/api/"):
            return jsonify(error=error.description), error.code
        return error

    @app.get("/api/health")
    def health():
        with connect() as db:
            db.execute("SELECT 1").fetchone()
        return jsonify(status="ok", game="Words Atack", version="0.1.0")

    @app.route("/api/scores", methods=["POST", "OPTIONS"])
    def save_score():
        if request.method == "OPTIONS":
            return "", 204
        if not request.is_json:
            return jsonify(error="Use Content-Type: application/json."), 415
        try:
            score = validate_score(request.get_json())
        except (ValueError, TypeError, AttributeError) as error:
            return jsonify(error=str(error)), 400
        with connect() as db:
            cursor = db.execute("""INSERT OR IGNORE INTO scores
                (id, nickname, score, words, accuracy, duration, level)
                VALUES (:id, :nickname, :score, :words, :accuracy, :duration, :level)""", score)
            created = cursor.rowcount == 1
            stored = db.execute("SELECT * FROM scores WHERE id = ?", (score["id"],)).fetchone()
            if not created and any(stored[field] != score[field] for field in FIELDS):
                return jsonify(error="Este ID já pertence a outra partida."), 409
        return jsonify(id=score["id"], saved=True, duplicate=not created), 201 if created else 200

    @app.get("/api/leaderboard")
    def leaderboard():
        try:
            limit = max(1, min(50, int(request.args.get("limit", 10))))
        except ValueError:
            return jsonify(error="limit deve ser inteiro."), 400
        with connect() as db:
            rows = db.execute("""SELECT nickname, score, words, accuracy, duration, level, created_at
                FROM scores ORDER BY score DESC, accuracy DESC, duration ASC,
                created_at DESC, id ASC LIMIT ?""", (limit,)).fetchall()
        return jsonify(scores=[dict(row) for row in rows])

    @app.get("/")
    def index():
        return send_from_directory(ROOT / "docs", "index.html")

    @app.get("/<path:filename>")
    def site_file(filename):
        return send_from_directory(ROOT / "docs", filename)

    return app
