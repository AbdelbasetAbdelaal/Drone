import pygame

# Display settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Drone Hunter"

# Colors (RGB)
COLOR_BG = (15, 23, 42)       # Dark slate blue background
COLOR_WHITE = (255, 255, 255)
COLOR_DRONE = (56, 189, 248)    # Cyan
COLOR_BULLET = (250, 204, 21)   # Yellow
COLOR_TARGET = (244, 63, 94)    # Coral Red
COLOR_HUD = (226, 232, 240)

# Game physics settings
GRAVITY = 700.0           # Downward acceleration (pixels / s^2)
THRUST_FORCE = -1500.0     # Upward thrust acceleration when Spacebar is pressed
MAX_FALL_SPEED = 600.0    # Terminal velocity
HORIZONTAL_SPEED = 400.0  # Horizontal movement speed (pixels / s)
BULLET_SPEED = 900.0      # Bullet velocity (pixels / s)
TARGET_SPEED = 150.0
SHOOT_COOLDOWN = 0.15     # Fire rate cooldown (seconds)

