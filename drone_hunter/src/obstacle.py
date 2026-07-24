import math
import random
import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT

class EnvironmentalObstacle(pygame.sprite.Sprite):
    """
    Environmental Destructible Obstacles:
    - 'sea_mine': Floating spiked naval mines (Stormy Ocean) -> Explosive shockwave on destroy!
    - 'asteroid': Cosmic space meteor rocks (Orbital Space) -> Shatters into rock fragments!
    - 'barrel': Unstable explosive fuel barrels (Factory / Desert) -> Massive fire blast!
    """
    def __init__(self, obstacle_type: str = "sea_mine", pos: tuple[float, float] = None, sector_idx: int = 0):
        super().__init__()
        self.obstacle_type = obstacle_type
        self.sector_idx = sector_idx
        self.time_accum = random.uniform(0, 6.28)
        
        if pos is None:
            spawn_x = SCREEN_WIDTH + random.randint(40, 100)
            if obstacle_type == "sea_mine":
                spawn_y = SCREEN_HEIGHT - random.randint(60, 150)
            elif obstacle_type == "barrel":
                spawn_y = SCREEN_HEIGHT - random.randint(70, 180)
            else: # asteroid
                spawn_y = random.randint(60, SCREEN_HEIGHT - 100)
            pos = (spawn_x, spawn_y)

        self.pos = pygame.Vector2(pos)
        
        if obstacle_type == "sea_mine":
            self.hp = 6
            self.max_hp = 6
            self.points = 50
            self.size = 46
            self.speed = random.uniform(90, 140)
            self.radius = 22
        elif obstacle_type == "barrel":
            self.hp = 4
            self.max_hp = 4
            self.points = 40
            self.size = 38
            self.speed = random.uniform(100, 160)
            self.radius = 18
        else: # asteroid
            self.hp = 8
            self.max_hp = 8
            self.points = 60
            self.size = random.randint(48, 64)
            self.speed = random.uniform(70, 130)
            self.radius = self.size // 2

        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self._render_sprite()
        self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))

    def _render_sprite(self):
        self.image.fill((0, 0, 0, 0))
        center = (self.size // 2, self.size // 2)
        r = self.size // 2

        if self.obstacle_type == "sea_mine":
            # Spiked Naval Mine
            pygame.draw.circle(self.image, (30, 41, 59), center, r - 6)
            pygame.draw.circle(self.image, (239, 68, 68), center, r - 6, 2)
            pygame.draw.circle(self.image, (250, 204, 21), center, 5)
            # Spikes
            for i in range(8):
                ang = i * (math.pi / 4)
                x1 = center[0] + math.cos(ang) * (r - 6)
                y1 = center[1] + math.sin(ang) * (r - 6)
                x2 = center[0] + math.cos(ang) * r
                y2 = center[1] + math.sin(ang) * r
                pygame.draw.line(self.image, (239, 68, 68), (x1, y1), (x2, y2), 3)

        elif self.obstacle_type == "barrel":
            # Fuel Barrel
            pygame.draw.rect(self.image, (245, 158, 11), (4, 4, self.size - 8, self.size - 8), border_radius=4)
            pygame.draw.rect(self.image, (15, 23, 42), (4, 4, self.size - 8, self.size - 8), 2, border_radius=4)
            pygame.draw.rect(self.image, (239, 68, 68), (8, self.size // 2 - 3, self.size - 16, 6))

        else:
            # Cosmic Asteroid
            pygame.draw.circle(self.image, (100, 116, 139), center, r - 2)
            pygame.draw.circle(self.image, (51, 65, 85), center, r - 2, 2)
            # Crater details
            pygame.draw.circle(self.image, (51, 65, 85), (center[0] - 6, center[1] - 4), 5)
            pygame.draw.circle(self.image, (51, 65, 85), (center[0] + 7, center[1] + 5), 4)

    def take_damage(self, amount: int = 1) -> bool:
        self.hp -= amount
        if self.hp <= 0:
            return True
        return False

    def update(self, dt: float):
        self.time_accum += dt
        self.pos.x -= self.speed * dt

        if self.obstacle_type == "sea_mine":
            # Float gently on ocean waves
            self.pos.y += math.sin(self.time_accum * 3.0) * 20.0 * dt
        elif self.obstacle_type == "asteroid":
            # Slowly drift up and down in space
            self.pos.y += math.cos(self.time_accum * 1.5) * 15.0 * dt

        self.rect.center = (round(self.pos.x), round(self.pos.y))

        if self.rect.right < -40:
            self.kill()
