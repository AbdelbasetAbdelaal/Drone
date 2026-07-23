import math
import random
import pygame
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_SPEED,
    TARGET_TYPE_STANDARD, TARGET_TYPE_FAST, TARGET_TYPE_ARMORED, TARGET_TYPE_BOSS,
    COLOR_TARGET, COLOR_MAGENTA, COLOR_CRIMSON
)

class Target(pygame.sprite.Sprite):
    """
    Target (Enemy) sprite supporting multiple enemy variants:
    - Standard: Normal speed, 1 HP, 10 pts
    - Fast: High speed, small size, 1 HP, 25 pts
    - Armored: Heavy shield, large size, 3+ HP, 50 pts
    - Boss: Giant Dreadnought Cruiser, 20+ HP, 250 pts, hovers & rotates shield
    """
    def __init__(self, target_type: str = TARGET_TYPE_STANDARD, speed_bonus: float = 0.0, level: int = 1):
        super().__init__()
        self.target_type = target_type
        self.level = level
        self.shield_angle = 0.0
        
        # Attribute configuration based on type & level
        if target_type == TARGET_TYPE_BOSS:
            boss_hp = 20 + (level - 1) * 8
            self.hp = boss_hp
            self.max_hp = boss_hp
            self.points = 250
            size = 110
            base_speed = 70.0
            color_outer = (225, 29, 72)  # Heavy Rose Crimson
            color_inner = (250, 204, 21) # Gold Core
        elif target_type == TARGET_TYPE_FAST:
            self.hp = 1
            self.max_hp = 1
            self.points = 25
            size = random.randint(26, 36)
            base_speed = (TARGET_SPEED + 160.0)
            color_outer = COLOR_MAGENTA
            color_inner = (56, 189, 248) # Cyan core
        elif target_type == TARGET_TYPE_ARMORED:
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

        # Spawning Position
        spawn_x = SCREEN_WIDTH + size
        spawn_y = random.randint(size, SCREEN_HEIGHT - size) if target_type != TARGET_TYPE_BOSS else SCREEN_HEIGHT // 2
        
        self.pos = pygame.Vector2(spawn_x, spawn_y)
        self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        
        # Collision Radius
        self.radius = size // 2
        self.speed = base_speed + speed_bonus
        self.time_accum = 0.0

    def _render_sprite(self):
        self.image.fill((0, 0, 0, 0))
        center = (self.size // 2, self.size // 2)
        
        if self.target_type == TARGET_TYPE_BOSS:
            # Giant Boss Dreadnought Visual
            pygame.draw.circle(self.image, (15, 23, 42), center, self.size // 2)
            pygame.draw.circle(self.image, self.color_outer, center, self.size // 2, 4)
            pygame.draw.circle(self.image, self.color_inner, center, self.size // 4)
            
            # Rotating Outer Shield Segment Lines
            for i in range(4):
                ang = self.shield_angle + i * (math.pi / 2)
                x1 = center[0] + math.cos(ang) * (self.size // 2 - 8)
                y1 = center[1] + math.sin(ang) * (self.size // 2 - 8)
                x2 = center[0] + math.cos(ang) * (self.size // 2)
                y2 = center[1] + math.sin(ang) * (self.size // 2)
                pygame.draw.line(self.image, (56, 189, 248), (x1, y1), (x2, y2), 4)

            # Boss Health Bar on top
            bar_w = self.size - 12
            bar_h = 6
            bar_x = 6
            bar_y = 4
            pygame.draw.rect(self.image, (51, 65, 85), (bar_x, bar_y, bar_w, bar_h))
            fill_w = max(0, int(bar_w * (self.hp / self.max_hp)))
            pygame.draw.rect(self.image, (239, 68, 68), (bar_x, bar_y, fill_w, bar_h))
        else:
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
        self.time_accum += dt
        
        if self.target_type == TARGET_TYPE_BOSS:
            # Rotate Boss Shield
            self.shield_angle = (self.shield_angle + 2.0 * dt) % 6.28318
            self._render_sprite()

            # Boss Entrance & Hover Behavior
            target_x = SCREEN_WIDTH - 180
            if self.pos.x > target_x:
                self.pos.x -= self.speed * dt
            else:
                self.pos.x = target_x + math.sin(self.time_accum * 1.5) * 15.0
                self.pos.y = (SCREEN_HEIGHT // 2) + math.sin(self.time_accum * 2.2) * 140.0
            
            self.rect.center = (round(self.pos.x), round(self.pos.y))
        else:
            # Normal Enemies move leftwards
            self.pos.x -= self.speed * dt
            self.rect.centerx = round(self.pos.x)

            if self.rect.right < 0:
                self.kill()


class Spawner:
    """
    Target Spawner managing dynamic creation of Targets and Bosses per level.
    """
    def __init__(self, base_min_interval: float = 1.5, base_max_interval: float = 3.0):
        self.base_min_interval = base_min_interval
        self.base_max_interval = base_max_interval
        self.level = 1
        
        self.min_interval = base_min_interval
        self.max_interval = base_max_interval
        self.speed_bonus = 0.0
        self.boss_spawned = False

        self.timer = 0.0
        self.current_interval = random.uniform(self.min_interval, self.max_interval)

    def set_level(self, level: int):
        self.level = level
        self.boss_spawned = False
        reduction_min = (level - 1) * 0.35
        reduction_max = (level - 1) * 0.55
        self.min_interval = max(0.4, self.base_min_interval - reduction_min)
        self.max_interval = max(0.8, self.base_max_interval - reduction_max)
        self.speed_bonus = (level - 1) * 55.0

    def _select_target_type(self) -> str:
        if self.level == 1:
            return TARGET_TYPE_STANDARD
        elif self.level == 2:
            return random.choices([TARGET_TYPE_STANDARD, TARGET_TYPE_FAST], weights=[60, 40], k=1)[0]
        elif self.level == 3:
            return random.choices([TARGET_TYPE_STANDARD, TARGET_TYPE_FAST, TARGET_TYPE_ARMORED], weights=[40, 35, 25], k=1)[0]
        else: # Level 4+
            return random.choices([TARGET_TYPE_STANDARD, TARGET_TYPE_FAST, TARGET_TYPE_ARMORED], weights=[20, 45, 35], k=1)[0]

    def update(self, dt: float, target_group: pygame.sprite.Group, level_score: int, points_per_level: int) -> Target | None:
        # Spawn Boss Dreadnought at 75% level progress on Level 3, Level 6, etc.
        if (self.level % 3 == 0) and not self.boss_spawned and (level_score >= int(points_per_level * 0.65)):
            self.boss_spawned = True
            boss = Target(target_type=TARGET_TYPE_BOSS, level=self.level)
            target_group.add(boss)
            return boss

        self.timer += dt
        if self.timer >= self.current_interval:
            self.timer = 0.0
            self.current_interval = random.uniform(self.min_interval, self.max_interval)
            
            target_type = self._select_target_type()
            new_target = Target(target_type=target_type, speed_bonus=self.speed_bonus, level=self.level)
            target_group.add(new_target)
            return new_target

        return None
