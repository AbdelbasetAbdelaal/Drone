import os
import sys
import json
import math
import random

# Ensure current working directory is on sys.path for Android
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import pygame

# Android Environment Detection
IS_ANDROID = 'ANDROID_ARGUMENT' in os.environ or 'ANDROID_ROOT' in os.environ

if IS_ANDROID:
    save_dir = os.environ.get('ANDROID_PRIVATE_DIR', current_dir)
    SAVE_FILE = os.path.join(save_dir, "save_data.json")
else:
    SAVE_FILE = "save_data.json"

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
    draw_campaign_victory_ui, draw_pause_settings_ui, draw_virtual_touch_controls
)

def load_save_data():
    """Loads coins, highscore, upgrade levels, sector unlocks, and sub-level stage unlocks from save file."""
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
                return coins, highscore, upgrades, sectors, stages, show_crt
        except Exception:
            return 0, 0, default_upgrades, default_sectors, default_stages, False
    return 0, 0, default_upgrades, default_sectors, default_stages, False

def save_game_data(coins: int, highscore: int, upgrades: dict[str, int], sectors: list[bool], show_crt: bool = False, stages: list[bool] = None):
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
            "show_crt": show_crt
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def main():
    try:
        pygame.init()
    except Exception:
        pass

    try:
        pygame.font.init()
    except Exception:
        pass

    try:
        pygame.joystick.init()
    except Exception:
        pass

    joystick = None
    try:
        if pygame.joystick.get_init() and pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
    except Exception:
        pass

    win_w, win_h = 1280, 720
    is_fullscreen = False
    
    if IS_ANDROID:
        try:
            screen = pygame.display.set_mode((0, 0))
            win_w, win_h = screen.get_size()
        except Exception:
            screen = pygame.display.set_mode((1280, 720))
            win_w, win_h = 1280, 720
    else:
        screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
    pygame.display.set_caption(TITLE)
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
    coins, highscore, upgrade_levels, unlocked_sectors, unlocked_stages, show_crt = load_save_data()
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

    # Touch Controls State Variables for Android Mobile
    joystick_center = (140, 580)
    joystick_knob = (140, 580)
    is_touch_active = False
    touch_move_vector = pygame.Vector2(0, 0)
    touch_fire = False
    touch_aim_pos = (SCREEN_WIDTH - 200, SCREEN_HEIGHT // 2)

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
        drone.apply_shop_upgrades(upgrade_levels)
        player_group.add(drone)
        
        sec_info = SECTORS[current_sector_idx]
        stages = sec_info.get("stages", [])
        target_score = stages[current_sub_level - 1]["score"] if (0 < current_sub_level <= len(stages)) else sec_info.get("base_target_score", 6000)
        
        spawner = Spawner(base_min_interval=1.5, base_max_interval=3.0)
        spawner.set_level(current_sector_idx * 3 + current_sub_level, current_sector_idx)
        wave_manager = WaveManager(target_score)
        background.set_sector(current_sector_idx)

        # Auto-unlock High-Level Plasma Beam on Stage 2 and Stage 3!
        if current_sub_level >= 2 or upgrade_levels.get("beam", 0) > 0:
            if WEAPON_BEAM not in drone.available_weapons:
                drone.available_weapons.append(WEAPON_BEAM)

    def start_next_stage():
        nonlocal current_sector_idx, current_sub_level, level_score, game_state, combo_count, combo_timer, obstacle_timer, hazard_timer, difficulty_mode
        
        cur_flat_idx = current_sector_idx * 3 + (current_sub_level - 1)
        next_flat_idx = cur_flat_idx + 1

        if next_flat_idx < 15:
            unlocked_stages[next_flat_idx] = True
            next_sec = next_flat_idx // 3
            if next_sec < len(unlocked_sectors):
                unlocked_sectors[next_sec] = True
            
            save_game_data(coins, highscore, upgrade_levels, unlocked_sectors, show_crt, unlocked_stages)

            if current_sub_level < 3:
                current_sub_level += 1
            else:
                current_sector_idx += 1
                current_sub_level = 1
            
            reset_game()
            game_state = STATE_PLAYING
        else:
            game_state = STATE_VICTORY
            audio_manager.play_celebration_fanfare()
            particle_manager.spawn_celebration(SCREEN_WIDTH, SCREEN_HEIGHT)

    def execute_emp_blast():
        nonlocal level_score, total_score, highscore, coins
        if drone and drone.trigger_emp():
            audio_manager.play_emp()
            particle_manager.spawn_emp_ring(drone.pos)
            particle_manager.spawn_floating_text(drone.pos, "⚡ EMP BLAST!", COLOR_CYAN, 28)
            trigger_shake(9.0, 0.25)

            for target in list(target_group):
                particle_manager.spawn_explosion(target.rect.center, count=20, color=target.color_outer)
                destroyed = target.take_damage(99 if target.target_type != TARGET_TYPE_BOSS else 15)
                if destroyed:
                    target.kill()
                    pts = target.points
                    earned_coins = random.randint(5, 15) if target.target_type != TARGET_TYPE_BOSS else 75
                    coins += earned_coins
                    level_score += pts
                    total_score += pts
                    particle_manager.spawn_floating_text(target.rect.center, f"+{pts}  +${earned_coins}", COLOR_GOLD, 24)

            for obs in list(obstacle_group):
                obs.kill()
                particle_manager.spawn_explosion(obs.rect.center, count=25, color=(239, 68, 68))

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
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F2:
                    show_crt = not show_crt
                    save_game_data(coins, highscore, upgrade_levels, unlocked_sectors, show_crt, unlocked_stages)

                if event.key == pygame.K_q and game_state in (STATE_MENU, STATE_SECTOR_SELECT, STATE_HANGAR, STATE_VICTORY):
                    running = False

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
                        running = False

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
                    game_state = STATE_SECTOR_SELECT

                elif game_state == STATE_LEVEL_CLEAR:
                    start_next_stage()

                elif game_state == STATE_GAME_OVER:
                    reset_game()
                    game_state = STATE_PLAYING

                elif game_state == STATE_VICTORY:
                    difficulty_mode = DIFFICULTY_NIGHTMARE
                    current_sector_idx = 4
                    current_sub_level = 3
                    reset_game()
                    game_state = STATE_PLAYING

                elif game_state in (STATE_SECTOR_SELECT, STATE_HANGAR):
                    exit_rect = pygame.Rect(SCREEN_WIDTH - 140, SCREEN_HEIGHT - 55, 120, 40)
                    if exit_rect.collidepoint(mx, my):
                        running = False

                if game_state == STATE_SECTOR_SELECT:
                    diff_rect = pygame.Rect(480, 24, 220, 36)
                    if diff_rect.collidepoint(mx, my):
                        difficulty_mode = (difficulty_mode + 1) % 4

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
                    upg_keys = ["battery", "speed", "fire_rate", "emp_recharge", "wingman", "cloak", "missiles", "beam"]
                    h_start_x, h_start_y = 44, 95
                    h_card_w, h_card_h = 280, 115
                    for u_i, u_key in enumerate(upg_keys):
                        u_col = u_i % 4
                        u_row = u_i // 4
                        u_rect = pygame.Rect(h_start_x + u_col * 300, h_start_y + u_row * 130, h_card_w, h_card_h)
                        if u_rect.collidepoint(mx, my):
                            buy_upgrade(u_key)

                    h_map_btn = pygame.Rect(44, SCREEN_HEIGHT - 65, 200, 48)
                    h_start_btn = pygame.Rect(260, SCREEN_HEIGHT - 65, 300, 48)
                    if h_map_btn.collidepoint(mx, my):
                        game_state = STATE_SECTOR_SELECT
                    elif h_start_btn.collidepoint(mx, my):
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
                            running = False

                elif game_state == STATE_PLAYING:
                    touch_ctrls = draw_virtual_touch_controls(canvas, joystick_center, joystick_knob, is_touch_active)
                    if touch_ctrls["pause"].collidepoint(mx, my):
                        game_state = STATE_PAUSED
                    elif touch_ctrls["weapon"].collidepoint(mx, my):
                        if drone: drone.cycle_weapon()
                    elif touch_ctrls["emp"].collidepoint(mx, my):
                        execute_emp_blast()
                    elif touch_ctrls["roll"].collidepoint(mx, my):
                        execute_barrel_roll()
                    elif touch_ctrls["cloak"].collidepoint(mx, my):
                        execute_cloak()
                    elif touch_ctrls["fire"].collidepoint(mx, my):
                        touch_fire = True
                    elif mx < SCREEN_WIDTH // 2:
                        is_touch_active = True
                        joystick_knob = (mx, my)

            elif event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
                touch_fire = False
                is_touch_active = False
                joystick_knob = joystick_center

            elif event.type in (pygame.MOUSEMOTION, pygame.FINGERMOTION):
                if event.type == pygame.FINGERMOTION:
                    raw_p = (event.x * screen.get_width(), event.y * screen.get_height())
                else:
                    raw_p = pygame.mouse.get_pos()
                mx, my = get_canvas_pos(raw_p)
                touch_aim_pos = (mx, my)

                if is_touch_active and game_state == STATE_PLAYING:
                    if mx < SCREEN_WIDTH // 2:
                        joystick_knob = (mx, my)

        if game_state == STATE_PLAYING and drone:
            # Handle touch joystick movement on mobile
            if is_touch_active:
                jx, jy = joystick_center
                kx, ky = joystick_knob
                dx = kx - jx
                dy = ky - jy
                dist = math.hypot(dx, dy)
                if dist > 5:
                    nx = dx / max(dist, 65.0)
                    ny = dy / max(dist, 65.0)
                    drone.velocity.x += nx * drone.speed * 3.5 * dt
                    drone.velocity.y += ny * drone.speed * 3.5 * dt

            particle_manager.spawn_drone_trail((drone.pos.x - 22, drone.pos.y))
            wm_bullets = drone.update(dt, particle_manager, audio_manager, targets_group=target_group)
            for wb in wm_bullets:
                bullet_group.add(wb)

            mouse_pressed = pygame.mouse.get_pressed()
            should_shoot = touch_fire or mouse_pressed[0]
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
                        if obs.obstacle_type == "sea_mine":
                            particle_manager.spawn_water_splash(obs.rect.center, count=16)
                            particle_manager.spawn_floating_text(obs.rect.center, "💥 MINE BLAST!", COLOR_CRIMSON, 26)
                        elif obs.obstacle_type == "asteroid":
                            particle_manager.spawn_floating_text(obs.rect.center, "🪨 ASTEROID SHATTER!", COLOR_GOLD, 24)
                        else:
                            particle_manager.spawn_floating_text(obs.rect.center, "🔥 FIRE BLAST!", COLOR_OVERCLOCK, 24)
                        
                        for t in list(target_group):
                            if t.pos.distance_to(obs.pos) < 190.0:
                                t.take_damage(75)

            # Bullet vs Target Collisions
            for b in list(bullet_group):
                hit_targets = pygame.sprite.spritecollide(b, target_group, False, pygame.sprite.collide_circle)
                for t in hit_targets:
                    b.kill()
                    dmg = getattr(b, "damage", 35)
                    destroyed = t.take_damage(dmg)
                    particle_manager.spawn_floating_text(t.rect.center, f"-{dmg}", (250, 204, 21), 20)
                    
                    if destroyed:
                        t.kill()
                        audio_manager.play_explosion()
                        particle_manager.spawn_explosion(t.rect.center, count=25, color=t.color_outer)
                        
                        earned_coins = random.randint(5, 15) if t.target_type != TARGET_TYPE_BOSS else 125
                        pts = t.points * combo_count
                        level_score += pts
                        total_score += pts
                        coins += earned_coins
                        
                        combo_count = min(8, combo_count + 1)
                        combo_timer = 2.5
                        
                        particle_manager.spawn_floating_text(t.rect.center, f"+{pts}  +${earned_coins}", COLOR_GOLD, 24)

                        if random.random() < 0.30:
                            p_type = random.choice(["shield", "overclock", "slowmo", "coin", "battery"])
                            powerup_group.add(PowerupItem(pos=t.rect.center, ptype=p_type))

                        if level_score >= target_stg_score:
                            game_state = STATE_LEVEL_CLEAR
                            audio_manager.play_celebration_fanfare()
                            particle_manager.spawn_celebration(SCREEN_WIDTH, SCREEN_HEIGHT)

            # Hazard vs Player Collisions
            if not drone.is_cloaked and not drone.is_rolling:
                hit_hazards = pygame.sprite.spritecollide(drone, hazard_group, False)
                for haz in hit_hazards:
                    if isinstance(haz, LaserGridFence) and haz.is_active:
                        if drone.take_damage(35):
                            game_state = STATE_GAME_OVER
                            audio_manager.play_gameover()
                        else:
                            trigger_shake(8.0, 0.25)
                            particle_manager.spawn_floating_text(drone.pos, "⚡ LASER TRAP -35 HP!", COLOR_CRIMSON, 26)

                hit_eb = pygame.sprite.spritecollide(drone, enemy_bullet_group, True, pygame.sprite.collide_circle)
                for eb in hit_eb:
                    if drone.take_damage(20):
                        game_state = STATE_GAME_OVER
                        audio_manager.play_gameover()
                    else:
                        trigger_shake(5.0, 0.2)
                        particle_manager.spawn_floating_text(drone.pos, "-20 HP", COLOR_CRIMSON, 22)

                hit_obs = pygame.sprite.spritecollide(drone, obstacle_group, True, pygame.sprite.collide_circle)
                for obs in hit_obs:
                    audio_manager.play_mine_explosion()
                    trigger_shake(10.0, 0.35)
                    particle_manager.spawn_explosion(obs.rect.center, count=40, color=(239, 68, 68))
                    if drone.take_damage(40):
                        game_state = STATE_GAME_OVER
                        audio_manager.play_gameover()
                    else:
                        particle_manager.spawn_floating_text(drone.pos, "-40 HP OBSTACLE BLAST!", COLOR_CRIMSON, 26)

                hit_t = pygame.sprite.spritecollide(drone, target_group, False, pygame.sprite.collide_circle)
                for t in hit_t:
                    if t.target_type != TARGET_TYPE_BOSS:
                        t.kill()
                    if drone.take_damage(30):
                        game_state = STATE_GAME_OVER
                        audio_manager.play_gameover()
                    else:
                        trigger_shake(7.0, 0.25)
                        particle_manager.spawn_floating_text(drone.pos, "-30 HP IMPACT!", COLOR_CRIMSON, 24)

            # Powerups vs Player
            hit_pow = pygame.sprite.spritecollide(drone, powerup_group, True, pygame.sprite.collide_circle)
            for p in hit_pow:
                audio_manager.play_powerup()
                p_kind = getattr(p, "ptype", getattr(p, "type", "battery"))
                if p_kind == "shield":
                    drone.activate_shield(2)
                    particle_manager.spawn_floating_text(drone.pos, "🛡️ SHIELD UP!", COLOR_SHIELD, 24)
                elif p_kind == "overclock":
                    drone.activate_overclock(5.0)
                    particle_manager.spawn_floating_text(drone.pos, "⚡ OVERCLOCK!", COLOR_OVERCLOCK, 24)
                elif p_kind == "slowmo":
                    drone.activate_slowmo(6.0)
                    particle_manager.spawn_floating_text(drone.pos, "⏱️ TIME DILATION!", COLOR_SLOWMO, 24)
                elif p_kind == "coin":
                    coins += 25
                    particle_manager.spawn_floating_text(drone.pos, "+$25 GOLD", COLOR_COIN, 24)
                elif p_kind == "battery":
                    drone.recharge_battery(30)
                    particle_manager.spawn_floating_text(drone.pos, "🔋 BATTERY RECHARGE", COLOR_EMERALD, 24)

            if total_score > highscore:
                highscore = total_score
            save_game_data(coins, highscore, upgrade_levels, unlocked_sectors, show_crt, unlocked_stages)

        # ---------------- RENDER ----------------
        canvas.fill(COLOR_BG)
        background.draw(canvas)

        if game_state == STATE_MENU:
            title_surf = font_title.render("DRONE HUNTER 2D", True, COLOR_CYAN)
            sub_surf = font_banner.render("ULTIMATE SCI-FI ARCADE EDITION", True, COLOR_GOLD)
            start_surf = font_hud.render("PRESS [SPACE] TO ENTER SECTOR MAP  |  [Q] EXIT", True, COLOR_HUD)
            canvas.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 260)))
            canvas.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 330)))
            canvas.blit(start_surf, start_surf.get_rect(center=(SCREEN_WIDTH // 2, 440)))
            draw_exit_button(canvas)

        elif game_state == STATE_SECTOR_SELECT:
            draw_sector_select_ui(canvas, unlocked_sectors, coins, difficulty_mode=difficulty_mode, unlocked_stages=unlocked_stages)

        elif game_state == STATE_HANGAR:
            draw_hangar_shop_ui(canvas, coins, current_sector_idx, upgrade_levels)

        elif game_state == STATE_VICTORY:
            draw_campaign_victory_ui(canvas, total_score, highscore, coins)

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

            if game_state == STATE_PLAYING:
                draw_virtual_touch_controls(canvas, joystick_center, joystick_knob, is_touch_active)

            elif game_state == STATE_PAUSED:
                draw_pause_settings_ui(canvas, difficulty_mode, show_crt, audio_manager.sound_enabled, is_diff_open=is_diff_dropdown_open)

            elif game_state == STATE_LEVEL_CLEAR:
                clear_surf = font_title.render(f"STAGE {current_sector_idx+1}-{current_sub_level} CLEARED!", True, COLOR_GOLD)
                sub_surf = font_hud.render("Press [SPACE] to Launch Next Stage", True, COLOR_CYAN)
                canvas.blit(clear_surf, clear_surf.get_rect(center=(SCREEN_WIDTH // 2, 300)))
                canvas.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 370)))

            elif game_state == STATE_GAME_OVER:
                go_surf = font_gameover.render("MISSION FAILED", True, COLOR_CRIMSON)
                score_surf = font_banner.render(f"FINAL SCORE: {total_score}  |  HIGHSCORE: {highscore}", True, COLOR_GOLD)
                sub_surf = font_hud.render("Press [SPACE] to Restart Mission", True, COLOR_HUD)
                canvas.blit(go_surf, go_surf.get_rect(center=(SCREEN_WIDTH // 2, 280)))
                canvas.blit(score_surf, score_surf.get_rect(center=(SCREEN_WIDTH // 2, 350)))
                canvas.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 420)))

        if show_crt:
            draw_crt_scanlines(canvas)

        if IS_ANDROID:
            scaled_canvas = pygame.transform.scale(canvas, screen.get_size())
        else:
            scaled_canvas = pygame.transform.smoothscale(canvas, (win_w, win_h))
        screen.blit(scaled_canvas, (shake_offset_x, shake_offset_y))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        log_path = os.path.join(os.environ.get('ANDROID_PRIVATE_DIR', '.'), "crash_log.txt")
        try:
            with open(log_path, "w") as f:
                f.write(str(e) + "\n")
                traceback.print_exc(file=f)
        except Exception:
            pass
