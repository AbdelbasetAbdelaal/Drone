import pygame
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_HUD, COLOR_CYAN, COLOR_GOLD,
    COLOR_CRIMSON, COLOR_EMERALD, COLOR_SHIELD, COLOR_OVERCLOCK,
    COLOR_SLOWMO, COLOR_BEAM, COLOR_MISSILE, COLOR_PURPLE, COLOR_COIN,
    COLOR_TEXT_DIM, SECTORS, WEAPON_DEFS, UPGRADES, COLOR_MAGENTA, COLOR_WHITE
)

_font_cache = {}

def safe_create_font(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    """Safe font creation with fallback for Android mobile compatibility."""
    cache_key = (name, size, bold)
    if cache_key in _font_cache:
        return _font_cache[cache_key]
    
    try:
        if not pygame.font.get_init():
            pygame.font.init()
    except Exception:
        pass

    font_obj = None
    try:
        font_obj = pygame.font.Font(None, size)
    except Exception:
        try:
            font_obj = pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            font_obj = None
    
    _font_cache[cache_key] = font_obj
    return font_obj

# Global lazy font accessors
class LazyFont:
    def __init__(self, name: str, font_size: int, bold: bool = False):
        self.name = name
        self.font_size = font_size
        self.bold = bold

    def render(self, *args, **kwargs):
        f = safe_create_font(self.name, self.font_size, self.bold)
        if f:
            return f.render(*args, **kwargs)
        surf = pygame.Surface((10, 10))
        return surf

    def size(self, text: str):
        f = safe_create_font(self.name, self.font_size, self.bold)
        if f:
            return f.size(text)
        return (len(text) * 8, 16)

    def size_text(self, text: str):
        return self.size(text)

font_title = LazyFont("Impact", 44)
font_banner = LazyFont("Verdana", 17, bold=True)
font_hud = LazyFont("Consolas", 15, bold=True)
font_card = LazyFont("Consolas", 13, bold=True)
font_small = LazyFont("Arial", 12)

def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Wraps text into multiple lines fitting within max_width."""
    words = text.split(" ")
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def draw_hud(canvas: pygame.Surface, player, sector_idx: int, level_score: int, total_score: int, coins: int, difficulty_name: str, combo_mult: int = 1, show_crt: bool = False, current_wave: int = 1, sub_level: int = 1):
    """Renders main top HUD bar with Sub-Level Stage, Wave status, and zero text overlaps."""
    bar_w = SCREEN_WIDTH - 215
    bar_rect = pygame.Rect(10, 10, bar_w, 75)
    pygame.draw.rect(canvas, (15, 23, 42, 230), bar_rect, border_radius=8)
    pygame.draw.rect(canvas, (56, 189, 248, 140), bar_rect, 2, border_radius=8)

    sec_info = SECTORS[sector_idx] if sector_idx < len(SECTORS) else SECTORS[0]
    stages = sec_info.get("stages", [])
    target_stg_score = stages[sub_level - 1]["score"] if (0 < sub_level <= len(stages)) else sec_info.get("base_target_score", 6000)

    txt_sector = font_hud.render(f"SEC {sector_idx+1}-{sub_level}: {sec_info['name'].upper()}", True, COLOR_GOLD)
    txt_score = font_hud.render(f"SCORE: {total_score} ({level_score}/{target_stg_score})", True, COLOR_HUD)
    txt_coins = font_hud.render(f"GOLD: ${coins}", True, COLOR_GOLD)
    txt_diff = font_hud.render(f"MODE: {difficulty_name}", True, COLOR_CYAN)
    txt_wave = font_hud.render(f"WAVE {current_wave}/4", True, COLOR_CRIMSON if current_wave == 4 else COLOR_EMERALD)

    canvas.blit(txt_sector, (20, 18))
    canvas.blit(txt_score, (360, 18))
    canvas.blit(txt_coins, (660, 18))
    canvas.blit(txt_diff, (770, 18))
    canvas.blit(txt_wave, (920, 18))

    # Health / Battery Gauge
    hp_pct = max(0.0, min(1.0, player.health / player.max_health))
    hp_bar_rect = pygame.Rect(20, 44, 130, 20)
    pygame.draw.rect(canvas, (30, 41, 59), hp_bar_rect, border_radius=4)
    if hp_pct > 0:
        fill_w = int(130 * hp_pct)
        hp_color = COLOR_EMERALD if hp_pct > 0.5 else (COLOR_OVERCLOCK if hp_pct > 0.25 else COLOR_CRIMSON)
        pygame.draw.rect(canvas, hp_color, (20, 44, fill_w, 20), border_radius=4)
    pygame.draw.rect(canvas, COLOR_HUD, hp_bar_rect, 1, border_radius=4)

    txt_hp = font_hud.render(f"BATTERY {int(hp_pct * 100)}%", True, COLOR_HUD)
    canvas.blit(txt_hp, (28, 46))

    # Status Badges (Shield / Overclock / Cloak)
    active_weapon_def = WEAPON_DEFS.get(player.active_weapon, {})
    w_name = active_weapon_def.get("name", "Pulse")
    txt_weapon = font_hud.render(f"[{player.current_weapon_idx+1}] {w_name} [TAB]", True, COLOR_GOLD)
    canvas.blit(txt_weapon, (165, 46))

    emp_pct = max(0.0, min(1.0, 1.0 - (player.emp_cooldown / player.emp_cooldown_max)))
    emp_color = COLOR_CYAN if emp_pct >= 1.0 else COLOR_TEXT_DIM
    txt_emp = font_hud.render(f"EMP [E] {'READY' if emp_pct >= 1.0 else f'{int(emp_pct*100)}%'}", True, emp_color)
    canvas.blit(txt_emp, (360, 46))

    roll_color = COLOR_OVERCLOCK if player.roll_cooldown <= 0.0 else COLOR_TEXT_DIM
    txt_roll = font_hud.render("ROLL [SHIFT]", True, roll_color)
    canvas.blit(txt_roll, (520, 46))

    cloak_color = COLOR_CYAN if (player.has_cloak_upgrade and player.cloak_cooldown <= 0.0) else COLOR_TEXT_DIM
    txt_cloak = font_hud.render("CLOAK [K]", True, cloak_color)
    canvas.blit(txt_cloak, (660, 46))

    if combo_mult > 1:
        txt_combo = font_hud.render(f"{combo_mult}x COMBO!", True, COLOR_OVERCLOCK)
        canvas.blit(txt_combo, (770, 46))


def draw_radar_minimap(canvas: pygame.Surface, player, targets_group, wingmen_group=None):
    radar_w, radar_h = 180, 75
    radar_rect = pygame.Rect(SCREEN_WIDTH - 190, 10, radar_w, radar_h)
    
    pygame.draw.rect(canvas, (15, 23, 42, 230), radar_rect, border_radius=8)
    pygame.draw.rect(canvas, COLOR_CYAN, radar_rect, 2, border_radius=8)
    
    pygame.draw.line(canvas, (30, 41, 59), (radar_rect.centerx, radar_rect.top), (radar_rect.centerx, radar_rect.bottom), 1)
    pygame.draw.line(canvas, (30, 41, 59), (radar_rect.left, radar_rect.centery), (radar_rect.right, radar_rect.centery), 1)
    
    txt_r = font_hud.render("RADAR", True, COLOR_CYAN)
    canvas.blit(txt_r, (radar_rect.left + 8, radar_rect.top + 4))

    if not player or not player.alive:
        return

    def to_radar_pos(world_pos: tuple[float, float]) -> tuple[int, int]:
        rx = radar_rect.left + int((world_pos[0] / SCREEN_WIDTH) * radar_w)
        ry = radar_rect.top + int((world_pos[1] / SCREEN_HEIGHT) * radar_h)
        return (max(radar_rect.left + 2, min(radar_rect.right - 2, rx)),
                max(radar_rect.top + 2, min(radar_rect.bottom - 2, ry)))

    px, py = to_radar_pos(player.pos)
    pygame.draw.circle(canvas, COLOR_CYAN, (px, py), 3)

    if wingmen_group:
        for wm in wingmen_group:
            wx, wy = to_radar_pos(wm.pos)
            pygame.draw.circle(canvas, COLOR_EMERALD, (wx, wy), 2)

    for target in targets_group:
        tx, ty = to_radar_pos(target.pos)
        t_col = COLOR_GOLD if target.target_type == "boss" else (COLOR_MAGENTA if target.target_type == "fast" else COLOR_CRIMSON)
        pygame.draw.circle(canvas, t_col, (tx, ty), 3 if target.target_type == "boss" else 2)


def draw_crt_scanlines(canvas: pygame.Surface):
    scanline_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for y in range(0, SCREEN_HEIGHT, 4):
        pygame.draw.line(scanline_surf, (0, 0, 0, 35), (0, y), (SCREEN_WIDTH, y), 1)
    canvas.blit(scanline_surf, (0, 0))


def draw_crosshair(canvas: pygame.Surface):
    mx, my = pygame.mouse.get_pos()
    pygame.draw.circle(canvas, COLOR_CYAN, (mx, my), 14, 2)
    pygame.draw.circle(canvas, COLOR_GOLD, (mx, my), 3)
    pygame.draw.line(canvas, COLOR_CYAN, (mx - 18, my), (mx - 6, my), 2)
    pygame.draw.line(canvas, COLOR_CYAN, (mx + 6, my), (mx + 18, my), 2)
    pygame.draw.line(canvas, COLOR_CYAN, (mx, my - 18), (mx, my - 6), 2)
    pygame.draw.line(canvas, COLOR_CYAN, (mx, my + 6), (mx, my + 18), 2)


def draw_exit_button(canvas: pygame.Surface) -> pygame.Rect:
    exit_rect = pygame.Rect(SCREEN_WIDTH - 140, SCREEN_HEIGHT - 55, 120, 40)
    mx, my = pygame.mouse.get_pos()
    is_hover = exit_rect.collidepoint(mx, my)

    bg_col = (255, 60, 60) if is_hover else (239, 68, 68)
    b_width = 3 if is_hover else 2

    pygame.draw.rect(canvas, bg_col, exit_rect, border_radius=6)
    pygame.draw.rect(canvas, COLOR_WHITE if is_hover else COLOR_HUD, exit_rect, b_width, border_radius=6)
    txt_exit = font_banner.render("EXIT", True, (255, 255, 255))
    canvas.blit(txt_exit, txt_exit.get_rect(center=exit_rect.center))
    return exit_rect


def draw_sector_select_ui(canvas: pygame.Surface, unlocked_sectors: list[bool], coins: int, difficulty_mode: int = 1, unlocked_stages: list[bool] = None) -> tuple[list[pygame.Rect], pygame.Rect, pygame.Rect]:
    """Renders Ultra-Clean 5-Sector Campaign Grid Side-By-Side with Progressive Stage Locking."""
    canvas.fill((10, 15, 26))
    
    if unlocked_stages is None:
        unlocked_stages = [True] + [False] * 14

    hdr_rect = pygame.Rect(30, 15, SCREEN_WIDTH - 60, 55)
    pygame.draw.rect(canvas, (15, 23, 42), hdr_rect, border_radius=8)
    pygame.draw.rect(canvas, COLOR_CYAN, hdr_rect, 2, border_radius=8)
    
    txt_hdr = font_title.render("SECTOR CAMPAIGN MAP", True, COLOR_CYAN)
    
    # Difficulty Selector Button
    diff_names = ["EASY (LOW)", "NORMAL (BALANCED)", "HARD (INTENSE)", "NIGHTMARE (EXTREME)"]
    diff_colors = [COLOR_EMERALD, COLOR_CYAN, COLOR_OVERCLOCK, COLOR_CRIMSON]
    diff_rect = pygame.Rect(480, 24, 250, 36)
    
    mx, my = pygame.mouse.get_pos()
    is_diff_h = diff_rect.collidepoint(mx, my)
    
    pygame.draw.rect(canvas, (45, 60, 95) if is_diff_h else (30, 41, 59), diff_rect, border_radius=6)
    pygame.draw.rect(canvas, COLOR_WHITE if is_diff_h else diff_colors[difficulty_mode], diff_rect, 3 if is_diff_h else 2, border_radius=6)
    txt_diff_btn = font_hud.render(f"[D] {diff_names[difficulty_mode]}", True, COLOR_WHITE if is_diff_h else diff_colors[difficulty_mode])
    canvas.blit(txt_diff_btn, txt_diff_btn.get_rect(center=diff_rect.center))

    txt_coins = font_banner.render(f"GOLD SCRAP: ${coins}", True, COLOR_GOLD)
    canvas.blit(txt_hdr, (45, 22))
    canvas.blit(txt_coins, (SCREEN_WIDTH - 260, 30))

    card_rects = []
    card_w = 226
    card_h = 530
    start_x = 44
    gap = 18

    sector_colors = [COLOR_CYAN, COLOR_OVERCLOCK, COLOR_PURPLE, (14, 116, 144), COLOR_GOLD]
    difficulty_stars = ["*     ", "**    ", "***   ", "****  ", "***** "]

    for idx, sec in enumerate(SECTORS):
        cx = start_x + idx * (card_w + gap)
        cy = 85
        card_rect = pygame.Rect(cx, cy, card_w, card_h)
        card_rects.append(card_rect)
        
        is_unlocked = unlocked_sectors[idx] if idx < len(unlocked_sectors) else (idx == 0)
        is_hovered = is_unlocked and card_rect.collidepoint(mx, my)

        bg_col = (20, 30, 52, 240) if is_hovered else ((15, 23, 42, 240) if is_unlocked else (24, 32, 48, 180))
        border_col = sector_colors[idx] if is_hovered else (sector_colors[idx] if is_unlocked else COLOR_TEXT_DIM)
        border_width = 3 if is_hovered else (2 if is_unlocked else 1)

        pygame.draw.rect(canvas, bg_col, card_rect, border_radius=10)
        pygame.draw.rect(canvas, border_col, card_rect, border_width, border_radius=10)

        title_txt = font_banner.render(f"SEC {idx+1}", True, border_col)
        canvas.blit(title_txt, (cx + 14, cy + 14))

        name_lines = wrap_text(sec['name'], font_banner, card_w - 28)
        for n_i, line in enumerate(name_lines):
            canvas.blit(font_banner.render(line, True, COLOR_HUD if is_unlocked else COLOR_TEXT_DIM), (cx + 14, cy + 40 + n_i * 20))

        bar_y = cy + 85
        pygame.draw.rect(canvas, border_col if is_unlocked else (50, 60, 75), (cx + 14, bar_y, card_w - 28, 4), border_radius=2)

        star_txt = font_card.render(f"DIFF: {difficulty_stars[idx]}", True, COLOR_GOLD if is_unlocked else COLOR_TEXT_DIM)
        canvas.blit(star_txt, (cx + 14, bar_y + 12))

        desc_y = bar_y + 36
        wrapped_desc = wrap_text(sec['description'], font_small, card_w - 28)
        for line_i, line_text in enumerate(wrapped_desc):
            t_surf = font_small.render(line_text, True, COLOR_HUD if is_unlocked else COLOR_TEXT_DIM)
            canvas.blit(t_surf, (cx + 14, desc_y + line_i * 18))

        # 6. Render 3 Progressive Sub-Level Stage Selector Buttons
        stage_buttons = []
        stages = sec.get("stages", [])
        stage_y_start = cy + 345
        
        for stg_i, stg in enumerate(stages):
            stg_rect = pygame.Rect(cx + 10, stage_y_start + stg_i * 38, card_w - 20, 34)
            stage_buttons.append(stg_rect)
            
            flat_stg_idx = idx * 3 + stg_i
            stg_unlocked = unlocked_stages[flat_stg_idx] if flat_stg_idx < len(unlocked_stages) else (flat_stg_idx == 0)
            stg_hovered = stg_unlocked and stg_rect.collidepoint(mx, my)
            
            if stg_unlocked:
                stg_bg = (56, 189, 248) if stg_hovered else (30, 41, 59)
                stg_text_col = (15, 23, 42) if stg_hovered else (COLOR_GOLD if stg_i == 2 else COLOR_HUD)
                pygame.draw.rect(canvas, stg_bg, stg_rect, border_radius=5)
                pygame.draw.rect(canvas, COLOR_WHITE if stg_hovered else border_col, stg_rect, 2 if stg_hovered else 1, border_radius=5)
                lbl = font_card.render(f"[>] STAGE {idx+1}-{stg_i+1} ({stg['score']} PTS)", True, stg_text_col)
                canvas.blit(lbl, (cx + 14, stage_y_start + stg_i * 38 + 8))
            else:
                pygame.draw.rect(canvas, (24, 32, 48), stg_rect, border_radius=5)
                pygame.draw.rect(canvas, (50, 60, 75), stg_rect, 1, border_radius=5)
                lbl = font_card.render(f"[LOCKED] STAGE {idx+1}-{stg_i+1}", True, COLOR_TEXT_DIM)
                canvas.blit(lbl, (cx + 14, stage_y_start + stg_i * 38 + 8))

        # 7. Sector Launch Action Prompt
        btn_y = cy + 472
        btn_rect = pygame.Rect(cx + 10, btn_y, card_w - 20, 44)
        if is_unlocked:
            b_bg = COLOR_EMERALD if is_hovered else (30, 41, 59)
            b_text_col = (15, 23, 42) if is_hovered else COLOR_EMERALD
            pygame.draw.rect(canvas, b_bg, btn_rect, border_radius=6)
            pygame.draw.rect(canvas, COLOR_WHITE if is_hovered else COLOR_EMERALD, btn_rect, 3 if is_hovered else 2, border_radius=6)
            b_label = font_banner.render(f"LAUNCH SEC {idx+1}", True, b_text_col)
            canvas.blit(b_label, b_label.get_rect(center=btn_rect.center))
        else:
            pygame.draw.rect(canvas, (30, 41, 59), btn_rect, border_radius=6)
            pygame.draw.rect(canvas, COLOR_CRIMSON, btn_rect, 1, border_radius=6)
            b_label = font_banner.render("SECTOR LOCKED", True, COLOR_CRIMSON)
            canvas.blit(b_label, b_label.get_rect(center=btn_rect.center))

    btn_ret = font_hud.render("Click Sector Card to Launch  |  [D] Toggle Difficulty Mode  |  [SPACE] Hangar  |  [Q] Exit", True, COLOR_HUD)
    canvas.blit(btn_ret, btn_ret.get_rect(center=(SCREEN_WIDTH // 2, 680)))

    exit_btn_rect = draw_exit_button(canvas)
    return card_rects, exit_btn_rect, diff_rect


def draw_hangar_shop_ui(canvas: pygame.Surface, coins: int, current_sector: int, upgrade_levels: dict[str, int]) -> pygame.Rect:
    canvas.fill((10, 15, 26))

    header_rect = pygame.Rect(30, 20, SCREEN_WIDTH - 60, 60)
    pygame.draw.rect(canvas, (15, 23, 42), header_rect, border_radius=6)
    pygame.draw.rect(canvas, COLOR_CYAN, header_rect, 2, border_radius=6)
    
    t_hdr = font_title.render("DRONE HANGAR & WEAPONS BAY", True, COLOR_CYAN)
    coin_hdr = font_banner.render(f"GOLD SCRAP: ${coins}", True, COLOR_GOLD)
    canvas.blit(t_hdr, (50, 28))
    canvas.blit(coin_hdr, (SCREEN_WIDTH - 320, 36))

    items = [
        ("1", "battery", "Max Battery Capacity", COLOR_EMERALD),
        ("2", "speed", "Thruster Agility", COLOR_CYAN),
        ("3", "fire_rate", "Cannon Fire-Rate", COLOR_GOLD),
        ("4", "emp_recharge", "EMP Shockwave Charger", COLOR_PURPLE),
        ("5", "wingman", "Wingman Support Minidrones", COLOR_EMERALD),
        ("6", "cloak", "Tactical Cloaking Unit", COLOR_CYAN),
        ("7", "missiles", "Homing Missile Ordnance", COLOR_MISSILE),
        ("8", "beam", "Thermal Laser Beam Cannon", COLOR_BEAM)
    ]

    card_w, card_h = 560, 110
    mx, my = pygame.mouse.get_pos()

    for idx, (key_num, upg_id, upg_name, color) in enumerate(items):
        col_idx = idx % 2
        row_idx = idx // 2
        
        cx = 40 + col_idx * 600
        cy = 95 + row_idx * 125
        
        upg_def = UPGRADES.get(upg_id, {})
        lvl = upgrade_levels.get(upg_id, 0)
        max_lvl = upg_def.get("max_lvl", 5)
        base_cost = upg_def.get("base_cost", 50)
        cost_mult = upg_def.get("cost_mult", 1.5)
        cost = int(base_cost * (cost_mult ** lvl))

        card_rect = pygame.Rect(cx, cy, card_w, card_h)
        is_hover = card_rect.collidepoint(mx, my)

        bg_col = (20, 30, 52, 240) if is_hover else (15, 23, 42, 240)
        pygame.draw.rect(canvas, bg_col, card_rect, border_radius=8)
        pygame.draw.rect(canvas, COLOR_WHITE if is_hover else color, card_rect, 3 if is_hover else 2, border_radius=8)

        lbl = font_banner.render(f"[{key_num}] {upg_name}", True, COLOR_WHITE if is_hover else color)
        canvas.blit(lbl, (cx + 20, cy + 15))

        if lvl >= max_lvl:
            txt_lvl = font_card.render(f"LEVEL {lvl}/{max_lvl} - MAX LEVEL", True, COLOR_EMERALD)
        else:
            txt_lvl = font_card.render(f"LEVEL {lvl}/{max_lvl} - Upgrade Cost: ${cost}", True, COLOR_HUD)
        canvas.blit(txt_lvl, (cx + 20, cy + 45))

        pygame.draw.rect(canvas, (30, 41, 59), (cx + 20, cy + 72, 500, 12), border_radius=3)
        fill_w = int(500 * (lvl / max_lvl))
        if fill_w > 0:
            pygame.draw.rect(canvas, color, (cx + 20, cy + 72, fill_w, 12), border_radius=3)

    btn_launch = font_banner.render("Press [M] for Sector Map  |  [SPACE] Launch Mission", True, COLOR_EMERALD)
    canvas.blit(btn_launch, btn_launch.get_rect(center=(SCREEN_WIDTH // 2, 650)))

    exit_btn_rect = draw_exit_button(canvas)
    return exit_btn_rect


def draw_campaign_victory_ui(canvas: pygame.Surface, total_score: int, highscore: int, coins: int):
    """Renders Grand Campaign Victory Champion Screen with Trophy & Statistics."""
    canvas.fill((10, 15, 26))
    
    card_rect = pygame.Rect(140, 80, SCREEN_WIDTH - 280, 560)
    pygame.draw.rect(canvas, (15, 23, 42, 245), card_rect, border_radius=16)
    pygame.draw.rect(canvas, COLOR_GOLD, card_rect, 3, border_radius=16)

    t1 = font_title.render("GRAND CAMPAIGN VICTORY!", True, COLOR_GOLD)
    t2 = font_banner.render("CONGRATULATIONS AGENT! ALL 5 SECTORS CLEARED!", True, COLOR_CYAN)
    
    canvas.blit(t1, t1.get_rect(center=(SCREEN_WIDTH // 2, 140)))
    canvas.blit(t2, t2.get_rect(center=(SCREEN_WIDTH // 2, 200)))

    trophy_txt = font_title.render("ULTIMATE DRONE HUNTER CHAMPION", True, COLOR_EMERALD)
    canvas.blit(trophy_txt, trophy_txt.get_rect(center=(SCREEN_WIDTH // 2, 270)))

    stat_rect = pygame.Rect(260, 330, SCREEN_WIDTH - 520, 190)
    pygame.draw.rect(canvas, (30, 41, 59), stat_rect, border_radius=10)
    pygame.draw.rect(canvas, COLOR_CYAN, stat_rect, 2, border_radius=10)

    s1 = font_banner.render(f"FINAL CAMPAIGN SCORE: {total_score:,} PTS", True, COLOR_GOLD)
    s2 = font_banner.render(f"ALL-TIME HIGHSCORE:   {highscore:,} PTS", True, COLOR_HUD)
    s3 = font_banner.render(f"TOTAL GOLD SCRAP:     ${coins:,}", True, COLOR_EMERALD)
    s4 = font_banner.render(f"CAMPAIGN STAGES CLEARED: 15 / 15 STAGES", True, COLOR_CYAN)

    canvas.blit(s1, (290, 350))
    canvas.blit(s2, (290, 390))
    canvas.blit(s3, (290, 430))
    canvas.blit(s4, (290, 470))

    p1 = font_banner.render("Press [SPACE] to Launch Endless Nightmare Survival Mode", True, COLOR_OVERCLOCK)
    p2 = font_hud.render("Press [M] Sector Map  |  [H] Hangar Shop  |  [Q] Exit Game", True, COLOR_HUD)
    canvas.blit(p1, p1.get_rect(center=(SCREEN_WIDTH // 2, 570)))
    canvas.blit(p2, p2.get_rect(center=(SCREEN_WIDTH // 2, 610)))

    draw_exit_button(canvas)


def draw_pause_settings_ui(canvas: pygame.Surface, difficulty_mode: int, show_crt: bool, sound_enabled: bool, is_diff_open: bool = False) -> dict[str, any]:
    """Renders Clean High-Tech Pause & Settings Control Panel with Mouse Hover Color Highlighting."""
    mx, my = pygame.mouse.get_pos()
    
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((15, 23, 42, 215))
    canvas.blit(overlay, (0, 0))

    panel_h = 650 if not is_diff_open else 665
    panel_rect = pygame.Rect(180, 25, SCREEN_WIDTH - 360, panel_h)
    pygame.draw.rect(canvas, (15, 23, 42, 250), panel_rect, border_radius=14)
    pygame.draw.rect(canvas, COLOR_CYAN, panel_rect, 3, border_radius=14)

    txt_pause = font_title.render("PAUSED & SETTINGS", True, COLOR_GOLD)
    canvas.blit(txt_pause, txt_pause.get_rect(center=(SCREEN_WIDTH // 2, 65)))

    # --- SECTION 1: SETTINGS DROPDOWN / TOGGLE BUTTONS ---
    sub_sett = font_banner.render("[+] GAME OPTION SETTINGS", True, COLOR_CYAN)
    canvas.blit(sub_sett, (220, 105))

    diff_names = ["EASY (LOW HP & SPEED)", "NORMAL (BALANCED)", "HARD (INTENSE SALVOS)", "NIGHTMARE (BULLET HELL)"]
    diff_colors = [COLOR_EMERALD, COLOR_CYAN, COLOR_OVERCLOCK, COLOR_CRIMSON]
    
    btn_diff = pygame.Rect(220, 135, 480, 40)
    hover_diff = btn_diff.collidepoint(mx, my)
    bg_diff = (45, 60, 95) if hover_diff else (30, 41, 59)
    border_w_diff = 3 if hover_diff else 2

    pygame.draw.rect(canvas, bg_diff, btn_diff, border_radius=6)
    pygame.draw.rect(canvas, COLOR_WHITE if hover_diff else diff_colors[difficulty_mode], btn_diff, border_w_diff, border_radius=6)
    
    t_diff = font_hud.render(f"DIFFICULTY: {diff_names[difficulty_mode]}  [SELECT]", True, COLOR_WHITE if hover_diff else diff_colors[difficulty_mode])
    canvas.blit(t_diff, t_diff.get_rect(center=btn_diff.center))

    dropdown_item_rects = []
    if is_diff_open:
        for d_i in range(4):
            d_rect = pygame.Rect(220, 180 + d_i * 36, 480, 32)
            dropdown_item_rects.append((d_rect, d_i))
            
            h_item = d_rect.collidepoint(mx, my)
            d_bg = (56, 189, 248) if h_item else ((45, 60, 85) if d_i == difficulty_mode else (24, 32, 48))
            d_text_col = (15, 23, 42) if h_item else diff_colors[d_i]
            
            pygame.draw.rect(canvas, d_bg, d_rect, border_radius=5)
            pygame.draw.rect(canvas, COLOR_WHITE if h_item else diff_colors[d_i], d_rect, 2 if (d_i == difficulty_mode or h_item) else 1, border_radius=5)
            
            check_mark = "[X] " if d_i == difficulty_mode else "[  ] "
            t_item = font_hud.render(f"{check_mark}{diff_names[d_i]}", True, d_text_col)
            canvas.blit(t_item, (235, 180 + d_i * 36 + 6))

    offset_y = 145 if is_diff_open else 0

    btn_crt = pygame.Rect(220, 185 + offset_y, 480, 38)
    hover_crt = btn_crt.collidepoint(mx, my)
    bg_crt = (45, 60, 95) if hover_crt else (30, 41, 59)
    col_crt = COLOR_GOLD if show_crt else COLOR_TEXT_DIM
    
    pygame.draw.rect(canvas, bg_crt, btn_crt, border_radius=6)
    pygame.draw.rect(canvas, COLOR_WHITE if hover_crt else col_crt, btn_crt, 3 if hover_crt else 2, border_radius=6)
    t_crt = font_banner.render(f"CRT RETRO FILTER:  {'[ ENABLED ]' if show_crt else '[ DISABLED ]'}  (Click/[F2])", True, COLOR_WHITE if hover_crt else (COLOR_GOLD if show_crt else COLOR_HUD))
    canvas.blit(t_crt, t_crt.get_rect(center=btn_crt.center))

    btn_sfx = pygame.Rect(220, 230 + offset_y, 480, 38)
    hover_sfx = btn_sfx.collidepoint(mx, my)
    bg_sfx = (45, 60, 95) if hover_sfx else (30, 41, 59)
    col_sfx = COLOR_EMERALD if sound_enabled else COLOR_CRIMSON
    
    pygame.draw.rect(canvas, bg_sfx, btn_sfx, border_radius=6)
    pygame.draw.rect(canvas, COLOR_WHITE if hover_sfx else col_sfx, btn_sfx, 3 if hover_sfx else 2, border_radius=6)
    t_sfx = font_banner.render(f"SYNTH AUDIO SFX:  {'[ ENABLED ]' if sound_enabled else '[ MUTED ]'}  (Click/[S])", True, COLOR_WHITE if hover_sfx else col_sfx)
    canvas.blit(t_sfx, t_sfx.get_rect(center=btn_sfx.center))

    # --- SECTION 2: CONTROLS & KEYBINDINGS CHART ---
    sub_ctrl = font_banner.render("[>] PILOT CONTROLS & KEYBINDINGS", True, COLOR_CYAN)
    canvas.blit(sub_ctrl, (220, 280 + offset_y))

    ctrl_box = pygame.Rect(220, 305 + offset_y, 480, 155)
    pygame.draw.rect(canvas, (24, 32, 48), ctrl_box, border_radius=8)
    pygame.draw.rect(canvas, (56, 189, 248, 100), ctrl_box, 1, border_radius=8)

    controls_list = [
        ("FLIGHT MOVEMENT:", "W A S D / ARROW KEYS"),
        ("AIM & RETICLE:", "MOUSE POINTER"),
        ("CANNON FIRE:", "LEFT MOUSE BUTTON"),
        ("EMP SHOCKWAVE:", "RIGHT MOUSE / PRESS [E]"),
        ("CYCLE WEAPON:", "PRESS [TAB] KEY"),
        ("EVASIVE ROLL:", "PRESS [L-SHIFT] KEY"),
        ("TACTICAL CLOAK:", "PRESS [C] / [K] KEY")
    ]

    for c_i, (k_lbl, k_val) in enumerate(controls_list):
        c_y = 312 + offset_y + c_i * 20
        canvas.blit(font_hud.render(k_lbl, True, COLOR_HUD), (235, c_y))
        canvas.blit(font_hud.render(k_val, True, COLOR_GOLD), (440, c_y))

    # --- SECTION 3: NAVIGATION ACTION BUTTONS WITH VIBRANT HOVER COLORS ---
    btn_resume = pygame.Rect(220, 475 + offset_y, 230, 40)
    btn_hangar = pygame.Rect(470, 475 + offset_y, 230, 40)
    btn_map = pygame.Rect(220, 523 + offset_y, 230, 40)
    btn_exit = pygame.Rect(470, 523 + offset_y, 230, 40)

    h_res = btn_resume.collidepoint(mx, my)
    h_hang = btn_hangar.collidepoint(mx, my)
    h_map = btn_map.collidepoint(mx, my)
    h_ex = btn_exit.collidepoint(mx, my)

    # Resume Button Hover Style (Emerald -> Bright Mint Cyan)
    pygame.draw.rect(canvas, (52, 211, 153) if not h_res else (110, 231, 183), btn_resume, border_radius=6)
    pygame.draw.rect(canvas, COLOR_WHITE if h_res else COLOR_EMERALD, btn_resume, 3 if h_res else 1, border_radius=6)

    # Hangar Button Hover Style (Slate -> Cyan Glow)
    pygame.draw.rect(canvas, (56, 189, 248) if h_hang else (30, 41, 59), btn_hangar, border_radius=6)
    pygame.draw.rect(canvas, COLOR_WHITE if h_hang else COLOR_CYAN, btn_hangar, 3 if h_hang else 2, border_radius=6)

    # Map Button Hover Style (Slate -> Gold Glow)
    pygame.draw.rect(canvas, (250, 204, 21) if h_map else (30, 41, 59), btn_map, border_radius=6)
    pygame.draw.rect(canvas, COLOR_WHITE if h_map else COLOR_GOLD, btn_map, 3 if h_map else 2, border_radius=6)

    # Exit Button Hover Style (Red -> Neon Crimson Glow)
    pygame.draw.rect(canvas, (255, 60, 60) if h_ex else (239, 68, 68), btn_exit, border_radius=6)
    pygame.draw.rect(canvas, COLOR_WHITE if h_ex else (255, 200, 200), btn_exit, 3 if h_ex else 1, border_radius=6)

    t_res = font_banner.render("[>] RESUME [P]", True, (15, 23, 42))
    t_hang = font_banner.render("HANGAR SHOP [H]", True, (15, 23, 42) if h_hang else COLOR_CYAN)
    t_map = font_banner.render("SECTOR MAP [M]", True, (15, 23, 42) if h_map else COLOR_GOLD)
    t_ex = font_banner.render("EXIT GAME [Q]", True, (255, 255, 255))

    canvas.blit(t_res, t_res.get_rect(center=btn_resume.center))
    canvas.blit(t_hang, t_hang.get_rect(center=btn_hangar.center))
    canvas.blit(t_map, t_map.get_rect(center=btn_map.center))
    canvas.blit(t_ex, t_ex.get_rect(center=btn_exit.center))

    return {
        "diff": btn_diff,
        "dropdown_items": dropdown_item_rects,
        "crt": btn_crt,
        "sfx": btn_sfx,
        "resume": btn_resume,
        "hangar": btn_hangar,
        "map": btn_map,
        "exit": btn_exit
    }


def draw_virtual_touch_controls(canvas: pygame.Surface, joystick_center=(140, 580), joystick_pos=None, is_touch_active=False) -> dict[str, pygame.Rect]:
    """Renders high-tech translucent virtual touch controls for Android mobile touchscreens."""
    controls = {}
    
    # 1. Virtual Joystick Base (Left side)
    jx, jy = joystick_center
    pygame.draw.circle(canvas, (15, 23, 42), (jx, jy), 65)
    pygame.draw.circle(canvas, COLOR_CYAN, (jx, jy), 65, width=2)
    
    # Inner Knob
    knob_x, knob_y = joystick_pos if joystick_pos else (jx, jy)
    pygame.draw.circle(canvas, COLOR_CYAN if is_touch_active else COLOR_HUD, (knob_x, knob_y), 30)
    pygame.draw.circle(canvas, COLOR_WHITE, (knob_x, knob_y), 30, width=2)

    # 2. Action Buttons (Right side)
    # Fire Button
    btn_fire = pygame.Rect(SCREEN_WIDTH - 125, SCREEN_HEIGHT - 125, 95, 95)
    pygame.draw.ellipse(canvas, (239, 68, 68), btn_fire)
    pygame.draw.ellipse(canvas, COLOR_WHITE, btn_fire, width=3)
    lbl_fire = font_hud.render("FIRE", True, COLOR_WHITE)
    canvas.blit(lbl_fire, lbl_fire.get_rect(center=btn_fire.center))
    controls["fire"] = btn_fire

    # EMP Button
    btn_emp = pygame.Rect(SCREEN_WIDTH - 235, SCREEN_HEIGHT - 95, 75, 75)
    pygame.draw.ellipse(canvas, (56, 189, 248), btn_emp)
    pygame.draw.ellipse(canvas, COLOR_CYAN, btn_emp, width=2)
    lbl_emp = font_card.render("EMP", True, COLOR_WHITE)
    canvas.blit(lbl_emp, lbl_emp.get_rect(center=btn_emp.center))
    controls["emp"] = btn_emp

    # Roll Button
    btn_roll = pygame.Rect(SCREEN_WIDTH - 125, SCREEN_HEIGHT - 230, 75, 75)
    pygame.draw.ellipse(canvas, (52, 211, 153), btn_roll)
    pygame.draw.ellipse(canvas, COLOR_EMERALD, btn_roll, width=2)
    lbl_roll = font_card.render("ROLL", True, COLOR_WHITE)
    canvas.blit(lbl_roll, lbl_roll.get_rect(center=btn_roll.center))
    controls["roll"] = btn_roll

    # Cloak Button
    btn_cloak = pygame.Rect(SCREEN_WIDTH - 235, SCREEN_HEIGHT - 195, 75, 75)
    pygame.draw.ellipse(canvas, (217, 70, 239), btn_cloak)
    pygame.draw.ellipse(canvas, COLOR_MAGENTA, btn_cloak, width=2)
    lbl_cloak = font_card.render("CLOAK", True, COLOR_WHITE)
    canvas.blit(lbl_cloak, lbl_cloak.get_rect(center=btn_cloak.center))
    controls["cloak"] = btn_cloak

    # Weapon Cycle Button (Top Right)
    btn_weapon = pygame.Rect(SCREEN_WIDTH - 150, 15, 135, 42)
    pygame.draw.rect(canvas, (30, 41, 59), btn_weapon, border_radius=8)
    pygame.draw.rect(canvas, COLOR_GOLD, btn_weapon, 2, border_radius=8)
    lbl_wpn = font_card.render("WEAPON ⇄", True, COLOR_GOLD)
    canvas.blit(lbl_wpn, lbl_wpn.get_rect(center=btn_weapon.center))
    controls["weapon"] = btn_weapon

    # Pause Button (Top Left)
    btn_pause = pygame.Rect(15, 15, 50, 50)
    pygame.draw.rect(canvas, (30, 41, 59), btn_pause, border_radius=8)
    pygame.draw.rect(canvas, COLOR_CYAN, btn_pause, 2, border_radius=8)
    lbl_p = font_hud.render("PAUSE", True, COLOR_CYAN)
    canvas.blit(lbl_p, lbl_p.get_rect(center=btn_pause.center))
    controls["pause"] = btn_pause

    return controls

