# Sistema: Cliente / UX (menu Shinobi, rank em tela, login, chat)

Implementa, no lado do **cliente** (OTClient Redemption, `client-otc/`), quatro pendências de
UX pedidas numa mesma missão: aba "Missões" no menu Shinobi (Ctrl+J), rank discreto em tela,
tela de login temática e tradução das mensagens de sistema que ainda apareciam em inglês.
Regra de ouro seguida em tudo: nada de UI "moderna" — só estilos existentes
(`data/styles/*.otui`, `50-ninja.otui`), fontes bitmap cp1252, `tr()`.

## 1. Aba "Missões" (menu Shinobi, opcode 210, ação nova `get_progress`)

### Protocolo (documentado em detalhe em `docs/sistemas/combate-e-jutsus.md`)

Estendido o opcode 210 existente (`character_switch.lua`, gerado por `tools/export_tfs.py`)
com uma ação nova, **sem quebrar as 3 já existentes** (`state`, `select`, `get_state`):

- Cliente → servidor: `{"type":"get_progress"}`.
- Servidor → cliente: `{"type":"progress", rank, tasks, dailies, missions, achievements}` — rank
  atual + próximo rank (com a lista de requisitos pendentes, via `NarutoQuests.rankGroups` +
  um índice reverso novo `NarutoQuests.byStorage`), tarefas ativas (`NarutoTasks`, com
  progresso `x/y` e cooldown restante em minutos), diárias do dia (`NarutoDailies`, com
  status `progress`/`ready`/`delivered`), as 45 missões de história (`NarutoQuests.list`) com
  status (`available`/`in_progress`/`done`) e o NPC que a dá, e as **55 conquistas**
  (`NarutoAchievements.list`, campo novo desta missão) com `unlocked` + `progress`/`count` nas
  contáveis — ver `docs/sistemas/progressao-servidor.md`, seção "Conquistas".
- O `state` (já existente, empurrado sozinho no login/troca de personagem) ganhou um campo
  `rank` (`{id, title, index}` ou `null`) — é o que alimenta a seção 2 abaixo.

Ao contrário do `state`, o `progress` **não** é empurrado sozinho: o cliente pede
(`requestProgress()`) quando a aba é aberta (`tabBar.onTabChange`) ou quando o jogador clica
"Atualizar" — evitar mandar a lista de 45 missões em todo login/troca de personagem.

### Cliente (`client-otc/modules/naruto_menu/`)

- `naruto_menu.otui`: 3 estilos novos — `ShinobiSectionHeader` (título de seção, ex. "RANK"),
  `ShinobiInfoRow` (linha genérica título+subtítulo à esquerda, status/botão à direita —
  reaproveitada para requisito de rank, tarefa, diária e missão) e `ShinobiMissionsTab`
  (hint + botão "Atualizar" + `ShinobiListArea` já usada nas outras abas).
- `naruto_menu.lua`: `requestProgress()`, `onProgress(data)` (decodifica com o mesmo
  `decodeStrings`/`utf8ToCp1252` já usado pelo `state`), `buildMissionsTab()` monta a lista do
  zero a cada `progress` recebido — 5 seções (RANK, TAREFAS ATIVAS, DIÁRIAS DE HOJE, MISSÕES,
  CONQUISTAS). O botão "Entregar" de uma diária pronta manda `g_game.talk('!diaria entregar')`
  (o comando de jogador já existente, `docs/sistemas/progressao-servidor.md`) e repede o
  `progress` 500 ms depois para refletir a entrega.

### Seção "CONQUISTAS" (dentro da aba Missões — nova nesta missão)

`buildAchievementsSection(list, p)` monta, a partir de `p.achievements` (55 entradas, mesma
ordem/agrupamento por categoria de `data/achievements.json`):

