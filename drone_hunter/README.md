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

### 1. 🎨 Visuals & Parallax Background
* **Parallax 2D Layers**: Starfield layer, mountain silhouettes, and a scrolling cyberpunk city skyline.
* **Particle System**: Real-time thruster smoke trails and explosive particle bursts when destroying enemy targets.

### 2. 🔊 Audio Layer (SFX)
* Procedurally synthesized sound effects for **laser fire**, **thruster hums**, **target explosions**, **level-up chimes**, and **game over alerts**.

### 3. 🛡️ Health / Battery & Game States
* **Start Menu**: Displays title screen, controls guide, and persistent **High Score**.
* **Battery System**: Drone features a 100% Battery Bar. Taking damage reduces battery by 25%.
* **Game Over & Restart**: Displays final stats, level reached, and press `R` to restart instantly.

### 4. 👾 Enemy Types & Level Scaling
* **Standard Target** (Red Ring): 1 HP, Normal speed, +10 Pts.
* **Fast Target** (Magenta/Cyan): 1 HP, High speed, +25 Pts.
* **Armored Target** (Crimson Shield): 3 HP (Armor Gauge), Heavy, +50 Pts.
* **Level Progression**: Every 100 points unlocks the next level with faster enemy spawns and movement.

---

## 🎮 Game Controls

| Key / Input | Action |
| :--- | :--- |
| **`Spacebar`** | Start game / Engage upward thrusters |
| **`A` / `D`** or **`←` / `→`** | Move drone horizontally left / right |
| **Mouse Cursor** | Aim cannon in 360 degrees |
| **Left Mouse Click** | Fire laser bullets (Hold for continuous fire) |
| **`R`** | Restart game when in Game Over state |
| **`Esc`** | Exit game |

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
