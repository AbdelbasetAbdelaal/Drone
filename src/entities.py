"""
================================================================================
                    DRONE HUNTER 3D - ENTITY COMPONENTS MODULE
================================================================================
Decoupled dynamic 3D gameplay entities using High-Fidelity Photorealistic Assets:
 - PlayerDrone3D (Perfectly proportioned 3D-Scaled High-Res Drone with smooth banking)
 - Enemy Target AI (TargetRover3D, TargetTurret3D, ChaserDrone3D, BossDreadnought3D)
 - Weaponry & FX (HomingMissile3D, SingularityDome3D, GravityTetherBeam, Bullet3D)
 - Pickups & Hazards (PowerupItem3D, ExplosiveBarrel3D, ThrusterParticle3D)
"""

import math
import random
import pygame

from src.config import (
    COLOR_CYAN, COLOR_GOLD, COLOR_EMERALD, COLOR_CRIMSON, COLOR_MAGENTA,
    COLOR_PURPLE, COLOR_COIN, COLOR_SHIELD, COLOR_OVERCLOCK, COLOR_SLOWMO,
    COLOR_ROOF, COLOR_ROAD, SCREEN_WIDTH, SCREEN_HEIGHT
)
from src.engine3d import project_3d, get_fog_color, trigger_screen_shake
from src.audio import play_synth_roll, play_synth_powerup, play_synth_explosion, play_synth_laser


class ThrusterParticle3D:
    def __init__(self, x, y, z):
        self.x = x + random.uniform(-0.3, 0.3)
        self.y = y + random.uniform(-0.2, 0.2)
        self.z = z - 0.5
        self.vx = random.uniform(-1.2, 1.2)
        self.vy = random.uniform(-1.0, 1.0)
        self.vz = -random.uniform(8.0, 16.0)
        self.radius = random.uniform(4.0, 7.0)
        self.alpha = 240.0
        self.life = 0.30

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        self.radius = max(1.0, self.radius - 14.0 * dt)
        self.alpha = max(0.0, self.alpha - 650.0 * dt)

    def draw(self, surface):
        if self.life <= 0 or self.alpha <= 0: return
        proj = project_3d(self.x, self.y, self.z)
        if not proj: return
        sx, sy, scale = proj
        r = max(1, int(self.radius * (scale / 40.0)))
        
        ratio = max(0.0, min(1.0, self.life / 0.30))
        c_r = int(14 * ratio + 30 * (1 - ratio))
        c_g = int(165 * ratio + 58 * (1 - ratio))
        c_b = int(233 * ratio + 138 * (1 - ratio))
        
        p_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(p_surf, (c_r, c_g, c_b, int(self.alpha)), (r, r), r)
        surface.blit(p_surf, (sx - r, sy - r))


