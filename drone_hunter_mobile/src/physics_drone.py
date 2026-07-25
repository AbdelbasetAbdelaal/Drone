"""
================================================================================
           DRONE HUNTER 3D - PHYSICS-BASED 3D DRONE FLIGHT CONTROLLER
================================================================================
A modular, physics-based 3D Quadcopter Flight Controller component using
real 3D RigidBody force vectors (ApplyForce & ApplyTorque), rotational inertia,
linear drag damping, and a timed Boost multiplier.

Features:
 1. RigidBody Forces (ApplyForce / ApplyTorque) for realistic weight & drift.
 2. 4-Axis Controls: Thrust (Up/Down), Roll (Left/Right), Pitch (Forward/Back), Yaw (Spin).
 3. Rotational Inertia & Damping (Linear Drag & Angular Drag).
 4. Timed Boost Mechanic (Multiplies thrust with duration timer & cooldown).
 5. Inspectable & Editable Configuration Properties for easy tuning.
"""

import math

class PhysicsDroneController3D:
    """Physics-based 3D RigidBody Drone Flight Controller."""
    def __init__(
        self,
        mass=1.2,                # RigidBody Mass (kg)
        thrust_force=45.0,       # Vertical Thrust Force (N)
        pitch_torque=18.0,       # Pitch Rotation Torque (N·m)
        roll_torque=18.0,        # Roll Rotation Torque (N·m)
        yaw_torque=12.0,         # Yaw Spinning Torque (N·m)
        linear_drag=2.4,         # Air Resistance Damping Factor
        angular_drag=4.5,        # Rotational Damping Factor
        boost_multiplier=2.0,    # Boost Thrust Speed Multiplier
        boost_duration=3.0,      # Maximum Boost Duration (sec)
        boost_cooldown=5.0       # Boost Recharge Cooldown (sec)
    ):
        # --- Inspectable / Editable Properties ---
        self.mass = mass
        self.thrust_force = thrust_force
        self.pitch_torque = pitch_torque
        self.roll_torque = roll_torque
        self.yaw_torque = yaw_torque
        self.linear_drag = linear_drag
        self.angular_drag = angular_drag
        self.boost_multiplier = boost_multiplier
        self.boost_duration = boost_duration
        self.boost_cooldown = boost_cooldown

        # --- RigidBody State Vectors ---
        self.position = [0.0, 4.0, 0.0]       # [X, Y, Z] World Position
        self.velocity = [0.0, 0.0, 0.0]       # [VX, VY, VZ] Linear Velocity
        self.rotation = [0.0, 0.0, 0.0]       # [Pitch, Yaw, Roll] Euler Angles in Radians
        self.angular_velocity = [0.0, 0.0, 0.0] # [WX, WY, WZ] Angular Velocity

        # --- Boost System State ---
        self.is_boosting = False
        self.boost_timer = 0.0
        self.cooldown_timer = 0.0

    def apply_force(self, force_x, force_y, force_z):
        """Applies a 3D Linear Force vector F (a = F / m)."""
        ax = force_x / self.mass
        ay = force_y / self.mass
        az = force_z / self.mass
        self.velocity[0] += ax
        self.velocity[1] += ay
        self.velocity[2] += az

    def apply_torque(self, torque_pitch, torque_yaw, torque_roll):
        """Applies a 3D Rotational Torque vector Tau (alpha = Tau / I)."""
        inertia_pitch_roll = 0.5 * self.mass
        inertia_yaw = 0.8 * self.mass
        self.angular_velocity[0] += torque_pitch / inertia_pitch_roll
        self.angular_velocity[1] += torque_yaw / inertia_yaw
        self.angular_velocity[2] += torque_roll / inertia_pitch_roll

    def trigger_boost(self):
        """Triggers the timed Boost mechanic."""
        if not self.is_boosting and self.cooldown_timer <= 0:
            self.is_boosting = True
            self.boost_timer = self.boost_duration
            return True
        return False

    def update(self, dt, input_thrust, input_pitch, input_roll, input_yaw, input_boost=False):
        """
        Physics Step Update.
        inputs expected in range [-1.0, 1.0].
        """
        # 1. Update Boost Timers
        if input_boost and self.cooldown_timer <= 0:
            self.trigger_boost()

        effective_thrust_mult = 1.0
        if self.is_boosting:
            self.boost_timer -= dt
            effective_thrust_mult = self.boost_multiplier
            if self.boost_timer <= 0:
                self.is_boosting = False
                self.cooldown_timer = self.boost_cooldown
        elif self.cooldown_timer > 0:
            self.cooldown_timer -= dt

        # 2. Compute 3D Thrust Force Vector relative to drone pitch/roll orientation
        curr_pitch, curr_yaw, curr_roll = self.rotation[0], self.rotation[1], self.rotation[2]
        
        # Thrust Direction calculation
        total_thrust = input_thrust * self.thrust_force * effective_thrust_mult
        
        # Transform local thrust into World Space (X, Y, Z)
        fx = total_thrust * math.sin(curr_roll)
        fy = total_thrust * math.cos(curr_pitch) * math.cos(curr_roll)
        fz = total_thrust * math.sin(curr_pitch)

        self.apply_force(fx * dt, fy * dt, fz * dt)

        # 3. Compute Rotational Torques (Pitch, Yaw, Roll)
        t_pitch = input_pitch * self.pitch_torque * dt
        t_yaw = input_yaw * self.yaw_torque * dt
        t_roll = input_roll * self.roll_torque * dt

        self.apply_torque(t_pitch, t_yaw, t_roll)

        # 4. Apply Linear & Angular Drag (Air Resistance Damping)
        for i in range(3):
            self.velocity[i] -= self.velocity[i] * self.linear_drag * dt
            self.angular_velocity[i] -= self.angular_velocity[i] * self.angular_drag * dt

        # 5. Integrate Velocities -> Position & Rotation
        for i in range(3):
            self.position[i] += self.velocity[i] * dt
            self.rotation[i] += self.angular_velocity[i] * dt

        # Bound position inside playable zone
        self.position[0] = max(-24.0, min(24.0, self.position[0]))
        self.position[1] = max(-2.0, min(26.0, self.position[1]))
        self.position[2] = max(-8.0, min(60.0, self.position[2]))

    def get_degrees(self):
        """Returns pitch, yaw, roll in degrees for visual rendering."""
        return (
            math.degrees(self.rotation[0]),
            math.degrees(self.rotation[1]),
            math.degrees(self.rotation[2])
        )
