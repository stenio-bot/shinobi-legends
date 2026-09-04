## Mochila com slots e stacks. Itens são {id, qty}.
class_name Inventory
extends RefCounted

signal changed

var size := 20
var slots: Array = []  # Dictionary ou null

func _init(p_size: int = 20) -> void:
	size = p_size
	slots.resize(size)

func stack_max(id: String) -> int:
	return int(GameData.items.get(id, {}).get("stack_max", 1))

## Retorna quantidade que NÃO coube.
func add(id: String, qty: int = 1) -> int:
	var smax := stack_max(id)
	if smax > 1:
		for s in slots:
			if s != null and s["id"] == id and int(s["qty"]) < smax:
				var take := mini(qty, smax - int(s["qty"]))
				s["qty"] = int(s["qty"]) + take
				qty -= take
				if qty == 0:
					changed.emit()
					return 0
	for i in size:
		if slots[i] == null:
			var take := mini(qty, smax)
			slots[i] = {"id": id, "qty": take}
			qty -= take
			if qty == 0:
				break
	changed.emit()
	return qty

func count(id: String) -> int:
	var n := 0
	for s in slots:
		if s != null and s["id"] == id:
			n += int(s["qty"])
	return n

func remove(id: String, qty: int = 1) -> bool:
	if count(id) < qty:
		return false
	for i in size:
		var s = slots[i]
		if s != null and s["id"] == id:
			var take := mini(qty, int(s["qty"]))
			s["qty"] = int(s["qty"]) - take
			qty -= take
			if int(s["qty"]) == 0:
				slots[i] = null
			if qty == 0:
				break
	changed.emit()
	return true

func remove_at(i: int, qty: int = 1) -> void:
	var s = slots[i]
	if s == null:
		return
	s["qty"] = int(s["qty"]) - qty
	if int(s["qty"]) <= 0:
		slots[i] = null
	changed.emit()

func free_slots() -> int:
	var n := 0
	for s in slots:
		if s == null:
			n += 1
	return n

func used_slots() -> int:
	return size - free_slots()

func to_array() -> Array:
	return slots.duplicate(true)

func from_array(a: Array) -> void:
	slots.resize(size)
	for i in size:
		slots[i] = null
		if i < a.size() and a[i] != null:
			slots[i] = {"id": a[i]["id"], "qty": int(a[i]["qty"])}
	changed.emit()