- Um cabeçalho `CONQUISTAS (X/55)` no topo (`X` = quantas o jogador já desbloqueou).
- Um sub-cabeçalho por categoria (`ShinobiInfoRow` reaproveitado como header, ex. "Chefes  —
  3/12") sempre que a categoria muda no array (já vem agrupado, então isso é só detectar a
  borda) — rótulos em pt-BR (`ACH_CATEGORY_LABEL`: Exploração, Exame, Cadeias de História,
  Chefes, Abates, Nível, Tarefas, Diárias, Coleção).
- Uma linha por conquista (nome + descrição), com status: **verde "Desbloqueada"** se
  `unlocked`, **dourado `x/y`** se ainda bloqueada mas contável (`progress`/`count` presentes —
  abates/tarefas/diárias/nível/troféus), **cinza "Bloqueada"** nas demais (chefe/cadeia de
  história/exame/zona/conjunto — só binário, sem progresso numérico do servidor).

Nenhum estilo `.otui` novo foi necessário — reaproveita `ShinobiSectionHeader`/`ShinobiInfoRow`
já existentes (mesmo padrão das outras 4 seções).

### Testado (conta `teste`, Genin nível 7-8)

`screenshots/ux_missoes_02_tab.png` / `ux_final_04_missoes_top.png`: RANK (Genin da vila →
Próximo: Chunin, 0/1 requisito, "Exame Chunin — Torneio (3/3)" pendente com o NPC
"Instrutora Ibuki"), TAREFAS ATIVAS ("Nenhuma tarefa aceita..."), DIÁRIAS DE HOJE (3 diárias
"Em andamento" com progresso `0/12` etc.), MISSÕES ("Clones não sangram, mas caem" —
Disponível). `ux_final_01/02/03` confirmam que Personagem/Elemento/Jutsus continuam
funcionando sem regressão. Zero Lua Script Error no servidor durante os testes.

### Testado também com GM (conta `slqa`, Chunin nível 21) — grupo de rank com 2+ requisitos

`screenshots/ux_final_08_missoes_gm.png`: RANK mostra "Chunin — aprovado no Exame Chunin"
atual → "Próximo: Jonin — venceu o Espadachim da Névoa e o Marionetista das Ru[ínas]", **0/2**
requisitos, com as DUAS linhas de requisito ("O Espadachim da Névoa" / NPC Ancião Tazu,
"Quem puxa os fios" / NPC Ancião Kaito, ambas "Pendente") — confirma que
`NarutoQuests.rankGroups` com múltiplas quests independentes (Jonin exige vencer 2 NPCs
diferentes, sem ordem entre si — `docs/sistemas/progressao-servidor.md`) aparece certo na
aba, não só o caso de 1 quest só (Chunin). `screenshots/ux_final_07_comandos_gm.png` confirma
que a aba "Comandos" (só GM) continua funcionando lado a lado com a "Missões" nova, sem
regressão de ordem/índice de abas.

## 2. Rank em tela (janela de Atributos)

Em vez de mexer em `client-otc/modules/game_skills/skills.otui` (módulo `game_*` original,
1600+ linhas), `naruto_menu.lua` (`updateRankDisplay`) **injeta um widget em runtime**: acha a
linha "Level" da janela de Atributos (`modules.game_skills.skillsWindow:recursiveGetChildById
('level')`), pega o painel-pai (`MiniWindowContents`, `layout: verticalBox`) e cria uma linha
`SkillButton` própria ("Rank" / "Genin da vila") logo depois, com
`parent:moveChildToIndex(rankRow, idx + 1)` — o `verticalBox` reflui sozinho. Atualiza sempre
que chega um `state` novo (login, troca de personagem/elemento, e agora também **depois de uma
promoção de rank**: `NarutoRanks.promote` passou a chamar `NarutoCharacters.sendState` no
servidor — ver seção 1 do protocolo). `menuController:onTerminate` destrói esse widget
explicitamente (ele não é filho da janela do menu Shinobi, então um reload do módulo duplicaria
a linha "Rank" sem isso).

