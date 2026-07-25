"""
================================================================================
                    DRONE HUNTER 3D - CONFIGURATION MODULE
================================================================================
Centralized configuration, color palette, constants, and save/load persistence.
"""

import os
import json

# --- Screen & Display ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TARGET_FPS = 60

# --- Sci-Fi Color Palette ---
COLOR_BG = (10, 15, 26)
COLOR_SKY_TOP = (15, 10, 30)
COLOR_SKY_BOTTOM = (45, 15, 55)
COLOR_CYAN = (14, 165, 233)
COLOR_GOLD = (245, 158, 11)
COLOR_EMERALD = (16, 185, 129)
COLOR_CRIMSON = (239, 68, 68)
COLOR_MAGENTA = (217, 70, 239)
COLOR_PURPLE = (168, 85, 247)
COLOR_COIN = (250, 204, 21)
COLOR_SHIELD = (6, 182, 212)
COLOR_OVERCLOCK = (236, 72, 153)
COLOR_SLOWMO = (168, 85, 247)
COLOR_HUD = (226, 232, 240)
COLOR_ROOF = (30, 41, 59)
COLOR_ROAD = (15, 23, 42)

# --- Save / Load System ---
SAVE_FILE = "save_data.json"

def load_game_data():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "coins": 183500,
        "highscore": 0,
        "upgrade_levels": {
            "battery": 2,
            "speed": 1,
            "fire_rate": 3,
            "emp_recharge": 2,
            "damage": 2
        }
    }

def save_game_data(coins, highscore, upgrade_levels):
    try:
        data = {"coins": coins, "highscore": highscore, "upgrade_levels": upgrade_levels}
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass
