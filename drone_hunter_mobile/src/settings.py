import pygame

# Display settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Drone Hunter - Sci-Fi Arcade Edition"

# Game States
STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2
STATE_LEVEL_CLEAR = 3
STATE_HANGAR = 4
STATE_PAUSED = 5
STATE_SECTOR_SELECT = 6
STATE_VICTORY = 7

# Colors (Vibrant Sci-Fi Synthwave & Cyberpunk Palette)
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
COLOR_NEON_RED = (255, 30, 60)     # Neon Red Crosshair Target lock-on
COLOR_HUD = (226, 232, 240)
COLOR_TEXT_DIM = (148, 163, 184)
COLOR_MISSILE = (249, 115, 22)    # Neon Orange Missile
COLOR_BEAM = (56, 189, 248)       # Electric Cyan Laser Beam
COLOR_PURPLE = (168, 85, 247)     # Neon Violet Singularity
COLOR_OCEAN_BLUE = (14, 116, 144) # Stormy Sea Blue
COLOR_DESERT_AMBER = (217, 119, 6) # Desert Sunset Amber

# Game Physics settings (Boosted for Mobile Speed & Hyper-Responsiveness)
GRAVITY = 90.0             # Ultra-gentle downward gravity (pixels / s^2)
THRUST_FORCE = -520.0      # Snappy upward thrust force
MAX_FALL_SPEED = 90.0      # Graceful free-fall speed (pixels / s)
HORIZONTAL_SPEED = 560.0   # Fast horizontal flight speed (pixels / s)
BULLET_SPEED = 1250.0      # Hyper-fast bullet velocity
ENEMY_BULLET_SPEED = 460.0 # Enemy bullet velocity
TARGET_SPEED = 220.0       # Dynamic target movement speed (pixels / s)
SHOOT_COOLDOWN = 0.10      # Fast fire rate cooldown (seconds)

# Evasive Roll & Tactical Cloaking
ROLL_DURATION = 0.40       # Roll duration in seconds
ROLL_COOLDOWN = 2.0        # Roll recharge cooldown in seconds
ROLL_SPEED_BOOST = 1.8     # Movement speed multiplier during roll
CLOAK_DURATION = 4.0       # Tactical Cloak duration in seconds
CLOAK_COOLDOWN_MAX = 15.0  # Tactical Cloak cooldown in seconds

# Difficulty Mode Settings (EASY, NORMAL, HARD, NIGHTMARE)
DIFFICULTY_EASY = 0
DIFFICULTY_NORMAL = 1
DIFFICULTY_HARD = 2
DIFFICULTY_NIGHTMARE = 3

DIFFICULTY_NAMES = ["EASY 🟢", "NORMAL 🔵", "HARD ⚠️", "NIGHTMARE ☠️"]

DIFFICULTY_SETTINGS = {
    0: {"name": "EASY 🟢", "hp_mult": 0.70, "speed_mult": 0.75, "damage_mult": 0.60, "drop_rate": 0.45},
    1: {"name": "NORMAL 🔵", "hp_mult": 1.00, "speed_mult": 1.00, "damage_mult": 1.00, "drop_rate": 0.30},
    2: {"name": "HARD ⚠️", "hp_mult": 1.35, "speed_mult": 1.30, "damage_mult": 1.40, "drop_rate": 0.22},
    3: {"name": "NIGHTMARE ☠️", "hp_mult": 1.80, "speed_mult": 1.60, "damage_mult": 1.80, "drop_rate": 0.15}
}

# Target Types Parameters
TARGET_TYPE_STANDARD = "standard"
TARGET_TYPE_FAST = "fast"
TARGET_TYPE_ARMORED = "armored"
TARGET_TYPE_SHOOTER = "shooter"
TARGET_TYPE_BOSS = "boss"
TARGET_TYPE_TURRET = "turret"
TARGET_TYPE_VEHICLE = "vehicle"
TARGET_TYPE_CHASER = "chaser"
TARGET_TYPE_STEALTH_MIRAGE = "stealth_mirage"
TARGET_TYPE_EMP_DISRUPTER = "emp_disrupter"
TARGET_TYPE_TITAN_MECH = "titan_mech"

# Player Settings
MAX_HEALTH = 100
EMP_COOLDOWN_MAX = 20.0
WINGMAN_MAX_COUNT = 2

# Weapon Definitions
WEAPON_PULSE = "pulse"
WEAPON_SCATTER = "scatter"
WEAPON_MISSILE = "missile"
WEAPON_BEAM = "beam"

WEAPON_DEFS = {
    WEAPON_PULSE: {
        "name": "Pulse Cannon",
        "cooldown": 0.14,
        "damage": 35,
        "color": COLOR_GOLD,
        "icon": "⚡",
        "unlocked_default": True
    },
    WEAPON_SCATTER: {
        "name": "Scatter Shotgun",
        "cooldown": 0.28,
        "damage": 22,
        "color": COLOR_OVERCLOCK,
        "icon": "💥",
        "unlocked_default": True
    },
    WEAPON_MISSILE: {
        "name": "Homing Missiles",
        "cooldown": 0.38,
        "damage": 75,
        "color": COLOR_MISSILE,
        "icon": "🚀",
        "unlocked_default": False
    },
    WEAPON_BEAM: {
        "name": "High-Level Plasma Laser",
        "cooldown": 0.05,
        "damage": 28,
        "color": COLOR_BEAM,
        "icon": "⚡",
        "unlocked_default": False
    }
}

