import random
import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT

class ParallaxBackground:
    """
    Multi-layered 2D scrolling parallax background creating a sense of forward flight.
    Dynamically switches sky gradients, mountain silhouettes, and building colors per Level!
    """
    def __init__(self):
        self.current_level = 1
        
        # 1. Starfield Layer
        self.stars = []
        for _ in range(90):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, int(SCREEN_HEIGHT * 0.75))
            speed = random.uniform(20, 55)
            radius = random.choice([1, 1, 2, 2])
            brightness = random.randint(160, 255)
            self.stars.append([x, y, speed, radius, brightness])

        self.mountain_scroll = 0.0
        self.mountain_speed = 40.0

        self.city_scroll = 0.0
        self.city_speed = 105.0

        # Build surfaces for initial level
        self.set_level(1)

    def set_level(self, level: int):
        """Generates dynamic level theme background graphics based on current level."""
        self.current_level = level
        
        # Theme Configurations
        if level == 1:
            # Cyberpunk Night
            self.bg_top_color = (15, 23, 42)      # Deep Navy
            self.bg_bottom_color = (30, 41, 59)   # Slate Blue
            self.mountain_color = (30, 41, 59)
            self.building_color = (15, 23, 42)
            self.window_colors = [(56, 189, 248), (14, 165, 233)] # Neon Cyan
        elif level == 2:
            # Desert Sunset & Neon Canyon
            self.bg_top_color = (67, 20, 52)      # Crimson Dusk
            self.bg_bottom_color = (124, 45, 18)   # Fiery Sunset Orange
            self.mountain_color = (88, 28, 28)    # Red Canyon Rock
            self.building_color = (40, 15, 20)
            self.window_colors = [(250, 204, 21), (251, 146, 60)] # Gold & Amber
        elif level == 3:
            # Cosmic Deep Space Station
            self.bg_top_color = (19, 14, 38)      # Deep Cosmic Purple
            self.bg_bottom_color = (36, 20, 68)   # Indigo Horizon
            self.mountain_color = (30, 27, 48)    # Lunar Crags
            self.building_color = (18, 14, 30)
            self.window_colors = [(52, 211, 153), (16, 185, 129)] # Emerald Green
        else: # Level 4+
            # Inferno Volcanic Matrix
            self.bg_top_color = (45, 10, 15)      # Dark Inferno Red
            self.bg_bottom_color = (80, 15, 20)   # Volcanic Glow
            self.mountain_color = (50, 15, 18)    # Obsidian Peaks
            self.building_color = (25, 8, 10)
            self.window_colors = [(239, 68, 68), (244, 63, 94)]  # Fiery Crimson Red

        # Regenerate Layer Surfaces with Level Theme Colors
        self.sky_surface = self._generate_sky_gradient()
        self.mountain_surface = self._generate_mountain_layer()
        self.city_surface = self._generate_city_layer()

    def _generate_sky_gradient(self) -> pygame.Surface:
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(self.bg_top_color[0] + (self.bg_bottom_color[0] - self.bg_top_color[0]) * ratio)
            g = int(self.bg_top_color[1] + (self.bg_bottom_color[1] - self.bg_top_color[1]) * ratio)
            b = int(self.bg_top_color[2] + (self.bg_bottom_color[2] - self.bg_top_color[2]) * ratio)
            pygame.draw.line(surf, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        return surf

    def _generate_mountain_layer(self) -> pygame.Surface:
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        points = [(0, SCREEN_HEIGHT)]
        
        x = 0
        while x <= SCREEN_WIDTH:
            y = SCREEN_HEIGHT - random.randint(180, 280)
            points.append((x, y))
            x += random.randint(80, 160)
        
        points.append((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.draw.polygon(surf, self.mountain_color, points)
        return surf

    def _generate_city_layer(self) -> pygame.Surface:
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        x = 0
        while x < SCREEN_WIDTH:
            width = random.randint(50, 110)
            height = random.randint(120, 220)
            rect = pygame.Rect(x, SCREEN_HEIGHT - height, width, height)
            pygame.draw.rect(surf, self.building_color, rect)
            pygame.draw.rect(surf, self.mountain_color, rect, 2) # Building border
            
            # Windows
            for wx in range(x + 10, x + width - 10, 16):
                for wy in range(SCREEN_HEIGHT - height + 15, SCREEN_HEIGHT - 20, 24):
                    if random.random() > 0.4:
                        w_color = random.choice(self.window_colors)
                        pygame.draw.rect(surf, w_color, (wx, wy, 8, 12))
            
            x += width + random.randint(5, 15)
        return surf

    def update(self, dt: float):
        # Update Stars
        for star in self.stars:
            star[0] -= star[2] * dt
            if star[0] < 0:
                star[0] = SCREEN_WIDTH
                star[1] = random.randint(0, int(SCREEN_HEIGHT * 0.75))

        # Scroll Layers
        self.mountain_scroll = (self.mountain_scroll + self.mountain_speed * dt) % SCREEN_WIDTH
        self.city_scroll = (self.city_scroll + self.city_speed * dt) % SCREEN_WIDTH

    def draw(self, surface: pygame.Surface):
        # 1. Draw Dynamic Level Sky Gradient
        surface.blit(self.sky_surface, (0, 0))

        # 2. Draw Starfield
        for x, y, speed, radius, brightness in self.stars:
            color = (brightness, brightness, min(255, brightness + 20))
            pygame.draw.circle(surface, color, (int(x), int(y)), radius)

        # 3. Draw Mountain Layer (Seamless wrapping)
        surface.blit(self.mountain_surface, (-self.mountain_scroll, 0))
        surface.blit(self.mountain_surface, (SCREEN_WIDTH - self.mountain_scroll, 0))

        # 4. Draw City Skyline Layer (Seamless wrapping)
        surface.blit(self.city_surface, (-self.city_scroll, 0))
        surface.blit(self.city_surface, (SCREEN_WIDTH - self.city_scroll, 0))
