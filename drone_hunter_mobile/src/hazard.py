import math
import random
import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_CYAN, COLOR_CRIMSON, COLOR_PURPLE

class LaserGridFence(pygame.sprite.Sprite):
    """
    Factory & City Sector Environmental Trap:
    Vertical laser beam barrier that toggles ON (deadly) and OFF (safe) on a timer.
    """
    def __init__(self, x_pos: float):
        super().__init__()
        self.x_pos = x_pos
        self.is_active = True
        self.timer = 0.0
        self.active_duration = 2.4
        self.cooldown_duration = 1.6

        self.image = pygame.Surface((20, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.rect = self.image.get_rect(centerx=round(x_pos), centery=SCREEN_HEIGHT // 2)
        self._render_grid()

    def _render_grid(self):
        self.image.fill((0, 0, 0, 0))
        if self.is_active:
            # Active Red Deadly Laser Beam Barrier
            pygame.draw.line(self.image, (239, 68, 68, 220), (10, 0), (10, SCREEN_HEIGHT), 8)
            pygame.draw.line(self.image, (255, 255, 255, 240), (10, 0), (10, SCREEN_HEIGHT), 3)
            # Pulsing Warning Emitting Emitters at top & bottom
            pygame.draw.circle(self.image, COLOR_CRIMSON, (10, 20), 8)
            pygame.draw.circle(self.image, COLOR_CRIMSON, (10, SCREEN_HEIGHT - 20), 8)
        else:
            # Inactive Faded Beam (Safe to pass through)
            pygame.draw.line(self.image, (100, 116, 139, 80), (10, 0), (10, SCREEN_HEIGHT), 2)
            pygame.draw.circle(self.image, (100, 116, 139), (10, 20), 5)
            pygame.draw.circle(self.image, (100, 116, 139), (10, SCREEN_HEIGHT - 20), 5)

    def update(self, dt: float):
        self.timer += dt
        if self.is_active and self.timer >= self.active_duration:
            self.is_active = False
            self.timer = 0.0
            self._render_grid()
        elif not self.is_active and self.timer >= self.cooldown_duration:
            self.is_active = True
            self.timer = 0.0
            self._render_grid()

        self.x_pos -= 60.0 * dt
        self.rect.centerx = round(self.x_pos)

        if self.rect.right < 0:
            self.kill()


class GravityAnomaly(pygame.sprite.Sprite):
    """
    Space & Ocean Sector Environmental Hazard:
    Rotating singularity vortex that pulls player drones and bullets toward its center!
    """
    def __init__(self, pos: tuple[float, float] = None):
        super().__init__()
        if pos is None:
            pos = (SCREEN_WIDTH + 80, random.randint(120, SCREEN_HEIGHT - 160))
        self.pos = pygame.Vector2(pos)
        self.pull_radius = 280.0
        self.pull_force = 180.0
        self.rotation_angle = 0.0
        self.speed = 50.0

        self.image = pygame.Surface((120, 120), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self._render_vortex()

    def _render_vortex(self):
        self.image.fill((0, 0, 0, 0))
        center = (60, 60)
        
        # Outer Singularity Glow
        pygame.draw.circle(self.image, (168, 85, 247, 80), center, 55)
        pygame.draw.circle(self.image, (56, 189, 248, 120), center, 40)
        pygame.draw.circle(self.image, (15, 23, 42), center, 22)
        
        # Rotating Spiral Arms
        for i in range(4):
            ang = self.rotation_angle + i * (math.pi / 2)
            x2 = center[0] + math.cos(ang) * 45
            y2 = center[1] + math.sin(ang) * 45
            pygame.draw.line(self.image, COLOR_PURPLE, center, (x2, y2), 3)

    def update(self, dt: float, player=None):
        self.rotation_angle = (self.rotation_angle + dt * 4.5) % 6.28318
        self._render_vortex()

        self.pos.x -= self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        # Pull Player Drone toward vortex if within pull_radius
        if player and player.alive:
            dist = self.pos.distance_to(player.pos)
            if 0 < dist < self.pull_radius:
                pull_dir = (self.pos - player.pos).normalize()
                strength = (1.0 - (dist / self.pull_radius)) * self.pull_force
                player.pos += pull_dir * strength * dt

        if self.rect.right < -60:
            self.kill()
