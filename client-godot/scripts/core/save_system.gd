class_name SaveSystem

const PATH := "user://save_slot_1.json"

static func save(p: Player) -> bool:
	var d := {
		"version": 1,
		"village": p.village_id,
		"level": p.level, "xp": p.xp, "hp": p.hp, "chakra": p.chakra, "ryo": p.ryo,
		"cell": [p.cell.x, p.cell.y],
		"skills": p.skills.to_dict(),
		"inventory": p.inventory.to_array(),
		"equipment": p.equipment.duplicate(),
		"known_jutsus": p.known_jutsus.duplicate(),
		"hotbar": p.hotbar.duplicate(),
		"quests": p.quests.duplicate(true),
	}
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(d, "  "))
	return true

static func exists() -> bool:
	return FileAccess.file_exists(PATH)

static func load_into(p: Player) -> bool:
	if not exists():
		return false
	var d = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	if d == null:
		return false
	p.village_id = d.get("village", "leaf")
	p.level = int(d["level"])
	p.xp = int(d["xp"])
	p.ryo = int(d.get("ryo", 0))
	p.skills.from_dict(d.get("skills", {}))
	p.inventory.from_array(d.get("inventory", []))
	p.equipment.clear()
	for k in d.get("equipment", {}):
		p.equipment[k] = d["equipment"][k]
	p.known_jutsus.clear()
	for j in d.get("known_jutsus", []):
		p.known_jutsus.append(j)
	p.hotbar.clear()
	for h in d.get("hotbar", []):
		p.hotbar.append(h)
	p.quests.clear()
	for k in d.get("quests", {}):
		p.quests[k] = {"state": d["quests"][k]["state"], "progress": int(d["quests"][k]["progress"])}
	p.recalc_stats()
	p.hp = mini(p.max_hp, int(d["hp"]))
	p.chakra = mini(p.max_chakra, int(d["chakra"]))
	var c: Array = d.get("cell", [p.cell.x, p.cell.y])
	p.respawn(Vector2i(int(c[0]), int(c[1])), false)
	return true
