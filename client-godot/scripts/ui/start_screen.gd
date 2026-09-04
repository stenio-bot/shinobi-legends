class_name StartScreen
extends CanvasLayer

signal village_chosen(village_id: String)

func _ready() -> void:
	layer = 10
	var bg := ColorRect.new()
	bg.color = Color("101418")
	bg.size = Vector2(1280, 720)
	add_child(bg)
	var box := VBoxContainer.new()
	box.position = Vector2(340, 120)
	box.custom_minimum_size = Vector2(600, 0)
	add_child(box)
	var title := Label.new()
	title.text = "SHINOBI LEGENDS"
	title.add_theme_font_size_override("font_size", 40)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(title)
	var sub := Label.new()
	sub.text = "Escolha sua vila. Ela define seu elemento, sua skill favorita e seu primeiro jutsu."
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(sub)
	box.add_child(Control.new())
	for vid in GameData.villages:
		var v: Dictionary = GameData.villages[vid]
		var b := Button.new()
		var jutsu_name: String = GameData.jutsus[v["starting_jutsus"][0]]["name"]
		b.text = "%s\nElemento %s · Skill favorita: %s · Jutsu inicial: %s" % [v["name"], v["element"].capitalize(), v["bonus_skill"].capitalize(), jutsu_name]
		b.custom_minimum_size = Vector2(600, 70)
		b.pressed.connect(func() -> void:
			village_chosen.emit(vid)
			queue_free())
		box.add_child(b)
