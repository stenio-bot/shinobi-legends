-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.

-- Suiton: Proj\xE9til de \xC1gua: Bala de \xE1gua comprimida.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_ICEDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 204)
combat:setParameter(COMBAT_PARAM_DISTANCEEFFECT, 61)

function onGetFormulaValues(player, level, maglevel)
	local base = 3.7 + level * 5.25 + maglevel * 0.11
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 3000)
condition:setFormula(-0.3, 0, -0.3, 0)
combat:addCondition(condition)  -- slow, chance 0.25

function onCastSpell(creature, variant)
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(creature:getPosition(), "sfx_splash") end
	return combat:execute(creature, variant)
end
