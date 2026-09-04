class_name InventoryPanel
extends PanelContainer

var player: Player
var equip_list: ItemList
var bag_list: ItemList
var skills_label: Label
var title: Label
var equip_slots_shown: Array = []

func setup(p: Player) -> void:
	player = p
	position = Vector2(1280 - 12 - 330, 44)
	custom_minimum_size = Vector2(330, 620)
	size = Vector2(330, 620)
	clip_contents = true
	var box := VBoxContainer.new()
	add_child(box)
	title = Label.new()
	title.autowrap_mode = TextServer.AUTOWRAP_WORD
	box.add_child(title)
	skills_label = Label.new()
	skills_label.autowrap_mode = TextServer.AUTOWRAP_WORD
	skills_label.add_theme_font_size_override("font_size", 12)
	box.add_child(skills_label)
	box.add_child(_header("Equipamento (selecione + Desequipar)"))
	equip_list = ItemList.new()
	equip_list.custom_minimum_size = Vector2(0, 150)
	equip_list.add_theme_font_size_override("font_size", 12)
	box.add_child(equip_list)
	var b1 := Button.new()
	b1.text = "Desequipar"
	b1.pressed.connect(_unequip)
	box.add_child(b1)
	box.add_child(_header("Mochila (selecione + Equipar/Usar)"))
	bag_list = ItemList.new()
	bag_list.custom_minimum_size = Vector2(0, 220)
	bag_list.add_theme_font_size_override("font_size", 12)
	bag_list.item_activated.connect(func(_i: int) -> void: _use())
	box.add_child(bag_list)
	var row := HBoxContainer.new()
	box.add_child(row)
	var b2 := Button.new()
	b2.text = "Equipar / Usar"
	b2.pressed.connect(_use)
	row.add_child(b2)
	var b3 := Button.new()
	b3.text = "Jogar fora"
	b3.pressed.connect(_drop)
	row.add_child(b3)
	var b4 := Button.new()
	b4.text = "Fechar (I)"
	b4.pressed.connect(func() -> void: visible = false)
	row.add_child(b4)
	player.inventory.changed.connect(refresh)
	player.stats_changed.connect(refresh)
	visible = false

func _header(t: String) -> Label:
	var l := Label.new()
	l.text = t
	l.add_theme_font_size_override("font_size", 12)
	l.add_theme_color_override("font_color", Color("ffd27a"))
	return l

func refresh() -> void:
	if not visible:
		return
	title.text = "Mochila %d/%d · Peso %.1f/%.0f · Ryo %d · Def %d · Atk %d" % [player.inventory.used_slots(), player.inventory.size, player.total_weight(), player.capacity(), player.ryo, player.defense, player.weapon_attack]
	var parts: Array[String] = []
	for s in GameData.skills.get("skills", []):
		var id: String = s["id"]
		var pct := int(100.0 * float(player.skills.tries[id]) / player.skills.tries_needed(id))
		parts.append("%s %d (%d%%)" % [s["name"], player.skill_value(id), pct])
	skills_label.text = "  ".join(parts)
	var sel_e := equip_list.get_selected_items()
	equip_list.clear()
	equip_slots_shown.clear()
	for slot in Player.EQUIP_SLOTS:
		if player.equipment.has(slot):
			var it: Dictionary = GameData.items[player.equipment[slot]]
			equip_list.add_item("%s: %s" % [slot, it["name"]])
			equip_slots_shown.append(slot)
	if sel_e.size() > 0 and sel_e[0] < equip_list.item_count:
		equip_list.select(sel_e[0])
	var sel_b := bag_list.get_selected_items()
	bag_list.clear()
	for i in player.inventory.size:
		var s = player.inventory.slots[i]
		if s == null:
			bag_list.add_item("—")
			bag_list.set_item_disabled(i, true)
		else:
			var it: Dictionary = GameData.items[s["id"]]
			var txt: String = it["name"]
			if int(s["qty"]) > 1:
				txt += " x%d" % int(s["qty"])
			bag_list.add_item(txt)
			bag_list.set_item_tooltip(i, it.get("description", ""))
	if sel_b.size() > 0 and sel_b[0] < bag_list.item_count:
		bag_list.select(sel_b[0])

func _use() -> void:
	var sel := bag_list.get_selected_items()
	if sel.size() > 0:
		player.equip_from_bag(sel[0])
		refresh()

func _drop() -> void:
	var sel := bag_list.get_selected_items()
	if sel.size() > 0 and player.inventory.slots[sel[0]] != null:
		player.inventory.remove_at(sel[0], int(player.inventory.slots[sel[0]]["qty"]))
		refresh()

func _unequip() -> void:
	var sel := equip_list.get_selected_items()
	if sel.size() > 0 and sel[0] < equip_slots_shown.size():
		player.unequip(equip_slots_shown[sel[0]])
		refresh()

func toggle() -> void:
	visible = not visible
	refresh()
