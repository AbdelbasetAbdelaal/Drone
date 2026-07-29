import math
import random
import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT

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


class FloatingText(pygame.sprite.Sprite):
    """
    Animated floating damage/score numbers that drift upward and fade out.
    """
    def __init__(self, pos: tuple[float, float], text: str, color: tuple[int, int, int] = (250, 204, 21), font_size: int = 24):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(random.uniform(-20, 20), -85.0)
        self.text = text
        self.color = color
        self.lifetime = 0.90
        self.max_lifetime = 0.90
        
        font = pygame.font.SysFont("Arial", font_size, bold=True)
        self.base_surface = font.render(text, True, color)
        self.image = self.base_surface.copy()
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt: float):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return

        self.pos += self.velocity * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        alpha = max(0, int(255 * (self.lifetime / self.max_lifetime)))
        self.image = self.base_surface.copy()
        self.image.set_alpha(alpha)


class EMPRing(pygame.sprite.Sprite):
    """
    Blinding expanding cyan EMP shockwave ring effect.
    """
    def __init__(self, pos: tuple[float, float]):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.radius = 10.0
        self.max_radius = 900.0
        self.speed = 1800.0
        self.lifetime = 0.5
        self.max_lifetime = 0.5

        self.image = pygame.Surface((1800, 1800), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt: float):
        self.lifetime -= dt
        self.radius += self.speed * dt

        if self.lifetime <= 0 or self.radius >= self.max_radius:
            self.kill()
            return

        alpha = max(0, int(255 * (self.lifetime / self.max_lifetime)))
        self.image.fill((0, 0, 0, 0))
        center = (900, 900)
        pygame.draw.circle(self.image, (56, 189, 248, alpha), center, int(self.radius), 8)
        pygame.draw.circle(self.image, (255, 255, 255, alpha), center, int(self.radius * 0.95), 3)


class RainStreak(pygame.sprite.Sprite):
    """Dynamic rain particle streak for storm weather hazards (Megacity)."""
    def __init__(self):
        super().__init__()
        self.pos = pygame.Vector2(random.randint(-100, SCREEN_WIDTH), random.randint(-50, 0))
        self.speed_y = random.uniform(600, 900)
        self.speed_x = random.uniform(-150, -50)
        self.length = random.randint(12, 22)
        
        self.image = pygame.Surface((8, self.length), pygame.SRCALPHA)
        pygame.draw.line(self.image, (186, 230, 253, 160), (4, 0), (0, self.length), 2)
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt: float):
        self.pos.x += self.speed_x * dt
        self.pos.y += self.speed_y * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if self.pos.y > SCREEN_HEIGHT + 20 or self.pos.x < -100:
            self.kill()


class SeaWaveParticle(pygame.sprite.Sprite):
    """Ocean sea spray droplet for Ocean sector."""
    def __init__(self):
        super().__init__()
        self.pos = pygame.Vector2(random.randint(-50, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT))
        self.speed_y = random.uniform(200, 500)
        self.speed_x = random.uniform(-250, -100)
        self.length = random.randint(14, 26)
        
        self.image = pygame.Surface((6, self.length), pygame.SRCALPHA)
        pygame.draw.line(self.image, (56, 189, 248, 200), (3, 0), (0, self.length), 2)
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt: float):
        self.pos.x += self.speed_x * dt
        self.pos.y += self.speed_y * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if self.pos.y > SCREEN_HEIGHT + 20 or self.pos.x < -50:
            self.kill()


class WaterSplashParticle(pygame.sprite.Sprite):
    """Upward water spray splash particle when projectiles or explosions hit the sea."""
    def __init__(self, pos: tuple[float, float]):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(random.uniform(-90, 90), random.uniform(-250, -120))
        self.lifetime = random.uniform(0.3, 0.6)
        self.max_lifetime = self.lifetime
        self.radius = random.uniform(2.5, 6.0)
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (186, 230, 253, 255), (6, 6), int(self.radius))
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt: float):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return
        self.velocity.y += 450.0 * dt
        self.pos += self.velocity * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        alpha = int(240 * (self.lifetime / self.max_lifetime))
        self.image.set_alpha(alpha)


class DroneVaporTrail(pygame.sprite.Sprite):
    """Glowing cyan vapor tail particle trailing behind the player drone."""
    def __init__(self, pos: tuple[float, float]):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(random.uniform(-40, -10), random.uniform(-15, 15))
        self.lifetime = 0.25
        self.max_lifetime = 0.25
        self.radius = 4.0
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (56, 189, 248, 255), (5, 5), int(self.radius))
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt: float):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return
        self.pos += self.velocity * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        alpha = int(220 * (self.lifetime / self.max_lifetime))
        self.image.set_alpha(alpha)


