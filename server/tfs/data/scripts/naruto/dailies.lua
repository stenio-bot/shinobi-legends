-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.
-- Coloque em data/scripts/naruto/dailies.lua (revscriptsys carrega sozinho).
local killEvent = CreatureEvent("NarutoDailyKill")
function killEvent.onKill(player, target)
	if not target:isMonster() then return true end
	-- entry.monster (naruto_dailies.lua) e' cp1252 gerado; getName() do TFS e' UTF-8 -- converte
	-- antes de entrar em NarutoDailies.onKill (mesma regra de quests_kill.lua/tasks.lua).
	NarutoDailies.onKill(player, NarutoText.utf8ToCp1252(target:getName()))
	return true
end
killEvent:register()

local login = CreatureEvent("NarutoDailyLogin")
function login.onLogin(player)
	player:registerEvent("NarutoDailyKill")
	NarutoDailies.rollIfNeeded(player)
	return true
end
login:register()

--- !diaria: mostra as 3 di\xE1rias do dia (j\xE1 auto-aceitas, ver naruto_dailies.lua) e progresso.
--- !diaria entregar: entrega todas as que j\xE1 estiverem prontas.
local talk = TalkAction("!diaria")
function talk.onSay(player, words, param)
	NarutoDailies.rollIfNeeded(player)
	param = param and param:trim() or ""
	if param == "entregar" then
		local ok, xp, ryo = NarutoDailies.deliver(player)
		if ok then
			player:sendTextMessage(MESSAGE_EVENT_ADVANCE, string.format("Di\xE1rias entregues: +%d xp, +%d ryo.", xp, ryo))
		else
			player:sendCancelMessage("Nenhuma di\xE1ria pronta para entregar.")
		end
		return false
	end
	local lines = {}
	for slot = 1, 3 do
		local entry = NarutoDailies.slotEntry(player, slot)
		if entry then
			local prog = NarutoDailies.slotProgress(player, slot)
			if prog < entry.count then
				lines[#lines + 1] = string.format("%d) %s: %d/%d %s", slot, entry.name, math.max(prog, 0), entry.count, entry.monster)
			elseif prog == entry.count then
				lines[#lines + 1] = string.format("%d) %s: PRONTA (!diaria entregar)", slot, entry.name)
			else
				lines[#lines + 1] = string.format("%d) %s: j\xE1 entregue hoje", slot, entry.name)
			end
		end
	end
	player:sendTextMessage(MESSAGE_INFO_DESCR, #lines > 0 and table.concat(lines, " | ") or "Nenhuma di\xE1ria dispon\xEDvel para o seu level hoje.")
	return false
end
talk:separator(" ")
talk:register()
