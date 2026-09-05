-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.
-- Coloque em data/scripts/naruto/rank_look.lua (revscriptsys carrega sozinho).
-- T\xEDtulo de rank no /look (docs/lore/progressao.md): usa o EventCallback nativo do TFS 1.4.2
-- (data/scripts/lib/event_callbacks.lua, mesmo padr\xE3o de
-- data/scripts/eventcallbacks/player/default_onLook.lua) em vez de editar
-- data/events/scripts/player.lua \xE0 m\xE3o \x97 o default_onLook roda primeiro (ordem alfab\xE9tica de
-- pasta) e monta "You see ...", este s\xF3 acrescenta uma linha com o rank.
--
-- T\xEDtulo de conquista (opcional, docs/sistemas/progressao-servidor.md se\xE7\xE3o Conquistas): sem
-- UI de sele\xE7\xE3o (fora do escopo desta miss\xE3o), mostra o t\xEDtulo da \xDALTIMA conquista desbloqueada
-- (NarutoAchievements.LAST_UNLOCKED) se houver uma \x97 simplifica\xE7\xE3o deliberada e documentada.
local ec = EventCallback
ec.onLook = function(self, thing, position, distance, description)
	if NarutoRanks and thing:isCreature() and thing:isPlayer() then
		local rank = NarutoRanks.get(thing)
		description = description .. "\nRank: " .. rank.title .. "."
	end
	if NarutoAchievements and thing:isCreature() and thing:isPlayer() then
		local idx = thing:getStorageValue(NarutoAchievements.LAST_UNLOCKED)
		local a = (idx and idx > 0) and NarutoAchievements.list[idx] or nil
		if a then
			description = description .. "\nT\xEDtulo: " .. a.title .. "."
		end
	end
	return description
end
ec:register()
