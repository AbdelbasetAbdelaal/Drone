"""
================================================================================
                    DRONE HUNTER 3D - ULTIMATE AAA EDITION
================================================================================
A full 3D Third-Person Cyberpunk Tactical Combat Game powered by high-fidelity
photorealistic artwork, dynamic 3D depth scaling, parallax camera scrolling,
and a modular, decoupled component architecture.
"""

import sys
import math
import random
import os
import pygame

# Import Decoupled Modules
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_FPS, COLOR_BG, COLOR_SKY_TOP,
    COLOR_SKY_BOTTOM, COLOR_ROAD, COLOR_CYAN, COLOR_GOLD, COLOR_EMERALD,
    COLOR_CRIMSON, COLOR_HUD, load_game_data, save_game_data
)
from src.engine3d import project_3d, get_fog_color, update_camera_spring, trigger_screen_shake
from src.audio import (
    play_synth_laser, play_synth_explosion, play_synth_powerup,
    play_synthwave_bgm_tick
)
from src.entities import (
    PlayerDrone3D, TargetRover3D, TargetTurret3D, ChaserDrone3D,
    BossDreadnought3D, ExplosiveBarrel3D, PowerupItem3D, Bullet3D,
    SingularityDome3D, GravityTetherBeam, HomingMissile3D
)
from src.environment import Building3D, Skybridge3D, MonorailTrain3D
from src.ui import draw_hud, draw_crosshair, draw_hangar_ui, font_title, font_banner, font_hud
from src.gl_engine import ModernGLEngine

# Initialize Pygame & Mixer & Joysticks
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.joystick.init()

joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
for joy in joysticks: joy.init()

win_w, win_h = SCREEN_WIDTH, SCREEN_HEIGHT
is_fullscreen = False

screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
pygame.display.set_caption("Drone Hunter 3D - Cyberpunk Tactical Combat (High-Fidelity Edition)")
clock = pygame.time.Clock()

# Initialize Hardware Shader Engine
gl_engine = ModernGLEngine()

# High-Fidelity Photorealistic Assets
use_sprites = True
has_sprites = True

try:
    sprite_bg_raw = pygame.image.load(os.path.join("assets", "bg.jpg")).convert()
    sprite_bg = pygame.transform.scale(sprite_bg_raw, (win_w + 180, win_h + 120))
    sprite_drone = pygame.image.load(os.path.join("assets", "drone.png")).convert_alpha()
    sprite_rover = pygame.image.load(os.path.join("assets", "rover.png")).convert_alpha()
except Exception:
    has_sprites = False

# Persistence
save_data = load_game_data()
coins = save_data.get("coins", 183500)
highscore = save_data.get("highscore", 0)
upgrade_levels = save_data.get("upgrade_levels", {"battery": 2, "speed": 1, "fire_rate": 3, "emp_recharge": 2, "damage": 2})

# Game States
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_LEVEL_CLEAR = "level_clear"
STATE_GAME_OVER = "game_over"
STATE_HANGAR = "hangar"

game_state = STATE_MENU
current_level = 3
level_score = 0
total_score = 0
difficulty_mode = 0
DIFFICULTY_NAMES = ["NORMAL", "HARDCORE ⚠️", "NIGHTMARE ☠️"]

# Instantiations
player_drone = PlayerDrone3D(upgrade_levels)
skybridges = [Skybridge3D(70.0), Skybridge3D(140.0)]
monorail_train = MonorailTrain3D()

city_buildings = []
def generate_city():
    city_buildings.clear()
    for z in range(-30, 380, 24):
        for side in [-1, 1]:
            x_pos = side * random.uniform(32, 65)
            h = random.uniform(22, 65)
            w = random.uniform(14, 22)
            d = random.uniform(14, 22)
            c = random.choice([(30, 41, 59), (15, 23, 42), (51, 65, 85)])
            city_buildings.append(Building3D(x_pos, z, w, h, d, c))

generate_city()

rain_particles = [[random.uniform(-40, 40), random.uniform(0, 35), random.uniform(5, 120), random.uniform(40, 60)] for _ in range(95)]
floating_popups = []
thruster_particles = []
homing_missiles = []
gravity_beams = []
player_bullets = []
enemy_bullets = []
emp_spheres = []
powerups = []
targets = []

