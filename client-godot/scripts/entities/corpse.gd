## Corpo de monstro com loot. Não bloqueia a célula. Some após 60s.
class_name Corpse
extends Node2D

var cell: Vector2i
var items: Array = []  # {id, qty}
var ryo := 0
var monster_name := ""

func setup(p_cell: Vector2i, p_name: String, p_items: Array, p_ryo: int, world: GameWorld) -> void:
	cell = p_cell
	monster_name = p_name
	items = p_items
	ryo = p_ryo
	position = world.cell_to_world(cell)
	z_index = -1
	get_tree().create_timer(60.0).timeout.connect(func() -> void:
		world.corpses.erase(cell)
		queue_free())

func is_empty() -> bool:
	return items.is_empty() and ryo == 0

func _draw() -> void:
	draw_rect(Rect2(-12, -8, 24, 16), Color("3b2a22"))
	draw_rect(Rect2(-12, -8, 24, 16), Color.BLACK, false, 1.0)
	if not is_empty():
		draw_circle(Vector2(8, -6), 3.0, Color.GOLD)
