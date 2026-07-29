# DroneStrike Prototype Usage Guide

## Requirements
- Godot Engine 4.4 installed
- The project root is `d:\AI_Projects\DroneStrike`

## Open the project
1. Launch Godot 4.4.
2. Click `Import` or `Open Existing Project`.
3. Select the folder `d:\AI_Projects\DroneStrike`.
4. Open the project.

## Run the game
- In the Godot editor, press the `Play Scene` button to test the current scene.
- Open `scenes/levels/Level01.tscn` and press `Play Scene` to run the first playable prototype level.
- To run the project from the project main scene, press `Play Project` or use `F5`.

## Input controls
- `move_up` → move up
- `move_down` → move down
- `move_left` → move left
- `move_right` → move right
- `fire` → shoot a missile

## Main prototype scenes
- `scenes/levels/Level01.tscn` — playable prototype level
- `scenes/player/Player.tscn` — player drone scene
- `scenes/camera/GameCamera.tscn` — reusable camera
- `scenes/weapons/Missile.tscn` — missile projectile
- `scenes/components/WeaponComponent.tscn` — weapon firing component

## Important files
- `project.godot` — Godot project file
- `assets/drones/drone_attack.png` — player drone sprite
- `assets/weapons/missile.png` — missile sprite
- `assets/tiles/level_tiles.tres` — TileSet resource for the level

## Run from command line (optional)
If you have the Godot CLI installed, run from the project folder:
```sh
cd d:\AI_Projects\DroneStrike
godot --path .
```

If Godot is not on your PATH, run the executable directly from the location on your machine. For example:
```sh
"C:\Users\DELL\Desktop\godot_drone_hunter\godot.exe" --path D:\AI_Projects\DroneStrike
```

To open the editor instead of running the game:
```sh
"C:\Users\DELL\Desktop\godot_drone_hunter\godot.exe" --path D:\AI_Projects\DroneStrike -e
```

## Notes
- Gameplay systems are currently limited to player movement, camera follow, missile spawning, and level geometry.
- Do not expect enemy or damage behavior yet.
