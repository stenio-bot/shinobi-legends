-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.

-- Doton: Bala de Lama: Uma bala de lama endurecida disparada em alta velocidade.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_EARTHDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 215)
combat:setParameter(COMBAT_PARAM_DISTANCEEFFECT, 63)

function onGetFormulaValues(player, level, maglevel)
	local base = 4.0 + level * 5.35 + maglevel * 0.115
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_PARALYZE)
condition:setParameter(CONDITION_PARAM_TICKS, 3000)
condition:setFormula(-0.25, 0, -0.25, 0)
combat:addCondition(condition)  -- slow, chance 0.3

function onCastSpell(creature, variant)
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(creature:getPosition(), "sfx_splat") end
	return combat:execute(creature, variant)
end
