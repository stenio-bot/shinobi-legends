class_name Player
extends Entity

signal stats_changed
signal target_changed(target: Entity)
signal jutsus_changed

const EQUIP_SLOTS := ["head", "body", "legs", "feet", "weapon", "offhand", "accessory1", "accessory2", "back"]

var level := 1
var xp := 0
var chakra := 0
var max_chakra := 0
var ryo := 0
var weapon_attack := 0
var weapon_class := "melee"
var weapon_range := 1
var weapon_skill := "taijutsu"
var crit_chance := 0.05
var skill_bonus: Dictionary = {}
var bonus: Dictionary = {}
var village_id := "leaf"

var skills: SkillSystem
var inventory: Inventory
var equipment: Dictionary = {}  # slot -> item_id
var known_jutsus: Array = []
var hotbar: Array = []           # 10 posições: jutsu_id ou ""
var cooldowns: Dictionary = {}   # jutsu_id -> segundos restantes
var quests: Dictionary = {}      # quest_id -> {state: active|done, progress}
var _overweight_warned := false

var target: Entity = null
var attack_cooldown := 2.0
var _attack_timer := 0.0
var _regen_acc_hp := 0.0
var _regen_acc_chakra := 0.0
var rng := RandomNumberGenerator.new()

func init_new_character() -> void:
	display_name = "Ninja"
	color = Color("ff8c1a")
	rng.randomize()
	skills = SkillSystem.new()
	skills.skill_up.connect(_on_skill_up)
	inventory = Inventory.new(20)
	hotbar.resize(10)
	hotbar.fill("")
	var village: Dictionary = GameData.villages.get(village_id, {})
	for item_id in village.get("starting_items", []):
		inventory.add(item_id, 10 if GameData.items[item_id].get("stack_max", 1) > 1 else 1)
	for item_id in village.get("starting_items", []):
		equip_from_bag_by_id(item_id)
	inventory.add("onigiri", 5)
	inventory.add("chakra_pill_small", 3)
	ryo = 100
	for jid in village.get("starting_jutsus", []):
		learn_jutsu(jid, false)
	_auto_learn()
	recalc_stats()
	hp = max_hp
	chakra = max_chakra
	stats_changed.emit()

func prepare_for_load() -> void:
	display_name = "Ninja"
	color = Color("ff8c1a")
	rng.randomize()
	skills = SkillSystem.new()
	skills.skill_up.connect(_on_skill_up)
	inventory = Inventory.new(20)
	hotbar.resize(10)
	hotbar.fill("")

# ---------- stats ----------
func recalc_stats() -> void:
	bonus.clear()
	skill_bonus.clear()
	defense = 0
	weapon_attack = 0
	weapon_class = "melee"
	weapon_range = 1
	weapon_skill = "taijutsu"
	for slot in equipment:
		var it: Dictionary = GameData.items.get(equipment[slot], {})
		defense += int(it.get("defense", 0))
		if slot == "weapon":
			weapon_attack = int(it.get("attack", 0))
			weapon_class = it.get("weapon_class", "melee")
			weapon_range = int(it.get("weapon_range", 1))
			weapon_skill = it.get("skill", "taijutsu")
		for k in it.get("bonuses", {}):
			var v := float(it["bonuses"][k])
			if k.begins_with("skill_"):
				skill_bonus[k.trim_prefix("skill_")] = float(skill_bonus.get(k.trim_prefix("skill_"), 0)) + v
			else:
				bonus[k] = float(bonus.get(k, 0)) + v
	max_hp = 100 + level * 15 + int(bonus.get("hp", 0))
	max_chakra = 50 + level * 10 + int(bonus.get("chakra", 0))
	speed_tiles_s = 4.0 + float(bonus.get("speed", 0))
	crit_chance = 0.05 + float(bonus.get("crit_chance", 0))
	defense += int(skill_value("defense") * 0.3)
	hp = mini(hp, max_hp)
	chakra = mini(chakra, max_chakra)
	stats_changed.emit()

func skill_value(id: String) -> int:
	return skills.get_value(id) + int(skill_bonus.get(id, 0))

