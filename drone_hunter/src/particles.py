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


class Balloon(pygame.sprite.Sprite):
    """
    Floating party balloon that rises smoothly from the bottom of the screen during celebration.
    """
    def __init__(self, pos: tuple[float, float], color: tuple[int, int, int]):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.base_x = pos[0]
        self.speed = random.uniform(110, 210)
        self.wobble_speed = random.uniform(2.5, 5.0)
        self.wobble_amplitude = random.uniform(15, 35)
        self.time_accum = random.uniform(0, 6.28)
        self.color = color

        # Surface containing Balloon head, shine, knot, and hanging string
        width, height = 44, 90
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self._render_balloon()

    def _render_balloon(self):
        self.image.fill((0, 0, 0, 0))
        # Balloon Oval Head
        pygame.draw.ellipse(self.image, self.color, (6, 6, 32, 42))
        # Highlight Shine
        pygame.draw.ellipse(self.image, (255, 255, 255, 170), (12, 10, 10, 15))
        # Knot
        pygame.draw.polygon(self.image, self.color, [(18, 48), (26, 48), (22, 53)])
        # Hanging String
        pygame.draw.line(self.image, (226, 232, 240), (22, 53), (22, 85), 2)

    def update(self, dt: float):
        self.time_accum += dt
        self.pos.y -= self.speed * dt
        self.pos.x = self.base_x + math.sin(self.time_accum * self.wobble_speed) * self.wobble_amplitude
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        # Despawn once off top edge
        if self.rect.bottom < 0:
            self.kill()


class ParticleManager:
    """
    Manages spawning and updating particle systems, confetti, and balloons.
    """
    def __init__(self):
        self.particles = pygame.sprite.Group()
        self.balloons = pygame.sprite.Group()

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
        """Spawns both celebration fireworks confetti and rising balloons!"""
        colors = [
            (56, 189, 248),   # Cyan
            (250, 204, 21),   # Gold
            (236, 72, 153),   # Magenta
            (52, 211, 153),   # Emerald
            (168, 85, 247),   # Purple
            (239, 68, 68)     # Crimson Red
        ]

        # 1. Fireworks Confetti
        for _ in range(70):
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

        # 2. Rising Party Balloons
        for i in range(25):
            pos_x = random.uniform(40, screen_width - 40)
            pos_y = screen_height + random.uniform(30, 450)
            color = random.choice(colors)
            self.balloons.add(Balloon((pos_x, pos_y), color))

    def update(self, dt: float):
        self.particles.update(dt)
        self.balloons.update(dt)

    def draw(self, surface: pygame.Surface):
        self.particles.draw(surface)
        self.balloons.draw(surface)
