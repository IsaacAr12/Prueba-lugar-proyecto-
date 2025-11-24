
# -*- coding: utf-8 -*-
import pygame
from gameplay_module.player import Player
from gameplay_module.bullet import Bullet
from gameplay_module.enemy import Enemy
from assets.bootstrap_sounds import ensure_default_sounds

ensure_default_sounds()

WIDTH, HEIGHT = 900, 700

def run():
    pygame.init()
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except Exception:
        pass

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Validación — Parte de Isaac (US-11/US-12)")
    bounds = screen.get_rect()

    player = Player(bounds.centerx, int(bounds.bottom * 0.85), speed=6)
    enemies = pygame.sprite.Group(Enemy(WIDTH//2, 120), Enemy(WIDTH//2 - 160, 180), Enemy(WIDTH//2 + 160, 180))
    bullets = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group(player, *enemies)

    font = pygame.font.SysFont("consolas", 22)
    clock = pygame.time.Clock()
    points = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    bullets.add(Bullet(player.rect.centerx, player.rect.top - 12))

        pressed = pygame.key.get_pressed()
        player.update(pressed, bounds)
        bullets.update()

        hit = pygame.sprite.groupcollide(enemies, bullets, True, True)
        if hit:
            points += 100 * len(hit)

        screen.fill((6, 8, 20))
        all_sprites.draw(screen)
        bullets.draw(screen)
        score_txt = font.render(f"Puntos: {points}", True, (230, 230, 240))
        screen.blit(score_txt, (12, 12))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    run()