class PlayerDrone3D:
    """High-Fidelity Photorealistic 3D Tactical Quadcopter Drone."""
    def __init__(self, upgrade_levels):
        self.x = 0.0
        self.y = 4.0
        self.z = 0.0
        self.speed = 18.0
        self.max_health = 100.0
        self.health = 100.0
        self.damage_mult = 1.0
        self.fire_rate = 0.18
        self.shoot_cooldown = 0.0
        
        self.emp_cooldown_max = 12.0
        self.emp_cooldown = 0.0
        self.roll_cooldown = 0.0
        self.tether_cooldown = 0.0
        self.missile_cooldown = 0.0
        self.cloak_cooldown = 0.0
        self.cloaked_timer = 0.0
        self.is_firing_beam = False
        
        self.is_rolling = False
        self.roll_angle = 0.0
        self.bank_angle = 0.0
        self.pitch_angle = 0.0
        self.recoil_z = 0.0
        self.hover_bob = 0.0
        self.roll_timer = 0.0
        self.slowmo_timer = 0.0
        self.overclock_timer = 0.0
        self.shield_hits = 0
        self.rotor_spin = 0.0

        self.apply_upgrades(upgrade_levels)

    def apply_upgrades(self, upgrade_levels):
        b_lvl = upgrade_levels.get("battery", 0)
        s_lvl = upgrade_levels.get("speed", 0)
        f_lvl = upgrade_levels.get("fire_rate", 0)
        e_lvl = upgrade_levels.get("emp_recharge", 0)
        d_lvl = upgrade_levels.get("damage", 0)

        self.max_health = 100.0 * (1.0 + b_lvl * 0.20)
        self.health = self.max_health
        self.speed = 18.0 * (1.0 + s_lvl * 0.15)
        self.fire_rate = max(0.06, 0.18 * (0.88 ** f_lvl))
        self.emp_cooldown_max = max(4.0, 12.0 - e_lvl * 2.5)
        self.damage_mult = 1.0 + d_lvl * 0.35

    def trigger_roll(self):
        if self.roll_cooldown <= 0 and not self.is_rolling:
            self.is_rolling = True
            self.roll_timer = 0.4
            self.roll_angle = 0.0
            self.roll_cooldown = 2.0
            play_synth_roll()
            return True
        return False

    def trigger_cloak(self, floating_popups):
        if self.cloak_cooldown <= 0 and self.cloaked_timer <= 0:
            self.cloaked_timer = 4.0
            self.cloak_cooldown = 10.0
            play_synth_powerup()
            floating_popups.append(["👻 OPTICAL CLOAK ENGAGED", self.x, self.y + 2.0, self.z, COLOR_CYAN, 1.0])

    def update(self, dt, game_state, joysticks, difficulty_mode, thruster_particles):
        if game_state != "playing": return

        self.rotor_spin += 3200.0 * dt
        self.hover_bob = math.sin(pygame.time.get_ticks() * 0.005) * 0.45

        if self.recoil_z < 0:
            self.recoil_z += 6.0 * dt
            if self.recoil_z > 0: self.recoil_z = 0.0

        if self.shoot_cooldown > 0: self.shoot_cooldown -= dt
        if self.emp_cooldown > 0: self.emp_cooldown -= dt
        if self.roll_cooldown > 0: self.roll_cooldown -= dt
        if self.tether_cooldown > 0: self.tether_cooldown -= dt
        if self.missile_cooldown > 0: self.missile_cooldown -= dt
        if self.cloak_cooldown > 0: self.cloak_cooldown -= dt
        if self.cloaked_timer > 0: self.cloaked_timer -= dt
        if self.slowmo_timer > 0: self.slowmo_timer -= dt
        if self.overclock_timer > 0: self.overclock_timer -= dt

        for _ in range(2):
            thruster_particles.append(ThrusterParticle3D(self.x, self.y + self.hover_bob, self.z + self.recoil_z))

        if self.is_rolling:
            self.roll_timer -= dt
            self.roll_angle += 900.0 * dt
            if self.roll_timer <= 0:
                self.is_rolling = False
                self.roll_angle = 0.0

        mx, my = pygame.mouse.get_pos()
        m_off_x = (mx - SCREEN_WIDTH / 2) / (SCREEN_WIDTH / 2)
        m_off_y = (my - SCREEN_HEIGHT / 2) / (SCREEN_HEIGHT / 2)

        keys = pygame.key.get_pressed()
        move_speed = self.speed * (1.4 if self.overclock_timer > 0 else 1.0)
        
        target_bank = m_off_x * -18.0
        target_pitch = m_off_y * 14.0

        joy_dx = 0.0
        joy_dy = 0.0
        if joysticks:
            j = joysticks[0]
            joy_dx = j.get_axis(0) if abs(j.get_axis(0)) > 0.15 else 0.0
            joy_dy = -j.get_axis(1) if abs(j.get_axis(1)) > 0.15 else 0.0

        if keys[pygame.K_d] or keys[pygame.K_RIGHT] or joy_dx > 0.2: target_bank = -30.0
        elif keys[pygame.K_a] or keys[pygame.K_LEFT] or joy_dx < -0.2: target_bank = 30.0

        if keys[pygame.K_w] or keys[pygame.K_UP] or joy_dy > 0.2: target_pitch = 18.0
        elif keys[pygame.K_s] or keys[pygame.K_DOWN] or joy_dy < -0.2: target_pitch = -18.0

        self.bank_angle += (target_bank - self.bank_angle) * 14.0 * dt
        self.pitch_angle += (target_pitch - self.pitch_angle) * 14.0 * dt

        is_moving = False
        dx = ((1.0 if keys[pygame.K_d] or keys[pygame.K_RIGHT] else 0.0) - (1.0 if keys[pygame.K_a] or keys[pygame.K_LEFT] else 0.0) + joy_dx) * move_speed * dt
        dy = ((1.0 if keys[pygame.K_SPACE] else 0.0) - (1.0 if keys[pygame.K_s] or keys[pygame.K_DOWN] else 0.0) + joy_dy) * move_speed * dt
        dz = ((1.0 if keys[pygame.K_w] or keys[pygame.K_UP] else 0.0)) * move_speed * dt

        if dx != 0 or dy != 0 or dz != 0: is_moving = True

        if difficulty_mode == 2 and is_moving:
            self.health = max(1.0, self.health - 1.8 * dt)

        self.x = max(-22.0, min(22.0, self.x + dx))
        self.y = max(-2.0, min(24.0, self.y + dy))
        self.z = max(-8.0, min(50.0, self.z + dz))

    def draw(self, surface, use_sprites, has_sprites, sprite_drone):
        """Renders Perfectly Proportioned Photorealistic 3D Drone Artwork."""
        curr_y = self.y + self.hover_bob
        curr_z = self.z + self.recoil_z
        
        proj = project_3d(self.x, curr_y, curr_z)
        if not proj: return
        sx, sy, scale = proj

        # Focused Plasma Beam (F Key)
        if self.is_firing_beam:
            p_end = project_3d(self.x, curr_y, curr_z + 120.0)
            if p_end:
                pygame.draw.line(surface, COLOR_OVERCLOCK, (int(sx), int(sy)), (int(p_end[0]), int(p_end[1])), 9)
                pygame.draw.line(surface, (255, 255, 255), (int(sx), int(sy)), (int(p_end[0]), int(p_end[1])), 3)

        # Ground Drop Shadow
        proj_shadow = project_3d(self.x, -10.0, curr_z)
        if proj_shadow:
            sh_x, sh_y, sh_scale = proj_shadow
            sw = max(18, int(52 * (sh_scale / 40.0)))
            sh = max(7, int(20 * (sh_scale / 40.0)))
            shadow_surf = pygame.Surface((sw * 2, sh * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 130), (0, 0, sw * 2, sh * 2))
            surface.blit(shadow_surf, (sh_x - sw, sh_y - sh/2))

        # Active Purple Force Shield
        if self.shield_hits > 0:
            r_shield = max(30, int(75 * (scale / 40.0)))
            pygame.draw.circle(surface, COLOR_PURPLE, (int(sx), int(sy)), r_shield, 4)
            pygame.draw.circle(surface, (255, 255, 255), (int(sx), int(sy)), max(2, r_shield - 4), 1)

        # PERFECTLY PROPORTIONED HIGH-RES DRONE SPRITE RENDERING
        if has_sprites and sprite_drone:
            # Scaled to ~220px wide (perfect arcade third-person drone scale)
            target_w = max(120, int(220 * (scale / 40.0)))
            aspect_ratio = sprite_drone.get_height() / max(1.0, sprite_drone.get_width())
            w_scaled = target_w
            h_scaled = int(target_w * aspect_ratio)

            if w_scaled > 10 and h_scaled > 10:
                scaled_img = pygame.transform.smoothscale(sprite_drone, (w_scaled, h_scaled))
                
                # Optical Cloak Transparency
                if self.cloaked_timer > 0:
                    scaled_img.set_alpha(75)

                # Smooth 3D Banking & Barrel Roll Rotation
                tot_angle = self.roll_angle + self.bank_angle
                if tot_angle != 0:
                    scaled_img = pygame.transform.rotate(scaled_img, -tot_angle)

                # Center Blit
                surface.blit(scaled_img, (sx - scaled_img.get_width() // 2, sy - scaled_img.get_height() // 2))
            return


class Bullet3D:
    def __init__(self, x, y, z, vx, vy, vz, is_player=True):
        self.x = x
        self.y = y
        self.z = z
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.is_player = is_player
        self.dodged = False

    def update(self, dt, player_drone):
        eff_dt = dt * (0.4 if (not self.is_player and player_drone.slowmo_timer > 0) else 1.0)
        self.x += self.vx * eff_dt
        self.y += self.vy * eff_dt
        self.z += self.vz * eff_dt

    def draw(self, surface):
        proj = project_3d(self.x, self.y, self.z)
        if not proj: return
        sx, sy, scale = proj
        
        trail_z = self.z - self.vz * 0.05
        trail_x = self.x - self.vx * 0.05
        trail_y = self.y - self.vy * 0.05
        proj_trail = project_3d(trail_x, trail_y, trail_z)
        
        c = (249, 115, 22) if self.is_player else COLOR_EMERALD
        fog_c = get_fog_color(c, self.z)
        core_c = get_fog_color((255, 255, 255), self.z)
        
        if proj_trail:
            tx, ty, _ = proj_trail
            thickness = max(2, int(7 * (scale / 40.0)))
            pygame.draw.line(surface, fog_c, (int(tx), int(ty)), (int(sx), int(sy)), thickness + 3)
            pygame.draw.line(surface, core_c, (int(tx), int(ty)), (int(sx), int(sy)), max(1, thickness - 2))
        else:
            r = max(2, int(5 * (scale / 40.0)))
            pygame.draw.circle(surface, fog_c, (int(sx), int(sy)), r)
            pygame.draw.circle(surface, (255, 255, 255), (int(sx), int(sy)), max(1, r - 2))


class HomingMissile3D:
    def __init__(self, start_pos, target):
        self.x, self.y, self.z = start_pos
        self.target = target
        self.speed = 70.0
        self.vx = random.uniform(-10.0, 10.0)
        self.vy = random.uniform(5.0, 15.0)
        self.vz = 20.0

    def update(self, dt, targets):
        if self.target and self.target in targets:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            dz = self.target.z - self.z
            dist = math.hypot(dx, dy, dz) or 1.0
            self.vx += (dx/dist * self.speed - self.vx) * 6.0 * dt
            self.vy += (dy/dist * self.speed - self.vy) * 6.0 * dt
            self.vz += (dz/dist * self.speed - self.vz) * 6.0 * dt

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt

    def draw(self, surface):
        proj = project_3d(self.x, self.y, self.z)
        if not proj: return
        sx, sy, scale = proj
        r = max(3, int(6 * (scale / 40.0)))
        pygame.draw.circle(surface, COLOR_GOLD, (int(sx), int(sy)), r)
        pygame.draw.circle(surface, (255, 255, 255), (int(sx), int(sy)), max(1, r - 2))


class GravityTetherBeam:
    def __init__(self, start_pos, target_pos):
        self.sx, self.sy, self.sz = start_pos
        self.ex, self.ey, self.ez = target_pos
        self.timer = 0.40

    def update(self, dt):
        self.timer -= dt

    def draw(self, surface):
        p1 = project_3d(self.sx, self.sy, self.sz)
        p2 = project_3d(self.ex, self.ey, self.ez)
        if p1 and p2:
            pygame.draw.line(surface, COLOR_CYAN, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), 4)
            pygame.draw.line(surface, (255, 255, 255), (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), 2)


class SingularityDome3D:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.radius = 3.0

    def update(self, dt, targets):
        self.radius += 50.0 * dt
        for t in targets:
            d = math.hypot(t.x - self.x, t.z - self.z)
            if d < 35.0:
                t.x += (self.x - t.x) * 3.0 * dt
                t.z += (self.z - t.z) * 3.0 * dt

    def draw(self, surface):
        proj = project_3d(self.x, self.y, self.z)
        if not proj: return
        sx, sy, scale = proj
        r = int(self.radius * (scale / 40.0))
        if r > 0:
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (168, 85, 247, 85), (r, r), r)
            pygame.draw.circle(s, (255, 255, 255, 180), (r, r), r, 3)
            surface.blit(s, (sx - r, sy - r))


