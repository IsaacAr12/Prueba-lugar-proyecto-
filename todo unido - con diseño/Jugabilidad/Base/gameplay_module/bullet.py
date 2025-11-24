
# -*- coding: utf-8 -*-
import pygame

DEFAULT_SHOT_WAV = "assets/sounds/shot.wav"


class Bullet(pygame.sprite.Sprite):
    WIDTH = 4
    HEIGHT = 12

    def __init__(self, x, y, speed=-12, color=(255, 255, 0), shoot_sound_path=None):
        super().__init__()
        self.image = pygame.Surface((Bullet.WIDTH, Bullet.HEIGHT), pygame.SRCALPHA)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_y = speed
        self.shoot_sound = self._load_sound(shoot_sound_path or DEFAULT_SHOT_WAV, volume=0.3)
        if self.shoot_sound:
            try:
                self.shoot_sound.play()
            except Exception:
                pass

    def _load_sound(self, path, volume=0.3):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            s = pygame.mixer.Sound(path)
            s.set_volume(volume)
            return s
        except Exception:
            return None

    def update(self, *args):
        self.rect.y += self.speed_y
        if self.rect.bottom < 0:
            self.kill()
