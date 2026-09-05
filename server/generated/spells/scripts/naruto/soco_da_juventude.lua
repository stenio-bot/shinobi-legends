-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Soco da Juventude: Um soco carregado de puro vigor físico, sem chakra nenhum envolvido.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_PHYSICALDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, CONST_ME_HITAREA)

function onGetFormulaValues(player, level, maglevel)
	local base = 15.8 + level * 0.887 + maglevel * 0.547
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 1000)
condition:setFormula(-0.9, 0, -0.9, 0)
combat:addCondition(condition)  -- stun, chance 0.3

function onCastSpell(creature, variant)
	return combat:execute(creature, variant)
end