lightning_timer = 0.0
lightning_interval = random.uniform(8.0, 16.0)
spawn_timer = 0.0
barrel_timer = 0.0

def update_spawner(dt):
    global spawn_timer, barrel_timer
    if game_state != STATE_PLAYING: return
    points_per_level = 1500 + (current_level - 1) * 1700
    spawn_timer += dt
    if spawn_timer >= max(0.6, 2.2 - (current_level - 1) * 0.3):
        spawn_timer = 0.0
        t_type = random.choice(["rover", "turret", "chaser", "rover"])
        spawn_x = random.uniform(-18, 18)
        if t_type == "rover": targets.append(TargetRover3D(spawn_x, 110.0, current_level))
        elif t_type == "turret": targets.append(TargetTurret3D(spawn_x, random.choice([4.0, 10.0, 16.0]), 110.0, current_level))
        elif t_type == "chaser": targets.append(ChaserDrone3D(spawn_x, random.uniform(4.0, 18.0), 110.0))

    if level_score >= points_per_level * 0.5 and not any(t.target_type == "boss" for t in targets):
        targets.append(BossDreadnought3D(0.0, 12.0, 110.0, current_level))

    barrel_timer += dt
    if barrel_timer >= 8.0:
        barrel_timer = 0.0
        powerups.append(ExplosiveBarrel3D(random.uniform(-16, 16), -8.8, 110.0))

def trigger_gravity_tether():
    if player_drone.tether_cooldown <= 0:
        player_drone.tether_cooldown = 1.8
        closest_t = None
        min_dist = 999.0
        for t in list(targets) + list(powerups):
            d = math.hypot(t.x - player_drone.x, t.y - player_drone.y, t.z - player_drone.z)
            if d < min_dist:
                min_dist = d
                closest_t = t
        
        if closest_t:
            play_synth_laser()
            gravity_beams.append(GravityTetherBeam((player_drone.x, player_drone.y, player_drone.z), (closest_t.x, closest_t.y, closest_t.z)))
            if hasattr(closest_t, 'hp'):
                closest_t.hp -= int(20 * player_drone.damage_mult)
                if closest_t.hp <= 0 and closest_t in targets: targets.remove(closest_t)
            elif isinstance(closest_t, ExplosiveBarrel3D):
                closest_t.detonate(emp_spheres, targets)

def trigger_homing_missiles():
    if player_drone.missile_cooldown <= 0:
        player_drone.missile_cooldown = 3.5
        play_synth_laser()
        for t in targets[:4]:
            homing_missiles.append(HomingMissile3D((player_drone.x, player_drone.y, player_drone.z), t))
        floating_popups.append(["🚀 HOMING MISSILES LAUNCHED", player_drone.x, player_drone.y + 2.0, player_drone.z, COLOR_GOLD, 1.0])

def buy_upgrade(name):
    global coins
    info = {
        "battery": {"base_cost": 50, "cost_mult": 1.5, "max_lvl": 5},
        "speed": {"base_cost": 60, "cost_mult": 1.5, "max_lvl": 5},
        "fire_rate": {"base_cost": 75, "cost_mult": 1.6, "max_lvl": 5},
        "emp_recharge": {"base_cost": 80, "cost_mult": 1.6, "max_lvl": 4},
        "damage": {"base_cost": 90, "cost_mult": 1.7, "max_lvl": 5},
    }[name]
    cur_lvl = upgrade_levels.get(name, 0)
    cost = int(info["base_cost"] * (info["cost_mult"] ** cur_lvl))
    if cur_lvl < info["max_lvl"] and coins >= cost:
        coins -= cost
        upgrade_levels[name] = cur_lvl + 1
        save_game_data(coins, highscore, upgrade_levels)
        player_drone.apply_upgrades(upgrade_levels)
        play_synth_powerup()
        return True
    return False

def reset_game():
    global current_level, level_score, total_score
    current_level = 1
    level_score = 0
    total_score = 0
    player_bullets.clear()
    enemy_bullets.clear()
    targets.clear()
    powerups.clear()
    emp_spheres.clear()
    gravity_beams.clear()
    homing_missiles.clear()
    floating_popups.clear()
    thruster_particles.clear()
    player_drone.x, player_drone.y, player_drone.z = 0.0, 4.0, 0.0
    player_drone.apply_upgrades(upgrade_levels)


