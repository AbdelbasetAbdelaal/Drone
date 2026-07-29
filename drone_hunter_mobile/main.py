import os
import sys
import json
import math
import random

# Ensure local directory is on sys.path so local 'src' imports cleanly on Android and PC
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import pygame

# Android Environment Storage Detection
IS_ANDROID = 'ANDROID_ARGUMENT' in os.environ or 'ANDROID_ROOT' in os.environ

if IS_ANDROID:
    save_dir = os.environ.get('ANDROID_PRIVATE_DIR', current_dir)
    SAVE_FILE = os.path.join(save_dir, "save_data_mobile.json")
else:
    SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save_data_mobile.json")

from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, COLOR_BG, COLOR_HUD,
    STATE_MENU, STATE_PLAYING, STATE_GAME_OVER, STATE_LEVEL_CLEAR, STATE_HANGAR,
    STATE_PAUSED, STATE_SECTOR_SELECT, STATE_VICTORY, COLOR_CYAN, COLOR_EMERALD, COLOR_GOLD,
    COLOR_MAGENTA, COLOR_CRIMSON, COLOR_SHIELD, COLOR_OVERCLOCK, COLOR_SLOWMO,
    COLOR_COIN, COLOR_NEON_RED, TARGET_TYPE_BOSS, TARGET_TYPE_VEHICLE,
    TARGET_TYPE_TURRET, TARGET_TYPE_CHASER, UPGRADES, ROLL_COOLDOWN,
    DIFFICULTY_NAMES, DIFFICULTY_NIGHTMARE, SECTORS, WEAPON_DEFS,
    WEAPON_PULSE, WEAPON_SCATTER, WEAPON_MISSILE, WEAPON_BEAM
)
from src.player import Player
from src.target import Spawner, Target, WaveManager
from src.powerup import PowerupItem
from src.particles import ParticleManager
from src.background import ParallaxBackground
from src.audio import AudioManager
from src.obstacle import EnvironmentalObstacle
from src.hazard import LaserGridFence, GravityAnomaly
from src.ui import (
    draw_hud, draw_radar_minimap, draw_crt_scanlines, draw_crosshair,
    draw_sector_select_ui, draw_hangar_shop_ui, draw_exit_button,
    draw_campaign_victory_ui, draw_pause_settings_ui, draw_virtual_touch_controls,
    draw_nav_buttons, draw_game_over_screen, draw_boss_health_bar, draw_combo_banner
)

def load_save_data():
    """Loads coins, highscore, upgrade levels, sector unlocks, sub-level stage unlocks, and skin theme from save file."""
    default_upgrades = {"battery": 0, "speed": 0, "fire_rate": 0, "emp_recharge": 0, "wingman": 0, "cloak": 0, "missiles": 0, "beam": 0}
    default_sectors = [True, False, False, False, False]
    default_stages = [True] + [False] * 14
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                coins = data.get("coins", 0)
                highscore = data.get("highscore", 0)
                upgrades = data.get("upgrades", default_upgrades)
                sectors = data.get("sectors", default_sectors)
                stages = data.get("stages", default_stages)
                while len(sectors) < len(SECTORS):
                    sectors.append(False)
                while len(stages) < 15:
                    stages.append(False)
                show_crt = data.get("show_crt", False)
                skin_theme = data.get("skin_theme", 0)
                return coins, highscore, upgrades, sectors, stages, show_crt, skin_theme
        except Exception:
            return 0, 0, default_upgrades, default_sectors, default_stages, False, 0
    return 0, 0, default_upgrades, default_sectors, default_stages, False, 0

