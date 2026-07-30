"""
Constants used across the SwimAnalyzer AI application.
"""
from typing import Tuple

# UI Settings
APP_TITLE = "SwimAnalyzer AI"
APP_VERSION = "0.1.0-alpha"

# Drawing Colors (BGR format for OpenCV)
COLOR_RED: Tuple[int, int, int] = (0, 0, 255)
COLOR_GREEN: Tuple[int, int, int] = (0, 255, 0)
COLOR_BLUE: Tuple[int, int, int] = (255, 0, 0)
COLOR_YELLOW: Tuple[int, int, int] = (0, 255, 255)
COLOR_WHITE: Tuple[int, int, int] = (255, 255, 255)

# Drawing Thicknesses
THICKNESS_LANDMARK = 2
THICKNESS_CONNECTION = 2

# Video Processing
DEFAULT_FPS = 30.0
