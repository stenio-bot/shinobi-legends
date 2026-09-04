class_name FloatingText
extends Label

func setup(text_value: String, color: Color) -> void:
	text = text_value
	add_theme_font_size_override("font_size", 14)
	add_theme_color_override("font_color", color)
	add_theme_color_override("font_outline_color", Color.BLACK)
	add_theme_constant_override("outline_size", 4)
	z_index = 100

func _ready() -> void:
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(self, "position", position + Vector2(0, -28), 0.8)
	tween.tween_property(self, "modulate:a", 0.0, 0.8).set_delay(0.3)
	tween.chain().tween_callback(queue_free)
