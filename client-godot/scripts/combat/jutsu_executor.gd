## Executa jutsus definidos em data/jutsus/*.json.
class_name JutsuExecutor

const ELEMENT_COLORS := {
	"katon": Color("ff6a2a"), "suiton": Color("3f8fff"), "raiton": Color("f2e94e"),
	"doton": Color("a3743d"), "fuuton": Color("b8f0d8"), "none": Color("dddddd"),
}

static func roll_effects(target: Entity, effects: Array, source: Entity) -> void:
	if target == null or not target.alive:
		return
	var rng := RandomNumberGenerator.new()
	rng.randomize()
	for e in effects:
		if rng.randf() < float(e.get("chance", 1.0)):
			target.apply_effect(e, source)

## Retorna "" se lançou, ou a razão da falha.
static func cast(world: GameWorld, caster: Player, j: Dictionary) -> String:
	var jid: String = j["id"]
	if not caster.can_act():
		return "Você está atordoado."
	if caster.level < int(j["required_level"]):
		return "Precisa de level %d." % int(j["required_level"])
	if caster.chakra < int(j["chakra_cost"]):
		return "Chakra insuficiente."
	if caster.cooldowns.get(jid, 0.0) > 0.0:
		return "Ainda em recarga."
	var skill_id: String = j.get("skill", "ninjutsu")
	var skill_val := caster.skill_value(skill_id)
	var color: Color = ELEMENT_COLORS.get(j["element"], Color.WHITE)
	var effects: Array = j.get("effects", [])
	var hit_any := false

	match j["type"]:
		"projectile", "target":
			var t := caster.target
			if t == null or not t.alive:
				return "Sem alvo."
			if caster.chebyshev_to(t) > int(j["range"]):
				return "Alvo fora de alcance."
			caster.face_towards(t)
			var dmg := _damage(j, caster, skill_val, t)
			if j["type"] == "projectile":
				world.spawn_projectile(caster, t, dmg, color, effects)
			else:
				world.spawn_area_flash([t.cell], color)
				t.take_damage(dmg, caster)
				roll_effects(t, effects, caster)
			hit_any = true
		"area", "beam":
			var shape: String = j.get("shape", "circle_r1")
			var cells := Shapes.cells(shape, caster.cell, caster.facing)
			world.spawn_area_flash(cells, color)
			for c in cells:
				var e := world.entity_at(c)
				if e is Monster and e.alive:
					var dmg := _damage(j, caster, skill_val, e)
					e.take_damage(dmg, caster)
					roll_effects(e, effects, caster)
					hit_any = true
		"self":
			_cast_self(world, caster, j, effects, color)
			hit_any = true

	caster.chakra -= int(j["chakra_cost"])
	caster.cooldowns[jid] = float(j["cooldown_s"])
	caster.skills.raise(skill_id, caster.skill_multiplier(skill_id))
	caster.stats_changed.emit()
	if not hit_any:
		world.hud.log_msg("%s não acertou nada." % j["name"])
	return ""

static func _damage(j: Dictionary, caster: Player, skill_val: int, target: Entity) -> int:
	var target_el: String = "none"
	if target is Monster:
		target_el = target.data.get("element", "none")
	var mult := DamageCalc.element_multiplier(j["element"], target_el, GameData.elements)
	var dmg := DamageCalc.jutsu(j, caster.level, skill_val, mult, caster.rng)
	dmg = DamageCalc.apply_crit(dmg, caster.crit_chance, caster.rng)
	return maxi(1, dmg - int(target.defense * 0.25))

static func _cast_self(world: GameWorld, caster: Player, j: Dictionary, effects: Array, color: Color) -> void:
	match j["id"]:
		"kawarimi":
			caster.invulnerable = true
			world.spawn_area_flash([caster.cell], color)
			var back := caster.cell - caster.facing * 2
			if not caster.teleport(back):
				caster.teleport(caster.cell - caster.facing)
			world.get_tree().create_timer(1.0).timeout.connect(func() -> void:
				caster.invulnerable = false
				caster.queue_redraw())
		"bunshin":
			for m in world.monsters:
				if m.alive and m.chebyshev_to(caster) <= 8:
					m.distract(6.0)
			world.spawn_area_flash(Shapes.cells("circle_r1", caster.cell, caster.facing), color)
		_:
			world.spawn_area_flash([caster.cell], color)
	roll_effects(caster, effects, caster)
