"""Pixel-art renderer and animation playback for Words Atack."""

from pathlib import Path
import time

import pygame

from game import settings as S


class Renderer:
    NAVY = (28, 48, 78)
    CREAM = (255, 248, 188)
    SAND = (246, 216, 121)
    TEAL = (23, 151, 150)
    SEA = (45, 195, 197)
    CORAL = (240, 82, 80)
    YELLOW = (255, 219, 83)
    WHITE = (255, 255, 233)
    MUTED = (80, 111, 120)

    def __init__(self, canvas):
        self.canvas = canvas
        self.root = Path(__file__).resolve().parent / "assets"
        self.started = time.monotonic()
        pygame.mouse.set_visible(False)

        self.background = self._image("backgrounds/praia_dia.png")
        self.background = pygame.transform.scale(self.background, (S.WIDTH, S.HEIGHT))
        self.ui_panel = self._image("ui/painel.png", alpha=True)
        self.ui_button = self._image("ui/botao.png", alpha=True)
        self.cursor = self._trim(self._image("ui/cursor.png", alpha=True), (16, 16))

        self.computer = self._sheet("animations/computador_sheet.png", 4, 2, (96, 64))
        hearts = self._sheet("ui/vidas_sheet.png", 2, 1, (8, 8))
        self.heart_full = hearts[0]
        self.heart_empty = hearts[1]
        self.waves = self._sheet("animations/ondas_sheet.png", 2, 2, (64, 32))
        self.shots = self._sheet("animations/tiro_sheet.png", 4, 1, (16, 16))
        self.word_frames = self._sheet("animations/palavra_inimiga_sheet.png", 3, 1, (96, 24))

        self.house = self._trim(self._image("sprites/casa.png", alpha=True), (78, 48))
        self.cannon = self._trim(self._image("sprites/canhao_laser.png", alpha=True), (24, 32))
        self.cannon = pygame.transform.flip(self.cannon, True, False)
        font_path = self.root / "fonts" / "Tiny5.ttf"
        self.fonts = {size: pygame.font.Font(str(font_path), size) for size in (10, 12, 14, 16, 20, 25)}

    def _image(self, relative, alpha=False):
        image = pygame.image.load(str(self.root / relative))
        return image.convert_alpha() if alpha else image.convert()

    @staticmethod
    def _trim(image, size):
        bounds = image.get_bounding_rect()
        if bounds.width and bounds.height:
            image = image.subsurface(bounds).copy()
        return Renderer._fit(image, size)

    @staticmethod
    def _fit(image, size):
        scale = min(size[0] / image.get_width(), size[1] / image.get_height())
        dimensions = (max(1, round(image.get_width()*scale)), max(1, round(image.get_height()*scale)))
        result = pygame.Surface(size, pygame.SRCALPHA)
        scaled = pygame.transform.scale(image, dimensions)
        result.blit(scaled, scaled.get_rect(center=result.get_rect().center))
        return result

    def _sheet(self, relative, columns, rows, frame_size):
        sheet = self._image(relative, alpha=True)
        source_w = sheet.get_width() // columns
        source_h = sheet.get_height() // rows
        frames = []
        for row in range(rows):
            for column in range(columns):
                frame = sheet.subsurface((column * source_w, row * source_h, source_w, source_h)).copy()
                frames.append(frame)
        bounds = pygame.Rect(0, 0, 0, 0)
        for frame in frames:
            for rect in pygame.mask.from_surface(frame, 127).get_bounding_rects():
                bounds = rect if not bounds.width else bounds.union(rect)
        if not bounds.width:
            bounds = frames[0].get_rect()
        return [self._fit(frame.subsurface(bounds), frame_size) for frame in frames]

    def _text(self, label, center, size=14, color=None):
        color = color or self.NAVY
        font = self.fonts.get(size) or pygame.font.Font(str(self.root / "fonts" / "Tiny5.ttf"), size)
        image = font.render(str(label), False, color)
        self.canvas.blit(image, image.get_rect(center=center))

    def _slice(self, image, rect, source_border=68, target_border=5):
        """Draw a panel/button with corners preserved and stretchable edges."""
        x, y, width, height = map(int, rect)
        sw, sh = image.get_size()
        sb = min(source_border, sw // 3, sh // 3)
        tb = min(target_border, width // 3, height // 3)
        src_x = (0, sb, sw - sb, sw)
        src_y = (0, sb, sh - sb, sh)
        dst_x = (x, x + tb, x + width - tb, x + width)
        dst_y = (y, y + tb, y + height - tb, y + height)
        for row in range(3):
            for col in range(3):
                source = pygame.Rect(src_x[col], src_y[row], src_x[col + 1] - src_x[col], src_y[row + 1] - src_y[row])
                dest = pygame.Rect(dst_x[col], dst_y[row], dst_x[col + 1] - dst_x[col], dst_y[row + 1] - dst_y[row])
                if source.width and source.height and dest.width and dest.height:
                    piece = image.subsurface(source)
                    self.canvas.blit(pygame.transform.scale(piece, dest.size), dest)

    def panel(self, rect):
        self._slice(self.ui_panel, rect)

    def button(self, game, key, label, rect, primary=False):
        rect = pygame.Rect(rect)
        game.button_rects[key] = rect
        hover = rect.collidepoint(game.pointer())
        draw_rect = rect.move(0, -1 if hover else 1)
        self._slice(self.ui_button, draw_rect, source_border=82, target_border=5)
        color = self.CORAL if hover else self.NAVY
        if primary:
            color = self.TEAL if not hover else self.CORAL
        self._text(label, rect.center, 14, color)

    def _cloud(self, x, y, scale=1):
        s = scale
        pixels = [
            (0, 7, 13, 7), (8, 2, 17, 12), (18, 0, 18, 14),
            (29, 4, 14, 10), (7, 11, 37, 6),
        ]
        for index, (dx, dy, width, height) in enumerate(pixels):
            color = (206, 227, 221) if index == 4 else self.WHITE
            pygame.draw.rect(self.canvas, color, (int(x + dx*s), int(y + dy*s), int(width*s), int(height*s)))

    def scene(self, game, active=False):
        now = time.monotonic() - self.started
        self.canvas.blit(self.background, (0, 0))

        # Animated cloud layers drift at different speeds over the daytime sky.
        for index, (speed, y, scale, offset) in enumerate(((7, 15, 1, 30), (4, 47, 0.7, 290), (5, 30, 0.8, 510))):
            x = int((now * speed + offset) % (S.WIDTH + 90)) - 55
            self._cloud(x, y, scale)

        # The 4-frame water sheet animates the shoreline in a loop.
        wave_frame = int(now * 7) % len(self.waves)
        wave = self.waves[wave_frame]
        for x in range(-64, S.WIDTH, 64):
            self.canvas.blit(wave, (x + int((now * 8) % 16), 216))

        # Computer idle/attack rows, 4 frames each.
        attacking = time.monotonic() < getattr(game, "attack_until", 0)
        row = 1 if attacking else 0
        frame = int(now * (12 if attacking else 2.3)) % 4
        computer = self.computer[row * 4 + frame]
        self.canvas.blit(computer, computer.get_rect(midtop=(S.WIDTH // 2, 44)))

        # House and the player's cannon sit on the sunlit sand.
        self.canvas.blit(self.house, (457, 236))
        self.canvas.blit(self.cannon, (483, 226))

        if not active:
            self._text("DEFENDA SUA CASA!", (S.WIDTH // 2, 90), 16, self.CORAL)

    def _hud(self, game):
        self.panel((8, 7, 624, 34))
        self._text(game.nickname[:12], (62, 24), 14, self.TEAL)
        self._text(f"PONTOS {game.score:05d}", (260, 24), 14, self.NAVY)
        self._text(f"NÍVEL {game.level}", (410, 24), 12, self.CORAL)
        for index in range(5):
            heart = self.heart_full if index < game.lives else self.heart_empty
            self.canvas.blit(heart, (542 + index * 15, 20))
        self._text("ESC", (612, 24), 10, self.NAVY)

    def draw_play(self, game):
        self.scene(game, True)
        self._hud(game)
        now = time.monotonic() - self.started

        for enemy in game.enemies:
            matched = bool(game.typed) and enemy["word"].startswith(game.typed)
            width = min(148, max(72, self.fonts[14].size(enemy["word"])[0] + 20))
            card = pygame.transform.scale(self.word_frames[int(now * 8) % 3], (width, 24))
            rect = card.get_rect(center=(int(enemy["x"]), int(enemy["y"])))
            self.canvas.blit(card, rect)
            self._text(enemy["word"], rect.center, 14, self.TEAL if matched else self.CORAL)

        for effect in game.effects:
            point = (int(effect["x"]), int(effect["y"]))
            if effect["kind"] == "laser":
                start = (495, 238)
                pygame.draw.line(self.canvas, self.TEAL, start, point, 2)
                shot = self.shots[int(max(0, effect["life"]) * 14) % len(self.shots)]
                self.canvas.blit(shot, shot.get_rect(center=point))
                self._text(effect["label"], (point[0], point[1] - 15), 12, self.CORAL)
            else:
                pygame.draw.rect(self.canvas, self.CORAL, (point[0]-5, point[1]-5, 10, 3))
                pygame.draw.rect(self.canvas, self.YELLOW, (point[0]+3, point[1]-1, 4, 4))
                pygame.draw.rect(self.canvas, self.CORAL, (point[0]-2, point[1]+3, 4, 3))

        self.panel((112, 303, 416, 38))
        self._text("TERMINAL", (155, 311), 10, self.MUTED)
        cursor = "_" if int(time.monotonic() * 2) % 2 == 0 else ""
        self._text("> " + game.typed + cursor, (320, 326), 20, self.TEAL)
        message = game.notice if game.notice_time else "Digite a palavra e pressione ENTER"
        self._text(message[:54], (320, 352), 10, self.CORAL if game.notice_time else self.NAVY)

    def draw_menu(self, game):
        self.scene(game)
        self.panel((72, 88, 496, 250))
        self._text("WORDS", (320, 117), 25, self.NAVY)
        self._text("ATACK!", (320, 145), 25, self.CORAL)
        self._text("A cidade precisa de você", (320, 170), 12, self.TEAL)
        self._text("Digite seu nickname:", (320, 195), 12, self.NAVY)
        self.panel((220, 204, 200, 26))
        cursor = "_" if int(time.monotonic() * 2) % 2 == 0 else ""
        self._text((game.nickname or "Defensor") + cursor, (320, 217), 14, self.TEAL)
        self.button(game, "start", "JOGAR", (243, 239, 154, 34), True)
        self.button(game, "ranking", "RANKING", (100, 282, 126, 32))
        self.button(game, "settings", "AJUSTES", (235, 282, 140, 32))
        self.button(game, "quit", "SAIR", (384, 282, 156, 32))
        if game.message:
            self._text(game.message[:42], (320, 327), 10, self.CORAL)

    def draw_overlay(self, game, heading, description):
        self.draw_play(game)
        shade = pygame.Surface((S.WIDTH, S.HEIGHT), pygame.SRCALPHA)
        shade.fill((20, 44, 67, 150))
        self.canvas.blit(shade, (0, 0))
        self.panel((120, 105, 400, 170))
        self._text(heading, (320, 133), 20, self.CORAL)
        self._text(description, (320, 159), 12, self.NAVY)

    def draw_ranking(self, game):
        self.scene(game)
        self.panel((72, 62, 496, 266))
        self._text("RANKING DOS DEFENSORES", (320, 88), 20, self.NAVY)
        self._text("#  NICKNAME                         PONTOS", (320, 119), 12, self.TEAL)
        if not game.ranking_rows:
            self._text("Ainda não há partidas salvas.", (320, 182), 14, self.NAVY)
        for index, row in enumerate(game.ranking_rows[:5]):
            self._text(f"{index+1}. {row['nickname'][:14]}", (180, 145 + index*24), 12, self.NAVY)
            self._text(f"{row['score']:05d}    {row['accuracy']:.0f}%", (438, 145 + index*24), 12, self.CORAL)
        self.button(game, "menu", "VOLTAR", (242, 270, 156, 34))

    def draw_settings(self, game):
        self.scene(game)
        self.panel((80, 69, 480, 246))
        self._text("AJUSTES DO RANKING", (320, 96), 20, self.NAVY)
        self._text("URL do servidor (vazio = modo local):", (320, 137), 12, self.TEAL)
        self.panel((110, 157, 420, 32))
        displayed = game.api_input
        while self.fonts[10].size(displayed)[0] > 390:
            displayed = displayed[1:]
        self._text(displayed + "_", (320, 173), 10, self.NAVY)
        self._text("Exemplo: http://127.0.0.1:5000", (320, 209), 10, self.MUTED)
        self.button(game, "save", "SALVAR", (168, 249, 136, 34), True)
        self.button(game, "menu", "CANCELAR", (315, 249, 156, 34))
        if game.message:
            self._text(game.message[:54], (320, 300), 10, self.CORAL)

    def draw(self, game):
        game.button_rects = {}
        if game.state == "menu":
            self.draw_menu(game)
        elif game.state == "playing":
            self.draw_play(game)
        elif game.state == "ranking":
            self.draw_ranking(game)
        elif game.state == "settings":
            self.draw_settings(game)
        elif game.state == "paused":
            self.draw_overlay(game, "PAUSADO", "A cidade espera sua volta.")
            self.button(game, "resume", "CONTINUAR", (243, 187, 154, 34), True)
            self.button(game, "menu", "MENU", (243, 228, 154, 32))
        elif game.state == "over":
            self.draw_overlay(game, "FIM DE JOGO", f"{game.nickname}: {game.score:05d} pontos")
            self._text(f"{game.hits} palavras  ·  {game.accuracy:.0f}% precisão", (320, 180), 12, self.TEAL)
            self.button(game, "retry", "JOGAR DE NOVO", (226, 207, 188, 36), True)
            self.button(game, "ranking", "RANKING", (248, 250, 144, 32))

        # Custom pixel reticle follows the mouse in logical canvas coordinates.
        pointer = game.pointer()
        self.canvas.blit(self.cursor, (int(pointer[0] - 8), int(pointer[1] - 8)))
