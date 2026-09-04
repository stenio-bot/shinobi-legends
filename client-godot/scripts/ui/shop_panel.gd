class_name ShopPanel
extends PanelContainer

var player: Player
var npc_data: Dictionary
var sell_list: ItemList   # o que o NPC vende
var buy_list: ItemList    # o que o player pode vender
var title: Label
var _buy_indices: Array[int] = []

func setup(p: Player) -> void:
	player = p
	position = Vector2(640 - 260, 80)
	custom_minimum_size = Vector2(520, 480)
	var box := VBoxContainer.new()
	add_child(box)
	title = Label.new()
	box.add_child(title)
	var cols := HBoxContainer.new()
	box.add_child(cols)
	var left := VBoxContainer.new()
	left.custom_minimum_size = Vector2(250, 0)
	cols.add_child(left)
	left.add_child(_header("NPC vende"))
	sell_list = ItemList.new()
	sell_list.custom_minimum_size = Vector2(0, 340)
	sell_list.add_theme_font_size_override("font_size", 12)
	sell_list.item_activated.connect(func(_i: int) -> void: _buy())
	left.add_child(sell_list)
	var bb := Button.new()
	bb.text = "Comprar"
	bb.pressed.connect(_buy)
	left.add_child(bb)
	var right := VBoxContainer.new()
	right.custom_minimum_size = Vector2(250, 0)
	cols.add_child(right)
	right.add_child(_header("Você vende"))
	buy_list = ItemList.new()
	buy_list.custom_minimum_size = Vector2(0, 340)
	buy_list.add_theme_font_size_override("font_size", 12)
	buy_list.item_activated.connect(func(_i: int) -> void: _sell())
	right.add_child(buy_list)
	var sb := Button.new()
	sb.text = "Vender 1"
	sb.pressed.connect(_sell)
	right.add_child(sb)
	var close := Button.new()
	close.text = "Fechar (Esc)"
	close.pressed.connect(func() -> void: visible = false)
	box.add_child(close)
	visible = false

func _header(t: String) -> Label:
	var l := Label.new()
	l.text = t
	l.add_theme_color_override("font_color", Color("ffd27a"))
	return l

func open_for(npc: NPC) -> void:
	npc_data = npc.data
	visible = true
	refresh()

func refresh() -> void:
	title.text = "%s · Seu ryo: %d" % [npc_data.get("name", "Loja"), player.ryo]
	sell_list.clear()
	for id in npc_data.get("sells", []):
		var it: Dictionary = GameData.items[id]
		sell_list.add_item("%s — %d ryo" % [it["name"], int(it["buy_price"])])
		sell_list.set_item_tooltip(sell_list.item_count - 1, it.get("description", ""))
	buy_list.clear()
	_buy_indices.clear()
	var types: Array = npc_data.get("buys_types", [])
	for i in player.inventory.size:
		var s = player.inventory.slots[i]
		if s == null:
			continue
		var it: Dictionary = GameData.items[s["id"]]
		if it["type"] in types and int(it["sell_price"]) > 0:
			buy_list.add_item("%s x%d — %d ryo" % [it["name"], int(s["qty"]), int(it["sell_price"])])
			_buy_indices.append(i)

func _buy() -> void:
	var sel := sell_list.get_selected_items()
	if sel.is_empty():
		return
	var id: String = npc_data["sells"][sel[0]]
	var it: Dictionary = GameData.items[id]
	var price := int(it["buy_price"])
	if player.ryo < price:
		player.world.hud.log_msg("Ryo insuficiente.")
		return
	if player.inventory.add(id, 1) > 0:
		player.world.hud.log_msg("Mochila cheia.")
		return
	player.ryo -= price
	player.world.hud.log_msg("Comprou %s por %d ryo." % [it["name"], price])
	player.stats_changed.emit()
	refresh()

func _sell() -> void:
	var sel := buy_list.get_selected_items()
	if sel.is_empty() or sel[0] >= _buy_indices.size():
		return
	var i := _buy_indices[sel[0]]
	var s = player.inventory.slots[i]
	var it: Dictionary = GameData.items[s["id"]]
	player.inventory.remove_at(i, 1)
	player.ryo += int(it["sell_price"])
	player.world.hud.log_msg("Vendeu %s por %d ryo." % [it["name"], int(it["sell_price"])])
	player.stats_changed.emit()
	refresh()
