import math
import random
import pygame
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_EMERALD, COLOR_SHIELD, COLOR_OVERCLOCK
)

class PowerupItem(pygame.sprite.Sprite):
    """
    Base class for floating powerup pickup items.
    """
    def __init__(self, ptype: str = "battery", pos: tuple[float, float] | None = None):
        super().__init__()
        self.ptype = ptype
        self.width = 36
        self.height = 36
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        if ptype == "shield":
            self.color = COLOR_SHIELD
        elif ptype == "overclock":
            self.color = COLOR_OVERCLOCK
        else: # battery
            self.color = COLOR_EMERALD

        self._render_powerup()

        # Spawning Position
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

    def _render_powerup(self):
        self.image.fill((0, 0, 0, 0))
        center = (self.width // 2, self.height // 2)
        
        # Glowing Outer Energy Aura
        pygame.draw.circle(self.image, self.color, center, 17)
        pygame.draw.circle(self.image, (15, 23, 42), center, 13) # Dark core background
        
        if self.ptype == "shield":
            # Shield Icon (Inner Ring + Cross)
            pygame.draw.circle(self.image, COLOR_SHIELD, center, 8, 2)
            pygame.draw.circle(self.image, (255, 255, 255), center, 3)
        elif self.ptype == "overclock":
            # Overclock Speed Icon (Double Arrows)
            pts1 = [(12, 22), (18, 14), (24, 22)]
            pts2 = [(12, 16), (18, 8), (24, 16)]
            pygame.draw.lines(self.image, COLOR_OVERCLOCK, False, pts1, 3)
            pygame.draw.lines(self.image, (255, 255, 255), False, pts2, 3)
        else:
            # Battery Icon
            pygame.draw.rect(self.image, COLOR_EMERALD, (12, 10, 12, 16), 2)
            pygame.draw.rect(self.image, COLOR_EMERALD, (14, 8, 8, 3))
            pygame.draw.rect(self.image, (52, 211, 153), (14, 14, 8, 10))

    def update(self, dt: float):
        self.time_accum += dt
        self.pos.x -= self.speed * dt
        self.pos.y += math.sin(self.time_accum * 3.0) * 0.8 # Gentle floating wave
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        # Despawn off left side of screen
        if self.rect.right < 0:
            self.kill()

# Alias for backwards compatibility
class BatteryCharge(PowerupItem):
    def __init__(self, pos: tuple[float, float] | None = None):
        super().__init__(ptype="battery", pos=pos)
