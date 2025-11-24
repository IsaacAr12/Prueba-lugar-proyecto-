
# -*- coding: utf-8 -*-
import pygame


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, w=40, h=28, color=(220, 60, 60)):
        super().__init__()
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
