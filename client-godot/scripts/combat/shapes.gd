## Formas de área para jutsus, relativas à célula do lançador e à direção.
## Formatos: circle_rN, cross_rN, line_N, cone_N
class_name Shapes

static func cells(shape: String, origin: Vector2i, facing: Vector2i) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	var parts := shape.split("_")
	if parts.size() < 2:
		return out
	var kind := parts[0]
	var n := int(parts[1].trim_prefix("r"))
	if facing == Vector2i.ZERO:
		facing = Vector2i.DOWN
	var perp := Vector2i(-facing.y, facing.x)
	match kind:
		"circle":
			for dy in range(-n, n + 1):
				for dx in range(-n, n + 1):
					if dx != 0 or dy != 0:
						out.append(origin + Vector2i(dx, dy))
		"cross":
			for d in [Vector2i.UP, Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT]:
				for k in range(1, n + 1):
					out.append(origin + d * k)
		"line":
			for k in range(1, n + 1):
				out.append(origin + facing * k)
		"cone":
			for k in range(1, n + 1):
				var center := origin + facing * k
				for w in range(-(k - 1), k):
					out.append(center + perp * w)
	return out
