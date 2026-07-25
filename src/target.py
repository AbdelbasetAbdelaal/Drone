import math
import random
import pygame
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_SPEED, ENEMY_BULLET_SPEED,
    TARGET_TYPE_STANDARD, TARGET_TYPE_FAST, TARGET_TYPE_ARMORED, TARGET_TYPE_SHOOTER, TARGET_TYPE_BOSS,
    TARGET_TYPE_TURRET, TARGET_TYPE_VEHICLE, TARGET_TYPE_CHASER,
    TARGET_TYPE_STEALTH_MIRAGE, TARGET_TYPE_EMP_DISRUPTER, TARGET_TYPE_TITAN_MECH,
    COLOR_TARGET, COLOR_MAGENTA, COLOR_CRIMSON, COLOR_CYAN, COLOR_NEON_RED, COLOR_OVERCLOCK, COLOR_PURPLE, COLOR_GOLD
)
from src.bullet import EnemyBullet

class Target(pygame.sprite.Sprite):
    """
    Target (Enemy) sprite supporting multiple enemy variants:
    - Standard, Fast, Armored, Shooter, Turret, Vehicle, Chaser.
    - NEW BOSS DRONES:
      1. Sky Fortress Boss (Classic 360-Degree Radial Spiral Salvos)
      2. Stealth Mirage Boss (Tactical Invisibility Cloak & Holographic Clones)
      3. EMP Disrupter Boss (EMP Shockwave Wave Jammer & Barrier Orbs)
      4. Super-Dreadnought Titan Mech (3-Phase Overclock Berserk Titan)
    """
    def __init__(self, target_type: str = TARGET_TYPE_STANDARD, speed_bonus: float = 0.0, level: int = 1, sector_idx: int = 0):
        super().__init__()
        self.target_type = target_type
        self.level = level
        self.sector_idx = sector_idx
        self.shield_angle = 0.0
        self.shoot_timer = random.uniform(0.3, 1.4)
        self.rage_phase = False
        
        # Stealth Mirage Boss specific stats
        self.is_cloaked = False
        self.cloak_timer = 0.0
        self.cloak_cooldown = 3.5
        self.is_decoy = False

        # EMP Disrupter Boss specific stats
        self.emp_pulse_timer = 4.0
        self.emp_wave_radius = 0.0
        self.is_emp_expanding = False

        # Titan Mech Boss specific stats
        self.boss_phase = 1

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

        elif target_type == TARGET_TYPE_STEALTH_MIRAGE:
            boss_hp = int((105 + (level - 1) * 50) * sec_mult)
            self.hp = boss_hp
            self.max_hp = boss_hp
            self.points = 800 + sector_idx * 250
            size = 110
            base_speed = 90.0 + sector_idx * 20.0
            color_outer = COLOR_PURPLE
            color_inner = COLOR_CYAN

        elif target_type == TARGET_TYPE_EMP_DISRUPTER:
            boss_hp = int((130 + (level - 1) * 60) * sec_mult)
            self.hp = boss_hp
            self.max_hp = boss_hp
            self.points = 1000 + sector_idx * 300
            size = 135
            base_speed = 65.0 + sector_idx * 15.0
            color_outer = (99, 102, 241)
            color_inner = COLOR_GOLD

        elif target_type == TARGET_TYPE_TITAN_MECH:
            boss_hp = int((200 + (level - 1) * 90) * sec_mult)
            self.hp = boss_hp
            self.max_hp = boss_hp
            self.points = 1500 + sector_idx * 400
            size = 155
            base_speed = 55.0 + sector_idx * 15.0
            color_outer = (190, 18, 60)
            color_inner = COLOR_OVERCLOCK

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
        if target_type in (TARGET_TYPE_BOSS, TARGET_TYPE_STEALTH_MIRAGE, TARGET_TYPE_EMP_DISRUPTER, TARGET_TYPE_TITAN_MECH):
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

    @property
    def score_value(self) -> int:
        return getattr(self, 'points', 100)

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

        elif self.target_type == TARGET_TYPE_STEALTH_MIRAGE:
            pygame.draw.polygon(self.image, COLOR_PURPLE, [
                (self.size - 4, center[1]), (12, 6), (center[0], center[1]), (12, self.size - 6)
            ])
            c_alpha = 70 if self.is_cloaked else 255
            pygame.draw.circle(self.image, COLOR_CYAN, center, self.size // 5)
            self.image.set_alpha(c_alpha)

            bar_w = self.size - 12
            bar_h = 6
            pygame.draw.rect(self.image, (51, 65, 85), (6, 4, bar_w, bar_h))
            fill_w = max(0, int(bar_w * (self.hp / self.max_hp)))
            pygame.draw.rect(self.image, COLOR_PURPLE, (6, 4, fill_w, bar_h))

        elif self.target_type == TARGET_TYPE_EMP_DISRUPTER:
            pygame.draw.circle(self.image, (30, 41, 59), center, self.size // 2)
            pygame.draw.circle(self.image, (99, 102, 241), center, self.size // 2, 5)
            pygame.draw.circle(self.image, COLOR_GOLD, center, self.size // 4)
            
            # EMP Expanding Ring visual
            if self.is_emp_expanding:
                pygame.draw.circle(self.image, COLOR_CYAN, center, int(self.emp_wave_radius % (self.size // 2)), 2)

            bar_w = self.size - 12
            bar_h = 6
            pygame.draw.rect(self.image, (51, 65, 85), (6, 4, bar_w, bar_h))
            fill_w = max(0, int(bar_w * (self.hp / self.max_hp)))
            pygame.draw.rect(self.image, (99, 102, 241), (6, 4, fill_w, bar_h))

        elif self.target_type == TARGET_TYPE_TITAN_MECH:
            # Titan Super-Dreadnought Hull
            pygame.draw.rect(self.image, (30, 41, 59), (10, 10, self.size - 20, self.size - 20), border_radius=12)
            border_col = COLOR_OVERCLOCK if self.boss_phase == 3 else (COLOR_CRIMSON if self.boss_phase == 2 else (56, 189, 248))
            pygame.draw.rect(self.image, border_col, (10, 10, self.size - 20, self.size - 20), 5, border_radius=12)
            pygame.draw.circle(self.image, COLOR_OVERCLOCK, center, self.size // 4)

            # Revolving Orbital Shield Orbs in Phase 1 & Phase 2
            if self.boss_phase < 3:
                for i in range(4):
                    ang = self.shield_angle + i * (math.pi / 2)
                    ox = int(center[0] + math.cos(ang) * (self.size // 2 - 12))
                    oy = int(center[1] + math.sin(ang) * (self.size // 2 - 12))
                    pygame.draw.circle(self.image, COLOR_CYAN, (ox, oy), 7)

            bar_w = self.size - 12
            bar_h = 8
            pygame.draw.rect(self.image, (51, 65, 85), (6, 2, bar_w, bar_h))
            fill_w = max(0, int(bar_w * (self.hp / self.max_hp)))
            pygame.draw.rect(self.image, border_col, (6, 2, fill_w, bar_h))

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

        if self.max_hp > 1 and self.target_type not in (TARGET_TYPE_BOSS, TARGET_TYPE_STEALTH_MIRAGE, TARGET_TYPE_EMP_DISRUPTER, TARGET_TYPE_TITAN_MECH):
            bar_w = self.size - 8
            bar_h = 4
            pygame.draw.rect(self.image, (51, 65, 85), (4, 2, bar_w, bar_h))
            fill_w = int(bar_w * (self.hp / self.max_hp))
            pygame.draw.rect(self.image, (250, 204, 21), (4, 2, fill_w, bar_h))

    def take_damage(self, amount: int = 1) -> bool:
        self.hp -= amount
        
        if self.target_type == TARGET_TYPE_BOSS and not self.rage_phase and self.hp <= self.max_hp // 2:
            self.rage_phase = True

        elif self.target_type == TARGET_TYPE_TITAN_MECH:
            if self.hp <= self.max_hp // 3:
                self.boss_phase = 3
            elif self.hp <= (self.max_hp * 2) // 3:
                self.boss_phase = 2

        if self.hp <= 0:
            return True
        self._render_sprite()
        return False

    def update(self, dt: float, player_pos: tuple[float, float] = (200, 360), player_vel: tuple[float, float] = (0, 0), bullet_group=None, player_obj=None) -> list[EnemyBullet]:
        effective_dt = dt
        self.time_accum += effective_dt
        new_enemy_bullets = []

        pred_aim_x = player_pos[0] + player_vel[0] * 0.35
        pred_aim_y = player_pos[1] + player_vel[1] * 0.35
        pred_aim = (pred_aim_x, pred_aim_y)

        bullet_speed = ENEMY_BULLET_SPEED + self.sector_idx * 50.0

        # Shooting Logic
        if self.target_type in (TARGET_TYPE_SHOOTER, TARGET_TYPE_TURRET, TARGET_TYPE_BOSS, TARGET_TYPE_STEALTH_MIRAGE, TARGET_TYPE_EMP_DISRUPTER, TARGET_TYPE_TITAN_MECH):
            self.shoot_timer -= effective_dt
            if self.shoot_timer <= 0:
                cx, cy = self.rect.center

                if self.target_type == TARGET_TYPE_TURRET:
                    self.shoot_timer = max(0.6, random.uniform(1.2, 1.8) - self.sector_idx * 0.15)
                    new_enemy_bullets.append(EnemyBullet((cx, cy), pred_aim, speed=bullet_speed+80, angle_offset_deg=-14.0))
                    new_enemy_bullets.append(EnemyBullet((cx, cy), pred_aim, speed=bullet_speed+100, angle_offset_deg=0.0))
                    new_enemy_bullets.append(EnemyBullet((cx, cy), pred_aim, speed=bullet_speed+80, angle_offset_deg=14.0))

                elif self.target_type == TARGET_TYPE_SHOOTER:
                    self.shoot_timer = max(0.8, random.uniform(1.5, 2.2) - self.sector_idx * 0.20)
                    new_enemy_bullets.append(EnemyBullet((cx, cy), pred_aim, speed=bullet_speed, angle_offset_deg=-8.0))
                    new_enemy_bullets.append(EnemyBullet((cx, cy), pred_aim, speed=bullet_speed, angle_offset_deg=8.0))

                elif self.target_type == TARGET_TYPE_STEALTH_MIRAGE:
                    self.shoot_timer = 1.2 if not self.is_cloaked else 2.5
                    if not self.is_cloaked:
                        new_enemy_bullets.append(EnemyBullet((cx, cy), pred_aim, speed=bullet_speed+150, angle_offset_deg=-6.0))
                        new_enemy_bullets.append(EnemyBullet((cx, cy), pred_aim, speed=bullet_speed+150, angle_offset_deg=6.0))

                elif self.target_type == TARGET_TYPE_EMP_DISRUPTER:
                    self.shoot_timer = 1.6
                    for offset in [-28.0, -14.0, 0.0, 14.0, 28.0]:
                        new_enemy_bullets.append(EnemyBullet((cx, cy), pred_aim, speed=bullet_speed+60, angle_offset_deg=offset))

                elif self.target_type == TARGET_TYPE_TITAN_MECH:
                    self.shoot_timer = 0.6 if self.boss_phase == 3 else (1.0 if self.boss_phase == 2 else 1.5)
                    if self.boss_phase == 3: # OVERCLOCK BERSERK: 360-Degree Radial Spiral
                        for ring_i in range(16):
                            ang_deg = ring_i * (360.0 / 16.0)
                            rad = math.radians(ang_deg)
                            tx = cx + math.cos(rad) * 400.0
                            ty = cy + math.sin(rad) * 400.0
                            new_enemy_bullets.append(EnemyBullet((cx, cy), (tx, ty), speed=bullet_speed+120))
                    else:
                        for offset in [-20.0, -10.0, 0.0, 10.0, 20.0]:
                            new_enemy_bullets.append(EnemyBullet((cx, cy), pred_aim, speed=bullet_speed+90, angle_offset_deg=offset))

                elif self.target_type == TARGET_TYPE_BOSS:
                    self.shoot_timer = 0.8 if self.rage_phase else 1.4
                    if self.rage_phase:
                        for ring_i in range(12):
                            ang_deg = ring_i * (360.0 / 12.0)
                            rad = math.radians(ang_deg)
                            tx = cx + math.cos(rad) * 400.0
                            ty = cy + math.sin(rad) * 400.0
                            new_enemy_bullets.append(EnemyBullet((cx, cy), (tx, ty), speed=bullet_speed+110))
                    else:
                        for offset in [-32.0, -18.0, 0.0, 18.0, 32.0]:
                            new_enemy_bullets.append(EnemyBullet((cx, cy), pred_aim, speed=bullet_speed+100, angle_offset_deg=offset))

        # Boss Movement & Special Powers Update
        if self.target_type == TARGET_TYPE_STEALTH_MIRAGE:
            self.cloak_timer += effective_dt
            if self.cloak_timer >= self.cloak_cooldown:
                self.cloak_timer = 0.0
                self.is_cloaked = not self.is_cloaked
                if self.is_cloaked:
                    # Relocate position while invisible
                    self.pos.y = random.randint(120, SCREEN_HEIGHT - 120)
            self._render_sprite()

        elif self.target_type == TARGET_TYPE_EMP_DISRUPTER:
            self.emp_pulse_timer -= effective_dt
            if self.emp_pulse_timer <= 0:
                self.emp_pulse_timer = 5.0
                self.is_emp_expanding = True
                self.emp_wave_radius = 0.0

            if self.is_emp_expanding:
                self.emp_wave_radius += 400.0 * effective_dt
                if player_obj and hasattr(player_obj, 'emp_jammed_timer'):
                    dx = player_pos[0] - self.pos.x
                    dy = player_pos[1] - self.pos.y
                    dist = math.hypot(dx, dy)
                    if dist <= 320.0:
                        player_obj.emp_jammed_timer = 1.5 # Jam player weapons!
                if self.emp_wave_radius > 350.0:
                    self.is_emp_expanding = False
            self._render_sprite()

        if self.target_type in (TARGET_TYPE_BOSS, TARGET_TYPE_STEALTH_MIRAGE, TARGET_TYPE_EMP_DISRUPTER, TARGET_TYPE_TITAN_MECH):
            rot_speed = 6.0 if self.rage_phase or self.boss_phase == 3 else 3.0
            self.shield_angle = (self.shield_angle + rot_speed * effective_dt) % 6.28318
            
            target_x = SCREEN_WIDTH - 200
            if self.pos.x > target_x:
                self.pos.x -= self.speed * effective_dt
            else:
                freq = 4.0 if self.boss_phase == 3 or self.rage_phase else 2.0
                self.pos.x = target_x + math.sin(self.time_accum * freq) * 30.0
                self.pos.y = (SCREEN_HEIGHT // 2) + math.sin(self.time_accum * freq * 0.8) * 190.0
            
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

    def is_stage_complete(self, level_score: int) -> bool:
        return level_score >= self.target_score


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
            
            # Select Boss type dynamically per Sector
            if self.sector_idx == 0:
                b_type = TARGET_TYPE_BOSS # Sky Dreadnought
            elif self.sector_idx == 1:
                b_type = TARGET_TYPE_EMP_DISRUPTER # Factory EMP Disrupter Boss
            elif self.sector_idx == 2:
                b_type = TARGET_TYPE_STEALTH_MIRAGE # Space Stealth Mirage Boss
            elif self.sector_idx == 3:
                b_type = TARGET_TYPE_EMP_DISRUPTER # Leviathan EMP Naval Boss
            elif self.sector_idx == 4:
                b_type = TARGET_TYPE_TITAN_MECH # Colossus Titan Mech Boss ☠️
            else:
                b_type = random.choice([TARGET_TYPE_BOSS, TARGET_TYPE_STEALTH_MIRAGE, TARGET_TYPE_EMP_DISRUPTER, TARGET_TYPE_TITAN_MECH])
            
            boss = Target(target_type=b_type, level=self.level, sector_idx=self.sector_idx)
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
