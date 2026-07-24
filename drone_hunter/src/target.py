import math
import random
import pygame
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_SPEED,
    TARGET_TYPE_STANDARD, TARGET_TYPE_FAST, TARGET_TYPE_ARMORED, TARGET_TYPE_SHOOTER, TARGET_TYPE_BOSS,
    TARGET_TYPE_TURRET, TARGET_TYPE_VEHICLE, TARGET_TYPE_CHASER,
    COLOR_TARGET, COLOR_MAGENTA, COLOR_CRIMSON, COLOR_CYAN, COLOR_NEON_RED
)
from src.bullet import EnemyBullet

class Target(pygame.sprite.Sprite):
    """
    Target (Enemy) sprite supporting multiple enemy variants:
    - Standard: Normal speed, 1 HP, 10 pts
    - Fast: High speed, small size, 1 HP, 25 pts
    - Armored: Heavy shield, large size, 3+ HP, 50 pts
    - Shooter: Fires plasma bullets at player, 2 HP, 40 pts
    - Boss: Giant Dreadnought Cruiser, 20+ HP, 250 pts
    - Ground Turret: Roof turret firing anti-air salvos upward, 3 HP, 45 pts
    - Target Vehicle: Armored ground rover with glowing neon red crosshairs, 4 HP, 70 pts
    - Chaser Drone: Aggressive pursuing drone tracking player position, 2 HP, 35 pts
    """
    def __init__(self, target_type: str = TARGET_TYPE_STANDARD, speed_bonus: float = 0.0, level: int = 1):
        super().__init__()
        self.target_type = target_type
        self.level = level
        self.shield_angle = 0.0
        self.shoot_timer = random.uniform(0.5, 1.8)
        
        # Attribute configuration based on type & level (Dramatically higher HP for heavy targets)
        if target_type == TARGET_TYPE_BOSS:
            boss_hp = 65 + (level - 1) * 30
            self.hp = boss_hp
            self.max_hp = boss_hp
            self.points = 450
            size = 110
            base_speed = 65.0
            color_outer = (225, 29, 72)  # Heavy Rose Crimson
            color_inner = (250, 204, 21) # Gold Core
        elif target_type == TARGET_TYPE_VEHICLE:
            v_hp = 14 + (level * 4)
            self.hp = v_hp
            self.max_hp = v_hp
            self.points = 120
            size = 76
            base_speed = (TARGET_SPEED - 40.0)
            color_outer = COLOR_NEON_RED
            color_inner = (255, 255, 255)
        elif target_type == TARGET_TYPE_TURRET:
            t_hp = 12 + (level * 2)
            self.hp = t_hp
            self.max_hp = t_hp
            self.points = 85
            size = 56
            base_speed = 100.0  # Matches background parallax
            color_outer = (100, 116, 139) # Metallic Slate
            color_inner = COLOR_NEON_RED
        elif target_type == TARGET_TYPE_CHASER:
            self.hp = 3
            self.max_hp = 3
            self.points = 45
            size = 38
            base_speed = (TARGET_SPEED + 80.0)
            color_outer = COLOR_MAGENTA
            color_inner = COLOR_CYAN
        elif target_type == TARGET_TYPE_SHOOTER:
            self.hp = 4
            self.max_hp = 4
            self.points = 60
            size = 46
            base_speed = (TARGET_SPEED + 40.0)
            color_outer = (244, 63, 94)  # Rose Coral
            color_inner = (56, 189, 248) # Cyan Core
        elif target_type == TARGET_TYPE_FAST:
            self.hp = 1
            self.max_hp = 1
            self.points = 25
            size = random.randint(26, 36)
            base_speed = (TARGET_SPEED + 160.0)
            color_outer = COLOR_MAGENTA
            color_inner = (56, 189, 248) # Cyan core
        elif target_type == TARGET_TYPE_ARMORED:
            armor_hp = 10 + (level * 3)
            self.hp = armor_hp
            self.max_hp = armor_hp
            self.points = 90 + (level - 1) * 15
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
        
        # Spawning Position
        spawn_x = SCREEN_WIDTH + size
        if target_type == TARGET_TYPE_BOSS:
            spawn_y = SCREEN_HEIGHT // 2
        elif target_type in (TARGET_TYPE_VEHICLE, TARGET_TYPE_TURRET):
            spawn_y = SCREEN_HEIGHT - 65
        else:
            spawn_y = random.randint(size, SCREEN_HEIGHT - 120)
        
        self.pos = pygame.Vector2(spawn_x, spawn_y)
        self._render_sprite()
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
            
            for i in range(4):
                ang = self.shield_angle + i * (math.pi / 2)
                x1 = center[0] + math.cos(ang) * (self.size // 2 - 8)
                y1 = center[1] + math.sin(ang) * (self.size // 2 - 8)
                x2 = center[0] + math.cos(ang) * (self.size // 2)
                y2 = center[1] + math.sin(ang) * (self.size // 2)
                pygame.draw.line(self.image, (56, 189, 248), (x1, y1), (x2, y2), 4)

            bar_w = self.size - 12
            bar_h = 6
            pygame.draw.rect(self.image, (51, 65, 85), (6, 4, bar_w, bar_h))
            fill_w = max(0, int(bar_w * (self.hp / self.max_hp)))
            pygame.draw.rect(self.image, (239, 68, 68), (6, 4, fill_w, bar_h))

        elif self.target_type == TARGET_TYPE_VEHICLE:
            # Armored Tactical Rover Chassis
            pygame.draw.rect(self.image, (30, 41, 59), (4, 16, self.size - 8, 28), border_radius=6)
            pygame.draw.rect(self.image, COLOR_NEON_RED, (4, 16, self.size - 8, 28), 2, border_radius=6)
            # Wheels
            pygame.draw.rect(self.image, (15, 23, 42), (8, 38, 14, 8))
            pygame.draw.rect(self.image, (15, 23, 42), (self.size - 22, 38, 14, 8))
            # Sensor Turret Top
            pygame.draw.circle(self.image, COLOR_NEON_RED, (center[0], 22), 8)

        elif self.target_type == TARGET_TYPE_TURRET:
            # Roof Defense Turret Structure
            pygame.draw.polygon(self.image, (51, 65, 85), [(4, self.size - 4), (self.size - 4, self.size - 4), (center[0] + 10, 18), (center[0] - 10, 18)])
            pygame.draw.circle(self.image, (100, 116, 139), (center[0], 22), 14)
            pygame.draw.circle(self.image, COLOR_NEON_RED, (center[0], 22), 6)
            # Dual Anti-Air Cannon Tubes
            pygame.draw.rect(self.image, (226, 232, 240), (center[0] - 8, 4, 4, 16))
            pygame.draw.rect(self.image, (226, 232, 240), (center[0] + 4, 4, 4, 16))

        elif self.target_type == TARGET_TYPE_CHASER:
            # Interceptor Chaser Drone Tri-wing
            pygame.draw.polygon(self.image, COLOR_MAGENTA, [
                (4, center[1]), (self.size - 6, 6), (self.size - 14, center[1]), (self.size - 6, self.size - 6)
            ])
            pygame.draw.circle(self.image, COLOR_CYAN, (self.size - 18, center[1]), 5)

        elif self.target_type == TARGET_TYPE_SHOOTER:
            pygame.draw.polygon(self.image, self.color_outer, [
                (self.size, center[1]), (8, 4), (16, center[1]), (8, self.size - 4)
            ])
            pygame.draw.circle(self.image, self.color_inner, center, 6)

        else:
            pygame.draw.circle(self.image, self.color_outer, center, self.size // 2)
            pygame.draw.circle(self.image, (15, 23, 42), center, int(self.size // 2 * 0.75))
            pygame.draw.circle(self.image, self.color_inner, center, self.size // 4)

        # Armor Bar for multihit enemies
        if self.max_hp > 1 and self.target_type not in (TARGET_TYPE_BOSS,):
            bar_w = self.size - 8
            bar_h = 4
            pygame.draw.rect(self.image, (51, 65, 85), (4, 2, bar_w, bar_h))
            fill_w = int(bar_w * (self.hp / self.max_hp))
            pygame.draw.rect(self.image, (250, 204, 21), (4, 2, fill_w, bar_h))

    def take_damage(self, amount: int = 1) -> bool:
        """Applies damage to target. Returns True if destroyed."""
        self.hp -= amount
        if self.hp <= 0:
            return True
        self._render_sprite()
        return False

    def update(self, dt: float, player_pos: tuple[float, float] = (200, 360), slowmo_factor: float = 1.0, player_vel: tuple[float, float] = (0, 0), bullet_group=None) -> list[EnemyBullet]:
        effective_dt = dt * slowmo_factor
        self.time_accum += effective_dt
        new_enemy_bullets = []

        # Smart Predictive Aiming (predict where player is flying)
        pred_aim_x = player_pos[0] + player_vel[0] * 0.35
        pred_aim_y = player_pos[1] + player_vel[1] * 0.35
        pred_aim = (pred_aim_x, pred_aim_y)

        # Check for Boss Enrage Phase 2 (< 50% HP)
        is_enraged = self.target_type == TARGET_TYPE_BOSS and (self.hp <= self.max_hp // 2)

        # Smart Reactive Bullet Dodging for Fast & Shooter Drones
        if self.target_type in (TARGET_TYPE_FAST, TARGET_TYPE_SHOOTER) and bullet_group:
            for b in bullet_group:
                if 0 < (b.pos.x - self.pos.x) < 130 and abs(b.pos.y - self.pos.y) < 45:
                    dodge_dir = -1.0 if b.pos.y > self.pos.y else 1.0
                    self.pos.y += dodge_dir * 220.0 * effective_dt

        # Handle Enemy Firing Logic (Predictive & Salvo Spread)
        if self.target_type in (TARGET_TYPE_SHOOTER, TARGET_TYPE_TURRET, TARGET_TYPE_BOSS):
            self.shoot_timer -= effective_dt
            if self.shoot_timer <= 0:
                if self.target_type == TARGET_TYPE_TURRET:
                    self.shoot_timer = random.uniform(1.2, 1.9)
                    # Predictive Triple AA Flak Salvo
                    new_enemy_bullets.append(EnemyBullet(self.rect.center, pred_aim, speed=520.0, angle_offset_deg=-14.0))
                    new_enemy_bullets.append(EnemyBullet(self.rect.center, pred_aim, speed=540.0, angle_offset_deg=0.0))
                    new_enemy_bullets.append(EnemyBullet(self.rect.center, pred_aim, speed=520.0, angle_offset_deg=14.0))
                elif self.target_type == TARGET_TYPE_SHOOTER:
                    self.shoot_timer = random.uniform(1.6, 2.3)
                    # Predictive Dual Plasma Burst
                    new_enemy_bullets.append(EnemyBullet(self.rect.center, pred_aim, speed=480.0, angle_offset_deg=-7.0))
                    new_enemy_bullets.append(EnemyBullet(self.rect.center, pred_aim, speed=480.0, angle_offset_deg=7.0))
                elif self.target_type == TARGET_TYPE_BOSS:
                    self.shoot_timer = 1.4 if is_enraged else 1.9
                    cx, cy = self.rect.center
                    offsets = [-28.0, -18.0, -8.0, 8.0, 18.0, 28.0] if is_enraged else [-22.0, -11.0, 0.0, 11.0, 22.0]
                    b_speed = 520.0 if is_enraged else 440.0
                    for offset in offsets:
                        new_enemy_bullets.append(EnemyBullet((cx, cy), pred_aim, speed=b_speed, angle_offset_deg=offset))

        if self.target_type == TARGET_TYPE_BOSS:
            rot_speed = 6.0 if is_enraged else 2.5
            self.shield_angle = (self.shield_angle + rot_speed * effective_dt) % 6.28318
            self._render_sprite()

            target_x = SCREEN_WIDTH - 180
            if self.pos.x > target_x:
                self.pos.x -= self.speed * effective_dt
            else:
                h_freq = 3.2 if is_enraged else 1.8
                self.pos.x = target_x + math.sin(self.time_accum * h_freq) * (30.0 if is_enraged else 20.0)
                self.pos.y = (SCREEN_HEIGHT // 2) + math.sin(self.time_accum * (3.0 if is_enraged else 2.5)) * 170.0
            
            self.rect.center = (round(self.pos.x), round(self.pos.y))

        elif self.target_type == TARGET_TYPE_CHASER:
            # Wild Erratic Tracking towards player altitude with sine-wave zigzag
            self.pos.x -= self.speed * effective_dt
            dy = player_pos[1] - self.pos.y
            tracking_step = math.copysign(min(abs(dy), 190.0 * effective_dt), dy)
            zigzag = math.sin(self.time_accum * 8.0) * 140.0 * effective_dt
            self.pos.y += tracking_step + zigzag
            self.rect.center = (round(self.pos.x), round(self.pos.y))

            if self.rect.right < 0:
                self.kill()

        elif self.target_type in (TARGET_TYPE_STANDARD, TARGET_TYPE_FAST):
            # Wild Weaving Movement for airborne targets
            self.pos.x -= self.speed * effective_dt
            self.pos.y += math.sin(self.time_accum * 3.8) * 75.0 * effective_dt
            self.rect.center = (round(self.pos.x), round(self.pos.y))

            if self.rect.right < 0:
                self.kill()

        else:
            # Vehicle & Armored Targets move leftwards along ground
            self.pos.x -= self.speed * effective_dt
            self.rect.centerx = round(self.pos.x)

            if self.rect.right < 0:
                self.kill()

        return new_enemy_bullets


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
            return random.choices([TARGET_TYPE_STANDARD, TARGET_TYPE_VEHICLE], weights=[70, 30], k=1)[0]
        elif self.level == 2:
            return random.choices([TARGET_TYPE_STANDARD, TARGET_TYPE_FAST, TARGET_TYPE_SHOOTER, TARGET_TYPE_VEHICLE, TARGET_TYPE_TURRET], weights=[35, 25, 15, 15, 10], k=1)[0]
        elif self.level == 3:
            return random.choices([TARGET_TYPE_STANDARD, TARGET_TYPE_FAST, TARGET_TYPE_ARMORED, TARGET_TYPE_SHOOTER, TARGET_TYPE_TURRET, TARGET_TYPE_VEHICLE, TARGET_TYPE_CHASER], weights=[20, 20, 15, 15, 10, 10, 10], k=1)[0]
        else: # Level 4+
            return random.choices([TARGET_TYPE_STANDARD, TARGET_TYPE_FAST, TARGET_TYPE_ARMORED, TARGET_TYPE_SHOOTER, TARGET_TYPE_TURRET, TARGET_TYPE_VEHICLE, TARGET_TYPE_CHASER], weights=[10, 25, 20, 15, 10, 10, 10], k=1)[0]

    def update(self, dt: float, target_group: pygame.sprite.Group, level_score: int, points_per_level: int) -> Target | None:
        # Spawn Boss Dreadnought at 65% level progress on Level 3, Level 6, etc.
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
