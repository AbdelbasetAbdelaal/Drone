import math
import random
import pygame

class Particle(pygame.sprite.Sprite):
    """
    Individual particle effect for explosions, engine smoke, and sparks.
    """
    def __init__(self, pos: tuple[float, float], velocity: tuple[float, float],
                 color: tuple[int, int, int], radius: float, lifetime: float):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(velocity)
        self.color = color
        self.radius = radius
        self.max_lifetime = lifetime
        self.lifetime = lifetime
        
        self.image = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self._update_surface()

    def _update_surface(self):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        r = max(1.0, self.radius * (self.lifetime / self.max_lifetime))
        
        self.image.fill((0, 0, 0, 0))
        color_with_alpha = (*self.color[:3], alpha)
        pygame.draw.circle(self.image, color_with_alpha, (int(self.image.get_width() // 2), int(self.image.get_height() // 2)), int(r))

    def update(self, dt: float):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return

        self.pos += self.velocity * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self._update_surface()


class ParticleManager:
    """
    Manages spawning and updating particle systems (Thrust smoke, Explosions, Celebration Fireworks).
    """
    def __init__(self):
        self.particles = pygame.sprite.Group()

    def spawn_thrust_smoke(self, pos: tuple[float, float]):
        """Spawns small smoke/flame particles behind the drone thruster."""
        vx = random.uniform(-120, -60)
        vy = random.uniform(40, 100)
        color = random.choice([
            (255, 180, 50),  # Orange flame
            (255, 90, 30),   # Red flame
            (100, 116, 139)  # Grey smoke
        ])
        radius = random.uniform(3, 6)
        lifetime = random.uniform(0.2, 0.45)
        self.particles.add(Particle(pos, (vx, vy), color, radius, lifetime))

    def spawn_explosion(self, pos: tuple[float, float], count: int = 25, color: tuple[int, int, int] = (250, 204, 21)):
        """Spawns radial explosion particle bursts when a target is destroyed."""
        for _ in range(count):
            angle_speed = random.uniform(100, 350)
            angle = random.uniform(0, 6.28318)
            vx = math.cos(angle) * angle_speed
            vy = math.sin(angle) * angle_speed
            
            p_color = random.choice([
                color,
                (255, 255, 255),
                (239, 68, 68)
            ])
            radius = random.uniform(2, 7)
            lifetime = random.uniform(0.3, 0.7)
            self.particles.add(Particle(pos, (vx, vy), p_color, radius, lifetime))

    def spawn_celebration(self, screen_width: int, screen_height: int):
        """Spawns vibrant celebration fireworks confetti particles across the screen."""
        colors = [
            (56, 189, 248),   # Cyan
            (250, 204, 21),   # Gold
            (236, 72, 153),   # Magenta
            (52, 211, 153),   # Emerald
            (168, 85, 247),   # Purple
            (255, 255, 255)   # White
        ]

        # Fireworks Confetti Particles
        for _ in range(90):
            pos_x = random.uniform(100, screen_width - 100)
            pos_y = random.uniform(50, screen_height * 0.45)
            angle_speed = random.uniform(80, 280)
            angle = random.uniform(0, 6.28318)
            vx = math.cos(angle) * angle_speed
            vy = math.sin(angle) * angle_speed
            color = random.choice(colors)
            radius = random.uniform(3, 7)
            lifetime = random.uniform(1.2, 2.8)
            self.particles.add(Particle((pos_x, pos_y), (vx, vy), color, radius, lifetime))

    def update(self, dt: float):
        self.particles.update(dt)

    def draw(self, surface: pygame.Surface):
        self.particles.draw(surface)
