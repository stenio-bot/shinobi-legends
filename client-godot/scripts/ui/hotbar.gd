class_name Hotbar
extends HBoxContainer

var player: Player
var buttons: Array[Button] = []

func setup(p: Player) -> void:
	player = p
	position = Vector2(640 - 5 * 66, 720 - 12 - 56)
	for i in 10:
		var b := Button.new()
		b.custom_minimum_size = Vector2(62, 56)
		b.add_theme_font_size_override("font_size", 10)
		b.focus_mode = Control.FOCUS_NONE
		b.pressed.connect(func() -> void: player.cast_slot(i))
		add_child(b)
		buttons.append(b)
	player.jutsus_changed.connect(refresh)
	refresh()

func refresh() -> void:
	for i in 10:
		var jid: String = player.hotbar[i] if i < player.hotbar.size() else ""
		var key := str((i + 1) % 10)
		if jid == "":
			buttons[i].text = key + "\n—"
			buttons[i].tooltip_text = ""
			continue
		var j: Dictionary = GameData.jutsus[jid]
		buttons[i].text = "%s\n%s\n%d ck" % [key, _short(j["name"]), int(j["chakra_cost"])]
		buttons[i].tooltip_text = "%s\n%s" % [j["name"], j.get("description", "")]

func _process(_d: float) -> void:
	for i in 10:
		var jid: String = player.hotbar[i] if i < player.hotbar.size() else ""
		if jid == "":
			continue
		var cd := float(player.cooldowns.get(jid, 0.0))
		buttons[i].disabled = cd > 0.0
		if cd > 0.0:
			buttons[i].text = "%s\n%.1fs" % [str((i + 1) % 10), cd]
		elif buttons[i].text.ends_with("s") and not buttons[i].text.ends_with("ck"):
			refresh()

static func _short(name: String) -> String:
	var n := name
	if ": " in n:
		n = n.split(": ")[1]
	return n.substr(0, 11)
