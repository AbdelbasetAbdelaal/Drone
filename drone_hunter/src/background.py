import random
import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT

class ParallaxBackground:
    """
    Multi-layered 2D scrolling parallax background creating a sense of forward flight.
    - Layer 1: Distant twinkling stars & nebula gradient
    - Layer 2: Distant mountain silhouettes (slow scroll speed)
    - Layer 3: Cyberpunk city skyline silhouettes (medium scroll speed)
    """
    def __init__(self):
        # 1. Starfield Layer
        self.stars = []
        for _ in range(80):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, int(SCREEN_HEIGHT * 0.7))
            speed = random.uniform(20, 50)
            radius = random.choice([1, 1, 2])
            brightness = random.randint(150, 255)
            self.stars.append([x, y, speed, radius, brightness])

        # 2. Distant Mountain Silhouette Layer
        self.mountain_surface = self._generate_mountain_layer()
        self.mountain_scroll = 0.0
        self.mountain_speed = 40.0

        # 3. Near City Skyline Layer
        self.city_surface = self._generate_city_layer()
        self.city_scroll = 0.0
        self.city_speed = 100.0

    def _generate_mountain_layer(self) -> pygame.Surface:
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        color = (30, 41, 59)  # Dark slate navy
        points = [(0, SCREEN_HEIGHT)]
        
        x = 0
        while x <= SCREEN_WIDTH:
            y = SCREEN_HEIGHT - random.randint(180, 280)
            points.append((x, y))
            x += random.randint(80, 160)
        
        points.append((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.draw.polygon(surf, color, points)
        return surf

    def _generate_city_layer(self) -> pygame.Surface:

        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        building_color = (15, 23, 42)    # Darkest navy
        window_color = (56, 189, 248)    # Neon cyan window dots
        
        x = 0
        while x < SCREEN_WIDTH:
            width = random.randint(50, 110)
            height = random.randint(120, 220)
            rect = pygame.Rect(x, SCREEN_HEIGHT - height, width, height)
            pygame.draw.rect(surf, building_color, rect)
            pygame.draw.rect(surf, (30, 41, 59), rect, 2) # Building border
            
            # Windows
            for wx in range(x + 10, x + width - 10, 16):
                for wy in range(SCREEN_HEIGHT - height + 15, SCREEN_HEIGHT - 20, 24):
                    if random.random() > 0.4:
                        pygame.draw.rect(surf, window_color, (wx, wy, 8, 12))
            
            x += width + random.randint(5, 15)
        return surf

    def update(self, dt: float):
        # Update Stars
        for star in self.stars:
            star[0] -= star[2] * dt
            if star[0] < 0:
                star[0] = SCREEN_WIDTH
                star[1] = random.randint(0, int(SCREEN_HEIGHT * 0.7))

        # Scroll Layers
        self.mountain_scroll = (self.mountain_scroll + self.mountain_speed * dt) % SCREEN_WIDTH
        self.city_scroll = (self.city_scroll + self.city_speed * dt) % SCREEN_WIDTH

    def draw(self, surface: pygame.Surface):
        # 1. Draw Starfield
        for x, y, speed, radius, brightness in self.stars:
            color = (brightness, brightness, min(255, brightness + 20))
            pygame.draw.circle(surface, color, (int(x), int(y)), radius)

        # 2. Draw Mountain Layer (Seamless wrapping)
        surface.blit(self.mountain_surface, (-self.mountain_scroll, 0))
        surface.blit(self.mountain_surface, (SCREEN_WIDTH - self.mountain_scroll, 0))

        # 3. Draw City Skyline Layer (Seamless wrapping)
        surface.blit(self.city_surface, (-self.city_scroll, 0))
        surface.blit(self.city_surface, (SCREEN_WIDTH - self.city_scroll, 0))
