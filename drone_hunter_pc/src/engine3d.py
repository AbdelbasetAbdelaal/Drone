"""
================================================================================
               DRONE HUNTER 3D - PERFORMANCE 3D PROJECTION ENGINE
================================================================================
Decoupled 3D Perspective Projection Engine featuring:
 - Fast vector transforms & near-plane frustum clipping.
 - Exponential distance fog calculations.
 - Close-proximity 3D Follow Camera for AAA third-person perspective.
"""

import math
import random
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG

# --- Engine Configuration ---
FOV = 520.0
cam_pos = [0.0, 2.5, -5.5]
cam_rot_x = 0.08

shake_timer = 0.0
shake_intensity = 0.0

def update_camera_spring(player_x, player_y, player_z, hover_bob, dt):
    """Close-proximity 3D Follow Camera for prominent third-person drone view."""
    global cam_pos, shake_timer
    if shake_timer > 0:
        shake_timer -= dt

    target_cam_x = player_x * 0.65
    target_cam_y = (player_y + hover_bob) * 0.45 + 1.8
    target_cam_z = player_z - 5.5

    cam_pos[0] += (target_cam_x - cam_pos[0]) * 8.0 * dt
    cam_pos[1] += (target_cam_y - cam_pos[1]) * 8.0 * dt
    cam_pos[2] += (target_cam_z - cam_pos[2]) * 8.0 * dt

def trigger_screen_shake(duration, intensity):
    global shake_timer, shake_intensity
    shake_timer = duration
    shake_intensity = intensity

def project_3d(x, y, z):
    """Translates 3D World Space (X, Y, Z) -> 2D Screen Space (SX, SY, Scale)."""
    rx = x - cam_pos[0]
    ry = y - cam_pos[1]
    rz = z - cam_pos[2]
    
    cos_p, sin_p = math.cos(cam_rot_x), math.sin(cam_rot_x)
    ry_rot = ry * cos_p - rz * sin_p
    rz_rot = ry * sin_p + rz * cos_p

    if rz_rot <= 0.8:
        return None # Behind near clipping plane
    
    scale = FOV / rz_rot
    sx = (SCREEN_WIDTH / 2) + rx * scale
    sy = (SCREEN_HEIGHT / 2) - ry_rot * scale

    if shake_timer > 0:
        sx += random.uniform(-shake_intensity, shake_intensity)
        sy += random.uniform(-shake_intensity, shake_intensity)

    return (sx, sy, scale)

def get_fog_color(base_color, z_dist, max_z=180.0):
    if z_dist <= 0: return base_color
    fog_factor = min(1.0, max(0.0, z_dist / max_z)) ** 1.4
    r = int(base_color[0] * (1 - fog_factor) + COLOR_BG[0] * fog_factor)
    g = int(base_color[1] * (1 - fog_factor) + COLOR_BG[1] * fog_factor)
    b = int(base_color[2] * (1 - fog_factor) + COLOR_BG[2] * fog_factor)
    return (r, g, b)