func skill_multiplier(id: String) -> float:
	var village: Dictionary = GameData.villages.get(village_id, {})
	return float(GameData.skills.get("village_bonus_multiplier", 1.2)) if village.get("bonus_skill") == id else 1.0

func capacity() -> float:
	return 100.0 + level * 5 + float(bonus.get("capacity", 0))

func total_weight() -> float:
	var w := 0.0
	for s in inventory.slots:
		if s != null:
			w += float(GameData.items.get(s["id"], {}).get("weight", 0)) * int(s["qty"])
	for slot in equipment:
		w += float(GameData.items.get(equipment[slot], {}).get("weight", 0))
	return w

func is_overweight() -> bool:
	return total_weight() > capacity()

func try_move(dir: Vector2i) -> bool:
	if is_overweight():
		if not _overweight_warned:
			_log("[color=orange]Você está pesado demais para andar. Jogue algo fora.[/color]")
			_overweight_warned = true
		facing = dir
		queue_redraw()
		return false
	_overweight_warned = false
	return super.try_move(dir)

# ---------- missões ----------
func quest_state(qid: String) -> String:
	return quests.get(qid, {}).get("state", "none")

func accept_quest(q: Dictionary) -> void:
	quests[q["id"]] = {"state": "active", "progress": 0}
	_log("[color=yellow]Missão aceita: %s[/color] — %s" % [q["name"], q["text"]])
	stats_changed.emit()

func active_quest_line() -> String:
	for qid in quests:
		if quests[qid]["state"] == "active":
			var q := GameData_find_quest(qid)
			if not q.is_empty():
				return "%s: %d/%d %s" % [q["name"], int(quests[qid]["progress"]), int(q["objective"]["count"]), GameData.monsters[q["objective"]["kill"]]["name"]]
	return ""

static func GameData_find_quest(qid: String) -> Dictionary:
	for npc_id in GameData.npcs:
		for q in GameData.npcs[npc_id].get("quests", []):
			if q["id"] == qid:
				return q
	return {}

func on_monster_killed(monster_id: String) -> void:
	for qid in quests:
		var st: Dictionary = quests[qid]
		if st["state"] != "active":
			continue
		var q := GameData_find_quest(qid)
		if q.get("objective", {}).get("kill") == monster_id:
			var need := int(q["objective"]["count"])
			if int(st["progress"]) < need:
				st["progress"] = int(st["progress"]) + 1
				if int(st["progress"]) >= need:
					_log("[color=yellow]Missão pronta: %s. Volte para entregar.[/color]" % q["name"])
	stats_changed.emit()

func quest_ready(q: Dictionary) -> bool:
	var st: Dictionary = quests.get(q["id"], {})
	return st.get("state") == "active" and int(st.get("progress", 0)) >= int(q["objective"]["count"])

func complete_quest(q: Dictionary) -> void:
	var r: Dictionary = q["reward"]
	quests[q["id"]]["state"] = "done"
	ryo += int(r.get("ryo", 0))
	for item_id in r.get("items", []):
		if inventory.add(item_id, 1) > 0:
			_log("Mochila cheia: %s ficou para trás." % GameData.items[item_id]["name"])
	_log("[color=yellow]Missão concluída: %s (+%d XP, +%d ryo)[/color]" % [q["name"], int(r.get("xp", 0)), int(r.get("ryo", 0))])
	gain_xp(int(r.get("xp", 0)))

func _on_skill_up(id: String, v: int) -> void:
	world.hud.log_msg("[color=cyan]%s avançou para %d.[/color]" % [_skill_name(id), v])
	if id == "defense":
		recalc_stats()
	stats_changed.emit()

func _skill_name(id: String) -> String:
	for s in GameData.skills.get("skills", []):
		if s["id"] == id:
			return s["name"]
	return id

# ---------- loop ----------
func _process(delta: float) -> void:
	super._process(delta)
	if not alive:
		return
	for k in cooldowns.keys():
		cooldowns[k] = maxf(0.0, float(cooldowns[k]) - delta)
	if world.ui_open():
		return
	_handle_movement()
	_regen(delta)
	_auto_attack(delta)

