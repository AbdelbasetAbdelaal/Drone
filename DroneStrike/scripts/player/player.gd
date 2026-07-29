extends CharacterBody2D

const ROTATION_OFFSET: float = deg_to_rad(90.0)
const ZERO_VECTOR: Vector2 = Vector2.ZERO

@export var max_speed: float = 250.0
@export var acceleration: float = 800.0
@export var friction: float = 900.0

var _direction: Vector2 = Vector2.ZERO
@onready var _weapon_component: Node = $WeaponComponent

func _physics_process(delta: float) -> void:
    # Reuse a single Vector2 to avoid allocating a new direction every frame.
    _direction.x = Input.get_action_strength("move_right") - Input.get_action_strength("move_left")
    _direction.y = Input.get_action_strength("move_down") - Input.get_action_strength("move_up")

    if _direction != ZERO_VECTOR:
        _direction = _direction.normalized()
        velocity = velocity.move_toward(_direction * max_speed, acceleration * delta)
        rotation = _direction.angle() + ROTATION_OFFSET
    else:
        velocity = velocity.move_toward(ZERO_VECTOR, friction * delta)

    if Input.is_action_just_pressed("fire") and _weapon_component:
        _weapon_component.fire()

    move_and_slide()