import pygame
import os

WIDTH = 4
HEIGHT = 12

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(_script_dir)))
ASSET_BASE = os.path.join(_project_root, "Jugabilidad/Base")
DEFAULT_SHOT_WAV = os.path.join(ASSET_BASE, "assets/sounds/shot.wav")


class Bala(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=-12, color=(255, 255, 0), shot_sound_path=None):
        super().__init__()
        print(f"✓ Bala creada en ({x}, {y})")
        self.image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_y = speed
        self.shot_sound = self._load_sound(shot_sound_path or DEFAULT_SHOT_WAV, volume=0.3)
        if self.shot_sound:
            try:
                self.shot_sound.play()
                print("✓ Sonido de disparo reproducido")
            except Exception as e:
                print(f"✗ Error al reproducir sonido: {e}")
        else:
            print("✗ No se pudo cargar el sonido")

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

    def update(self, *args):
        self.rect.y += self.speed_y
        if self.rect.bottom < 0:
            self.kill()
