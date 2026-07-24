import math
import random
import pygame

from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GRAVITY, THRUST_FORCE,
    MAX_FALL_SPEED, HORIZONTAL_SPEED, COLOR_DRONE, SHOOT_COOLDOWN, MAX_HEALTH,
    EMP_COOLDOWN_MAX, COLOR_SHIELD, ROLL_DURATION, ROLL_COOLDOWN, ROLL_SPEED_BOOST
)
from src.bullet import Bullet

class Player(pygame.sprite.Sprite):
    """
    Realistic Tactical Quadcopter Drone sprite featuring animated spinning rotors,
    carbon-fiber frame arms, optical camera sensor pod, dual cannon barrels,
    EMP Shockwave ability, Forcefield Shield, Evasive Barrel Roll, and Rotational Sprite Caching.
    """
    def __init__(self, pos: tuple[float, float]):
        super().__init__()
        
        # Base Health & Upgrade Multipliers
        self.max_health = MAX_HEALTH
        self.health = MAX_HEALTH
        self.emp_cooldown_max = EMP_COOLDOWN_MAX
        self.cooldown_mult = 1.0
        self.agility_mult = 1.0
        
        self.emp_cooldown = 0.0      # Seconds until EMP ready
        self.shield_hits = 0         # Shield forcefield charges
        self.overclock_timer = 0.0   # Overclock speed boost remaining
        self.slowmo_timer = 0.0      # Time Dilation Slow Motion remaining
        self.shoot_timer = 0.0

        # Evasive Barrel Roll Mechanics
        self.is_rolling = False
        self.roll_timer = 0.0
        self.roll_cooldown = 0.0
        self.roll_angle = 0.0
        self.roll_dir = 1.0

        # Surface Dimensions (68x44 for a clear, high-detail drone)
        self.width = 68
        self.height = 44
        self.original_image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Propeller animation angle
        self.rotor_angle = 0.0
        self._render_drone_sprite()
        self.image = self.original_image.copy()

        # Performance Optimization: Rotational Sprite Cache
        self._rotation_cache = {}
        
        # Position & Movement Vectors
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(0, 0)
        self.rect = self.image.get_rect(center=pos)
        
        # Collision Radius
        self.radius = 28
        self.is_thrusting = False

    def apply_shop_upgrades(self, upgrade_levels: dict[str, int]):
        """Applies persistent shop level upgrades to player stats."""
        bat_lvl = upgrade_levels.get("battery", 0)
        spd_lvl = upgrade_levels.get("speed", 0)
        fr_lvl = upgrade_levels.get("fire_rate", 0)
        emp_lvl = upgrade_levels.get("emp_recharge", 0)

        self.max_health = 100 + (bat_lvl * 20)
        self.health = self.max_health
        self.agility_mult = 1.0 + (spd_lvl * 0.15)
        self.cooldown_mult = max(0.4, 1.0 - (fr_lvl * 0.12))
        self.emp_cooldown_max = max(7.0, EMP_COOLDOWN_MAX - (emp_lvl * 2.5))

    def _render_drone_sprite(self):
        """
        Renders detailed vector graphics for the Quadcopter Drone sprite.
        """
        self.original_image.fill((0, 0, 0, 0))
        cx, cy = self.width // 2, self.height // 2

        # 1. Carbon Fiber Chassis Body
        pygame.draw.ellipse(self.original_image, (30, 41, 59), (cx - 18, cy - 10, 36, 20))
        pygame.draw.ellipse(self.original_image, COLOR_DRONE, (cx - 14, cy - 7, 28, 14), 2)

        # 2. Front Optical Camera Sensor Lens
        pygame.draw.circle(self.original_image, (15, 23, 42), (cx + 14, cy), 5)
        pygame.draw.circle(self.original_image, (56, 189, 248), (cx + 14, cy), 3)

        # 3. Dual Laser Cannon Barrels
        pygame.draw.rect(self.original_image, (148, 163, 184), (cx + 10, cy - 9, 14, 3))
        pygame.draw.rect(self.original_image, (148, 163, 184), (cx + 10, cy + 6, 14, 3))

        # 4. Carbon Fiber Rotor Arms (X-Shape Quadcopter Layout)
        rotors = [
            (cx - 20, cy - 14),  # Top-Left
            (cx + 20, cy - 14),  # Top-Right
            (cx - 20, cy + 14),  # Bottom-Left
            (cx + 20, cy + 14)   # Bottom-Right
        ]
        for rx, ry in rotors:
            pygame.draw.line(self.original_image, (71, 85, 105), (cx, cy), (rx, ry), 3)

        # 5. Animated Spinning Propeller Rotor Blades & Navigation Lights
        blade_length = 13
        blade_dx = int(math.cos(self.rotor_angle) * blade_length)
        blade_dy = int(math.sin(self.rotor_angle) * blade_length)

        for idx, (rx, ry) in enumerate(rotors):
            pygame.draw.circle(self.original_image, (15, 23, 42), (rx, ry), 5)
            pygame.draw.ellipse(self.original_image, (148, 163, 184, 140), (rx - 14, ry - 5, 28, 10), 1)
            pygame.draw.line(self.original_image, (226, 232, 240, 200), (rx - blade_dx, ry - blade_dy), (rx + blade_dx, ry + blade_dy), 2)

            strobe_color = (52, 211, 153) if idx % 2 == 1 else (239, 68, 68)
            pygame.draw.circle(self.original_image, strobe_color, (rx, ry), 2)

        # 6. Render Glowing Forcefield Shield Bubble if Active
        if self.shield_hits > 0:
            pygame.draw.ellipse(self.original_image, (99, 102, 241, 180), (2, 2, self.width - 4, self.height - 4), 3)
            pygame.draw.ellipse(self.original_image, (165, 180, 252, 100), (4, 4, self.width - 8, self.height - 8), 1)

    def trigger_roll(self, dir_x: float = 1.0) -> bool:
        """Triggers Evasive Barrel Roll with i-frame invulnerability if ready."""
        if self.roll_cooldown <= 0.0 and not self.is_rolling:
            self.is_rolling = True
            self.roll_timer = ROLL_DURATION
            self.roll_cooldown = ROLL_COOLDOWN
            self.roll_dir = dir_x if dir_x != 0 else 1.0
            return True
        return False

    def update(self, dt: float, particle_manager=None, audio_manager=None, wind_force: float = 0.0):
        # Update cooldown timers
        self.shoot_timer = max(0.0, self.shoot_timer - dt)
        self.emp_cooldown = max(0.0, self.emp_cooldown - dt)
        self.overclock_timer = max(0.0, self.overclock_timer - dt)
        self.slowmo_timer = max(0.0, self.slowmo_timer - dt)
        self.roll_cooldown = max(0.0, self.roll_cooldown - dt)

        # Animate Propellers continuously
        self.rotor_angle = (self.rotor_angle + 25.0 * dt) % 6.28318
        self._render_drone_sprite()

        # Update Barrel Roll duration & animation
        if self.is_rolling:
            self.roll_timer -= dt
            self.roll_angle = (self.roll_angle + self.roll_dir * 1800.0 * dt) % 360.0
            if particle_manager and random.random() < 0.6:
                particle_manager.create_evasive_sparks((self.pos.x, self.pos.y))
            if self.roll_timer <= 0.0:
                self.is_rolling = False
                self.roll_angle = 0.0

        # 1. Physics: Apply continuous gravity & environmental wind force
        keys = pygame.key.get_pressed()
        move_down = keys[pygame.K_DOWN] or keys[pygame.K_s]
        
        self.velocity.y += GRAVITY * dt
        self.velocity.x += wind_force * dt
        
        max_fall = 480.0 if move_down else MAX_FALL_SPEED
        if self.velocity.y > max_fall:
            self.velocity.y = max_fall

        # 2. Player Input (Thrust & Movement)
        self._handle_movement_input(dt, particle_manager, audio_manager, move_down)

        # 3. Apply position updates & boundary checks
        self.pos += self.velocity * dt
        self._clamp_to_screen()

        # 4. Aiming: Rotate surface toward mouse position or spin during barrel roll
        if self.is_rolling:
            rot_surf = pygame.transform.rotate(self.original_image, self.roll_angle)
            self.image = rot_surf
            self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        else:
            self._aim_towards_mouse()

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
        angle_deg = int(math.degrees(-angle_rad)) % 360  # Quantize angle for caching

        # Performance Optimization: Sprite Rotation Caching
        cache_key = (angle_deg, int(self.rotor_angle * 10), self.shield_hits > 0)
        if cache_key not in self._rotation_cache:
            if len(self._rotation_cache) > 250:
                self._rotation_cache.clear()
            self._rotation_cache[cache_key] = pygame.transform.rotate(self.original_image, angle_deg)

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
        """Triggers EMP Shockwave blast if cooldown is ready."""
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
        # Invulnerable during Evasive Barrel Roll!
        if self.is_rolling:
            return False

        # Forcefield Shield absorbs hit first!
        if self.shield_hits > 0:
            self.shield_hits -= 1
            return False

        self.health = max(0, self.health - amount)
        return self.health <= 0

    def recharge_battery(self, amount: int = 30):
        self.health = min(self.max_health, self.health + amount)

    def can_shoot(self) -> bool:
        return self.shoot_timer <= 0.0

    def shoot(self, target_pos: tuple[int, int], level: int = 1) -> list[Bullet]:
        if not self.can_shoot():
            return []

        base_cd = SHOOT_COOLDOWN * self.cooldown_mult
        cooldown = base_cd * 0.5 if self.overclock_timer > 0 else base_cd
        self.shoot_timer = cooldown
        bullets = []

        if level >= 3:
            # Triple Spread Shooting
            b_center = Bullet(start_pos=(self.pos.x, self.pos.y), target_pos=target_pos, angle_offset_deg=0.0)
            b_top = Bullet(start_pos=(self.pos.x, self.pos.y - 10), target_pos=target_pos, angle_offset_deg=-12.0)
            b_bot = Bullet(start_pos=(self.pos.x, self.pos.y + 10), target_pos=target_pos, angle_offset_deg=12.0)
            bullets.extend([b_center, b_top, b_bot])
        elif level == 2:
            # Double Twin Cannons
            b1 = Bullet(start_pos=(self.pos.x, self.pos.y - 8), target_pos=target_pos)
            b2 = Bullet(start_pos=(self.pos.x, self.pos.y + 8), target_pos=target_pos)
            bullets.extend([b1, b2])
        else:
            # Single Cannon
            b = Bullet(start_pos=(self.pos.x, self.pos.y), target_pos=target_pos)
            bullets.append(b)

        return bullets
