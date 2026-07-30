extends Area2D

signal hit(body)

@export var speed: float = 600.0
@export var damage: float = 25.0
@export var lifetime: float = 8.0

var _lifetime_timer: SceneTreeTimer

func _ready() -> void:
    _lifetime_timer = get_tree().create_timer(lifetime)
    _lifetime_timer.connect("timeout", Callable(self, "_on_lifetime_timeout"))
    connect("body_entered", Callable(self, "_on_body_entered"))

func _physics_process(delta: float) -> void:
    position += transform.x * speed * delta

func _on_lifetime_timeout() -> void:
    queue_free()

func _on_body_entered(body: Node) -> void:
    emit_signal("hit", body)
    queue_free()
