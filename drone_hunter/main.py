import os
import sys
import json
import math
import random
import pygame

from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, COLOR_BG, COLOR_HUD,
    STATE_MENU, STATE_PLAYING, STATE_GAME_OVER, STATE_LEVEL_CLEAR, STATE_HANGAR, STATE_PAUSED,
    COLOR_CYAN, COLOR_EMERALD, COLOR_GOLD, COLOR_MAGENTA, COLOR_CRIMSON,
    COLOR_SHIELD, COLOR_OVERCLOCK, COLOR_SLOWMO, COLOR_COIN, COLOR_NEON_RED,
    TARGET_TYPE_BOSS, TARGET_TYPE_VEHICLE, TARGET_TYPE_TURRET, TARGET_TYPE_CHASER,
    UPGRADES, ROLL_COOLDOWN, DIFFICULTY_NAMES
)
from src.player import Player
from src.target import Spawner, Target
from src.powerup import PowerupItem
from src.particles import ParticleManager
from src.background import ParallaxBackground
from src.audio import AudioManager

SAVE_FILE = "save_data.json"

def load_save_data() -> tuple[int, int, dict[str, int]]:
    """Loads coins, highscore, and upgrade levels from JSON save file."""
    default_upgrades = {"battery": 0, "speed": 0, "fire_rate": 0, "emp_recharge": 0}
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                coins = data.get("coins", 0)
                highscore = data.get("highscore", 0)
                upgrades = data.get("upgrades", default_upgrades)
                return coins, highscore, upgrades
        except Exception:
            return 0, 0, default_upgrades
    return 0, 0, default_upgrades

