import random
import math
import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, SECTORS

class CloudLayer:
    """Drifting atmospheric cloud fluff layer for realistic environment sky."""
    def __init__(self, count: int = 6):
        self.clouds = []
        for _ in range(count):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(20, 220)
            speed = random.uniform(15, 35)
            w = random.randint(140, 280)
            h = random.randint(40, 80)
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            color = (255, 255, 255, 30)
            pygame.draw.ellipse(surf, color, (0, 0, w, h))
            pygame.draw.ellipse(surf, color, (int(w * 0.2), int(-h * 0.2), int(w * 0.6), int(h * 0.8)))
            self.clouds.append([x, y, speed, w, h, surf])

    def update(self, dt: float):
        for c in self.clouds:
            c[0] -= c[2] * dt
            if c[0] < -c[3]:
                c[0] = SCREEN_WIDTH + random.randint(20, 100)
                c[1] = random.randint(20, 220)

    def draw(self, surface: pygame.Surface, color: tuple[int, int, int] = (255, 255, 255, 30)):
        for c in self.clouds:
            surface.blit(c[5], (c[0], c[1]))


class ParallaxBackground:
    """
    Multi-layered 2D scrolling parallax background supporting 5 unique sectors:
    - Sector 0: Megacity Skyline (Rain & Searchlights)
    - Sector 1: Cyber Factory Core (Smokestacks & Lava Channel)
    - Sector 2: Orbital Space Citadel (Nebulas & Asteroids)
    - Sector 3: Stormy Ocean Battlescape (Ocean Swells & Lightning Storms)
    - Sector 4: Neon Sun Desert Wasteland (Cyber Pyramids & Sand Dunes)
    """
    def __init__(self):
        self.current_sector = 0
        
        self.stars = []
        for _ in range(90):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, int(SCREEN_HEIGHT * 0.75))
            speed = random.uniform(20, 55)
            radius = random.choice([1, 1, 2, 2])
            brightness = random.randint(160, 255)
            self.stars.append([x, y, speed, radius, brightness])

        self.cloud_layer = CloudLayer(count=8)

        self.mountain_scroll = 0.0
        self.mountain_speed = 40.0

        self.city_scroll = 0.0
        self.city_speed = 105.0

        self.wave_time = 0.0
        self.lightning_flash_time = 0.0
        self.lightning_timer = random.uniform(3.0, 7.0)

        self.searchlight_angle = 0.0

        self.set_sector(0)

    def set_sector(self, sector_id: int):
        self.current_sector = sector_id
        
        if sector_id == 0:
            # Megacity Skyline
            self.bg_top_color = (15, 23, 42)      # Deep Navy
            self.bg_bottom_color = (30, 41, 59)   # Slate Blue
            self.mountain_color = (30, 41, 59)
            self.building_color = (15, 23, 42)
            self.window_colors = [(56, 189, 248), (14, 165, 233)]
        elif sector_id == 1:
            # Cyber Factory Core
            self.bg_top_color = (25, 12, 10)      # Industrial Rust
            self.bg_bottom_color = (55, 25, 15)   # Foundry Amber
            self.mountain_color = (45, 20, 15)
            self.building_color = (20, 10, 8)
            self.window_colors = [(245, 158, 11), (234, 88, 12)]
        elif sector_id == 2:
            # Orbital Space Citadel
            self.bg_top_color = (10, 5, 25)       # Cosmic Black/Purple
            self.bg_bottom_color = (28, 15, 50)   # Deep Nebula Violet
            self.mountain_color = (22, 18, 40)    # Lunar Crags
            self.building_color = (15, 10, 30)
            self.window_colors = [(168, 85, 247), (56, 189, 248)]
        elif sector_id == 3:
            # Stormy Ocean Battlescape
            self.bg_top_color = (6, 20, 34)       # Dark Tempest Blue
            self.bg_bottom_color = (12, 45, 75)   # Ocean Wave Horizon
            self.mountain_color = (10, 35, 60)    # Distant Sea Crags
            self.building_color = (6, 22, 40)
            self.window_colors = [(56, 189, 248), (186, 230, 253)]
        elif sector_id == 4:
            # Neon Sun Desert Wasteland
            self.bg_top_color = (45, 15, 25)      # Deep Synthwave Dusk
            self.bg_bottom_color = (195, 75, 25)  # Scorching Sand Amber
            self.mountain_color = (110, 35, 18)   # Dune Ridge
            self.building_color = (65, 22, 14)
            self.window_colors = [(250, 204, 21), (245, 158, 11)]
        else:
            self.bg_top_color = (15, 23, 42)
            self.bg_bottom_color = (30, 41, 59)
            self.mountain_color = (30, 41, 59)
            self.building_color = (15, 23, 42)
            self.window_colors = [(56, 189, 248), (14, 165, 233)]

        self.sky_surface = self._generate_sky_gradient()
        self.mountain_surface = self._generate_mountain_layer()
        self.city_surface = self._generate_foreground_layer()

    def set_level(self, level: int):
        sector_idx = (level - 1) % len(SECTORS)
        self.set_sector(sector_idx)

    def _generate_sky_gradient(self) -> pygame.Surface:
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(self.bg_top_color[0] + (self.bg_bottom_color[0] - self.bg_top_color[0]) * ratio)
            g = int(self.bg_top_color[1] + (self.bg_bottom_color[1] - self.bg_top_color[1]) * ratio)
            b = int(self.bg_top_color[2] + (self.bg_bottom_color[2] - self.bg_top_color[2]) * ratio)
            pygame.draw.line(surf, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Synthwave Sun for Desert (Sector 4)
        if self.current_sector == 4:
            cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT - 210
            sun_radius = 85
            
            glow_surf = pygame.Surface((sun_radius * 3, sun_radius * 3), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (250, 204, 21, 50), (sun_radius * 1.5, sun_radius * 1.5), sun_radius * 1.4)
            pygame.draw.circle(glow_surf, (245, 158, 11, 80), (sun_radius * 1.5, sun_radius * 1.5), sun_radius * 1.2)
            surf.blit(glow_surf, glow_surf.get_rect(center=(cx, cy)))

            pygame.draw.circle(surf, (250, 204, 21), (cx, cy), sun_radius)
            
            for stripe_y in range(cy - 20, cy + sun_radius, 12):
                stripe_h = max(2, int((stripe_y - (cy - 20)) * 0.12))
                pygame.draw.rect(surf, self.bg_bottom_color, (cx - sun_radius, stripe_y, sun_radius * 2, stripe_h))

        return surf

    def _generate_mountain_layer(self) -> pygame.Surface:
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        points = [(0, SCREEN_HEIGHT)]
        
        x = 0
        while x <= SCREEN_WIDTH:
            if self.current_sector == 4:
                y = SCREEN_HEIGHT - random.randint(140, 220)
            elif self.current_sector == 3:
                y = SCREEN_HEIGHT - random.randint(160, 240)
            else:
                y = SCREEN_HEIGHT - random.randint(180, 280)
            points.append((x, y))
            x += random.randint(80, 160)
        
        points.append((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.draw.polygon(surf, self.mountain_color, points)
        return surf

    def _generate_foreground_layer(self) -> pygame.Surface:
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        if self.current_sector == 4:
            x = 0
            while x < SCREEN_WIDTH:
                if random.random() < 0.35:
                    p_w = random.randint(120, 200)
                    p_h = random.randint(140, 210)
                    top_x = x + p_w // 2
                    bot_y = SCREEN_HEIGHT
                    top_y = SCREEN_HEIGHT - p_h
                    
                    pygame.draw.polygon(surf, self.building_color, [(x, bot_y), (top_x, top_y), (x + p_w, bot_y)])
                    pygame.draw.polygon(surf, (140, 50, 20), [(top_x, top_y), (x + p_w, bot_y), (top_x, bot_y)])
                    pygame.draw.circle(surf, (250, 204, 21), (top_x, top_y + 35), 6)
                    x += p_w + random.randint(30, 80)
                else:
                    d_w = random.randint(160, 260)
                    d_h = random.randint(80, 130)
                    pygame.draw.ellipse(surf, self.building_color, (x, SCREEN_HEIGHT - d_h, d_w, d_h * 2))
                    x += d_w - 40

        elif self.current_sector == 1:
            x = 0
            while x < SCREEN_WIDTH:
                width = random.randint(60, 110)
                height = random.randint(140, 230)
                rect = pygame.Rect(x, SCREEN_HEIGHT - height, width, height)
                pygame.draw.rect(surf, self.building_color, rect, border_radius=4)
                pygame.draw.rect(surf, (80, 35, 20), rect, 2, border_radius=4)
                pygame.draw.rect(surf, (245, 158, 11), (x + 8, SCREEN_HEIGHT - height + 10, width - 16, 6))
                x += width + random.randint(10, 25)

        elif self.current_sector == 2:
            x = 0
            while x < SCREEN_WIDTH:
                width = random.randint(70, 130)
                height = random.randint(110, 200)
                rect = pygame.Rect(x, SCREEN_HEIGHT - height, width, height)
                pygame.draw.rect(surf, self.building_color, rect)
                pygame.draw.rect(surf, (168, 85, 247), rect, 1)
                pygame.draw.line(surf, (56, 189, 248), (x + width // 2, SCREEN_HEIGHT - height), (x + width // 2, SCREEN_HEIGHT - height - 35), 2)
                pygame.draw.circle(surf, (56, 189, 248), (x + width // 2, SCREEN_HEIGHT - height - 35), 4)
                x += width + random.randint(20, 40)

        elif self.current_sector == 0:
            x = 0
            while x < SCREEN_WIDTH:
                width = random.randint(50, 110)
                height = random.randint(120, 220)
                rect = pygame.Rect(x, SCREEN_HEIGHT - height, width, height)
                pygame.draw.rect(surf, self.building_color, rect)
                pygame.draw.rect(surf, self.mountain_color, rect, 2)
                
                for wx in range(x + 10, x + width - 10, 16):
                    for wy in range(SCREEN_HEIGHT - height + 15, SCREEN_HEIGHT - 20, 24):
                        if random.random() > 0.4:
                            w_color = random.choice(self.window_colors)
                            pygame.draw.rect(surf, w_color, (wx, wy, 8, 12))
                
                x += width + random.randint(5, 15)

        return surf

    def update(self, dt: float):
        for star in self.stars:
            star[0] -= star[2] * dt
            if star[0] < 0:
                star[0] = SCREEN_WIDTH
                star[1] = random.randint(0, int(SCREEN_HEIGHT * 0.75))

        self.cloud_layer.update(dt)
        self.mountain_scroll = (self.mountain_scroll + self.mountain_speed * dt) % SCREEN_WIDTH
        self.city_scroll = (self.city_scroll + self.city_speed * dt) % SCREEN_WIDTH
        self.wave_time += dt
        self.searchlight_angle = (self.searchlight_angle + dt * 0.8) % 6.28318

        # Lightning Timer (Sector 3 Stormy Ocean & Sector 0 Megacity)
        if self.current_sector in (0, 3):
            self.lightning_timer -= dt
            if self.lightning_timer <= 0:
                self.lightning_flash_time = 0.08
                self.lightning_timer = random.uniform(4.0, 9.0)

        if self.lightning_flash_time > 0:
            self.lightning_flash_time -= dt

    def draw(self, surface: pygame.Surface):
        surface.blit(self.sky_surface, (0, 0))

        if self.current_sector != 4:
            for x, y, speed, radius, brightness in self.stars:
                color = (brightness, brightness, min(255, brightness + 20))
                pygame.draw.circle(surface, color, (int(x), int(y)), radius)

        # Draw Volumetric Cloud Layer
        c_alpha = (180, 220, 255, 25) if self.current_sector in (0, 3) else (250, 204, 21, 20)
        self.cloud_layer.draw(surface, color=c_alpha)

        # Megacity Sweeping Searchlight Beams
        if self.current_sector == 0:
            sl_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            sl_x = SCREEN_WIDTH * 0.35
            sl_angle = math.sin(self.searchlight_angle) * 0.45
            beam_x = sl_x + math.sin(sl_angle) * 450.0
            pygame.draw.polygon(sl_surf, (56, 189, 248, 28), [(sl_x, SCREEN_HEIGHT - 100), (beam_x - 60, 0), (beam_x + 60, 0)])
            surface.blit(sl_surf, (0, 0))

        surface.blit(self.mountain_surface, (-self.mountain_scroll, 0))
        surface.blit(self.mountain_surface, (SCREEN_WIDTH - self.mountain_scroll, 0))

        if self.current_sector == 3:
            # Animated Ocean Wave Swells with Foam Crests
            wave_surf = pygame.Surface((SCREEN_WIDTH, 140), pygame.SRCALPHA)
            points = [(0, 140)]
            foam_points = []
            for x in range(0, SCREEN_WIDTH + 20, 20):
                y = 45 + math.sin(x * 0.02 + self.wave_time * 4.0) * 18.0
                points.append((x, y))
                if random.random() < 0.3:
                    foam_points.append((x, y))
            points.append((SCREEN_WIDTH, 140))
            
            pygame.draw.polygon(wave_surf, (14, 116, 144, 210), points)
            for fx, fy in foam_points:
                pygame.draw.circle(wave_surf, (186, 230, 253, 220), (int(fx), int(fy)), random.randint(3, 7))
            
            surface.blit(wave_surf, (0, SCREEN_HEIGHT - 140))
        else:
            surface.blit(self.city_surface, (-self.city_scroll, 0))
            surface.blit(self.city_surface, (SCREEN_WIDTH - self.city_scroll, 0))

        # Dynamic Lightning Flash illumination
        if self.lightning_flash_time > 0:
            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((200, 230, 255, 80))
            surface.blit(flash_surf, (0, 0))
