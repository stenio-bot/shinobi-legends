-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Agulhas Incendiárias: Agulhas finas envoltas em chamas, lançadas com precisão cirúrgica.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_FIREDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 200)
combat:setParameter(COMBAT_PARAM_DISTANCEEFFECT, 67)

function onGetFormulaValues(player, level, maglevel)
	local base = 25.2 + level * 1.324 + maglevel * 1.125
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

local condition = Condition(CONDITION_FIRE)
condition:setParameter(CONDITION_PARAM_DELAYED, 1)
condition:addDamage(4, 1000, -3)
combat:addCondition(condition)  -- chance 0.3: TODO aplicar chance via callback

function onCastSpell(creature, variant)
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(creature:getPosition(), "sfx_metal_throw") end
	return combat:execute(creature, variant)
end
