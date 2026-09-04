## Fórmulas puras de dano. Sem estado, sem nós. Testável.
## Ver docs/sistemas/combate-e-jutsus.md
class_name DamageCalc

static func element_multiplier(attacker_el: String, defender_el: String, elements: Dictionary) -> float:
	if attacker_el == "none" or defender_el == "none":
		return elements.get("neutral_multiplier", 1.0)
	var order: Array = elements["order"]
	var a := order.find(attacker_el)
	var d := order.find(defender_el)
	if a == -1 or d == -1:
		return 1.0
	if (a + 1) % order.size() == d:
		return elements["advantage_multiplier"]
	if (d + 1) % order.size() == a:
		return elements["disadvantage_multiplier"]
	return elements["neutral_multiplier"]

static func physical(weapon_attack: int, skill: int, target_defense: int, rng: RandomNumberGenerator) -> int:
	var raw := (weapon_attack + skill * 0.5) * rng.randf_range(0.8, 1.0) - target_defense * 0.5
	return maxi(1, int(round(raw)))

static func jutsu(j: Dictionary, level: int, ninjutsu: int, mult: float, rng: RandomNumberGenerator) -> int:
	var raw: float = (j["base_damage"] + level * j["level_scale"] + ninjutsu * j["skill_scale"]) \
		* mult * rng.randf_range(0.9, 1.1)
	return maxi(1, int(round(raw)))

static func apply_crit(damage: int, crit_chance: float, rng: RandomNumberGenerator) -> int:
	return int(damage * 1.5) if rng.randf() < crit_chance else damage
