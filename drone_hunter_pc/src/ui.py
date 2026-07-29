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

font_title = LazyFont("Impact", 48)
font_banner = LazyFont("Verdana", 20, bold=True)
font_hud = LazyFont("Consolas", 18, bold=True)
font_card = LazyFont("Consolas", 15, bold=True)
font_small = LazyFont("Arial", 14)

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


def draw_combo_banner(canvas: pygame.Surface, combo_count: int, combo_timer: float):
    """Renders glowing animated kill streak combo banner when combo > 1."""
    if combo_count <= 1 or combo_timer <= 0:
        return

    if combo_count >= 20:
        color = (236, 72, 153)
        tier_label = f"LEGENDARY x{combo_count}!"
    elif combo_count >= 10:
        color = (250, 204, 21)
        tier_label = f"OVERKILL x{combo_count}!"
    elif combo_count >= 5:
        color = (168, 85, 247)
        tier_label = f"RAMPAGE x{combo_count}!"
    elif combo_count >= 3:
        color = (56, 189, 248)
        tier_label = f"MULTI-KILL x{combo_count}!"
    else:
        color = (52, 211, 153)
        tier_label = f"DOUBLE KILL x{combo_count}!"

    fade_alpha = min(255, int(255 * min(1.0, combo_timer / 0.8)))
    pulse = 1.0 + 0.08 * abs((combo_timer % 0.4) - 0.2) / 0.2
    combo_font_size = int(34 * pulse)
    combo_font = safe_create_font("Impact", combo_font_size)
    if combo_font is None:
        return

    glow_surf = pygame.Surface((500, 60), pygame.SRCALPHA)
    glow_surf.fill((0, 0, 0, 0))
    glow_col = (*color[:3], max(0, fade_alpha // 3))
    pygame.draw.rect(glow_surf, glow_col, (0, 0, 500, 60), border_radius=12)
    canvas.blit(glow_surf, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 80))

    txt = combo_font.render(tier_label, True, color)
    txt.set_alpha(fade_alpha)
    canvas.blit(txt, txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 55)))

    sub_font = safe_create_font("Consolas", 18, bold=True)
    if sub_font:
        sub_txt = sub_font.render(f"x{combo_count} SCORE MULTIPLIER ACTIVE!", True, (255, 255, 255))
        sub_txt.set_alpha(max(0, fade_alpha - 60))
        canvas.blit(sub_txt, sub_txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 28)))