class SandDustParticle(pygame.sprite.Sprite):
    """Desert sandstorm dust particle for Desert sector."""
    def __init__(self):
        super().__init__()
        self.pos = pygame.Vector2(SCREEN_WIDTH + 20, random.randint(0, SCREEN_HEIGHT))
        self.speed_x = random.uniform(-380, -180)
        self.speed_y = random.uniform(-40, 40)
        self.lifetime = random.uniform(1.0, 2.5)
        self.max_lifetime = self.lifetime
        self.radius = random.uniform(2, 5)
        
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (217, 119, 6, 255), (6, 6), int(self.radius))
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt: float):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return
        self.pos += pygame.Vector2(self.speed_x, self.speed_y) * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        alpha = int(200 * (self.lifetime / self.max_lifetime))
        self.image.set_alpha(alpha)


class SparkParticle(pygame.sprite.Sprite):
    """Glowing industrial spark particle for Factory sector."""
    def __init__(self):
        super().__init__()
        self.pos = pygame.Vector2(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT))
        self.speed_y = random.uniform(30, 120)
        self.speed_x = random.uniform(-50, 50)
        self.lifetime = random.uniform(0.8, 2.0)
        self.max_lifetime = self.lifetime
        self.radius = random.uniform(2, 4)
        
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt: float):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return
        self.pos += pygame.Vector2(self.speed_x, self.speed_y) * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, (245, 158, 11, alpha), (5, 5), int(self.radius))


class StardustParticle(pygame.sprite.Sprite):
    """Drifting cosmic nebula stardust for Orbital Citadel sector."""
    def __init__(self):
        super().__init__()
        self.pos = pygame.Vector2(SCREEN_WIDTH + 10, random.randint(0, SCREEN_HEIGHT))
        self.speed_x = random.uniform(-180, -60)
        self.radius = random.uniform(1.5, 3.5)
        
        self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (192, 132, 252, 180), (4, 4), int(self.radius))
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt: float):
        self.pos.x += self.speed_x * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if self.pos.x < -20:
            self.kill()


