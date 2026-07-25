import math
import random
import pygame

from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GRAVITY, THRUST_FORCE,
    MAX_FALL_SPEED, HORIZONTAL_SPEED, COLOR_DRONE, SHOOT_COOLDOWN, MAX_HEALTH,
    EMP_COOLDOWN_MAX, COLOR_SHIELD, ROLL_DURATION, ROLL_COOLDOWN, ROLL_SPEED_BOOST,
    CLOAK_DURATION, CLOAK_COOLDOWN_MAX, WEAPON_PULSE, WEAPON_SCATTER,
    WEAPON_MISSILE, WEAPON_BEAM, WEAPON_DEFS, COLOR_GOLD, COLOR_MISSILE, COLOR_BEAM,
    COLOR_OVERCLOCK, COLOR_CYAN, COLOR_EMERALD, COLOR_CRIMSON, COLOR_PURPLE
)
from src.bullet import Bullet, HomingMissile, ContinuousBeam

class WingmanDrone(pygame.sprite.Sprite):
    """
    Automated escort minidrone that orbits the player drone and auto-fires at nearest enemies.
    """
    def __init__(self, index: int = 0):
        super().__init__()
        self.index = index
        self.orbit_angle = index * math.pi
        self.orbit_radius = 45.0
        self.shoot_timer = 0.0
        
        self.width = 24
        self.height = 18
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._render_sprite()
        
        self.pos = pygame.Vector2(0, 0)
        self.rect = self.image.get_rect()

    def _render_sprite(self):
        self.image.fill((0, 0, 0, 0))
        cx, cy = self.width // 2, self.height // 2
        pygame.draw.ellipse(self.image, (30, 41, 59), (2, 2, 20, 14))
        pygame.draw.circle(self.image, (56, 189, 248), (cx, cy), 4)
        pygame.draw.circle(self.image, (250, 204, 21), (cx + 5, cy), 2)

    def update(self, dt: float, player_pos: pygame.Vector2, targets_group=None) -> list[Bullet]:
        self.orbit_angle = (self.orbit_angle + 2.5 * dt) % (2 * math.pi)
        self.pos.x = player_pos.x + math.cos(self.orbit_angle) * self.orbit_radius
        self.pos.y = player_pos.y + math.sin(self.orbit_angle) * self.orbit_radius
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        self.shoot_timer = max(0.0, self.shoot_timer - dt)
        
        bullets = []
        if self.shoot_timer <= 0.0 and targets_group and len(targets_group) > 0:
            nearest = min(targets_group, key=lambda t: self.pos.distance_to(t.pos))
            if self.pos.distance_to(nearest.pos) < 400.0:
                self.shoot_timer = 0.50
                b = Bullet(start_pos=(self.pos.x, self.pos.y), target_pos=(nearest.pos.x, nearest.pos.y), damage=15)
                bullets.append(b)
        return bullets