def draw_hud(canvas: pygame.Surface, player, sector_idx: int, level_score: int, total_score: int, coins: int, difficulty_name: str, combo_mult: int = 1, show_crt: bool = False, current_wave: int = 1, sub_level: int = 1):
    """Renders main top HUD bar — mobile-first, no keyboard hints, colored pill badges."""
    bar_x = 115
    bar_w = SCREEN_WIDTH - 310
    bar_rect = pygame.Rect(bar_x, 10, bar_w, 56)
    
    pygame.draw.rect(canvas, (15, 23, 42, 235), bar_rect, border_radius=8)
    pygame.draw.rect(canvas, (56, 189, 248, 140), bar_rect, 2, border_radius=8)

    sec_info = SECTORS[sector_idx] if sector_idx < len(SECTORS) else SECTORS[0]
    stages = sec_info.get("stages", [])
    target_stg_score = stages[sub_level - 1]["score"] if (0 < sub_level <= len(stages)) else sec_info.get("base_target_score", 6000)

    txt_sector = font_hud.render(f"SEC {sector_idx+1}-{sub_level}: {sec_info['name'].upper()}", True, COLOR_GOLD)
    txt_score = font_hud.render(f"SCORE: {total_score} ({level_score}/{target_stg_score})", True, COLOR_HUD)
    txt_coins = font_hud.render(f"GOLD: ${coins}", True, COLOR_GOLD)
    txt_diff = font_hud.render(f"MODE: {difficulty_name}", True, COLOR_CYAN)
    txt_wave = font_hud.render(f"WAVE {current_wave}/4", True, COLOR_CRIMSON if current_wave == 4 else COLOR_EMERALD)

    canvas.blit(txt_sector, (bar_x + 12, 14))
    canvas.blit(txt_score, (bar_x + 200, 14))
    canvas.blit(txt_coins, (bar_x + 420, 14))
    canvas.blit(txt_diff, (bar_x + 540, 14))
    canvas.blit(txt_wave, (bar_x + 670, 14))

    # Health / Battery Gauge
    hp_pct = max(0.0, min(1.0, player.health / player.max_health))
    hp_bar_rect = pygame.Rect(bar_x + 12, 34, 110, 16)
    pygame.draw.rect(canvas, (30, 41, 59), hp_bar_rect, border_radius=4)
    if hp_pct > 0:
        fill_w = int(110 * hp_pct)
        hp_color = COLOR_EMERALD if hp_pct > 0.5 else (COLOR_OVERCLOCK if hp_pct > 0.25 else COLOR_CRIMSON)
        pygame.draw.rect(canvas, hp_color, (bar_x + 12, 34, fill_w, 16), border_radius=4)
    pygame.draw.rect(canvas, COLOR_HUD, hp_bar_rect, 1, border_radius=4)

    txt_hp = font_card.render(f"BATTERY {int(hp_pct * 100)}%", True, COLOR_WHITE)
    canvas.blit(txt_hp, (bar_x + 18, 36))

    # --- Status Pill Badges (mobile: no keyboard hints, colored active/dim states) ---
    def _pill(x, label, value, active, active_col):
        """Draw a colored pill badge with a status dot and label."""
        w = 95
        r = pygame.Rect(x, 34, w, 16)
        bg = active_col if active else (30, 41, 59)
        pygame.draw.rect(canvas, bg, r, border_radius=4)
        pygame.draw.rect(canvas, active_col if active else (60, 75, 95), r, 1, border_radius=4)
        dot = (200, 255, 200) if active else (70, 85, 100)
        pygame.draw.circle(canvas, dot, (x + 6, 42), 3)
        txt = font_card.render(f"{label}: {value}", True, (15, 23, 42) if active else (110, 130, 155))
        canvas.blit(txt, (x + 13, 35))

    # Weapon pill
    active_weapon_def = WEAPON_DEFS.get(player.active_weapon, {})
    w_name = active_weapon_def.get("name", "Pulse")
    _pill(bar_x + 130, "WPN", w_name.upper()[:7], True, (220, 160, 10))

    # EMP pill
    emp_pct = max(0.0, min(1.0, 1.0 - (player.emp_cooldown / player.emp_cooldown_max)))
    emp_ready = emp_pct >= 1.0
    _pill(bar_x + 232, "EMP", "READY" if emp_ready else f"{int(emp_pct*100)}%", emp_ready, (14, 165, 233))

    # Roll pill
    roll_ready = player.roll_cooldown <= 0.0
    _pill(bar_x + 334, "ROLL", "READY" if roll_ready else "WAIT", roll_ready, (16, 185, 129))

    # Cloak pill
    cloak_avail = player.has_cloak_upgrade and player.cloak_cooldown <= 0.0
    _pill(bar_x + 436, "CLOAK", "READY" if cloak_avail else "N/A", cloak_avail, (168, 85, 247))

    # Ultimate Overdrive pill
    ult_ready = player.ultimate_charge >= 100.0
    _pill(bar_x + 538, "ULT", "100%" if ult_ready else f"{int(player.ultimate_charge)}%", ult_ready, (250, 204, 21))

    # Advanced Stage Weather Hazard Banner (Stages 2 & 3 only)
    if sub_level in (2, 3):
        haz_name = "🌩️ ELECTROMAGNETIC STORM" if sector_idx >= 2 else "☄️ DEBRIS SHOWER"
        txt_haz = font_card.render(f"ADVANCED HAZARD: {haz_name}", True, COLOR_OVERCLOCK)
        canvas.blit(txt_haz, (bar_x + 640, 36))


