import pygame

# Display settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Drone Hunter - Sci-Fi Arcade"

# Game States
STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2
STATE_LEVEL_CLEAR = 3
STATE_HANGAR = 4
STATE_PAUSED = 5


# Colors (Vibrant Sci-Fi Synthwave Palette)
COLOR_BG = (15, 23, 42)          # Deep slate navy
COLOR_WHITE = (255, 255, 255)
COLOR_CYAN = (56, 189, 248)       # Player drone cyan
COLOR_DRONE = COLOR_CYAN          # Alias for player drone
COLOR_GOLD = (250, 204, 21)       # Laser bullet yellow
COLOR_BULLET = COLOR_GOLD         # Alias for bullets
COLOR_MAGENTA = (236, 72, 153)    # Fast enemy magenta
COLOR_CRIMSON = (239, 68, 68)     # Armored enemy crimson
COLOR_TARGET = COLOR_CRIMSON      # Alias for enemy target
COLOR_EMERALD = (52, 211, 153)    # Health / Emerald green
COLOR_SHIELD = (99, 102, 241)     # Forcefield Indigo
COLOR_OVERCLOCK = (245, 158, 11)  # Overclock Speed Amber
COLOR_SLOWMO = (14, 165, 233)     # Time Dilation Electric Blue
COLOR_COIN = (234, 179, 8)        # Gold Currency Coin
COLOR_HUD = (226, 232, 240)
COLOR_TEXT_DIM = (148, 163, 184)

# Game Physics settings
GRAVITY = 90.0             # Ultra-gentle downward gravity (pixels / s^2)
THRUST_FORCE = -350.0      # Soft upward thrust force
MAX_FALL_SPEED = 70.0      # Very slow, graceful free-fall speed (pixels / s)
HORIZONTAL_SPEED = 420.0   # Horizontal flight speed
BULLET_SPEED = 950.0       # Bullet velocity
ENEMY_BULLET_SPEED = 400.0 # Enemy bullet velocity
TARGET_SPEED = 180.0       # Base target movement speed (pixels / s)
SHOOT_COOLDOWN = 0.14      # Fire rate cooldown (seconds)

# Target Types Parameters
TARGET_TYPE_STANDARD = "standard"
TARGET_TYPE_FAST = "fast"
TARGET_TYPE_ARMORED = "armored"
TARGET_TYPE_SHOOTER = "shooter"
TARGET_TYPE_BOSS = "boss"

# Player Settings
MAX_HEALTH = 100
EMP_COOLDOWN_MAX = 20.0

# Shop Upgrade Definitions (Costs & Max Levels)
UPGRADES = {
    "battery": {"name": "Max Battery Capacity", "base_cost": 50, "cost_mult": 1.6, "max_lvl": 5},
    "speed": {"name": "Thruster Agility", "base_cost": 60, "cost_mult": 1.7, "max_lvl": 5},
    "fire_rate": {"name": "Cannon Fire-Rate", "base_cost": 75, "cost_mult": 1.8, "max_lvl": 5},
    "emp_recharge": {"name": "EMP Shockwave Charger", "base_cost": 100, "cost_mult": 2.0, "max_lvl": 5},
}
