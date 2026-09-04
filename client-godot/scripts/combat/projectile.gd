class_name Projectile
extends Node2D

var target: Entity
var source: Entity
var damage := 0
var color := Color.WHITE
var effects: Array = []
var on_hit: Callable

func launch(p_source: Entity, p_target: Entity, p_damage: int, p_color: Color, p_effects: Array = []) -> void:
	source = p_source
	target = p_target
	damage = p_damage
	color = p_color
	effects = p_effects
	position = source.position
	z_index = 50
	var dist := position.distance_to(target.position)
	var tween := create_tween()
	tween.tween_property(self, "position", target.position, dist / 400.0)
	tween.tween_callback(_hit)

func _hit() -> void:
	if target != null and target.alive:
		target.take_damage(damage, source)
		JutsuExecutor.roll_effects(target, effects, source)
		if on_hit.is_valid():
			on_hit.call(target)
	queue_free()

func _draw() -> void:
	draw_circle(Vector2.ZERO, 4.0, color)
	draw_circle(Vector2.ZERO, 4.0, Color.BLACK, false, 1.0)
