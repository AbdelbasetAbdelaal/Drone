import math
import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, BULLET_SPEED, ENEMY_BULLET_SPEED, COLOR_BULLET, COLOR_CRIMSON

class Bullet(pygame.sprite.Sprite):
    """
    Bullet projectile class calculated via trigonometry (math.atan2).
    Supports angled spread trajectories for double and triple shooting.
    """
    def __init__(self, start_pos: tuple[float, float], target_pos: tuple[float, float], angle_offset_deg: float = 0.0):
        super().__init__()
        
        # Surface creation (glowing energy laser bolt)
        self.original_image = pygame.Surface((18, 6), pygame.SRCALPHA)
        self.original_image.fill(COLOR_BULLET)
        pygame.draw.circle(self.original_image, (255, 255, 255), (14, 3), 2) # Laser tip highlight
        
        # Calculate angle and velocity using trigonometry (math.atan2)
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        base_angle_rad = math.atan2(dy, dx)
        
        # Add angle offset for triple spread shooting
        self.angle_rad = base_angle_rad + math.radians(angle_offset_deg)
        self.angle_deg = math.degrees(-self.angle_rad)

        # Calculate directional velocity components
        self.velocity_x = math.cos(self.angle_rad) * BULLET_SPEED
        self.velocity_y = math.sin(self.angle_rad) * BULLET_SPEED

        # Rotate visual sprite to align with trajectory
        self.image = pygame.transform.rotate(self.original_image, self.angle_deg)

        # Precise position tracking with float vectors
        self.pos = pygame.Vector2(start_pos)
        self.rect = self.image.get_rect(center=start_pos)
        
        # Circular collision radius
        self.radius = max(self.rect.width, self.rect.height) // 2

    def update(self, dt: float, slowmo_factor: float = 1.0):
        # Move forward at high speed each frame
        self.pos.x += self.velocity_x * dt
        self.pos.y += self.velocity_y * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        # Self-destruct when outside screen boundaries
        if (self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or
            self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT):
            self.kill()


class EnemyBullet(pygame.sprite.Sprite):
    """
    Red plasma bullet fired by Shooting Enemies and Boss Dreadnoughts toward the player.
    """
    def __init__(self, start_pos: tuple[float, float], target_pos: tuple[float, float], speed: float = ENEMY_BULLET_SPEED):
        super().__init__()
        
        self.original_image = pygame.Surface((16, 6), pygame.SRCALPHA)
        self.original_image.fill(COLOR_CRIMSON)
        pygame.draw.circle(self.original_image, (255, 200, 100), (12, 3), 3) # Plasma tip glow
        
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        dist = math.hypot(dx, dy) or 1.0
        
        self.velocity_x = (dx / dist) * speed
        self.velocity_y = (dy / dist) * speed
        
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(-angle_rad)
        
        self.image = pygame.transform.rotate(self.original_image, angle_deg)
        self.pos = pygame.Vector2(start_pos)
        self.rect = self.image.get_rect(center=start_pos)
        self.radius = 6

    def update(self, dt: float, slowmo_factor: float = 1.0):
        effective_dt = dt * slowmo_factor
        self.pos.x += self.velocity_x * effective_dt
        self.pos.y += self.velocity_y * effective_dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        if (self.rect.right < -50 or self.rect.left > SCREEN_WIDTH + 50 or
            self.rect.bottom < -50 or self.rect.top > SCREEN_HEIGHT + 50):
            self.kill()
