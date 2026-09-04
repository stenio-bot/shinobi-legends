## Mapa em grid gerado a partir de data/maps/<id>.json com tiles placeholder via _draw().
## Marco 4+ troca o desenho por TileMapLayer com arte; a API (is_walkable, blocks_sight, W, H) fica.
class_name WorldMap
extends Node2D

const TILE := 32
static var W := 48
static var H := 36

enum T { GRASS, TREE, PATH, WATER, SWAMP, DEADTREE }

const COLORS := {
	T.GRASS: Color("4f8a3a"), T.TREE: Color("22461c"), T.PATH: Color("b9a172"),
	T.WATER: Color("2f6fb3"), T.SWAMP: Color("4a5a2e"), T.DEADTREE: Color("2e2a1e"),
}

var def: Dictionary
var tiles: Array = []  # tiles[y][x]
var start_cell := Vector2i(12, 18)

func load_def(map_def: Dictionary) -> void:
	def = map_def
	W = int(def["width"])
	H = int(def["height"])
	start_cell = Vector2i(int(def["start"]["x"]), int(def["start"]["y"]))
	generate()
	queue_redraw()

func zone_at(c: Vector2i) -> Dictionary:
	for z in def.get("zones", []):
		var r: Array = z["rect"]
		if c.x >= int(r[0]) and c.y >= int(r[1]) and c.x < int(r[0]) + int(r[2]) and c.y < int(r[1]) + int(r[3]):
			return z
	return {}

func generate() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = int(def.get("seed", 42))
	var swamp_x := W  # onde começa o pântano (2ª zona), se existir
	var zones: Array = def.get("zones", [])
	if zones.size() >= 2:
		swamp_x = int(zones[1]["rect"][0])
	tiles.clear()
	for y in H:
		var row := []
		for x in W:
			var is_swamp := x >= swamp_x
			var t: int = T.SWAMP if is_swamp else T.GRASS
			if x == 0 or y == 0 or x == W - 1 or y == H - 1:
				t = T.DEADTREE if is_swamp else T.TREE
			elif is_swamp:
				var r := rng.randf()
				if r < 0.07: t = T.DEADTREE
				elif r < 0.19: t = T.WATER
			elif rng.randf() < 0.08:
				t = T.TREE
			row.append(t)
		tiles.append(row)
	# lago da floresta
	for y in range(20, 26):
		for x in range(30, 37):
			if x < W and y < H:
				tiles[y][x] = T.WATER
	# estradas: horizontal no meio, vertical na vila
	var road_y := start_cell.y
	for x in range(2, W - 2):
		tiles[road_y][x] = T.PATH
	for y in range(2, H - 2):
		tiles[y][start_cell.x] = T.PATH
	# clareira inicial
	for y in range(start_cell.y - 2, start_cell.y + 3):
		for x in range(start_cell.x - 2, start_cell.x + 3):
			if tiles[y][x] == T.TREE:
				tiles[y][x] = T.GRASS

func in_bounds(c: Vector2i) -> bool:
	return c.x >= 0 and c.y >= 0 and c.x < W and c.y < H

func is_walkable(c: Vector2i) -> bool:
	if not in_bounds(c):
		return false
	var t: int = tiles[c.y][c.x]
	return t == T.GRASS or t == T.PATH or t == T.SWAMP

func blocks_sight(c: Vector2i) -> bool:
	if not in_bounds(c):
		return true
	var t: int = tiles[c.y][c.x]
	return t == T.TREE or t == T.DEADTREE

## Linha de visão (Bresenham) entre duas células; ignora as extremidades.
func has_line_of_sight(a: Vector2i, b: Vector2i) -> bool:
	var dx := absi(b.x - a.x)
	var dy := -absi(b.y - a.y)
	var sx := 1 if a.x < b.x else -1
	var sy := 1 if a.y < b.y else -1
	var err := dx + dy
	var c := a
	while c != b:
		var e2 := 2 * err
		if e2 >= dy:
			err += dy
			c.x += sx
		if e2 <= dx:
			err += dx
			c.y += sy
		if c != b and blocks_sight(c):
			return false
	return true

func force_walkable(c: Vector2i) -> void:
	if in_bounds(c):
		tiles[c.y][c.x] = T.SWAMP if c.x >= _swamp_x() else T.GRASS

func _swamp_x() -> int:
	var zones: Array = def.get("zones", [])
	return int(zones[1]["rect"][0]) if zones.size() >= 2 else W

func _draw() -> void:
	for y in H:
		for x in W:
			var r := Rect2(x * TILE, y * TILE, TILE, TILE)
			var t: int = tiles[y][x]
			draw_rect(r, COLORS[t])
			match t:
				T.TREE: draw_circle(r.get_center(), 11, Color("2f6b28"))
				T.DEADTREE:
					draw_line(r.get_center() + Vector2(0, 12), r.get_center() + Vector2(0, -12), Color("5a4a30"), 3.0)
					draw_line(r.get_center(), r.get_center() + Vector2(8, -8), Color("5a4a30"), 2.0)
				T.WATER: draw_rect(Rect2(r.position + Vector2(6, 12), Vector2(12, 3)), Color("6fa3e0"))
				T.SWAMP:
					if (x * 7 + y * 13) % 5 == 0:
						draw_rect(Rect2(r.position + Vector2(10, 14), Vector2(10, 4)), Color("3a4a22"))
	var grid_color := Color(0, 0, 0, 0.08)
	for x in W + 1:
		draw_line(Vector2(x * TILE, 0), Vector2(x * TILE, H * TILE), grid_color)
	for y in H + 1:
		draw_line(Vector2(0, y * TILE), Vector2(W * TILE, y * TILE), grid_color)