func _handle_movement() -> void:
	var dir := Vector2i.ZERO
	if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
		dir = Vector2i.UP
	elif Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
		dir = Vector2i.DOWN
	elif Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
		dir = Vector2i.LEFT
	elif Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
		dir = Vector2i.RIGHT
	if dir != Vector2i.ZERO:
		try_move(dir)

func _regen(delta: float) -> void:
	_regen_acc_hp += ((2.0 + level * 0.2) / 5.0 + float(bonus.get("regen_hp", 0)) / 5.0) * delta
	_regen_acc_chakra += ((3.0 + level * 0.3) / 5.0 + float(bonus.get("regen_chakra", 0)) / 5.0) * delta
	var changed := false
	if _regen_acc_hp >= 1.0:
		if hp < max_hp:
			heal(int(_regen_acc_hp))
			changed = true
		_regen_acc_hp -= int(_regen_acc_hp)
	if _regen_acc_chakra >= 1.0:
		if chakra < max_chakra:
			chakra = mini(max_chakra, chakra + int(_regen_acc_chakra))
			changed = true
		_regen_acc_chakra -= int(_regen_acc_chakra)
	if changed:
		stats_changed.emit()

func set_target(t: Entity) -> void:
	if t == target:
		return
	target = t
	target_changed.emit(target)

func _auto_attack(delta: float) -> void:
	_attack_timer = maxf(0.0, _attack_timer - delta)
	if target == null:
		return
	if not target.alive:
		set_target(null)
		return
	if chebyshev_to(target) > weapon_range or _attack_timer > 0.0 or not can_act():
		return
	face_towards(target)
	var dmg := DamageCalc.physical(weapon_attack, skill_value(weapon_skill), target.defense, rng)
	dmg = DamageCalc.apply_crit(dmg, crit_chance, rng)
	if weapon_class == "ranged":
		var ammo_id: String = equipment.get("weapon", "")
		if GameData.items.get(ammo_id, {}).get("stack_max", 1) > 1:
			# arma consumível (shuriken): gasta uma da mochila, se não tiver usa a última equipada
			if not inventory.remove(ammo_id, 1) and inventory.count(ammo_id) == 0:
				pass
		world.spawn_projectile(self, target, dmg, Color("cccccc"))
	else:
		target.take_damage(dmg, self)
	skills.raise(weapon_skill, skill_multiplier(weapon_skill))
	_attack_timer = attack_cooldown

# ---------- jutsus ----------
func learn_jutsu(jid: String, announce: bool = true) -> void:
	if jid in known_jutsus or not GameData.jutsus.has(jid):
		return
	known_jutsus.append(jid)
	for i in hotbar.size():
		if hotbar[i] == "":
			hotbar[i] = jid
			break
	if announce and world != null:
		world.hud.log_msg("[color=yellow]Você aprendeu %s![/color]" % GameData.jutsus[jid]["name"])
	jutsus_changed.emit()

func _auto_learn() -> void:
	for jid in GameData.jutsus:
		var j: Dictionary = GameData.jutsus[jid]
		var villages: Array = j.get("villages", [])
		if int(j.get("tier", 1)) == 1 and level >= int(j["required_level"]) \
				and (villages.is_empty() or village_id in villages):
			learn_jutsu(jid)

func cast_slot(i: int) -> void:
	if i < 0 or i >= hotbar.size() or hotbar[i] == "" or not alive:
		return
	var err := JutsuExecutor.cast(world, self, GameData.jutsus[hotbar[i]])
	if err != "":
		world.hud.log_msg("[color=gray]%s[/color]" % err)

# ---------- inventário ----------
func equip_from_bag_by_id(item_id: String) -> bool:
	for i in inventory.size:
		var s = inventory.slots[i]
		if s != null and s["id"] == item_id:
			return equip_from_bag(i)
	return false

