class_name NPC
extends Entity

var data: Dictionary

func init_from_data(d: Dictionary) -> void:
	data = d
	display_name = d["name"]
	max_hp = 999
	hp = 999
	invulnerable = true
	color = Color("f0d060") if d.get("type") == "shop" else Color("60c0f0")

func _draw() -> void:
	draw_rect(Rect2(-14, -14, 28, 28), color)
	draw_rect(Rect2(-14, -14, 28, 28), Color.BLACK, false, 2.0)
	var tag := "$" if data.get("type") == "shop" else "!"
	draw_string(ThemeDB.fallback_font, Vector2(-5, 6), tag, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.BLACK)
