-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.

-- Kunai Marcada: Uma kunai selada, lançada para marcar o alvo e permitir um salto instantâneo depois.
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
	return combat:execute(creature, variant)
end
