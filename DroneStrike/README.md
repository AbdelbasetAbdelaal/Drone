# DroneStrike Prototype

This is the first playable prototype for the 2D top-down Godot 4.4 game `DroneStrike`.

## How to use
- Open the project in Godot 4.4 using the `project.godot` file.
- See `docs/USAGE.md` for detailed run instructions and controls.

## Key scenes
- `scenes/levels/Level01.tscn` — playable prototype level
- `scenes/player/Player.tscn` — player drone scene
- `scenes/weapons/Missile.tscn` — projectile scene
- `scenes/components/WeaponComponent.tscn` — generic weapon component
- `scenes/camera/GameCamera.tscn` — reusable camera component

## Notes
- The prototype includes player movement, camera follow, missile firing, and a small tiled level.
- Enemy, damage, and explosion systems are not implemented yet.
