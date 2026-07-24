import math
import random
import pygame
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_SPEED, ENEMY_BULLET_SPEED,
    TARGET_TYPE_STANDARD, TARGET_TYPE_FAST, TARGET_TYPE_ARMORED, TARGET_TYPE_SHOOTER, TARGET_TYPE_BOSS,
    TARGET_TYPE_TURRET, TARGET_TYPE_VEHICLE, TARGET_TYPE_CHASER,
    COLOR_TARGET, COLOR_MAGENTA, COLOR_CRIMSON, COLOR_CYAN, COLOR_NEON_RED
)
from src.bullet import EnemyBullet

class Target(pygame.sprite.Sprite):
    """
    Target (Enemy) sprite supporting multiple enemy variants:
    - Standard, Fast, Armored, Shooter, Boss Dreadnought, Turret, Vehicle, Chaser.
    Supports Multi-Phase Boss encounters with 360-Degree Radial Spiral Salvos!
    """
    def __init__(self, target_type: str = TARGET_TYPE_STANDARD, speed_bonus: float = 0.0, level: int = 1, sector_idx: int = 0):
        super().__init__()
        self.target_type = target_type
        self.level = level
        self.sector_idx = sector_idx
        self.shield_angle = 0.0
        self.shoot_timer = random.uniform(0.3, 1.4)
        self.rage_phase = False
        
        sec_mult = 1.0 + (sector_idx * 0.35)
        
        if target_type == TARGET_TYPE_BOSS:
            boss_hp = int((90 + (level - 1) * 45) * sec_mult)
            self.hp = boss_hp
            self.max_hp = boss_hp
            self.points = 600 + sector_idx * 200
            size = 125
            base_speed = 75.0 + sector_idx * 15.0
            color_outer = (225, 29, 72)
            color_inner = (250, 204, 21)
        elif target_type == TARGET_TYPE_VEHICLE:
            v_hp = int((14 + level * 4) * sec_mult)
            self.hp = v_hp
            self.max_hp = v_hp
            self.points = 120
            size = 76
            base_speed = (TARGET_SPEED - 40.0) + sector_idx * 20.0
            color_outer = COLOR_NEON_RED
            color_inner = (255, 255, 255)
        elif target_type == TARGET_TYPE_TURRET:
            t_hp = int((12 + level * 3) * sec_mult)
            self.hp = t_hp
            self.max_hp = t_hp
            self.points = 85
            size = 56
            base_speed = 100.0 + sector_idx * 25.0
            color_outer = (100, 116, 139)
            color_inner = COLOR_NEON_RED
        elif target_type == TARGET_TYPE_CHASER:
            c_hp = int(3 * sec_mult)
            self.hp = c_hp
            self.max_hp = c_hp
            self.points = 45
            size = 38
            base_speed = (TARGET_SPEED + 100.0) + sector_idx * 30.0
            color_outer = COLOR_MAGENTA
            color_inner = COLOR_CYAN
        elif target_type == TARGET_TYPE_SHOOTER:
            s_hp = int(5 * sec_mult)
            self.hp = s_hp
            self.max_hp = s_hp
            self.points = 60
            size = 46
            base_speed = (TARGET_SPEED + 50.0) + sector_idx * 25.0
            color_outer = (244, 63, 94)
            color_inner = (56, 189, 248)
        elif target_type == TARGET_TYPE_FAST:
            f_hp = int(2 * sec_mult)
            self.hp = f_hp
            self.max_hp = f_hp
            self.points = 25
            size = random.randint(26, 36)
            base_speed = (TARGET_SPEED + 180.0) + sector_idx * 35.0
            color_outer = COLOR_MAGENTA
            color_inner = (56, 189, 248)
        elif target_type == TARGET_TYPE_ARMORED:
            armor_hp = int((14 + level * 5) * sec_mult)
            self.hp = armor_hp
            self.max_hp = armor_hp
            self.points = 90 + sector_idx * 30
            size = random.randint(58, 72)
            base_speed = (TARGET_SPEED - 20.0) + sector_idx * 20.0
            color_outer = COLOR_CRIMSON
            color_inner = (250, 204, 21)
        else: # Standard
            std_hp = int(3 * sec_mult)
            self.hp = std_hp
            self.max_hp = std_hp
            self.points = 15
            size = random.randint(36, 48)
            base_speed = TARGET_SPEED + sector_idx * 20.0
            color_outer = COLOR_TARGET
            color_inner = (255, 255, 255)

        self.size = size
        self.color_outer = color_outer
        self.color_inner = color_inner

        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        
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
        
        self.radius = size // 2
        self.speed = base_speed + speed_bonus
        self.time_accum = 0.0

    def _render_sprite(self):
        self.image.fill((0, 0, 0, 0))
        center = (self.size // 2, self.size // 2)
        
        if self.target_type == TARGET_TYPE_BOSS:
            pygame.draw.circle(self.image, (15, 23, 42), center, self.size // 2)
            border_col = (239, 68, 68) if self.rage_phase else self.color_outer
            pygame.draw.circle(self.image, border_col, center, self.size // 2, 4)
            pygame.draw.circle(self.image, self.color_inner, center, self.size // 4)
            
            for i in range(4):
                ang = self.shield_angle + i * (math.pi / 2)
                x1 = center[0] + math.cos(ang) * (self.size // 2 - 8)
                y1 = center[1] + math.sin(ang) * (self.size // 2 - 8)
                x2 = center[0] + math.cos(ang) * (self.size // 2)
                y2 = center[1] + math.sin(ang) * (self.size // 2)
                pygame.draw.line(self.image, (239, 68, 68) if self.rage_phase else (56, 189, 248), (x1, y1), (x2, y2), 5 if self.rage_phase else 3)

            bar_w = self.size - 12
            bar_h = 6
            pygame.draw.rect(self.image, (51, 65, 85), (6, 4, bar_w, bar_h))
            fill_w = max(0, int(bar_w * (self.hp / self.max_hp)))
            bar_fill_col = (239, 68, 68) if self.rage_phase else (250, 204, 21)
            pygame.draw.rect(self.image, bar_fill_col, (6, 4, fill_w, bar_h))

        elif self.target_type == TARGET_TYPE_VEHICLE:
            pygame.draw.rect(self.image, (30, 41, 59), (4, 16, self.size - 8, 28), border_radius=6)
            pygame.draw.rect(self.image, COLOR_NEON_RED, (4, 16, self.size - 8, 28), 2, border_radius=6)
            pygame.draw.rect(self.image, (15, 23, 42), (8, 38, 14, 8))
            pygame.draw.rect(self.image, (15, 23, 42), (self.size - 22, 38, 14, 8))
            pygame.draw.circle(self.image, COLOR_NEON_RED, (center[0], 22), 8)

        elif self.target_type == TARGET_TYPE_TURRET:
            pygame.draw.polygon(self.image, (51, 65, 85), [(4, self.size - 4), (self.size - 4, self.size - 4), (center[0] + 10, 18), (center[0] - 10, 18)])
            pygame.draw.circle(self.image, (100, 116, 139), (center[0], 22), 14)
            pygame.draw.circle(self.image, COLOR_NEON_RED, (center[0], 22), 6)
            pygame.draw.rect(self.image, (226, 232, 240), (center[0] - 8, 4, 4, 16))
            pygame.draw.rect(self.image, (226, 232, 240), (center[0] + 4, 4, 4, 16))

        elif self.target_type == TARGET_TYPE_CHASER:
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

        if self.max_hp > 1 and self.target_type not in (TARGET_TYPE_BOSS,):
            bar_w = self.size - 8
            bar_h = 4
            pygame.draw.rect(self.image, (51, 65, 85), (4, 2, bar_w, bar_h))
            fill_w = int(bar_w * (self.hp / self.max_hp))
            pygame.draw.rect(self.image, (250, 204, 21), (4, 2, fill_w, bar_h))

    def take_damage(self, amount: int = 1) -> bool:
        self.hp -= amount
        if self.target_type == TARGET_TYPE_BOSS and not self.rage_phase and self.hp <= self.max_hp // 2:
            self.rage_phase = True
        if self.hp <= 0:
            return True
        self._render_sprite()
        return False

    def update(self, dt: float, player_pos: tuple[float, float] = (200, 360), player_vel: tuple[float, float] = (0, 0), bullet_group=None) -> list[EnemyBullet]:
        effective_dt = dt
        self.time_accum += effective_dt
        new_enemy_bullets = []

        pred_aim_x = player_pos[0] + player_vel[0] * 0.35
        pred_aim_y = player_pos[1] + player_vel[1] * 0.35
        pred_aim = (pred_aim_x, pred_aim_y)

        bullet_speed = ENEMY_BULLET_SPEED + self.sector_idx * 50.0

        if self.target_type in (TARGET_TYPE_SHOOTER, TARGET_TYPE_TURRET, TARGET_TYPE_BOSS):
            self.shoot_timer -= effective_dt
            if self.shoot_timer <= 0:
                if self.target_type == TARGET_TYPE_TURRET:
                    self.shoot_timer = max(0.6, random.uniform(1.2, 1.8) - self.sector_idx * 0.15)
                    new_enemy_bullets.append(EnemyBullet(self.rect.center, pred_aim, speed=bullet_speed+80, angle_offset_deg=-14.0))
                    new_enemy_bullets.append(EnemyBullet(self.rect.center, pred_aim, speed=bullet_speed+100, angle_offset_deg=0.0))
                    new_enemy_bullets.append(EnemyBullet(self.rect.center, pred_aim, speed=bullet_speed+80, angle_offset_deg=14.0))
                elif self.target_type == TARGET_TYPE_SHOOTER:
                    self.shoot_timer = max(0.8, random.uniform(1.5, 2.2) - self.sector_idx * 0.20)
                    new_enemy_bullets.append(EnemyBullet(self.rect.center, pred_aim, speed=bullet_speed, angle_offset_deg=-8.0))
                    new_enemy_bullets.append(EnemyBullet(self.rect.center, pred_aim, speed=bullet_speed, angle_offset_deg=8.0))
                elif self.target_type == TARGET_TYPE_BOSS:
                    self.shoot_timer = 0.8 if self.rage_phase else 1.4
                    cx, cy = self.rect.center
                    if self.rage_phase:
                        # 360-Degree Radial Spiral Ring Attack Pattern!
                        for ring_i in range(12):
                            ang_deg = ring_i * (360.0 / 12.0)
                            rad = math.radians(ang_deg)
                            tx = cx + math.cos(rad) * 400.0
                            ty = cy + math.sin(rad) * 400.0
                            new_enemy_bullets.append(EnemyBullet((cx, cy), (tx, ty), speed=bullet_speed+110))
                    else:
                        offsets = [-32.0, -18.0, 0.0, 18.0, 32.0]
                        for offset in offsets:
                            new_enemy_bullets.append(EnemyBullet((cx, cy), pred_aim, speed=bullet_speed+100, angle_offset_deg=offset))

        if self.target_type == TARGET_TYPE_BOSS:
            rot_speed = 7.5 if self.rage_phase else 3.0
            self.shield_angle = (self.shield_angle + rot_speed * effective_dt) % 6.28318
            self._render_sprite()

            target_x = SCREEN_WIDTH - 190
            if self.pos.x > target_x:
                self.pos.x -= self.speed * effective_dt
            else:
                h_freq = 3.6 if self.rage_phase else 1.8
                self.pos.x = target_x + math.sin(self.time_accum * h_freq) * (35.0 if self.rage_phase else 20.0)
                self.pos.y = (SCREEN_HEIGHT // 2) + math.sin(self.time_accum * (3.5 if self.rage_phase else 2.5)) * 180.0
            
            self.rect.center = (round(self.pos.x), round(self.pos.y))

        elif self.target_type == TARGET_TYPE_CHASER:
            self.pos.x -= self.speed * effective_dt
            dy = player_pos[1] - self.pos.y
            tracking_step = math.copysign(min(abs(dy), (200.0 + self.sector_idx * 40.0) * effective_dt), dy)
            zigzag = math.sin(self.time_accum * 8.0) * 140.0 * effective_dt
            self.pos.y += tracking_step + zigzag
            self.rect.center = (round(self.pos.x), round(self.pos.y))

            if self.rect.right < 0:
                self.kill()

        elif self.target_type in (TARGET_TYPE_STANDARD, TARGET_TYPE_FAST):
            self.pos.x -= self.speed * effective_dt
            self.pos.y += math.sin(self.time_accum * 3.8) * 75.0 * effective_dt
            self.rect.center = (round(self.pos.x), round(self.pos.y))

            if self.rect.right < 0:
                self.kill()

        else:
            self.pos.x -= self.speed * effective_dt
            self.rect.centerx = round(self.pos.x)

            if self.rect.right < 0:
                self.kill()

        return new_enemy_bullets


class WaveManager:
    """
    4-Phase Sector Wave Escalation System:
    Wave 1: RECON SQUAD
    Wave 2: HEAVY FIRE TEAM
    Wave 3: HAZARD SURGE
    Wave 4: DREADNOUGHT BOSS ENCOUNTER
    """
    def __init__(self, target_score: int = 1200):
        self.target_score = target_score
        self.current_wave = 1
        self.wave_names = [
            "WAVE 1: RECON SQUAD 🛸",
            "WAVE 2: HEAVY FIRE TEAM ⚔️",
            "WAVE 3: HAZARD SURGE ⚠️",
            "WAVE 4: DREADNOUGHT BOSS ☠️"
        ]

    def update_wave(self, level_score: int) -> int:
        ratio = level_score / max(1, self.target_score)
        if ratio >= 0.70:
            self.current_wave = 4
        elif ratio >= 0.45:
            self.current_wave = 3
        elif ratio >= 0.20:
            self.current_wave = 2
        else:
            self.current_wave = 1
        return self.current_wave

    def get_wave_title(self) -> str:
        return self.wave_names[self.current_wave - 1]


class Spawner:
    """
    Target Spawner managing dynamic creation of Targets and Bosses per level/sector & wave.
    """
    def __init__(self, base_min_interval: float = 1.5, base_max_interval: float = 3.0):
        self.base_min_interval = base_min_interval
        self.base_max_interval = base_max_interval
        self.level = 1
        self.sector_idx = 0
        
        self.min_interval = base_min_interval
        self.max_interval = base_max_interval
        self.speed_bonus = 0.0
        self.boss_spawned = False

        self.timer = 0.0
        self.current_interval = random.uniform(self.min_interval, self.max_interval)

    def set_level(self, level: int, sector_idx: int = 0):
        self.level = level
        self.sector_idx = sector_idx
        self.boss_spawned = False
        reduction_min = (level - 1) * 0.25 + sector_idx * 0.20
        reduction_max = (level - 1) * 0.35 + sector_idx * 0.25
        self.min_interval = max(0.3, self.base_min_interval - reduction_min)
        self.max_interval = max(0.6, self.base_max_interval - reduction_max)
        self.speed_bonus = (level - 1) * 35.0 + sector_idx * 45.0

    def _select_target_type(self, current_wave: int = 1) -> str:
        if current_wave == 1:
            return random.choices([TARGET_TYPE_STANDARD, TARGET_TYPE_FAST], weights=[70, 30], k=1)[0]
        elif current_wave == 2:
            return random.choices([TARGET_TYPE_STANDARD, TARGET_TYPE_SHOOTER, TARGET_TYPE_TURRET, TARGET_TYPE_VEHICLE], weights=[35, 30, 20, 15], k=1)[0]
        elif current_wave == 3:
            return random.choices([TARGET_TYPE_FAST, TARGET_TYPE_ARMORED, TARGET_TYPE_SHOOTER, TARGET_TYPE_CHASER], weights=[30, 30, 20, 20], k=1)[0]
        else: # Wave 4
            return random.choices([TARGET_TYPE_FAST, TARGET_TYPE_ARMORED, TARGET_TYPE_CHASER, TARGET_TYPE_SHOOTER], weights=[30, 30, 20, 20], k=1)[0]

    def update(self, dt: float, target_group: pygame.sprite.Group, level_score: int, points_per_level: int, current_wave: int = 1) -> Target | None:
        if not self.boss_spawned and (current_wave == 4 or level_score >= int(points_per_level * 0.70)):
            self.boss_spawned = True
            boss = Target(target_type=TARGET_TYPE_BOSS, level=self.level, sector_idx=self.sector_idx)
            target_group.add(boss)
            return boss

        self.timer += dt
        if self.timer >= self.current_interval:
            self.timer = 0.0
            self.current_interval = random.uniform(self.min_interval, self.max_interval)
            
            target_type = self._select_target_type(current_wave)
            new_target = Target(target_type=target_type, speed_bonus=self.speed_bonus, level=self.level, sector_idx=self.sector_idx)
            target_group.add(new_target)
            return new_target

        return None
