import pygame
import os
from pygame import Rect

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(_script_dir)))
ASSET_BASE = os.path.join(_project_root, "Jugabilidad/Base")

DEFAULT_IMG = os.path.join(ASSET_BASE, "assets/images/player_ship.png")
DEFAULT_MOVE_WAV = os.path.join(ASSET_BASE, "assets/sounds/move.wav")
DEFAULT_SHOT_WAV = os.path.join(ASSET_BASE, "assets/sounds/shot.wav")


class Nave(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=5, image_path=None, move_sound_path=None, shot_sound_path=None):
        super().__init__()
        img_path = self._resolve_image_path(image_path)
        self.image = self._load_ship(img_path)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed
        self.move_sound = self._load_sound(move_sound_path or DEFAULT_MOVE_WAV, volume=0.28)
        self.shot_sound = self._load_sound(shot_sound_path or DEFAULT_SHOT_WAV, volume=0.3)
        self._move_sound_cooldown_ms = 100
        self._last_move_sound_time = 0

    def _resolve_image_path(self, image_path):
        candidate = (image_path or "").strip()
        if candidate:
            expanded = os.path.expanduser(candidate)
            if not os.path.isabs(expanded):
                expanded = os.path.join(_project_root, expanded)
            if os.path.isfile(expanded):
                return expanded
        if os.path.isfile(DEFAULT_IMG):
            return DEFAULT_IMG
        alt = os.path.join(_project_root, "assets", "images", "player_ship.png")
        if os.path.isfile(alt):
            return alt
        return None

    def _load_ship(self, path):
        try:
            if path and os.path.isfile(path):
                img = pygame.image.load(path).convert_alpha()
                print(f"✓ Imagen cargada: {path}")
                return img
        except Exception as e:
            print(f"✗ No se pudo cargar imagen {path}: {e}")
        print(f"   Usando sprite generado por código")
        surf = pygame.Surface((44, 44), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (220, 240, 255), [(22, 2), (34, 20), (28, 20), (28, 30), (16, 30), (16, 20), (10, 20)])
        pygame.draw.rect(surf, (240, 70, 70), pygame.Rect(20, 24, 8, 10))
        pygame.draw.rect(surf, (70, 140, 255), pygame.Rect(12, 22, 6, 6))
        pygame.draw.rect(surf, (70, 140, 255), pygame.Rect(26, 22, 6, 6))
        return surf

    def _load_sound(self, path, volume=0.3):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            s = pygame.mixer.Sound(path)
            s.set_volume(volume)
            print(f"✓ Sonido cargado: {path}")
            return s
        except Exception as e:
            print(f"✗ No se pudo cargar sonido {path}: {e}")
            return None

    def _play_move_sound(self):
        if self.move_sound:
            now = pygame.time.get_ticks()
            if now - self._last_move_sound_time >= self._move_sound_cooldown_ms:
                self.move_sound.play()
                self._last_move_sound_time = now

    def play_shot_sound(self):
        if self.shot_sound:
            try:
                self.shot_sound.play()
            except Exception:
                pass

    def get_shot_position(self):
        return (self.rect.centerx, self.rect.top)

    def update(self, pressed_keys, bounds_rect: Rect):
        moved = False
        if pressed_keys[pygame.K_LEFT] and self.rect.left > bounds_rect.left:
            self.rect.x -= self.speed
            moved = True
        if pressed_keys[pygame.K_RIGHT] and self.rect.right < bounds_rect.right:
            self.rect.x += self.speed
            moved = True
        if pressed_keys[pygame.K_UP] and self.rect.top > bounds_rect.top:
            self.rect.y -= self.speed
            moved = True
        if pressed_keys[pygame.K_DOWN] and self.rect.bottom < bounds_rect.bottom:
            self.rect.y += self.speed
            moved = True
        self.rect.clamp_ip(bounds_rect)
        if moved:
            self._play_move_sound()
            print(f"Nave en ({self.rect.x}, {self.rect.y})")

    @property
    def hitbox(self):
        return self.rect
