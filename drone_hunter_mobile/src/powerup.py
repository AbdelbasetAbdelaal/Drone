import math
import random
import pygame
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_EMERALD, COLOR_SHIELD, COLOR_OVERCLOCK, COLOR_SLOWMO, COLOR_COIN
)

class PowerupItem(pygame.sprite.Sprite):
    """
    Base class for floating powerup pickup items:
    - Battery (+30% Recharge)
    - Shield (Absorbs 2 hits)
    - Overclock (2X fire-rate & +40% speed)
    - SlowMo (Time-Dilation 40% slow motion)
    - Coin (+10 Gold Scrap Currency)
    """
    def __init__(self, arg1=None, arg2=None, ptype: str = "battery", pos: tuple[float, float] | None = None):
        super().__init__()
        
        # Robust flexible positional argument parsing
        if isinstance(arg1, str):
            self.ptype = arg1
            actual_pos = arg2 if arg2 is not None else pos
        elif isinstance(arg1, (tuple, list, pygame.Vector2)):
            actual_pos = arg1
            self.ptype = arg2 if isinstance(arg2, str) else ptype
        else:
            self.ptype = ptype
            actual_pos = pos

        self.width = 36
        self.height = 36
        self.type = self.ptype # Alias for compatibility
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        if self.ptype == "shield":
            self.color = COLOR_SHIELD
        elif self.ptype == "overclock":
            self.color = COLOR_OVERCLOCK
        elif self.ptype == "slowmo":
            self.color = COLOR_SLOWMO
        elif self.ptype == "coin":
            self.color = COLOR_COIN
        elif self.ptype == "barrel":
            self.color = (249, 115, 22)
        else: # battery
            self.color = COLOR_EMERALD

        self._render_powerup()

        # Spawning Position
        if actual_pos is None:
            spawn_x = SCREEN_WIDTH + self.width
            spawn_y = random.randint(50, SCREEN_HEIGHT - 100) if self.ptype != "barrel" else SCREEN_HEIGHT - 70
            self.pos = pygame.Vector2(spawn_x, spawn_y)
        else:
            self.pos = pygame.Vector2(actual_pos)

        self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        self.radius = 18
        self.speed = 140.0
        self.time_accum = random.uniform(0, 6.28)

    @property
    def p_type(self) -> str:
        return self.ptype

    def _render_powerup(self):
        self.image.fill((0, 0, 0, 0))
        center = (self.width // 2, self.height // 2)
        
        # Glowing Outer Energy Aura
        pygame.draw.circle(self.image, self.color, center, 17)
        pygame.draw.circle(self.image, (15, 23, 42), center, 13)
        
        if self.ptype == "shield":
            pygame.draw.circle(self.image, COLOR_SHIELD, center, 8, 2)
            pygame.draw.circle(self.image, (255, 255, 255), center, 3)
        elif self.ptype == "overclock":
            pts1 = [(12, 22), (18, 14), (24, 22)]
            pts2 = [(12, 16), (18, 8), (24, 16)]
            pygame.draw.lines(self.image, COLOR_OVERCLOCK, False, pts1, 3)
            pygame.draw.lines(self.image, (255, 255, 255), False, pts2, 3)
        elif self.ptype == "slowmo":
            pygame.draw.circle(self.image, COLOR_SLOWMO, center, 8, 2)
            pygame.draw.line(self.image, (255, 255, 255), center, (center[0], center[1] - 5), 2)
            pygame.draw.line(self.image, (255, 255, 255), center, (center[0] + 4, center[1]), 2)
        elif self.ptype == "coin":
            pygame.draw.circle(self.image, COLOR_COIN, center, 10)
            pygame.draw.circle(self.image, (250, 204, 21), center, 7)
            font = pygame.font.SysFont("Arial", 12, bold=True)
            c_txt = font.render("$", True, (15, 23, 42))
            self.image.blit(c_txt, c_txt.get_rect(center=center))
        elif self.ptype == "barrel":
            pygame.draw.rect(self.image, (249, 115, 22), (10, 8, 16, 20), border_radius=4)
            pygame.draw.rect(self.image, (255, 255, 255), (12, 14, 12, 8))
            font = pygame.font.SysFont("Arial", 10, bold=True)
            b_txt = font.render("💥", True, (15, 23, 42))
            self.image.blit(b_txt, b_txt.get_rect(center=center))
        else: # battery
            pygame.draw.rect(self.image, COLOR_EMERALD, (12, 10, 12, 16), 2)
            pygame.draw.rect(self.image, COLOR_EMERALD, (14, 8, 8, 3))
            pygame.draw.rect(self.image, (52, 211, 153), (14, 14, 8, 10))

    def update(self, dt: float):
        self.time_accum += dt
        self.pos.x -= self.speed * dt
        self.pos.y += math.sin(self.time_accum * 3.0) * 0.8
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        if self.rect.right < 0:
            self.kill()

class BatteryCharge(PowerupItem):
    def __init__(self, pos: tuple[float, float] | None = None):
        super().__init__(pos=pos, ptype="battery")
