-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.
-- Coloque em data/scripts/naruto/tasks.lua (revscriptsys carrega sozinho).
local killEvent = CreatureEvent("NarutoTaskKill")
function killEvent.onKill(player, target)
	if not target:isMonster() then return true end
	local name = target:getName()
	for _, t in ipairs(NarutoTasks.list) do
		if t.monster == name then
			local prog = player:getStorageValue(t.progressStorage)
			if prog >= 0 and prog < t.count then
				player:setStorageValue(t.progressStorage, prog + 1)
				player:sendTextMessage(MESSAGE_EVENT_ADVANCE, t.name .. ": " .. (prog + 1) .. "/" .. t.count)
			end
		end
	end
	return true
end
killEvent:register()

local login = CreatureEvent("NarutoTaskLogin")
function login.onLogin(player)
	player:registerEvent("NarutoTaskKill")
	return true
end
login:register()

--- !tarefas: lista s\xF3 as tarefas ATIVAS (aceitas) do jogador, com progresso. Para aceitar/
--- entregar, fale com o Mestre de Tarefas da regi\xE3o (palavras-chave {tarefa}/{entregar}).
local talk = TalkAction("!tarefas")
function talk.onSay(player, words, param)
	local lines = {}
	for _, t in ipairs(NarutoTasks.list) do
		local prog = player:getStorageValue(t.progressStorage)
		if prog >= 0 then
			if prog < t.count then
				lines[#lines + 1] = t.name .. ": " .. prog .. "/" .. t.count .. " " .. t.monster
			else
				lines[#lines + 1] = t.name .. ": PRONTA (entregue com " .. t.npcName .. ")"
			end
		end
	end
	if #lines == 0 then
		player:sendTextMessage(MESSAGE_INFO_DESCR, "Nenhuma tarefa ativa. Fale com um Mestre de Tarefas da regi\xE3o e diga {tarefa} para aceitar uma.")
	else
		player:sendTextMessage(MESSAGE_INFO_DESCR, table.concat(lines, " | "))
	end
	return false
end
talk:separator(" ")
talk:register()
