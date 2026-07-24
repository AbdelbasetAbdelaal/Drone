import math
import random
import pygame
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BULLET_SPEED, ENEMY_BULLET_SPEED,
    COLOR_GOLD, COLOR_CRIMSON, COLOR_MISSILE, COLOR_BEAM, COLOR_OVERCLOCK
)

class Bullet(pygame.sprite.Sprite):
    """
    Primary Player Projectile bolt.
    """
    def __init__(self, start_pos: tuple[float, float], target_pos: tuple[float, float],
                 angle_offset_deg: float = 0.0, color: tuple[int, int, int] = COLOR_GOLD,
                 speed: float = BULLET_SPEED, damage: int = 35):
        super().__init__()
        self.damage = damage
        self.speed = speed
        
        self.original_image = pygame.Surface((22, 6), pygame.SRCALPHA)
        pygame.draw.rect(self.original_image, color, (0, 0, 22, 6), border_radius=3)
        pygame.draw.rect(self.original_image, (255, 255, 255), (4, 1, 14, 4), border_radius=2)
        
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        base_angle_rad = math.atan2(dy, dx)
        
        offset_rad = math.radians(angle_offset_deg)
        self.angle_rad = base_angle_rad + offset_rad
        self.angle_deg = math.degrees(-self.angle_rad)
        
        self.image = pygame.transform.rotate(self.original_image, self.angle_deg)
        self.pos = pygame.Vector2(start_pos)
        self.rect = self.image.get_rect(center=start_pos)
        self.radius = 8

    def update(self, dt: float, slowmo_factor: float = 1.0):
        self.pos.x += math.cos(self.angle_rad) * self.speed * dt
        self.pos.y += math.sin(self.angle_rad) * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        if (self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or
            self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT):
            self.kill()


class HomingMissile(pygame.sprite.Sprite):
    """
    Homing Missile projectile that tracks nearest enemy.
    """
    def __init__(self, start_pos: tuple[float, float], target_pos: tuple[float, float], damage: int = 75):
        super().__init__()
        self.damage = damage
        self.speed = 680.0
        self.turn_rate = 7.5
        
        self.original_image = pygame.Surface((28, 10), pygame.SRCALPHA)
        pygame.draw.polygon(self.original_image, COLOR_MISSILE, [(28, 5), (0, 0), (4, 5), (0, 10)])
        pygame.draw.rect(self.original_image, (255, 255, 255), (14, 3, 10, 4))
        
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        self.angle_rad = math.atan2(dy, dx)
        
        self.image = pygame.transform.rotate(self.original_image, math.degrees(-self.angle_rad))
        self.pos = pygame.Vector2(start_pos)
        self.rect = self.image.get_rect(center=start_pos)
        self.radius = 12

    def update(self, dt: float, slowmo_factor: float = 1.0, targets_group=None):
        if targets_group and len(targets_group) > 0:
            nearest_t = min(targets_group, key=lambda t: self.pos.distance_to(t.pos))
            if self.pos.distance_to(nearest_t.pos) < 600:
                desired_dx = nearest_t.pos.x - self.pos.x
                desired_dy = nearest_t.pos.y - self.pos.y
                desired_angle = math.atan2(desired_dy, desired_dx)
                
                angle_diff = (desired_angle - self.angle_rad + math.pi) % (2 * math.pi) - math.pi
                self.angle_rad += max(-self.turn_rate * dt, min(self.turn_rate * dt, angle_diff))
                self.image = pygame.transform.rotate(self.original_image, math.degrees(-self.angle_rad))

        self.pos.x += math.cos(self.angle_rad) * self.speed * dt
        self.pos.y += math.sin(self.angle_rad) * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        if (self.rect.right < -50 or self.rect.left > SCREEN_WIDTH + 50 or
            self.rect.bottom < -50 or self.rect.top > SCREEN_HEIGHT + 50):
            self.kill()


class ContinuousBeam(pygame.sprite.Sprite):
    """
    High-Level Plasma Beam Cannon bolt segment with intense glowing aura halo and piercing damage!
    """
    def __init__(self, start_pos: tuple[float, float], target_pos: tuple[float, float], damage: int = 24, level: int = 1):
        super().__init__()
        self.damage = damage
        self.speed = 1450.0
        
        beam_w = 42 + (level * 8)
        beam_h = 12 + (level * 4)
        
        self.original_image = pygame.Surface((beam_w, beam_h), pygame.SRCALPHA)
        # Outer Cyan/Plasma Electric Halo
        pygame.draw.ellipse(self.original_image, (56, 189, 248, 160), (0, 0, beam_w, beam_h))
        pygame.draw.rect(self.original_image, COLOR_BEAM, (4, 2, beam_w - 8, beam_h - 4), border_radius=3)
        # Blinding White Plasma Core
        pygame.draw.rect(self.original_image, (255, 255, 255), (8, 4, beam_w - 16, beam_h - 8), border_radius=2)
        
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        self.angle_rad = math.atan2(dy, dx)
        self.angle_deg = math.degrees(-self.angle_rad)
        
        self.image = pygame.transform.rotate(self.original_image, self.angle_deg)
        self.pos = pygame.Vector2(start_pos)
        self.rect = self.image.get_rect(center=start_pos)
        self.radius = 16

    def update(self, dt: float, slowmo_factor: float = 1.0):
        self.pos.x += math.cos(self.angle_rad) * self.speed * dt
        self.pos.y += math.sin(self.angle_rad) * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        if (self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or
            self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT):
            self.kill()


class EnemyBullet(pygame.sprite.Sprite):
    """
    Red plasma bullet fired by Shooting Enemies, Turrets and Boss Dreadnoughts toward the player.
    """
    def __init__(self, start_pos: tuple[float, float], target_pos: tuple[float, float], speed: float = ENEMY_BULLET_SPEED, angle_offset_deg: float = 0.0):
        super().__init__()
        
        self.original_image = pygame.Surface((18, 8), pygame.SRCALPHA)
        self.original_image.fill(COLOR_CRIMSON)
        pygame.draw.circle(self.original_image, (255, 220, 100), (14, 4), 3)
        
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        base_angle_rad = math.atan2(dy, dx)
        
        offset_rad = math.radians(angle_offset_deg)
        self.angle_rad = base_angle_rad + offset_rad
        self.angle_deg = math.degrees(-self.angle_rad)
        
        self.image = pygame.transform.rotate(self.original_image, self.angle_deg)
        self.pos = pygame.Vector2(start_pos)
        self.rect = self.image.get_rect(center=start_pos)
        self.speed = speed
        self.radius = 6

    def update(self, dt: float, slowmo_factor: float = 1.0):
        effective_dt = dt * slowmo_factor
        self.pos.x += math.cos(self.angle_rad) * self.speed * effective_dt
        self.pos.y += math.sin(self.angle_rad) * self.speed * effective_dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        if (self.rect.right < -40 or self.rect.left > SCREEN_WIDTH + 40 or
            self.rect.bottom < -40 or self.rect.top > SCREEN_HEIGHT + 40):
            self.kill()
