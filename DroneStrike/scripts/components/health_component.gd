extends Node

signal health_changed(current: float, max: float)
signal died()

@export var max_health: float = 100.0
var current_health: float

func _ready() -> void:
    current_health = max_health
    emit_signal("health_changed", current_health, max_health)

func take_damage(amount: float) -> void:
    current_health = clamp(current_health - amount, 0.0, max_health)
    emit_signal("health_changed", current_health, max_health)
    if current_health == 0.0:
        emit_signal("died")

func heal(amount: float) -> void:
    current_health = clamp(current_health + amount, 0.0, max_health)
    emit_signal("health_changed", current_health, max_health)

func is_dead() -> bool:
    return current_health <= 0.0