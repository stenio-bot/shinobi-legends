# Sistema: Progressão de servidor (rank, quiz, tarefas, diárias)

Implementa no servidor (TFS 1.4.2, revscriptsys) as pendências técnicas descritas em
`docs/lore/progressao.md`: rank Genin→Kage com storage central, o objetivo de quest
`keyword_quiz` (prova por palavra-chave), tarefas repetíveis estilo Tibia tasks e missões
diárias. Tudo gerado por `tools/export_tfs.py` a partir de `data/*.json` — **nunca edite os
arquivos em `server/generated/` ou `server/tfs/data/lib|scripts/naruto/*.lua` à mão** (exceção:
`server/tfs/data/scripts/naruto/gm_tools.lua`, que é manual por design).

## 1. Rank (Genin → Kage)

- **Dado**: `data/ranks.json` (schema `data/schemas/rank.schema.json`), já existente antes desta
  missão. Ordem fixa `["genin","chunin","jonin","anbu","kage"]` = índice 1..5.
- **Gerado**: `server/generated/lib/naruto_ranks.lua` → instalado em
  `server/tfs/data/lib/naruto_ranks.lua` (dofile em `lib.lua`).
- **Storage único**: `NarutoRanks.STORAGE = 60010` — inteiro 1..5 (rank atual do jogador; ausente
  ou < 1 é tratado como Genin). Faixa 60000-60002 já era usada por `character_switch.lua`
  (personagem/elemento); 60010 fica livre nessa mesma vizinhança de "storages de identidade".
- **API** (`NarutoRanks`, global após o dofile):
  - `NarutoRanks.get(player)` → entrada de `NarutoRanks.list` (rank atual).
  - `NarutoRanks.canEnter(player, zone)` → bool. `zone` é o id de região de `docs/lore/mundo.md`
    (`floresta_da_vila`, `costa_das_mares`, ...). Zona não listada em nenhum `unlocks.areas` de
    `ranks.json` é **sempre livre** (retorna `true`).
  - `NarutoRanks.applyBonus(player)` — remove e recria do zero a condição de bônus de status do
    rank atual. Chamada automaticamente no login (`quests_kill.lua`, `login.onLogin`) e ao final
    de `NarutoRanks.promote`.
  - `NarutoRanks.promote(player, rankId)` — promove se `rankId` for maior que o rank atual;
    aplica bônus, manda a mensagem de título (`MESSAGE_EVENT_ADVANCE`) e efeito
    `CONST_ME_FIREWORK_YELLOW`. Retorna `false` sem fazer nada se o jogador já tiver esse rank ou
    superior (idempotente — seguro chamar de novo).

### Bônus de status (`status_bonus` de `ranks.json`)

O TFS 1.4.2 não tem setter direto de HP/chakra máximo ou "defesa" do jogador. Decisão tomada
(documentada aqui por pedido da missão):

- **HP e chakra máximos**: condição permanente `CONDITION_ATTRIBUTES` (ticks = -1) com
  `CONDITION_PARAM_STAT_MAXHITPOINTS` / `..._MAXMANAPOINTS` — suporte **nativo** do TFS
  (`server/tfs/src/condition.cpp`), soma direta e exata ao valor de `ranks.json`.
- **`defense`**: o TFS não tem stat de "defesa" aplicável via condição (armor só vem de itens).
  Aproximado com `CONDITION_PARAM_SKILL_SHIELD` (soma pontos à skill Shield, que entra no
  cálculo de bloqueio/defesa do combate). É uma aproximação deliberada — o valor "+5 defesa" do
  Jonin, por exemplo, vira "+5 na skill Shield", não um número de armor equivalente. Se o
  balanceamento precisar de outra curva, a função a ajustar é `NarutoRanks.applyBonus` no
  cabeçalho gerado (`tools/export_tfs.py`, seção "ranks").
- A condição usa **subId fixo** (`NarutoRanks.BONUS_SUBID = 9010`) e é **removida e recriada do
  zero** a cada login/promoção — o bônus ativo é sempre o do rank ATUAL, nunca a soma de todos
  os ranks já alcançados (evita duplicar HP/chakra ao promover várias vezes).

### Gate de área por rank

Dois mecanismos, complementares:

1. **`NarutoRanks.canEnter(player, zone)`** — chamada de qualquer script (ex.: `onStepIn` de um
   teleporte específico de uma região) para checar por **nome de zona**.
2. **MoveEvent genérico** (`server/generated/scripts/naruto/rank_gate.lua`): qualquer tile com
   `actionid` de **45001 a 45005** (= rank mínimo 1 Genin .. 5 Kage) barra quem não tem o rank —
   manda `sendCancelMessage`, teleporta de volta (`fromPosition`) e efeito `CONST_ME_POFF`. Sem
   depender de nome de zona: o **agente de mapa** só precisa aplicar o actionid certo no
   teleporte/porta de cada região nova (fora do escopo desta missão editar `data/maps`/`tools/map`).
   **Pendência**: nenhum tile com esse actionid existe ainda no mapa físico atual — o mecanismo
   está pronto e testado via `/zonecheck` (abaixo), mas o bloqueio de um jogador de verdade
   andando até uma zona só é observável depois que o agente de mapa aplicar os actionids.

