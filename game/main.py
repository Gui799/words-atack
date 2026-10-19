"""Ponto de entrada do jogo. Gráficos vetoriais provisórios, sem assets externos."""

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


class Game:
    def __init__(self, data_dir=None):
        pygame.init()
        self.window = pygame.display.set_mode((S.WIDTH, S.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption(S.TITLE)
        self.canvas = pygame.Surface((S.WIDTH, S.HEIGHT))
        icon = pygame.Surface((32, 32))
        icon.fill(S.BG)
        pygame.draw.rect(icon, S.CYAN, (5, 5, 22, 16), 2)
        pygame.draw.line(icon, S.RED, (8, 28), (24, 10), 3)
        pygame.display.set_icon(icon)
        self.clock = pygame.time.Clock()
        self.fonts = {}
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
        self.stars = [(random.randrange(1100), random.randrange(80, 580), random.randint(1, 2)) for _ in range(70)]
        self.buildings = [(x, random.randrange(60, 145), random.randrange(35, 63)) for x in range(0, 1100, 62)]
        pygame.key.start_text_input()
        self.reset()

    def font(self, size):
        if size not in self.fonts:
            # Fonte distribuída com o Pygame, incluída no executável.
            self.fonts[size] = pygame.font.Font(None, size)
        return self.fonts[size]

    def text(self, label, x, y, size=26, color=S.INK, center=False):
        rendered = self.font(size).render(str(label), True, color)
        rect = rendered.get_rect(center=(x, y)) if center else rendered.get_rect(topleft=(x, y))
        self.canvas.blit(rendered, rect)
        return rect

    def panel(self, rect, fill=S.PANEL, border=None, radius=14):
        pygame.draw.rect(self.canvas, fill, rect, border_radius=radius)
        if border:
            pygame.draw.rect(self.canvas, border, rect, width=1, border_radius=radius)

    def button(self, key, label, rect, primary=False):
        rect = pygame.Rect(rect)
        self.button_rects[key] = rect
        hover = rect.collidepoint(self.pointer())
        fill = S.CYAN if primary else (28, 46, 62)
        if hover:
            fill = (135, 255, 225) if primary else (42, 64, 81)
        self.panel(rect, fill)
        self.text(label, rect.centerx, rect.centery, 25, S.BG if primary else S.INK, True)

    def pointer(self, pos=None):
        width, height = self.window.get_size()
        scale = min(width / S.WIDTH, height / S.HEIGHT)
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
        lanes = [x for x in S.LANES if not any(e["x"] == x and e["y"] < 320 for e in self.enemies)]
        maximum = min(9, 5 + self.level // 2)
        used = {e["word"] for e in self.enemies}
        words = [word for word in S.WORDS if len(word) <= maximum and word not in used]
        if not lanes or not words:
            return
        self.enemies.append({"word": random.choice(words), "x": random.choice(lanes),
                             "y": 247.0, "speed": min(78, 24 + self.level * 4) + random.uniform(0, 5)})

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

    def scene(self, active=False):
        self.canvas.fill(S.BG)
        for x, y, radius in self.stars:
            pygame.draw.circle(self.canvas, (57, 78, 101), (x, y), radius)
        # Cidade ao fundo, com janelas acesas.
        for x, height, width in self.buildings:
            pygame.draw.rect(self.canvas, (22, 38, 53), (x, S.BASE_Y - height, width, height))
            for wx in range(x + 8, x + width - 5, 15):
                for wy in range(S.BASE_Y - height + 12, S.BASE_Y - 10, 22):
                    pygame.draw.rect(self.canvas, (57, 91, 98), (wx, wy, 4, 7))
        # Computador gigante: inimigo principal e origem das palavras.
        self.panel((365, 97, 370, 129), (33, 44, 61), (64, 83, 104), 20)
        self.panel((382, 110, 336, 96), (12, 27, 35), S.RED, 9)
        pygame.draw.line(self.canvas, S.RED, (456, 140), (489, 151), 7)
        pygame.draw.line(self.canvas, S.RED, (611, 140), (578, 151), 7)
        self.text("WORD // OVERLORD", 550, 182, 21, S.RED, True)
        pygame.draw.rect(self.canvas, (50, 68, 82), (533, 226, 34, 13))
        pygame.draw.line(self.canvas, S.RED, (415, 239), (685, 239), 3)
        if not active:
            self.text("AMEAÇA DIGITAL DETECTADA", 550, 72, 19, S.RED, True)
        # Escudo urbano e casa do jogador.
        pygame.draw.line(self.canvas, S.CYAN if not self.shake else S.RED, (0, S.BASE_Y), (1100, S.BASE_Y), 2)
        pygame.draw.rect(self.canvas, (28, 58, 63), (468, 550, 164, 43))
        pygame.draw.polygon(self.canvas, (42, 91, 92), [(452, 551), (550, 508), (648, 551)])
        pygame.draw.rect(self.canvas, S.YELLOW, (486, 561, 19, 17))
        pygame.draw.rect(self.canvas, S.YELLOW, (596, 561, 19, 17))
        pygame.draw.rect(self.canvas, (19, 37, 46), (536, 560, 28, 33))
        pygame.draw.circle(self.canvas, (36, 108, 105), (550, 532), 18)
        pygame.draw.line(self.canvas, S.CYAN, (550, 535), (550, 496), 9)

    def draw_play(self):
        self.scene(True)
        self.panel((20, 16, 1060, 60), (16, 28, 43))
        self.text(self.nickname, 38, 29, 25, S.CYAN)
        self.text(f"{self.score:06d}", 280, 24, 39)
        self.text(f"NÍVEL {self.level:02d}", 475, 33, 23, S.YELLOW)
        self.text(f"CASA {'| ' * self.lives}", 660, 33, 25, S.CYAN if self.lives > 2 else S.RED)
        self.text("ESC  pausar", 946, 34, 21, S.MUTED)
        for x in S.LANES:
            for y in range(271, 560, 22):
                pygame.draw.line(self.canvas, (21, 35, 49), (x, y), (x, y + 7))
        for enemy in self.enemies:
            matched = bool(self.typed) and enemy["word"].startswith(self.typed)
            color = S.CYAN if matched else S.RED
            width = max(100, self.font(29).size(enemy["word"])[0] + 30)
            rect = pygame.Rect(0, 0, width, 43)
            rect.center = (int(enemy["x"]), int(enemy["y"]))
            self.panel(rect, (25, 41, 53), color, 9)
            self.text(enemy["word"], *rect.center, 29, color, True)
            pygame.draw.polygon(self.canvas, color, [(rect.centerx - 5, rect.bottom + 3), (rect.centerx + 5, rect.bottom + 3), (rect.centerx, rect.bottom + 9)])
        for effect in self.effects:
            point = (int(effect["x"]), int(effect["y"]))
            if effect["kind"] == "laser":
                pygame.draw.line(self.canvas, S.CYAN, (550, 496), point, 5)
                pygame.draw.circle(self.canvas, S.INK, point, int(7 + effect["life"] * 30), 2)
                self.text(effect["label"], point[0], point[1] - 35, 28, S.CYAN, True)
            else:
                pygame.draw.circle(self.canvas, S.RED, point, int(8 + (.45 - effect["life"]) * 85), 3)
        self.panel((20, 611, 1060, 128), S.PANEL)
        self.text("TERMINAL DE DEFESA", 40, 625, 19, S.MUTED)
        self.panel((39, 650, 700, 55), (8, 19, 30), S.CYAN)
        cursor = "_" if time.monotonic() % 1 < .55 else ""
        self.text("> " + self.typed + cursor, 55, 662, 35, S.CYAN)
        self.text("ENTER  disparar", 765, 657, 25, S.CYAN)
        self.text(f"Precisão {self.accuracy:.0f}%  ·  Combo {self.combo}", 765, 691, 20, S.MUTED)
        label = self.notice if self.notice_time else "Digite uma palavra visível e pressione ENTER. BACKSPACE corrige."
        self.text(label, 40, 717, 20, S.YELLOW if self.notice_time else S.MUTED)

    def draw_menu(self):
        self.scene()
        self.panel((147, 260, 806, 446), (15, 26, 41), (43, 68, 82), 22)
        self.text("WORDS", 550, 307, 68, S.INK, True)
        self.text("ATACK", 550, 362, 72, S.CYAN, True)
        self.text("Sua casa. Seu teclado. A última linha de defesa.", 550, 413, 27, S.INK, True)
        self.text("Um computador gigante tomou a cidade e está lançando palavras digitais.", 550, 446, 22, S.MUTED, True)
        self.text("O governo entregou seu canhão laser. Digite para proteger sua casa.", 550, 472, 22, S.MUTED, True)
        self.text("IDENTIFICAÇÃO DO DEFENSOR", 285, 507, 19, S.MUTED)
        self.panel((280, 533, 540, 49), (8, 19, 30), S.CYAN)
        cursor = "_" if time.monotonic() % 1 < .55 else ""
        self.text(self.nickname + cursor, 299, 545, 29, S.CYAN)
        self.button("start", "DEFENDER A CASA  /  ENTER", (280, 599, 540, 48), True)
        self.button("ranking", "Ranking local", (280, 661, 169, 32))
        self.button("settings", "Servidor / F2", (462, 661, 176, 32))
        self.button("quit", "Sair", (651, 661, 169, 32))
        self.text(self.message or "Digite seu nickname acima · até 18 caracteres", 550, 721, 20, S.YELLOW if self.message else S.MUTED, True)
        self.text(f"PRÉVIA {S.VERSION}", 24, 24, 19, S.MUTED)

    def overlay(self, heading, subheading):
        self.draw_play()
        shade = pygame.Surface((1100, 760), pygame.SRCALPHA)
        shade.fill((3, 9, 16, 225))
        self.canvas.blit(shade, (0, 0))
        self.panel((225, 195, 650, 400), S.PANEL, (50, 78, 92), 22)
        self.text(heading, 550, 247, 49, S.CYAN, True)
        self.text(subheading, 550, 295, 24, S.MUTED, True)

    def draw_ranking(self):
        self.scene()
        self.panel((140, 260, 820, 442), S.PANEL, (43, 68, 82))
        self.text("DEFENSORES DA CIDADE", 550, 292, 38, S.CYAN, True)
        self.text("Ranking deste computador · melhores partidas", 550, 329, 22, S.MUTED, True)
        self.text("#     DEFENSOR", 175, 369, 20, S.MUTED)
        self.text("PONTOS", 590, 369, 20, S.MUTED)
        self.text("PRECISÃO", 739, 369, 20, S.MUTED)
        if not self.ranking_rows:
            self.text("A cidade ainda espera seu primeiro defensor.", 550, 461, 26, S.INK, True)
        for index, row in enumerate(self.ranking_rows):
            y = 407 + index * 28
            self.text(f"{index + 1:02d}    {row['nickname']}", 175, y, 25)
            self.text(f"{row['score']:06d}", 590, y, 25, S.CYAN)
            self.text(f"{row['accuracy']:.0f}%", 759, y, 25)
        self.button("menu", "Voltar / ESC", (400, 649, 300, 37))
        self.text(self.storage.status, 550, 724, 20, S.MUTED, True)

    def draw_settings(self):
        self.scene()
        self.panel((110, 260, 880, 442), S.PANEL, (43, 68, 82))
        self.text("CONEXÃO COM O RANKING", 550, 302, 39, S.CYAN, True)
        self.text("O jogo funciona offline. O servidor permite compartilhar as partidas.", 550, 350, 24, S.INK, True)
        self.text("URL do servidor Flask · deixe vazio para usar apenas o ranking local", 150, 398, 22, S.MUTED)
        self.panel((150, 434, 800, 52), (8, 19, 30), S.CYAN)
        displayed = self.api_input
        while self.font(25).size(displayed)[0] > 755:
            displayed = displayed[1:]
        self.text(displayed + "_", 165, 450, 25, S.CYAN)
        self.text("Exemplo local: http://127.0.0.1:5000", 150, 506, 23, S.MUTED)
        self.text("Partidas pendentes são reenviadas ao iniciar ou concluir uma partida.", 150, 543, 22, S.MUTED)
        self.button("save", "Salvar / ENTER", (220, 608, 310, 48), True)
        self.button("menu", "Cancelar / ESC", (560, 608, 310, 48))
        self.text(self.message, 550, 724, 20, S.YELLOW, True)

    def draw(self):
        self.button_rects = {}
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "ranking":
            self.draw_ranking()
        elif self.state == "settings":
            self.draw_settings()
        elif self.state == "playing":
            self.draw_play()
        elif self.state == "paused":
            self.overlay("DEFESA EM PAUSA", "Respire. A cidade espera seu retorno.")
            self.button("resume", "Continuar / ENTER", (350, 361, 400, 50), True)
            self.button("menu", "Abandonar e voltar ao menu", (350, 434, 400, 48))
            self.text("Partidas abandonadas não entram no ranking.", 550, 536, 22, S.MUTED, True)
        elif self.state == "over":
            self.overlay("SINAL INTERROMPIDO", f"{self.nickname}, sua defesa entrou para a história.")
            self.text(f"{self.score:06d}", 550, 358, 66, S.INK, True)
            self.text(f"{self.hits} palavras  ·  {self.accuracy:.0f}% precisão  ·  nível {self.level}", 550, 412, 26, S.YELLOW, True)
            self.button("retry", "Defender novamente / ENTER", (315, 458, 470, 47), True)
            self.button("ranking", "Ranking local", (315, 522, 225, 40))
            self.button("menu", "Menu", (560, 522, 225, 40))
            self.text(self.message, 550, 628, 23, S.INK, True)
            self.text(self.storage.status, 550, 663, 20, S.MUTED, True)
        width, height = self.window.get_size()
        scale = min(width / 1100, height / 760)
        size = (max(1, int(1100 * scale)), max(1, int(760 * scale)))
        image = pygame.transform.smoothscale(self.canvas, size)
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
            game.enemies.append({"word": word, "x": S.LANES[index], "y": 320 + index % 3 * 65, "speed": 30})
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
