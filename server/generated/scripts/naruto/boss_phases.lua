-- GERADO por tools/export_tfs.py a partir de data/*.json. N\xC3O EDITE \xC0 M\xC3O.

-- Coloque em data/scripts/naruto/boss_phases.lua
local PHASES = {
	['O Vigia Ilus\xF3rio'] = {
		{hp = 100, mult = 1.0, message = 'Voc\xEA n\xE3o devia ter chegado t\xE3o longe.', summons = {}},
		{hp = 50, mult = 1.4, message = 'Ent\xE3o eu mesmo encerro isso.', summons = {}},
	},
	['O Mascarado das Sombras'] = {
		{hp = 100, mult = 1.0, message = 'Nada disso importa. Eu j\xE1 vi como isso termina.', summons = {}},
		{hp = 50, mult = 1.4, message = 'Vou parar de fingir que isso \xE9 um jogo.', summons = {}},
	},
	['O Portador dos Seis Caminhos'] = {
		{hp = 100, mult = 1.0, message = 'A dor \xE9 o \xFAnico caminho para a paz.', summons = {}},
		{hp = 60, mult = 1.0, message = 'Minha vontade n\xE3o cabe em um corpo s\xF3. Vejam com seus pr\xF3prios olhos.', summons = {{name = 'Caminho Invocado', count = 1}}},
		{hp = 25, mult = 1.5, message = 'Vou mostrar a voc\xEAs o verdadeiro poder de um deus.', summons = {}},
	},
	['O Ancestral da Nuvem Vermelha'] = {
		{hp = 100, mult = 1.0, message = 'Eu fundei isso tudo antes de qualquer um de voc\xEAs nascer.', summons = {}},
		{hp = 60, mult = 1.3, message = 'A Grande Guerra nunca terminou. S\xF3 mudou de nome.', summons = {}},
		{hp = 25, mult = 1.7, message = 'As vilas dizem que venceram aquela guerra. Mentira que contam h\xE1 uma gera\xE7\xE3o \x97 e o eco que voc\xEAs veem agora \xE9 a prova de que nada acabou.', summons = {{name = 'Eco Carmesim', count = 1}}},
	},
	['Espadachim da N\xE9voa'] = {
		{hp = 100, mult = 1.0, message = 'N\xE3o \xE9 nada pessoal, moleque. \xC9 s\xF3 o trabalho.', summons = {}},
		{hp = 60, mult = 1.0, message = 'Ainda n\xE3o. N\xE3o vou deixar que ele me leve ainda \x97 ele n\xE3o luta por dinheiro, luta por mim.', summons = {{name = 'Aprendiz Mascarado', count = 1}}},
		{hp = 25, mult = 1.6, message = 'Voc\xEAs tiraram tudo que eu tinha. Agora eu n\xE3o tenho mais nada a perder.', summons = {}},
	},
	['Chefe dos Bandidos'] = {
		{hp = 50, mult = 1.0, message = 'Venham, seus in\xFAteis! Essa \x91nuvem vermelha\x92 que anda nos vigiando n\xE3o fui eu quem escolhi, moleque \x97 fui s\xF3 pago.', summons = {{name = 'Bandido', count = 3}}},
		{hp = 20, mult = 1.5, message = 'N\xE3o vou cair para um genin!', summons = {}},
	},
	['O S\xF3cio Eterno'] = {
		{hp = 75, mult = 1.0, message = 'Mais um cora\xE7\xE3o ainda bate.', summons = {}},
		{hp = 50, mult = 1.3, message = 'As fendas ainda respondem ao meu chamado.', summons = {{name = 'Serpente de Magma', count = 1}}},
		{hp = 25, mult = 1.6, message = 'O \xFAltimo cora\xE7\xE3o \xE9 sempre o mais faminto.', summons = {}},
	},
	['Oni Ancestral'] = {
		{hp = 70, mult = 1.0, message = 'O c\xE9u \xE9 meu. Des\xE7am com ele.', summons = {{name = '\xC1guia do Trov\xE3o', count = 3}}},
		{hp = 40, mult = 1.0, message = 'Meus irm\xE3os ainda respiram sob o gelo!', summons = {{name = 'Oni da Geleira', count = 2}}},
		{hp = 15, mult = 1.7, message = 'Que a montanha caia junto comigo!', summons = {{name = 'Monge da Tempestade', count = 2}}},
	},
	['Desertor de Elite'] = {
		{hp = 40, mult = 1.3, message = 'Poder de verdade n\xE3o se pede. Se toma.', summons = {}},
	},
	['Marionetista das Ru\xEDnas'] = {
		{hp = 70, mult = 1.0, message = 'Voc\xEAs vieram brincar com meus bonecos?', summons = {{name = 'Marionete de Combate', count = 2}}},
		{hp = 40, mult = 1.0, message = 'A sentinela acorda. Corram.', summons = {{name = 'Sentinela de Pedra', count = 1}, {name = 'Marionete de Combate', count = 2}}},
		{hp = 15, mult = 1.5, message = 'Ent\xE3o eu mesmo corto os fios! A Nuvem Vermelha prometeu poder a quem guardasse este templo at\xE9 o fim \x97 e \xE9 isso que vou fazer.', summons = {}},
	},
	['Sapo Anci\xE3o'] = {
		{hp = 60, mult = 1.0, message = 'Meus filhos, devorem o intruso!', summons = {{name = 'Sapo Gigante', count = 2}}},
		{hp = 30, mult = 1.6, message = 'O p\xE2ntano inteiro se levanta contra voc\xEA!', summons = {{name = 'Sanguessuga Gigante', count = 3}}},
	},
	['Serpente Branca'] = {
		{hp = 100, mult = 1.0, message = 'Que curioso... um genin que ainda n\xE3o sabe correr.', summons = {}},
		{hp = 60, mult = 1.0, message = 'Chega de fingir que sou gente. Vejam o que eu realmente sou!', looktype = 890, summons = {{name = 'Cobra da Floresta', count = 3}}},
		{hp = 25, mult = 1.9, message = 'Minhas crias v\xE3o limpar o que sobrar de voc\xEA! Nem a organiza\xE7\xE3o que me expulsou quis ver o que eu virei \x97 e voc\xEAs v\xE3o descobrir por qu\xEA.', summons = {{name = 'Serpente Menor', count = 2}}},
	},
}

-- Estado por boss vivo: creatureId -> {name = string, mult = number (fase atual)}. Chave por
-- getId() (n\xE3o por nome) porque dois bosses do mesmo tipo podem existir ao mesmo tempo; o campo
-- `name` \xE9 revalidado no CreatureEvent de jogador abaixo para n\xE3o vazar dano se o id for
-- reciclado para OUTRO monstro depois que o boss morre (getId() do TFS \xE9 reaproveitado).
NarutoBossPhases = NarutoBossPhases or {}
NarutoBossPhases.state = NarutoBossPhases.state or {}

local fired = {}  -- monsterId -> \xEDndice da \xFAltima fase disparada
local ev = CreatureEvent("NarutoBossPhases")
function ev.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType, origin)
	local list = PHASES[creature:getName()]
	if not list then return primaryDamage, primaryType, secondaryDamage, secondaryType end
	local id = creature:getId()
	local pct = (creature:getHealth() - primaryDamage) * 100 / creature:getMaxHealth()
	local idx = fired[id] or 0
	while idx < #list and pct <= list[idx + 1].hp do
		idx = idx + 1
		local ph = list[idx]
		if ph.message ~= '' then creature:say(ph.message, TALKTYPE_MONSTER_YELL) end
		for _, s in ipairs(ph.summons) do
			for _ = 1, s.count do
				local pos = creature:getPosition()
				pos.x = pos.x + math.random(-2, 2); pos.y = pos.y + math.random(-2, 2)
				local mon = Game.createMonster(s.name, pos, false, true)
				if mon and attacker then mon:setTarget(attacker) end
			end
		end
		if ph.looktype then
			-- transforma\xE7\xE3o: troca o outfit do boss (ex.: humano -> serpente 2x2)
			local out = creature:getOutfit()
			out.lookType = ph.looktype
			out.lookHead, out.lookBody, out.lookLegs, out.lookFeet, out.lookAddons = 0, 0, 0, 0, 0
			creature:setOutfit(out)
			creature:getPosition():sendMagicEffect(CONST_ME_MAGIC_GREEN)
		end
		if ph.mult > 1.0 then
			-- Fase de "f\xFAria": cura pontual + acelera (o boss alcan\xE7a o alvo e bate mais vezes por
			-- minuto) E, de verdade, multiplica o dano \x97 o onHealthChange do MONSTRO (aqui) n\xE3o
			-- consegue reescrever a lista de <attack>/spells j\xE1 carregada do XML, ent\xE3o quem
			-- aplica o multiplicador \xE9 o CreatureEvent NarutoBossFury, registrado no onHealthChange
			-- do JOGADOR (o lado que recebe o golpe), lendo NarutoBossPhases.state[id].mult.
			local heal = math.floor(creature:getMaxHealth() * (ph.mult - 1.0) * 0.10)
			if heal > 0 then creature:addHealth(heal) end
			creature:changeSpeed(math.floor(creature:getBaseSpeed() * (ph.mult - 1.0) * 0.5))
			creature:getPosition():sendMagicEffect(CONST_ME_MAGIC_RED)
		end
	end
	fired[id] = idx
	-- Publica o multiplicador da fase atual pro NarutoBossFury ler quando o jogador apanhar.
	NarutoBossPhases.state[id] = {name = creature:getName(), mult = (idx > 0 and list[idx].mult) or 1.0}
	return primaryDamage, primaryType, secondaryDamage, secondaryType
end
ev:register()

-- Multiplica de verdade o dano (melee E de spell do boss \x97 os dois chegam aqui com `attacker` =
-- o boss) recebido pelo JOGADOR enquanto o atacante est\xE1 numa fase de f\xFAria (mult > 1). Summons
-- invocados na fase N\xC3O s\xE3o afetados: eles nunca ganham entrada em NarutoBossPhases.state (s\xF3 o
-- id do boss original tem), ent\xE3o `state` fica nil pra eles e a fun\xE7\xE3o devolve o dano original.
local fury = CreatureEvent("NarutoBossFury")
function fury.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType, origin)
	if not attacker then return primaryDamage, primaryType, secondaryDamage, secondaryType end
	local state = NarutoBossPhases.state[attacker:getId()]
	if not state or state.mult <= 1.0 or state.name ~= attacker:getName() then
		-- sem estado, fase 1.0x, ou id reciclado para outro monstro depois que o boss morreu.
		return primaryDamage, primaryType, secondaryDamage, secondaryType
	end
	local mult = state.mult
	-- abs()+arredonda: o retorno \xE9 sempre positivo de prop\xF3sito \x97 o TFS (CreatureEvent::
	-- executeHealthChange) reaplica o sinal certo por conta pr\xF3pria a partir de primaryType.
	local newPrimary = math.floor(math.abs(primaryDamage) * mult + 0.5)
	local newSecondary = math.floor(math.abs(secondaryDamage) * mult + 0.5)
	return newPrimary, primaryType, newSecondary, secondaryType
end
fury:register()

local reset = CreatureEvent("NarutoBossReset")
function reset.onDeath(creature)
	local id = creature:getId()
	fired[id] = nil
	NarutoBossPhases.state[id] = nil  -- limpa pra n\xE3o vazar o mult se o id for reciclado
	return true
end
reset:register()

