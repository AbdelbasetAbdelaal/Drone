import random
import pygame
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_SPEED,
    TARGET_TYPE_STANDARD, TARGET_TYPE_FAST, TARGET_TYPE_ARMORED,
    COLOR_TARGET, COLOR_MAGENTA, COLOR_CRIMSON
)

class Target(pygame.sprite.Sprite):
    """
    Target (Enemy) sprite supporting multiple enemy variants:
    - Standard: Normal speed, 1 HP, 10 pts
    - Fast: High speed, small size, 1 HP, 25 pts
    - Armored: Heavy shield, large size, 3+ HP, 50 pts
    """
    def __init__(self, target_type: str = TARGET_TYPE_STANDARD, speed_bonus: float = 0.0, level: int = 1):
        super().__init__()
        self.target_type = target_type
        
        # Attribute configuration based on type & level
        if target_type == TARGET_TYPE_FAST:
            self.hp = 1
            self.max_hp = 1
            self.points = 25
            size = random.randint(26, 36)
            base_speed = (TARGET_SPEED + 160.0)
            color_outer = COLOR_MAGENTA
            color_inner = (56, 189, 248) # Cyan core
        elif target_type == TARGET_TYPE_ARMORED:
            # Higher levels make Armored targets even tougher (3 to 5 HP)
            armor_hp = 3 + max(0, level - 3)
            self.hp = armor_hp
            self.max_hp = armor_hp
            self.points = 50 + (level - 1) * 10
            size = random.randint(58, 72)
            base_speed = (TARGET_SPEED - 20.0)
            color_outer = COLOR_CRIMSON
            color_inner = (250, 204, 21) # Gold core
        else: # Standard
            self.hp = 1
            self.max_hp = 1
            self.points = 10
            size = random.randint(36, 48)
            base_speed = TARGET_SPEED
            color_outer = COLOR_TARGET
            color_inner = (255, 255, 255)

        self.size = size
        self.color_outer = color_outer
        self.color_inner = color_inner

        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self._render_sprite()

        # Spawning Position (Off the right edge of the screen)
        spawn_x = SCREEN_WIDTH + size
        spawn_y = random.randint(size, SCREEN_HEIGHT - size)
        
        self.pos = pygame.Vector2(spawn_x, spawn_y)
        self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        
        # Collision Radius
        self.radius = size // 2
        self.speed = base_speed + speed_bonus

    def _render_sprite(self):
        self.image.fill((0, 0, 0, 0))
        center = (self.size // 2, self.size // 2)
        
        # Outer Ring & Inner Core Visual
        pygame.draw.circle(self.image, self.color_outer, center, self.size // 2)
        pygame.draw.circle(self.image, (15, 23, 42), center, int(self.size // 2 * 0.75)) # Inner dark ring
        pygame.draw.circle(self.image, self.color_inner, center, self.size // 4)

        # Render Armor Health bar if HP > 1
        if self.max_hp > 1:
            bar_w = self.size - 8
            bar_h = 4
            bar_x = 4
            bar_y = 2
            pygame.draw.rect(self.image, (51, 65, 85), (bar_x, bar_y, bar_w, bar_h))
            fill_w = int(bar_w * (self.hp / self.max_hp))
            pygame.draw.rect(self.image, (250, 204, 21), (bar_x, bar_y, fill_w, bar_h))

    def take_damage(self, amount: int = 1) -> bool:
        """Applies damage to target. Returns True if destroyed."""
        self.hp -= amount
        if self.hp <= 0:
            return True
        self._render_sprite()
        return False

    def update(self, dt: float):
        # Move leftwards across the screen
        self.pos.x -= self.speed * dt
        self.rect.centerx = round(self.pos.x)

        # Self-destruct if it moves off the left side of the screen
        if self.rect.right < 0:
            self.kill()


class Spawner:
    """
    Target Spawner class managing dynamic creation of Targets with scaling difficulty
    and enemy type variety based on current Level.
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
        """Adjusts spawn intervals, speed bonuses, and enemy variety based on current level."""
        self.level = level
        # Spawn interval scaling: Level 1 (1.5s - 3.0s), Level 2 (1.1s - 2.1s), Level 3 (0.7s - 1.4s), Level 4+ (0.4s - 0.8s)
        reduction_min = (level - 1) * 0.35
        reduction_max = (level - 1) * 0.55
        self.min_interval = max(0.4, self.base_min_interval - reduction_min)
        self.max_interval = max(0.8, self.base_max_interval - reduction_max)
        
        # Movement speed scaling: +55 px/s per level
        self.speed_bonus = (level - 1) * 55.0

    def _select_target_type(self) -> str:
        """Selects target type based on current level probabilities."""
        if self.level == 1:
            return TARGET_TYPE_STANDARD
        elif self.level == 2:
            # 60% Standard, 40% Fast
            return random.choices([TARGET_TYPE_STANDARD, TARGET_TYPE_FAST], weights=[60, 40], k=1)[0]
        elif self.level == 3:
            # 40% Standard, 35% Fast, 25% Armored
            return random.choices([TARGET_TYPE_STANDARD, TARGET_TYPE_FAST, TARGET_TYPE_ARMORED], weights=[40, 35, 25], k=1)[0]
        else: # Level 4+
            # 20% Standard, 45% Fast, 35% Armored
            return random.choices([TARGET_TYPE_STANDARD, TARGET_TYPE_FAST, TARGET_TYPE_ARMORED], weights=[20, 45, 35], k=1)[0]

    def update(self, dt: float, target_group: pygame.sprite.Group) -> Target | None:
        self.timer += dt
        if self.timer >= self.current_interval:
            self.timer = 0.0
            self.current_interval = random.uniform(self.min_interval, self.max_interval)
            
            target_type = self._select_target_type()
            new_target = Target(target_type=target_type, speed_bonus=self.speed_bonus, level=self.level)
            target_group.add(new_target)
            return new_target

        return None