def save_game_data(coins: int, highscore: int, upgrades: dict[str, int]):
    """Saves coins, highscore, and upgrade levels to JSON save file."""
    try:
        data = {
            "coins": coins,
            "highscore": highscore,
            "upgrades": upgrades
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def main():
    pygame.init()
    pygame.font.init()

    # Window & Screen Size Control State
    win_w, win_h = 1280, 720
    is_fullscreen = False
    screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # Virtual 1280x720 Canvas for Resolution-Independent Rendering
    canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    # Core Systems
    background = ParallaxBackground()
    particle_manager = ParticleManager()
    audio_manager = AudioManager()

    # Fonts
    font_title = pygame.font.SysFont("Arial", 64, bold=True)
    font_hud = pygame.font.SysFont("Arial", 22, bold=True)
    font_banner = pygame.font.SysFont("Arial", 40, bold=True)
    font_gameover = pygame.font.SysFont("Arial", 52, bold=True)

    # Sprite Groups
    player_group = pygame.sprite.GroupSingle()
    bullet_group = pygame.sprite.Group()
    enemy_bullet_group = pygame.sprite.Group()
    target_group = pygame.sprite.Group()
    powerup_group = pygame.sprite.Group()

    # Save Data & Difficulty State
    coins, highscore, upgrade_levels = load_save_data()
    game_state = STATE_MENU
    difficulty_mode = 0 # 0=NORMAL, 1=HARDCORE, 2=NIGHTMARE
    
    current_level = 1
    level_score = 0
    total_score = 0
    battery_timer = 0.0

    # Combo & Screen Shake & Weather Systems
    combo_count = 1
    combo_timer = 0.0
    screen_shake_time = 0.0
    screen_shake_intensity = 0.0
    
    # Weather System: "clear", "rain", "wind"
    weather_type = "clear"
    weather_timer = 0.0
    wind_force = 0.0
    lightning_flash = 0.0

    # Pause Button Rect on HUD
    pause_btn_rect = pygame.Rect(SCREEN_WIDTH - 110, 48, 90, 30)

    drone = None
    spawner = None

    def get_virtual_mouse_pos() -> tuple[int, int]:
        """Translates current window mouse position to virtual (1280x720) canvas coordinates."""
        mx, my = pygame.mouse.get_pos()
        cw, ch = screen.get_size()
        if cw <= 0 or ch <= 0:
            return (mx, my)
        return (int(mx * (SCREEN_WIDTH / cw)), int(my * (SCREEN_HEIGHT / ch)))

    def toggle_fullscreen():
        nonlocal is_fullscreen, screen
        is_fullscreen = not is_fullscreen
        if is_fullscreen:
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)

    def set_resolution(w: int, h: int):
        nonlocal win_w, win_h, is_fullscreen, screen
        win_w, win_h = w, h
        is_fullscreen = False
        screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)

    def trigger_shake(intensity: float = 6.0, duration: float = 0.25):
        nonlocal screen_shake_intensity, screen_shake_time
        screen_shake_intensity = intensity
        screen_shake_time = duration

    def reset_game():
        nonlocal drone, spawner, current_level, level_score, total_score, battery_timer, combo_count, combo_timer
        current_level = 1
        level_score = 0
        total_score = 0
        battery_timer = 0.0
        combo_count = 1
        combo_timer = 0.0
        
        bullet_group.empty()
        enemy_bullet_group.empty()
        target_group.empty()
        powerup_group.empty()
        particle_manager.particles.empty()
        particle_manager.floating_texts.empty()
        
        drone = Player((200, SCREEN_HEIGHT // 2))
        drone.apply_shop_upgrades(upgrade_levels)
        player_group.add(drone)
        
        spawner = Spawner(base_min_interval=1.5, base_max_interval=3.0)
        spawner.set_level(current_level)
        background.set_level(current_level)

    def start_next_level():
        nonlocal current_level, level_score, game_state, battery_timer, combo_count, combo_timer
        current_level += 1
        level_score = 0
        battery_timer = 0.0
        combo_count = 1
        combo_timer = 0.0
        
        bullet_group.empty()
        enemy_bullet_group.empty()
        target_group.empty()
        powerup_group.empty()
        particle_manager.particles.empty()
        particle_manager.floating_texts.empty()
        
        spawner.set_level(current_level)
        background.set_level(current_level)
        game_state = STATE_PLAYING

    def execute_emp_blast():
        nonlocal level_score, total_score, highscore, coins
        if drone.trigger_emp():
            audio_manager.play_emp()
            particle_manager.spawn_emp_ring(drone.pos)
            particle_manager.spawn_floating_text(drone.pos, "⚡ EMP BLAST!", COLOR_CYAN, 28)
            trigger_shake(9.0, 0.25)

            # Destroy non-boss targets & heavily damage boss
            for target in list(target_group):
                particle_manager.spawn_explosion(target.rect.center, count=20, color=target.color_outer)
                if target.target_type == TARGET_TYPE_BOSS:
                    destroyed = target.take_damage(8)
                else:
                    destroyed = target.take_damage(99)

                if destroyed:
                    target.kill()
                    pts = target.points
                    earned_coins = random.randint(5, 15) if target.target_type != TARGET_TYPE_BOSS else 75
                    coins += earned_coins
                    level_score += pts
                    total_score += pts
                    particle_manager.spawn_floating_text(target.rect.center, f"+{pts}  +${earned_coins}", COLOR_GOLD, 24)

            # Destroy incoming enemy bullets
            enemy_bullet_group.empty()

            if total_score > highscore:
                highscore = total_score
            save_game_data(coins, highscore, upgrade_levels)

    def execute_barrel_roll():
        if drone and drone.trigger_roll(dir_x=1.0):
            audio_manager.play_thrust()
            trigger_shake(4.0, 0.18)
            particle_manager.spawn_floating_text(drone.pos, "🌀 EVASIVE ROLL!", COLOR_CYAN, 22)

    def buy_upgrade(name: str) -> bool:

        nonlocal coins
        info = UPGRADES[name]
        cur_lvl = upgrade_levels.get(name, 0)
        cost = int(info["base_cost"] * (info["cost_mult"] ** cur_lvl))
        if cur_lvl < info["max_lvl"] and coins >= cost:
            coins -= cost
            upgrade_levels[name] = cur_lvl + 1
            audio_manager.play_buy()
            save_game_data(coins, highscore, upgrade_levels)
            if drone:
                drone.apply_shop_upgrades(upgrade_levels)
            return True
        return False

    reset_game()

    # Shop Card Rects for Mouse Interaction
    card_rects = [
        (pygame.Rect(160, 240, 440, 160), "battery"),
        (pygame.Rect(680, 240, 440, 160), "speed"),
        (pygame.Rect(160, 440, 440, 160), "fire_rate"),
        (pygame.Rect(680, 440, 440, 160), "emp_recharge"),
    ]

    # Track origin state when entering Hangar Shop
    shop_return_state = STATE_MENU

    def exit_hangar_shop():
        nonlocal game_state
        if shop_return_state == STATE_LEVEL_CLEAR:
            start_next_level()
        elif shop_return_state in (STATE_PAUSED, STATE_PLAYING):
            game_state = STATE_PLAYING
        else:
            reset_game()
            game_state = STATE_PLAYING

    # Hangar Launch Button Rect
    launch_btn_rect = pygame.Rect((SCREEN_WIDTH - 460) // 2, 635, 460, 54)


    # Main Loop
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        background.update(dt)

        # Screen Shake offset calculation
        shake_offset_x, shake_offset_y = 0, 0
        if screen_shake_time > 0:
            screen_shake_time -= dt
            shake_offset_x = random.randint(-int(screen_shake_intensity), int(screen_shake_intensity))
            shake_offset_y = random.randint(-int(screen_shake_intensity), int(screen_shake_intensity))

        # Dynamic Weather Hazard System Updates
        if game_state == STATE_PLAYING:
            weather_timer += dt
            if weather_timer >= 22.0: # Change weather every 22s
                weather_timer = 0.0
                weather_type = random.choice(["clear", "rain", "wind"])
                if weather_type == "wind":
                    wind_force = random.choice([-160.0, 160.0])
                else:
                    wind_force = 0.0

            # Update Weather Effects
            if weather_type == "rain":
                particle_manager.spawn_weather("rain")
                if random.random() < 0.008:
                    lightning_flash = 0.12 # Thunder flash

            if lightning_flash > 0:
                lightning_flash -= dt

        # Always update particles
        if game_state in (STATE_PLAYING, STATE_LEVEL_CLEAR):
            particle_manager.update(dt)

        # Event Loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game_state == STATE_HANGAR:
                        exit_hangar_shop()
                    elif game_state == STATE_PAUSED:
                        game_state = STATE_PLAYING
                    else:
                        running = False

                # Fullscreen & Resolution Controls
                if event.key in (pygame.K_F11, pygame.K_f) and not (game_state == STATE_PLAYING and event.key == pygame.K_f):
                    toggle_fullscreen()
                elif event.key == pygame.K_F2:
                    set_resolution(1280, 720)
                elif event.key == pygame.K_F3:
                    set_resolution(1600, 900)
                elif event.key == pygame.K_F4:
                    set_resolution(1920, 1080)

                # Difficulty Toggle with 'D' Key
                if event.key == pygame.K_d and game_state in (STATE_MENU, STATE_PAUSED):
                    difficulty_mode = (difficulty_mode + 1) % 3
                    audio_manager.play_buy()

                # Pause Menu Access & Controls (Hangar Shop, Quick Upgrades)
                if game_state == STATE_PAUSED:
                    if event.key == pygame.K_h:
                        shop_return_state = STATE_PAUSED
                        game_state = STATE_HANGAR
                    elif event.key in (pygame.K_1, pygame.K_KP1):
                        buy_upgrade("battery")
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        buy_upgrade("speed")
                    elif event.key in (pygame.K_3, pygame.K_KP3):
                        buy_upgrade("fire_rate")
                    elif event.key in (pygame.K_4, pygame.K_KP4):
                        buy_upgrade("emp_recharge")

                # Pause Toggle with 'P' Key
                if event.key == pygame.K_p:
                    if game_state == STATE_PLAYING:
                        game_state = STATE_PAUSED
                    elif game_state == STATE_PAUSED:
                        game_state = STATE_PLAYING

                # Return to menu from Pause
                if game_state == STATE_PAUSED and event.key == pygame.K_m:
                    game_state = STATE_MENU

                # EMP Shockwave Blast on 'E' Key
                if game_state == STATE_PLAYING and event.key == pygame.K_e:
                    execute_emp_blast()

                # Evasive Barrel Roll on Shift key
                if game_state == STATE_PLAYING and event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    execute_barrel_roll()

                # State Transitions & Hangar Shop Interactions
                if game_state == STATE_MENU:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        reset_game()
                        game_state = STATE_PLAYING
                    elif event.key == pygame.K_h:
                        shop_return_state = STATE_MENU
                        game_state = STATE_HANGAR

                elif game_state == STATE_HANGAR:
                    # Keyboard & Numpad Shop Purchases
                    if event.key in (pygame.K_1, pygame.K_KP1):
                        buy_upgrade("battery")
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        buy_upgrade("speed")
                    elif event.key in (pygame.K_3, pygame.K_KP3):
                        buy_upgrade("fire_rate")
                    elif event.key in (pygame.K_4, pygame.K_KP4):
                        buy_upgrade("emp_recharge")
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        exit_hangar_shop()

                elif game_state == STATE_LEVEL_CLEAR:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_s):
                        start_next_level()
                    elif event.key in (pygame.K_h, pygame.K_b):
                        shop_return_state = STATE_LEVEL_CLEAR
                        game_state = STATE_HANGAR

                elif game_state == STATE_GAME_OVER:
                    if event.key in (pygame.K_r, pygame.K_SPACE, pygame.K_s):
                        reset_game()
                        game_state = STATE_PLAYING

            # Mouse Click Events (scaled to virtual 1280x720 canvas)
            if event.type == pygame.MOUSEBUTTONDOWN:
                m_pos = get_virtual_mouse_pos()
                
                if game_state == STATE_HANGAR:
                    if launch_btn_rect.collidepoint(m_pos):
                        exit_hangar_shop()
                    else:
                        for rect, name in card_rects:
                            if rect.collidepoint(m_pos):
                                buy_upgrade(name)

                elif game_state == STATE_PLAYING and pause_btn_rect.collidepoint(m_pos):
                    game_state = STATE_PAUSED
                elif game_state == STATE_PAUSED:
                    game_state = STATE_PLAYING
                elif game_state == STATE_PLAYING:
                    if event.button == 1:
                        new_bullets = drone.shoot(m_pos, level=current_level)
                        if new_bullets:
                            for b in new_bullets:
                                bullet_group.add(b)
                            audio_manager.play_laser()
                    elif event.button == 3: # Right Click EMP
                        execute_emp_blast()

        # Update Logic per State
        if game_state == STATE_PLAYING:
            points_per_level = 1500 + (current_level - 1) * 1700
            slowmo_active = drone.slowmo_timer > 0
            slowmo_factor = 0.4 if slowmo_active else 1.0

            # Difficulty speed & interval multipliers
            diff_speed_mult = 1.0 + (difficulty_mode * 0.25)
            spawner_dt_mult = 1.0 + (difficulty_mode * 0.35)

            # Continuous thrust battery drain in Nightmare difficulty mode
            if difficulty_mode == 2 and drone.is_thrusting:
                drone.health = max(0.0, drone.health - 1.8 * dt)

            # Combo Multiplier decay timer
            if combo_timer > 0:
                combo_timer -= dt
                if combo_timer <= 0:
                    combo_count = 1

            # Continuous automatic fire when holding left click (virtual mouse position)
            v_mpos = get_virtual_mouse_pos()
            if pygame.mouse.get_pressed()[0] and not pause_btn_rect.collidepoint(v_mpos):
                new_bullets = drone.shoot(v_mpos, level=current_level)
                if new_bullets:
                    for b in new_bullets:
                        bullet_group.add(b)
                    audio_manager.play_laser()

            # Periodic Powerup & Explosive Barrel Spawner (Every 6.5s)
            battery_timer += dt
            if battery_timer >= 6.5:
                battery_timer = 0.0
                ptype = random.choice(["battery", "shield", "overclock", "slowmo", "coin", "barrel"])
                powerup_group.add(PowerupItem(ptype=ptype))

            # Update Entities
            drone.update(dt, particle_manager, audio_manager, wind_force=wind_force)
            bullet_group.update(dt)
            enemy_bullet_group.update(dt, slowmo_factor=slowmo_factor * diff_speed_mult)

            # Update Targets & Enemy Bullet Firing with Predictive Aiming & Dodging
            for target in list(target_group):
                enemy_shots = target.update(
                    dt, player_pos=drone.pos, slowmo_factor=slowmo_factor * diff_speed_mult,
                    player_vel=drone.velocity, bullet_group=bullet_group
                )
                if enemy_shots:
                    for eb in enemy_shots:
                        enemy_bullet_group.add(eb)

            powerup_group.update(dt)
            spawner.update(dt * slowmo_factor * spawner_dt_mult, target_group, level_score, points_per_level)

            # Smart Near-Miss Bullet-Time Dodge Detection
            if drone and drone.is_rolling:
                for eb in enemy_bullet_group:
                    d_dist = math.hypot(eb.pos.x - drone.pos.x, eb.pos.y - drone.pos.y)
                    if 28.0 < d_dist < 52.0:
                        drone.activate_slowmo(0.35)
                        level_score += 100
                        total_score += 100
                        particle_manager.spawn_floating_text(drone.pos, "⚡ NEAR MISS DODGE! +100 PTS", COLOR_CYAN, 24)
                        trigger_shake(5.0, 0.15)
                        break

            # Player Bullet vs Powerup/Barrel Collisions (Explosive Barrels!)
            barrel_hits = pygame.sprite.groupcollide(bullet_group, powerup_group, True, False, pygame.sprite.collide_circle)
            for bullet, p_list in barrel_hits.items():
                for item in p_list:
                    if item.ptype == "barrel":
                        item.kill()
                        audio_manager.play_explosion()
                        trigger_shake(12.0, 0.35)
                        particle_manager.spawn_explosion(item.rect.center, count=55, color=(249, 115, 22))
                        particle_manager.spawn_floating_text(item.rect.center, "💥 BARREL CHAIN EXPLOSION!", (249, 115, 22), 30)
                        
                        # Chain explosion wipes nearby bullets and damages targets!
                        enemy_bullet_group.empty()
                        for target in list(target_group):
                            if math.hypot(target.pos.x - item.pos.x, target.pos.y - item.pos.y) < 260:
                                destroyed = target.take_damage(12)
                                particle_manager.spawn_explosion(target.rect.center, count=20, color=target.color_outer)
                                if destroyed:
                                    target.kill()
                                    level_score += target.points
                                    total_score += target.points

            # Player Bullet vs Target Collisions
            hits = pygame.sprite.groupcollide(bullet_group, target_group, True, False, pygame.sprite.collide_circle)
            for bullet, targets_hit in hits.items():
                for target in targets_hit:
                    destroyed = target.take_damage(1)
                    particle_manager.spawn_explosion(target.rect.center, count=15, color=target.color_outer)
                    audio_manager.play_explosion()

                    if destroyed:
                        target.kill()
                        
                        # Combo Calculation
                        combo_count = min(5, combo_count + 1)
                        combo_timer = 1.8 # 1.8s window to extend combo
                        
                        earned_pts = target.points * combo_count
                        earned_coins = random.randint(3, 8) if target.target_type != TARGET_TYPE_BOSS else 50
                        coins += earned_coins
                        level_score += earned_pts
                        total_score += earned_pts

                        # Floating Score & Coins Text
                        combo_str = f" x{combo_count}!" if combo_count > 1 else ""
                        particle_manager.spawn_floating_text(target.rect.center, f"+{earned_pts}{combo_str}  +${earned_coins}", COLOR_GOLD, 22 + combo_count * 2)

                        # Powerup Drop Chance
                        if random.random() < 0.35:
                            ptype = random.choice(["battery", "shield", "overclock", "slowmo", "coin", "barrel"])
                            powerup_group.add(PowerupItem(ptype=ptype, pos=target.rect.center))

                        # Save Data
                        if total_score > highscore:
                            highscore = total_score
                        save_game_data(coins, highscore, upgrade_levels)

                        # Level Completion Check
                        if level_score >= points_per_level:
                            game_state = STATE_LEVEL_CLEAR
                            bullet_group.empty()
                            enemy_bullet_group.empty()
                            target_group.empty()
                            powerup_group.empty()
                            particle_manager.spawn_celebration(SCREEN_WIDTH, SCREEN_HEIGHT)
                            particle_manager.spawn_floating_text((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), f"🏆 LEVEL {current_level} FINISHED!", COLOR_CYAN, 36)
                            audio_manager.play_celebration_fanfare()
                            break

            # Enemy Bullet vs Player Drone Collisions
            if game_state == STATE_PLAYING:
                eb_hits = pygame.sprite.spritecollide(drone, enemy_bullet_group, True, pygame.sprite.collide_circle)
                for eb in eb_hits:
                    particle_manager.spawn_explosion(drone.rect.center, count=15, color=COLOR_CRIMSON)
                    audio_manager.play_explosion()
                    dead = drone.take_damage(15)
                    if dead:
                        game_state = STATE_GAME_OVER
                        audio_manager.play_gameover()

            # Drone vs Powerup Collection
            if game_state == STATE_PLAYING:
                powerup_hits = pygame.sprite.spritecollide(drone, powerup_group, True, pygame.sprite.collide_circle)
                for item in powerup_hits:
                    if item.ptype == "shield":
                        drone.activate_shield(2)
                        audio_manager.play_shield()
                        particle_manager.spawn_floating_text(drone.pos, "🛡️ SHIELD ACTIVE!", COLOR_SHIELD, 26)
                        particle_manager.spawn_explosion(drone.rect.center, count=20, color=COLOR_SHIELD)
                    elif item.ptype == "overclock":
                        drone.activate_overclock(5.0)
                        audio_manager.play_recharge()
                        particle_manager.spawn_floating_text(drone.pos, "⚡ OVERCLOCK 2X!", COLOR_OVERCLOCK, 26)
                        particle_manager.spawn_explosion(drone.rect.center, count=20, color=COLOR_OVERCLOCK)
                    elif item.ptype == "slowmo":
                        drone.activate_slowmo(6.0)
                        audio_manager.play_recharge()
                        particle_manager.spawn_floating_text(drone.pos, "⌛ SLOW MOTION TIME-DILATION!", COLOR_SLOWMO, 26)
                        particle_manager.spawn_explosion(drone.rect.center, count=20, color=COLOR_SLOWMO)
                    elif item.ptype == "coin":
                        coins += 25
                        audio_manager.play_recharge()
                        particle_manager.spawn_floating_text(drone.pos, "🪙 +$25 GOLD SCRAP!", COLOR_COIN, 26)
                        save_game_data(coins, highscore, upgrade_levels)
                    elif item.ptype == "barrel":
                        # Accidentally touching a barrel detonates it!
                        particle_manager.spawn_explosion(drone.rect.center, count=25, color=(249, 115, 22))
                        audio_manager.play_explosion()
                        dead = drone.take_damage(20)
                        if dead:
                            game_state = STATE_GAME_OVER
                            audio_manager.play_gameover()
                    else: # battery
                        drone.recharge_battery(30)
                        audio_manager.play_recharge()
                        particle_manager.spawn_floating_text(drone.pos, "🔋 BATTERY +30%", COLOR_EMERALD, 24)
                        particle_manager.spawn_explosion(drone.rect.center, count=20, color=COLOR_EMERALD)

            # Drone vs Target Collisions
            if game_state == STATE_PLAYING:
                drone_hits = pygame.sprite.spritecollide(drone, target_group, True, pygame.sprite.collide_circle)
                for target in drone_hits:
                    particle_manager.spawn_explosion(target.rect.center, count=25, color=(239, 68, 68))
                    audio_manager.play_explosion()
                    dead = drone.take_damage(25)
                    if dead:
                        game_state = STATE_GAME_OVER
                        audio_manager.play_gameover()

        # Rendering (with Screen Shake offset)
        canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        canvas.fill(COLOR_BG)
        background.draw(canvas)

        if game_state in (STATE_PLAYING, STATE_PAUSED, STATE_LEVEL_CLEAR, STATE_GAME_OVER):
            player_group.draw(canvas)
            bullet_group.draw(canvas)
            enemy_bullet_group.draw(canvas)
            target_group.draw(canvas)
            powerup_group.draw(canvas)
            particle_manager.draw(canvas)

            # Draw Glowing Neon Red Target Lock-on Crosshairs over Target Vehicles
            for target in target_group:
                if target.target_type == TARGET_TYPE_VEHICLE:
                    cx, cy = target.rect.centerx, target.rect.top - 24
                    pulse_r = 16 + int(math.sin(pygame.time.get_ticks() * 0.012) * 3)
                    pygame.draw.circle(canvas, COLOR_NEON_RED, (cx, cy), pulse_r, 2)
                    pygame.draw.circle(canvas, (255, 255, 255), (cx, cy), 3)
                    pygame.draw.line(canvas, COLOR_NEON_RED, (cx - pulse_r - 4, cy), (cx + pulse_r + 4, cy), 2)
                    pygame.draw.line(canvas, COLOR_NEON_RED, (cx, cy - pulse_r - 4), (cx, cy + pulse_r + 4), 2)

            # Slow Motion Visual Overlay Tint
            if drone and drone.slowmo_timer > 0:
                slowmo_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                slowmo_overlay.fill((14, 165, 233, 30))
                canvas.blit(slowmo_overlay, (0, 0))

            # Lightning Flash Overlay
            if lightning_flash > 0:
                flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, 140))
                canvas.blit(flash_surf, (0, 0))

            # --- HUD Overlay ---
            current_fps = int(clock.get_fps())
            points_per_level = 1500 + (current_level - 1) * 1700
            
            lvl_surf = font_hud.render(f"LEVEL {current_level}", True, COLOR_GOLD)
            prog_surf = font_hud.render(f"Progress: {level_score}/{points_per_level} pts", True, COLOR_HUD)
            score_surf = font_hud.render(f"Score: {total_score}", True, COLOR_HUD)
            coin_surf = font_hud.render(f"COINS: ${coins}", True, COLOR_COIN)
            high_surf = font_hud.render(f"HI-SCORE: {highscore}", True, COLOR_CYAN)
            fps_surf = font_hud.render(f"FPS: {current_fps}", True, COLOR_EMERALD)

            canvas.blit(lvl_surf, (20, 15))
            canvas.blit(prog_surf, (140, 15))
            canvas.blit(score_surf, (400, 15))
            canvas.blit(coin_surf, (560, 15))
            canvas.blit(high_surf, (720, 15))
            canvas.blit(fps_surf, (SCREEN_WIDTH - 210, 15))

            # HUD Pause Button [⏸ PAUSE]
            pygame.draw.rect(canvas, (30, 41, 59), pause_btn_rect)
            pygame.draw.rect(canvas, COLOR_CYAN, pause_btn_rect, 2)
            pause_btn_txt = font_hud.render("⏸ PAUSE", True, COLOR_CYAN)
            canvas.blit(pause_btn_txt, pause_btn_txt.get_rect(center=pause_btn_rect.center))

            # Drone Health / Battery Bar
            bar_w, bar_h = 200, 16
            bar_x, bar_y = 20, 48
            pygame.draw.rect(canvas, (30, 41, 59), (bar_x, bar_y, bar_w, bar_h))
            health_pct = max(0.0, drone.health / drone.max_health)
            health_color = COLOR_EMERALD if health_pct > 0.4 else (239, 68, 68)
            pygame.draw.rect(canvas, health_color, (bar_x, bar_y, int(bar_w * health_pct), bar_h))
            pygame.draw.rect(canvas, COLOR_HUD, (bar_x, bar_y, bar_w, bar_h), 2)
            
            hp_txt = font_hud.render(f"BATTERY: {int(drone.health)}/{int(drone.max_health)}", True, COLOR_HUD)
            canvas.blit(hp_txt, (bar_x + bar_w + 12, bar_y - 2))

            # EMP & Evasive Roll Ability HUD Indicators
            emp_pct = max(0.0, 1.0 - (drone.emp_cooldown / drone.emp_cooldown_max))
            emp_color = COLOR_CYAN if emp_pct >= 1.0 else (100, 116, 139)
            emp_status_txt = "EMP READY [E]" if emp_pct >= 1.0 else f"EMP {int(emp_pct*100)}%"
            emp_surf = font_hud.render(emp_status_txt, True, emp_color)
            canvas.blit(emp_surf, (20, 72))

            roll_pct = max(0.0, 1.0 - (drone.roll_cooldown / 2.0))
            roll_color = COLOR_EMERALD if roll_pct >= 1.0 else (100, 116, 139)
            roll_status_txt = "ROLL READY [SHIFT]" if roll_pct >= 1.0 else f"ROLL {int(roll_pct*100)}%"
            roll_surf = font_hud.render(roll_status_txt, True, roll_color)
            canvas.blit(roll_surf, (180, 72))

            # Difficulty Indicator on HUD
            diff_color = COLOR_GOLD if difficulty_mode == 1 else ((239, 68, 68) if difficulty_mode == 2 else COLOR_CYAN)
            diff_surf = font_hud.render(f"MODE: {DIFFICULTY_NAMES[difficulty_mode]}", True, diff_color)
            canvas.blit(diff_surf, (SCREEN_WIDTH - 340, 48))

            # Weather Hazard Indicator
            if weather_type != "clear":
                w_str = "🌧️ STORMY RAIN" if weather_type == "rain" else f"💨 GUSTY WIND ({'EAST' if wind_force > 0 else 'WEST'})"
                w_surf = font_hud.render(w_str, True, (186, 230, 253))
                canvas.blit(w_surf, (360, 72))

            # Combo Multiplier Indicator
            if combo_count > 1:
                combo_surf = font_banner.render(f"{combo_count}X COMBO!", True, COLOR_GOLD)
                canvas.blit(combo_surf, (SCREEN_WIDTH // 2 - 80, 50))

            # Render Boss HUD Health Bar if Boss Target is present
            boss_target = next((t for t in target_group if t.target_type == TARGET_TYPE_BOSS), None)
            if boss_target:
                b_bar_w = 400
                b_bar_h = 20
                b_bar_x = (SCREEN_WIDTH - b_bar_w) // 2
                b_bar_y = 18
                pygame.draw.rect(canvas, (15, 23, 42), (b_bar_x - 4, b_bar_y - 4, b_bar_w + 8, b_bar_h + 8))
                pygame.draw.rect(canvas, (30, 41, 59), (b_bar_x, b_bar_y, b_bar_w, b_bar_h))
                b_pct = max(0.0, boss_target.hp / boss_target.max_hp)
                pygame.draw.rect(canvas, (239, 68, 68), (b_bar_x, b_bar_y, int(b_bar_w * b_pct), b_bar_h))
                pygame.draw.rect(canvas, COLOR_GOLD, (b_bar_x, b_bar_y, b_bar_w, b_bar_h), 2)
                boss_txt = font_hud.render(f"⚠️ BOSS DREADNOUGHT CRUISER - {boss_target.hp}/{boss_target.max_hp} HP", True, COLOR_GOLD)
                canvas.blit(boss_txt, boss_txt.get_rect(center=(SCREEN_WIDTH // 2, b_bar_y - 12)))

        # --- PAUSED SCREEN OVERLAY ---
        if game_state == STATE_PAUSED:
            p_box_w, p_box_h = 740, 330
            p_box_x = (SCREEN_WIDTH - p_box_w) // 2
            p_box_y = (SCREEN_HEIGHT - p_box_h) // 2

            p_dialog = pygame.Surface((p_box_w, p_box_h), pygame.SRCALPHA)
            p_dialog.fill((15, 23, 42, 240))
            pygame.draw.rect(p_dialog, COLOR_CYAN, (0, 0, p_box_w, p_box_h), 3)
            pygame.draw.rect(p_dialog, COLOR_GOLD, (4, 4, p_box_w - 8, p_box_h - 8), 1)
            canvas.blit(p_dialog, (p_box_x, p_box_y))

            p_title = font_banner.render("⏸️ GAME PAUSED — TACTICAL COMMAND", True, COLOR_CYAN)
            p_resume = font_banner.render("Press 'P' or Click Anywhere to Resume", True, COLOR_EMERALD)
            p_shop = font_hud.render("🛸 Press [H]: Visit Hangar Shop & Upgrade Drone", True, COLOR_COIN)
            p_diff = font_hud.render(f"☠️ Press [D]: Cycle Difficulty  (Mode: {DIFFICULTY_NAMES[difficulty_mode]})", True, COLOR_GOLD)
            p_upg = font_hud.render("⚡ Quick Upgrades: [1] Battery | [2] Speed | [3] Fire-Rate | [4] EMP", True, COLOR_HUD)
            p_screen = font_hud.render("📺 F11/F: Fullscreen | F2: 720p | F3: 900p | F4: 1080p | [M]: Main Menu", True, (186, 230, 253))

            canvas.blit(p_title, p_title.get_rect(center=(SCREEN_WIDTH // 2, p_box_y + 40)))
            canvas.blit(p_resume, p_resume.get_rect(center=(SCREEN_WIDTH // 2, p_box_y + 90)))
            canvas.blit(p_shop, p_shop.get_rect(center=(SCREEN_WIDTH // 2, p_box_y + 140)))
            canvas.blit(p_diff, p_diff.get_rect(center=(SCREEN_WIDTH // 2, p_box_y + 185)))
            canvas.blit(p_upg, p_upg.get_rect(center=(SCREEN_WIDTH // 2, p_box_y + 230)))
            canvas.blit(p_screen, p_screen.get_rect(center=(SCREEN_WIDTH // 2, p_box_y + 275)))

        # --- Hangar / Shop Screen ---
        elif game_state == STATE_HANGAR:
            shop_title = font_title.render("🛸 DRONE HANGAR & UPGRADES 🛸", True, COLOR_CYAN)
            coin_display = font_banner.render(f"Available Gold Scrap: ${coins}", True, COLOR_COIN)
            
            sub_prompt = f"👉 Press SPACE to Start Level {current_level + 1} 👈" if shop_return_state == STATE_LEVEL_CLEAR else "👉 Press SPACE to Play 👈"
            sub_txt = font_hud.render(f"Click Any Card or Press Keys [1] [2] [3] [4] to Upgrade | {sub_prompt}", True, COLOR_HUD)

            canvas.blit(shop_title, shop_title.get_rect(center=(SCREEN_WIDTH // 2, 65)))
            canvas.blit(coin_display, coin_display.get_rect(center=(SCREEN_WIDTH // 2, 120)))
            canvas.blit(sub_txt, sub_txt.get_rect(center=(SCREEN_WIDTH // 2, 165)))

            m_pos = get_virtual_mouse_pos()
            upg_keys_str = ["1", "2", "3", "4"]


            for idx, (rect, name) in enumerate(card_rects):
                gx, gy = rect.x, rect.y
                info = UPGRADES[name]
                cur_lvl = upgrade_levels.get(name, 0)
                max_lvl = info["max_lvl"]
                cost = int(info["base_cost"] * (info["cost_mult"] ** cur_lvl))
                is_max = cur_lvl >= max_lvl
                can_afford = coins >= cost and not is_max
                is_hovered = rect.collidepoint(m_pos)

                card_w, card_h = rect.width, rect.height
                
                # Dynamic hover colors
                if is_hovered and can_afford:
                    bg_color = (30, 58, 110) # Highlighted navy
                    border_color = COLOR_GOLD # Glowing Gold border
                    border_width = 3
                elif can_afford:
                    bg_color = (30, 41, 59)
                    border_color = COLOR_CYAN
                    border_width = 2
                else:
                    bg_color = (15, 23, 42)
                    border_color = (71, 85, 105)
                    border_width = 1

                pygame.draw.rect(canvas, bg_color, rect)
                pygame.draw.rect(canvas, border_color, rect, border_width)

                # Upgrade Header
                name_surf = font_banner.render(f"[{upg_keys_str[idx]}] {info['name']}", True, COLOR_GOLD if (is_hovered and can_afford) else COLOR_CYAN)
                canvas.blit(name_surf, (gx + 16, gy + 16))

                # Level Progress Meter
                meter_txt = f"Level {cur_lvl} / {max_lvl}" if not is_max else "MAX LEVEL REACHED"
                lvl_surf = font_hud.render(meter_txt, True, COLOR_EMERALD if is_max else COLOR_HUD)
                canvas.blit(lvl_surf, (gx + 16, gy + 65))

                # Level Meter Blocks
                for b in range(max_lvl):
                    bx = gx + 16 + b * 28
                    by = gy + 95
                    b_color = COLOR_EMERALD if b < cur_lvl else (51, 65, 85)
                    pygame.draw.rect(canvas, b_color, (bx, by, 22, 12))

                # Price Tag & Click Button
                if is_max:
                    btn_rect = pygame.Rect(gx + card_w - 140, gy + 105, 120, 36)
                    pygame.draw.rect(canvas, (51, 65, 85), btn_rect)
                    btn_txt = font_hud.render("MAXED", True, (148, 163, 184))
                    canvas.blit(btn_txt, btn_txt.get_rect(center=btn_rect.center))
                else:
                    btn_rect = pygame.Rect(gx + card_w - 160, gy + 105, 140, 38)
                    btn_bg = COLOR_GOLD if (is_hovered and can_afford) else ((30, 41, 59) if can_afford else (15, 23, 42))
                    btn_border = COLOR_GOLD if can_afford else (71, 85, 105)
                    
                    pygame.draw.rect(canvas, btn_bg, btn_rect)
                    pygame.draw.rect(canvas, btn_border, btn_rect, 2)
                    
                    btn_txt_color = (15, 23, 42) if (is_hovered and can_afford) else (COLOR_COIN if can_afford else (148, 163, 184))
                    btn_txt = font_hud.render(f"BUY ${cost}", True, btn_txt_color)
                    canvas.blit(btn_txt, btn_txt.get_rect(center=btn_rect.center))

            # Bottom Launch / Resume Button
            is_launch_hovered = launch_btn_rect.collidepoint(m_pos)
            l_bg = COLOR_EMERALD if is_launch_hovered else (30, 41, 59)
            l_border = (255, 255, 255) if is_launch_hovered else COLOR_EMERALD
            pygame.draw.rect(canvas, l_bg, launch_btn_rect)
            pygame.draw.rect(canvas, l_border, launch_btn_rect, 3)

            l_str = f"🚀 START LEVEL {current_level + 1} NOW!" if shop_return_state == STATE_LEVEL_CLEAR else "🚀 LAUNCH MISSION NOW!"
            l_txt_color = (15, 23, 42) if is_launch_hovered else COLOR_EMERALD
            l_surf = font_banner.render(l_str, True, l_txt_color)
            canvas.blit(l_surf, l_surf.get_rect(center=launch_btn_rect.center))



        # --- Celebration Screen (Level Clear / Level Finished Notification) ---
        elif game_state == STATE_LEVEL_CLEAR:
            points_per_level = 1500 + (current_level - 1) * 1700
            
            box_w, box_h = 820, 340
            box_x = (SCREEN_WIDTH - box_w) // 2
            box_y = (SCREEN_HEIGHT - box_h) // 2
            
            dialog_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            dialog_surf.fill((15, 23, 42, 235))
            pygame.draw.rect(dialog_surf, COLOR_CYAN, (0, 0, box_w, box_h), 3)
            pygame.draw.rect(dialog_surf, COLOR_GOLD, (4, 4, box_w - 8, box_h - 8), 1)
            canvas.blit(dialog_surf, (box_x, box_y))

            title_surf = font_banner.render(f"🏆 MISSION COMPLETE! LEVEL {current_level} FINISHED! 🏆", True, COLOR_CYAN)
            score_surf = font_banner.render(f"Level Goal Achieved: {points_per_level} / {points_per_level} PTS", True, COLOR_GOLD)
            coins_surf = font_hud.render(f"Total Score: {total_score}   |   Current Gold Scrap: ${coins}", True, (226, 232, 240))
            
            shop_prompt = font_banner.render("🛒 Press [H] to Visit Hangar Shop & Upgrade Drone", True, COLOR_COIN)
            launch_prompt = font_banner.render(f"🚀 Press [SPACE], [ENTER], or [S] to Start Level {current_level + 1}", True, COLOR_EMERALD)

            canvas.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, box_y + 48)))
            canvas.blit(score_surf, score_surf.get_rect(center=(SCREEN_WIDTH // 2, box_y + 105)))
            canvas.blit(coins_surf, coins_surf.get_rect(center=(SCREEN_WIDTH // 2, box_y + 155)))
            canvas.blit(shop_prompt, shop_prompt.get_rect(center=(SCREEN_WIDTH // 2, box_y + 215)))
            canvas.blit(launch_prompt, launch_prompt.get_rect(center=(SCREEN_WIDTH // 2, box_y + 275)))


        # --- Menu Screens ---
        elif game_state == STATE_MENU:
            title_surf = font_title.render("DRONE HUNTER", True, COLOR_CYAN)
            subtitle_surf = font_hud.render("Sci-Fi 2D Tactical Arcade Side-Scroller", True, (148, 163, 184))
            high_surf = font_banner.render(f"HIGH SCORE: {highscore}   |   GOLD SCRAP: ${coins}", True, COLOR_GOLD)
            
            diff_color = COLOR_GOLD if difficulty_mode == 1 else ((239, 68, 68) if difficulty_mode == 2 else COLOR_CYAN)
            diff_menu_surf = font_banner.render(f"DIFFICULTY: {DIFFICULTY_NAMES[difficulty_mode]}  [Press 'D' to Cycle]", True, diff_color)

            start_surf = font_banner.render("Press SPACE to Play   |   Press 'H' for Hangar Shop", True, COLOR_EMERALD)
            controls_surf = font_hud.render("WASD/Arrows: Flight | Shift: Evasive Roll | Left-Click: Shoot | E: EMP | P: Pause", True, COLOR_HUD)
            screen_guide_surf = font_hud.render("📺 F11/F: Fullscreen | F2: 720p | F3: 900p | F4: 1080p | Resizable Window", True, (186, 230, 253))

            canvas.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 170)))
            canvas.blit(subtitle_surf, subtitle_surf.get_rect(center=(SCREEN_WIDTH // 2, 235)))
            canvas.blit(diff_menu_surf, diff_menu_surf.get_rect(center=(SCREEN_WIDTH // 2, 300)))
            canvas.blit(high_surf, high_surf.get_rect(center=(SCREEN_WIDTH // 2, 365)))
            canvas.blit(start_surf, start_surf.get_rect(center=(SCREEN_WIDTH // 2, 450)))
            canvas.blit(controls_surf, controls_surf.get_rect(center=(SCREEN_WIDTH // 2, 545)))
            canvas.blit(screen_guide_surf, screen_guide_surf.get_rect(center=(SCREEN_WIDTH // 2, 595)))

        # --- GAME OVER / DEFEAT SCREEN ---
        elif game_state == STATE_GAME_OVER:
            go_box_w, go_box_h = 780, 310
            go_box_x = (SCREEN_WIDTH - go_box_w) // 2
            go_box_y = (SCREEN_HEIGHT - go_box_h) // 2

            go_dialog = pygame.Surface((go_box_w, go_box_h), pygame.SRCALPHA)
            go_dialog.fill((15, 23, 42, 235))
            pygame.draw.rect(go_dialog, (239, 68, 68), (0, 0, go_box_w, go_box_h), 3) # Crimson Red border
            pygame.draw.rect(go_dialog, COLOR_GOLD, (4, 4, go_box_w - 8, go_box_h - 8), 1)
            canvas.blit(go_dialog, (go_box_x, go_box_y))

            over_surf = font_gameover.render("☠️ MISSION FAILED - DRONE DESTROYED ☠️", True, (239, 68, 68))
            stats_surf = font_banner.render(f"Final Level: {current_level}   |   Final Score: {total_score}", True, COLOR_GOLD)
            reset_note_surf = font_hud.render("⚠️ Run Scores & Level Progress Reset to Zero for Next Game", True, (239, 68, 68))
            coins_stat_surf = font_hud.render(f"Gold Scrap Coins Saved: ${coins}   |   High Score: {highscore}", True, COLOR_HUD)
            restart_surf = font_banner.render("👉 Press [R], [SPACE], or [S] to Restart Fresh 👈", True, COLOR_CYAN)

            canvas.blit(over_surf, over_surf.get_rect(center=(SCREEN_WIDTH // 2, go_box_y + 45)))
            canvas.blit(stats_surf, stats_surf.get_rect(center=(SCREEN_WIDTH // 2, go_box_y + 100)))
            canvas.blit(reset_note_surf, reset_note_surf.get_rect(center=(SCREEN_WIDTH // 2, go_box_y + 145)))
            canvas.blit(coins_stat_surf, coins_stat_surf.get_rect(center=(SCREEN_WIDTH // 2, go_box_y + 185)))
            canvas.blit(restart_surf, restart_surf.get_rect(center=(SCREEN_WIDTH // 2, go_box_y + 245)))

        # Render Virtual Canvas onto Window Display with smooth scaling
        cur_w, cur_h = screen.get_size()
        if cur_w > 0 and cur_h > 0:
            scaled_canvas = pygame.transform.smoothscale(canvas, (cur_w, cur_h))
            screen.blit(scaled_canvas, (shake_offset_x, shake_offset_y))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