# --- MAIN GAME LOOP ---
running = True
while running:
    dt = clock.tick(TARGET_FPS) / 1000.0

    update_camera_spring(player_drone.x, player_drone.y, player_drone.z, player_drone.hover_bob, dt)

    lightning_interval -= dt
    if lightning_interval <= 0:
        lightning_interval = random.uniform(8.0, 16.0)
        lightning_timer = 0.15
    if lightning_timer > 0: lightning_timer -= dt

    if game_state == STATE_PLAYING:
        play_synthwave_bgm_tick(dt)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state == STATE_PAUSED: game_state = STATE_PLAYING
                elif game_state == STATE_PLAYING: game_state = STATE_PAUSED
                else: running = False
            elif event.key in (pygame.K_F11, pygame.K_f) and not (game_state == STATE_PLAYING and event.key == pygame.K_f):
                is_fullscreen = not is_fullscreen
                screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN) if is_fullscreen else pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
            elif event.key == pygame.K_p:
                if game_state == STATE_PLAYING: game_state = STATE_PAUSED
                elif game_state == STATE_PAUSED: game_state = STATE_PLAYING
            elif event.key == pygame.K_d and game_state in (STATE_MENU, STATE_PAUSED, STATE_HANGAR):
                difficulty_mode = (difficulty_mode + 1) % 3
            elif event.key == pygame.K_h:
                game_state = STATE_HANGAR if game_state != STATE_HANGAR else STATE_PLAYING
            elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT) and game_state == STATE_PLAYING:
                player_drone.trigger_roll()
            elif event.key == pygame.K_q and game_state == STATE_PLAYING:
                trigger_homing_missiles()
            elif event.key == pygame.K_c and game_state == STATE_PLAYING:
                player_drone.trigger_cloak(floating_popups)
            elif event.key == pygame.K_g and game_state == STATE_PLAYING:
                trigger_gravity_tether()
            elif game_state in (STATE_HANGAR, STATE_PAUSED, STATE_MENU):
                if event.key in (pygame.K_1, pygame.K_KP1): buy_upgrade("battery")
                elif event.key in (pygame.K_2, pygame.K_KP2): buy_upgrade("speed")
                elif event.key in (pygame.K_3, pygame.K_KP3): buy_upgrade("fire_rate")
                elif event.key in (pygame.K_4, pygame.K_KP4): buy_upgrade("emp_recharge")
                elif event.key in (pygame.K_5, pygame.K_KP5): buy_upgrade("damage")
            elif event.key == pygame.K_e and game_state == STATE_PLAYING:
                if player_drone.emp_cooldown <= 0:
                    player_drone.emp_cooldown = player_drone.emp_cooldown_max
                    trigger_screen_shake(0.45, 18.0)
                    play_synth_explosion()
                    emp_spheres.append(SingularityDome3D(player_drone.x, player_drone.y, player_drone.z))
                    enemy_bullets.clear()
                    for t in list(targets):
                        t.disabled_timer = 5.0
                        t.hp -= int(25 * player_drone.damage_mult)
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if game_state in (STATE_MENU, STATE_GAME_OVER):
                    reset_game()
                    game_state = STATE_PLAYING
                elif game_state == STATE_HANGAR: game_state = STATE_PLAYING
                elif game_state == STATE_LEVEL_CLEAR:
                    current_level += 1
                    game_state = STATE_PLAYING

        elif event.type == pygame.MOUSEBUTTONDOWN and game_state == STATE_PLAYING:
            if event.button == 1 and player_drone.shoot_cooldown <= 0:
                play_synth_laser()
                player_drone.shoot_cooldown = player_drone.fire_rate
                player_drone.recoil_z = -0.5
                if current_level == 1:
                    player_bullets.append(Bullet3D(player_drone.x, player_drone.y, player_drone.z + 1.5, 0, 0, 80))
                elif current_level == 2:
                    player_bullets.append(Bullet3D(player_drone.x - 0.8, player_drone.y, player_drone.z + 1.5, 0, 0, 80))
                    player_bullets.append(Bullet3D(player_drone.x + 0.8, player_drone.y, player_drone.z + 1.5, 0, 0, 80))
                else:
                    player_bullets.append(Bullet3D(player_drone.x - 0.8, player_drone.y, player_drone.z + 1.5, -6, 0, 78))
                    player_bullets.append(Bullet3D(player_drone.x, player_drone.y, player_drone.z + 1.5, 0, 0, 80))
                    player_bullets.append(Bullet3D(player_drone.x + 0.8, player_drone.y, player_drone.z + 1.5, 6, 0, 78))
            elif event.button == 3: trigger_gravity_tether()

    keys = pygame.key.get_pressed()
    player_drone.is_firing_beam = keys[pygame.K_f] and game_state == STATE_PLAYING
    if player_drone.is_firing_beam:
        for t in list(targets):
            if abs(t.x - player_drone.x) < 3.0 and t.z > player_drone.z:
                t.hp -= int(40 * dt * player_drone.damage_mult)
                if t.hp <= 0: targets.remove(t)

    if game_state == STATE_PLAYING:
        player_drone.update(dt, game_state, joysticks, difficulty_mode, thruster_particles)
        monorail_train.update(dt)
        update_spawner(dt)

        thruster_particles = [p for p in thruster_particles if p.life > 0 and p.alpha > 0]
        for p in thruster_particles: p.update(dt)

        for gb in list(gravity_beams):
            gb.update(dt)
            if gb.timer <= 0: gravity_beams.remove(gb)

        for hm in list(homing_missiles):
            hm.update(dt, targets)
            for t in list(targets):
                if math.hypot(t.x - hm.x, t.y - hm.y, t.z - hm.z) < 3.5:
                    play_synth_explosion()
                    t.hp -= int(25 * player_drone.damage_mult)
                    if t.hp <= 0: targets.remove(t)
                    if hm in homing_missiles: homing_missiles.remove(hm)
                    break
            if hm.z > 140 or hm.z < -20:
                if hm in homing_missiles: homing_missiles.remove(hm)

        for b in list(player_bullets):
            b.update(dt, player_drone)
            if b.z > 140 or b.z < -20: player_bullets.remove(b)

        for eb in list(enemy_bullets):
            eb.update(dt, player_drone)
            if player_drone.is_rolling and not eb.dodged:
                dist = math.hypot(eb.x - player_drone.x, eb.y - player_drone.y, eb.z - player_drone.z)
                if 2.5 <= dist <= 6.5:
                    eb.dodged = True
                    player_drone.slowmo_timer = 0.35
                    total_score += 100
                    level_score += 100
                    play_synth_powerup()
                    floating_popups.append(["⚡ NEAR-MISS DODGE! +100 PTS", player_drone.x, player_drone.y + 2.5, player_drone.z, COLOR_GOLD, 1.0])

            if eb.z < -20 or eb.z > 150: enemy_bullets.remove(eb)

        for t in list(targets):
            if isinstance(t, TargetRover3D):
                t.update(dt, player_drone, enemy_bullets, current_level, difficulty_mode)
            elif isinstance(t, TargetTurret3D):
                t.update(dt, player_drone, enemy_bullets, difficulty_mode)
            elif isinstance(t, ChaserDrone3D):
                t.update(dt, player_drone, difficulty_mode)
            elif isinstance(t, BossDreadnought3D):
                t.update(dt, enemy_bullets, difficulty_mode)
            if t.z < -15: targets.remove(t)

        for p in list(powerups):
            p.update(dt)
            if p.z < -15: powerups.remove(p)

        for emp in list(emp_spheres):
            emp.update(dt, targets)
            if emp.radius > 45.0: emp_spheres.remove(emp)

        for b in list(player_bullets):
            b_hit = False
            for t in list(targets):
                if math.hypot(t.x - b.x, t.y - b.y, t.z - b.z) < 3.2:
                    b_hit = True
                    t.hp -= int(1 * player_drone.damage_mult)
                    if t.hp <= 0:
                        play_synth_explosion()
                        targets.remove(t)
                        earned_pts = t.points
                        earned_coins = random.randint(4, 9)
                        coins += earned_coins
                        level_score += earned_pts
                        total_score += earned_pts
                        if total_score > highscore: highscore = total_score
                        save_game_data(coins, highscore, upgrade_levels)

                        floating_popups.append([f"+{earned_pts} PTS", t.x, t.y + 2.0, t.z, COLOR_CYAN, 1.0])
                        floating_popups.append([f"+${earned_coins} GOLD", t.x, t.y + 3.2, t.z, COLOR_GOLD, 1.0])

                        if random.random() < 0.25:
                            ptype = random.choice(["battery", "shield", "overclock", "slowmo", "coin"])
                            powerups.append(PowerupItem3D(ptype, t.x, t.y, t.z))

                        points_per_level = 1500 + (current_level - 1) * 1700
                        if level_score >= points_per_level: game_state = STATE_LEVEL_CLEAR
                    break
            if b_hit:
                if b in player_bullets: player_bullets.remove(b)

        for b in list(player_bullets):
            for p in list(powerups):
                if isinstance(p, ExplosiveBarrel3D) and math.hypot(p.x - b.x, p.y - b.y, p.z - b.z) < 3.0:
                    p.detonate(emp_spheres, targets)
                    if b in player_bullets: player_bullets.remove(b)
                    break

        for p in list(powerups):
            if isinstance(p, PowerupItem3D) and math.hypot(p.x - player_drone.x, p.y - player_drone.y, p.z - player_drone.z) < 3.5:
                play_synth_powerup()
                if p.ptype == "battery": player_drone.health = min(player_drone.max_health, player_drone.health + player_drone.max_health * 0.3)
                elif p.ptype == "shield": player_drone.shield_hits = 2
                elif p.ptype == "overclock": player_drone.overclock_timer = 5.0
                elif p.ptype == "slowmo": player_drone.slowmo_timer = 4.0
                elif p.ptype == "coin":
                    coins += 10
                    save_game_data(coins, highscore, upgrade_levels)
                powerups.remove(p)

        if not player_drone.is_rolling:
            for eb in list(enemy_bullets):
                if math.hypot(eb.x - player_drone.x, eb.y - player_drone.y, eb.z - player_drone.z) < 2.4:
                    enemy_bullets.remove(eb)
                    if player_drone.shield_hits > 0:
                        player_drone.shield_hits -= 1
                        play_synth_powerup()
                    else:
                        play_synth_explosion()
                        trigger_screen_shake(0.25, 10.0)
                        player_drone.health -= 15
                        if player_drone.health <= 0: game_state = STATE_GAME_OVER
                    break

    # --- RENDER PIPELINE ---
    canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    # DYNAMIC PARALLAX BACKGROUND ARTWORK
    if has_sprites and sprite_bg:
        para_x = int(-60 - player_drone.x * 2.2)
        para_y = int(-40 - player_drone.y * 1.2)
        canvas.blit(sprite_bg, (para_x, para_y))

    if lightning_timer > 0:
        l_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        l_surf.fill((255, 255, 255, 130))
        canvas.blit(l_surf, (0, 0))

    for sb in skybridges: sb.draw(canvas, SCREEN_WIDTH, SCREEN_HEIGHT)
    monorail_train.draw(canvas)

    for rp in rain_particles:
        rp[2] -= rp[3] * dt
        if rp[2] <= 2.0:
            rp[2] = random.uniform(70, 120)
            rp[0] = random.uniform(-40, 40)
            rp[1] = random.uniform(0, 35)
        p1 = project_3d(rp[0], rp[1], rp[2])
        p2 = project_3d(rp[0] - 0.8, rp[1] - 2.5, rp[2] + 1.2)
        if p1 and p2:
            fog_c = get_fog_color((120, 170, 200), rp[2])
            pygame.draw.line(canvas, fog_c, (p1[0], p1[1]), (p2[0], p2[1]), 1)

    for tp in thruster_particles: tp.draw(canvas)
    for gb in gravity_beams: gb.draw(canvas)
    for hm in homing_missiles: hm.draw(canvas)

    all_entities = []
    for p in powerups: all_entities.append((p.z, p))
    for t in targets: all_entities.append((t.z, t))
    for b in player_bullets: all_entities.append((b.z, b))
    for eb in enemy_bullets: all_entities.append((eb.z, eb))
    for emp in emp_spheres: all_entities.append((emp.z, emp))
    all_entities.append((player_drone.z, player_drone))

    all_entities.sort(key=lambda item: item[0], reverse=True)
    for z_depth, entity in all_entities:
        if entity == player_drone:
            player_drone.draw(canvas, use_sprites, has_sprites, sprite_drone)
        elif isinstance(entity, TargetRover3D):
            entity.draw(canvas, use_sprites, has_sprites, sprite_rover, player_drone)
        else:
            entity.draw(canvas)

    if game_state == STATE_PLAYING:
        draw_crosshair(canvas)
        draw_hud(canvas, player_drone, current_level, level_score, total_score, coins, difficulty_mode, DIFFICULTY_NAMES, use_sprites)

    if game_state == STATE_HANGAR:
        draw_hangar_ui(canvas, coins, current_level, upgrade_levels, PlayerDrone3D)
    elif game_state in (STATE_MENU, STATE_PAUSED, STATE_LEVEL_CLEAR, STATE_GAME_OVER):
        box_w, box_h = 820, 380
        box_x = (SCREEN_WIDTH - box_w) // 2
        box_y = (SCREEN_HEIGHT - box_h) // 2
        
        dialog_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        dialog_surf.fill((15, 23, 42, 238))
        pygame.draw.rect(dialog_surf, COLOR_CYAN, (0, 0, box_w, box_h), 3)
        pygame.draw.rect(dialog_surf, COLOR_GOLD, (4, 4, box_w - 8, box_h - 8), 1)
        canvas.blit(dialog_surf, (box_x, box_y))

        if game_state == STATE_MENU:
            t_surf = font_title.render("DRONE HUNTER 3D", True, COLOR_CYAN)
            s1_surf = font_banner.render("Press [SPACE] or Click to Launch 3D Mission", True, COLOR_EMERALD)
            s2_surf = font_hud.render("[H] Hangar Loadout | [D] Difficulty Mode", True, COLOR_GOLD)
            s3_surf = font_hud.render("Flight: W/A/S/D | Roll: SHIFT | Tether: Right-Click | Missiles: Q | Cloak: C", True, COLOR_HUD)
        elif game_state == STATE_PAUSED:
            t_surf = font_title.render("GAME PAUSED", True, COLOR_CYAN)
            s1_surf = font_banner.render("Press 'P' or ESC to Resume Mission", True, COLOR_EMERALD)
            s2_surf = font_hud.render("[H] Hangar Loadout | [D] Difficulty | [1-5] Quick Upgrades", True, COLOR_GOLD)
            s3_surf = font_hud.render("Flight: W/A/S/D | Roll: SHIFT | Tether: Right-Click | Missiles: Q | Cloak: C", True, COLOR_HUD)
        elif game_state == STATE_LEVEL_CLEAR:
            t_surf = font_title.render(f"MISSION COMPLETE! LEVEL {current_level}", True, COLOR_CYAN)
            s1_surf = font_banner.render("Press [SPACE] to Start Next Level", True, COLOR_EMERALD)
            s2_surf = font_hud.render(f"Total Score: {total_score}  |  Gold Scrap: ${coins}", True, COLOR_GOLD)
            s3_surf = font_hud.render("Press [H] to Visit Hangar Loadout", True, COLOR_HUD)
        else:
            t_surf = font_title.render("MISSION FAILED - DRONE DESTROYED", True, COLOR_CRIMSON)
            s1_surf = font_banner.render(f"Final Level: {current_level}  |  Total Score: {total_score}", True, COLOR_GOLD)
            s2_surf = font_hud.render("Run Score Reset to Zero for Next Game", True, COLOR_CRIMSON)
            s3_surf = font_hud.render("Press [SPACE] or [R] to Restart Fresh", True, COLOR_EMERALD)

        canvas.blit(t_surf, t_surf.get_rect(center=(SCREEN_WIDTH // 2, box_y + 40)))
        canvas.blit(s1_surf, s1_surf.get_rect(center=(SCREEN_WIDTH // 2, box_y + 100)))
        canvas.blit(s2_surf, s2_surf.get_rect(center=(SCREEN_WIDTH // 2, box_y + 170)))
        canvas.blit(s3_surf, s3_surf.get_rect(center=(SCREEN_WIDTH // 2, box_y + 240)))

    cur_w, cur_h = screen.get_size()
    if cur_w > 0 and cur_h > 0:
        scaled_canvas = pygame.transform.smoothscale(canvas, (cur_w, cur_h))
        screen.blit(scaled_canvas, (0, 0))

    pygame.display.flip()

pygame.quit()
sys.exit()
