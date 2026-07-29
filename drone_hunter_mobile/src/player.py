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


SKIN_THEMES = {
    0: {
        "name": "PLATINUM",
        "body": (241, 245, 249),
        "accent1": (250, 204, 21),
        "accent2": (6, 182, 212),
        "glow": (56, 189, 248, 160),
        "motors": (236, 72, 153),
    },
    1: {
        "name": "CYBERNEON",
        "body": (15, 23, 42),
        "accent1": (236, 72, 153),
        "accent2": (56, 189, 248),
        "glow": (236, 72, 153, 180),
        "motors": (56, 189, 248),
    },
    2: {
        "name": "SOVEREIGN",
        "body": (250, 204, 21),
        "accent1": (30, 41, 59),
        "accent2": (245, 158, 11),
        "glow": (250, 204, 21, 180),
        "motors": (217, 119, 6),
    },
    3: {
        "name": "CRIMSON",
        "body": (225, 29, 72),
        "accent1": (15, 23, 42),
        "accent2": (255, 120, 120),
        "glow": (239, 68, 68, 180),
        "motors": (168, 85, 247),
    }
}

class Player(pygame.sprite.Sprite):
    """
    Tactical Quadcopter Drone with multi-weapon loadouts, Wingman escort minidrones,
    Tactical Cloaking, EMP shockwave, Evasive Barrel Roll, Forcefield Shield,
    Auto-Lock Target Assist, Ultimate Overdrive Strike, and Skin Color Customization.
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
        self.dpad_up = False
        self.dpad_down = False
        self.dpad_left = False
        self.dpad_right = False
        self.slowmo_timer = 0.0
        self.shoot_timer = 0.0

        # Auto-Lock & Ultimate Overdrive
        self.auto_lock_enabled = False
        self.ultimate_charge = 0.0
        self.skin_theme = 0

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

        # Surface Dimensions (Enlarged to 118x76px with high-contrast hero armor styling)
        self.width = 118
        self.height = 76
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

    @property
    def energy(self) -> float:
        return self.health

    @energy.setter
    def energy(self, value: float):
        self.health = value

    @property
    def max_energy(self) -> float:
        return self.max_health

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

        # 0. Outer High-Visibility Cyan Silhouette Glow (Stands out against ANY dark background)
        pygame.draw.ellipse(self.original_image, (56, 189, 248, 160), (cx - 34, cy - 18, 68, 36), 3)
        pygame.draw.ellipse(self.original_image, (255, 255, 255, 220), (cx - 32, cy - 16, 64, 32), 1)

        # 1. Premium Platinum & Cyan Armor Chassis Body
        pygame.draw.ellipse(self.original_image, (15, 23, 42), (cx - 30, cy - 15, 60, 30))
        drone_color = (148, 163, 184, 100) if self.is_cloaked else (241, 245, 249) # Platinum White Body
        pygame.draw.ellipse(self.original_image, drone_color, (cx - 26, cy - 12, 52, 24))
        # Gold & Cyan Cyberpunk Accents
        pygame.draw.ellipse(self.original_image, (250, 204, 21), (cx - 16, cy - 8, 32, 16), 2)
        pygame.draw.ellipse(self.original_image, (6, 182, 212), (cx - 10, cy - 5, 20, 10))

        # 2. Front Optical Camera Sensor Lens (Glowing Cyan + Diamond White Core)
        pygame.draw.circle(self.original_image, (15, 23, 42), (cx + 25, cy), 9)
        pygame.draw.circle(self.original_image, (56, 189, 248), (cx + 25, cy), 6)
        pygame.draw.circle(self.original_image, (255, 255, 255), (cx + 25, cy), 3)

        # 3. Dual Gold & Chrome Laser Cannon Barrels
        pygame.draw.rect(self.original_image, (250, 204, 21), (cx + 16, cy - 15, 24, 5), border_radius=2)
        pygame.draw.rect(self.original_image, (250, 204, 21), (cx + 16, cy + 10, 24, 5), border_radius=2)
        pygame.draw.rect(self.original_image, (255, 255, 255), (cx + 22, cy - 14, 16, 3))
        pygame.draw.rect(self.original_image, (255, 255, 255), (cx + 22, cy + 11, 16, 3))

        # 4. Carbon Fiber Rotor Arms
        rotors = [
            (cx - 36, cy - 25),
            (cx + 36, cy - 25),
            (cx - 36, cy + 25),
            (cx + 36, cy + 25)
        ]
        for rx, ry in rotors:
            pygame.draw.line(self.original_image, (30, 41, 59), (cx, cy), (rx, ry), 6)
            pygame.draw.line(self.original_image, (56, 189, 248), (cx, cy), (rx, ry), 2)

        # 5. Animated Propellers, High-Contrast Neon Motors & Navigation Strobes
        blade_length = 22
        blade_dx = int(math.cos(self.rotor_angle) * blade_length)
        blade_dy = int(math.sin(self.rotor_angle) * blade_length)

        for idx, (rx, ry) in enumerate(rotors):
            # Vibrant Neon Magenta Motor Housing Pods (Distinct from White Body)
            pygame.draw.circle(self.original_image, (236, 72, 153), (rx, ry), 10)
            pygame.draw.circle(self.original_image, (250, 204, 21), (rx, ry), 6, 2)
            pygame.draw.circle(self.original_image, (255, 255, 255), (rx, ry), 3)

            # Glowing Electric Cyan Spinning Disc
            pygame.draw.ellipse(self.original_image, (34, 211, 238, 180), (rx - 23, ry - 9, 46, 18), 2)
            pygame.draw.line(self.original_image, (255, 255, 255, 240), (rx - blade_dx, ry - blade_dy), (rx + blade_dx, ry + blade_dy), 4)
            strobe_color = (52, 211, 153) if idx % 2 == 1 else (239, 68, 68)
            pygame.draw.circle(self.original_image, strobe_color, (rx, ry), 4)

        # 6. Render Forcefield Shield Bubble if Active
        if self.shield_hits > 0:
            pygame.draw.ellipse(self.original_image, (99, 102, 241, 200), (2, 2, self.width - 4, self.height - 4), 4)
            pygame.draw.ellipse(self.original_image, (165, 180, 252, 140), (5, 5, self.width - 10, self.height - 10), 2)

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
        move_down = keys[pygame.K_DOWN] or keys[pygame.K_s] or self.dpad_down
        
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
        else:
            self._aim_towards_mouse()

        # Update Wingmen and collect their fired bullets
        wingman_bullets = []
        for wm in self.wingmen:
            wm_b = wm.update(dt, self.pos, targets_group=targets_group)
            wingman_bullets.extend(wm_b)
        return wingman_bullets

    def _handle_movement_input(self, dt: float, particle_manager=None, audio_manager=None, move_down_key: bool = False):
        keys = pygame.key.get_pressed()
        move_up = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w] or self.dpad_up
        move_down = move_down_key or keys[pygame.K_DOWN] or keys[pygame.K_s] or self.dpad_down

        move_x = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT] or self.dpad_left:
            move_x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT] or self.dpad_right:
            move_x += 1

        self.is_thrusting = move_up
        speed_mult = (1.4 if self.overclock_timer > 0 else 1.0) * self.agility_mult
        if self.is_rolling:
            speed_mult *= ROLL_SPEED_BOOST

        # Play sound effect & spawn particles on ANY arrow/movement input!
        is_any_moving = move_up or move_down or (move_x != 0)

        if move_up:
            self.velocity.y += THRUST_FORCE * speed_mult * dt
            if particle_manager:
                particle_manager.spawn_thrust_smoke((self.pos.x - 30, self.pos.y + 8))

        if move_down:
            self.velocity.y += abs(THRUST_FORCE) * 2.8 * speed_mult * dt
            if particle_manager:
                particle_manager.spawn_thrust_smoke((self.pos.x - 30, self.pos.y - 8))

        if move_x < 0:
            if particle_manager:
                particle_manager.spawn_thrust_smoke((self.pos.x + 25, self.pos.y))

        if move_x > 0:
            if particle_manager:
                particle_manager.spawn_thrust_smoke((self.pos.x - 35, self.pos.y))

        if is_any_moving and audio_manager and random.random() < 0.30:
            audio_manager.play_thrust()

        # Plasma trail: emit skin-colored trail from back of drone while moving
        if is_any_moving and particle_manager and hasattr(particle_manager, "spawn_plasma_trail"):
            # skin_theme maps to trail colors matching each drone skin
            trail_colors = [
                (56, 189, 248),    # 0: PLATINUM — electric cyan
                (168, 85, 247),    # 1: CYBERNEON — neon purple
                (250, 204, 21),    # 2: SOVEREIGN — gold
                (239, 68, 68),     # 3: CRIMSON — red fire
            ]
            trail_color = trail_colors[getattr(self, "skin_theme", 0) % len(trail_colors)]
            # Emit from the rear of the drone (offset -30px behind direction of travel)
            trail_x = self.pos.x - 28 - move_x * 8
            trail_y = self.pos.y + random.uniform(-6, 6)
            particle_manager.spawn_plasma_trail((trail_x, trail_y), trail_color)

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

    def add_ultimate_charge(self, amount: float = 10.0):
        self.ultimate_charge = min(100.0, self.ultimate_charge + amount)

    def trigger_ultimate(self, targets_group=None, particle_manager=None, audio_manager=None, trigger_shake_fn=None) -> bool:
        """Unleashes screen-clearing Orbital Beam Strike when ultimate meter is 100% full."""
        if self.ultimate_charge >= 100.0:
            self.ultimate_charge = 0.0
            if audio_manager:
                audio_manager.play_emp()
            if trigger_shake_fn:
                trigger_shake_fn(16.0, 0.6)
            if particle_manager:
                particle_manager.spawn_shockwave((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), max_r=600, color=(250, 204, 21))
                particle_manager.spawn_spark((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), count=60, color=(56, 189, 248))
            if targets_group:
                for t in targets_group:
                    t.take_damage(500)
            return True
        return False

    def toggle_auto_lock(self) -> bool:
        self.auto_lock_enabled = not self.auto_lock_enabled
        return self.auto_lock_enabled

    def cycle_skin(self):
        self.skin_theme = (self.skin_theme + 1) % len(SKIN_THEMES)
        self._rotation_cache.clear()
        self._render_drone_sprite()
        return self.skin_theme

    def activate_shield(self, charges: int = 2):
        self.shield_hits = max(self.shield_hits, charges)

    def activate_overclock(self, duration: float = 5.0):
        self.overclock_timer = duration

    def trigger_overclock(self, duration: float = 6.0):
        self.activate_overclock(duration)

    def activate_slowmo(self, duration: float = 6.0):
        self.slowmo_timer = duration

    def trigger_slowmo(self, duration: float = 6.0):
        self.activate_slowmo(duration)

    def spawn_wingman(self):
        """Spawns an extra wingman drone escort (up to 4)."""
        if len(self.wingmen) < 4:
            new_idx = len(self.wingmen)
            self.wingmen.append(WingmanDrone(new_idx))
            self.wingman_count = len(self.wingmen)

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