class TargetRover3D:
    def __init__(self, x, z, current_level):
        self.x = x
        self.y = -9.0
        self.z = z
        self.w = 4.2
        self.h = 2.2
        self.d = 6.0
        self.hp = 14 + current_level * 4
        self.max_hp = self.hp
        self.points = 120
        self.target_type = "rover"
        self.shoot_timer = random.uniform(1.5, 2.5)
        self.lockon_timer = 0.0
        self.turret_angle = 0.0
        self.disabled_timer = 0.0

    def update(self, dt, player_drone, enemy_bullets, current_level, difficulty_mode):
        eff_dt = dt * (0.4 if player_drone.slowmo_timer > 0 else 1.0)
        spd_mult = 1.0 + (0.25 if difficulty_mode == 1 else (0.60 if difficulty_mode == 2 else 0.0))
        self.z -= (12.0 + current_level * 2.0) * spd_mult * eff_dt

        if self.disabled_timer > 0:
            self.disabled_timer -= dt
            return

        if player_drone.cloaked_timer <= 0:
            dx = player_drone.x - self.x
            dz = player_drone.z - self.z
            self.turret_angle = math.atan2(dx, dz or 1.0)

            self.shoot_timer -= eff_dt
            if self.shoot_timer <= 0.8: self.lockon_timer = 0.8
            if self.shoot_timer <= 0:
                self.shoot_timer = random.uniform(2.0, 3.2)
                self.lockon_timer = 0.0
                dist = math.hypot(dx, player_drone.y - self.y, dz) or 1.0
                b_spd = 48.0 * (1.35 if difficulty_mode == 1 else (1.50 if difficulty_mode == 2 else 1.0))
                enemy_bullets.append(Bullet3D(self.x, self.y + 1.2, self.z, (dx/dist)*b_spd, ((player_drone.y - self.y)/dist)*b_spd, (dz/dist)*b_spd, is_player=False))

    def draw(self, surface, use_sprites, has_sprites, sprite_rover, player_drone):
        proj = project_3d(self.x, self.y, self.z)
        if not proj: return
        sx, sy, scale = proj
        
        sw = max(12, int(26 * (scale / 40.0)))
        sh = max(4, int(8 * (scale / 40.0)))
        shadow_surf = pygame.Surface((sw * 2, sh * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 130), (0, 0, sw * 2, sh * 2))
        surface.blit(shadow_surf, (sx - sw, sy - sh/2))

        if self.lockon_timer > 0 and self.disabled_timer <= 0 and player_drone.cloaked_timer <= 0:
            p_player = project_3d(player_drone.x, player_drone.y, player_drone.z)
            if p_player:
                pygame.draw.line(surface, COLOR_CRIMSON, (int(sx), int(sy - 15 * scale/40.0)), (int(p_player[0]), int(p_player[1])), 2)

        if has_sprites and sprite_rover:
            w_scaled = int(sprite_rover.get_width() * (scale / 95.0))
            h_scaled = int(sprite_rover.get_height() * (scale / 95.0))
            if w_scaled > 4 and h_scaled > 4:
                scaled_img = pygame.transform.smoothscale(sprite_rover, (w_scaled, h_scaled))
                refl_img = pygame.transform.flip(scaled_img, False, True)
                refl_img.set_alpha(55)
                surface.blit(refl_img, (sx - w_scaled//2, sy))
                surface.blit(scaled_img, (sx - w_scaled//2, sy - h_scaled))
            h_px = h_scaled
        else:
            w_px = max(14, int(self.w * scale * 0.8))
            h_px = max(8, int(self.h * scale * 0.8))
            rect = pygame.Rect(sx - w_px/2, sy - h_px, w_px, h_px)
            fog_c = get_fog_color(COLOR_CRIMSON, self.z)
            pygame.draw.rect(surface, fog_c, rect)
            pygame.draw.rect(surface, get_fog_color((255, 255, 255), self.z), rect, 1)
            h_px = h_px

        if self.disabled_timer > 0:
            for _ in range(3):
                sp_x = sx + random.uniform(-18, 18)
                sp_y = sy - random.uniform(5, 30)
                pygame.draw.circle(surface, COLOR_CYAN, (int(sp_x), int(sp_y)), random.randint(2, 4))

        icon_y = sy - h_px/2
        s = max(14, int(26 * (scale / 40.0)))
        th = max(2, int(3 * (scale / 40.0)))
        pygame.draw.line(surface, COLOR_CRIMSON, (sx - 5, icon_y), (sx + 5, icon_y), th)
        pygame.draw.line(surface, COLOR_CRIMSON, (sx, icon_y - 5), (sx, icon_y + 5), th)


class TargetTurret3D:
    def __init__(self, x, y, z, current_level):
        self.x = x
        self.y = y
        self.z = z
        self.hp = 12 + current_level * 2
        self.max_hp = self.hp
        self.points = 85
        self.target_type = "turret"
        self.shoot_timer = random.uniform(1.2, 2.2)
        self.disabled_timer = 0.0

    def update(self, dt, player_drone, enemy_bullets, difficulty_mode):
        eff_dt = dt * (0.4 if player_drone.slowmo_timer > 0 else 1.0)
        spd_mult = 1.0 + (0.25 if difficulty_mode == 1 else (0.60 if difficulty_mode == 2 else 0.0))
        self.z -= 10.0 * spd_mult * eff_dt

        if self.disabled_timer > 0:
            self.disabled_timer -= dt
            return

        if player_drone.cloaked_timer <= 0:
            self.shoot_timer -= eff_dt
            if self.shoot_timer <= 0:
                self.shoot_timer = random.uniform(1.6, 2.5)
                dx = player_drone.x - self.x
                dy = player_drone.y - self.y
                dz = player_drone.z - self.z
                dist = math.hypot(dx, dy, dz) or 1.0
                b_spd = 45.0 * (1.35 if difficulty_mode == 1 else (1.50 if difficulty_mode == 2 else 1.0))
                enemy_bullets.append(Bullet3D(self.x, self.y, self.z, (dx/dist)*b_spd, (dy/dist)*b_spd, (dz/dist)*b_spd, is_player=False))

    def draw(self, surface):
        proj = project_3d(self.x, self.y, self.z)
        if not proj: return
        sx, sy, scale = proj
        r = max(5, int(9 * (scale / 40.0)))
        fog_base = get_fog_color((100, 116, 139), self.z)
        fog_glow = get_fog_color(COLOR_CRIMSON, self.z)
        pygame.draw.circle(surface, fog_base, (int(sx), int(sy)), r)
        pygame.draw.circle(surface, fog_glow, (int(sx), int(sy)), max(2, r - 3))


class ChaserDrone3D:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.hp = 3
        self.max_hp = 3
        self.points = 45
        self.target_type = "chaser"
        self.time_accum = random.uniform(0, 6.28)
        self.disabled_timer = 0.0

    def update(self, dt, player_drone, difficulty_mode):
        self.time_accum += dt
        if self.disabled_timer > 0:
            self.disabled_timer -= dt
            return

        spd_mult = 1.0 + (0.25 if difficulty_mode == 1 else (0.60 if difficulty_mode == 2 else 0.0))
        if player_drone.cloaked_timer <= 0:
            dir_x = math.copysign(min(abs(player_drone.x - self.x), 8.0 * spd_mult * dt), player_drone.x - self.x)
            dir_y = math.copysign(min(abs(player_drone.y - self.y), 6.0 * spd_mult * dt), player_drone.y - self.y)
            self.x += dir_x
            self.y += dir_y + math.sin(self.time_accum * 6.0) * 8.0 * dt
        self.z -= 18.0 * spd_mult * dt

    def draw(self, surface):
        proj = project_3d(self.x, self.y, self.z)
        if not proj: return
        sx, sy, scale = proj
        r = max(5, int(9 * (scale / 40.0)))
        fog_base = get_fog_color(COLOR_MAGENTA, self.z)
        fog_glow = get_fog_color(COLOR_CYAN, self.z)
        pygame.draw.circle(surface, fog_base, (int(sx), int(sy)), r)
        pygame.draw.circle(surface, fog_glow, (int(sx), int(sy)), max(2, r - 4))


class BossDreadnought3D:
    def __init__(self, x, y, z, current_level):
        self.x = x
        self.y = y
        self.z = z
        self.hp = 85 + (current_level - 1) * 45
        self.max_hp = self.hp
        self.left_turret_hp = 20
        self.right_turret_hp = 20
        self.points = 650
        self.target_type = "boss"
        self.shoot_timer = 2.0
        self.shield_angle = 0.0
        self.disabled_timer = 0.0

    def update(self, dt, enemy_bullets, difficulty_mode):
        is_enraged = self.hp <= (self.max_hp // 2)
        self.shield_angle += (7.0 if is_enraged else 2.5) * dt
        
        target_z = 35.0
        if self.z > target_z:
            self.z -= 10.0 * dt
        else:
            self.x = math.sin(pygame.time.get_ticks() * 0.002 * (1.5 if is_enraged else 1.0)) * 12.0
            self.y = 10.0 + math.sin(pygame.time.get_ticks() * 0.003) * 4.0

        if self.disabled_timer > 0:
            self.disabled_timer -= dt
            return

        self.shoot_timer -= dt
        if self.shoot_timer <= 0:
            self.shoot_timer = 1.2 if is_enraged else 1.8
            b_spd = 35.0 * (1.35 if difficulty_mode == 1 else (1.50 if difficulty_mode == 2 else 1.0))
            salvo_angles = [-20, -10, 0, 10, 20] if is_enraged else [-12, 0, 12]
            for angle in salvo_angles:
                rad = math.radians(angle)
                enemy_bullets.append(Bullet3D(self.x, self.y, self.z, math.sin(rad)*b_spd, -2.0, -math.cos(rad)*b_spd, is_player=False))

    def draw(self, surface):
        proj = project_3d(self.x, self.y, self.z)
        if not proj: return
        sx, sy, scale = proj
        w = max(30, int(50 * (scale / 40.0)))
        h = max(14, int(24 * (scale / 40.0)))
        rect = pygame.Rect(sx - w/2, sy - h/2, w, h)
        fog_body = get_fog_color((30, 0, 0), self.z)
        fog_glow = get_fog_color(COLOR_CRIMSON, self.z)
        pygame.draw.rect(surface, fog_body, rect)
        pygame.draw.rect(surface, fog_glow, rect, 2)
        
        if self.left_turret_hp > 0:
            pygame.draw.circle(surface, COLOR_GOLD, (int(sx - w*0.4), int(sy)), max(3, int(6*scale/40.0)))
        if self.right_turret_hp > 0:
            pygame.draw.circle(surface, COLOR_GOLD, (int(sx + w*0.4), int(sy)), max(3, int(6*scale/40.0)))

        if self.hp <= self.max_hp * 0.3:
            pygame.draw.circle(surface, COLOR_CRIMSON, (int(sx), int(sy)), max(4, int(8*scale/40.0)))
            pygame.draw.circle(surface, (255, 255, 255), (int(sx), int(sy)), max(2, int(4*scale/40.0)))
        else:
            r_size = int(w * 0.8)
            rx = sx + math.cos(self.shield_angle) * r_size * 0.6
            ry = sy + math.sin(self.shield_angle) * r_size * 0.3
            fog_shield = get_fog_color(COLOR_COIN, self.z)
            pygame.draw.circle(surface, fog_shield, (int(rx), int(ry)), max(3, int(6 * scale/40.0)))


class ExplosiveBarrel3D:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def update(self, dt):
        self.z -= 12.0 * dt

    def draw(self, surface):
        proj = project_3d(self.x, self.y, self.z)
        if not proj: return
        sx, sy, scale = proj
        r = max(5, int(9 * (scale / 40.0)))
        pygame.draw.circle(surface, (249, 115, 22), (int(sx), int(sy)), r)
        pygame.draw.circle(surface, (255, 255, 255), (int(sx), int(sy)), max(2, r - 4))

    def detonate(self, emp_spheres, targets):
        trigger_screen_shake(0.35, 14.0)
        play_synth_explosion()
        emp_spheres.append(SingularityDome3D(self.x, self.y, self.z))
        for t in list(targets):
            if math.hypot(t.x - self.x, t.y - self.y, t.z - self.z) < 25.0:
                t.hp -= 20
                if t.hp <= 0: targets.remove(t)


class PowerupItem3D:
    def __init__(self, ptype="battery", x=0.0, y=4.0, z=100.0):
        self.ptype = ptype
        self.x = x
        self.y = y
        self.z = z
        self.time_accum = random.uniform(0, 6.28)
        
        if ptype == "shield": self.color = COLOR_SHIELD
        elif ptype == "overclock": self.color = COLOR_OVERCLOCK
        elif ptype == "slowmo": self.color = COLOR_SLOWMO
        elif ptype == "coin": self.color = COLOR_COIN
        else: self.color = COLOR_EMERALD

    def update(self, dt):
        self.time_accum += dt
        self.z -= 14.0 * dt
        self.y += math.sin(self.time_accum * 4.0) * 0.6 * dt

    def draw(self, surface):
        proj = project_3d(self.x, self.y, self.z)
        if not proj: return
        sx, sy, scale = proj
        r = max(5, int(11 * (scale / 40.0)))
        fog_c = get_fog_color(self.color, self.z)
        pygame.draw.circle(surface, fog_c, (int(sx), int(sy)), r)
        pygame.draw.circle(surface, (255, 255, 255), (int(sx), int(sy)), max(2, r - 3))
