"""Ponto de entrada do jogo Words Atack."""

import argparse
import json
import random
import sqlite3
import sys
import time
import unicodedata
import uuid
from pathlib import Path

import pygame

from game import settings as S
from game.storage import Storage
from game.rendering import Renderer


class Game:
    def __init__(self, data_dir=None):
        pygame.init()
        self.fullscreen = "--smoke-test" not in sys.argv
        self.window = pygame.display.set_mode((0, 0) if self.fullscreen else (1280, 720), pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE)
        pygame.display.set_caption(S.TITLE)
        self.canvas = pygame.Surface((S.WIDTH, S.HEIGHT))
        self.renderer = Renderer(self.canvas)
        icon = pygame.Surface((32, 32))
        icon.fill(S.BG)
        pygame.draw.rect(icon, S.CYAN, (5, 5, 22, 16), 2)
        pygame.draw.line(icon, S.RED, (8, 28), (24, 10), 3)
        pygame.display.set_icon(icon)
        self.clock = pygame.time.Clock()
        self.storage = Storage(data_dir)
        self.nickname = self.storage.config["nickname"]
        self.api_input = self.storage.config["api_url"]
        self.state = "menu"
        self.running = True
        self.message = ""
        self.effects = []
        self.shake = 0
        self.button_rects = {}
        self.ranking_rows = []
        self.attack_until = 0
        pygame.key.start_text_input()
        self.reset()

    def pointer(self, pos=None):
        width, height = self.window.get_size()
        scale = min(width / S.WIDTH, height / S.HEIGHT)
        if scale >= 1:
            scale = max(1, int(scale))
        x, y = pygame.mouse.get_pos() if pos is None else pos
        return ((x - (width - S.WIDTH * scale) / 2) / scale,
                (y - (height - S.HEIGHT * scale) / 2) / scale)

    def reset(self):
        self.enemies = []
        self.typed = ""
        self.score = 0
        self.lives = 5
        self.hits = 0
        self.attempts = 0
        self.combo = 0
        self.elapsed = 0
        self.spawn_timer = 1.1
        self.notice = ""
        self.notice_time = 0
        self.effects = []
        self.saved = False

    @property
    def level(self):
        return 1 + self.hits // 5

    @property
    def accuracy(self):
        return round(100 * self.hits / self.attempts, 1) if self.attempts else 0.0

    def start(self):
        name = self.nickname.strip()
        if not name:
            self.message = "Escolha seu nickname para defender a cidade."
            return
        try:
            self.storage.save_config(nickname=name)
        except OSError:
            self.message = "Não foi possível salvar o perfil. Verifique a pasta de dados."
            return
        self.nickname = name
        self.reset()
        self.message = ""
        self.state = "playing"
        self.storage.sync()

    def spawn(self):
        # Mantém espaço entre inimigos da mesma coluna.
        lanes = [x for x in S.LANES if not any(e["x"] == x and e["y"] < 178 for e in self.enemies)]
        maximum = min(9, 5 + self.level // 2)
        used = {e["word"] for e in self.enemies}
        words = [word for word in S.WORDS if len(word) <= maximum and word not in used]
        if not lanes or not words:
            return
        self.enemies.append({"word": random.choice(words), "x": random.choice(lanes),
                             "y": 112.0, "speed": min(78, 24 + self.level * 4) + random.uniform(0, 5)})
        self.attack_until = time.monotonic() + .8

    def shoot(self):
        if not self.typed:
            return
        self.attempts += 1
        target = next((enemy for enemy in self.enemies if enemy["word"] == self.typed), None)
        if target:
            self.enemies.remove(target)
            self.hits += 1
            self.combo += 1
            multiplier = min(4, 1 + (self.combo - 1) // 5)
            gained = len(target["word"]) * 10 * multiplier
            self.score += gained
            self.effects.append({"kind": "laser", "x": target["x"], "y": target["y"], "life": .3, "label": f"+{gained}"})
            self.notice = f"Alvo eliminado! Combo {self.combo} · multiplicador x{multiplier}"
        else:
            self.combo = 0
            self.notice = "Alvo não encontrado. Confira a palavra e tente outra vez."
        self.notice_time = 1.6
        self.typed = ""

    def finish(self):
        self.state = "over"
        if self.saved:
            return
        self.saved = True
        record = {"id": str(uuid.uuid4()), "nickname": self.nickname,
                  "score": self.score, "words": self.hits, "accuracy": self.accuracy,
                  "duration": round(self.elapsed, 2), "level": self.level}
        try:
            self.storage.save_run(record)
            self.storage.sync()
            self.message = "Partida salva no ranking local."
        except (OSError, sqlite3.Error):
            self.message = "Falha ao salvar a partida. Verifique o espaço em disco."

    def open_ranking(self):
        self.ranking_rows = self.storage.ranking()
        self.state = "ranking"
        self.storage.sync()

    def save_settings(self):
        try:
            self.storage.save_config(api_url=self.api_input)
            self.message = "Configuração salva."
            self.storage.sync()
            self.state = "menu"
        except (ValueError, OSError) as error:
            self.message = str(error)

    def action(self, key):
        if key in ("start", "retry"):
            self.start()
        elif key == "ranking":
            self.open_ranking()
        elif key == "settings":
            self.api_input = self.storage.config["api_url"]
            self.message = ""
            self.state = "settings"
        elif key == "menu":
            self.state = "menu"
            self.message = ""
        elif key == "resume":
            self.state = "playing"
        elif key == "save":
            self.save_settings()
        elif key == "quit":
            self.running = False

    def handle(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.fullscreen = not self.fullscreen
            self.window = pygame.display.set_mode((0, 0) if self.fullscreen else (1280, 720), pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE)
            return
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.WINDOWFOCUSLOST and self.state == "playing":
            self.state = "paused"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, rect in self.button_rects.items():
                if rect.collidepoint(self.pointer(event.pos)):
                    self.action(key)
                    break
        elif event.type == pygame.TEXTINPUT:
            if self.state == "menu":
                cleaned = "".join(c for c in event.text if c.isprintable())
                self.nickname = (self.nickname + cleaned)[:18]
            elif self.state == "settings":
                self.api_input = (self.api_input + "".join(c for c in event.text if c.isprintable()))[:250]
            elif self.state == "playing":
                normalized = unicodedata.normalize("NFD", event.text.lower())
                self.typed = (self.typed + "".join(c for c in normalized if "a" <= c <= "z"))[:24]
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == "playing":
                    self.state = "paused"
                elif self.state == "paused":
                    self.state = "playing"
                elif self.state != "menu":
                    self.state = "menu"
                    self.message = ""
            elif event.key == pygame.K_BACKSPACE:
                if self.state == "menu":
                    self.nickname = self.nickname[:-1]
                elif self.state == "settings":
                    self.api_input = self.api_input[:-1]
                elif self.state == "playing":
                    self.typed = self.typed[:-1]
            elif event.key == pygame.K_F2 and self.state == "menu":
                self.action("settings")
            elif event.key == pygame.K_RETURN:
                if self.state == "menu":
                    self.start()
                elif self.state == "playing":
                    self.shoot()
                elif self.state == "paused":
                    self.state = "playing"
                elif self.state == "over":
                    self.start()
                elif self.state == "settings":
                    self.save_settings()

    def update(self, dt):
        if self.state != "playing":
            return
        self.elapsed += dt
        self.spawn_timer -= dt
        self.notice_time = max(0, self.notice_time - dt)
        self.shake = max(0, self.shake - dt)
        if self.spawn_timer <= 0:
            self.spawn()
            self.spawn_timer = max(.72, 2.5 - self.level * .14)
        for enemy in self.enemies[:]:
            enemy["y"] += enemy["speed"] * dt
            if enemy["y"] + 20 >= S.BASE_Y:
                self.enemies.remove(enemy)
                self.lives -= 1
                self.combo = 0
                self.shake = .3
                self.effects.append({"kind": "impact", "x": enemy["x"], "y": S.BASE_Y, "life": .45})
                self.notice = "Impacto! A casa perdeu um ponto de integridade."
                self.notice_time = 1.7
                if self.lives <= 0:
                    self.finish()
                    break
        for effect in self.effects:
            effect["life"] -= dt
        self.effects = [effect for effect in self.effects if effect["life"] > 0]

    def draw(self):
        self.renderer.draw(self)
        width, height = self.window.get_size()
        scale = min(width / S.WIDTH, height / S.HEIGHT)
        if scale >= 1:
            scale = max(1, int(scale))
        size = (max(1, int(S.WIDTH * scale)), max(1, int(S.HEIGHT * scale)))
        image = pygame.transform.scale(self.canvas, size)
        self.window.fill((0, 0, 0))
        self.window.blit(image, ((width - size[0]) // 2, (height - size[1]) // 2))
        pygame.display.flip()

    def run(self):
        try:
            while self.running:
                dt = min(self.clock.tick(S.FPS) / 1000, .05)
                for event in pygame.event.get():
                    self.handle(event)
                self.update(dt)
                self.draw()
        finally:
            pygame.quit()


def main():
    parser = argparse.ArgumentParser(description="Words Atack — defesa por digitação")
    parser.add_argument("--data-dir", help="Pasta alternativa para configuração e partidas")
    parser.add_argument("--smoke-test", metavar="PASTA", help="Gera capturas e relatório e encerra")
    args = parser.parse_args()
    game = Game(args.data_dir)
    if args.smoke_test:
        folder = Path(args.smoke_test)
        folder.mkdir(parents=True, exist_ok=True)
        game.nickname = "Defensor"
        game.draw()
        pygame.image.save(game.canvas, str(folder / "menu.png"))
        game.start()
        for index, word in enumerate(("laser", "python", "dados", "pixel", "rede")):
            game.enemies.append({"word": word, "x": S.LANES[index], "y": 128 + index % 3 * 38, "speed": 30})
        game.typed = "py"
        game.draw()
        pygame.image.save(game.canvas, str(folder / "gameplay.png"))
        for state in ("paused", "over", "settings", "ranking"):
            game.state = state
            game.draw()
            pygame.image.save(game.canvas, str(folder / (state + ".png")))
        (folder / "smoke-test.json").write_text(json.dumps({"ok": True, "version": S.VERSION, "frozen": bool(getattr(sys, "frozen", False)), "screens": 6}), encoding="utf-8")
        pygame.quit()
    else:
        game.run()


if __name__ == "__main__":
    main()
