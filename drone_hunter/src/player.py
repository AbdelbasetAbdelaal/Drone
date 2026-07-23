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
    Drone player sprite with health management, gravity/thrust physics,
    particle integration, and mouse aiming capabilities.
    """
    def __init__(self, pos: tuple[float, float]):
        super().__init__()
        
        # Health / Battery System
        self.max_health = MAX_HEALTH
        self.health = MAX_HEALTH

        # Render high-detail sci-fi drone surface
        self.original_image = pygame.Surface((56, 30), pygame.SRCALPHA)
        self._render_drone_sprite()

        self.image = self.original_image.copy()
        
        # Position & Movement Vectors
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(0, 0)
        self.rect = self.image.get_rect(center=pos)
        
        # Circular collision radius
        self.radius = 20
        self.is_thrusting = False

        # Shooting Cooldown
        self.shoot_timer = 0.0

    def _render_drone_sprite(self):
        self.original_image.fill((0, 0, 0, 0))
        # Main Metallic Fuselage
        pygame.draw.ellipse(self.original_image, COLOR_DRONE, (4, 8, 44, 16))
        # Front Cannon Barrel
        pygame.draw.rect(self.original_image, (226, 232, 240), (36, 12, 18, 6))
        pygame.draw.circle(self.original_image, (250, 204, 21), (52, 15), 3) # Muzzle tip glow
        # Cockpit Dome
        pygame.draw.ellipse(self.original_image, (14, 165, 233), (16, 2, 22, 12))
        # Rear Thruster Exhaust Nozzle
        pygame.draw.rect(self.original_image, (100, 116, 139), (0, 11, 8, 10))

    def update(self, dt: float, particle_manager=None, audio_manager=None):
        # Update fire rate cooldown timer
        self.shoot_timer = max(0.0, self.shoot_timer - dt)

        # 1. Physics: Apply continuous gravity
        self.velocity.y += GRAVITY * dt
        if self.velocity.y > MAX_FALL_SPEED:
            self.velocity.y = MAX_FALL_SPEED

        # 2. Player Input (Thrust & Horizontal Movement)
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
                particle_manager.spawn_thrust_smoke((self.pos.x - 20, self.pos.y + 8))
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
        half_w = self.original_image.get_width() // 2
        half_h = self.original_image.get_height() // 2

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
        """Decreases player health. Returns True if dead."""
        self.health = max(0, self.health - amount)
        return self.health <= 0

    def can_shoot(self) -> bool:
        return self.shoot_timer <= 0.0

    def shoot(self, target_pos: tuple[int, int]) -> Bullet | None:
        if self.can_shoot():
            self.shoot_timer = SHOOT_COOLDOWN
            return Bullet(start_pos=(self.pos.x, self.pos.y), target_pos=target_pos)
        return None
