extends Node

enum FireMode {
    SINGLE,
    BURST,
    AUTO
}

@export var fire_rate: float = 1.0
@export var projectile_scene: PackedScene
@export var muzzle_path: NodePath = NodePath()
@export var fire_mode: FireMode = FireMode.SINGLE
@export var burst_count: int = 3
@export var burst_delay: float = 0.1

var _cooldown: float = 0.0
var _burst_shots_left: int = 0
var _burst_timer: float = 0.0

func _ready() -> void:
    set_process(true)

func _process(delta: float) -> void:
    if _cooldown > 0.0:
        _cooldown = max(_cooldown - delta, 0.0)

    if _burst_timer > 0.0:
        _burst_timer = max(_burst_timer - delta, 0.0)
        if _burst_timer == 0.0 and _burst_shots_left > 0:
            _burst_shots_left -= 1
            _burst_timer = burst_delay
            _fire_projectile()

func fire() -> void:
    if fire_mode == FireMode.SINGLE:
        _try_fire_single()
        return

    if fire_mode == FireMode.BURST:
        _start_burst()
        return

    if fire_mode == FireMode.AUTO:
        _try_fire_single()
        return

func _try_fire_single() -> void:
    if _cooldown > 0.0:
        return
    _fire_projectile()
    _cooldown = _get_cooldown_duration()

func _start_burst() -> void:
    if _cooldown > 0.0:
        return
    _burst_shots_left = burst_count
    _burst_timer = 0.0
    _try_fire_single()
    _cooldown = _get_cooldown_duration()

func _fire_projectile() -> void:
    if projectile_scene == null:
        return

    var projectile = projectile_scene.instantiate()
    var spawn_parent := _get_spawn_parent()
    if projectile is Node2D:
        var spawn_position := _get_muzzle_position()
        if spawn_position != null:
            projectile.global_position = spawn_position
    spawn_parent.add_child(projectile)

func _get_spawn_parent() -> Node:
    return get_parent() if get_parent() else get_tree().get_current_scene() if get_tree().get_current_scene() else self

func _get_muzzle_position() -> Vector2:
    if muzzle_path == NodePath():
        return null
    var muzzle = get_node_or_null(muzzle_path)
    if muzzle is Node2D:
        return muzzle.global_position
    return null

func _get_cooldown_duration() -> float:
    return fire_rate > 0.0 ? 1.0 / fire_rate : 0.0