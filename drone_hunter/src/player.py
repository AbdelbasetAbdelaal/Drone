import math
import pygame
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GRAVITY, THRUST_FORCE,
    MAX_FALL_SPEED, HORIZONTAL_SPEED, COLOR_DRONE, SHOOT_COOLDOWN
)
from src.bullet import Bullet

class Player(pygame.sprite.Sprite):
    """
    Drone class with gravity, upward thrust physics, mouse aiming rotation,
    and projectile shooting capabilities.
    """
    def __init__(self, pos: tuple[float, float]):
        super().__init__()
        
        # Create a detailed original Surface (pointing right by default at 0 degrees)
        self.original_image = pygame.Surface((50, 26), pygame.SRCALPHA)
        # Drone Main Body
        pygame.draw.ellipse(self.original_image, COLOR_DRONE, (0, 6, 40, 14))
        # Front Cannon Barrel (pointing right)
        pygame.draw.rect(self.original_image, (226, 232, 240), (32, 10, 18, 6))
        # Top Rotor / Cockpit
        pygame.draw.ellipse(self.original_image, (14, 165, 233), (12, 0, 20, 10))

        self.image = self.original_image.copy()
        
        # Position & Movement Vectors
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(0, 0)
        self.rect = self.image.get_rect(center=pos)
        
        # Circular collision radius
        self.radius = 18

        # Shooting Cooldown
        self.shoot_timer = 0.0

    def update(self, dt: float):
        # Update fire rate cooldown timer
        self.shoot_timer = max(0.0, self.shoot_timer - dt)

        # 1. Physics: Apply continuous gravity
        self.velocity.y += GRAVITY * dt
        if self.velocity.y > MAX_FALL_SPEED:
            self.velocity.y = MAX_FALL_SPEED

        # 2. Player Input (Thrust & Horizontal Movement)
        self._handle_movement_input(dt)

        # 3. Apply position updates & boundary checks
        self.pos += self.velocity * dt
        self._clamp_to_screen()

        # 4. Aiming: Rotate surface toward mouse position
        self._aim_towards_mouse()

    def _handle_movement_input(self, dt: float):
        keys = pygame.key.get_pressed()

        # Upward Thrust on Spacebar
        if keys[pygame.K_SPACE]:
            self.velocity.y += THRUST_FORCE * dt

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
        
        # Calculate rotation angle in degrees (Pygame rotates counter-clockwise)
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(-angle_rad)

        # Rotate original surface smoothly without stretching
        self.image = pygame.transform.rotate(self.original_image, angle_deg)
        self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))

    def _clamp_to_screen(self):
        half_w = self.original_image.get_width() // 2
        half_h = self.original_image.get_height() // 2

        # Horizontal clamping
        if self.pos.x < half_w:
            self.pos.x = half_w
            self.velocity.x = 0
        elif self.pos.x > SCREEN_WIDTH - half_w:
            self.pos.x = SCREEN_WIDTH - half_w
            self.velocity.x = 0

        # Vertical clamping
        if self.pos.y < half_h:
            self.pos.y = half_h
            self.velocity.y = 0  # Stop upward movement when hitting ceiling
        elif self.pos.y > SCREEN_HEIGHT - half_h:
            self.pos.y = SCREEN_HEIGHT - half_h
            self.velocity.y = 0  # Stop falling when hitting ground

        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def is_touching_ground(self) -> bool:

        half_h = self.original_image.get_height() // 2
        return self.pos.y >= SCREEN_HEIGHT - half_h


    def can_shoot(self) -> bool:
        return self.shoot_timer <= 0.0

    def shoot(self, target_pos: tuple[int, int]) -> Bullet | None:
        """
        Creates and returns a new Bullet instance towards target_pos if cooldown ready.
        """
        if self.can_shoot():
            self.shoot_timer = SHOOT_COOLDOWN
            return Bullet(start_pos=(self.pos.x, self.pos.y), target_pos=target_pos)
        return None
