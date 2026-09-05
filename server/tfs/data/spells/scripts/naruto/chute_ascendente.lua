-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.

-- Chute Ascendente: Um chute ascendente que desequilibra o alvo e abre espa\xE7o para o pr\xF3ximo golpe.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_PHYSICALDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 224)

function onGetFormulaValues(player, level, maglevel)
	local base = 8.8 + level * 0.438 + maglevel * 0.372
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 2000)
condition:setFormula(-0.2, 0, -0.2, 0)
combat:addCondition(condition)  -- slow, chance 0.3

function onCastSpell(creature, variant)
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(creature:getPosition(), "sfx_kick") end
	return combat:execute(creature, variant)
end
