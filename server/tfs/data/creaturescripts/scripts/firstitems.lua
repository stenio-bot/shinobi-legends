-- Shinobi Legends: o kit vanilla do TFS (club, jacket, bag, apple) foi removido — ele ocupava
-- os slots de corpo/arma/mochila antes do kit da vila (data/villages.json) ser entregue em
-- character_switch.lua (gerado), deixando o Genin novo com um porrete em vez da kunai
-- (playtest rodada 2, 2026-09-05). Aqui so' a mochila de couro (backpack_leather, id 1988),
-- que nao faz parte do kit por vila.
local BACKPACK_LEATHER = 1988

function onLogin(player)
	if player:getLastLoginSaved() == 0 then
		player:addItem(BACKPACK_LEATHER, 1)
	end
	return true
end