def save_game_data(coins: int, highscore: int, upgrades: dict[str, int], sectors: list[bool], show_crt: bool = False, stages: list[bool] = None, skin_theme: int = 0):
    """Saves progress state to JSON file."""
    if stages is None:
        stages = [True] + [False] * 14
    try:
        data = {
            "coins": coins,
            "highscore": highscore,
            "upgrades": upgrades,
            "sectors": sectors,
            "stages": stages,
            "show_crt": show_crt,
            "skin_theme": skin_theme
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def main():
    try: pygame.init()
    except Exception: pass

    try: pygame.font.init()
    except Exception: pass

    if IS_ANDROID:
        try:
            screen = pygame.display.set_mode((0, 0))
            win_w, win_h = screen.get_size()
        except Exception:
            screen = pygame.display.set_mode((1280, 720))
            win_w, win_h = 1280, 720
    else:
        win_w, win_h = 1280, 720
        screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)

    pygame.display.set_caption(f"{TITLE} [MOBILE EDITION]")
    clock = pygame.time.Clock()

    canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    # Core Systems
    background = ParallaxBackground()
    particle_manager = ParticleManager()
    audio_manager = AudioManager()

    # Fonts
    from src.ui import safe_create_font
    font_title = safe_create_font("Impact", 54)
    font_hud = safe_create_font("Consolas", 18, bold=True)
    font_banner = safe_create_font("Verdana", 24, bold=True)
    font_gameover = safe_create_font("Impact", 52)

    # Sprite Groups
    player_group = pygame.sprite.GroupSingle()
    bullet_group = pygame.sprite.Group()
    enemy_bullet_group = pygame.sprite.Group()
    target_group = pygame.sprite.Group()
    obstacle_group = pygame.sprite.Group()
    hazard_group = pygame.sprite.Group()
    powerup_group = pygame.sprite.Group()

    # Save Data & Game State
    coins, highscore, upgrade_levels, unlocked_sectors, unlocked_stages, show_crt, current_skin_theme = load_save_data()
    game_state = STATE_MENU
    difficulty_mode = 0
    is_diff_dropdown_open = False
    current_sector_idx = 0
    current_sub_level = 1
    
    current_level = 1
    level_score = 0
    total_score = 0
    combo_count = 1
    combo_timer = 0.0

    obstacle_timer = 0.0
    next_obstacle_spawn = random.uniform(3.0, 6.0)
    hazard_timer = 0.0
    next_hazard_spawn = random.uniform(5.0, 9.0)
    ambient_timer = 0.0

    screen_shake_time = 0.0
    screen_shake_intensity = 0.0

    drone = None
    spawner = None
    wave_manager = None

    def get_canvas_pos(raw_pos):
        try:
            real_w, real_h = screen.get_size()
            if real_w <= 0 or real_h <= 0:
                return raw_pos
            cx = int(raw_pos[0] * SCREEN_WIDTH / real_w)
            cy = int(raw_pos[1] * SCREEN_HEIGHT / real_h)
            return (cx, cy)
        except Exception:
            return raw_pos

    # Mobile Virtual Touch Controls State — D-Pad
    dpad_state = {"up": False, "down": False, "left": False, "right": False}
    touch_fire = False
    touch_aim_pos = (SCREEN_WIDTH - 200, SCREEN_HEIGHT // 2)
    auto_fire_enabled = False
    damage_flash_timer = 0.0

    def trigger_shake(intensity: float = 6.0, duration: float = 0.25):
        nonlocal screen_shake_intensity, screen_shake_time
        screen_shake_intensity = intensity
        screen_shake_time = duration

    def reset_game():
        nonlocal drone, spawner, wave_manager, current_level, level_score, total_score, combo_count, combo_timer, obstacle_timer, hazard_timer
        current_level = 1
        level_score = 0
        total_score = 0
        combo_count = 1
        combo_timer = 0.0
        obstacle_timer = 0.0
        hazard_timer = 0.0
        
        bullet_group.empty()
        enemy_bullet_group.empty()
        target_group.empty()
        obstacle_group.empty()
        hazard_group.empty()
        powerup_group.empty()
        particle_manager.particles.empty()
        particle_manager.floating_texts.empty()
        
        drone = Player((200, SCREEN_HEIGHT // 2))
        drone.skin_theme = current_skin_theme
        drone._rotation_cache.clear()
        drone._render_drone_sprite()
        drone.apply_shop_upgrades(upgrade_levels)
        player_group.add(drone)
        
        sec_info = SECTORS[current_sector_idx]
        stages = sec_info.get("stages", [])
        target_score = stages[current_sub_level - 1]["score"] if (0 < current_sub_level <= len(stages)) else sec_info.get("base_target_score", 6000)
        
        spawner = Spawner(base_min_interval=1.5, base_max_interval=3.0)
        spawner.set_level(current_sector_idx * 3 + current_sub_level, current_sector_idx)
        wave_manager = WaveManager(target_score)
        background.set_sector(current_sector_idx)

        if current_sub_level >= 2 or upgrade_levels.get("beam", 0) > 0:
            if WEAPON_BEAM not in drone.available_weapons:
                drone.available_weapons.append(WEAPON_BEAM)

    def start_next_stage():
        nonlocal current_sub_level, current_sector_idx, unlocked_stages, unlocked_sectors
        current_sub_level += 1
        if current_sub_level > 3:
            current_sub_level = 1
            if current_sector_idx < len(SECTORS) - 1:
                current_sector_idx += 1
                unlocked_sectors[current_sector_idx] = True

        flat_idx = current_sector_idx * 3 + (current_sub_level - 1)
        if flat_idx < len(unlocked_stages):
            unlocked_stages[flat_idx] = True

        save_game_data(coins, highscore, upgrade_levels, unlocked_sectors, show_crt, unlocked_stages)

        if current_sector_idx >= len(SECTORS):
            nonlocal game_state
            game_state = STATE_VICTORY
        else:
            reset_game()
            game_state = STATE_PLAYING

    def execute_emp_blast():
        nonlocal coins, level_score, total_score, combo_count, combo_timer, highscore
        if drone and drone.trigger_emp():
            audio_manager.play_emp()
            trigger_shake(12.0, 0.45)
            particle_manager.spawn_emp_shockwave(drone.pos)
            
            for t in list(target_group):
                pts = t.score_value * combo_count
                coins += max(1, pts // 25)
                level_score += pts
                total_score += pts
                combo_count = min(99, combo_count + 1)
                combo_timer = 4.5
                t.kill()
                particle_manager.spawn_explosion(t.rect.center, count=25, color=(56, 189, 248))
                particle_manager.spawn_floating_text(t.rect.center, f"+{pts} EMP!", COLOR_CYAN, 24)

            for b in list(enemy_bullet_group):
                b.kill()
                particle_manager.spawn_spark(b.rect.center, count=6, color=(56, 189, 248))

            for obs in list(obstacle_group):
                obs.kill()
                particle_manager.spawn_explosion(obs.rect.center, count=30, color=(239, 68, 68))

            enemy_bullet_group.empty()
            if total_score > highscore:
                highscore = total_score
            save_game_data(coins, highscore, upgrade_levels, unlocked_sectors, show_crt, unlocked_stages)

    def execute_barrel_roll():
        if drone and drone.trigger_roll(dir_x=1.0):
            audio_manager.play_roll()
            trigger_shake(4.0, 0.18)
            particle_manager.spawn_floating_text(drone.pos, "🌀 EVASIVE ROLL!", COLOR_CYAN, 22)

    def execute_cloak():
        if drone and drone.trigger_cloak():
            audio_manager.play_cloak()
            particle_manager.spawn_floating_text(drone.pos, "👻 CLOAKING INVISIBILITY!", COLOR_CYAN, 24)

    def buy_upgrade(name: str) -> bool:
        nonlocal coins
        if name not in UPGRADES:
            return False
        info = UPGRADES[name]
        cur_lvl = upgrade_levels.get(name, 0)
        cost = int(info["base_cost"] * (info["cost_mult"] ** cur_lvl))
        if cur_lvl < info["max_lvl"] and coins >= cost:
            coins -= cost
            upgrade_levels[name] = cur_lvl + 1
            audio_manager.play_buy()
            save_game_data(coins, highscore, upgrade_levels, unlocked_sectors, show_crt, unlocked_stages)
            if drone:
                drone.apply_shop_upgrades(upgrade_levels)
            return True
        return False

    reset_game()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        background.update(dt)

        shake_offset_x, shake_offset_y = 0, 0
        if screen_shake_time > 0:
            screen_shake_time -= dt
            shake_offset_x = random.randint(-int(screen_shake_intensity), int(screen_shake_intensity))
            shake_offset_y = random.randint(-int(screen_shake_intensity), int(screen_shake_intensity))

        cur_wave = 1
        if game_state in (STATE_PLAYING, STATE_VICTORY):
            sec_info = SECTORS[current_sector_idx]
            cur_wave = wave_manager.update_wave(level_score)
            particle_manager.spawn_weather(sec_info.get("weather", "clear"))
            particle_manager.update(dt)

            if current_sector_idx == 3 and drone and drone.alive:
                drone.pos.y += math.sin(pygame.time.get_ticks() * 0.003) * 18.0 * dt

            ambient_timer += dt
            if ambient_timer >= 4.0:
                ambient_timer = 0.0
                audio_manager.play_sector_ambient(current_sector_idx)

            if game_state == STATE_PLAYING:
                obstacle_timer += dt
                if obstacle_timer >= next_obstacle_spawn:
                    obstacle_timer = 0.0
                    next_obstacle_spawn = random.uniform(3.5, 6.5)
                    if current_sector_idx == 3: obs_type = "sea_mine"
                    elif current_sector_idx == 2: obs_type = "asteroid"
                    elif current_sector_idx in (1, 4): obs_type = "barrel"
                    else: obs_type = random.choice(["sea_mine", "barrel"])
                    obstacle_group.add(EnvironmentalObstacle(obs_type, sector_idx=current_sector_idx))

                hazard_timer += dt
                if hazard_timer >= next_hazard_spawn:
                    hazard_timer = 0.0
                    next_hazard_spawn = random.uniform(6.0, 11.0)
                    if current_sector_idx in (0, 1):
                        hazard_group.add(LaserGridFence(SCREEN_WIDTH + 40))
                    else:
                        hazard_group.add(GravityAnomaly())

        if combo_count > 1:
            combo_timer -= dt
            if combo_timer <= 0.0:
                combo_count = 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if not IS_ANDROID:
                    running = False
                else:
                    game_state = STATE_PAUSED

            elif event.type == pygame.VIDEORESIZE:
                win_w, win_h = event.w, event.h

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F2:
                    show_crt = not show_crt
                    save_game_data(coins, highscore, upgrade_levels, unlocked_sectors, show_crt, unlocked_stages)

                if event.key == pygame.K_q and game_state in (STATE_MENU, STATE_SECTOR_SELECT, STATE_HANGAR, STATE_VICTORY):
                    if not IS_ANDROID:
                        running = False
                    else:
                        game_state = STATE_MENU

                if game_state == STATE_MENU:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        game_state = STATE_SECTOR_SELECT

                elif game_state == STATE_SECTOR_SELECT:
                    if event.key == pygame.K_d:
                        difficulty_mode = (difficulty_mode + 1) % 4
                    elif event.key in (pygame.K_1, pygame.K_KP1) and unlocked_stages[0]:
                        current_sector_idx = 0; current_sub_level = 1; reset_game(); game_state = STATE_PLAYING
                    elif event.key in (pygame.K_2, pygame.K_KP2) and unlocked_stages[3]:
                        current_sector_idx = 1; current_sub_level = 1; reset_game(); game_state = STATE_PLAYING
                    elif event.key in (pygame.K_3, pygame.K_KP3) and unlocked_stages[6]:
                        current_sector_idx = 2; current_sub_level = 1; reset_game(); game_state = STATE_PLAYING
                    elif event.key in (pygame.K_4, pygame.K_KP4) and unlocked_stages[9]:
                        current_sector_idx = 3; current_sub_level = 1; reset_game(); game_state = STATE_PLAYING
                    elif event.key in (pygame.K_5, pygame.K_KP5) and unlocked_stages[12]:
                        current_sector_idx = 4; current_sub_level = 1; reset_game(); game_state = STATE_PLAYING
                    elif event.key in (pygame.K_SPACE, pygame.K_h):
                        game_state = STATE_HANGAR

                elif game_state == STATE_HANGAR:
                    if event.key == pygame.K_1: buy_upgrade("battery")
                    elif event.key == pygame.K_2: buy_upgrade("speed")
                    elif event.key == pygame.K_3: buy_upgrade("fire_rate")
                    elif event.key == pygame.K_4: buy_upgrade("emp_recharge")
                    elif event.key == pygame.K_5: buy_upgrade("wingman")
                    elif event.key == pygame.K_6: buy_upgrade("cloak")
                    elif event.key == pygame.K_7: buy_upgrade("missiles")
                    elif event.key == pygame.K_8: buy_upgrade("beam")
                    elif event.key == pygame.K_m: game_state = STATE_SECTOR_SELECT
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        reset_game()
                        game_state = STATE_PLAYING

                elif game_state == STATE_PLAYING:
                    if event.key in (pygame.K_p, pygame.K_ESCAPE):
                        game_state = STATE_PAUSED
                    elif event.key == pygame.K_e:
                        execute_emp_blast()
                    elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        execute_barrel_roll()
                    elif event.key in (pygame.K_k, pygame.K_c):
                        execute_cloak()
                    elif event.key == pygame.K_TAB:
                        if drone: drone.cycle_weapon()

                elif game_state == STATE_PAUSED:
                    if event.key in (pygame.K_p, pygame.K_SPACE):
                        game_state = STATE_PLAYING
                    elif event.key == pygame.K_d:
                        difficulty_mode = (difficulty_mode + 1) % 4
                    elif event.key == pygame.K_s:
                        audio_manager.sound_enabled = not audio_manager.sound_enabled
                    elif event.key == pygame.K_h:
                        game_state = STATE_HANGAR
                    elif event.key == pygame.K_m:
                        game_state = STATE_SECTOR_SELECT
                    elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                        if not IS_ANDROID:
                            running = False
                        else:
                            game_state = STATE_MENU

                elif game_state == STATE_VICTORY:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        difficulty_mode = DIFFICULTY_NIGHTMARE
                        current_sector_idx = 4
                        current_sub_level = 3
                        reset_game()
                        game_state = STATE_PLAYING
                    elif event.key == pygame.K_m:
                        game_state = STATE_SECTOR_SELECT
                    elif event.key == pygame.K_h:
                        game_state = STATE_HANGAR

                elif game_state in (STATE_GAME_OVER, STATE_LEVEL_CLEAR):
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        if game_state == STATE_LEVEL_CLEAR:
                            start_next_stage()
                        else:
                            reset_game()
                            game_state = STATE_PLAYING

            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                raw_p = (event.x * screen.get_width(), event.y * screen.get_height()) if event.type == pygame.FINGERDOWN else pygame.mouse.get_pos()
                mx, my = get_canvas_pos(raw_p)

                if game_state == STATE_MENU:
                    # Draw nav buttons to get rects, then check tap
                    nav = draw_nav_buttons(canvas, mode="menu")
                    if "enter" in nav and nav["enter"].collidepoint(mx, my):
                        game_state = STATE_SECTOR_SELECT
                    else:
                        game_state = STATE_SECTOR_SELECT  # tap anywhere on menu works too

                elif game_state == STATE_LEVEL_CLEAR:
                    nav = draw_nav_buttons(canvas, mode="level_clear")
                    if "map" in nav and nav["map"].collidepoint(mx, my):
                        game_state = STATE_SECTOR_SELECT
                    else:
                        start_next_stage()

                elif game_state == STATE_GAME_OVER:
                    go_nav = draw_game_over_screen(canvas, total_score, highscore, current_sector_idx, current_sub_level)
                    if "map" in go_nav and go_nav["map"].collidepoint(mx, my):
                        game_state = STATE_SECTOR_SELECT
                    else:
                        reset_game()
                        game_state = STATE_PLAYING

                elif game_state == STATE_VICTORY:
                    nav = draw_nav_buttons(canvas, mode="victory")
                    if "map" in nav and nav["map"].collidepoint(mx, my):
                        game_state = STATE_SECTOR_SELECT
                    else:
                        difficulty_mode = DIFFICULTY_NIGHTMARE
                        current_sector_idx = 4
                        current_sub_level = 3
                        reset_game()
                        game_state = STATE_PLAYING

                elif game_state == STATE_SECTOR_SELECT:
                    exit_rect = pygame.Rect(SCREEN_WIDTH - 140, SCREEN_HEIGHT - 55, 120, 40)
                    diff_rect = pygame.Rect(480, 24, 220, 36)
                    hangar_btn_r = pygame.Rect(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT - 58, 220, 46)
                    if exit_rect.collidepoint(mx, my):
                        save_game_data(coins, highscore, upgrade_levels, unlocked_sectors, show_crt, unlocked_stages, current_skin_theme)
                        running = False
                    elif diff_rect.collidepoint(mx, my):
                        difficulty_mode = (difficulty_mode + 1) % 4
                    elif hangar_btn_r.collidepoint(mx, my):
                        game_state = STATE_HANGAR
                    else:
                        card_w = 226
                        start_x = 44
                        gap = 18
                        for idx in range(len(SECTORS)):
                            cx = start_x + idx * (card_w + gap)
                            card_r = pygame.Rect(cx, 85, card_w, 530)
                            
                            stage_y_start = 85 + 345
                            selected_stage = False
                            for stg_i in range(3):
                                stg_r = pygame.Rect(cx + 10, stage_y_start + stg_i * 38, card_w - 20, 34)
                                if stg_r.collidepoint(mx, my):
                                    flat_idx = idx * 3 + stg_i
                                    stg_unlocked = unlocked_stages[flat_idx] if flat_idx < len(unlocked_stages) else (flat_idx == 0)
                                    if stg_unlocked:
                                        current_sector_idx = idx
                                        current_sub_level = stg_i + 1
                                        reset_game()
                                        game_state = STATE_PLAYING
                                        selected_stage = True
                                        break

                            if selected_stage:
                                break

                            if card_r.collidepoint(mx, my):
                                first_stg_idx = idx * 3
                                is_unlocked = unlocked_stages[first_stg_idx] if first_stg_idx < len(unlocked_stages) else (idx == 0)
                                if is_unlocked:
                                    current_sector_idx = idx
                                    current_sub_level = 1
                                    reset_game()
                                    game_state = STATE_PLAYING
                                    break

                elif game_state == STATE_HANGAR:
                    upg_rects, exit_r, skin_r = draw_hangar_shop_ui(canvas, coins, current_sector_idx, upgrade_levels, drone_skin=current_skin_theme)
                    if skin_r.collidepoint(mx, my):
                        current_skin_theme = (current_skin_theme + 1) % 4
                        if drone:
                            drone.skin_theme = current_skin_theme
                            drone._rotation_cache.clear()
                            drone._render_drone_sprite()
                        save_game_data(coins, highscore, upgrade_levels, unlocked_sectors, show_crt, unlocked_stages, current_skin_theme)
                        audio_manager.play_powerup()
                    elif exit_r.collidepoint(mx, my):
                        save_game_data(coins, highscore, upgrade_levels, unlocked_sectors, show_crt, unlocked_stages, current_skin_theme)
                        running = False
                    else:
                        bought = False
                        for u_key, u_rect in upg_rects.items():
                            if u_rect.collidepoint(mx, my):
                                buy_upgrade(u_key)
                                bought = True
                                save_game_data(coins, highscore, upgrade_levels, unlocked_sectors, show_crt, unlocked_stages, current_skin_theme)
                                break

                        if not bought:
                            h_nav = draw_nav_buttons(canvas, mode="hangar")
                            if "map" in h_nav and h_nav["map"].collidepoint(mx, my):
                                game_state = STATE_SECTOR_SELECT
                            elif "play" in h_nav and h_nav["play"].collidepoint(mx, my):
                                reset_game()
                                game_state = STATE_PLAYING

                elif game_state == STATE_PAUSED:
                    pause_btns = draw_pause_settings_ui(canvas, difficulty_mode, show_crt, audio_manager.sound_enabled, is_diff_open=is_diff_dropdown_open)
                    
                    clicked_item = False
                    if is_diff_dropdown_open and "dropdown_items" in pause_btns:
                        for d_r, d_idx in pause_btns["dropdown_items"]:
                            if d_r.collidepoint(mx, my):
                                difficulty_mode = d_idx
                                is_diff_dropdown_open = False
                                clicked_item = True
                                break

                    if not clicked_item:
                        if pause_btns["diff"].collidepoint(mx, my):
                            is_diff_dropdown_open = not is_diff_dropdown_open
                        elif pause_btns["crt"].collidepoint(mx, my):
                            show_crt = not show_crt
                            save_game_data(coins, highscore, upgrade_levels, unlocked_sectors, show_crt, unlocked_stages)
                        elif pause_btns["sfx"].collidepoint(mx, my):
                            audio_manager.sound_enabled = not audio_manager.sound_enabled
                        elif pause_btns["resume"].collidepoint(mx, my):
                            is_diff_dropdown_open = False
                            game_state = STATE_PLAYING
                        elif pause_btns["hangar"].collidepoint(mx, my):
                            is_diff_dropdown_open = False
                            game_state = STATE_HANGAR
                        elif pause_btns["map"].collidepoint(mx, my):
                            is_diff_dropdown_open = False
                            game_state = STATE_SECTOR_SELECT
                        elif pause_btns["exit"].collidepoint(mx, my):
                            if not IS_ANDROID:
                                running = False
                            else:
                                game_state = STATE_MENU

                elif game_state == STATE_PLAYING:
                    active_touch_btn = None
                    active_wpn = drone.active_weapon if drone else "pulse"
                    touch_ctrls = draw_virtual_touch_controls(canvas, dpad_state=dpad_state, active_weapon=active_wpn, auto_fire_enabled=auto_fire_enabled)
                    if touch_ctrls["pause"].collidepoint(mx, my):
                        active_touch_btn = "pause"
                        game_state = STATE_PAUSED
                    elif "auto_fire" in touch_ctrls and touch_ctrls["auto_fire"].collidepoint(mx, my):
                        auto_fire_enabled = not auto_fire_enabled
                        audio_manager.play_powerup()
                    elif touch_ctrls["weapon"].collidepoint(mx, my):
                        active_touch_btn = "weapon"
                        if drone: drone.cycle_weapon()
                    elif touch_ctrls["emp"].collidepoint(mx, my):
                        active_touch_btn = "emp"
                        execute_emp_blast()
                    elif touch_ctrls["roll"].collidepoint(mx, my):
                        active_touch_btn = "roll"
                        execute_barrel_roll()
                    elif touch_ctrls["cloak"].collidepoint(mx, my):
                        active_touch_btn = "cloak"
                        execute_cloak()
                    elif "autolock" in touch_ctrls and touch_ctrls["autolock"].collidepoint(mx, my):
                        active_touch_btn = "autolock"
                        if drone: drone.toggle_auto_lock()
                    elif "ultimate" in touch_ctrls and touch_ctrls["ultimate"].collidepoint(mx, my):
                        active_touch_btn = "ultimate"
                        if drone: drone.trigger_ultimate(target_group, particle_manager, audio_manager, trigger_shake)
                    elif touch_ctrls["fire"].collidepoint(mx, my):
                        active_touch_btn = "fire"
                        touch_fire = True
                    elif touch_ctrls["dpad_up"].collidepoint(mx, my):
                        dpad_state["up"] = True
                    elif touch_ctrls["dpad_down"].collidepoint(mx, my):
                        dpad_state["down"] = True
                    elif touch_ctrls["dpad_left"].collidepoint(mx, my):
                        dpad_state["left"] = True
                    elif touch_ctrls["dpad_right"].collidepoint(mx, my):
                        dpad_state["right"] = True

            elif event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
                touch_fire = False
                dpad_state["up"] = False
                dpad_state["down"] = False
                dpad_state["left"] = False
                dpad_state["right"] = False

            elif event.type in (pygame.MOUSEMOTION, pygame.FINGERMOTION):
                if event.type == pygame.FINGERMOTION:
                    raw_p = (event.x * screen.get_width(), event.y * screen.get_height())
                else:
                    raw_p = pygame.mouse.get_pos()
                mx, my = get_canvas_pos(raw_p)
                touch_aim_pos = (mx, my)

                # Update d-pad on slide
                if game_state == STATE_PLAYING and mx < SCREEN_WIDTH // 2:
                    active_wpn2 = drone.active_weapon if drone else "pulse"
                    tc2 = draw_virtual_touch_controls(canvas, dpad_state=dpad_state, active_weapon=active_wpn2)
                    dpad_state["up"]    = tc2["dpad_up"].collidepoint(mx, my)
                    dpad_state["down"]  = tc2["dpad_down"].collidepoint(mx, my)
                    dpad_state["left"]  = tc2["dpad_left"].collidepoint(mx, my)
                    dpad_state["right"] = tc2["dpad_right"].collidepoint(mx, my)

        if game_state == STATE_PLAYING and drone:
            mouse_down = pygame.mouse.get_pressed()[0]
            if mouse_down:
                raw_p = pygame.mouse.get_pos()
                mx, my = get_canvas_pos(raw_p)
                active_wpn_str = drone.active_weapon if drone else "pulse"
                tc_rects = draw_virtual_touch_controls(canvas, dpad_state=dpad_state, active_weapon=active_wpn_str)
                dpad_state["up"]    = tc_rects["dpad_up"].collidepoint(mx, my)
                dpad_state["down"]  = tc_rects["dpad_down"].collidepoint(mx, my)
                dpad_state["left"]  = tc_rects["dpad_left"].collidepoint(mx, my)
                dpad_state["right"] = tc_rects["dpad_right"].collidepoint(mx, my)
            else:
                dpad_state["up"] = False
                dpad_state["down"] = False
                dpad_state["left"] = False
                dpad_state["right"] = False

            drone.dpad_up = dpad_state["up"]
            drone.dpad_down = dpad_state["down"]
            drone.dpad_left = dpad_state["left"]
            drone.dpad_right = dpad_state["right"]

            particle_manager.spawn_drone_trail((drone.pos.x - 22, drone.pos.y))
            wm_bullets = drone.update(dt, particle_manager, audio_manager, targets_group=target_group)
            for wb in wm_bullets:
                bullet_group.add(wb)

            mouse_pressed = pygame.mouse.get_pressed()
            # Auto-fire: also fire when Space is held (PC) or auto_fire_enabled is on (Mobile)
            space_held = pygame.key.get_pressed()[pygame.K_SPACE]
            should_shoot = touch_fire or mouse_pressed[0] or (auto_fire_enabled) or space_held
            if should_shoot and drone.can_shoot():
                raw_m = pygame.mouse.get_pos()
                mx, my = get_canvas_pos(raw_m) if not touch_fire else touch_aim_pos
                fired_bullets = drone.shoot((mx, my), level=current_sub_level, targets_group=target_group)
                for b in fired_bullets:
                    bullet_group.add(b)
                if drone.active_weapon == "pulse": audio_manager.play_laser()
                elif drone.active_weapon == "scatter": audio_manager.play_laser()
                elif drone.active_weapon == "missile": audio_manager.play_missile()
                elif drone.active_weapon == "beam": audio_manager.play_beam()

            # Tick damage flash timer
            damage_flash_timer = max(0.0, damage_flash_timer - dt)

            sec_info = SECTORS[current_sector_idx]
            stages = sec_info.get("stages", [])
            target_stg_score = stages[current_sub_level - 1]["score"] if (0 < current_sub_level <= len(stages)) else sec_info.get("base_target_score", 6000)

            spawner.update(dt, target_group, level_score, target_stg_score, current_wave=cur_wave)
            
            for target in list(target_group):
                new_e_bullets = target.update(dt, player_pos=(drone.pos.x, drone.pos.y), player_vel=(drone.velocity.x, drone.velocity.y), bullet_group=bullet_group)
                for eb in new_e_bullets:
                    enemy_bullet_group.add(eb)

            for h in list(hazard_group):
                if isinstance(h, GravityAnomaly):
                    h.update(dt, player=drone)
                else:
                    h.update(dt)

            obstacle_group.update(dt)
            bullet_group.update(dt)
            enemy_bullet_group.update(dt)
            powerup_group.update(dt)

            # Bullet vs Obstacle Collisions
            for b in list(bullet_group):
                hit_obs = pygame.sprite.spritecollide(b, obstacle_group, False, pygame.sprite.collide_circle)
                for obs in hit_obs:
                    b.kill()
                    if obs.take_damage(getattr(b, "damage", 35)):
                        obs.kill()
                        audio_manager.play_mine_explosion()
                        trigger_shake(9.0, 0.3)
                        particle_manager.spawn_explosion(obs.rect.center, count=35, color=(239, 68, 68))

            # Bullet vs Target Collisions
            for b in list(bullet_group):
                hits = pygame.sprite.spritecollide(b, target_group, False)
                for target in hits:
                    dmg = getattr(b, "damage", 25)
                    is_dead = target.take_damage(dmg)
                    if not getattr(b, "is_piercing", False):
                        b.kill()
                    
                    particle_manager.spawn_spark(b.rect.center, count=8, color=COLOR_CYAN)
                    audio_manager.play_hit()
                    
                    if is_dead:
                        target.kill()
                        audio_manager.play_explosion()
                        trigger_shake(6.0, 0.2)
                        
                        pts = target.score_value * combo_count
                        coins += max(1, pts // 20)
                        level_score += pts
                        total_score += pts
                        combo_count = min(99, combo_count + 1)
                        combo_timer = 4.0
                        if drone: drone.add_ultimate_charge(15.0)
                        
                        if total_score > highscore:
                            highscore = total_score
                        
                        save_game_data(coins, highscore, upgrade_levels, unlocked_sectors, show_crt, unlocked_stages)
                        
                        # Enhanced death explosion — boss vs regular enemy
                        t_type = getattr(target, "enemy_type", "standard")
                        t_color = getattr(target, "color", (250, 204, 21))
                        if t_type in ("boss", "titan_mech"):
                            particle_manager.spawn_boss_explosion(target.rect.center)
                            trigger_shake(14.0, 0.6)
                        else:
                            particle_manager.spawn_enemy_death(target.rect.center, t_color)
                        particle_manager.spawn_floating_text(target.rect.center, f"+{pts}", COLOR_GOLD, 20)
                        
                        if random.random() < 0.30:
                            p_type = random.choice(["battery", "overclock", "shield", "slowmo", "coin", "wingman", "weapon"])
                            powerup_group.add(PowerupItem(target.rect.center, p_type))

            # Enemy Bullet vs Player
            if drone and drone.alive and not drone.is_invulnerable and not drone.is_cloaked:
                e_hits = pygame.sprite.spritecollide(drone, enemy_bullet_group, True)
                for eb in e_hits:
                    if drone.shield_hits > 0:
                        drone.shield_hits = max(0, drone.shield_hits - 1)
                        audio_manager.play_hit()
                        particle_manager.spawn_spark(drone.rect.center, count=10, color=COLOR_SHIELD)
                    else:
                        drone.energy = max(0.0, drone.energy - 20.0)
                        trigger_shake(8.0, 0.25)
                        damage_flash_timer = 0.18   # ❤️ Red screen flash
                        audio_manager.play_explosion()
                        particle_manager.spawn_explosion(drone.rect.center, count=20, color=COLOR_CRIMSON)
                        if drone.energy <= 0.0:
                            drone.kill()
                            game_state = STATE_GAME_OVER
                            save_game_data(coins, highscore, upgrade_levels, unlocked_sectors, show_crt, unlocked_stages)

            # Hazards vs Player
            if drone and drone.alive and not drone.is_cloaked:
                h_hits = pygame.sprite.spritecollide(drone, hazard_group, False)
                for h in h_hits:
                    if isinstance(h, LaserGridFence):
                        drone.energy = max(0.0, drone.energy - 35.0 * dt)
                        trigger_shake(4.0, 0.1)
                        particle_manager.spawn_spark(drone.rect.center, count=4, color=COLOR_NEON_RED)
                        if drone.energy <= 0.0:
                            drone.kill()
                            game_state = STATE_GAME_OVER
                            save_game_data(coins, highscore, upgrade_levels, unlocked_sectors, show_crt, unlocked_stages)

            # Player vs Powerups
            if drone and drone.alive:
                p_hits = pygame.sprite.spritecollide(drone, powerup_group, True)
                for p in p_hits:
                    audio_manager.play_powerup()
                    if p.p_type == "battery":
                        drone.energy = min(drone.max_energy, drone.energy + 35.0)
                        particle_manager.spawn_floating_text(p.rect.center, "+ENERGY", COLOR_EMERALD, 18)
                    elif p.p_type == "overclock":
                        drone.trigger_overclock(6.0)
                        particle_manager.spawn_floating_text(p.rect.center, "OVERCLOCK!", COLOR_OVERCLOCK, 22)
                    elif p.p_type == "shield":
                        drone.activate_shield(charges=3)
                        particle_manager.spawn_floating_text(p.rect.center, "SHIELD UP", COLOR_SHIELD, 20)
                    elif p.p_type == "slowmo":
                        drone.activate_slowmo(5.0)
                        particle_manager.spawn_floating_text(p.rect.center, "TIME SLOW", COLOR_SLOWMO, 20)
                    elif p.p_type == "coin":
                        coins += 50
                        particle_manager.spawn_floating_text(p.rect.center, "+50 COINS", COLOR_COIN, 18)
                    elif p.p_type == "wingman":
                        drone.spawn_wingman()
                        particle_manager.spawn_floating_text(p.rect.center, "+WINGMAN DRONE", COLOR_CYAN, 20)
                    elif p.p_type == "weapon":
                        drone.cycle_weapon()
                        wpn_name = str(drone.active_weapon)
                        particle_manager.spawn_floating_text(p.rect.center, f"WEAPON: {wpn_name.upper()}", COLOR_GOLD, 22)

            # Advanced Stage Environmental Hazards & Repair Drops (Stages 2 & 3 only)
            if game_state == STATE_PLAYING and current_sub_level in (2, 3):
                if random.random() < 0.008:
                    if current_sector_idx >= 2:
                        lx = random.randint(100, SCREEN_WIDTH - 100)
                        particle_manager.spawn_spark((lx, SCREEN_HEIGHT // 2), count=18, color=COLOR_CYAN)
                        if drone and abs(drone.pos.x - lx) < 60:
                            drone.take_damage(10)
                            audio_manager.play_hit()
                    else:
                        dx = random.randint(100, SCREEN_WIDTH - 100)
                        particle_manager.spawn_explosion((dx, 100), count=10, color=COLOR_GOLD)
                        if drone and abs(drone.pos.x - dx) < 50:
                            drone.take_damage(8)
                            audio_manager.play_hit()

            # Check Stage Clearing
            if game_state == STATE_PLAYING and wave_manager.is_stage_complete(level_score):
                game_state = STATE_LEVEL_CLEAR
                audio_manager.play_powerup()
                save_game_data(coins, highscore, upgrade_levels, unlocked_sectors, show_crt, unlocked_stages)

        # RENDER ENGINE
        canvas.fill(COLOR_BG)
        background.draw(canvas)

        if game_state == STATE_MENU:
            title_surf = font_title.render("DRONE HUNTER 2D", True, COLOR_CYAN)
            sub_surf = font_banner.render("ULTIMATE SCI-FI ARCADE EDITION [MOBILE]", True, COLOR_GOLD)
            canvas.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 260)))
            canvas.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 330)))
            draw_nav_buttons(canvas, mode="menu")
            draw_exit_button(canvas)

        elif game_state == STATE_SECTOR_SELECT:
            draw_sector_select_ui(canvas, unlocked_sectors, coins, difficulty_mode=difficulty_mode, unlocked_stages=unlocked_stages)

        elif game_state == STATE_HANGAR:
            cur_skin = drone.skin_theme if drone else 0
            draw_hangar_shop_ui(canvas, coins, current_sector_idx, upgrade_levels, drone_skin=cur_skin)
            draw_nav_buttons(canvas, mode="hangar")

        elif game_state == STATE_VICTORY:
            draw_campaign_victory_ui(canvas, total_score, highscore, coins)
            draw_nav_buttons(canvas, mode="victory")

        elif game_state in (STATE_PLAYING, STATE_PAUSED, STATE_LEVEL_CLEAR, STATE_GAME_OVER):
            target_group.draw(canvas)
            obstacle_group.draw(canvas)
            hazard_group.draw(canvas)
            bullet_group.draw(canvas)
            enemy_bullet_group.draw(canvas)
            powerup_group.draw(canvas)
            
            if drone:
                canvas.blit(drone.image, drone.rect)
                drone.draw_wingmen(canvas)

            particle_manager.draw(canvas)

            sec_info = SECTORS[current_sector_idx]
            draw_hud(canvas, drone, current_sector_idx, level_score, total_score, coins, DIFFICULTY_NAMES[difficulty_mode], combo_mult=combo_count, show_crt=show_crt, current_wave=cur_wave, sub_level=current_sub_level)
            draw_radar_minimap(canvas, drone, target_group, wingmen_group=drone.wingmen if drone else None)
            draw_crosshair(canvas)

            # Draw Boss Health Bar when in Boss Wave
            if cur_wave == 4:
                boss_targets = [t for t in target_group if getattr(t, "target_type", "") == "boss"]
                if boss_targets:
                    draw_boss_health_bar(canvas, boss_targets[0])

            if game_state == STATE_PLAYING:
                active_wpn3 = drone.active_weapon if drone else "pulse"
                tc = draw_virtual_touch_controls(canvas, dpad_state=dpad_state, active_weapon=active_wpn3, auto_fire_enabled=auto_fire_enabled)
                # Auto-fire touch toggle
                if pygame.mouse.get_just_pressed()[0] if hasattr(pygame.mouse, 'get_just_pressed') else False:
                    pass  # handled in event loop below

                # Draw combo banner
                draw_combo_banner(canvas, combo_count, combo_timer)

                # Red damage flash overlay
                if damage_flash_timer > 0:
                    flash_alpha = int(110 * (damage_flash_timer / 0.18))
                    flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                    flash_surf.fill((239, 68, 68, flash_alpha))
                    canvas.blit(flash_surf, (0, 0))

            elif game_state == STATE_PAUSED:
                draw_pause_settings_ui(canvas, difficulty_mode, show_crt, audio_manager.sound_enabled, is_diff_open=is_diff_dropdown_open)

            elif game_state == STATE_LEVEL_CLEAR:
                clear_surf = font_title.render(f"STAGE {current_sector_idx+1}-{current_sub_level} CLEARED!", True, COLOR_GOLD)
                canvas.blit(clear_surf, clear_surf.get_rect(center=(SCREEN_WIDTH // 2, 300)))
                draw_nav_buttons(canvas, mode="level_clear")

            elif game_state == STATE_GAME_OVER:
                draw_game_over_screen(canvas, total_score, highscore, current_sector_idx, current_sub_level)

        if show_crt:
            draw_crt_scanlines(canvas)

        if IS_ANDROID:
            scaled_canvas = pygame.transform.scale(canvas, screen.get_size())
        else:
            scaled_canvas = pygame.transform.scale(canvas, (win_w, win_h))
        screen.blit(scaled_canvas, (shake_offset_x, shake_offset_y))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        log_path = os.path.join(os.environ.get('ANDROID_PRIVATE_DIR', '.'), "crash_log_mobile.txt")
        try:
            with open(log_path, "w") as f:
                f.write(str(e) + "\n")
                traceback.print_exc(file=f)
        except Exception:
            pass
