"""Configuração e partidas locais. Nunca grava ao lado do executável."""

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def valid_api_url(value):
    if not value:
        return ""
    value = value.strip().rstrip("/")
    parsed = urlsplit(value)
    local = parsed.hostname in ("localhost", "127.0.0.1", "::1")
    if (parsed.scheme != "https" and not (parsed.scheme == "http" and local)):
        raise ValueError("Use HTTPS, ou HTTP apenas para localhost.")
    if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Informe apenas a URL do servidor, sem senha ou parâmetros.")
    if len(value) > 250:
        raise ValueError("URL muito longa.")
    return value


class Storage:
    def __init__(self, folder=None):
        default = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "WordsAtack"
        self.folder = Path(folder) if folder else default
        self.folder.mkdir(parents=True, exist_ok=True)
        self.database = self.folder / "partidas.sqlite3"
        self.config_file = self.folder / "config.json"
        self.config = {"nickname": "", "api_url": ""}
        self.lock = threading.Lock()
        self.status = "Ranking local · configure o servidor com F2"
        if self.config_file.exists():
            try:
                saved = json.loads(self.config_file.read_text(encoding="utf-8"))
                self.config["nickname"] = str(saved.get("nickname", ""))[:18]
                self.config["api_url"] = valid_api_url(str(saved.get("api_url", "")))
            except (ValueError, OSError, AttributeError):
                pass
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, nickname TEXT NOT NULL,
                score INTEGER NOT NULL, words INTEGER NOT NULL,
                accuracy REAL NOT NULL, duration REAL NOT NULL,
                level INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                synced INTEGER NOT NULL DEFAULT 0
            )""")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.database, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def save_config(self, nickname=None, api_url=None):
        updated = dict(self.config)
        if nickname is not None:
            updated["nickname"] = nickname.strip()[:18]
        if api_url is not None:
            updated["api_url"] = valid_api_url(api_url)
        temporary = self.config_file.with_suffix(".tmp")
        temporary.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.config_file)
        self.config = updated

    def save_run(self, run):
        with self.connect() as db:
            db.execute("""INSERT OR IGNORE INTO runs
                (id, nickname, score, words, accuracy, duration, level)
                VALUES (:id, :nickname, :score, :words, :accuracy, :duration, :level)""", run)

    def ranking(self):
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute("""SELECT nickname, score, words,
                accuracy, level FROM runs ORDER BY score DESC, accuracy DESC,
                duration ASC, created_at DESC, id ASC LIMIT 8""")]

    def sync(self):
        """Thread daemon: nunca bloqueia o loop gráfico. Reenvio idempotente por UUID."""
        endpoint = self.config["api_url"]
        if not endpoint or not self.lock.acquire(blocking=False):
            return

        def upload():
            try:
                with self.connect() as db:
                    db.row_factory = sqlite3.Row
                    pending = [dict(row) for row in db.execute(
                        "SELECT id, nickname, score, words, accuracy, duration, level "
                        "FROM runs WHERE synced = 0 ORDER BY created_at LIMIT 100"
                    )]
                if not pending:
                    self.status = "Nenhuma partida pendente de envio"
                    return
                self.status = "Enviando partidas ao ranking..."
                sent = 0
                rejected = 0
                for run in pending:
                    request = Request(
                        endpoint + "/api/scores",
                        data=json.dumps(run).encode("utf-8"),
                        headers={"Content-Type": "application/json", "User-Agent": "WordsAtack/0.1"},
                        method="POST",
                    )
                    try:
                        with urlopen(request, timeout=4) as response:
                            result = json.loads(response.read(8192))
                            if response.status not in (200, 201) or result.get("id") != run["id"]:
                                raise ValueError("Resposta inesperada")
                    except HTTPError as error:
                        if error.code in (400, 409):
                            rejected += 1
                            continue
                        raise
                    with self.connect() as db:
                        db.execute("UPDATE runs SET synced = 1 WHERE id = ?", (run["id"],))
                    sent += 1
                self.status = f"{sent} partida(s) enviada(s) ao ranking"
                if rejected:
                    self.status += f" · {rejected} rejeitada(s); registro local mantido"
            except (OSError, URLError, ValueError, sqlite3.Error):
                self.status = "Servidor indisponível · partidas preservadas no computador"
            finally:
                self.lock.release()

        threading.Thread(target=upload, daemon=True).start()
