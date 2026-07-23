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
COLOR_HUD = (226, 232, 240)
COLOR_TEXT_DIM = (148, 163, 184)


# Game Physics settings
GRAVITY = 90.0             # Ultra-gentle downward gravity (pixels / s^2)
THRUST_FORCE = -350.0      # Soft upward thrust force
MAX_FALL_SPEED = 70.0      # Very slow, graceful free-fall speed (pixels / s)
HORIZONTAL_SPEED = 420.0   # Horizontal flight speed
BULLET_SPEED = 950.0       # Bullet velocity
TARGET_SPEED = 180.0       # Base target movement speed (pixels / s)
SHOOT_COOLDOWN = 0.14      # Fire rate cooldown (seconds)




# Target Types Parameters
TARGET_TYPE_STANDARD = "standard"
TARGET_TYPE_FAST = "fast"
TARGET_TYPE_ARMORED = "armored"

# Player Settings
MAX_HEALTH = 100
