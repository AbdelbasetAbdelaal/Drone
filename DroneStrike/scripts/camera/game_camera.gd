extends Camera2D

# Use a generic NodePath so the camera can follow any Node2D in the scene.
@export var follow_speed: float = 5.0
@export var zoom_level: Vector2 = Vector2.ONE
@export var target_path: NodePath = NodePath()

var _target: Node2D

func _ready() -> void:
    zoom = zoom_level
    if target_path != NodePath():
        set_target(get_node_or_null(target_path))

func _process(delta: float) -> void:
    if _target:
        position = position.lerp(_target.global_position, clamp(follow_speed * delta, 0.0, 1.0))

func set_target(target: Node2D) -> void:
    _target = target
