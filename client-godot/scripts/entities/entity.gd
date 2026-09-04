## Base de tudo que ocupa uma célula do grid e tem HP.
class_name Entity
extends Node2D

signal died(entity: Entity)
signal damaged(entity: Entity, amount: int)

var world: GameWorld
var cell: Vector2i
var facing := Vector2i.DOWN
var hp := 1
var max_hp := 1
var defense := 0
var speed_tiles_s := 4.0
var is_moving := false
var alive := true
var invulnerable := false
var display_name := "Entidade":
	set(v):
		display_name = v
		if _name_label != null:
			_name_label.text = v
var color := Color.WHITE
var statuses: Array = []  # {type, remaining, value, tick_acc}

var _name_label: Label

func setup(p_world: GameWorld, p_cell: Vector2i) -> void:
	world = p_world
	cell = p_cell
	position = world.cell_to_world(cell)
	world.occupy(self, cell)

func _ready() -> void:
	_name_label = Label.new()
	_name_label.text = display_name
	_name_label.position = Vector2(-40, -36)
	_name_label.size = Vector2(80, 14)
	_name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_name_label.add_theme_font_size_override("font_size", 10)
	_name_label.add_theme_color_override("font_outline_color", Color.BLACK)
	_name_label.add_theme_constant_override("outline_size", 3)
	add_child(_name_label)
	queue_redraw()

func _process(delta: float) -> void:
	_tick_statuses(delta)

# ---------- movimento ----------
func can_move() -> bool:
	return alive and not has_status("stun") and not has_status("paralyze")

func can_act() -> bool:
	return alive and not has_status("stun")

func speed_multiplier() -> float:
	var m := 1.0
	for s in statuses:
		if s["type"] == "slow":
			m *= 1.0 - float(s["value"])
	return maxf(0.2, m)

func try_move(dir: Vector2i) -> bool:
	if is_moving or not can_move() or dir == Vector2i.ZERO:
		return false
	facing = dir
	queue_redraw()
	var target := cell + dir
	if not world.is_free(target):
		return false
	world.move_entity(self, cell, target)
	cell = target
	is_moving = true
	var tween := create_tween()
	tween.tween_property(self, "position", world.cell_to_world(target), 1.0 / (speed_tiles_s * speed_multiplier()))
	tween.finished.connect(func() -> void: is_moving = false)
	return true

func teleport(to: Vector2i) -> bool:
	if not world.is_free(to):
		return false
	world.move_entity(self, cell, to)
	cell = to
	position = world.cell_to_world(to)
	return true

func face_towards(other: Entity) -> void:
	var d := other.cell - cell
	if abs(d.x) >= abs(d.y):
		facing = Vector2i(signi(d.x), 0)
	else:
		facing = Vector2i(0, signi(d.y))
	queue_redraw()

func chebyshev_to(other: Entity) -> int:
	var d := (other.cell - cell).abs()
	return maxi(d.x, d.y)

# ---------- dano e status ----------
func take_damage(amount: int, _source: Entity, text_color: Color = Color("ff5252")) -> void:
	if not alive or invulnerable:
		return
	hp = maxi(0, hp - amount)
	damaged.emit(self, amount)
	world.spawn_floating_text(position + Vector2(0, -20), str(amount), text_color)
	queue_redraw()
	if hp == 0:
		alive = false
		statuses.clear()
		died.emit(self)

func heal(amount: int) -> void:
	hp = mini(max_hp, hp + amount)
	queue_redraw()

func apply_effect(effect: Dictionary, _source: Entity) -> void:
	var t: String = effect["type"]
	var dur := float(effect.get("duration_s", 0))
	var val := float(effect.get("value", 0))
	for s in statuses:
		if s["type"] == t:
			s["remaining"] = maxf(float(s["remaining"]), dur)
			s["value"] = maxf(float(s["value"]), val)
			return
	statuses.append({"type": t, "remaining": dur, "value": val, "tick_acc": 0.0})
	queue_redraw()

func has_status(t: String) -> bool:
	for s in statuses:
		if s["type"] == t:
			return true
	return false

func cure(t: String) -> void:
	statuses = statuses.filter(func(s: Dictionary) -> bool: return s["type"] != t)

func _tick_statuses(delta: float) -> void:
	if statuses.is_empty() or not alive:
		return
	for s in statuses.duplicate():
		s["remaining"] = float(s["remaining"]) - delta
		s["tick_acc"] = float(s["tick_acc"]) + delta
		if float(s["tick_acc"]) >= 1.0:
			s["tick_acc"] = float(s["tick_acc"]) - 1.0
			match s["type"]:
				"burn": take_damage(int(s["value"]), null, Color("ff9a3c"))
				"poison": take_damage(int(s["value"]), null, Color("7dd85a"))
				"heal_over_time":
					heal(int(s["value"]))
					world.spawn_floating_text(position + Vector2(0, -20), "+" + str(int(s["value"])), Color("6cf27a"))
		if float(s["remaining"]) <= 0.0:
			statuses.erase(s)
	queue_redraw()

func _draw() -> void:
	draw_rect(Rect2(-14, -14, 28, 28), color)
	draw_rect(Rect2(-14, -14, 28, 28), Color.BLACK, false, 2.0)
	draw_circle(Vector2(facing) * 9.0, 3.0, Color.BLACK)
	var ratio := float(hp) / float(max_hp)
	draw_rect(Rect2(-14, -22, 28, 4), Color(0, 0, 0, 0.7))
	draw_rect(Rect2(-14, -22, 28.0 * ratio, 4), Color.GREEN if ratio > 0.3 else Color.RED)
	var x := -14.0
	for s in statuses:
		var c := Color.WHITE
		match s["type"]:
			"burn": c = Color.ORANGE
			"poison": c = Color.GREEN
			"slow": c = Color.SKY_BLUE
			"stun", "paralyze": c = Color.YELLOW
			"heal_over_time": c = Color.LIGHT_GREEN
		draw_rect(Rect2(x, 16, 6, 6), c)
		x += 8
	if invulnerable:
		draw_rect(Rect2(-16, -16, 32, 32), Color.WHITE, false, 2.0)
