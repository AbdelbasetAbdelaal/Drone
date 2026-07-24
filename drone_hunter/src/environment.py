"""
================================================================================
                    DRONE HUNTER 3D - ENVIRONMENT MODULE
================================================================================
Decoupled 3D environmental components:
 - Building3D (Skyscrapers with glowing neon window grids)
 - Skybridge3D (Glass overhead skywalk bridges)
 - MonorailTrain3D (Speeding monorail bullet trains)
"""

import random
import pygame
from src.config import (
    COLOR_CYAN, COLOR_GOLD, COLOR_EMERALD, COLOR_CRIMSON, COLOR_MAGENTA,
    COLOR_ROOF, COLOR_ROAD
)
from src.engine3d import project_3d, get_fog_color

class Building3D:
    def __init__(self, x, z, w, h, d, color_val):
        self.x = x
        self.z = z
        self.w = w
        self.h = h
        self.d = d
        self.color = color_val
        self.windows = []
        for _ in range(random.randint(8, 22)):
            wx = random.uniform(-w/2.3, w/2.3)
            wy = random.uniform(4, h - 4)
            ww = random.uniform(0.6, 2.2)
            wh = random.uniform(1.8, 4.5)
            wc = random.choice([COLOR_CYAN, (253, 224, 71), COLOR_MAGENTA, (56, 189, 248)])
            self.windows.append((wx, wy, ww, wh, wc))

    def draw(self, surface, use_sprites, has_sprites):
        proj = project_3d(self.x, -10.0, self.z)
        if not proj: return
        sx, sy, scale = proj

        if use_sprites and has_sprites:
            if abs(self.x) > 28:
                r_post = max(3, int(6 * (scale / 40.0)))
                fog_post = get_fog_color((50, 65, 85), self.z)
                fog_lamp = get_fog_color(COLOR_CYAN, self.z)
                pygame.draw.line(surface, fog_post, (int(sx), int(sy)), (int(sx), int(sy - 30 * scale / 40.0)), max(2, int(4 * scale/40.0)))
                pygame.draw.circle(surface, fog_lamp, (int(sx), int(sy - 30 * scale / 40.0)), r_post)
            return

        y0 = -10.0
        y1 = y0 + self.h
        
        v000 = project_3d(self.x - self.w/2, y0, self.z - self.d/2)
        v100 = project_3d(self.x + self.w/2, y0, self.z - self.d/2)
        v110 = project_3d(self.x + self.w/2, y1, self.z - self.d/2)
        v010 = project_3d(self.x - self.w/2, y1, self.z - self.d/2)
        
        v001 = project_3d(self.x - self.w/2, y0, self.z + self.d/2)
        v101 = project_3d(self.x + self.w/2, y0, self.z + self.d/2)
        v111 = project_3d(self.x + self.w/2, y1, self.z + self.d/2)
        v011 = project_3d(self.x - self.w/2, y1, self.z + self.d/2)

        fog_col = get_fog_color(self.color, self.z)
        side_col = get_fog_color((15, 23, 42), self.z)
        top_col = get_fog_color((30, 41, 59), self.z)
        outline_c = get_fog_color(COLOR_CYAN, self.z)
        outline_m = get_fog_color(COLOR_MAGENTA, self.z)

        if v000 and v100 and v110 and v010:
            pts = [(v000[0], v000[1]), (v100[0], v100[1]), (v110[0], v110[1]), (v010[0], v010[1])]
            pygame.draw.polygon(surface, fog_col, pts)
            pygame.draw.polygon(surface, outline_c, pts, 1)
            for wx, wy, ww, wh, wc in self.windows:
                p1 = project_3d(self.x + wx, y0 + wy, self.z - self.d/2 - 0.1)
                p2 = project_3d(self.x + wx + ww, y0 + wy + wh, self.z - self.d/2 - 0.1)
                if p1 and p2:
                    pygame.draw.polygon(surface, get_fog_color(wc, self.z), [(p1[0], p1[1]), (p2[0], p1[1]), (p2[0], p2[1]), (p1[0], p2[1])])

        if v100 and v101 and v111 and v110 and self.x > 0:
            pts = [(v100[0], v100[1]), (v101[0], v101[1]), (v111[0], v111[1]), (v110[0], v110[1])]
            pygame.draw.polygon(surface, side_col, pts)
            pygame.draw.polygon(surface, outline_m, pts, 1)

        if v000 and v001 and v011 and v010 and self.x < 0:
            pts = [(v000[0], v000[1]), (v001[0], v001[1]), (v011[0], v011[1]), (v010[0], v010[1])]
            pygame.draw.polygon(surface, side_col, pts)
            pygame.draw.polygon(surface, outline_m, pts, 1)

        if v010 and v110 and v111 and v011:
            pts = [(v010[0], v010[1]), (v110[0], v110[1]), (v111[0], v111[1]), (v011[0], v011[1])]
            pygame.draw.polygon(surface, top_col, pts)
            pygame.draw.polygon(surface, outline_c, pts, 1)


class Skybridge3D:
    def __init__(self, z_pos):
        self.z = z_pos
        self.y = 18.0
        self.h = 4.0
        self.w = 70.0

    def draw(self, surface, screen_width, screen_height):
        p_left = project_3d(-self.w/2, self.y, self.z)
        p_right = project_3d(self.w/2, self.y, self.z)
        p_left_top = project_3d(-self.w/2, self.y + self.h, self.z)
        p_right_top = project_3d(self.w/2, self.y + self.h, self.z)

        if p_left and p_right and p_left_top and p_right_top:
            pts = [(p_left[0], p_left[1]), (p_right[0], p_right[1]), (p_right_top[0], p_right_top[1]), (p_left_top[0], p_left_top[1])]
            outline_c = get_fog_color(COLOR_CYAN, self.z)
            s = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            pygame.draw.polygon(s, (14, 165, 233, 70), pts)
            surface.blit(s, (0, 0))
            pygame.draw.polygon(surface, outline_c, pts, 2)
            pygame.draw.line(surface, COLOR_GOLD, (p_left[0], p_left[1]), (p_right[0], p_right[1]), 2)


class MonorailTrain3D:
    def __init__(self):
        self.x = -24.0
        self.y = -4.0
        self.z = 150.0
        self.speed = 45.0

    def update(self, dt):
        self.z -= self.speed * dt
        if self.z < -30.0: self.z = 180.0

    def draw(self, surface):
        proj = project_3d(self.x, self.y, self.z)
        if not proj: return
        sx, sy, scale = proj
        w = max(18, int(35 * (scale / 40.0)))
        h = max(8, int(14 * (scale / 40.0)))
        rect = pygame.Rect(sx - w/2, sy - h/2, w, h)
        fog_c = get_fog_color((203, 213, 225), self.z)
        pygame.draw.rect(surface, fog_c, rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_CRIMSON, rect, 2, border_radius=4)
        pygame.draw.line(surface, COLOR_CYAN, (sx - w/2 + 2, sy), (sx + w/2 - 2, sy), max(2, int(4 * scale/40.0)))
