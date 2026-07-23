import math
import random
import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_EMERALD

class BatteryCharge(pygame.sprite.Sprite):
    """
    Floating Battery Power-Up pickup item that recharges the Drone's battery when collected.
    """
    def __init__(self, pos: tuple[float, float] | None = None):
        super().__init__()
        
        self.width = 36
        self.height = 36
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._render_battery()

        # Spawning Position (Random right edge or specified position)
        if pos is None:
            spawn_x = SCREEN_WIDTH + self.width
            spawn_y = random.randint(50, SCREEN_HEIGHT - 50)
            self.pos = pygame.Vector2(spawn_x, spawn_y)
        else:
            self.pos = pygame.Vector2(pos)

        self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        self.radius = 18
        self.speed = 140.0
        self.time_accum = random.uniform(0, 6.28)

    def _render_battery(self):
        self.image.fill((0, 0, 0, 0))
        center = (self.width // 2, self.height // 2)
        
        # Glowing Outer Emerald Energy Aura
        pygame.draw.circle(self.image, COLOR_EMERALD, center, 17)
        pygame.draw.circle(self.image, (15, 23, 42), center, 14) # Dark core background
        
        # Battery Cell Box
        pygame.draw.rect(self.image, COLOR_EMERALD, (12, 10, 12, 16), 2)
        pygame.draw.rect(self.image, COLOR_EMERALD, (14, 8, 8, 3)) # Battery Top Cap
        
        # Battery Fill Level
        pygame.draw.rect(self.image, (52, 211, 153), (14, 14, 8, 10))

        # Lightning Bolt Symbol Glow
        pts = [(19, 11), (15, 18), (18, 18), (17, 25), (21, 17), (18, 17)]
        pygame.draw.polygon(self.image, (255, 255, 255), pts)

    def update(self, dt: float):
        self.time_accum += dt
        self.pos.x -= self.speed * dt
        self.pos.y += math.sin(self.time_accum * 3.0) * 0.8 # Gentle floating wave
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        # Despawn off left side of screen
        if self.rect.right < 0:
            self.kill()
