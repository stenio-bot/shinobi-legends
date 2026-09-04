## Teste de fumaça: cena principal + combate, jutsu, loot, loja, missão, boss, peso, save.
## Uso: godot --headless --path client res://tests/smoke_test.tscn
extends Node

var frame := 0
var world: GameWorld
var kills := 0
var failures: Array[String] = []

func _ready() -> void:
	if FileAccess.file_exists(SaveSystem.PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(SaveSystem.PATH))
	world = load("res://scenes/world/main.tscn").instantiate()
	add_child(world)

func check(cond: bool, msg: String) -> void:
	if not cond:
		failures.append(msg)
		print("FALHOU: " + msg)

func find_monster(id: String) -> Monster:
	for m in world.monsters:
		if m.monster_id == id and m.alive:
			return m
	return null

func _process(_delta: float) -> void:
	frame += 1
	if frame == 5:
		check(not world.started, "deveria esperar escolha de vila")
		world.start_game("leaf", false)
		check(world.started and world.player != null, "start_game")
	if frame < 6:
		return
	var p := world.player
	if frame == 10:
		var wolf := find_monster("wolf")
		p.respawn(wolf.spawn_cell + Vector2i(-2, 0))
		p.set_target(wolf)
		wolf.died.connect(func(_e: Entity) -> void: kills += 1)
		check(p.known_jutsus.size() >= 1, "jutsu inicial")
		check(p.equipment.has("weapon") and p.equipment.has("body"), "equipamento inicial")
		check(world.monsters.size() >= 20, "spawns do mapa (tem %d)" % world.monsters.size())
		check(world.npcs.size() == 5, "5 NPCs (tem %d)" % world.npcs.size())
		check(WorldMap.W == 96, "mapa 96 de largura")
		print("t=10: jutsus=%s def=%d atk=%d peso=%.1f/%.0f" % [p.known_jutsus, p.defense, p.weapon_attack, p.total_weight(), p.capacity()])
	if frame == 30:
		var before := p.chakra
		p.cast_slot(0)
		check(p.chakra < before, "jutsu gasta chakra")
		check(p.cooldowns.get(p.hotbar[0], 0.0) > 0.0, "jutsu em cooldown")
	if frame == 60:
		check(JutsuExecutor.cast(world, p, GameData.jutsus["katon_goukakyuu"]) == "Ainda em recarga.", "cooldown bloqueia")
		# missão: aceita com a Capitã Rin
		var rin: NPC = null
		for n in world.npcs:
			if n.data["id"] == "quest_giver_leaf":
				rin = n
		world.talk_quest(rin)
		check(p.quest_state("q_wolves_1") == "active", "missão de lobos aceita")
	if frame == 90 and p.target != null:
		p.target.take_damage(p.target.hp, p)
	if frame == 200:
		check(kills >= 1, "lobo morreu")
		check(int(p.quests["q_wolves_1"]["progress"]) == 1, "progresso da missão = 1")
		check(world.corpses.size() >= 1, "corpo")
		if world.corpses.size() > 0:
			var c: Corpse = world.corpses.values()[0]
			p.teleport(c.cell + Vector2i(1, 0))
			world._loot_corpse(c)
		check(p.xp > 0, "xp subiu")
		# completa missão à força
		p.quests["q_wolves_1"]["progress"] = 5
		var rin: NPC = null
		for n in world.npcs:
			if n.data["id"] == "quest_giver_leaf":
				rin = n
		var ryo_before := p.ryo
		world.talk_quest(rin)
		check(p.quest_state("q_wolves_1") == "done", "missão concluída")
		check(p.ryo == ryo_before + 60, "recompensa de ryo")
		check(p.inventory.count("health_potion_small") >= 1, "recompensa de item")
		world.talk_quest(rin)
		check(p.quest_state("q_bandits_1") == "active", "próxima missão oferecida")
	if frame == 220:
		var t: float = p.skills.tries["taijutsu"]
		check(t > 0.0 or p.skills.get_value("taijutsu") > 10, "taijutsu com tentativas")
		p.hp = 10
		var idx := -1
		for i in p.inventory.size:
			if p.inventory.slots[i] != null and p.inventory.slots[i]["id"] == "onigiri":
				idx = i
		if idx >= 0:
			p.equip_from_bag(idx)
			check(p.hp == 50, "onigiri cura 40 (hp=%d)" % p.hp)
		# peso
		p.inventory.add("toad_skin", 100)
		check(p.is_overweight(), "deveria estar pesado")
		check(not p.try_move(Vector2i.UP), "pesado não anda")
		p.inventory.remove("toad_skin", 100)
		check(not p.is_overweight(), "peso normalizado")
		# loja
		var npc: NPC = world.npcs[0]
		world.shop_panel.open_for(npc)
		p.ryo = 1000
		world.shop_panel.sell_list.select(0)
		world.shop_panel._buy()
		check(p.ryo < 1000, "compra gasta ryo")
		world.shop_panel.visible = false
		# save/load com missões
		check(SaveSystem.save(p), "save")
		var ryo := p.ryo
		p.ryo = 0
		p.quests.clear()
		check(SaveSystem.load_into(p), "load")
		check(p.ryo == ryo and p.quest_state("q_wolves_1") == "done", "load restaura ryo e missões")
		DirAccess.remove_absolute(ProjectSettings.globalize_path(SaveSystem.PATH))
	if frame == 240 and DisplayServer.get_name() != "headless":
		p.teleport(Vector2i(62, 18))
	if frame == 290 and DisplayServer.get_name() != "headless":
		var img := get_viewport().get_texture().get_image()
		img.save_png(ProjectSettings.globalize_path("res://").rstrip("/").get_base_dir().path_join("screenshot_marco3.png"))
		print("screenshot salvo")
	if frame == 300:
		# boss: fase em 50% invoca 3 bandidos
		var boss := find_monster("boss_bandit_chief")
		var before := world.monsters.size()
		p.teleport(boss.cell + Vector2i(-2, 0))
		boss.take_damage(int(boss.max_hp * 0.55), p)
		check(world.monsters.size() == before + 3, "boss invocou 3 bandidos (%d -> %d)" % [before, world.monsters.size()])
		boss.take_damage(int(boss.max_hp * 0.3), p)
		check(boss.attack_multiplier > 1.0, "boss fase 2 aumenta ataque")
		# invocado morre e some sem respawn
		var temp: Monster = null
		for m in world.monsters:
			if m.temporary:
				temp = m
		if temp != null:
			temp.take_damage(temp.hp, p)
			check(not world.monsters.has(temp), "invocado removido ao morrer")
		# visão: lobo atrás de árvore não vê
		check(world.map.has_line_of_sight(Vector2i(12, 18), Vector2i(14, 18)), "LOS na estrada")
		# área
		var b := find_monster("bandit")
		if b != null:
			p.teleport(b.cell + Vector2i(0, 2))
			p.facing = Vector2i.UP
			var hp_before := b.hp
			p.chakra = p.max_chakra
			p.cooldowns.clear()
			p.level = 12
			var err := JutsuExecutor.cast(world, p, GameData.jutsus["katon_housenka"])
			check(err == "", "housenka: " + err)
			check(b.hp < hp_before, "cone acerta bandido")
		# morte do player dropa corpo
		p.inventory.add("wolf_pelt", 50)
		p.take_damage(p.hp, b)
		check(not p.alive, "player morreu")
	if frame >= 400:
		print("RESULTADO: kills=%d level=%d xp=%d ryo=%d falhas=%d" % [kills, p.level, p.xp, p.ryo, failures.size()])
		get_tree().quit(0 if failures.is_empty() else 1)