## Equipa (ou usa) o item no slot i da mochila.
func equip_from_bag(i: int) -> bool:
	var s = inventory.slots[i]
	if s == null:
		return false
	var it: Dictionary = GameData.items.get(s["id"], {})
	if level < int(it.get("required_level", 1)):
		_log("Precisa de level %d." % int(it["required_level"]))
		return false
	match it.get("type"):
		"weapon", "armor", "accessory":
			var slot: String = it.get("slot", "")
			if slot == "accessory":
				slot = "accessory1" if not equipment.has("accessory1") else "accessory2"
			if slot == "":
				return false
			var prev: String = equipment.get(slot, "")
			var qty := 1
			if slot == "weapon" and int(it.get("stack_max", 1)) > 1:
				qty = int(s["qty"])
			inventory.remove_at(i, qty)
			if prev != "":
				inventory.add(prev, 1)
			equipment[slot] = it["id"]
			recalc_stats()
			return true
		"consumable":
			var e: Dictionary = it.get("effect", {})
			match e.get("type"):
				"heal_hp": heal(int(e["value"]))
				"heal_chakra": chakra = mini(max_chakra, chakra + int(e["value"]))
				"heal_both":
					heal(int(e["value"]))
					chakra = mini(max_chakra, chakra + int(e["value"]))
				"cure": cure(e.get("stat", "poison"))
			inventory.remove_at(i, 1)
			_log("Você usou %s." % it["name"])
			stats_changed.emit()
			return true
		"scroll":
			var jid: String = it.get("teaches_jutsu", "")
			if jid in known_jutsus:
				_log("Você já conhece esse jutsu.")
				return false
			var req_v: String = it.get("required_village", "")
			if req_v != "" and req_v != village_id:
				_log("Esse pergaminho é de outra vila.")
				return false
			inventory.remove_at(i, 1)
			learn_jutsu(jid)
			return true
	return false

func unequip(slot: String) -> bool:
	if not equipment.has(slot):
		return false
	if inventory.free_slots() == 0:
		_log("Mochila cheia.")
		return false
	inventory.add(equipment[slot], 1)
	equipment.erase(slot)
	recalc_stats()
	return true

func _log(t: String) -> void:
	if world != null:
		world.hud.log_msg(t)

# ---------- progressão ----------
func gain_xp(amount: int) -> void:
	xp += amount
	while xp >= GameData.xp_for_level(level + 1):
		level += 1
		recalc_stats()
		hp = max_hp
		chakra = max_chakra
		_log("[color=yellow]Você subiu para o level %d![/color]" % level)
		_auto_learn()
	stats_changed.emit()

func take_damage(amount: int, source: Entity, text_color: Color = Color("ff5252")) -> void:
	super.take_damage(amount, source, text_color)
	if source != null and alive:
		skills.raise("defense", skill_multiplier("defense"))
	stats_changed.emit()

func on_death_penalty() -> Array:
	var span := GameData.xp_for_level(level + 1) - GameData.xp_for_level(level)
	var loss := int(span * float(GameData.progression.get("death_xp_loss_percent", 10)) / 100.0)
	xp = maxi(GameData.xp_for_level(level), xp - loss)
	_log("Você perdeu %d de XP." % loss)
	# 30% de chance de cada stack da mochila cair no seu corpo
	var dropped: Array = []
	var chance := float(GameData.progression.get("death_item_drop_chance", 0.3))
	for i in inventory.size:
		var s = inventory.slots[i]
		if s != null and rng.randf() < chance:
			dropped.append({"id": s["id"], "qty": int(s["qty"])})
			inventory.slots[i] = null
	if not dropped.is_empty():
		inventory.changed.emit()
		_log("[color=orange]Você deixou %d item(ns) no seu corpo.[/color]" % dropped.size())
	return dropped

func respawn(at: Vector2i, restore: bool = true) -> void:
	world.vacate(self)
	cell = at
	position = world.cell_to_world(cell)
	world.occupy(self, cell)
	if restore:
		hp = max_hp
		chakra = max_chakra
	alive = true
	visible = true
	statuses.clear()
	set_target(null)
	stats_changed.emit()
	queue_redraw()
