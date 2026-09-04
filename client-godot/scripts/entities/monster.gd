class_name Monster
extends Entity

enum State { IDLE, CHASE, ATTACK, FLEE }

var data: Dictionary
var monster_id := ""
var spawn_cell: Vector2i
var state := State.IDLE
var aggro_range := 5
var attack_range := 1
var behavior := "aggressive"
var xp_value := 0
var respawn_s := 30
var attacks: Array = []
var temporary := false        # invocado por boss: não respawna
var attack_multiplier := 1.0
var _phase_index := 0
var _attack_timers: Array[float] = []
var _lost_timer := 0.0
var _wander_timer := 0.0
var _flee_timer := 0.0
var _distract_timer := 0.0
var rng := RandomNumberGenerator.new()

func init_from_data(id: String) -> void:
	monster_id = id
	data = GameData.monsters[id]
	display_name = data["name"]
	max_hp = int(data["hp"])
	hp = max_hp
	defense = int(data["defense"])
	speed_tiles_s = float(data["speed"])
	aggro_range = int(data["aggro_range"])
	attack_range = int(data["attack_range"])
	behavior = data["behavior"]
	xp_value = int(data["xp"])
	respawn_s = int(data["respawn_s"])
	attacks = data["attacks"]
	_attack_timers.clear()
	for a in attacks:
		_attack_timers.append(0.0)
	color = _color_for(id)
	rng.randomize()

func is_boss() -> bool:
	return bool(data.get("boss", false))

func _color_for(id: String) -> Color:
	match id:
		"wolf": return Color("8a8a8a")
		"bandit": return Color("7a3e2e")
		"forest_snake": return Color("3aa64a")
		"bandit_archer": return Color("5a3a7a")
		"boss_bandit_chief": return Color("b01818")
		"leech": return Color("6a2a4a")
		"giant_toad": return Color("6a8a2a")
		"rogue_ninja": return Color("2a2a3a")
		"boss_elder_toad": return Color("3a6a1a")
	return Color.MAGENTA

func distract(seconds: float) -> void:
	_distract_timer = seconds
	state = State.IDLE

func _process(delta: float) -> void:
	super._process(delta)
	if not alive or not can_act() or world.player == null:
		return
	if _distract_timer > 0.0:
		_distract_timer -= delta
		_wander(delta)
		return
	var player := world.player
	for i in _attack_timers.size():
		_attack_timers[i] = maxf(0.0, _attack_timers[i] - delta)
	var dist := chebyshev_to(player) if player.alive else 999
	match state:
		State.IDLE:
			_wander(delta)
			if behavior != "passive" and dist <= aggro_range and (dist <= 2 or world.map.has_line_of_sight(cell, player.cell)):
				state = State.CHASE
				if is_boss():
					world.hud.log_msg("[color=red]%s te viu![/color]" % display_name)
		State.CHASE:
			if dist > aggro_range + 3 or not player.alive:
				_lost_timer += delta
				if _lost_timer > 5.0:
					_lost_timer = 0.0
					state = State.IDLE
			else:
				_lost_timer = 0.0
			if _should_flee():
				_flee_timer = 5.0
				state = State.FLEE
			elif dist <= attack_range and _has_line(player):
				state = State.ATTACK
			elif not is_moving:
				_step_towards(player.cell)
		State.ATTACK:
			if not player.alive:
				state = State.IDLE
			elif _should_flee():
				_flee_timer = 5.0
				state = State.FLEE
			elif dist > attack_range or not _has_line(player):
				state = State.CHASE
			else:
				face_towards(player)
				_try_attack(player)
		State.FLEE:
			_flee_timer -= delta
			if not is_moving:
				_step_towards(cell + (cell - player.cell))
			if _flee_timer <= 0.0:
				state = State.CHASE

func _should_flee() -> bool:
	return behavior == "cowardly" and hp < max_hp * 0.2 and _flee_timer <= 0.0

func _has_line(p: Entity) -> bool:
	if chebyshev_to(p) <= 1:
		return true
	return world.map.has_line_of_sight(cell, p.cell)

func _wander(delta: float) -> void:
	_wander_timer -= delta
	if _wander_timer <= 0.0:
		_wander_timer = rng.randf_range(1.5, 4.0)
		if rng.randf() < 0.6:
			var dirs := [Vector2i.UP, Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT]
			var d: Vector2i = dirs[rng.randi_range(0, 3)]
			if (cell + d - spawn_cell).length() <= 4.0:
				try_move(d)

func _step_towards(goal: Vector2i) -> void:
	var d := goal - cell
	if d == Vector2i.ZERO:
		return
	var primary := Vector2i(signi(d.x), 0) if abs(d.x) >= abs(d.y) else Vector2i(0, signi(d.y))
	var secondary := Vector2i(0, signi(d.y)) if primary.x != 0 else Vector2i(signi(d.x), 0)
	if try_move(primary):
		return
	if secondary != Vector2i.ZERO and try_move(secondary):
		return
	var perp := Vector2i(primary.y, primary.x)
	if not try_move(perp):
		try_move(-perp)

func _try_attack(p: Entity) -> void:
	var dist := chebyshev_to(p)
	for i in attacks.size():
		if _attack_timers[i] > 0.0:
			continue
		var a: Dictionary = attacks[i]
		if a["type"] == "melee" and dist > 1:
			continue
		_attack_timers[i] = float(a["cooldown_s"])
		var raw := rng.randi_range(int(a["damage_min"]), int(a["damage_max"])) * attack_multiplier
		var dmg := maxi(1, int(raw) - int(p.defense * 0.5))
		var effects: Array = a.get("effects", [])
		match a["type"]:
			"projectile":
				world.spawn_projectile(self, p, dmg, Color("d9c26b"), effects)
			"area":
				var cells := Shapes.cells(a.get("shape", "circle_r1"), cell, facing)
				world.spawn_area_flash(cells, Color(color, 0.8))
				if p.cell in cells:
					p.take_damage(dmg, self)
					JutsuExecutor.roll_effects(p, effects, self)
			_:
				p.take_damage(dmg, self)
				JutsuExecutor.roll_effects(p, effects, self)
		return

func take_damage(amount: int, source: Entity, text_color: Color = Color("ff5252")) -> void:
	super.take_damage(amount, source, text_color)
	if alive:
		_check_phase()

func _check_phase() -> void:
	var phases: Array = data.get("phases", [])
	while _phase_index < phases.size():
		var ph: Dictionary = phases[_phase_index]
		if float(hp) / float(max_hp) * 100.0 > float(ph["hp_percent"]):
			break
		_phase_index += 1
		if ph.has("attack_multiplier"):
			attack_multiplier = float(ph["attack_multiplier"])
		if ph.has("message"):
			world.hud.log_msg("[color=red]%s: \"%s\"[/color]" % [display_name, ph["message"]])
		for s in ph.get("summons", []):
			for k in int(s.get("count", 1)):
				world.spawn_temporary_monster(s["monster_id"], cell)

func reset_for_respawn() -> void:
	hp = max_hp
	alive = true
	state = State.IDLE
	visible = true
	_flee_timer = 0.0
	_phase_index = 0
	attack_multiplier = 1.0
	statuses.clear()
	cell = spawn_cell
	position = world.cell_to_world(cell)
	world.occupy(self, cell)
	queue_redraw()