### Título no `/look`

`server/generated/scripts/naruto/rank_look.lua` usa o `EventCallback` nativo do TFS 1.4.2
(`data/scripts/lib/event_callbacks.lua`), o **mesmo mecanismo** que
`data/scripts/eventcallbacks/player/default_onLook.lua` (que monta o "You see ...") já usa —
por isso **não foi necessário editar `data/events/scripts/player.lua`**. O callback roda depois
do padrão (ordem alfabética de pasta: `eventcallbacks` antes de `naruto`) e só acrescenta uma
linha `Rank: <título>.` quando o alvo do look é um jogador.

### Promoção automática (`grants_rank` / `grants_rank_progress`)

As quests em `data/npcs/*.json` já carregavam (de uma missão anterior de lore) os campos
`grants_rank` (esta quest, ao ser concluída, é a etapa final de um exame) e
`grants_rank_progress` (esta quest é UMA das etapas de um exame com múltiplos requisitos
independentes, ex.: Jonin exige vencer o Espadachim da Névoa E o Marionetista das Ruínas, em
NPCs diferentes, sem ordem entre si). `tools/export_tfs.py` (seção "lib + quests") agora:

1. Coleta, para cada rank, a lista de `storage`s de TODAS as quests do jogo marcadas com
   `grants_rank` OU `grants_rank_progress` == esse rank → `NarutoQuests.rankGroups`.
2. Ao concluir QUALQUER quest com um desses campos (`completeQuest`, chamada tanto pelo fluxo
   normal `kill`/`collect_item` quanto pelo fim do quiz), verifica se **todas** as quests do
   grupo já estão com storage `NarutoQuests.DONE`. Se sim, chama `NarutoRanks.promote`.

Isso generaliza os dois casos do jogo hoje: Chunin (uma única quest com `grants_rank`, as
etapas anteriores já são garantidas pela ordem sequencial da lista do NPC — regra do
`CLAUDE.md`) e Jonin/Anbu/Kage (2+ quests em NPCs diferentes, todas com
`grants_rank`/`grants_rank_progress`, sem ordem entre si).

## 2. Quiz por palavra-chave (`objective.kind = "keyword_quiz"`)

Estende o gerador de NPC (`tools/export_tfs.py`, `npc_files()`) para NPCs `type: "quest"`.

- **Aceitar**: igual a antes (`missao`/`mission`/`quest`) — `NarutoQuests.talk` reconhece
  `kind == 'keyword_quiz'` e aceita a etapa (`storage = 0`) sem exigir nada além disso.
- **Responder**: o jogador diz `{prova}` (ou `{quiz}`) para começar. O NPC pergunta as questões
  de `objective.quiz` **uma por vez**, em sequência (sem repetir se errar — é um exame de
  verdade, não uma tentativa-e-erro por pergunta). Cada resposta é comparada (sem acento, minúsculo,
  `string.find` simples) contra QUALQUER palavra de `keywords` daquela pergunta.
- **Aprovação**: `quizMin = ceil(0.6 * N)` perguntas certas (N = total de perguntas; hoje só a
  prova do Exame Chunin, 5 perguntas → `quizMin = 3`). Ao acertar o suficiente, a etapa é
  concluída na hora (recompensa + checagem de rank, mesmo fluxo de `completeQuest`); se não
  acertar o suficiente, a etapa **não é perdida** — o jogador pode dizer `{prova}` de novo a
  qualquer momento para tentar de novo (reseta as 5 perguntas).
- **Compat**: o objetivo `keyword_quiz` no JSON ainda carrega `kill`/`count` (ex.:
  `exam_chunin_1_teoria` tem `kill: forest_snake, count: 1`) só por compatibilidade com o schema
  antigo — o exportador **ignora** esses dois campos para quizzes (não conta mortes; ver
  `quests_kill.lua`, que agora pula quests com `kind == 'keyword_quiz'` explicitamente, para não
  destravar a prova matando o monstro à toa).

### Achados de implementação (por que isto não é trivial)

Dois bugs reais foram encontrados e corrigidos **só** testando in-game (nenhum dos dois gera
"Lua Script Error" óbvio na primeira olhada de código):

