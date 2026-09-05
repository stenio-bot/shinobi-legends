-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Suiton: Prisão de Água: Uma esfera de água prende o alvo no lugar e o sufoca lentamente.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_ICEDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 207)

function onGetFormulaValues(player, level, maglevel)
	local base = 30.6 + level * 1.17 + maglevel * 0.9
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 3000)
condition:setFormula(-0.9, 0, -0.9, 0)
combat:addCondition(condition)  -- paralyze, chance 0.7

function onCastSpell(creature, variant)
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(creature:getPosition(), "sfx_bubble") end
	return combat:execute(creature, variant)
end
