## Raiz da cena principal. Dono do mapa, das entidades, da ocupação do grid e da UI.
class_name GameWorld
extends Node2D

const TILE := 32
const MAP_ID := "forest_valley"

var map: WorldMap
var player: Player
var hud: HUD
var ui_layer: CanvasLayer
var hotbar: Hotbar
var inventory_panel: InventoryPanel
var shop_panel: ShopPanel
var camera: Camera2D
var monsters: Array[Monster] = []
var npcs: Array[NPC] = []
var corpses: Dictionary = {}     # Vector2i -> Corpse
var occupancy: Dictionary = {}   # Vector2i -> Entity
var rng := RandomNumberGenerator.new()
var started := false
var _reticle: Node2D
var _flash_layer: Node2D
var _flashes: Array = []
var _last_zone := ""

func _ready() -> void:
	rng.randomize()
	map = WorldMap.new()
	add_child(map)
	map.load_def(GameData.maps[MAP_ID])
	_flash_layer = Node2D.new()
	_flash_layer.z_index = 5
	_flash_layer.draw.connect(_draw_flashes)
	add_child(_flash_layer)
	_reticle = Node2D.new()
	_reticle.z_index = 200
	_reticle.draw.connect(_draw_reticle)
	add_child(_reticle)
	hud = HUD.new()
	add_child(hud)
	hud.visible = false

	if SaveSystem.exists():
		start_game("", true)
	else:
		var ss := StartScreen.new()
		add_child(ss)
		ss.village_chosen.connect(func(vid: String) -> void: start_game(vid, false))

## Cria o player (novo ou carregado), UI, monstros e NPCs.
func start_game(village_id: String, from_save: bool) -> void:
	for c in get_children():
		if c is StartScreen:
			c.queue_free()
	player = Player.new()
	add_child(player)
	if from_save:
		player.prepare_for_load()
		player.setup(self, map.start_cell)
		SaveSystem.load_into(player)
	else:
		player.village_id = village_id
		player.init_new_character()
		player.setup(self, map.start_cell)
	player.stats_changed.connect(func() -> void: hud.update_player(player))
	player.target_changed.connect(_on_player_target_changed)
	player.died.connect(_on_player_died)

	ui_layer = CanvasLayer.new()
	ui_layer.layer = 2
	add_child(ui_layer)
	hotbar = Hotbar.new()
	ui_layer.add_child(hotbar)
	hotbar.setup(player)
	inventory_panel = InventoryPanel.new()
	ui_layer.add_child(inventory_panel)
	inventory_panel.setup(player)
	shop_panel = ShopPanel.new()
	ui_layer.add_child(shop_panel)
	shop_panel.setup(player)

	camera = Camera2D.new()
	camera.zoom = Vector2(2, 2)
	camera.limit_left = 0
	camera.limit_top = 0
	camera.limit_right = WorldMap.W * TILE
	camera.limit_bottom = WorldMap.H * TILE
	camera.position_smoothing_enabled = true
	camera.position_smoothing_speed = 12.0
	player.add_child(camera)
	camera.make_current()

	for s in map.def.get("spawns", []):
		_spawn_monster(s["monster_id"], Vector2i(int(s["x"]), int(s["y"])))
	for npc_id in GameData.npcs:
		var d: Dictionary = GameData.npcs[npc_id]
		if d.get("map", MAP_ID) == MAP_ID:
			_spawn_npc(d, Vector2i(int(d["x"]), int(d["y"])))

	hud.visible = true
	hud.update_player(player)
	started = true
	if from_save:
		hud.log_msg("Jogo carregado. Bem-vindo de volta.")
	else:
		hud.log_msg("Bem-vindo à %s. Fale com a Capitã Rin (azul, !) para pegar uma missão." % GameData.villages[village_id]["name"])

func _spawn_monster(id: String, at: Vector2i, temporary: bool = false) -> Monster:
	map.force_walkable(at)
	var m := Monster.new()
	m.init_from_data(id)
	m.spawn_cell = at
	m.temporary = temporary
	add_child(m)
	m.setup(self, at)
	m.died.connect(_on_monster_died)
	monsters.append(m)
	return m

## Invocação de boss: aparece numa célula livre perto de `near` e não respawna.
func spawn_temporary_monster(id: String, near: Vector2i) -> void:
	for r in range(1, 4):
		for c in Shapes.cells("circle_r%d" % r, near, Vector2i.DOWN):
			if is_free(c):
				var m := _spawn_monster(id, c, true)
				m.state = Monster.State.CHASE
				return

func _spawn_npc(d: Dictionary, at: Vector2i) -> void:
	map.force_walkable(at)
	var n := NPC.new()
	n.init_from_data(d)
	add_child(n)
	n.setup(self, at)
	npcs.append(n)

