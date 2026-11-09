"""Testes de regras, persistência, API e envio real via HTTP local."""
import json
import os
import tempfile
import threading
import time
import unittest
import uuid
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame
from werkzeug.serving import make_server
from game.main import Game
from game.storage import Storage, valid_api_url
from server.app import create_app


def record(**changes):
    result = {"id": str(uuid.uuid4()), "nickname": "Defensor", "score": 350,
              "words": 5, "accuracy": 83.3, "duration": 48.2, "level": 2}
    result.update(changes)
    return result


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING": True, "DATABASE": str(Path(self.tmp.name) / "ranking.db"),
                               "ALLOWED_ORIGINS": ["https://defensor.github.io"]})
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_health_empty_ranking_and_site(self):
        self.assertEqual(self.client.get("/api/health").json["status"], "ok")
        self.assertEqual(self.client.get("/api/leaderboard").json, {"scores": []})
        with self.client.get("/") as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"WORDS ATACK", response.data)
        with self.client.get("/../server/schema.sql") as response:
            self.assertEqual(response.status_code, 404)

    def test_save_persist_sort_and_idempotency(self):
        first = record()
        self.assertEqual(self.client.post("/api/scores", json=first).status_code, 201)
        self.assertEqual(self.client.post("/api/scores", json=first).status_code, 200)
        changed = dict(first, score=999)
        self.assertEqual(self.client.post("/api/scores", json=changed).status_code, 409)
        self.client.post("/api/scores", json=record(nickname="Melhor", score=1000))
        rows = self.client.get("/api/leaderboard").json["scores"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["nickname"], "Melhor")
        other = create_app({"TESTING": True, "DATABASE": self.app.config["DATABASE"]})
        self.assertEqual(len(other.test_client().get("/api/leaderboard").json["scores"]), 2)

    def test_invalid_payloads_and_limits(self):
        for change in ({"score": -1}, {"score": True}, {"nickname": ""}, {"id": "x"},
                       {"accuracy": float("nan")}, {"duration": float("inf")},
                       {"nickname": "a\nb"}, {"level": 3}, {"words": "10"}):
            with self.subTest(change=change):
                self.assertEqual(self.client.post("/api/scores", json=record(**change)).status_code, 400)
        self.assertEqual(self.client.post("/api/scores", json=[]).status_code, 400)
        self.assertEqual(self.client.post("/api/scores", data="{}", content_type="text/plain").status_code, 415)
        self.assertEqual(self.client.post("/api/scores", data="x" * 5000, content_type="application/json").status_code, 413)
        self.assertEqual(self.client.get("/api/leaderboard?limit=abc").status_code, 400)

    def test_cors_and_sql_parameters(self):
        response = self.client.options("/api/scores", headers={"Origin": "https://defensor.github.io"})
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "https://defensor.github.io")
        response = self.client.get("/api/leaderboard", headers={"Origin": "https://outro.example"})
        self.assertNotIn("Access-Control-Allow-Origin", response.headers)
        payload = record(nickname="'; DROP TABLE x;--")
        self.assertEqual(self.client.post("/api/scores", json=payload).status_code, 201)
        self.assertEqual(self.client.get("/api/leaderboard").json["scores"][0]["nickname"], payload["nickname"])

    def test_real_sync_and_offline_persistence(self):
        storage = Storage(Path(self.tmp.name) / "local")
        payload = record()
        storage.save_run(payload)
        storage.save_run(payload)
        self.assertEqual(len(storage.ranking()), 1)
        server = make_server("127.0.0.1", 0, self.app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            storage.save_config(api_url=f"http://127.0.0.1:{server.server_port}")
            storage.sync()
            deadline = time.monotonic() + 8
            while storage.lock.locked() and time.monotonic() < deadline:
                time.sleep(.03)
            self.assertFalse(storage.lock.locked())
            self.assertEqual(len(self.client.get("/api/leaderboard").json["scores"]), 1)
            with storage.connect() as db:
                self.assertEqual(db.execute("SELECT synced FROM runs").fetchone()[0], 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
        storage.save_run(record(score=500))
        storage.sync()
        deadline = time.monotonic() + 8
        while storage.lock.locked() and time.monotonic() < deadline:
            time.sleep(.03)
        self.assertIn("indisponível", storage.status)
        self.assertEqual(len(Storage(Path(self.tmp.name) / "local").ranking()), 2)


class GameTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.game = Game(self.tmp.name)
        self.game.storage.save_config(api_url="")
        self.game.nickname = "Player"
        self.game.start()

    def tearDown(self):
        pygame.quit()
        self.tmp.cleanup()

    def enemy(self, word="laser", y=300):
        return {"word": word, "x": 120, "y": y, "speed": 30}

    def test_typing_hit_combo_and_miss(self):
        for _ in range(6):
            self.game.enemies = [self.enemy()]
            self.game.handle(pygame.event.Event(pygame.TEXTINPUT, text="laser"))
            self.game.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertEqual(self.game.score, 350)
        self.assertEqual(self.game.level, 2)
        self.assertEqual(self.game.accuracy, 100)
        self.game.typed = "errado"
        self.game.shoot()
        self.assertEqual(self.game.combo, 0)
        self.assertAlmostEqual(self.game.accuracy, 85.7)
        self.game.handle(pygame.event.Event(pygame.TEXTINPUT, text="vírus"))
        self.assertEqual(self.game.typed, "virus")

    def test_pause_and_focus_loss_freeze_simulation(self):
        self.game.enemies = [self.enemy(y=100)]
        self.game.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.game.update(1)
        self.assertEqual(self.game.enemies[0]["y"], 100)
        self.game.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.game.update(.5)
        self.assertEqual(self.game.enemies[0]["y"], 115)
        self.game.handle(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.assertEqual(self.game.state, "paused")

    def test_impacts_save_once_and_restart(self):
        self.game.lives = 1
        self.game.enemies = [self.enemy(y=580)]
        self.game.update(.1)
        self.assertEqual(self.game.state, "over")
        self.game.finish()
        self.assertEqual(len(self.game.storage.ranking()), 1)
        self.game.start()
        self.assertEqual(self.game.lives, 5)
        self.assertEqual(self.game.score, 0)

    def test_spawn_unique_words_and_no_lane_overlap(self):
        for _ in range(100):
            self.game.spawn()
        self.assertEqual(len(self.game.enemies), 5)
        self.assertEqual(len({enemy["word"] for enemy in self.game.enemies}), 5)
        self.assertEqual(len({enemy["x"] for enemy in self.game.enemies}), 5)

    def test_render_all_screens_and_empty_nickname(self):
        for state in ("menu", "playing", "paused", "over", "settings", "ranking"):
            with self.subTest(state=state):
                self.game.state = state
                self.game.draw()
        self.game.state = "menu"
        self.game.nickname = "  "
        self.game.start()
        self.assertEqual(self.game.state, "menu")
        self.assertIn("nickname", self.game.message)

    def test_server_url_validation(self):
        self.assertEqual(valid_api_url("https://example.org/"), "https://example.org")
        self.assertEqual(valid_api_url(""), "")
        for value in ("http://example.org", "file:///x", "https://user:pass@example.org", "https://example.org?x=1"):
            with self.assertRaises(ValueError):
                valid_api_url(value)

    def test_menu_opens_nickname_before_starting(self):
        self.game.state = 'menu'
        self.game.nickname = ''
        self.game.handle(pygame.event.Event(pygame.TEXTINPUT, text='ignored'))
        self.assertEqual(self.game.nickname, '')
        self.game.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertEqual(self.game.state, 'nickname')
        self.game.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertEqual(self.game.state, 'nickname')
        self.game.handle(pygame.event.Event(pygame.TEXTINPUT, text='Defensor'))
        self.game.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertEqual(self.game.state, 'playing')
        self.assertEqual(self.game.storage.config['nickname'], 'Defensor')

    def test_expanded_vocabulary_is_typeable_and_unique(self):
        from game import settings
        self.assertGreater(len(settings.WORDS), 150)
        self.assertEqual(len(settings.WORDS), len(set(settings.WORDS)))
        self.assertTrue(all(word.isascii() and word.isalpha() and word.islower() for word in settings.WORDS))
        self.game.enemies = [self.enemy(word='criatividade')]
        self.game.typed = 'criatividade'
        self.game.shoot()
        self.assertEqual(self.game.score, 120)

    def test_music_changes_with_screen_and_mute_persists(self):
        from game.audio import Audio
        audio = self.game.audio
        self.assertTrue(audio.enabled)
        audio.set_state('menu')
        self.assertEqual(audio.track, 'menu')
        audio.set_state('nickname')
        self.assertEqual(audio.track, 'menu')
        audio.set_state('playing')
        self.assertEqual(audio.track, 'stage')
        self.assertTrue(pygame.mixer.Channel(1).get_busy())
        audio.set_state('paused')
        self.assertFalse(pygame.mixer.Channel(1).get_busy())
        audio.toggle()
        audio.set_state('menu')
        self.assertEqual(pygame.mixer.music.get_volume(), 0)
        self.assertTrue(Audio(self.tmp.name).muted)


if __name__ == "__main__":
    unittest.main()
