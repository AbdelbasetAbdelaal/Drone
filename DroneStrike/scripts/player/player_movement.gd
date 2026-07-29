extends RefCounted
class_name PlayerMovement

# Modular movement component for the player character.
# This keeps motion logic separate from the CharacterBody2D node.

@export var max_speed: float = 250.0
@export var acceleration: float = 800.0
@export var friction: float = 1000.0

func compute_input_vector() -> Vector2:
    return Vector2(
        Input.get_action_strength("move_right") - Input.get_action_strength("move_left"),
        Input.get_action_strength("move_down") - Input.get_action_strength("move_up")
    )

func update_body(body: CharacterBody2D, delta: float) -> void:
    var input_vector := compute_input_vector()

    if input_vector != Vector2.ZERO:
        input_vector = input_vector.normalized()
        body.velocity = body.velocity.move_toward(input_vector * max_speed, acceleration * delta)
        body.rotation = input_vector.angle() + deg_to_rad(90)
    else:
        body.velocity = body.velocity.move_toward(Vector2.ZERO, friction * delta)
