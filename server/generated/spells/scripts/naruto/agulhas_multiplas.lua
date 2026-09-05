-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Agulhas Multiplas: Uma saraivada de agulhas de metal lancadas contra o alvo.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_PHYSICALDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 224)
combat:setParameter(COMBAT_PARAM_DISTANCEEFFECT, 67)

function onGetFormulaValues(player, level, maglevel)
	local base = 16 + level * 0.9 + maglevel * 0.9
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

function onCastSpell(creature, variant)
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(creature:getPosition(), "sfx_metal_throw") end
	return combat:execute(creature, variant)
end