1. **`cid` do `onCreatureSay` GLOBAL não é estável.** O script de NPC tem duas "portas de
   entrada" para mensagens: o `onCreatureSay(cid, type, msg)` global (chamado direto pelo core
   do TFS) e, por baixo dele, `npcHandler:onCreatureSay` (que por sua vez chama
   `keywordHandler:processMessage`). Dentro do `NpcHandler:onCreatureSay` de
   `data/npc/lib/npcsystem/npchandler.lua`, o `cid` usado pelo `keywordHandler` **é**
   `creature:getId()` (inteiro estável) — mas o `cid` que chega no `onCreatureSay` GLOBAL (antes
   de delegar) é o **userdata do Player**, e o TFS entrega um **objeto novo a cada mensagem**
   (endereço diferente mesmo para o mesmo jogador falando duas vezes seguidas). Guardar estado
   por `quizState[cid]` com esse `cid` cru falha sempre a partir da 2ª mensagem (a prova
   avançava até a 1ª pergunta e travava). **Corrigido**: todo código que precisa lembrar de um
   jogador entre mensagens resolve `cid` para `Player(cid):getId()` primeiro
   (`playerIdOf`, em `exam_proctor_forest.lua` e qualquer outro NPC `keyword_quiz`).
2. **`npcHandler:say(msg, cid)` com esse mesmo `cid` cru quebra em runtime.** `NpcHandler:say`
   agenda a resposta via `addEvent` (fila de ~1s, ver `NPCHANDLER_TALKDELAY`), e `addEvent` não
   aceita userdata como argumento — resultado: `Lua Script Error: luaAddEvent(). Argument #5 is
   unsafe`, silenciosamente (a mensagem às vezes ainda aparecia pro jogador de forma inconsistente,
   o que mascarou o problema por várias rodadas de teste). **Corrigido**: toda chamada de
   `npcHandler:say(...)` dentro do fluxo de quiz usa o mesmo id inteiro (`pid`), nunca o `cid`
   cru.
3. **Falar com um NPC focado exige `TALKTYPE_PRIVATE_PN`** (`MessageModes.NpcTo` no
   OTClient/Lua) depois do `{hi}` inicial — `g_game.talk()` simples sempre manda
   `MessageSay`, que o `npchandler.lua` **ignora** quando o NPC já está focado
   (`data/npc/lib/npcsystem/npchandler.lua:407`:
   `self:isFocused(cid) and msgtype == TALKTYPE_PRIVATE_PN or not self:isFocused(cid)`). Isso não
   é um bug do sistema (é o comportamento normal do NPC do jogo — o cliente de verdade troca de
   canal sozinho ao focar um NPC), só uma pegadinha de **automação de teste** — documentado aqui
   para quem for escrever outro script de teste: use
   `g_game.talkChannel(MessageModes.NpcTo, 0, msg)` para falas DEPOIS do `{hi}`.

## 3. Tarefas (`data/tasks.json`)

Estilo Tibia "tasks": repetíveis, com cooldown, dadas por um NPC dedicado por região
(`type: "tasks"`).

### Formato (`data/schemas/task.schema.json`)

```json
{
  "id": "task_leaf_wolves",
  "name": "Alcateia da trilha",
  "npc": "task_master_leaf",
  "zone": "floresta_da_vila",
  "monster_id": "wolf",
  "count": 8,
  "min_level": 1,
  "repeatable": true,
  "cooldown_min": 30,
  "reward": {"xp": 6, "ryo": 80, "items": []}
}
```

`reward.xp` é um número de **kills equivalentes** (tipicamente 5-8), não XP absoluto — ver
seção 5. `reward.ryo` é ryo absoluto (não escalado). Arquivo **opcional**: se não existir,
`tools/export_tfs.py` não gera `naruto_tasks.lua`/`scripts/naruto/tasks.lua` (avisa e segue).

