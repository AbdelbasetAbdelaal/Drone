import math
import random
import pygame

from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GRAVITY, THRUST_FORCE,
    MAX_FALL_SPEED, HORIZONTAL_SPEED, COLOR_DRONE, SHOOT_COOLDOWN, MAX_HEALTH
)
from src.bullet import Bullet

class Player(pygame.sprite.Sprite):
    """
    Realistic Tactical Quadcopter Drone sprite featuring animated spinning rotors,
    carbon-fiber frame arms, optical camera sensor pod, dual cannon barrels,
    and LED navigation lights.
    """
    def __init__(self, pos: tuple[float, float]):
        super().__init__()
        
        # Health / Battery System
        self.max_health = MAX_HEALTH
        self.health = MAX_HEALTH

        # Surface Dimensions (68x44 for a clear, high-detail drone)
        self.width = 68
        self.height = 44
        self.original_image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Propeller animation angle
        self.rotor_angle = 0.0

        self._render_drone_sprite()
        self.image = self.original_image.copy()
        
        # Position & Movement Vectors
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(0, 0)
        self.rect = self.image.get_rect(center=pos)
        
        # Circular collision radius
        self.radius = 22
        self.is_thrusting = False

        # Shooting Cooldown
        self.shoot_timer = 0.0

    def _render_drone_sprite(self):
        self.original_image.fill((0, 0, 0, 0))
        center_x = 28
        center_y = 22

        # 1. Carbon-Fiber Structural Arm Struts (4 Rotor Arms)
        arm_color = (51, 65, 85)     # Dark slate carbon fiber
        arm_border = (15, 23, 42)
        
        # Top-Left Arm & Top-Right Arm
        pygame.draw.line(self.original_image, arm_color, (center_x, center_y), (12, 8), 4)
        pygame.draw.line(self.original_image, arm_color, (center_x, center_y), (44, 8), 4)
        # Bottom-Left Arm & Bottom-Right Arm
        pygame.draw.line(self.original_image, arm_color, (center_x, center_y), (12, 36), 4)
        pygame.draw.line(self.original_image, arm_color, (center_x, center_y), (44, 36), 4)

        # 2. Dual Tactical Cannon Barrels (Mounted on side pylons)
        gun_color = (203, 213, 225)  # Metallic silver
        pygame.draw.rect(self.original_image, gun_color, (34, 15, 28, 4)) # Upper Cannon
        pygame.draw.rect(self.original_image, gun_color, (34, 25, 28, 4)) # Lower Cannon
        pygame.draw.circle(self.original_image, (250, 204, 21), (62, 17), 2) # Upper Muzzle Glow
        pygame.draw.circle(self.original_image, (250, 204, 21), (62, 27), 2) # Lower Muzzle Glow

        # 3. Main Stealth Armored Fuselage (Body)
        body_outer = (30, 41, 59)    # Dark metallic navy body
        body_inner = COLOR_DRONE     # Cyan accents
        
        pygame.draw.ellipse(self.original_image, body_outer, (12, 12, 32, 20))
        pygame.draw.ellipse(self.original_image, body_inner, (16, 14, 24, 16))

        # 4. Front Optical Sensor Camera Pod / Lens Eye
        pygame.draw.ellipse(self.original_image, (15, 23, 42), (38, 17, 12, 10))
        pygame.draw.circle(self.original_image, (14, 165, 233), (44, 22), 4) # Glowing Cyan Camera Lens
        pygame.draw.circle(self.original_image, (255, 255, 255), (45, 21), 1) # Glint highlight

        # 5. Rotor Motor Hubs & Spinning Propeller Blades
        rotor_hubs = [(12, 8), (44, 8), (12, 36), (44, 36)]
        
        # Blade offset calculation from animation angle
        blade_dx = int(math.cos(self.rotor_angle) * 14)
        blade_dy = int(math.sin(self.rotor_angle) * 6)

        for idx, (rx, ry) in enumerate(rotor_hubs):
            # Motor Hub Mount
            pygame.draw.circle(self.original_image, (15, 23, 42), (rx, ry), 5)
            
            # Spinning Propeller Disc / Blades (semi-transparent)
            pygame.draw.ellipse(self.original_image, (148, 163, 184, 140), (rx - 14, ry - 5, 28, 10), 1)
            pygame.draw.line(self.original_image, (226, 232, 240, 200), (rx - blade_dx, ry - blade_dy), (rx + blade_dx, ry + blade_dy), 2)

            # LED Strobe Navigation Lights (Green at front right, Red at rear)
            strobe_color = (52, 211, 153) if idx % 2 == 1 else (239, 68, 68)
            pygame.draw.circle(self.original_image, strobe_color, (rx, ry), 2)

    def update(self, dt: float, particle_manager=None, audio_manager=None):
        # Update fire rate cooldown timer
        self.shoot_timer = max(0.0, self.shoot_timer - dt)

        # Animate Propellers continuously
        self.rotor_angle = (self.rotor_angle + 25.0 * dt) % 6.28318
        self._render_drone_sprite()

        # 1. Physics: Apply continuous gravity
        self.velocity.y += GRAVITY * dt
        if self.velocity.y > MAX_FALL_SPEED:
            self.velocity.y = MAX_FALL_SPEED

        # 2. Player Input (Thrust & Movement)
        self._handle_movement_input(dt, particle_manager, audio_manager)

        # 3. Apply position updates & boundary checks
        self.pos += self.velocity * dt
        self._clamp_to_screen()

        # 4. Aiming: Rotate surface toward mouse position
        self._aim_towards_mouse()

    def _handle_movement_input(self, dt: float, particle_manager=None, audio_manager=None):
        keys = pygame.key.get_pressed()

        # Upward Movement / Thrust (Spacebar, Up Arrow, or W key)
        move_up = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        move_down = keys[pygame.K_DOWN] or keys[pygame.K_s]

        self.is_thrusting = move_up
        if move_up:
            self.velocity.y += THRUST_FORCE * dt
            if particle_manager:
                particle_manager.spawn_thrust_smoke((self.pos.x - 22, self.pos.y + 6))
            if audio_manager and random.random() < 0.2:
                audio_manager.play_thrust()

        if move_down:
            self.velocity.y += abs(THRUST_FORCE) * 0.7 * dt

        # Horizontal Movement (A/D or Left/Right Arrow Keys)
        move_x = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move_x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move_x += 1

        self.velocity.x = move_x * HORIZONTAL_SPEED

    def _aim_towards_mouse(self):
        mouse_pos = pygame.mouse.get_pos()
        dx = mouse_pos[0] - self.pos.x
        dy = mouse_pos[1] - self.pos.y
        
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(-angle_rad)

        self.image = pygame.transform.rotate(self.original_image, angle_deg)
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

    def take_damage(self, amount: int = 25) -> bool:
        self.health = max(0, self.health - amount)
        return self.health <= 0

    def can_shoot(self) -> bool:
        return self.shoot_timer <= 0.0

    def shoot(self, target_pos: tuple[int, int]) -> Bullet | None:
        if self.can_shoot():
            self.shoot_timer = SHOOT_COOLDOWN
            return Bullet(start_pos=(self.pos.x, self.pos.y), target_pos=target_pos)
        return None
