# 🛸 Unreal Engine 5 (UE5) AAA Setup Manual & Blueprint Guide

This guide details how to create and configure **Drone Hunter 3D** in **Unreal Engine 5** using C++ and Blueprints.

---

## 🛠️ Step 1: Create the Project in Unreal Engine 5

1. Open **Epic Games Launcher** -> Launch **Unreal Engine 5.3+**.
2. Under **New Project Categories**, select **Games** -> **Blank** (or **Third Person**).
3. Project Settings:
   - **C++** (or Blueprint)
   - **Desktop** / **Maximum Quality**
   - Project Name: `DroneHunter3D_UE5`
   - Project Path: `D:\AI_Projects\DroneHunter3D_UE5`
4. Click **Create**.

---

## 🛠️ Step 2: Add the C++ Source Files

Copy the pre-written C++ files into your project's `Source/DroneHunter3D_UE5/` directory:

- [DronePawn.h](file:///D:/AI_Projects/DroneHunter3D_UE5/Source/DronePawn.h)
- [DronePawn.cpp](file:///D:/AI_Projects/DroneHunter3D_UE5/Source/DronePawn.cpp)
- [GravityTetherComponent.h](file:///D:/AI_Projects/DroneHunter3D_UE5/Source/GravityTetherComponent.h)
- [GravityTetherComponent.cpp](file:///D:/AI_Projects/DroneHunter3D_UE5/Source/GravityTetherComponent.cpp)

---

## 🛠️ Step 3: Configure UE5 Input Mappings & Physics

### Input Mappings (Project Settings -> Engine -> Input)
Create the following Axis and Action mappings:

| Mapping Name | Type | Key / Controller Input | Scale / Action |
| :--- | :--- | :--- | :--- |
| `Thrust` | Axis | `SpaceBar` (`+1.0`), `Left Control` (`-1.0`) | Vertical Flight |
| `Pitch` | Axis | `W` (`+1.0`), `S` (`-1.0`) | Pitch Forward/Back |
| `Roll` | Axis | `D` (`+1.0`), `A` (`-1.0`) | Roll Left/Right |
| `Yaw` | Axis | `E` (`+1.0`), `Q` (`-1.0`) | Yaw Spin |
| `Boost` | Action | `Left Shift` | Timed Speed Multiplier |
| `Tether` | Action | `Right Mouse Button` / `G` | Lock / Launch Object |

---

## 🎨 Step 4: PBR Cyberpunk Rain Shader & Niagara VFX

1. **Lumen Wet Asphalt Puddle Material**:
   - Create Material `M_WetAsphalt`.
   - Set Roughness to `0.05` inside wet puddles for real-time Lumen reflections.
2. **Niagara Thruster Bloom (`FX_DroneThruster`)**:
   - Create Niagara System for cyan plasma thruster flames.
3. **UMG Tactical HUD (`WBP_TacticalHUD`)**:
   - Create UMG Widget Blueprint for the HUD overlay, target reticles, and loadout hangar.
