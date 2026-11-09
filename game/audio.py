"""Music, ambience and effects with independent channels and safe fallback."""
import json
from pathlib import Path
import pygame


class Audio:
    def __init__(self, folder):
        self.root = Path(__file__).resolve().parent / 'assets/audio'
        self.preferences = Path(folder) / 'audio.json'
        self.muted = False
        try:
            self.muted = bool(json.loads(self.preferences.read_text()).get('muted', False))
        except (OSError, ValueError, TypeError, AttributeError):
            pass
        self.enabled = bool(pygame.mixer.get_init())
        self.track = None
        self.sounds = {}
        self.hovered = None
        if self.enabled:
            pygame.mixer.set_num_channels(16)
            pygame.mixer.set_reserved(2)
            for path in self.root.glob('*.wav'):
                if path.stem not in ('menu', 'stage'):
                    self.sounds[path.stem] = pygame.mixer.Sound(str(path))

    def play(self, name):
        if self.enabled and not self.muted and name in self.sounds:
            channel = pygame.mixer.find_channel()
            if channel:
                channel.set_volume(.38 if name != 'type' else .18)
                channel.play(self.sounds[name])

    def set_state(self, state):
        if not self.enabled:
            return
        track = 'stage' if state in ('playing', 'paused', 'over') else 'menu'
        if track != self.track:
            pygame.mixer.music.load(str(self.root / (track + '.wav')))
            pygame.mixer.music.play(-1, fade_ms=350)
            self.track = track
        pygame.mixer.music.set_volume(0 if self.muted else (.10 if state == 'paused' else .23))
        ambient = pygame.mixer.Channel(1)
        if state == 'playing' and not self.muted:
            if not ambient.get_busy() and 'shore' in self.sounds:
                ambient.play(self.sounds['shore'], loops=-1)
                ambient.set_volume(.35)
        else:
            ambient.stop()

    def toggle(self):
        self.muted = not self.muted
        if self.enabled and self.muted:
            pygame.mixer.stop()
        try:
            self.preferences.write_text(json.dumps({'muted': self.muted}), encoding='utf-8')
        except OSError:
            pass
