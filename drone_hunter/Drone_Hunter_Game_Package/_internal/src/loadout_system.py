"""
================================================================================
          DRONE HUNTER 3D - LOADOUT & WEAPON MANAGEMENT SYSTEM
================================================================================
A modular Data Architecture and Loadout System implementing:
 1. DroneDataAsset container storing Speed, Shield, Weapon Type, and Energy.
 2. WeaponSystem3D handling firing logic & World-to-Screen target reticle HUD projection.
 3. DroneEventSystem signal/observer system updating stats & visuals on module swap.
"""

import math
import pygame
from src.engine3d import project_3d


class DroneDataAsset:
    """Data Container Asset storing inspectable drone stats and equipped modules."""
    def __init__(
        self,
        speed=18.0,
        shield_capacity=100.0,
        equipped_weapon_type="PLASMA_CANNON",
        energy_level=100.0
    ):
        self.speed = speed
        self.shield_capacity = shield_capacity
        self.equipped_weapon_type = equipped_weapon_type
        self.energy_level = energy_level
        self.max_energy = 100.0
        self.installed_modules = {
            "ENGINE_SLOT": "Phase-Rotor Hybrid",
            "SHIELD_SLOT": "Singularity Core",
            "WEAPON_SLOT": "Plasma Cannon"
        }

    def to_dict(self):
        return {
            "speed": self.speed,
            "shield_capacity": self.shield_capacity,
            "equipped_weapon_type": self.equipped_weapon_type,
            "energy_level": self.energy_level,
            "installed_modules": self.installed_modules
        }


class DroneEventSystem:
    """Event / Signal System notifying listeners when modules are swapped."""
    def __init__(self):
        self._module_swapped_listeners = []

    def subscribe_module_swapped(self, callback):
        self._module_swapped_listeners.append(callback)

    def notify_module_swapped(self, slot_name, module_name, new_stats):
        for callback in self._module_swapped_listeners:
            callback(slot_name, module_name, new_stats)


class WeaponSystem3D:
    """Weapon Management Component handling firing logic & HUD Target Reticle Projection."""
    def __init__(self, data_asset):
        self.data_asset = data_asset
        self.cooldown_timer = 0.0

    def can_fire(self):
        return self.cooldown_timer <= 0 and self.data_asset.energy_level >= 5.0

    def update(self, dt):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt

    def fire(self, origin_pos, aim_dir, player_bullets, homing_missiles, targets):
        """Fires weapon according to data asset's equipped_weapon_type."""
        if not self.can_fire():
            return False

        w_type = self.data_asset.equipped_weapon_type
        self.data_asset.energy_level = max(0.0, self.data_asset.energy_level - 5.0)

        if w_type == "PLASMA_CANNON":
            self.cooldown_timer = 0.18
            return "PLASMA_FIRED"

        elif w_type == "HOMING_MISSILES":
            self.cooldown_timer = 1.20
            return "MISSILES_FIRED"

        elif w_type == "GRAVITY_TETHER":
            self.cooldown_timer = 0.40
            return "TETHER_FIRED"

        return False

    def project_reticle_to_hud(self, surface, target_3d_pos, font_reticle=None):
        """
        Projects 3D Target Coordinates -> 2D Screen HUD Reticle (World-to-Screen Projection).
        """
        proj = project_3d(target_3d_pos[0], target_3d_pos[1], target_3d_pos[2])
        if not proj:
            return None # Target behind camera frustum

        sx, sy, scale = proj
        r_size = max(14, int(26 * (scale / 40.0)))
        
        # Draw HUD Target Lock Reticle Box & Crosshairs
        pygame.draw.rect(surface, (239, 68, 68), (sx - r_size, sy - r_size, r_size * 2, r_size * 2), 2)
        pygame.draw.line(surface, (245, 158, 11), (sx - r_size - 6, sy), (sx + r_size + 6, sy), 1)
        pygame.draw.line(surface, (245, 158, 11), (sx, sy - r_size - 6), (sx, sy + r_size + 6), 1)

        if font_reticle:
            dist_str = f"LOCK [{int(target_3d_pos[2])}m]"
            txt = font_reticle.render(dist_str, True, (239, 68, 68))
            surface.blit(txt, (sx - txt.get_width() // 2, sy + r_size + 4))

        return (sx, sy)


class LoadoutManager:
    """Loadout Manager coordinating DataAsset, WeaponSystem, and Event Signals."""
    def __init__(self):
        self.data_asset = DroneDataAsset()
        self.weapon_system = WeaponSystem3D(self.data_asset)
        self.event_system = DroneEventSystem()
        
        # Subscribe internal handler
        self.event_system.subscribe_module_swapped(self._on_module_changed)

    def equip_module(self, slot_name, module_name, speed_delta=0.0, shield_delta=0.0, new_weapon_type=None):
        """Equips/swaps a module, updating stats and emitting event signal."""
        self.data_asset.installed_modules[slot_name] = module_name
        self.data_asset.speed += speed_delta
        self.data_asset.shield_capacity += shield_delta
        if new_weapon_type:
            self.data_asset.equipped_weapon_type = new_weapon_type

        # Emit Signal
        self.event_system.notify_module_swapped(slot_name, module_name, self.data_asset.to_dict())

    def _on_module_changed(self, slot_name, module_name, new_stats):
        """Internal callback responding to module swap events."""
        pass