def draw_boss_health_bar(canvas: pygame.Surface, boss_target):
    """Renders top AAA Boss Health Bar with danger alarm flashing border."""
    if not boss_target or not boss_target.alive:
        return
    hp_pct = max(0.0, min(1.0, boss_target.hp / boss_target.max_hp))
    bar_w = 420
    bar_rect = pygame.Rect(SCREEN_WIDTH // 2 - bar_w // 2, 72, bar_w, 22)
    
    pygame.draw.rect(canvas, (15, 23, 42, 240), bar_rect, border_radius=6)
    fill_w = int(bar_w * hp_pct)
    if fill_w > 0:
        pygame.draw.rect(canvas, COLOR_CRIMSON, (bar_rect.left, bar_rect.top, fill_w, 22), border_radius=6)
    pygame.draw.rect(canvas, COLOR_WHITE, bar_rect, 2, border_radius=6)
    
    lbl = font_hud.render(f"DREADNOUGHT BOSS: {int(hp_pct * 100)}%", True, COLOR_WHITE)
    canvas.blit(lbl, lbl.get_rect(center=bar_rect.center))

    # Combo pill
    if combo_mult > 1:
        _pill(bar_x + 538, "COMBO", f"x{combo_mult}", True, (255, 100, 20))


def draw_radar_minimap(canvas: pygame.Surface, player, targets_group, wingmen_group=None):
    radar_w, radar_h = 175, 56
    radar_rect = pygame.Rect(SCREEN_WIDTH - 185, 10, radar_w, radar_h)
    
    pygame.draw.rect(canvas, (15, 23, 42, 235), radar_rect, border_radius=8)
    pygame.draw.rect(canvas, COLOR_CYAN, radar_rect, 2, border_radius=8)
    
    pygame.draw.line(canvas, (30, 41, 59), (radar_rect.centerx, radar_rect.top), (radar_rect.centerx, radar_rect.bottom), 1)
    pygame.draw.line(canvas, (30, 41, 59), (radar_rect.left, radar_rect.centery), (radar_rect.right, radar_rect.centery), 1)
    
    txt_r = font_card.render("RADAR", True, COLOR_CYAN)
    canvas.blit(txt_r, (radar_rect.left + 6, radar_rect.top + 3))

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


_cached_scanline_surf = None

def draw_crt_scanlines(canvas: pygame.Surface):
    global _cached_scanline_surf
    if _cached_scanline_surf is None:
        _cached_scanline_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(0, SCREEN_HEIGHT, 4):
            pygame.draw.line(_cached_scanline_surf, (0, 0, 0, 35), (0, y), (SCREEN_WIDTH, y), 1)
    canvas.blit(_cached_scanline_surf, (0, 0))


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


def draw_nav_buttons(canvas: pygame.Surface, mode: str = "game_over") -> dict[str, pygame.Rect]:
    """
    Draw large on-screen navigation arrow/action buttons for mobile.
    Replaces all keyboard M / SPACE / RETURN shortcuts with visible touch buttons.

    mode options:
      'menu'       -> single ENTER arrow button
      'game_over'  -> RETRY (right arrow) + MAP (left arrow)
      'level_clear'-> NEXT STAGE (right arrow) + MAP (left arrow)
      'victory'    -> PLAY AGAIN (right arrow) + MAP (left arrow)
      'hangar'     -> MAP (left) + PLAY (right arrow)
    """
    btns = {}
    cy = SCREEN_HEIGHT - 90  # vertical center of all nav buttons
    bh = 64                  # button height
    bw = 200                 # button width

    def _nav_btn(rect, label, icon_dir, bg_col, border_col):
        """Draw an arrow nav button. icon_dir: 'left' or 'right'."""
        mx, my = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mx, my)
        bg = tuple(min(255, c + 20) for c in bg_col) if hovered else bg_col
        pygame.draw.rect(canvas, bg, rect, border_radius=10)
        pygame.draw.rect(canvas, COLOR_WHITE if hovered else border_col, rect, 3 if hovered else 2, border_radius=10)

        # Arrow triangle
        cx, cy2 = rect.centerx, rect.centery
        if icon_dir == "right":
            arr = [(cx + 70, cy2), (cx + 54, cy2 - 12), (cx + 54, cy2 + 12)]
        else:
            arr = [(cx - 70, cy2), (cx - 54, cy2 - 12), (cx - 54, cy2 + 12)]
        pygame.draw.polygon(canvas, COLOR_WHITE if hovered else border_col, arr)

        lbl = font_banner.render(label, True, (15, 23, 42) if hovered else COLOR_WHITE)
        canvas.blit(lbl, lbl.get_rect(center=rect.center))

    if mode == "menu":
        r = pygame.Rect(SCREEN_WIDTH // 2 - bw // 2, cy, bw, bh)
        _nav_btn(r, "ENTER", "right", (14, 165, 233), COLOR_CYAN)
        btns["enter"] = r

    elif mode == "game_over":
        # Large primary RETRY button (centered, prominent)
        r_retry = pygame.Rect(SCREEN_WIDTH // 2 - 130, cy, 260, bh + 16)
        mx2, my2 = pygame.mouse.get_pos()
        hov = r_retry.collidepoint(mx2, my2)
        pygame.draw.rect(canvas, (255, 60, 60) if hov else (225, 29, 72), r_retry, border_radius=14)
        pygame.draw.rect(canvas, COLOR_WHITE, r_retry, 3 if hov else 2, border_radius=14)
        # Large arrow right
        rx, ry = r_retry.centerx, r_retry.centery
        pygame.draw.polygon(canvas, COLOR_WHITE, [(rx + 100, ry), (rx + 82, ry - 14), (rx + 82, ry + 14)])
        lbl_r = font_title.render("RETRY", True, COLOR_WHITE)
        canvas.blit(lbl_r, lbl_r.get_rect(center=r_retry.center))
        btns["retry"] = r_retry
        # Smaller MAP button below
        r_map = pygame.Rect(SCREEN_WIDTH // 2 - 100, cy + bh + 28, 200, 46)
        hov2 = r_map.collidepoint(mx2, my2)
        pygame.draw.rect(canvas, (40, 55, 80) if hov2 else (30, 41, 59), r_map, border_radius=10)
        pygame.draw.rect(canvas, COLOR_WHITE if hov2 else COLOR_CYAN, r_map, 2, border_radius=10)
        pygame.draw.polygon(canvas, COLOR_WHITE if hov2 else COLOR_CYAN,
                            [(r_map.left + 14, r_map.centery), (r_map.left + 26, r_map.centery - 8), (r_map.left + 26, r_map.centery + 8)])
        lbl_m = font_banner.render("SECTOR MAP", True, COLOR_WHITE if hov2 else COLOR_CYAN)
        canvas.blit(lbl_m, lbl_m.get_rect(center=r_map.center))
        btns["map"] = r_map

    elif mode == "level_clear":
        # Next stage (right)
        r_next = pygame.Rect(SCREEN_WIDTH // 2 + 20, cy, bw, bh)
        _nav_btn(r_next, "  NEXT STAGE", "right", (16, 185, 129), COLOR_EMERALD)
        btns["next"] = r_next
        # Map (left)
        r_map = pygame.Rect(SCREEN_WIDTH // 2 - bw - 20, cy, bw, bh)
        _nav_btn(r_map, "MAP  ", "left", (30, 41, 59), COLOR_CYAN)
        btns["map"] = r_map

    elif mode == "victory":
        # Play Again (right)
        r_again = pygame.Rect(SCREEN_WIDTH // 2 + 20, cy, bw, bh)
        _nav_btn(r_again, "  PLAY AGAIN", "right", (250, 204, 21), COLOR_GOLD)
        btns["again"] = r_again
        # Map (left)
        r_map = pygame.Rect(SCREEN_WIDTH // 2 - bw - 20, cy, bw, bh)
        _nav_btn(r_map, "MAP  ", "left", (30, 41, 59), COLOR_CYAN)
        btns["map"] = r_map

    elif mode == "hangar":
        # Map (left)
        r_map = pygame.Rect(44, SCREEN_HEIGHT - 75, bw, bh)
        _nav_btn(r_map, "MAP  ", "left", (30, 41, 59), COLOR_CYAN)
        btns["map"] = r_map
        # Play (right)
        r_play = pygame.Rect(260, SCREEN_HEIGHT - 75, bw + 60, bh)
        _nav_btn(r_play, "  LAUNCH", "right", (14, 165, 233), COLOR_CYAN)
        btns["play"] = r_play

    return btns


def draw_game_over_screen(canvas: pygame.Surface, total_score: int, highscore: int, sector_idx: int, sub_level: int) -> dict[str, pygame.Rect]:
    """
    Renders a full-screen dramatic Game Over overlay with clear instructions and touch buttons.
    Returns dict with 'retry' and 'map' Rects.
    """
    # Dark red semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((80, 0, 0, 190))
    canvas.blit(overlay, (0, 0))

    # Flashing red border
    pygame.draw.rect(canvas, COLOR_CRIMSON, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 6)

    # Title
    go_surf = font_title.render("MISSION FAILED", True, COLOR_CRIMSON)
    canvas.blit(go_surf, go_surf.get_rect(center=(SCREEN_WIDTH // 2, 210)))

    # Subtitle — tell the player what happened
    sub1 = font_banner.render("Your drone was destroyed!", True, (255, 180, 180))
    canvas.blit(sub1, sub1.get_rect(center=(SCREEN_WIDTH // 2, 285)))

    # Sector info
    sec_surf = font_hud.render(f"Sector {sector_idx + 1}  -  Stage {sub_level}", True, COLOR_HUD)
    canvas.blit(sec_surf, sec_surf.get_rect(center=(SCREEN_WIDTH // 2, 325)))

    # Score line
    score_surf = font_banner.render(f"Score: {total_score}    Best: {highscore}", True, COLOR_GOLD)
    canvas.blit(score_surf, score_surf.get_rect(center=(SCREEN_WIDTH // 2, 368)))

    # Divider
    pygame.draw.line(canvas, (80, 30, 30), (120, 400), (SCREEN_WIDTH - 120, 400), 2)

    # Instruction text
    tip = font_hud.render("Tap RETRY to try again or SECTOR MAP to choose a mission", True, COLOR_HUD)
    canvas.blit(tip, tip.get_rect(center=(SCREEN_WIDTH // 2, 430)))

    # -- Large RETRY button --
    mx, my = pygame.mouse.get_pos()
    r_retry = pygame.Rect(SCREEN_WIDTH // 2 - 140, 460, 280, 72)
    hov_r = r_retry.collidepoint(mx, my)
    pygame.draw.rect(canvas, (255, 70, 70) if hov_r else (200, 20, 50), r_retry, border_radius=16)
    pygame.draw.rect(canvas, COLOR_WHITE, r_retry, 4 if hov_r else 2, border_radius=16)
    # Arrow
    arx, ary = r_retry.right - 24, r_retry.centery
    pygame.draw.polygon(canvas, COLOR_WHITE, [(arx, ary), (arx - 14, ary - 10), (arx - 14, ary + 10)])
    lbl_retry = font_title.render("RETRY MISSION", True, COLOR_WHITE)
    canvas.blit(lbl_retry, lbl_retry.get_rect(center=r_retry.center))

    # -- SECTOR MAP button (smaller, secondary) --
    r_map = pygame.Rect(SCREEN_WIDTH // 2 - 110, 550, 220, 52)
    hov_m = r_map.collidepoint(mx, my)
    pygame.draw.rect(canvas, (40, 55, 80) if hov_m else (20, 30, 50), r_map, border_radius=10)
    pygame.draw.rect(canvas, COLOR_WHITE if hov_m else COLOR_CYAN, r_map, 3 if hov_m else 2, border_radius=10)
    pygame.draw.polygon(canvas, COLOR_WHITE if hov_m else COLOR_CYAN,
                        [(r_map.left + 14, r_map.centery), (r_map.left + 28, r_map.centery - 9), (r_map.left + 28, r_map.centery + 9)])
    lbl_map = font_banner.render("SECTOR MAP", True, COLOR_WHITE if hov_m else COLOR_CYAN)
    canvas.blit(lbl_map, lbl_map.get_rect(center=r_map.center))

    return {"retry": r_retry, "map": r_map}



def draw_virtual_touch_controls(canvas: pygame.Surface, dpad_state: dict = None, active_weapon: str = "pulse", active_button: str = None) -> dict[str, pygame.Rect]:
    """
    Renders D-pad (4 arrow buttons) on the left for movement,
    large selectable FIRE button on the right, plus EMP/ROLL/CLOAK/PAUSE buttons.
    """
    controls = {}
    if dpad_state is None:
        dpad_state = {"up": False, "down": False, "left": False, "right": False}

    # ── WEAPON COLOR MAP ──────────────────────────────────────────────────────
    wpn_colors = {
        "pulse":   (14, 165, 233),   # cyan-blue
        "scatter": (16, 185, 129),   # emerald green
        "missile": (239, 68, 68),    # red
        "beam":    (168, 85, 247),   # purple
    }
    wpn_names = {
        "pulse": "PULSE", "scatter": "SCATTER",
        "missile": "MISSILE", "beam": "BEAM",
    }
    fire_col = wpn_colors.get(active_weapon, (225, 29, 72))
    fire_name = wpn_names.get(active_weapon, "FIRE")

    # ── D-PAD (left side) ─────────────────────────────────────────────────────
    pad = 65          # button size
    gap = 8           # gap between buttons
    d_cx = 130        # d-pad horizontal center
    d_cy = SCREEN_HEIGHT - 170  # d-pad vertical center

    def _dpad_btn(rect, direction, arrow_pts):
        active = dpad_state.get(direction, False) or (active_button == direction)
        bg = (56, 189, 248) if active else (20, 30, 50, 200)
        border = COLOR_WHITE if active else (56, 189, 248)
        pygame.draw.rect(canvas, bg, rect, border_radius=12)
        pygame.draw.rect(canvas, border, rect, 2, border_radius=12)
        pygame.draw.polygon(canvas, COLOR_WHITE if active else COLOR_CYAN, arrow_pts)
        return rect

    # UP
    r_up = pygame.Rect(d_cx - pad // 2, d_cy - pad - gap, pad, pad)
    cx, cy2 = r_up.centerx, r_up.centery
    controls["dpad_up"] = _dpad_btn(r_up, "up", [(cx, cy2 - 18), (cx - 14, cy2 + 10), (cx + 14, cy2 + 10)])

    # ── D-PAD (left side) ─────────────────────────────────────────────────────
    pad = 88          # enlarged button size (was 65)
    gap = 10          # gap between buttons
    d_cx = 160        # d-pad horizontal center
    d_cy = SCREEN_HEIGHT - 170  # d-pad vertical center

    def _dpad_btn(rect, direction, arrow_pts):
        active = dpad_state.get(direction, False) or (active_button == direction)
        bg = (56, 189, 248) if active else (20, 30, 50, 220)
        border = COLOR_WHITE if active else (56, 189, 248)
        pygame.draw.rect(canvas, bg, rect, border_radius=14)
        pygame.draw.rect(canvas, border, rect, 3 if active else 2, border_radius=14)
        pygame.draw.polygon(canvas, COLOR_WHITE if active else COLOR_CYAN, arrow_pts)
        return rect

    # UP
    r_up = pygame.Rect(d_cx - pad // 2, d_cy - pad - gap, pad, pad)
    cx, cy2 = r_up.centerx, r_up.centery
    controls["dpad_up"] = _dpad_btn(r_up, "up", [(cx, cy2 - 24), (cx - 18, cy2 + 14), (cx + 18, cy2 + 14)])

    # DOWN
    r_dn = pygame.Rect(d_cx - pad // 2, d_cy + gap, pad, pad)
    cx, cy2 = r_dn.centerx, r_dn.centery
    controls["dpad_down"] = _dpad_btn(r_dn, "down", [(cx, cy2 + 24), (cx - 18, cy2 - 14), (cx + 18, cy2 - 14)])

    # LEFT
    r_lt = pygame.Rect(d_cx - pad - gap, d_cy - pad // 2, pad, pad)
    cx, cy2 = r_lt.centerx, r_lt.centery
    controls["dpad_left"] = _dpad_btn(r_lt, "left", [(cx - 24, cy2), (cx + 14, cy2 - 18), (cx + 14, cy2 + 18)])

    # RIGHT
    r_rt = pygame.Rect(d_cx + gap, d_cy - pad // 2, pad, pad)
    cx, cy2 = r_rt.centerx, r_rt.centery
    controls["dpad_right"] = _dpad_btn(r_rt, "right", [(cx + 24, cy2), (cx - 14, cy2 - 18), (cx - 14, cy2 + 18)])

    # Center decorative pip
    pygame.draw.circle(canvas, (30, 41, 59), (d_cx, d_cy), 22)
    pygame.draw.circle(canvas, (56, 189, 248), (d_cx, d_cy), 22, 2)

    # ── FIRE BUTTON (right side, extra large) ─────────────────────────
    btn_fire = pygame.Rect(SCREEN_WIDTH - 165, SCREEN_HEIGHT - 170, 140, 140)
    is_f_active = (active_button == "fire")
    fire_draw_col = tuple(min(255, c + 40) for c in fire_col) if is_f_active else fire_col
    pygame.draw.ellipse(canvas, fire_draw_col, btn_fire)
    pygame.draw.ellipse(canvas, COLOR_WHITE if is_f_active else (200, 220, 255), btn_fire, width=5 if is_f_active else 3)
    # Crosshair icon inside FIRE
    fcx, fcy = btn_fire.center
    pygame.draw.circle(canvas, COLOR_WHITE, (fcx, fcy - 8), 16, 2)
    pygame.draw.circle(canvas, COLOR_WHITE, (fcx, fcy - 8), 4)
    # Weapon name label
    lbl_fire = font_hud.render("FIRE", True, COLOR_WHITE)
    lbl_wpn_name = font_card.render(fire_name, True, COLOR_WHITE)
    canvas.blit(lbl_fire, (fcx - lbl_fire.get_width() // 2, fcy + 12))
    canvas.blit(lbl_wpn_name, (fcx - lbl_wpn_name.get_width() // 2, fcy + 32))
    controls["fire"] = btn_fire

    # ── WEAPON SELECT BUTTON (above FIRE, tap to cycle) ──────────────────────
    btn_weapon = pygame.Rect(SCREEN_WIDTH - 165, SCREEN_HEIGHT - 290, 140, 60)
    is_w_active = (active_button == "weapon")
    pygame.draw.rect(canvas, tuple(min(255, c + 30) for c in fire_col) if is_w_active else (30, 41, 59), btn_weapon, border_radius=12)
    pygame.draw.rect(canvas, COLOR_WHITE if is_w_active else fire_col, btn_weapon, 3 if is_w_active else 2, border_radius=12)
    # Left/right cycle arrows
    wcx, wcy = btn_weapon.center
    pygame.draw.polygon(canvas, COLOR_WHITE, [(wcx - 52, wcy), (wcx - 38, wcy - 10), (wcx - 38, wcy + 10)])
    pygame.draw.polygon(canvas, COLOR_WHITE, [(wcx + 52, wcy), (wcx + 38, wcy - 10), (wcx + 38, wcy + 10)])
    lbl_wsel = font_banner.render(fire_name, True, COLOR_WHITE)
    canvas.blit(lbl_wsel, lbl_wsel.get_rect(center=btn_weapon.center))
    controls["weapon"] = btn_weapon

    # ── EMP Button (90x90) ───────────────────────────────────────────────────
    btn_emp = pygame.Rect(SCREEN_WIDTH - 290, SCREEN_HEIGHT - 130, 90, 90)
    is_e_active = (active_button == "emp")
    pygame.draw.ellipse(canvas, (56, 189, 248) if is_e_active else (14, 165, 233), btn_emp)
    pygame.draw.ellipse(canvas, COLOR_WHITE if is_e_active else COLOR_CYAN, btn_emp, width=3 if is_e_active else 2)
    ecx, ecy = btn_emp.center
    bolt_pts = [(ecx+3, ecy-18), (ecx-9, ecy-2), (ecx-1, ecy-2), (ecx-5, ecy+16), (ecx+8, ecy), (ecx, ecy)]
    pygame.draw.polygon(canvas, COLOR_WHITE, bolt_pts)
    lbl_e = font_card.render("EMP", True, COLOR_WHITE)
    canvas.blit(lbl_e, (ecx - lbl_e.get_width() // 2, ecy + 16))
    controls["emp"] = btn_emp

    # ── ROLL Button (90x90) ──────────────────────────────────────────────────
    btn_roll = pygame.Rect(SCREEN_WIDTH - 290, SCREEN_HEIGHT - 235, 90, 90)
    is_r_active = (active_button == "roll")
    pygame.draw.ellipse(canvas, (52, 211, 153) if is_r_active else (16, 185, 129), btn_roll)
    pygame.draw.ellipse(canvas, COLOR_WHITE if is_r_active else COLOR_EMERALD, btn_roll, width=3 if is_r_active else 2)
    rcx, rcy = btn_roll.center
    pygame.draw.arc(canvas, COLOR_WHITE, (rcx - 16, rcy - 16, 32, 32), 0.5, 5.0, 3)
    lbl_r = font_card.render("ROLL", True, COLOR_WHITE)
    canvas.blit(lbl_r, (rcx - lbl_r.get_width() // 2, rcy + 16))
    controls["roll"] = btn_roll

    # ── CLOAK Button (90x90) ─────────────────────────────────────────────────
    btn_cloak = pygame.Rect(SCREEN_WIDTH - 290, SCREEN_HEIGHT - 340, 90, 90)
    is_c_active = (active_button == "cloak")
    pygame.draw.ellipse(canvas, (217, 70, 239) if is_c_active else (168, 85, 247), btn_cloak)
    pygame.draw.ellipse(canvas, COLOR_WHITE if is_c_active else COLOR_MAGENTA, btn_cloak, width=3 if is_c_active else 2)
    ccx, ccy = btn_cloak.center
    shield_pts = [(ccx, ccy-16), (ccx+12, ccy-9), (ccx+11, ccy+6), (ccx, ccy+14), (ccx-11, ccy+6), (ccx-12, ccy-9)]
    pygame.draw.polygon(canvas, COLOR_WHITE, shield_pts, 2)
    lbl_c = font_card.render("CLOAK", True, COLOR_WHITE)
    canvas.blit(lbl_c, (ccx - lbl_c.get_width() // 2, ccy + 16))
    controls["cloak"] = btn_cloak

    # ── AUTO-LOCK TARGET ASSIST Button ───────────────────────────────────────
    btn_lock = pygame.Rect(SCREEN_WIDTH - 165, SCREEN_HEIGHT - 365, 140, 56)
    is_l_active = (active_button == "autolock")
    bg_l = (16, 185, 129) if is_l_active else (30, 41, 59)
    pygame.draw.rect(canvas, bg_l, btn_lock, border_radius=12)
    pygame.draw.rect(canvas, COLOR_WHITE if is_l_active else COLOR_EMERALD, btn_lock, 3 if is_l_active else 2, border_radius=12)
    lbl_lock = font_card.render("LOCK ON" if is_l_active else "AUTO LOCK", True, COLOR_WHITE)
    canvas.blit(lbl_lock, lbl_lock.get_rect(center=btn_lock.center))
    controls["autolock"] = btn_lock

    # ── ULTIMATE OVERDRIVE Button (90x90) ────────────────────────────────────
    btn_ult = pygame.Rect(SCREEN_WIDTH - 290, SCREEN_HEIGHT - 445, 90, 90)
    is_u_active = (active_button == "ultimate")
    pygame.draw.ellipse(canvas, (250, 204, 21) if is_u_active else (147, 51, 234), btn_ult)
    pygame.draw.ellipse(canvas, COLOR_WHITE if is_u_active else COLOR_GOLD, btn_ult, width=4 if is_u_active else 2)
    ucx, ucy = btn_ult.center
    pygame.draw.circle(canvas, COLOR_WHITE, (ucx, ucy - 6), 14, 2)
    pygame.draw.circle(canvas, COLOR_GOLD, (ucx, ucy - 6), 5)
    lbl_u = font_card.render("ULTIMATE", True, COLOR_WHITE)
    canvas.blit(lbl_u, (ucx - lbl_u.get_width() // 2, ucy + 16))
    controls["ultimate"] = btn_ult

    # ── PAUSE Button (top-left standalone) ───────────────────────────────────
    btn_pause = pygame.Rect(12, 10, 100, 60)
    is_p_active = (active_button == "pause")
    pygame.draw.rect(canvas, (56, 189, 248) if is_p_active else (30, 41, 59), btn_pause, border_radius=10)
    pygame.draw.rect(canvas, COLOR_WHITE if is_p_active else COLOR_CYAN, btn_pause, 3 if is_p_active else 2, border_radius=10)
    pcx, pcy = btn_pause.center
    pygame.draw.rect(canvas, (15, 23, 42) if is_p_active else COLOR_CYAN, (pcx - 14, pcy - 14, 10, 28), border_radius=3)
    pygame.draw.rect(canvas, (15, 23, 42) if is_p_active else COLOR_CYAN, (pcx + 4, pcy - 14, 10, 28), border_radius=3)
    controls["pause"] = btn_pause

    return controls


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

    # Mobile HANGAR button — replaces [SPACE] keyboard shortcut
    hangar_btn = pygame.Rect(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT - 58, 220, 46)
    mx_h, my_h = pygame.mouse.get_pos()
    hh = hangar_btn.collidepoint(mx_h, my_h)
    pygame.draw.rect(canvas, (56, 189, 248) if hh else (30, 41, 59), hangar_btn, border_radius=8)
    pygame.draw.rect(canvas, COLOR_WHITE if hh else COLOR_CYAN, hangar_btn, 3 if hh else 2, border_radius=8)
    lbl_h = font_banner.render("HANGAR SHOP", True, (15, 23, 42) if hh else COLOR_CYAN)
    canvas.blit(lbl_h, lbl_h.get_rect(center=hangar_btn.center))

    exit_btn_rect = draw_exit_button(canvas)
    return card_rects, exit_btn_rect, diff_rect, hangar_btn


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

    # Skin Theme Selector Button in Hangar Header
    skin_btn_rect = pygame.Rect(SCREEN_WIDTH - 600, 30, 240, 42)
    hov_s = skin_btn_rect.collidepoint(mx, my)
    pygame.draw.rect(canvas, (16, 185, 129) if hov_s else (30, 41, 59), skin_btn_rect, border_radius=8)
    pygame.draw.rect(canvas, COLOR_WHITE if hov_s else COLOR_EMERALD, skin_btn_rect, 2, border_radius=8)
    lbl_skin = font_card.render("🎨 CHANGE DRONE SKIN", True, COLOR_WHITE)
    canvas.blit(lbl_skin, lbl_skin.get_rect(center=skin_btn_rect.center))

    exit_btn_rect = draw_exit_button(canvas)
    return exit_btn_rect, skin_btn_rect


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

