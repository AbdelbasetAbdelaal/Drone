"""
================================================================================
           DRONE HUNTER 3D - GRAVITY-TETHER MECHANIC COMPONENT
================================================================================
A modular 3D Gravity-Tether System component implementing:
 1. 3D SphereCast / Raycast detection up to max_reach_distance for "Draggable" objects.
 2. Object snapping and lock-on offset in front of the drone during flight.
 3. High-impulse launching towards the camera/aim vector upon release.
 4. Anti-clipping collision bounds preventing mesh overlap with the drone.
"""

import math

class DraggableObject3D:
    """Represents a physics object tagged as 'Draggable' in the 3D scene."""
    def __init__(self, obj_id, x, y, z, radius=1.5, mass=3.0, tag="Draggable"):
        self.obj_id = obj_id
        self.x = x
        self.y = y
        self.z = z
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.radius = radius
        self.mass = mass
        self.tag = tag
        self.is_tethered = False

    def update(self, dt):
        if not self.is_tethered:
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.z += self.vz * dt
            # Damping air resistance
            self.vx *= (1.0 - 1.2 * dt)
            self.vy *= (1.0 - 1.2 * dt)
            self.vz *= (1.0 - 1.2 * dt)


class GravityTetherSystem:
    """3D Gravity Tether Component handling object detection, tether lock, and launching."""
    def __init__(
        self,
        max_reach_distance=35.0,     # Max SphereCast detection range (units)
        spherecast_radius=4.0,       # SphereCast beam radius
        hold_offset=(0.0, -0.5, 4.5),# Lock offset relative to drone (X, Y, Z)
        launch_force=120.0,          # Forward impulse launch force
        snap_speed=18.0,             # Smooth lerp snap speed toward hold offset
        min_safe_distance=2.5,       # Anti-clipping collision padding distance
        tag_filter="Draggable"       # Tag filter for target detection
    ):
        # --- Inspectable / Editable Properties ---
        self.max_reach_distance = max_reach_distance
        self.spherecast_radius = spherecast_radius
        self.hold_offset = hold_offset
        self.launch_force = launch_force
        self.snap_speed = snap_speed
        self.min_safe_distance = min_safe_distance
        self.tag_filter = tag_filter

        # --- Tether State ---
        self.tethered_object = None
        self.beam_active = False
        self.beam_timer = 0.0

    def sphere_cast(self, origin_x, origin_y, origin_z, aim_dir_x, aim_dir_y, aim_dir_z, scene_objects):
        """
        Casts a 3D SphereCast forward along aiming vector to detect nearest object tagged 'Draggable'.
        """
        closest_obj = None
        min_dist = self.max_reach_distance

        for obj in scene_objects:
            if getattr(obj, "tag", None) != self.tag_filter and not hasattr(obj, "hp"):
                continue

            # Vector from ray origin to object position
            dx = obj.x - origin_x
            dy = obj.y - origin_y
            dz = obj.z - origin_z
            dist = math.hypot(dx, dy, dz)

            if dist > self.max_reach_distance:
                continue

            # Project object onto aiming direction vector
            dot_prod = (dx * aim_dir_x + dy * aim_dir_y + dz * aim_dir_z)
            if dot_prod <= 0:
                continue # Behind the drone raycast

            # Distance perpendicular to ray path
            perp_dist_sq = max(0.0, dist**2 - dot_prod**2)
            perp_dist = math.sqrt(perp_dist_sq)

            if perp_dist <= (self.spherecast_radius + getattr(obj, "radius", 1.0)):
                if dist < min_dist:
                    min_dist = dist
                    closest_obj = obj

        return closest_obj

    def toggle_tether(self, drone_x, drone_y, drone_z, aim_dir_x, aim_dir_y, aim_dir_z, scene_objects):
        """
        Interacts with Tether:
        - If holding an object: Launches object forward toward aim vector.
        - If not holding: Casts SphereCast to tether nearest Draggable object.
        """
        if self.tethered_object:
            # Launch Object Forward with Impulse Force
            obj = self.tethered_object
            obj.is_tethered = False
            
            # Apply Impulse F_launch / mass toward aiming vector
            impulse_speed = self.launch_force / getattr(obj, "mass", 3.0)
            obj.vx = aim_dir_x * impulse_speed
            obj.vy = aim_dir_y * impulse_speed
            obj.vz = aim_dir_z * impulse_speed

            self.tethered_object = None
            self.beam_active = False
            return "LAUNCHED"

        else:
            # SphereCast Detection
            target = self.sphere_cast(drone_x, drone_y, drone_z, aim_dir_x, aim_dir_y, aim_dir_z, scene_objects)
            if target:
                self.tethered_object = target
                target.is_tethered = True
                self.beam_active = True
                self.beam_timer = 0.5
                return "LATCHED"

        return "NONE"

    def update(self, dt, drone_x, drone_y, drone_z):
        """
        Updates tethered object position & anti-clipping collision bounds.
        """
        if self.beam_timer > 0:
            self.beam_timer -= dt

        if self.tethered_object:
            obj = self.tethered_object
            
            # Compute Target Lock Position in front of Drone
            target_x = drone_x + self.hold_offset[0]
            target_y = drone_y + self.hold_offset[1]
            target_z = drone_z + self.hold_offset[2]

            # Anti-Clipping Collision Check: Enforce minimum safe distance from Drone Mesh
            dist_from_drone = math.hypot(target_x - drone_x, target_y - drone_y, target_z - drone_z)
            min_allowed = self.min_safe_distance + getattr(obj, "radius", 1.0)
            
            if dist_from_drone < min_allowed:
                # Push forward along Z to prevent clipping
                target_z = drone_z + min_allowed

            # Smoothly lerp object position toward target offset
            obj.x += (target_x - obj.x) * self.snap_speed * dt
            obj.y += (target_y - obj.y) * self.snap_speed * dt
            obj.z += (target_z - obj.z) * self.snap_speed * dt