class ParticleManager:
    """
    Manages spawning and updating particle systems.
    """
    def __init__(self):
        self.particles = pygame.sprite.Group()
        self.floating_texts = pygame.sprite.Group()
        self.weather_particles = pygame.sprite.Group()

    def spawn_thrust_smoke(self, pos: tuple[float, float]):
        vx = random.uniform(-120, -60)
        vy = random.uniform(40, 100)
        color = random.choice([(255, 180, 50), (255, 90, 30), (100, 116, 139)])
        radius = random.uniform(3, 6)
        lifetime = random.uniform(0.2, 0.45)
        self.particles.add(Particle(pos, (vx, vy), color, radius, lifetime))

    def spawn_drone_trail(self, pos: tuple[float, float]):
        self.particles.add(DroneVaporTrail(pos))

    def spawn_water_splash(self, pos: tuple[float, float], count: int = 8):
        for _ in range(count):
            self.particles.add(WaterSplashParticle(pos))

    def spawn_explosion(self, pos: tuple[float, float], count: int = 25, color: tuple[int, int, int] = (250, 204, 21)):
        for _ in range(count):
            angle_speed = random.uniform(100, 350)
            angle = random.uniform(0, 6.28318)
            vx = math.cos(angle) * angle_speed
            vy = math.sin(angle) * angle_speed
            p_color = random.choice([color, (255, 255, 255), (239, 68, 68)])
            radius = random.uniform(2, 7)
            lifetime = random.uniform(0.3, 0.7)
            self.particles.add(Particle(pos, (vx, vy), p_color, radius, lifetime))

    def spawn_enemy_death(self, pos: tuple[float, float], color: tuple[int, int, int] = (250, 204, 21)):
        """Satisfying 40-particle enemy death explosion with multi-color layers."""
        colors = [color, (255, 255, 255), (239, 68, 68), (250, 204, 21)]
        for _ in range(40):
            speed = random.uniform(80, 450)
            angle = random.uniform(0, 6.28318)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            p_color = random.choice(colors)
            radius = random.uniform(2.5, 8.0)
            lifetime = random.uniform(0.35, 0.85)
            self.particles.add(Particle(pos, (vx, vy), p_color, radius, lifetime))
        # Inner hot-core bright flash burst (small fast sparks)
        for _ in range(12):
            speed = random.uniform(300, 700)
            angle = random.uniform(0, 6.28318)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            radius = random.uniform(1.5, 4.0)
            lifetime = random.uniform(0.12, 0.30)
            self.particles.add(Particle(pos, (vx, vy), (255, 255, 220), radius, lifetime))

    def spawn_boss_explosion(self, pos: tuple[float, float]):
        """Massive 80-particle multi-stage boss death explosion with EMP ring."""
        layers = [
            ((239, 68, 68),   80, 600, 0.4, 1.0),   # Red outer ring
            ((250, 204, 21),  50, 400, 0.3, 0.7),   # Gold mid burst
            ((255, 255, 255), 30, 700, 0.1, 0.3),   # White shockwave sparks
            ((168, 85, 247),  25, 250, 0.5, 1.1),   # Purple debris
            ((56, 189, 248),  20, 500, 0.2, 0.5),   # Cyan energy fragments
        ]
        for p_color, count, max_spd, min_lt, max_lt in layers:
            for _ in range(count):
                speed = random.uniform(max_spd * 0.3, max_spd)
                angle = random.uniform(0, 6.28318)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                radius = random.uniform(3.0, 10.0)
                lifetime = random.uniform(min_lt, max_lt)
                self.particles.add(Particle(pos, (vx, vy), p_color, radius, lifetime))
        # EMP shockwave ring
        self.particles.add(EMPRing(pos))

    def spawn_plasma_trail(self, pos: tuple[float, float], color: tuple[int, int, int] = (56, 189, 248)):
        """Short-lived plasma trail particle emitted from drone's back while moving."""
        vx = random.uniform(-60, 60)
        vy = random.uniform(-40, 40)
        radius = random.uniform(2.5, 5.0)
        lifetime = random.uniform(0.12, 0.28)
        self.particles.add(Particle(pos, (vx, vy), color, radius, lifetime))

    def spawn_floating_text(self, pos: tuple[float, float], text: str, color: tuple[int, int, int] = (250, 204, 21), font_size: int = 24):
        self.floating_texts.add(FloatingText(pos, text, color, font_size))

    def spawn_emp_ring(self, pos: tuple[float, float]):
        self.particles.add(EMPRing(pos))

    def spawn_emp_shockwave(self, pos: tuple[float, float]):
        self.particles.add(EMPRing(pos))

    def spawn_spark(self, pos: tuple[float, float], count: int = 8, color: tuple[int, int, int] = (56, 189, 248)):
        for _ in range(count):
            angle_speed = random.uniform(80, 250)
            angle = random.uniform(0, 6.28318)
            vx = math.cos(angle) * angle_speed
            vy = math.sin(angle) * angle_speed
            radius = random.uniform(1.5, 4.0)
            lifetime = random.uniform(0.15, 0.35)
            self.particles.add(Particle(pos, (vx, vy), color, radius, lifetime))

    def spawn_sparks(self, pos: tuple[float, float], count: int = 8, color: tuple[int, int, int] = (56, 189, 248)):
        self.spawn_spark(pos, count, color)

    def create_evasive_sparks(self, pos: tuple[float, float]):
        for _ in range(3):
            vx = random.uniform(-180, 180)
            vy = random.uniform(-100, 100)
            color = random.choice([(56, 189, 248), (255, 255, 255), (14, 165, 233)])
            radius = random.uniform(2.0, 5.0)
            lifetime = random.uniform(0.15, 0.35)
            self.particles.add(Particle(pos, (vx, vy), color, radius, lifetime))

    def spawn_weather(self, weather_type: str):
        if weather_type == "rain":
            if len(self.weather_particles) < 70: self.weather_particles.add(RainStreak())
        elif weather_type == "sparks":
            if len(self.weather_particles) < 40: self.weather_particles.add(SparkParticle())
        elif weather_type == "stardust":
            if len(self.weather_particles) < 50: self.weather_particles.add(StardustParticle())
        elif weather_type == "sea_storm":
            if len(self.weather_particles) < 80: self.weather_particles.add(SeaWaveParticle())
        elif weather_type == "sandstorm":
            if len(self.weather_particles) < 70: self.weather_particles.add(SandDustParticle())

    def spawn_celebration(self, screen_width: int, screen_height: int):
        colors = [(56, 189, 248), (250, 204, 21), (236, 72, 153), (52, 211, 153), (168, 85, 247), (255, 255, 255)]
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
        self.floating_texts.update(dt)
        self.weather_particles.update(dt)

    def draw(self, surface: pygame.Surface):
        self.weather_particles.draw(surface)
        self.particles.draw(surface)
        self.floating_texts.draw(surface)

