
# Parte de Daniel — Sprint 1 (US-11 y US-12)

Contenido listo, funcional y **autónomo** para validar tu parte sin tocar el código del equipo.

## Estructura
```
gameplay_module/
  ├─ player.py
  ├─ bullet.py
  └─ enemy.py
assets/
  ├─ images/
  │  └─ player_ship.png
  ├─ sounds/
  │  ├─ move.wav
  │  └─ shot.wav
  └─ bootstrap_sounds.py
examples/
  └─ demo_local.py
```

## Integración con el proyecto del equipo (sin modificar archivos existentes)
1. Copia `gameplay_module/` y `assets/` dentro del repo del juego.
2. En el archivo principal del juego agrega:
   ```python
   from gameplay_module.player import Player
   from gameplay_module.bullet import Bullet
   from gameplay_module.enemy import Enemy
   from assets.bootstrap_sounds import ensure_default_sounds
   ensure_default_sounds()
   ```
3. Dentro del bucle del juego:
   ```python
   player = Player(screen.get_width()//2, int(screen.get_height()*0.85), speed=6)
   bullets = pygame.sprite.Group()
   # Disparo:
   # if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
   #     bullets.add(Bullet(player.rect.centerx, player.rect.top - 12))
   # En cada frame:
   # player.update(pygame.key.get_pressed(), screen.get_rect())
   # bullets.update()
   ```

## Demo local
```
pip install pygame
python examples/demo_local.py
```
