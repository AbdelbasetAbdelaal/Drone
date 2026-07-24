# 🛸 Drone Hunter - Sci-Fi Arcade

A feature-packed 2D side-scrolling sci-fi arcade game built with Python and Pygame (`pygame-ce`).

---

## 🚀 How to Run

Open your terminal or command prompt and execute:

```bash
cd /d D:\AI_Projects\drone_hunter
python main.py
```

---

## 🌟 Game Features

### 1. 🌀 Evasive Barrel Roll & Defense
* **Evasive Roll (`Shift` / `E`)**: Execute a 360° spin dodge maneuver with invulnerability frames (i-frames) and cyan trailing energy sparks.
* **EMP Shockwave (`E` / `Right-Click`)**: Radial energy shockwave that wipes incoming missiles and non-boss targets.
* **Forcefield Shield & Overclock**: Collectable pickups granting temp shields and 2x fire rate.

### 2. 🏙️ Tactical Targets & Ground Combat
* **Target Vehicles**: Armored rovers patrolling city streets with a **pulsing neon red lock-on target crosshair** (+70 Pts).
* **Ground Turrets**: Roof/street mounted defense turrets firing anti-air energy salvos upward (+45 Pts).
* **Aggressive Chaser Drones**: High-speed interceptors actively tracking and pursuing player altitude (+35 Pts).
* **Standard, Fast, Armored & Boss Drones**: Full enemy hierarchy with boss dreadnoughts every 3 levels.

### 3. 🎨 Visuals & Weather Dynamics
* **Parallax City Skyline**: Multi-layered scrolling backdrop with dynamic **Clear**, **Rainstorm**, and **Wind Hazard** mechanics.
* **Particle Physics**: Real-time thruster trails, roll sparks, explosion bursts, and floating damage numbers.

---

## 🎮 Game Controls

| Key / Input | Action |
| :--- | :--- |
| **`Spacebar` / `W`** | Fly upward with thrusters |
| **`A` / `D`** or **`←` / `→`** | Move drone left / right |
| **`Shift`** | **Evasive Barrel Roll** (Invulnerability & Dodge) |
| **`E` / Right Click** | **EMP Shockwave Blast** |
| **Mouse Cursor** | Aim cannon 360 degrees |
| **Left Click** | Fire laser cannons (Hold to continuous fire) |
| **`H`** | Open **Hangar Shop** & Upgrade Drone |
| **`P`** | Pause Game |
| **`R`** | Instant Restart on Game Over |

---

## 📁 Project Structure

```text
drone_hunter/
├── main.py             # Main game loop, states & HUD rendering
├── settings.py         # Sci-fi colors, game states, constants
├── highscore.txt       # Local high score persistence
├── requirements.txt    # Dependencies (pygame-ce)
├── USAGE.txt           # Plain text instructions guide
├── README.md           # Markdown project guide
└── src/
    ├── player.py       # Player Drone with Battery System & Thrusters
    ├── bullet.py       # Laser projectile with trigonometry
    ├── target.py       # Standard, Fast, and Armored Targets & Spawner
    ├── particles.py    # Particle system (smoke, explosions)
    ├── background.py   # Multi-layered parallax scrolling
    ├── audio.py        # Sound synthesis manager
    └── game_manager.py # State manager
```
