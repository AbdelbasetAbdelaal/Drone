import random
import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_SPEED, COLOR_TARGET

# Custom Pygame Event ID for Target Spawning
SPAWN_TARGET_EVENT = pygame.USEREVENT + 1

class Target(pygame.sprite.Sprite):
    """
    Target (Enemy) sprite that spawns off the right side of the screen at a random Y position,
    moves leftwards across the screen, and self-destructs when exiting the screen.
    """
    def __init__(self, speed_bonus: float = 0.0):
        super().__init__()
        
        size = random.randint(32, 52)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Outer Ring & Inner Core Visual
        color_outer = COLOR_TARGET
        color_inner = (255, 255, 255)
        pygame.draw.circle(self.image, color_outer, (size // 2, size // 2), size // 2)
        pygame.draw.circle(self.image, color_inner, (size // 2, size // 2), size // 4)

        # Spawning Position (Off the right edge of the screen)
        spawn_x = SCREEN_WIDTH + size
        spawn_y = random.randint(size, SCREEN_HEIGHT - size)
        
        self.pos = pygame.Vector2(spawn_x, spawn_y)
        self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        
        # Collision Radius
        self.radius = size // 2

        # Speed increases with level bonus
        base_speed = float(random.randint(int(TARGET_SPEED - 40), int(TARGET_SPEED + 60)))
        self.speed = base_speed + speed_bonus

    def update(self, dt: float):
        # Move leftwards across the screen
        self.pos.x -= self.speed * dt
        self.rect.centerx = round(self.pos.x)

        # Self-destruct if it moves off the left side of the screen
        if self.rect.right < 0:
            self.kill()


class Spawner:
    """
    Target Spawner class managing dynamic creation of Targets with scaling difficulty per level.
    """
    def __init__(self, base_min_interval: float = 1.5, base_max_interval: float = 3.0):
        self.base_min_interval = base_min_interval
        self.base_max_interval = base_max_interval
        self.level = 1
        
        self.min_interval = base_min_interval
        self.max_interval = base_max_interval
        self.speed_bonus = 0.0

        self.timer = 0.0
        self.current_interval = random.uniform(self.min_interval, self.max_interval)

    def set_level(self, level: int):
        """Adjusts spawn intervals and speed bonuses based on current level."""
        self.level = level
        # Spawn faster at higher levels (min threshold 0.5s)
        reduction = (level - 1) * 0.15
        self.min_interval = max(0.5, self.base_min_interval - reduction)
        self.max_interval = max(0.9, self.base_max_interval - reduction)
        
        # Targets move faster at higher levels (+35 px/s per level)
        self.speed_bonus = (level - 1) * 35.0

    def update(self, dt: float, target_group: pygame.sprite.Group) -> Target | None:
        """
        Delta-time based spawner update.
        Accumulates dt and spawns a new Target into target_group when interval expires.
        """
        self.timer += dt
        if self.timer >= self.current_interval:
            self.timer = 0.0
            self.current_interval = random.uniform(self.min_interval, self.max_interval)
            
            new_target = Target(speed_bonus=self.speed_bonus)
            target_group.add(new_target)
            return new_target

        return None
