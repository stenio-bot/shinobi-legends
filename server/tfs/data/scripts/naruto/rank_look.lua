-- GERADO por tools/export_tfs.py a partir de data/*.json. NÃO EDITE À MÃO.
-- Coloque em data/scripts/naruto/rank_look.lua (revscriptsys carrega sozinho).
-- Título de rank no /look (docs/lore/progressao.md): usa o EventCallback nativo do TFS 1.4.2
-- (data/scripts/lib/event_callbacks.lua, mesmo padrão de
-- data/scripts/eventcallbacks/player/default_onLook.lua) em vez de editar
-- data/events/scripts/player.lua à mão — o default_onLook roda primeiro (ordem alfabética de
-- pasta) e monta "You see ...", este só acrescenta uma linha com o rank.
local ec = EventCallback
ec.onLook = function(self, thing, position, distance, description)
	if NarutoRanks and thing:isCreature() and thing:isPlayer() then
		local rank = NarutoRanks.get(thing)
		description = description .. "\nRank: " .. rank.title .. "."
	end
	return description
end
ec:register()
