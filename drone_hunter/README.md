# 🛸 Drone Hunter - Sci-Fi Arcade

A feature-packed 2D side-scrolling sci-fi tactical arcade game built with Python and Pygame (`pygame-ce`).

---

## 🚀 How to Run

Open your terminal or command prompt and execute:

```bash
cd /d D:\AI_Projects\drone_hunter
python main.py
```

Or launch the pre-compiled executable:
```text
D:\AI_Projects\drone_hunter\dist\DroneHunterSingle.exe
```

---

## 🌟 Key Game Features

### 1. 🌀 Evasive Barrel Roll & Defense
* **Evasive Roll (`Shift`)**: Execute a 360° spin dodge maneuver with invulnerability frames (i-frames) and cyan trailing energy sparks.
* **⚡ Near-Miss Bullet-Time Dodge**: Rolling close to enemy projectiles triggers a Matrix slow-mo reaction effect and awards `+100 Bonus PTS`.
* **EMP Shockwave (`E` / `Right-Click`)**: Radial energy shockwave that wipes incoming missiles and non-boss targets.

### 2. 🧠 Smart Enemy AI & Heavy Targets
* **Predictive Aiming AI**: Ground turrets and shooter drones predict your velocity vector and shoot ahead of your drone.
* **Reactive Dodging AI**: Fast interceptors detect incoming lasers and execute vertical evasive maneuvers.
* **Boss Phase 2 Enrage**: Under 50% HP, the Boss Dreadnought enters Phase 2 Rage mode with 3x shield speed and 6-bullet fan salvos.
* **Heavy Enemy Durability**: Heavy Bosses (65-125+ HP), Armored Rovers (14-26+ HP), and Ground Turrets (12-18+ HP) require sustained tactical fire.

### 3. 💥 Interactive Environment & Weather Hazards
* **Explosive Energy Barrels (`💥`)**: Shoot floating canisters to detonate a massive 250px radial chain explosion.
* **Parallax City Skyline**: Multi-layered scrolling backdrop with dynamic **Clear**, **Stormy Rain**, and **Wind Hazard** mechanics.

### 4. ⏸️ Interactive Pause Menu & Screen Controls
* Access Hangar Shop (`H`), Difficulty Selector (`D`), Quick Upgrades (`1-4`), and Screen Resolutions (`F11`, `F2-F4`) directly from the Pause menu!

---

## 🎮 Game Controls & Hotkeys

| Key / Input | Action |
| :--- | :--- |
| **`Spacebar` / `W`** | Fly upward with thrusters |
| **`A` / `D`** or **`←` / `→`** | Move drone left / right |
| **`Shift`** | **Evasive Barrel Roll** (Invulnerability & Dodge) |
| **`E` / Right Click** | **EMP Shockwave Blast** |
| **Mouse Cursor** | Aim cannon 360 degrees |
| **Left Click** | Fire laser cannons (Hold for continuous fire) |
| **`H`** | Open **Hangar Shop** & Upgrade Drone *(Usable anytime & in Pause)* |
| **`D`** | Cycle **Difficulty Mode** (`NORMAL` ➔ `HARDCORE ⚠️` ➔ `NIGHTMARE ☠️`) |
| **`1` `2` `3` `4`** | **Quick-Buy Drone Upgrades** *(Battery, Speed, Fire-Rate, EMP)* |
| **`F11` / `F`** | Toggle Fullscreen Mode |
| **`F2` / `F3` / `F4`** | Change Resolution (`F2`: 720p, `F3`: 900p, `F4`: 1080p) |
| **`P`** | Pause / Resume Game |
| **`R`** | Restart Fresh on Game Over |

---

## 📁 Project Structure

```text
drone_hunter/
├── main.py             # Main game loop, state machine & HUD rendering
├── settings.py         # Sci-fi colors, game states, resolution constants
├── save_data.json      # Saved coins, high score, and shop upgrades
├── USAGE.txt           # Detailed user guide and usage manual
├── README.md           # Project summary guide
└── src/
    ├── player.py       # Player Drone with Battery, Barrel Roll & Thrusters
    ├── bullet.py       # Player and Enemy laser projectiles
    ├── target.py       # Standard, Fast, Armored, Vehicle, Turret & Boss AI
    ├── powerup.py      # Battery, Shield, Overclock, SlowMo, Coin & Explosive Barrels
    ├── particles.py    # Particle system (smoke, explosions, near-miss text)
    ├── background.py   # Multi-layered parallax scrolling & weather effects
    └── audio.py        # Sound synthesis manager
```
