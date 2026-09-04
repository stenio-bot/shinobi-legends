## Autoload: carrega todo o conteúdo de data/*.json no boot.
## Acesso: GameData.jutsus["katon_goukakyuu"], GameData.items["kunai_iron"], etc.
## No editor lê direto de ../data (raiz do repo). Em export, copie data/ para client/data/.
extends Node

var jutsus: Dictionary = {}
var items: Dictionary = {}
var monsters: Dictionary = {}
var villages: Dictionary = {}
var npcs: Dictionary = {}
var progression: Dictionary = {}
var skills: Dictionary = {}
var elements: Dictionary = {}
var maps: Dictionary = {}

var _root: String

func _ready() -> void:
	_root = _data_root()
	jutsus = _load_folder("jutsus")
	items = _load_folder("items")
	monsters = _load_folder("monsters")
	npcs = _load_folder("npcs")
	villages = _index_by_id(_load_json("villages.json"))
	progression = _load_json("progression.json")
	skills = _load_json("skills.json")
	elements = _load_json("elements.json")
	var mdir := DirAccess.open(_root + "maps")
	if mdir != null:
		for f in mdir.get_files():
			if f.ends_with(".json"):
				var m: Dictionary = _load_json("maps/" + f)
				maps[m["id"]] = m
	print("GameData: %d jutsus, %d itens, %d monstros (de %s)" % [jutsus.size(), items.size(), monsters.size(), _root])

func _data_root() -> String:
	if OS.has_feature("editor"):
		var client_dir := ProjectSettings.globalize_path("res://").rstrip("/")
		return client_dir.get_base_dir().path_join("data") + "/"
	return "res://data/"

func _load_folder(folder: String) -> Dictionary:
	var result := {}
	var dir := DirAccess.open(_root + folder)
	if dir == null:
		push_error("GameData: pasta não encontrada: " + _root + folder)
		return result
	for file in dir.get_files():
		if file.ends_with(".json"):
			result.merge(_index_by_id(_load_json(folder + "/" + file)))
	return result

func _load_json(rel_path: String) -> Variant:
	var text := FileAccess.get_file_as_string(_root + rel_path)
	var parsed = JSON.parse_string(text)
	if parsed == null:
		push_error("GameData: JSON inválido ou ausente: " + rel_path)
	return parsed

func _index_by_id(list: Variant) -> Dictionary:
	var out := {}
	if list is Array:
		for obj in list:
			out[obj["id"]] = obj
	return out

## XP total necessária para atingir `level`.
func xp_for_level(level: int) -> int:
	return 50 * level * level + 50 * level
