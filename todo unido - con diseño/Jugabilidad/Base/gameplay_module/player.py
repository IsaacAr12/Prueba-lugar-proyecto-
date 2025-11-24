# -*- coding: utf-8 -*-
import pygame
from pygame import Rect
from pathlib import Path
from typing import Optional

DEFAULT_IMG = "assets/images/player_ship.png"
DEFAULT_MOVE_WAV = "assets/sounds/move.wav"


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=5, image_path: Optional[str] = None, move_sound_path: Optional[str] = None):
        super().__init__()
        # ruta original proporcionada por la persistencia (puede ser None)
        self.stored_image_path = image_path
        # resuelve la ruta efectiva (imagen subida o default) y carga la imagen
        img_path = self._resolve_image_path()
        self.image = self._load_ship(img_path)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed
        self.move_sound = self._load_sound(move_sound_path or DEFAULT_MOVE_WAV, volume=0.28)
        self._move_sound_cooldown_ms = 100
        self._last_move_sound_time = 0

    def _resolve_image_path(self) -> Optional[str]:
        """
        Devuelve la ruta de la imagen a usar:
         - si hay una ruta guardada y existe, la devuelve
         - si no, busca imágenes por defecto relativas al proyecto y devuelve la primera existente
         - si no encuentra nada, devuelve None (el loader usará el placeholder)
        """
        # 1) ruta guardada por el usuario
        if self.stored_image_path:
            p = Path(self.stored_image_path)
            if p.exists():
                return str(p)

        # 2) rutas candidatas dentro del proyecto (ajusta si tu estructura cambia)
        here = Path(__file__).parent  # .../gameplay_module
        candidates = [
            here.parent / "assets" / "images" / "player_ship.png",                 # .../Base/assets/images/...
            here.parent.parent / "assets" / "images" / "player_ship.png",          # .../Jugabilidad/assets/images/...
            here.parent.parent / "s_hud" / "assets" / "images" / "player_ship.png",
            Path(DEFAULT_IMG),                                                     # ruta relativa al cwd
        ]
        for cand in candidates:
            try:
                if cand and Path(cand).exists():
                    return str(cand)
            except Exception:
                continue

        return None

    def set_image_path(self, new_path: Optional[str]):
        """
        Actualiza la ruta almacenada y recarga la imagen del jugador.
        Pasa None para limpiar (usar default).
        """
        self.stored_image_path = new_path
        img_path = self._resolve_image_path()
        self.image = self._load_ship(img_path)
        # mantener el centro al recargar la imagen
        center = self.rect.center
        self.rect = self.image.get_rect(center=center)

    def get_spaceship_image(self) -> Optional[str]:
        """Devuelve la ruta efectiva (string) de la imagen usada actualmente o None."""
        return self._resolve_image_path()

    def _load_ship(self, path: Optional[str]):
        try:
            if path:
                return pygame.image.load(path).convert_alpha()
        except Exception:
            # fallthrough to placeholder
            pass

        # placeholder simple si la carga falla o path es None
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
            return s
        except Exception:
            return None

    def _play_move_sound(self):
        if self.move_sound:
            now = pygame.time.get_ticks()
            if now - self._last_move_sound_time >= self._move_sound_cooldown_ms:
                self.move_sound.play()
                self._last_move_sound_time = now

    def update(self, pressed_keys, bounds_rect: Rect):
        moved = False
        if pressed_keys[pygame.K_LEFT] and self.rect.left > bounds_rect.left:
            self.rect.x -= self.speed; moved = True
        if pressed_keys[pygame.K_RIGHT] and self.rect.right < bounds_rect.right:
            self.rect.x += self.speed; moved = True
        if pressed_keys[pygame.K_UP] and self.rect.top > bounds_rect.top:
            self.rect.y -= self.speed; moved = True
        if pressed_keys[pygame.K_DOWN] and self.rect.bottom < bounds_rect.bottom:
            self.rect.y += self.speed; moved = True
        self.rect.clamp_ip(bounds_rect)
        if moved: self._play_move_sound()

    @property
    def hitbox(self):
        return self.rect