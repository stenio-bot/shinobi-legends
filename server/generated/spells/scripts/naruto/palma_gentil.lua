-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Palma Gentil: Um toque preciso em pontos de chakra que trava os movimentos do alvo.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_PHYSICALDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 224)

function onGetFormulaValues(player, level, maglevel)
	local base = 22 + level * 1.0 + maglevel * 0.9
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 3000)
condition:setFormula(-0.3, 0, -0.3, 0)
combat:addCondition(condition)  -- slow, chance 0.3

function onCastSpell(creature, variant)
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(creature:getPosition(), "sfx_punch") end
	return combat:execute(creature, variant)
end
