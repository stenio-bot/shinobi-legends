# Sistema: Missões (`data/npcs/*.json` → `quests`)

Formato JSON de uma missão de NPC, gerado por `tools/export_tfs.py` (seção "lib + quests") em
`server/generated/lib/naruto_quests.lua` (dados + a lógica compartilhada `NarutoQuests.talk`/
`completeQuest`/`progressText`) e `server/generated/scripts/naruto/quests_kill.lua` (o gancho de
morte que conta progresso de `kill`/`any_of` e o poll que completa `reach`). Schema formal em
`data/schemas/quest.schema.json`, validado por `tools/validate_data.py`.

**Nunca edite `server/generated/` nem `server/tfs/data/lib|scripts/naruto/*.lua` à mão** — edite
o JSON em `data/npcs/*.json` e rode `tools/export_tfs.py`.

Esta missão estendeu o motor para 6 tipos de `objective.kind` (era 2: `kill`, `keyword_quiz`, mais
`collect_item` que já existia parcialmente) sem mudar o comportamento de nenhuma das 45 missões
já escritas — todo campo novo é opcional, com fallback para o texto/comportamento de sempre.

## Formato geral de uma quest

```json
{
  "id": "q_exemplo",
  "name": "Nome da Missão",
  "text": "Fala do NPC ao oferecer a missão. Placeholders: {player}.",
  "progress_text": "Opcional. Fala enquanto em andamento. Placeholders: {count}, {needed}, {player}.",
  "done_text": "Opcional. Fala ao concluir. Placeholders: {player}.",
  "locked_text": "Opcional. Fala quando 'requires' não foi satisfeito. Placeholders: {player}.",
  "requires": {
    "level": 20,
    "rank": "chunin",
    "quests": ["outra_quest_id"]
  },
  "objective": { "kind": "...", "...": "..." },
  "reward": {
    "xp": 100, "ryo": 50, "items": ["item_id"],
    "storage": { "key": 66001, "value": 1 },
    "outfit": 950, "addon": 3,
    "title": "Nome do título (documentário)"
  },
  "grants_rank": "chunin",
  "grants_rank_progress": "chunin"
}
```

Todos os campos além de `id`/`name`/`text`/`objective`/`reward.items` são opcionais. `requires`,
`progress_text`, `done_text`, `locked_text` e os campos novos de `reward` funcionam em **qualquer**
`kind` (inclusive os antigos `kill`/`collect_item`/`keyword_quiz`).

## Storage de uma quest

Cada quest recebe um storage único: `base + i` (`base` = `data/tfs_mapping.json
storage_base` = 50000, `i` = índice sequencial de todas as quests do jogo, na ordem dos NPCs).
Semântica (igual para todo `kind`, inclusive os novos):

- `-1` (ou ausente): não aceita.
- `0 .. count-1`: aceita, em andamento.
- `count`: pronta para entregar (só usado internamente por alguns kinds — ver abaixo).
- `NarutoQuests.DONE` (= `base + 500` = 50500): concluída.

`reach` e `talk_to` **reusam este mesmo storage** — não precisaram de faixa nova. `reward.storage`
(opcional, para destravar diálogo/gate em outro script) usa uma faixa própria: **66000-66999**
(ver `docs/sistemas/progressao-servidor.md`, seção 10).

## Diálogo condicionado e pré-requisitos (`requires`)

`requires.level`/`requires.rank`/`requires.quests` (lista de ids de OUTRAS quests, de qualquer
NPC) são checados só no momento de **aceitar** (storage `< 0`). Uma quest já aceita nunca "tranca"
de novo. Sem `requires`, o padrão continua sendo puramente sequencial por NPC: `NarutoQuests.talk`
sempre olha a lista de quests do NPC em ordem e para na primeira que ainda não está `DONE` — isso
não muda. `requires` serve para bloquear a PRÓXIMA quest da lista até algo de fora dessa
sequência (nível, rank, ou uma quest de OUTRO NPC) acontecer.

Quando bloqueado, o NPC diz `locked_text` (com placeholder `{player}`) ou, se ausente, uma fala
padrão pt-BR: `"Volte quando estiver pronto: falta level X, rank Y, N missão(ões) anterior(es)."`
(só lista o que de fato falta).

```json
{
  "id": "q_com_prerequisito",
  "name": "Depende de Outro NPC",
  "text": "Só disponível depois de ajudar o Ferreiro.",
  "requires": { "quests": ["q_ferreiro_ferramentas"], "level": 15 },
  "objective": { "kind": "kill", "kill": "bandit_lv5", "count": 3 },
  "reward": { "xp": 500, "ryo": 100, "items": [] }
}
```

## Placeholders