Testado: `screenshots/ux_missoes_01_skills_rank.png` e `ux_final_06_atributos_rank.png` —
"Rank: Genin da vila" aparece discreto, logo abaixo de "Nível", no mesmo estilo das outras
linhas (Experiência, XP Gain Rate...). Não cheguei a testar uma promoção de rank ao vivo
(exigiria simular `/storage` várias etapas do Exame Chunin do zero); o código que reenvia o
`state` depois do `promote` foi revisado, mas **fica como pendência de teste end-to-end** —
`docs/sistemas/progressao-servidor.md` já tem o passo a passo de fast-forward via `/storage`
usado por outra sessão para testar `NarutoRanks.promote` isoladamente.

## 3. Tela de login temática

Ao investigar, a maior parte já estava pronta de uma sessão anterior (antes desta missão
começar): `client-otc/modules/client_background/background.otui` já tinha um fundo gerado
(`data/images/background.png`, 1920×1080, vila silhueta + lua + folhas caindo, sem nenhum
asset de terceiro) e os labels `NinjaGameTitle`/`NinjaGameSubtitle` ("SHINOBI LEGENDS" /
"Narutibia PvM", estilo em `50-ninja.otui`); `init.lua` já chamava `g_app.setName("Shinobi
Legends")` e `modules/startup/startup.lua` já usa isso para `g_window.setTitle` — então a
barra de título do SO **já** mostra "Shinobi Legends", não "OTClient" (confirmado lendo
`src/framework/platform/cocoawindow.mm`: o `"OTClient"` hardcoded ali é só o título inicial da
janela antes do C++ terminar de subir; `startup.lua` sobrescreve segundos depois).

O que faltava e foi adicionado nesta missão: em nenhum lugar da UI havia crédito ao motor
OTClient/OTClient Redemption (o requisito pedia manter os créditos). Adicionado um label
discreto (`creditsLabel`, cinza, canto inferior direito, acima do label de versão) em
`client_background/background.otui`: "Baseado em OTClient Redemption".