Como o campo é novo, esta missão criou 18 tarefas de exemplo (3 por região × 6 regiões) — desde
então outra sessão/agente expandiu `data/tasks.json` para 114 entradas (3 tiers "Iniciante /
Veterana / Lendária" por monstro, todas usando o mesmo `npc`/`zone` já cadastrados aqui). O
gerador é inteiramente data-driven (não fixa contagem nem regiões), então a expansão foi
absorvida sem mudar nada no exportador.

### NPCs "Mestre de Tarefas" (um por região)

Adicionados em `data/npcs/*.json` (só isso foi tocado nesses arquivos, conforme escopo):
`task_master_leaf`/`task_master_swamp` (`leaf.json`, floresta da vila/da morte),
`task_master_coastal` (`coastal_tides.json`), `task_master_ruins` (`ruins.json`),
`task_master_mountain` (`mountain.json`), `task_master_lair` (`akatsuki_lair.json`).
**Pendência**: nenhum deles tem posição física no mapa ainda (o mapa é hardcoded por NPC em
`tools/map/build_valley.py`, que não conhece esses ids novos) — o agente de mapa precisa
adicioná-los. Testado com `/npc <Nome>` (comando de GM novo, ver seção 6) invocando o NPC do
lado de quem testa.

### Storages

`server/generated/lib/naruto_tasks.lua`: cada tarefa recebe, na ordem do JSON,
`progressStorage = 61000 + i` e `cooldownStorage = 63000 + i` (i = índice 1-based). Semântica:

- `progressStorage`: `-1` não aceita · `0..count-1` em andamento · `count` pronta para entregar.
- `cooldownStorage`: `os.time()` (epoch) até quando a tarefa fica bloqueada depois da última
  entrega (`os.time() + cooldownMin*60`).

### Fluxo (NPC `type: "tasks"`, palavras-chave)

- `{tarefas}` / `{lista}` — lista as tarefas cujo `min_level` o jogador atende, com status
  (disponível / em espera / progresso / pronta).
- `{tarefa}` / `{aceitar}` — aceita a PRIMEIRA elegível (nível ok, não em cooldown, ainda não
  aceita). Repita para aceitar mais de uma.
- `{entregar}` — entrega a primeira tarefa pronta (`progressStorage >= count`): concede
  `NarutoRewards.scaledXp` + ryo + itens, zera `progressStorage` para `-1` e arma o cooldown.

Contagem de mortes: `scripts/naruto/tasks.lua`, `CreatureEvent NarutoTaskKill.onKill` — percorre
`NarutoTasks.list` e incrementa qualquer tarefa cujo monstro bate e que esteja em andamento
(mesmo padrão de `quests_kill.lua`).

### Comando de jogador `!tarefas`

Lista só as tarefas **ativas** (aceitas) do jogador com progresso — não a lista completa (que
com 114 entradas seria spam). Para ver o catálogo completo de uma região, fale com o Mestre de
Tarefas de lá (`{tarefas}`).

## 4. Diárias (`data/dailies.json`)

Pool de entradas por faixa de level (`level_min`/`level_max`); 3 são sorteadas por dia por
jogador, na faixa que contém o level dele no momento do sorteio.

### Formato (`data/schemas/daily.schema.json`)

```json
{
  "id": "daily_wolves", "name": "Diária: Alcateia",
  "text": "...", "monster_id": "wolf", "count": 6,
  "level_min": 1, "level_max": 19,
  "reward": {"xp": 8, "ryo": 100, "items": []}
}
```

Como em tasks, `reward.xp` é kills equivalentes. Criadas 15 entradas de exemplo nesta missão;
outra sessão expandiu para 60 (várias faixas de 5 em 5 levels, ~3 por faixa) — de novo, o
gerador é agnóstico à quantidade/faixas exatas.

### Simplificação deliberada vs. o pedido original

O pedido original era "NPC 'Quadro de Missões' (placa readable com actionid) na praça" +
"!diaria mostra/aceita". Implementado:

- **`!diaria`** (TalkAction, funciona de qualquer lugar) e o NPC `dailies_board_leaf`
  (`type: "dailies"`, adicionado em `leaf.json`) mostram as 3 diárias do dia.
- As 3 diárias **já ficam auto-aceitas** assim que sorteadas (login, primeiro `!diaria`, ou
  primeira morte do dia) — sem um passo extra de "aceitar por número". Isso remove a
  necessidade de um parser de "aceitar 1/2/3" e é uma escolha de design razoável (o jogador não
  perde nada por não ter "aceitado" antes de matar).
- **"Placa readable com actionid"**: não implementado como item de verdade. `data/items.json` e
  `data/maps` estão fora do escopo de edição desta missão (ver regras no início da missão), e
  criar um item novo + posicioná-lo no mapa exigiria os dois. O NPC `dailies_board_leaf` cumpre
  a mesma função (mostrar/entregar as diárias da praça) sem depender de item/mapa novos — quando
  o agente de itens/mapa quiser a placa de verdade, o handler é o mesmo (`NarutoDailies.*`); só
  precisaria de um Action script por actionid chamando as mesmas funções.

### Storages

`NarutoDailies.DAY = 60020` (dia do último sorteio, `ano*400 + dia-do-ano`),
`SLOT_POOL = {60021, 60022, 60023}` (índice no pool sorteado por slot),
`SLOT_PROGRESS = {60024, 60025, 60026}` (`-1` sem entrada · `0..count-1` em andamento ·
`count` pronta · `count+1` já entregue hoje).

### Fluxo

- `NarutoDailies.rollIfNeeded(player)` — sorteia (Fisher-Yates) até 3 entradas do pool da faixa
  de level do jogador, se `DAY` não bate com hoje. Chamada no login, em `!diaria` e em qualquer
  morte (então nunca precisa ser chamada manualmente por fora).
- `NarutoDailies.onKill` (via `CreatureEvent NarutoDailyKill`) incrementa o slot certo.
- `NarutoDailies.deliver(player)` entrega TODAS as prontas de uma vez, soma XP/ryo escalados.
- `!diaria entregar` (ou `{entregar}` no NPC do quadro) chama `deliver`.

## 5. XP escalada (`NarutoRewards.scaledXp`)

`server/generated/lib/naruto_rewards.lua`:

```lua
function NarutoRewards.xpToNextLevel(level) return 100 * level + 100 end
function NarutoRewards.scaledXp(player, killsEquivalent)
	local xpPerKill = NarutoRewards.xpToNextLevel(math.max(1, player:getLevel())) / 5.5
	return math.floor(xpPerKill * (killsEquivalent or 0))
end
```

`5.5` vem de `docs/sistemas/balanceamento.md` ("~4-7 kills por level" no conteúdo já existente,
média ≈5,5). **Decisão de escopo**: usada SÓ por tarefas e diárias (onde o "level" de quem
entrega pode ser bem diferente do level "pensado" pela entrada do pool/tarefa, já que são
repetíveis e de longo prazo). As quests de história (`data/npcs/*.json`, campo `quests`)
continuam com `reward.xp` **absoluto e hand-tuned**, sem passar por `scaledXp` — os valores já
foram calibrados contra as tabelas de `balanceamento.md` para momentos narrativos específicos
(ex.: a última etapa do Exame Chunin vale 5000 xp fixos, não "kills equivalentes"); rotear isso
por `scaledXp` destuning números já validados não fazia parte do pedido e foi deliberadamente
evitado.

## 6. Ferramentas de GM novas (`gm_tools.lua`)

Adicionadas para depurar os sistemas acima (arquivo manual, fora do exportador):

- `/storage key [value]` — lê (sem `value`) ou grava um storage do PRÓPRIO jogador GM. Usado
  nos testes para fast-forward de progresso (ex.: `/storage 61001 50` simula 50 kills de uma
  tarefa sem precisar matar 50 lobos de verdade).
- `/rank [rankId]` — mostra rank atual + HP/chakra (com `[rankId]`, força uma promoção via
  `NarutoRanks.promote`, ignorando `rankGroups` — só para teste).
- `/zonecheck zona` — mostra `NarutoRanks.canEnter(player, zona)`.
- `/npc Nome Exato` — invoca (`Game.createNpc`) o NPC do lado do GM. Essencial para testar
  diálogo de NPCs que ainda não têm posição física no mapa (todos os "Mestre de Tarefas" e o
  "Quadro de Missões" desta missão, e a "Instrutora Ibuki" do Exame Chunin também não tinha
  posição no `.otbm` no momento deste teste).

## 7. Testes realizados (in-game, `client-otc/shinobirc.lua` temporário)

Conta dedicada `slqa`/`slqa123` (tipo GOD) criada só para este teste, para não colidir com a
conta `god` usada em paralelo por outra sessão/agente no mesmo servidor compartilhado (achado
real: duas sessões na mesma conta causam desconexões e leituras cruzadas de estado). Screenshots
em `screenshots/sistemas_01..14_*.png`.

Resultado, ponta a ponta, **zero Lua Script Error** no log do servidor:

1. `missao` → aceita `exam_chunin_1_teoria` (quiz). `prova` → 5 perguntas em sequência,
   respondidas certo (`chakra`, `fuuton`, `hayato`, `ninjutsu`, `hokage`) → "5/5 certas" + 500 xp
   + quest concluída.
2. Fast-forward das etapas 2a/2b/3a/3b via `/storage` (não são o mecanismo novo sob teste) →
   `missao` oferece corretamente só a etapa final (`exam_chunin_3c_rival_mist`, aceita).
3. `/storage 50031 1` simula a morte do rival final → `missao` conclui: +5000 xp e
   **"Parabéns! Você agora é Chunin — aprovado no Exame Chunin!"**.
4. `/rank` confirma: HP e chakra máximos subiram exatamente `+30`/`+15` (bônus de `ranks.json`
   para chunin). `/zonecheck floresta_da_morte` = `true` (liberado), `/zonecheck
   montanha_do_trovao` = `false` (ainda não é Jonin) — gate por rank correto.
5. Tarefas: `{tarefa}` aceita `task_wolf_1`; matar 1 Lobo de verdade incrementa o contador (`{...}
   1/50`, confirmado no primeiro teste); `/storage 61001 50` fast-forward; `{entregar}` → "+7636
   xp, +75 ryo" (nível 20 → `scaledXp(20 kills) ≈ 7636`, bate com a fórmula); `!tarefas` depois
   confirma "nenhuma tarefa ativa".
6. Diárias: `!diaria` mostra as 3 do dia (auto-aceitas) já contando; `!diaria entregar` paga
   as 3 de uma vez.
7. **Jogador comum, do zero** (conta `teste`, personagem "Naruto", nível 8, nunca tocado por
   nenhum destes sistemas): `!tarefas` e `!diaria` funcionam sem erro (diárias sorteadas
   corretamente pra faixa 6-10).

## 8. Pendências / fora do escopo desta missão

- **Posição física dos NPCs novos** (6 Mestres de Tarefas + Quadro de Missões + Instrutora
  Ibuki) no `.otbm`: depende do agente de mapa (`tools/map/build_valley.py`, hardcoded por NPC —
  não lê `data/npcs/*.json` genericamente).
- **Actionids 45001-45005** nos teleportes/portas de zona: idem, agente de mapa.
- **"Placa readable"** de verdade para as diárias: precisaria de um item novo
  (`data/items.json`, fora do escopo) + posição no mapa. O NPC `dailies_board_leaf` cobre a
  mesma função hoje.
- **48 itens de recompensa sem id** em `data/tfs_mapping.json` no momento em que esta missão
  começou (a maioria `trophy_*`, mais alguns equipamentos de exam/anbu) — o exportador agora
  **omite** silenciosamente (com aviso no console) qualquer item de recompensa (quest, tarefa ou
  diária) sem id mapeado, em vez de gerar `{id=0,...}` (que faria `player:addItem(0,1)` falhar).
  Ao longo desta sessão outro agente já preencheu boa parte deles em `tfs_mapping.json`; os que
  sobrarem aparecem no aviso final de `tools/export_tfs.py`.
- **Conta de teste `slqa`/`slqa123`** (tipo GOD) foi criada no banco só para este teste e
  **não foi removida** (útil para QA futuro; remova com
  `DELETE FROM players WHERE name='SLQA'; DELETE FROM accounts WHERE name='slqa';` se não for
  mais necessária).
- **Senha da conta `teste`** foi alterada temporariamente durante o teste e restaurada para
  `teste` (mesmo padrão de `god`/`god`) ao final — confirme com quem administra se esse era o
  valor original.

## 9. Conquistas (`data/achievements.json`)

55 conquistas fixas (schema `data/schemas/achievement.schema.json`), geradas por
`tools/export_tfs.py` em `server/generated/lib/naruto_achievements.lua` (dados: lista completa +
conjuntos de equipamento por tier + ids de item por prefixo) e
`server/generated/scripts/naruto/achievements.lua` (revscript: `CreatureEvent`s, `GlobalEvent` de
poll e `!conquistas`). Antes desta missão **nenhuma** das 55 tinha lógica no servidor.

### Storages (faixa nova, documentada aqui — não colide com nada existente)

| Storage | Conteúdo |
|---|---|
| `64000 + i` | "desbloqueada" da conquista de índice `i` (1-based, ordem de `data/achievements.json` = ordem de `NarutoAchievements.list`) — ausente/≠1 = bloqueada, `1` = desbloqueada. 55 conquistas → `64001`..`64055`. |
| `65000` | contador **global** de mortes (qualquer monstro) — não existia nenhum contador "total de mortes, qualquer tipo" antes desta missão (os storages de tasks/quests são por-monstro/por-tarefa). |
| `65001` | contador global de tarefas entregues (soma de qualquer NPC "Mestre de Tarefas", qualquer região). |
| `65002` | contador global de diárias entregues (ver nota sobre `daily_streak` abaixo). |
| `65003` | índice (`NarutoAchievements.list`) da **última** conquista desbloqueada — só para ter algo pra mostrar no `/look` (ver seção "Título no /look"). |

Confirmado sem colisão com: `45001-45005` (gates de rank), `50000-50500` (quests de história,
`NarutoQuests.DONE = 50500`), `60000-60002` (personagem/elemento), `60010` (rank),
`60020-60026` (diárias), `61001-61114` (progresso de tarefas), `63001-63114` (cooldown de
tarefas) — a faixa `62000-64999` estava livre, e `64000+`/`65000+` foram escolhidos por serem a
sugestão já dada na missão.

### Tipos de condição: implementados vs. não

Todos os 10 `kind` do schema (`data/schemas/achievement.schema.json`) estão implementados — a
tabela abaixo mostra o evento/hook exato de cada um:

| `kind` | Conquistas | Hook | Onde |
|---|---|---|---|
| `kill_count` (target `any`) | 5 (100/500/1000/5000/10000 abates) | `CreatureEvent NarutoAchievementKill.onKill` → `NarutoAchievements.onKill` incrementa `65000` e checa | `scripts/naruto/achievements.lua` |
| `kill_specific` (target = monster_id) | 12 (bosses) | mesmo `onKill`, compara `target:getName()` com o nome resolvido do monstro (`monsters[target].name`, pré-computado em `tools/export_tfs.py`) | idem |
| `quest_chain_complete` (target = npc id) | 6 (uma por região) | `completeQuest` (`naruto_quests.lua`), depois de marcar a quest atual `DONE`: percorre `NarutoQuests.byNpc[q.npc]` inteiro e só dispara se **todas** já estiverem `DONE` | `server/generated/lib/naruto_quests.lua` |
| `grants_rank` (target = rank id) | 4 (exames) | `NarutoRanks.promote`, depois de `player:setStorageValue(STORAGE, ...)` | `server/generated/lib/naruto_ranks.lua` |
| `level_reached` (count = nível) | 4 (25/50/75/100) | `CreatureEvent NarutoAchievementAdvance.onAdvance` (nativo do TFS, `skill == SKILL_LEVEL`) | `scripts/naruto/achievements.lua` |
| `task_count` (target `any`) | 3 (10/50/100 tarefas) | `deliverCallback` do NPC "Mestre de Tarefas" (gerado por `npc_files()`, branch `n["type"] == "tasks"` — as 6 regiões compartilham o mesmo template Python), depois de conceder XP/ryo/itens: incrementa `65001` e checa | `server/generated/npc/scripts/naruto/task_master_*.lua` |
| `daily_streak` (target `any`) | 3 (7/30/100 diárias) | `NarutoDailies.deliver`, uma vez por slot efetivamente entregue nessa chamada: incrementa `65002` e checa | `server/generated/lib/naruto_dailies.lua` |
| `visit_zone` (target = zona) | 6 (uma por região) | poll (ver abaixo) — sem hook de evento dedicado | `NarutoAchievements.pollPlayer` |
| `collect_set` (target `tier_N`) | 11 (kits de equipamento) | poll — idem | idem |
| `collect_item_count` (target `trophy_*`) | 1 (38 troféus) | poll — idem | idem |

**Nenhum contador pré-existente foi duplicado**: os únicos 3 contadores novos (`65000-65002`)
não tinham equivalente antes — tudo o mais (rank atual, storage de cada quest, progresso de
cada tarefa/diária, level do jogador, itens no inventário, slots equipados) é **lido direto**
das libs já existentes (`NarutoRanks`, `NarutoQuests`, `player:getLevel()`,
`player:getItemCount()`, `player:getSlotItem()`), nunca recontado à parte.

### `visit_zone`/`collect_set`/`collect_item_count`: por que poll, e a limitação real

O TFS 1.4.2 não tem um evento nativo "jogador entrou na zona X" nem "jogador equipou o item Y"
— o primeiro exigiria um sistema de zonas em runtime que não existe (as "regiões" do jogo são
só retângulos de posição usados **na hora de construir o mapa**, `tools/map/build_valley.py` e
`tools/map/build_regions.py`, sem contrapartida em nenhum arquivo carregado pelo servidor); o
segundo exigiria um script `onEquip`/`onDeEquip` por item nos 47 equipamentos de
`data/items/tiers.json`+`armor.json`+`weapons.json` (fora do escopo — editar item por item).

**Solução adotada**: um `GlobalEvent` (`NarutoAchievementPoll`, intervalo de 7 s) itera
`Game.getPlayers()` e chama `NarutoAchievements.pollPlayer(player)`, que:

1. Calcula a zona pela posição (`NarutoAchievements.zoneAt`, comparando contra os **mesmos**
   retângulos `X0/Y0/DEATH_X0` (`build_valley.py`) e `COAST_*/RUINS_*/MOUNT_*/LAIR_*`
   (`build_regions.py`) copiados **verbatim** para `NarutoAchievements.zoneBounds` — os 6 não se
   sobrepõem, então a checagem é só "está dentro do retângulo?"). **Limitação**: se o agente de
   mapa mudar essas coordenadas no futuro sem atualizar `tools/export_tfs.py` em conjunto, o
   `visit_zone` desalinha silenciosamente (nenhum erro, só para de bater na hora certa).
2. Checa `collect_set` via `player:getSlotItem` nos 6 slots (`CONST_SLOT_HEAD/ARMOR/LEGS/FEET/
   RING` + `LEFT`/`RIGHT` para arma) contra `NarutoAchievements.gearSets[tier]`.
3. Checa `collect_item_count` via `player:getItemCount` para cada id do prefixo (`trophy_`).

Também chamado uma vez no login (`NarutoAchievementLogin.onLogin`), então um jogador que já
estava com o conjunto vestido ou já tinha os 38 troféus antes desta missão existir é premiado
logo ao entrar, sem esperar o próximo tick do poll. **Latência real**: até 7 s de atraso entre
"vestir a última peça"/"entrar na zona" e a mensagem de desbloqueio aparecer — aceitável para
conquistas (não são checks de gameplay sensíveis a frame).

### `collect_set`: gap de dado real (não é bug do exportador)

`tools/export_tfs.py` monta `NarutoAchievements.gearSets[tier]` varrendo `data/items/*.json`
por `required_level == tier` nos 6 slots (`head/body/legs/feet/accessory/weapon`). Os tiers
**1, 10, 30, 40, 50, 60, 70, 80, 90, 100** têm os 6 slots completos (a arma aceita qualquer uma
das opções cadastradas nesse level, ex. tier 1 aceita `kunai_iron` OU `shuriken_iron`) — **mas
o tier 20 não tem nenhum item `accessory` cadastrado** em `data/items/*.json`. A conquista
`gearset_l20` ("Uniforme Chunin") fica, portanto, com um requisito de **5 dos 6 slots**
(head/body/legs/feet/weapon), não 6 como as outras 10 — a lógica (`NarutoAchievements.
hasGearSet`) simplesmente itera os slots que existem em `gearSets[20]`, então funciona, só que
com um "kit" objetivamente mais fácil que os outros. Fica registrado aqui para quem for
adicionar um acessório de tier 20 depois (basta rodar o exportador de novo, nada de código
muda).

### `daily_streak`: nome do `kind` não bate com o comportamento (schema pré-existente)

O `kind` no schema chama-se `daily_streak`, mas a descrição das 3 conquistas
(`dailies_completed_7/30/100`) é explicitamente "no total", não "N dias seguidos" — e o próprio
sistema de diárias (`NarutoDailies`) não guarda nenhum conceito de sequência/streak (só o dia do
último sorteio, `NarutoDailies.DAY`). Implementado fielmente à **descrição** (contador
cumulativo de diárias entregues, storage `65002`), não ao nome do `kind` — uma conquista de
streak de verdade (ex.: "diária todo dia por 7 dias seguidos, sem furar") exigiria um storage
de "última data que entregou pelo menos 1" + zerar o contador se um dia pular, o que é uma
mudança de schema/design maior, fora do escopo desta missão de implementação.

### Feedback ao desbloquear

`NarutoAchievements.grant(player, a)` (idempotente — não faz nada se já desbloqueada):

1. `player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "Conquista desbloqueada: <nome>!")`.
2. Efeito visual: `player:getPosition():sendMagicEffect(NarutoAchievements.EFFECT_ID)`, onde
   `EFFECT_ID = 222` (`fx_seal_glow` do catálogo `assets-src/sprites/effects.json`, resolvido em
   tempo de exportação via a mesma `_catalog_id()` que os jutsus usam).
3. Recompensa: **só `ryo`** (`player:addItem(NarutoQuests.RYO_ID, a.ryo)`) — `data/
   achievements.json` (`reward: {title, ryo}`, ver o schema) não tem campo de XP nem de item;
   a missão pediu "xp/ryo/item/título conforme o JSON", mas o JSON em si só carrega `ryo` e
   `title`, então XP e item **não existem para conceder** (não é uma omissão da implementação —
   não há dado de origem). Se o time de conteúdo quiser XP/item por conquista, é preciso
   estender o schema + preencher os 55 registros primeiro.
4. Título: ver próxima seção.

### Título de conquista no `/look` (simplificação deliberada)

O pedido original ("título de conquista opcional no `/look`, junte com `rank_look.lua`") não
especifica COMO escolher qual título mostrar entre até 55 possíveis — implementar uma UI de
seleção de título está fora do escopo desta missão de conteúdo/backend. **Decisão tomada**:
`rank_look.lua` (mesmo `EventCallback.onLook` que já mostra o rank) agora também mostra o
**título da última conquista desbloqueada** (`NarutoAchievements.LAST_UNLOCKED`, atualizado a
cada `grant`), como uma segunda linha `"Título: <nome>."` — sem quebrar a linha de rank
existente. Não há comando para o jogador *escolher* qual dos títulos já conquistados exibir;
isso ficaria para uma missão de UX dedicada (o `!conquistas`/aba Conquistas já mostram todos os
títulos disponíveis, então o jogador sabe o que tem).

### Comandos

- **`!conquistas`** (qualquer jogador): resumo no chat — `"Conquistas: X/55 | kill Y/5 | boss
  Y/12 | ..."` (uma entrada por categoria, na ordem em que aparecem em
  `data/achievements.json`).
- **`/conquista [id]`** (GM, `gm_tools.lua` — arquivo manual, não gerado): sem parâmetro, lista
  os `id`s ainda bloqueados do próprio GM (para copiar/colar); com um `id` de
  `data/achievements.json`, força o desbloqueio via `NarutoAchievements.grant` (ignora a
  condição de verdade — só para teste, mesmo padrão do `/rank`/`/storage` já existentes).

### Cliente (aba Missões → seção Conquistas)

Ver `docs/sistemas/cliente-ux.md` para a UI. Resumo: `NarutoCharacters.sendProgress` ganhou um
campo `achievements` (array das 55, com `id/name/description/category/title/unlocked` e
`progress/count` nas 5 categorias contáveis) — `client-otc/modules/naruto_menu/naruto_menu.lua`
(`buildAchievementsSection`) monta uma seção "CONQUISTAS (X/55)" dentro da aba Missões já
existente, com um sub-cabeçalho por categoria (`Y/Z`) e uma linha por conquista (verde
"Desbloqueada", dourado com progresso `x/y` nas contáveis ainda bloqueadas, cinza "Bloqueada"
nas demais).

### Testes realizados

Ver o relatório final da missão (mensagem de encerramento da sessão) para os resultados
in-game (kill de teste, entrega de tarefa, `/conquista` forçado, aba aberta mostrando X/55,
`!conquistas`) e screenshots — não duplicado aqui para não desincronizar as duas fontes.