func ui_open() -> bool:
	return inventory_panel.visible or shop_panel.visible

# ---------- grid ----------
func cell_to_world(c: Vector2i) -> Vector2:
	return Vector2(c.x * TILE + TILE / 2.0, c.y * TILE + TILE / 2.0)

func world_to_cell(p: Vector2) -> Vector2i:
	return Vector2i(floori(p.x / TILE), floori(p.y / TILE))

func is_free(c: Vector2i) -> bool:
	return map.is_walkable(c) and not occupancy.has(c)

func occupy(e: Entity, c: Vector2i) -> void:
	occupancy[c] = e

func vacate(e: Entity) -> void:
	if occupancy.get(e.cell) == e:
		occupancy.erase(e.cell)

func move_entity(e: Entity, from: Vector2i, to: Vector2i) -> void:
	if occupancy.get(from) == e:
		occupancy.erase(from)
	occupancy[to] = e

func entity_at(c: Vector2i) -> Entity:
	return occupancy.get(c)

# ---------- loot ----------
func _roll_loot(m: Monster) -> Array:
	var out: Array = []
	for l in m.data.get("loot", []):
		if rng.randf() < float(l["chance"]):
			var qty := rng.randi_range(int(l.get("min", 1)), int(l.get("max", 1)))
			out.append({"id": l["item_id"], "qty": qty})
	return out

func _make_corpse(at: Vector2i, name: String, items: Array, ryo: int) -> Corpse:
	if corpses.has(at):
		corpses[at].queue_free()
	var c := Corpse.new()
	add_child(c)
	c.setup(at, name, items, ryo, self)
	corpses[at] = c
	return c

func _loot_corpse(c: Corpse) -> void:
	if c.ryo > 0:
		player.ryo += c.ryo
		hud.log_msg("Você pegou %d ryo." % c.ryo)
		c.ryo = 0
	var remaining: Array = []
	for it in c.items:
		var left := player.inventory.add(it["id"], int(it["qty"]))
		var got := int(it["qty"]) - left
		if got > 0:
			hud.log_msg("Você pegou %s x%d." % [GameData.items[it["id"]]["name"], got])
		if left > 0:
			remaining.append({"id": it["id"], "qty": left})
	if not remaining.is_empty():
		hud.log_msg("Mochila cheia, sobrou loot no corpo.")
	c.items = remaining
	c.queue_redraw()
	player.stats_changed.emit()

# ---------- eventos ----------
func _on_monster_died(e: Entity) -> void:
	var m := e as Monster
	vacate(m)
	m.visible = false
	player.gain_xp(m.xp_value)
	hud.log_msg("Você matou [color=white]%s[/color] (+%d XP)." % [m.display_name, m.xp_value])
	player.on_monster_killed(m.monster_id)
	if player.target == m:
		player.set_target(null)
	var ryo := rng.randi_range(int(m.data["ryo_min"]), int(m.data["ryo_max"]))
	_make_corpse(m.cell, m.display_name, _roll_loot(m), ryo)
	if m.temporary:
		monsters.erase(m)
		m.queue_free()
		return
	get_tree().create_timer(m.respawn_s).timeout.connect(func() -> void: _try_respawn(m))

func _try_respawn(m: Monster) -> void:
	if is_free(m.spawn_cell):
		m.reset_for_respawn()
	else:
		get_tree().create_timer(5.0).timeout.connect(func() -> void: _try_respawn(m))

func _on_player_died(_e: Entity) -> void:
	hud.log_msg("[color=red]Você morreu.[/color] Voltando à vila em 3s...")
	vacate(player)
	player.visible = false
	var dropped := player.on_death_penalty()
	if not dropped.is_empty():
		_make_corpse(player.cell, "Seu corpo", dropped, 0)
	for m in monsters:
		if m.alive:
			m.state = Monster.State.IDLE
	get_tree().create_timer(3.0).timeout.connect(func() -> void:
		player.respawn(map.start_cell)
		hud.log_msg("Você renasceu."))

func _on_player_target_changed(t: Entity) -> void:
	hud.update_target(t)
	if t != null:
		t.damaged.connect(func(_e: Entity, _a: int) -> void:
			if player.target == t:
				hud.update_target(t)
		, CONNECT_REFERENCE_COUNTED)

# ---------- input ----------
func _unhandled_input(event: InputEvent) -> void:
	if not started:
		return
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_click_cell(world_to_cell(get_global_mouse_position()))
	elif event is InputEventKey and event.pressed and not event.echo:
		_key(event.keycode)

