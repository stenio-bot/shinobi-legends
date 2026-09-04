## Skills sobem com uso. Ver docs/sistemas/personagem-e-progressao.md
class_name SkillSystem
extends RefCounted

signal skill_up(skill_id: String, new_value: int)

var values: Dictionary = {}
var tries: Dictionary = {}

func _init() -> void:
	var start := int(GameData.skills.get("start_value", 10))
	for s in GameData.skills.get("skills", []):
		values[s["id"]] = start
		tries[s["id"]] = 0.0

func get_value(id: String) -> int:
	return int(values.get(id, 10))

func tries_needed(id: String) -> float:
	return 50.0 * pow(1.1, get_value(id) - 10)

## Adiciona uma tentativa. Retorna true se subiu.
func raise(id: String, mult: float = 1.0) -> bool:
	if not values.has(id):
		return false
	var max_v := int(GameData.skills.get("max_value", 150))
	if get_value(id) >= max_v:
		return false
	tries[id] = float(tries[id]) + mult
	if float(tries[id]) >= tries_needed(id):
		tries[id] = float(tries[id]) - tries_needed(id)
		values[id] = get_value(id) + 1
		skill_up.emit(id, values[id])
		return true
	return false

func to_dict() -> Dictionary:
	return {"values": values.duplicate(), "tries": tries.duplicate()}

func from_dict(d: Dictionary) -> void:
	for k in d.get("values", {}):
		values[k] = int(d["values"][k])
	for k in d.get("tries", {}):
		tries[k] = float(d["tries"][k])
