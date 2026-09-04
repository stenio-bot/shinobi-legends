class_name HUD
extends CanvasLayer

var hp_bar: ProgressBar
var chakra_bar: ProgressBar
var info_label: Label
var target_label: Label
var quest_label: Label
var zone_label: Label
var log_box: RichTextLabel
var _lines: Array[String] = []

func _ready() -> void:
	var panel := PanelContainer.new()
	panel.position = Vector2(12, 12)
	panel.custom_minimum_size = Vector2(260, 0)
	add_child(panel)
	var box := VBoxContainer.new()
	panel.add_child(box)

	info_label = Label.new()
	box.add_child(info_label)
	hp_bar = _make_bar(Color("d63c3c"))
	box.add_child(hp_bar)
	chakra_bar = _make_bar(Color("3c7bd6"))
	box.add_child(chakra_bar)
	target_label = Label.new()
	target_label.text = "Alvo: nenhum (clique num monstro, Tab = mais próximo)"
	target_label.add_theme_font_size_override("font_size", 12)
	box.add_child(target_label)
	quest_label = Label.new()
	quest_label.add_theme_font_size_override("font_size", 12)
	quest_label.add_theme_color_override("font_color", Color("ffd27a"))
	box.add_child(quest_label)
	zone_label = Label.new()
	zone_label.add_theme_font_size_override("font_size", 12)
	zone_label.add_theme_color_override("font_color", Color("bbbbbb"))
	box.add_child(zone_label)

	log_box = RichTextLabel.new()
	log_box.bbcode_enabled = true
	log_box.scroll_active = false
	log_box.position = Vector2(12, 720 - 12 - 150)
	log_box.size = Vector2(520, 150)
	log_box.add_theme_font_size_override("normal_font_size", 13)
	add_child(log_box)

	var help := Label.new()
	help.text = "WASD: andar · clique: alvo/corpo/NPC · Tab: alvo · 1-0: jutsus · I: mochila · F5/F9: salvar/carregar"
	help.position = Vector2(1280 - 12 - 640, 12)
	help.size = Vector2(640, 20)
	help.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	help.add_theme_font_size_override("font_size", 12)
	add_child(help)

func _make_bar(fill: Color) -> ProgressBar:
	var bar := ProgressBar.new()
	bar.custom_minimum_size = Vector2(240, 18)
	bar.show_percentage = false
	var sb := StyleBoxFlat.new()
	sb.bg_color = fill
	bar.add_theme_stylebox_override("fill", sb)
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0, 0, 0, 0.5)
	bar.add_theme_stylebox_override("background", bg)
	return bar

func update_player(p: Player) -> void:
	hp_bar.max_value = p.max_hp
	hp_bar.value = p.hp
	chakra_bar.max_value = p.max_chakra
	chakra_bar.value = p.chakra
	var next_xp := GameData.xp_for_level(p.level + 1)
	var ql := p.active_quest_line()
	quest_label.text = ("Missão: " + ql) if ql != "" else "Sem missão ativa (fale com a Capitã Rin)"
	info_label.text = "Lv %d  XP %d/%d  HP %d/%d  CK %d/%d  Ryo %d" % [p.level, p.xp, next_xp, p.hp, p.max_hp, p.chakra, p.max_chakra, p.ryo]

func update_zone(z: Dictionary) -> void:
	if z.is_empty():
		zone_label.text = ""
	else:
		zone_label.text = "%s (lv %d–%d)" % [z["name"], int(z["level_range"][0]), int(z["level_range"][1])]

func update_target(t: Entity) -> void:
	if t == null:
		target_label.text = "Alvo: nenhum"
	else:
		target_label.text = "Alvo: %s  (%d/%d HP)" % [t.display_name, t.hp, t.max_hp]

func log_msg(text: String) -> void:
	_lines.append(text)
	if _lines.size() > 8:
		_lines.pop_front()
	log_box.text = "\n".join(_lines)