class Player(pygame.sprite.Sprite):
    """
    Tactical Quadcopter Drone with multi-weapon loadouts, Wingman escort minidrones,
    Tactical Cloaking, EMP shockwave, Evasive Barrel Roll, and Forcefield Shield.
    """
    def __init__(self, pos: tuple[float, float]):
        super().__init__()
        
        self.max_health = MAX_HEALTH
        self.health = MAX_HEALTH
        self.emp_cooldown_max = EMP_COOLDOWN_MAX
        self.cooldown_mult = 1.0
        self.agility_mult = 1.0
        
        self.emp_cooldown = 0.0
        self.shield_hits = 0
        self.overclock_timer = 0.0
        self.slowmo_timer = 0.0
        self.shoot_timer = 0.0

        # Weapon System & Loadouts
        self.available_weapons = [WEAPON_PULSE, WEAPON_SCATTER]
        self.current_weapon_idx = 0
        self.active_weapon = WEAPON_PULSE

        # Tactical Cloaking Mechanics
        self.is_cloaked = False
        self.cloak_timer = 0.0
        self.cloak_cooldown = 0.0
        self.has_cloak_upgrade = False

        # Wingman Minidrones
        self.wingmen: list[WingmanDrone] = []
        self.wingman_count = 0

        # Evasive Barrel Roll Mechanics
        self.is_rolling = False
        self.roll_timer = 0.0
        self.roll_cooldown = 0.0
        self.roll_angle = 0.0
        self.roll_dir = 1.0

        # Surface Dimensions
        self.width = 68
        self.height = 44
        self.original_image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        self.rotor_angle = 0.0
        self._render_drone_sprite()
        self.image = self.original_image.copy()

        self._rotation_cache = {}
        
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(0, 0)
        self.rect = self.image.get_rect(center=pos)
        
        self.radius = 28
        self.is_thrusting = False
        self.emp_jammed_timer = 0.0
        self.invulnerable_timer = 0.0

    @property
    def is_invulnerable(self) -> bool:
        return self.is_rolling or self.invulnerable_timer > 0.0

    @property
    def speed(self) -> float:
        return HORIZONTAL_SPEED * self.agility_mult

    def apply_shop_upgrades(self, upgrade_levels: dict[str, int]):
        """Applies persistent shop level upgrades to player stats, weapons, and wingmen."""
        bat_lvl = upgrade_levels.get("battery", 0)
        spd_lvl = upgrade_levels.get("speed", 0)
        fr_lvl = upgrade_levels.get("fire_rate", 0)
        emp_lvl = upgrade_levels.get("emp_recharge", 0)
        wm_lvl = upgrade_levels.get("wingman", 0)
        cloak_lvl = upgrade_levels.get("cloak", 0)
        missile_lvl = upgrade_levels.get("missiles", 0)
        beam_lvl = upgrade_levels.get("beam", 0)

        self.max_health = 100 + (bat_lvl * 20)
        self.health = self.max_health
        self.agility_mult = 1.0 + (spd_lvl * 0.15)
        self.cooldown_mult = max(0.4, 1.0 - (fr_lvl * 0.12))
        self.emp_cooldown_max = max(7.0, EMP_COOLDOWN_MAX - (emp_lvl * 2.5))

        self.has_cloak_upgrade = (cloak_lvl > 0)
        
        # Unlock weapons
        self.available_weapons = [WEAPON_PULSE, WEAPON_SCATTER]
        if missile_lvl > 0 and WEAPON_MISSILE not in self.available_weapons:
            self.available_weapons.append(WEAPON_MISSILE)
        if beam_lvl > 0 and WEAPON_BEAM not in self.available_weapons:
            self.available_weapons.append(WEAPON_BEAM)

        # Setup Wingmen
        self.wingman_count = wm_lvl
        self.wingmen = [WingmanDrone(i) for i in range(self.wingman_count)]

    def cycle_weapon(self):
        """Swaps to the next available weapon loadout."""
        if len(self.available_weapons) > 1:
            self.current_weapon_idx = (self.current_weapon_idx + 1) % len(self.available_weapons)
            self.active_weapon = self.available_weapons[self.current_weapon_idx]
            return True
        return False

    def trigger_cloak(self) -> bool:
        """Triggers Tactical Cloaking if unlocked and ready."""
        if self.has_cloak_upgrade and self.cloak_cooldown <= 0.0 and not self.is_cloaked:
            self.is_cloaked = True
            self.cloak_timer = CLOAK_DURATION
            self.cloak_cooldown = CLOAK_COOLDOWN_MAX
            return True
        return False

    def trigger_roll(self, dir_x: float = 1.0) -> bool:
        if self.roll_cooldown <= 0.0 and not self.is_rolling:
            self.is_rolling = True
            self.roll_timer = ROLL_DURATION
            self.roll_cooldown = ROLL_COOLDOWN
            self.roll_dir = dir_x if dir_x != 0 else 1.0
            return True
        return False

    def _render_drone_sprite(self):
        self.original_image.fill((0, 0, 0, 0))
        cx, cy = self.width // 2, self.height // 2

        # 1. Carbon Fiber Chassis Body
        pygame.draw.ellipse(self.original_image, (30, 41, 59), (cx - 18, cy - 10, 36, 20))
        drone_color = (148, 163, 184, 100) if self.is_cloaked else COLOR_DRONE
        pygame.draw.ellipse(self.original_image, drone_color, (cx - 14, cy - 7, 28, 14), 2)

        # 2. Front Optical Camera Sensor Lens
        pygame.draw.circle(self.original_image, (15, 23, 42), (cx + 14, cy), 5)
        pygame.draw.circle(self.original_image, (56, 189, 248), (cx + 14, cy), 3)

        # 3. Dual Laser Cannon Barrels
        pygame.draw.rect(self.original_image, (148, 163, 184), (cx + 10, cy - 9, 14, 3))
        pygame.draw.rect(self.original_image, (148, 163, 184), (cx + 10, cy + 6, 14, 3))

        # 4. Carbon Fiber Rotor Arms
        rotors = [
            (cx - 20, cy - 14),
            (cx + 20, cy - 14),
            (cx - 20, cy + 14),
            (cx + 20, cy + 14)
        ]
        for rx, ry in rotors:
            pygame.draw.line(self.original_image, (71, 85, 105), (cx, cy), (rx, ry), 3)

        # 5. Animated Propellers & Navigation Lights
        blade_length = 13
        blade_dx = int(math.cos(self.rotor_angle) * blade_length)
        blade_dy = int(math.sin(self.rotor_angle) * blade_length)

        for idx, (rx, ry) in enumerate(rotors):
            pygame.draw.circle(self.original_image, (15, 23, 42), (rx, ry), 5)
            pygame.draw.ellipse(self.original_image, (148, 163, 184, 140), (rx - 14, ry - 5, 28, 10), 1)
            pygame.draw.line(self.original_image, (226, 232, 240, 200), (rx - blade_dx, ry - blade_dy), (rx + blade_dx, ry + blade_dy), 2)
            strobe_color = (52, 211, 153) if idx % 2 == 1 else (239, 68, 68)
            pygame.draw.circle(self.original_image, strobe_color, (rx, ry), 2)

        # 6. Render Forcefield Shield Bubble if Active
        if self.shield_hits > 0:
            pygame.draw.ellipse(self.original_image, (99, 102, 241, 180), (2, 2, self.width - 4, self.height - 4), 3)
            pygame.draw.ellipse(self.original_image, (165, 180, 252, 100), (4, 4, self.width - 8, self.height - 8), 1)

    def update(self, dt: float, particle_manager=None, audio_manager=None, wind_force: float = 0.0, targets_group=None) -> list[Bullet]:
        self.shoot_timer = max(0.0, self.shoot_timer - dt)
        self.emp_cooldown = max(0.0, self.emp_cooldown - dt)
        self.overclock_timer = max(0.0, self.overclock_timer - dt)
        self.slowmo_timer = max(0.0, self.slowmo_timer - dt)
        self.roll_cooldown = max(0.0, self.roll_cooldown - dt)
        self.cloak_cooldown = max(0.0, self.cloak_cooldown - dt)
        self.emp_jammed_timer = max(0.0, self.emp_jammed_timer - dt)

        # Update Cloak timer
        if self.is_cloaked:
            self.cloak_timer -= dt
            if self.cloak_timer <= 0.0:
                self.is_cloaked = False

        self.rotor_angle = (self.rotor_angle + 25.0 * dt) % 6.28318
        self._render_drone_sprite()

        if self.is_rolling:
            self.roll_timer -= dt
            self.roll_angle = (self.roll_angle + self.roll_dir * 1800.0 * dt) % 360.0
            if particle_manager and random.random() < 0.6:
                particle_manager.create_evasive_sparks((self.pos.x, self.pos.y))
            if self.roll_timer <= 0.0:
                self.is_rolling = False
                self.roll_angle = 0.0

        # Physics
        keys = pygame.key.get_pressed()
        move_down = keys[pygame.K_DOWN] or keys[pygame.K_s]
        
        self.velocity.y += GRAVITY * dt
        self.velocity.x += wind_force * dt
        
        max_fall = 480.0 if move_down else MAX_FALL_SPEED
        if self.velocity.y > max_fall:
            self.velocity.y = max_fall

        self._handle_movement_input(dt, particle_manager, audio_manager, move_down)
        self.pos += self.velocity * dt
        self._clamp_to_screen()

        if self.is_rolling:
            rot_surf = pygame.transform.rotate(self.original_image, self.roll_angle)
            self.image = rot_surf
            self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        else:
            self._aim_towards_mouse()

        # Update Wingmen and collect their fired bullets
        wingman_bullets = []
        for wm in self.wingmen:
            wm_b = wm.update(dt, self.pos, targets_group)
            wingman_bullets.extend(wm_b)
        return wingman_bullets

    def _handle_movement_input(self, dt: float, particle_manager=None, audio_manager=None, move_down: bool = False):
        keys = pygame.key.get_pressed()
        move_up = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]

        self.is_thrusting = move_up
        speed_mult = (1.4 if self.overclock_timer > 0 else 1.0) * self.agility_mult
        if self.is_rolling:
            speed_mult *= ROLL_SPEED_BOOST

        if move_up:
            self.velocity.y += THRUST_FORCE * speed_mult * dt
            if particle_manager:
                particle_manager.spawn_thrust_smoke((self.pos.x - 22, self.pos.y + 6))
            if audio_manager and random.random() < 0.2:
                audio_manager.play_thrust()

        if move_down:
            self.velocity.y += abs(THRUST_FORCE) * 2.8 * speed_mult * dt

        move_x = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move_x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move_x += 1

        if self.is_rolling and move_x == 0:
            move_x = self.roll_dir

        self.velocity.x = move_x * HORIZONTAL_SPEED * speed_mult

    def _aim_towards_mouse(self):
        mouse_pos = pygame.mouse.get_pos()
        dx = mouse_pos[0] - self.pos.x
        dy = mouse_pos[1] - self.pos.y
        
        angle_rad = math.atan2(dy, dx)
        angle_deg = int(math.degrees(-angle_rad)) % 360

        cache_key = (angle_deg, int(self.rotor_angle * 10), self.shield_hits > 0, self.is_cloaked)
        if cache_key not in self._rotation_cache:
            if len(self._rotation_cache) > 250:
                self._rotation_cache.clear()
            rot_img = pygame.transform.rotate(self.original_image, angle_deg)
            if self.is_cloaked:
                rot_img.set_alpha(120)
            self._rotation_cache[cache_key] = rot_img

        self.image = self._rotation_cache[cache_key]
        self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))

    def _clamp_to_screen(self):
        half_w = self.width // 2
        half_h = self.height // 2

        if self.pos.x < half_w:
            self.pos.x = half_w
            self.velocity.x = 0
        elif self.pos.x > SCREEN_WIDTH - half_w:
            self.pos.x = SCREEN_WIDTH - half_w
            self.velocity.x = 0

        if self.pos.y < half_h:
            self.pos.y = half_h
            self.velocity.y = 0
        elif self.pos.y > SCREEN_HEIGHT - half_h:
            self.pos.y = SCREEN_HEIGHT - half_h
            self.velocity.y = 0

        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def trigger_emp(self) -> bool:
        if self.emp_cooldown <= 0.0:
            self.emp_cooldown = self.emp_cooldown_max
            return True
        return False

    def activate_shield(self, charges: int = 2):
        self.shield_hits = max(self.shield_hits, charges)

    def activate_overclock(self, duration: float = 5.0):
        self.overclock_timer = duration

    def activate_slowmo(self, duration: float = 6.0):
        self.slowmo_timer = duration

    def take_damage(self, amount: int = 25) -> bool:
        if self.is_rolling or self.is_cloaked:
            return False

        if self.shield_hits > 0:
            self.shield_hits -= 1
            return False

        self.health = max(0, self.health - amount)
        return self.health <= 0

    def recharge_battery(self, amount: int = 30):
        self.health = min(self.max_health, self.health + amount)

    def can_shoot(self) -> bool:
        return self.shoot_timer <= 0.0 and self.emp_jammed_timer <= 0.0

    def shoot(self, target_pos: tuple[int, int], level: int = 1, targets_group=None) -> list[pygame.sprite.Sprite]:
        if not self.can_shoot():
            return []

        w_def = WEAPON_DEFS.get(self.active_weapon, WEAPON_DEFS[WEAPON_PULSE])
        base_cd = w_def["cooldown"] * self.cooldown_mult
        cooldown = base_cd * 0.5 if self.overclock_timer > 0 else base_cd
        self.shoot_timer = cooldown
        bullets = []

        if self.active_weapon == WEAPON_PULSE:
            if level >= 3:
                b_center = Bullet(start_pos=(self.pos.x, self.pos.y), target_pos=target_pos, angle_offset_deg=0.0, damage=35)
                b_top = Bullet(start_pos=(self.pos.x, self.pos.y - 10), target_pos=target_pos, angle_offset_deg=-12.0, damage=35)
                b_bot = Bullet(start_pos=(self.pos.x, self.pos.y + 10), target_pos=target_pos, angle_offset_deg=12.0, damage=35)
                bullets.extend([b_center, b_top, b_bot])
            elif level == 2:
                b1 = Bullet(start_pos=(self.pos.x, self.pos.y - 8), target_pos=target_pos, damage=35)
                b2 = Bullet(start_pos=(self.pos.x, self.pos.y + 8), target_pos=target_pos, damage=35)
                bullets.extend([b1, b2])
            else:
                b = Bullet(start_pos=(self.pos.x, self.pos.y), target_pos=target_pos, damage=35)
                bullets.append(b)

        elif self.active_weapon == WEAPON_SCATTER:
            for offset in [-24.0, -12.0, 0.0, 12.0, 24.0]:
                b = Bullet(start_pos=(self.pos.x, self.pos.y), target_pos=target_pos, angle_offset_deg=offset, color=COLOR_OVERCLOCK, speed=850.0, damage=22)
                bullets.append(b)

        elif self.active_weapon == WEAPON_MISSILE:
            m = HomingMissile(start_pos=(self.pos.x, self.pos.y), target_pos=target_pos, damage=75)
            bullets.append(m)

        elif self.active_weapon == WEAPON_BEAM:
            beam = ContinuousBeam(start_pos=(self.pos.x, self.pos.y), target_pos=target_pos, damage=28, level=level)
            bullets.append(beam)

        return bullets

    def draw_wingmen(self, surface: pygame.Surface):
        for wm in self.wingmen:
            surface.blit(wm.image, wm.rect)