func _click_cell(c: Vector2i) -> void:
	var e := entity_at(c)
	if e is Monster and e.alive:
		player.set_target(e)
		return
	if e is NPC:
		if player.chebyshev_to(e) <= 2:
			_talk(e)
		else:
			hud.log_msg("Chegue mais perto de %s." % e.display_name)
		return
	if corpses.has(c):
		var corpse: Corpse = corpses[c]
		if maxi(abs(player.cell.x - c.x), abs(player.cell.y - c.y)) <= 1:
			_loot_corpse(corpse)
		else:
			hud.log_msg("Chegue mais perto do corpo.")

func _talk(n: NPC) -> void:
	match n.data.get("type"):
		"shop":
			inventory_panel.visible = false
			shop_panel.open_for(n)
		"quest":
			talk_quest(n)
		_:
			hud.log_msg("%s acena." % n.display_name)

## Missões sequenciais por NPC: entrega a pronta, mostra progresso da ativa, ou oferece a próxima.
func talk_quest(n: NPC) -> void:
	for q in n.data.get("quests", []):
		var st := player.quest_state(q["id"])
		if st == "done":
			continue
		if st == "active":
			if player.quest_ready(q):
				player.complete_quest(q)
				hud.log_msg("[color=white]%s:[/color] \"Bom trabalho, ninja.\"" % n.display_name)
			else:
				hud.log_msg("[color=white]%s:[/color] \"Ainda não terminou? %s\"" % [n.display_name, player.active_quest_line()])
			return
		# não iniciada: só oferece se não há outra ativa deste NPC
		for other in n.data.get("quests", []):
			if player.quest_state(other["id"]) == "active":
				return
		hud.log_msg("[color=white]%s:[/color] \"%s\"" % [n.display_name, q["text"]])
		player.accept_quest(q)
		return
	hud.log_msg("[color=white]%s:[/color] \"Não tenho mais nada para você por enquanto.\"" % n.display_name)

func _key(code: Key) -> void:
	match code:
		KEY_TAB: player.set_target(_nearest_monster())
		KEY_ESCAPE:
			if shop_panel.visible: shop_panel.visible = false
			elif inventory_panel.visible: inventory_panel.visible = false
			else: player.set_target(null)
		KEY_I: inventory_panel.toggle()
		KEY_F5:
			hud.log_msg("Jogo salvo." if SaveSystem.save(player) else "Falha ao salvar.")
		KEY_F9:
			if SaveSystem.load_into(player):
				hud.log_msg("Jogo carregado.")
				hotbar.refresh()
			else:
				hud.log_msg("Nenhum save encontrado.")
		KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9:
			player.cast_slot(code - KEY_1)
		KEY_0: player.cast_slot(9)

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST and started and player.alive:
		SaveSystem.save(player)

func _nearest_monster() -> Monster:
	var best: Monster = null
	var best_d := 999
	for m in monsters:
		if not m.alive:
			continue
		var d := player.chebyshev_to(m)
		if d < best_d:
			best_d = d
			best = m
	return best

# ---------- efeitos ----------
func spawn_floating_text(at: Vector2, text: String, color: Color) -> void:
	var ft := FloatingText.new()
	ft.setup(text, color)
	ft.position = at + Vector2(-12, 0)
	add_child(ft)

func spawn_projectile(source: Entity, target: Entity, damage: int, color: Color, effects: Array = []) -> void:
	var p := Projectile.new()
	add_child(p)
	p.launch(source, target, damage, color, effects)

func spawn_area_flash(cells: Array, color: Color) -> void:
	_flashes.append({"cells": cells, "color": color, "remaining": 0.35})

func _process(delta: float) -> void:
	_reticle.queue_redraw()
	if not _flashes.is_empty():
		for f in _flashes.duplicate():
			f["remaining"] = float(f["remaining"]) - delta
			if float(f["remaining"]) <= 0.0:
				_flashes.erase(f)
		_flash_layer.queue_redraw()
	if started:
		var z := map.zone_at(player.cell)
		var zname: String = z.get("name", "")
		if zname != _last_zone:
			_last_zone = zname
			hud.update_zone(z)
			if zname != "":
				hud.log_msg("[color=gray]Você entrou em %s.[/color]" % zname)

func _draw_flashes() -> void:
	for f in _flashes:
		var c: Color = f["color"]
		c.a = clampf(float(f["remaining"]) / 0.35, 0.0, 1.0) * 0.7
		for cell in f["cells"]:
			_flash_layer.draw_rect(Rect2(cell.x * TILE, cell.y * TILE, TILE, TILE), c)

func _draw_reticle() -> void:
	if player != null and player.target != null and player.target.alive:
		var r := Rect2(player.target.position - Vector2(17, 17), Vector2(34, 34))
		_reticle.draw_rect(r, Color.YELLOW, false, 2.0)
