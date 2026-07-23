# 🛸 Drone Hunter

A 2D side-scrolling arcade game built with Python and Pygame (`pygame-ce`).

---

## 🚀 How to Run

Open your terminal or command prompt and execute:

```bash
cd /d D:\AI_Projects\drone_hunter
python main.py
```

---

## 🏆 Level Progression System

* **100 Points Per Level**: Every **100 points** scored advances you to the **Next Level** (Level 1 → Level 2 → Level 3...).
* **Dynamic Difficulty Scaling**:
  * **Faster Enemy Targets**: Targets move faster at each new level (+35 px/s per level).
  * **Faster Spawning**: Target spawn intervals decrease at higher levels.
  * **Level Up Banner & Sound**: Triggers an audio chime and on-screen celebratory banner when unlocking the next level.

---

## 🎮 Game Controls

| Key / Input | Action |
| :--- | :--- |
| **`Spacebar`** | Hold to engage upward thrusters (resists gravity) |
| **`A` / `D`** or **`←` / `→`** | Move drone horizontally left / right |
| **Mouse Cursor** | Aim cannon towards cursor position |
| **Left Mouse Click** | Shoot bullets (Hold for continuous fire) |
| **`R`** | Restart game when in Game Over state |
| **`Esc`** | Exit game |

---

## 🎯 Game Over Conditions

* Touching the bottom ground floor.
* Colliding directly with an enemy target.

---

## 📁 File Structure

```text
drone_hunter/
├── main.py             # Main entry point, level system & rendering loop
├── settings.py         # Game parameters (gravity, speed, colors, resolution)
├── requirements.txt    # Dependencies (pygame-ce)
├── USAGE.txt           # Plain text instructions guide
├── README.md           # Markdown project guide
└── src/
    ├── player.py       # Player drone physics & aiming
    ├── bullet.py       # Trigonometric projectile trajectory
    ├── target.py       # Enemy target sprite & dynamic spawner with level scaling
    └── game_manager.py # State controller
```
