-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Palma Dupla: Uma sequência dupla de palmas que atinge tudo à frente em rajada.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_PHYSICALDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 224)
local area = {
	{1, 1, 1},
	{0, 1, 0},
	{0, 2, 0}
}
combat:setArea(createCombatArea(area))

function onGetFormulaValues(player, level, maglevel)
	local base = 38 + level * 2.1 + maglevel * 1.25
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 1500)
condition:setFormula(-0.9, 0, -0.9, 0)
combat:addCondition(condition)  -- paralyze, chance 0.4

function onCastSpell(creature, variant)
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(creature:getPosition(), "sfx_double_hit") end
	return combat:execute(creature, variant)
end