Testado: `screenshots/ux_login_01_initial.png` mostra o título/subtítulo/fundo/janela "Entrar
no Jogo" já traduzida e temática (estado de antes desta missão). `screenshots/
ux_login_02_credit.png` (e o recorte `ux_login_02_credit_zoom.png`) confirmam o crédito novo:
"Baseado em OTClient Redemption" em cinza, logo abaixo do bloco de versão, sem sobrepor nada.

## 4. Barra de chat: mensagens de sistema em inglês

Duas causas raiz diferentes, as duas resolvidas:

### 4.1 Mojibake de acento (achado não previsto no pedido original, mas do mesmo bug)

Confirmado com `screenshots/ux_chat_01_zoom.png`: `!tarefas` respondia "regi**Ã£**o" em vez de
"reg**ĩ**ão" — o servidor manda UTF-8, mas as fontes do OTClient são bitmaps indexados por
BYTE (o mesmo problema que `naruto_menu.lua` já tratava só para o JSON do opcode 210). Isso
afetava **qualquer** mensagem do servidor com acento: diárias, tarefas, `/look`, boas-vindas
de login etc. — não só as 3 frases em inglês citadas na missão.

### 4.2 Frases hardcoded em inglês no núcleo do TFS (`server/tfs/src/*.cpp`)

Ex.: `"You advanced to {skill} level {N}."`, `"There is not enough room."`, `"{alvo} loses {N}
hitpoints due to your attack."` — vêm do C++ (`player.cpp`, `game.cpp`, `tools.cpp`), não do
JSON gerado por `tools/export_tfs.py`. **Não reescrevi o núcleo do TFS** (regra de ouro):
resolvido inteiramente no cliente, por padrão/regex.

### Implementação

- **Novo arquivo** `client-otc/modules/naruto_theme/naruto_chat.lua` (adicionado à lista
  `scripts` de `naruto_theme.otmod`): expõe `translateMessage(text)`.
  1. Dicionário exato (~60 entradas) para as mensagens de cancelamento fixas do TFS
     (`tools.cpp: getReturnMessage`) — `"There is not enough room."` → `"Não há espaço
     suficiente."`, `"Sorry, not possible."`, `"You are too far away."` etc.
  2. ~25 padrões Lua com captura (nível de personagem, nível de skill — com `SKILL_NAMES`
     mapeando `"fist fighting"→"Corpo a Corpo"`, `"magic level"→"Ninjutsu"` etc. —, chakra/mana,
     vida/hitpoints, cura, experiência), cada um already produzindo pt-BR no estilo do projeto
     ("Você avançou em Taijutsu nível X.").
  3. Fallback: `utf8ToCp1252` (cópia da função de `naruto_menu.lua`) para qualquer texto sem
     padrão reconhecido — conserta o mojibake de acento (seção 4.1) em texto que já está em
     português (diárias, tarefas, NPCs).
- **Hook de instalação** em `naruto_menu.lua` (`hookChatTranslation`, chamado de
  `menuController:onInit`), **não** em `naruto_theme` (prioridade 600, carrega cedo demais —
  `game_textmessage` só existe depois que `game_interface` termina de carregar seu
  `load-later`, o que só acontece na faixa de prioridade 1000+, onde o `naruto_menu` mora; ver
  o comentário longo no código). Desregistra `modules.game_textmessage.displayMessage` de
  todo "message mode" (`registerMessageMode`/`unregisterMessageMode`, `gamelib/
  textmessages.lua`) e registra um wrapper que chama `translateMessage` antes do original.
- **Servidor, alteração trivial e documentada aqui** (permitida pela missão): `server/tfs/data/
  creaturescripts/scripts/login.lua` (arquivo padrão do TFS, **não gerado** por
  `tools/export_tfs.py`) — só o texto: `"Welcome to X!"` → `"Bem-vindo(a) a X!"`, `"Your last
  visit in X: ..."` → `"Sua última visita em X: ..."` (e a data passou de `%d %b %Y %X`, que
  sai com mês abreviado em inglês, para `%d/%m/%Y %H:%M:%S`, totalmente numérico). Nenhuma
  lógica de jogo tocada.

### Testado

Suite de 14 casos direto contra `translateMessage` (sem precisar de combate ao vivo,
`client-otc/shinobirc.lua` temporário) — todos corretos, incluindo os 3 casos citados na
missão. Ao vivo, confirmado em tela: `screenshots/ux_chatfix_00_welcome.png` ("Sua última
visita em Shinobi Legends: 05/09/2026 00:45:53." — acento renderizando certo),
`ux_chatfix_02_diaria.png` ("Diária: Sanguessuga Gigante — segunda leva", "caçada rápida" —
acentos e travessão certos), `ux_chat_01_accents.png` (antes do fix, mostrando o bug original
para registro).

**Achado real durante o teste** (não hipotético): a primeira versão de `naruto_chat.lua` usava
`table.unpack(caps)`, que **não existe no LuaJIT 5.1** deste projeto (é `unpack` global, não
`table.unpack` — confirmado por convenção em `modules/corelib/*.lua`). O bug não travava o
cliente (a chamada tem `pcall`, cai no texto original em inglês) mas *silenciava* toda a
tradução por padrão (só o dicionário exato e o fallback de acento funcionavam) — só foi pego
testando `translateMessage` isoladamente e vendo o log de erro
(`attempt to call field 'unpack' (a nil value)`). Corrigido antes de fechar a missão.

### Cobertura conhecidamente incompleta (decisão de escopo)

O dicionário/padrões cobrem os casos citados na missão + os mais frequentes de combate/nível/
diárias/tarefas. **Não** cobrem (não vistos em uso neste projeto — sem mercado/loja/casas/
guilda): mensagens de troca (`trade`), casas, `party`/`guild` details, e a descrição completa
de `/look` em itens/criaturas (só o rank do jogador, que já vinha traduzido por
`rank_look.lua`). Se aparecer uma frase nova em inglês, o padrão é o mesmo: achar a string
literal em `server/tfs/src/*.cpp`, adicionar um `EXACT[...]` ou `PATTERNS` novo em
`naruto_chat.lua`.

## 5. Encoding — mojibake residual em NOMES (NPC/criatura/item), corrigido no protocolo (C++)

Depois do fix da seção 4.1 (Lua, só para mensagens de sistema e o JSON do opcode 210), sobrou
mojibake em **nomes**: NPC "AnciÃ£o Kaito" na aba NPCs/balão de fala, itens "poÃ§Ã£o de vida" no
chat de loot, nomes de criatura. Causa: esses nomes vêm de um pipeline de protocolo diferente
do texto de sistema — atributo `name=` do XML de monstro/NPC (gerado a partir de `data/*.json`,
**não** passa por `tools/export_tfs.py`), continuam em UTF-8, enquanto o texto de Lua
(`tools/export_tfs.py`'s `_lua_cp1252`, desde 2026-09-05) já vai em cp1252. O cliente antigo
tratava toda string do protocolo como se já viesse pronta pra tela; qualquer uma em UTF-8
virava mojibake byte-a-byte nas fontes bitmap cp1252.

### Implementação

Conversão movida para um ponto único e obrigatório: **`InputMessage::getString()`**
(`client-otc/src/framework/net/inputmessage.cpp`) — todo texto do protocolo do jogo passa por
aqui (nome de criatura/NPC/item, falas, JSON do opcode 210, textos de janela, etc.), então não
há mais depender de cada callsite lembrar de converter.

- Regra aplicada string a string, sem estado: se tem byte ≥0x80 **e** é UTF-8 válido de ponta a
  ponta (`stdext::is_valid_utf8`), converte com a nova `stdext::utf8_to_cp1252` (mesma tabela
  `CP1252_EXTRA` de `naruto_chat.lua`/`naruto_menu.lua` — €, aspas curvas, travessão en/em,
  reticências etc. viram o byte cp1252 certo em vez de sumir; qualquer outro codepoint fora do
  latin1 vira `?`). Se **não** é UTF-8 válido (caso do texto de Lua, que já é cp1252 — um byte
  solto como `\xE3` quase nunca fecha uma sequência UTF-8 válida junto com o resto da string),
  passa intacta.
- **Idempotente por construção**: cada chamada de `getString()` lê bytes novos do buffer de
  rede: não há "converter duas vezes" a mesma string. E o texto já-cp1252 vindo do Lua do
  servidor sobrevive ileso porque falha o teste `is_valid_utf8` (mesma lógica de `isCont` que
  `naruto_chat.lua` já usava do lado Lua).
- `stdext::utf8_to_latin1` (existente) **não foi reaproveitada** para isto: ela descarta
  qualquer codepoint fora de 0x00A0–0x00FF (perderia €/aspas curvas/travessão/reticências em
  silêncio) — por isso a nova `stdext::utf8_to_cp1252`
  (`client-otc/src/framework/stdext/string.{h,cpp}`), com fallback `?` só para o que sobra fora
  do cp1252.
- `parseExtendedOpcode` (opcode 210) usa `getString()` para o buffer JSON — a conversão roda
  antes do `json::parse` em `naruto_menu.lua`. Aspas/escapes/chaves do JSON são ASCII (não têm
  byte ≥0x80), então a re-codificação só toca valores de string com acento; não há risco de
  quebrar a estrutura do JSON.
- Consequência: `utf8ToCp1252` dos módulos Lua (`naruto_chat.lua`, `naruto_menu.lua`) virou
  **no-op** na prática — o texto já chega em cp1252 do C++, `str:find('[\128-\255]')` só acha
  bytes cp1252 soltos que a própria função já tratava como "passa direto". Funções mantidas
  (não removidas): continuam servindo de rede de segurança e não quebram nada rodando em cima
  de texto já convertido.

### Testado

Build: `cmake --build --preset macos-release --target otclient` (ver tempo no relatório da
sessão). In-game com conta `slqa`: NPC com acento (`/tp` até um NPC como Ancião Kaito) na aba
NPCs e no balão de fala, `/m <criatura acentuada>` pra ver o nome em tela, loot de criatura com
acento no chat, Menu Shinobi (aba Missões, nomes de missão acentuados) — screenshots
`screenshots/encoding_*.png`. Zero `Lua exception` no log do cliente durante o teste.

### Limitações conhecidas (fora do escopo deste fix, cliente não pode resolver sozinho)

- **Bug de missão "kill não conta" com monstro acentuado** (`docs/qa/playtest-historia-
  arcos4-6.md`, Achado #2) era **do servidor**, não do cliente — **CORRIGIDO** (2026-09-05,
  mesmo dia deste achado): `NarutoText.utf8ToCp1252`/`.cp1252ToUtf8` (novo, gerado em
  `lib/naruto_json.lua` por `tools/export_tfs.py`) converte o nome vindo de `creature:getName()`
  (UTF-8, do `name=` do XML do monstro) antes de comparar contra os literais cp1252 deste Lua
  gerado, em `quests_kill.lua`/`tasks.lua`/`dailies.lua`/`achievements.lua` (contagem de kill) e
  `boss_phases.lua` (`PHASES[...]` e summons via `Game.createMonster`). **Regra geral:** Lua
  gerado = cp1252 para exibição; qualquer nome que chega do jogo em tempo de execução chega em
  UTF-8 → sempre `NarutoText.utf8ToCp1252(nome)` antes de comparar/indexar contra um literal
  gerado (e `NarutoText.cp1252ToUtf8(nome)` na direção inversa, ex. summon de boss). Testes
  headless em `tools/tests/test_encoding_headless.lua`.
- Um texto cp1252 cujo trecho acentuado formar, por coincidência, uma sequência UTF-8
  multibyte válida (ex.: os bytes cp1252 de "Ã" seguido de um byte de continuação válido)
  passaria pela conversão por engano. Não observado em texto real do jogo (mesmo risco que o
  fallback Lua já aceitava); documentado aqui para quem for investigar um nome esquisito no
  futuro.
- **Achado ao vivo, residual, servidor**: a mensagem `"Loot of %s: %s"` (`server/tfs/data/
  scripts/eventcallbacks/monster/default_onDropLoot.lua`) mistura DUAS codificações **dentro da
  mesma string** antes mesmo de chegar ao cliente — bytes reais capturados matando uma Águia do
  Trovão (`xxd` no log): `mType:getNameDescription()` chega no wire já como cp1252 de um byte só
  (`74 72 6f 76 e3 6f` = "trov" + `\xE3` + "o", `\xE3`='ã' cp1252), mas
  `corpse:getContentDescription()` (nome do item, `poção`/`pena do trovão` etc.) chega em UTF-8
  de verdade (`74 72 6f 76 c3 a3 6f 73` = "trov" + `\xC3\xA3` + "os", 2 bytes válidos). Como é
  **uma única string** (`("Loot of %s: %s"):format(...)`), `is_valid_utf8` roda sobre o buffer
  inteiro: o `\xE3` solto do nome do monstro já quebra a validade global, então
  `InputMessage::getString` (corretamente, pela regra "se não é UTF-8 válido, passa intacta")
  deixa a string INTEIRA sem tocar — o nome do monstro aparece perfeito (já era cp1252) mas o
  nome do item continua mojibake (ainda UTF-8 de 2 bytes na tela cp1252). Não investiguei por
  que `getNameDescription()` (via Lua) chega diferente de `getContentDescription()` — os dois
  deveriam vir do mesmo tipo de atributo XML (`nameDescription=`/`name=`, ambos UTF-8 no
  arquivo-fonte, confirmado com `xxd` em `thunder_eagle.xml`); é uma inconsistência do
  **servidor** (TFS C++/Lua), fora do escopo desta missão ("engenheiro de cliente") — repro:
  matar qualquer monstro com nome acentuado que largue um item com nome acentuado, olhar o
  canal de chat onde a mensagem `MESSAGE_LOOT` aparece.

## Arquivos tocados

**Servidor** (gerador + instalado): `tools/export_tfs.py` (ação `get_progress`, campo `rank`
no `state`, `NarutoRanks.promote` chama `sendState`, `npcName`/`NarutoQuests.byStorage`) →
regenerado em `server/generated/{scripts/naruto/character_switch.lua, lib/naruto_quests.lua,
lib/naruto_ranks.lua}` → instalado em `server/tfs/data/{scripts/naruto/character_switch.lua,
lib/naruto_quests.lua, lib/naruto_ranks.lua}` via `tools/install_generated.sh`. Manual:
`server/tfs/data/creaturescripts/scripts/login.lua` (não gerado).

**Cliente**: `client-otc/modules/naruto_menu/{naruto_menu.lua, naruto_menu.otui}` (aba
Missões, rank em tela, hook de chat), `client-otc/modules/naruto_theme/{naruto_chat.lua
(novo), naruto_theme.otmod}`, `client-otc/modules/client_background/background.otui`
(crédito OTClient).

**Docs**: este arquivo + `docs/sistemas/combate-e-jutsus.md` (protocolo opcode 210 atualizado).

**Encoding de nomes no protocolo (missão posterior, seção "5")**: `client-otc/src/framework/
net/inputmessage.cpp` (`InputMessage::getString`, conversão UTF-8→cp1252 na entrada do
protocolo), `client-otc/src/framework/stdext/string.{h,cpp}` (`stdext::utf8_to_cp1252`, nova).
Nenhum arquivo de módulo Lua alterado (só validado que `utf8ToCp1252` virou no-op).

**Conquistas (missão posterior, mesma seção "1")**: `tools/export_tfs.py` ganhou a geração de
`lib/naruto_achievements.lua` + `scripts/naruto/achievements.lua`, o campo `achievements` no
`progress` (`character_switch.lua`/`achievementsProgressJson`), o hook de conquista em
`naruto_quests.lua` (`completeQuest`), `naruto_ranks.lua` (`promote`), `naruto_dailies.lua`
(`deliver`) e no template de NPC "tasks" (`deliverCallback`, `npc_files()`), e a 2ª linha
("Título: ...") em `rank_look.lua`. Manual: `server/tfs/data/lib/lib.lua` (novo `dofile`),
`tools/install_generated.sh` (cp/dofile condicional, mesmo padrão de tasks/dailies),
`server/tfs/data/scripts/naruto/gm_tools.lua` (`/conquista`). Cliente:
`client-otc/modules/naruto_menu/naruto_menu.lua` (`buildAchievementsSection`, seção
"CONQUISTAS" dentro da aba Missões — sem `.otui` novo). Docs: `docs/sistemas/
progressao-servidor.md` (seção 9, "Conquistas") + este arquivo + `docs/sistemas/
combate-e-jutsus.md` (campo `achievements` no `progress`).

## Ambiente / achados operacionais (para quem testar isto depois)

- `/reload global` **recria do zero** `NarutoCharacters`/`NarutoRanks`/etc. (re-executa os
  `dofile` das libs) — se rodar depois de `/reload scripts`, apaga os métodos que
  `character_switch.lua` tinha colado em `NarutoCharacters` (`.apply`, `.sendState`,
  `.sendProgress`), e o próximo login quebra com `Lua Script Error: ... attempt to call field
  'apply' (a nil value)`. Ordem certa: **`/reload global` antes de `/reload scripts`** (ou só
  rode `/reload scripts` de novo depois, como fiz para recuperar). Isto aconteceu de verdade
  durante os testes desta missão (log do servidor confirmado).
- `/reload scripts` **não** recarrega `data/creaturescripts/*.lua` (sistema clássico, não
  revscriptsys) — para pegar a mudança em `login.lua` precisa de `/reload creaturescripts`
  (ou `/reload all`, ou restart).
- Durante os testes, o processo `tfs` reiniciou sozinho (PID mudou de 45599 para 47439) —
  **não fui eu** que reiniciei; percebi pela mudança de PID e pelo log ter zerado. Não reiniciei
  de novo (regra do ambiente compartilhado).