# Campaign Sector Definitions (Sub-level stage goals balanced for deep, thrilling missions!)
SECTORS = [
    {
        "id": 0,
        "name": "Megacity Skyline",
        "theme": "neon_city",
        "description": "High-tech rooftop megacity with heavy airborne chasers & turrets.",
        "weather": "rain",
        "base_target_score": 6000,
        "stages": [
            {"sub_level": 1, "name": "Stage 1-1: Recon Patrol", "score": 1800, "desc": "Scout drones & airborne reconnaissance."},
            {"sub_level": 2, "name": "Stage 1-2: Laser Grid Assault", "score": 3500, "desc": "Armored mechs & deadly laser traps."},
            {"sub_level": 3, "name": "Stage 1-3: Sky Dreadnought ☠️", "score": 6000, "desc": "Climax battle against Sky Fortress Boss."}
        ],
        "unlocked_default": True
    },
    {
        "id": 1,
        "name": "Cyber Factory Core",
        "theme": "factory",
        "description": "Industrial automated foundry filled with armored mechs & defensive grids.",
        "weather": "sparks",
        "base_target_score": 10000,
        "stages": [
            {"sub_level": 1, "name": "Stage 2-1: Foundry Gates", "score": 3000, "desc": "Automated security sentries."},
            {"sub_level": 2, "name": "Stage 2-2: Furnace Breach", "score": 6000, "desc": "Molten lava hazards & heavy mechs."},
            {"sub_level": 3, "name": "Stage 2-3: Overlord Core ☠️", "score": 10000, "desc": "Climax battle against Factory Core Titan."}
        ],
        "unlocked_default": False
    },
    {
        "id": 2,
        "name": "Orbital Space Citadel",
        "theme": "space",
        "description": "Deep space fortress guarded by meteor storms & the Dreadnought Flagship.",
        "weather": "stardust",
        "base_target_score": 15000,
        "stages": [
            {"sub_level": 1, "name": "Stage 3-1: Asteroid Field", "score": 5000, "desc": "Meteor shower obstacles & scout ships."},
            {"sub_level": 2, "name": "Stage 3-2: Citadel Defense Grid", "score": 9500, "desc": "Singularity vortexes & plasma turrets."},
            {"sub_level": 3, "name": "Stage 3-3: Flagship Dreadnought ☠️", "score": 15000, "desc": "Climax battle against Space Citadel Flagship."}
        ],
        "unlocked_default": False
    },
    {
        "id": 3,
        "name": "Stormy Ocean Battlescape",
        "theme": "ocean",
        "description": "Raging tempest ocean with naval warship salvos & aggressive sea drones.",
        "weather": "sea_storm",
        "base_target_score": 22000,
        "stages": [
            {"sub_level": 1, "name": "Stage 4-1: Tempest Swells", "score": 7500, "desc": "Sea spray wind gusts & naval mines."},
            {"sub_level": 2, "name": "Stage 4-2: Naval Fleet Siege", "score": 14000, "desc": "Warship salvos & aquatic chasers."},
            {"sub_level": 3, "name": "Stage 4-3: Leviathan Warship ☠️", "score": 22000, "desc": "Climax battle against Leviathan Naval Boss."}
        ],
        "unlocked_default": False
    },
    {
        "id": 4,
        "name": "Neon Sun Desert Wasteland",
        "theme": "desert",
        "description": "Scorching dune wasteland guarded by sand turrets & the Colossus Titan Mech.",
        "weather": "sandstorm",
        "base_target_score": 30000,
        "stages": [
            {"sub_level": 1, "name": "Stage 5-1: Dune Canyons", "score": 10000, "desc": "Sandstorm dust haze & sand turrets."},
            {"sub_level": 2, "name": "Stage 5-2: Monolith Ruins", "score": 18000, "desc": "Cyber pyramid monoliths & explosive barrels."},
            {"sub_level": 3, "name": "Stage 5-3: Colossus Titan Mech ☠️", "score": 30000, "desc": "Ultimate climax battle against Colossus Titan Mech."}
        ],
        "unlocked_default": False
    }
]

# Shop Upgrade Definitions
UPGRADES = {
    "battery": {"name": "Max Battery Capacity", "base_cost": 50, "cost_mult": 1.6, "max_lvl": 5},
    "speed": {"name": "Thruster Agility", "base_cost": 60, "cost_mult": 1.7, "max_lvl": 5},
    "fire_rate": {"name": "Cannon Fire-Rate", "base_cost": 75, "cost_mult": 1.8, "max_lvl": 5},
    "emp_recharge": {"name": "EMP Shockwave Charger", "base_cost": 100, "cost_mult": 2.0, "max_lvl": 5},
    "wingman": {"name": "Wingman Support Minidrones", "base_cost": 150, "cost_mult": 2.2, "max_lvl": 2},
    "cloak": {"name": "Tactical Cloaking Unit", "base_cost": 200, "cost_mult": 1.0, "max_lvl": 1},
    "missiles": {"name": "Homing Missile Ordnance", "base_cost": 250, "cost_mult": 1.0, "max_lvl": 1},
    "beam": {"name": "High-Level Plasma Laser Cannon", "base_cost": 300, "cost_mult": 1.0, "max_lvl": 1},
}
