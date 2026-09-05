-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.

-- Kunai Marcada: Uma kunai selada, lan\xE7ada para marcar o alvo e permitir um salto instant\xE2neo depois.
local combat = Combat()
combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_PHYSICALDAMAGE)
combat:setParameter(COMBAT_PARAM_EFFECT, 224)
combat:setParameter(COMBAT_PARAM_DISTANCEEFFECT, 65)

function onGetFormulaValues(player, level, maglevel)
	local base = 18 + level * 1.0 + maglevel * 0.8
	return -math.floor(base * 0.9), -math.floor(base * 1.1)
end
combat:setCallback(CALLBACK_PARAM_LEVELMAGICVALUE, "onGetFormulaValues")

function onCastSpell(creature, variant)
	if NarutoJson.broadcastSfx then NarutoJson.broadcastSfx(creature:getPosition(), "sfx_metal_throw") end
	return combat:execute(creature, variant)
end
