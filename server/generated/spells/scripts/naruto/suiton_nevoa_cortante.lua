-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Suiton: Névoa Cortante: Uma névoa densa de gotículas afiadas cobre uma área maior à frente, encharcando e retardando quem passar.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_ICEDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 206)
local area = {
	{1, 1, 1, 1, 1},
	{0, 1, 1, 1, 0},
	{0, 0, 1, 0, 0},
	{0, 0, 2, 0, 0}
}
combat:setArea(createCombatArea(area))

function onGetFormulaValues(player, level, maglevel)
	local base = 5.25 + level * 0.315 + maglevel * 0.227
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 5000)
condition:setFormula(-0.45, 0, -0.45, 0)
combat:addCondition(condition)  -- slow, chance 0.6

function onCastSpell(creature, variant)
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(creature:getPosition(), "sfx_mist") end
	return combat:execute(creature, variant)
end