`text`, `progress_text`, `done_text` e `locked_text` suportam:

- `{player}` — nome do jogador.
- `{count}` — progresso atual (só em `progress_text`; nos outros vira `0`).
- `{needed}` — `objective.count` (quando aplicável).

Sem nenhum desses tokens, o texto é usado como está (substring vazia = no-op) — é seguro usar em
qualquer quest, nova ou já existente.

## Tipos de `objective.kind`

### `kill` (padrão, `kind` pode ficar ausente)

```json
{ "objective": { "kind": "kill", "kill": "wolf_forest", "count": 5 } }
```

**Novo**: `any_of` (lista — qualquer um dos monstros conta pro mesmo contador) e `boss` (metadado
de UI, ver abaixo).

```json
{
  "objective": {
    "kind": "kill",
    "any_of": ["bandit_lieutenant_stone", "bandit_lieutenant_sound"],
    "count": 1,
    "boss": true
  }
}
```

`boss: true` **não** mexe no monstro nem no `/look` dele — é só um metadado que a aba Missões do
cliente usa pra mostrar uma tag "(chefe)" (`NarutoQuests.progressText` acrescenta o sufixo). Não
implementamos uma tag no `/look` do MONSTRO porque isso exigiria mudar `EventCallback.onLook` para
también decidir, por creatura, se ela é alvo de alguma quest ativa do jogador que a estiver
olhando — acoplamento monstro↔quest desnecessário para o pedido ("marca para a UI saber que é
chefe"), que a aba Missões já resolve.

### `keyword_quiz` (sem mudança nesta extensão)

```json
{
  "objective": {
    "kind": "keyword_quiz",
    "quiz": [{ "question": "Pergunta?", "keywords": ["resposta", "sinonimo"] }]
  }
}
```

O jogador diz `{prova}`/`{quiz}` ao NPC pra responder. Continua igual — documentado aqui só pra
referência do formato completo.

### `collect_item`

```json
{
  "objective": {
    "kind": "collect_item",
    "items": [{ "item_id": "wolf_pelt", "count": 5 }]
  }
}
```

Ao falar `{missao}`, se o jogador tiver os itens na mochila, eles são removidos e a missão
completa; senão o NPC diz o que falta (`progress_text` custom, ou o padrão "Ainda falta trazer:
Nx item, ..."). `NarutoQuests.progressText` soma por UNIDADE (não por tipo de item): "3/5 itens".

**Novo**: `drops_from` — chance de o item de missão cair como drop extra ao matar um monstro
específico, enquanto a missão está ativa e o jogador ainda não tem o suficiente (não empilha além
do necessário). O TFS 1.4.2 não tem "loot condicional por quest" no `monster/*.xml` (a tabela de
loot não enxerga o storage do jogador que matou) — implementado em `onKill`
(`scripts/naruto/quests_kill.lua`), não no monstro.

```json
{
  "objective": {
    "kind": "collect_item",
    "items": [{ "item_id": "rare_scale", "count": 2 }],
    "drops_from": [{ "item_id": "rare_scale", "monster_id": "swamp_dragon", "chance": 0.3 }]
  }
}
```

Recomenda-se marcar o item usado aqui com `quest_item: true` (`data/schemas/item.schema.json`) —
`tools/export_tfs.py` então garante que ele nunca entra em nenhuma lista de venda de NPC, mesmo
que o tipo dele esteja no `buys_types` de algum mercador. Sobre "não dropar ao morrer": o script
de perda de itens do TFS (`droploot.lua`, vanilla) só afeta os slots EQUIPADOS
(`CONST_SLOT_HEAD..CONST_SLOT_AMMO`) — um item de missão comum (pele, escama, carta) fica na
mochila e já não é afetado por padrão; só evite usar `quest_item` num item pensado para ser
equipado se quiser essa garantia.

### `talk_to` (NOVO)

Completa quando o jogador diz a keyword (padrão `missao`) para OUTRO npc — o alvo, não quem deu a
missão.

```json
{
  "objective": {
    "kind": "talk_to",
    "npc": "merchant_leaf",
    "keyword": "missao"
  }
}
```

- `npc`: id do NPC alvo (precisa existir — `tools/validate_data.py` acusa se não existir, ou se
  for o MESMO npc que ofereceu a missão).
- `keyword`: opcional, padrão `"missao"`.

Implementação: `tools/export_tfs.py` (`npc_files()`) injeta, em **todo** NPC gerado (não só nos
`type: "quest"` — o alvo pode ser um mercador, um NPC de tarefas, etc.), um bloco que filtra
`NarutoQuests.list` procurando quests `kind == 'talk_to'` com `targetNpc` igual ao próprio id.
Se a lista ficar vazia (nenhuma quest do jogo mira esse NPC — o caso de TODO NPC hoje, já que
nenhuma missão real usa `talk_to` ainda), nada é registrado: zero mudança de comportamento. Se não
ficar vazia, o NPC passa a responder à keyword configurada checando, para cada jogador que fala
com ele, se alguma dessas quests está ativa (aceita, não concluída) — e, se sim, completa na hora
(`NarutoQuests.completeTalkTo`) e devolve a mensagem de conclusão. Se o jogador não tiver nenhuma
dessas quests ativas, o callback devolve `false` e a keyword cai pro próximo handler do NPC (ex.:
o `{missao}` normal, se o alvo também for um NPC de quests) — mesma semântica de fallthrough do
`keywordhandler.lua` do TFS (vários callbacks podem responder à mesma keyword; o primeiro que
retornar `true` "vence").

### `reach` (NOVO)

Completa ao chegar perto de uma posição do mapa.

```json
{
  "objective": {
    "kind": "reach",
    "pos": { "x": 132, "y": 84, "z": 7 },
    "radius": 3
  }
}
```

- `pos`: coordenadas **absolutas do mapa TFS** (mesmo espaço de `player:getPosition()`/
  `Position(x,y,z)` — **não** é o x/y relativo de `data/maps/*.json`). Descubra a posição certa
  andando até o local no jogo e usando uma ferramenta de GM que mostre a posição atual, ou
  inspecionando o `.otbm`/script de mapa.
- `radius`: raio **quadrado** (Chebyshev — `|dx| <= radius` E `|dy| <= radius`, mesmo `z`), não
  euclidiano. Um `radius` pequeno (2-4) já cobre uma sala/praça inteira sem exigir precisão de
  1 tile.

Implementação escolhida — **poll**, não `onStepIn`/actionid de tile nem `MoveEvent`:
`server/generated/scripts/naruto/quests_kill.lua` registra um `GlobalEvent`
(`NarutoQuestReachPoll`, intervalo 7s — mesmo padrão do poll de conquistas, ver
`docs/sistemas/progressao-servidor.md` seção 9, mas em `GlobalEvent` PRÓPRIO, arquivo/lib
diferente, pra `naruto_quests` continuar autocontido) que, a cada tick, olha todo jogador online e
toda quest `reach` ativa dele, comparando posição. `onStepIn`/actionid exigiria editar o MAPA
(colocar uma actionid de tile por missão) e `MoveEvent` tem a mesma exigência — ambos fora do
escopo de `tools/export_tfs.py`, que só gera a partir de `data/*.json`, sem tocar no `.otbm`. Ao
chegar, a etapa só fica "pronta para entregar" — a recompensa é dada ao falar `{missao}` com o
NPC que deu a missão (mesmo fluxo de `kill`, narrativamente "volte e me conte que chegou").
Latência: até 7s entre chegar e a etapa virar "pronta" — aceitável para uma missão de progressão
(não é um QTE).

## Recompensas (`reward`)

```json
{
  "reward": {
    "xp": 500, "ryo": 100, "items": ["chakra_pill_medium"],
    "storage": { "key": 66001, "value": 1 },
    "outfit": 950,
    "addon": 3,
    "title": "Guardião da Vila"
  }
}
```

- `xp`/`ryo`/`items`: já existiam.
- `storage` (NOVO): grava um storage arbitrário do jogador ao concluir — para destravar diálogo
  condicionado ou um gate em outro script (`if player:getStorageValue(66001) == 1 then ...`).
  Use a faixa **66000-66999** (reservada, ver `docs/sistemas/progressao-servidor.md` seção 10)
  para não colidir com nada.
- `outfit`/`addon` (NOVO): concede um looktype (`player:addOutfit`) e, opcionalmente, um addon
  (`player:addOutfitAddon`, bitmask 1/2/3) nesse looktype. `addon` sem `outfit` é um erro de dado
  (`tools/validate_data.py` acusa).
- `title` (NOVO, documentário): só é armazenado em `NarutoQuests.list[].reward.title` para uma
  futura UI de seleção de título — **não** integrado ao sistema de conquistas
  (`data/achievements.json`) automaticamente, por design (conquistas têm seu próprio catálogo
  fixo de 55 títulos, ver `docs/sistemas/progressao-servidor.md` seção 9). Se quiser um título de
  verdade hoje, use uma conquista.

## Cliente (aba Missões)

`NarutoCharacters.sendProgress` (opcode 210, `get_progress`) → `missionsProgressJson` ganhou,
por missão: `kind` e `progress` (texto curto de `NarutoQuests.progressText`: "3/5 itens",
"Chegou! Fale com o NPC", "A caminho", "Fale com <npc alvo>", "X/Y" [+ "(chefe)" se `boss`],
"Disponível", "Concluída") e `boss` (bool, só `true` em `kill` com `objective.boss`). O cliente
(`client-otc/`) **não foi editado** por esta extensão — os campos são aditivos; um cliente antigo
que ignora `kind`/`progress`/`boss` continua funcionando (o campo `status` de sempre não mudou).

## Validação (`tools/validate_data.py`)

Além do schema completo (`data/schemas/quest.schema.json`, via `jsonschema` quando instalado),
checa: monstros de `kill`/`any_of`/`drops_from` existem; itens de `objective.items`/`drops_from`
existem; `drops_from.chance` está em `0..1`; NPC alvo de `talk_to` existe e não é o próprio NPC
que dá a missão; `reach` tem `pos` completo (x/y/z) e `radius`; `requires.rank` é um rank válido;
`requires.quests` referencia quests que existem; **ciclos em `requires.quests`** (DFS,
detecta pré-requisito circular entre quests, mesmo cruzando NPCs); `reward.storage` tem `key`
e `value`; `reward.addon` não aparece sem `reward.outfit`; item `quest_item: true` não aparece em
nenhum `sells` de NPC.

```
.venv/bin/python tools/validate_data.py
```

## Como testar

1. **Dados**: `.venv/bin/python tools/validate_data.py` (schema + referências).
2. **Exportador**: `python3 tools/export_tfs.py` (só escreve em `server/generated/` — nunca em
   `server/tfs/`). Compare o Lua gerado antes/depois de mexer no exportador (`diff -rq`) — para
   missões que já existiam, a mudança deve ser só ADIÇÃO de campos/blocos, nunca remoção/edição
   de uma linha existente.
3. **Sintaxe Lua**: `luajit -bl <arquivo>` em todo `.lua` de `server/generated/` (checa só
   sintaxe, não roda).
4. **Testes funcionais headless** (sem servidor, sem cliente): `tools/tests/test_quests_headless.lua`,
   rodado com `luajit tools/tests/test_quests_headless.lua`, ou via o runner completo (repete os
   3 passos acima e então roda os testes):
   ```
   bash tools/tests/run_quests_tests.sh
   ```
   O teste carrega os arquivos REAIS gerados (`server/generated/lib/naruto_quests.lua`,
   `lib/naruto_ranks.lua`, `scripts/naruto/quests_kill.lua`, um npc real —
   `npc/scripts/naruto/merchant_leaf.lua`) contra um stub mínimo das APIs do TFS
   (`tools/tests/tfs_stub.lua` — `Player`, `CreatureEvent`, `GlobalEvent`, `KeywordHandler`,
   `NpcHandler`, etc.), sem precisar do TFS instalado nem do cliente. Cobre:
   - **Regressão**: 3 quests REAIS (`q_wolves_1` kill, `q_forest_supplies` collect_item,
     `exam_chunin_1_teoria` keyword_quiz) produzem exatamente as mesmas mensagens/efeitos de
     antes desta extensão.
   - **Fixtures** (uma por tipo/recurso novo, só no teste — nenhuma missão real foi criada/
     alterada em `data/npcs/*.json`): `kill`+`any_of`+`boss`, `collect_item`+`drops_from`,
     `talk_to` (contra o NPC real `merchant_leaf`), `reach` (via o `GlobalEvent` real), `requires`
     (level/rank cruzando NPCs + `locked_text`), `reward.storage`/`outfit`/`addon`,
     `progress_text`/`done_text` com placeholders, e `NarutoQuests.progressText` por `kind`.
5. **Nunca** rode `tools/install_generated.sh` nem reinicie o servidor/cliente durante o
   desenvolvimento — outro agente pode estar jogando; só o orquestrador decide quando instalar.

## Fora de escopo (documentado, não implementado)

- **UI de seleção de título** (`reward.title`): dado armazenado, sem tela de seleção no cliente.
- **Tag "chefe" no `/look` do monstro**: `boss` é metadado só de quest/UI, não altera o monstro.
- **Loot condicional nativo** (`drops_from`): implementado via `onKill`, não como uma feature
  genérica do `monster/*.xml` — cada quest com `drops_from` adiciona um pequeno custo de CPU no
  `onKill` de QUALQUER monstro (um loop sobre `NarutoQuests.list`, já existente antes desta
  extensão para `kill`/`any_of`), desprezível na escala do projeto.
- **`kill_sequence`**: campo do schema mantido só como documentário (já existia antes desta
  extensão), sem lógica própria — continua modelado como N quests sequenciais separadas.
- **Cliente (`client-otc/`)**: não editado; só o JSON enviado (`kind`/`progress`/`boss`) foi
  estendido, de forma aditiva.
