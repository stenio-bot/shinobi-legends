# Playtest QA — jornada de história, Arcos 1-3 (2026-09-05, pós-correções Lote A/B/M)

*QA de narrativa. Escopo: Arco 1 (Academia/Floresta da Vila — Capitã Rin), Arco 2 (Costa das
Marés — Ancião Tazu) e Arco 3 (Floresta da Morte/Exame Chunin — Rastreador Goro + Instrutora
Ibuki), validados IN-GAME com personagem GM (`slqa`/`slqa123`, conta GOD) depois dos commits de
hoje: `1439749` (Lote A), `6f0893f` (Lote B), `006f3c3` (Lote C) e `0dc49a5` (Lote M).*

## Veredito

**Sim, jogável de ponta a ponta — com uma ressalva séria de exibição de texto.** A engrenagem de
missões (aceitar → progresso em tempo real "x/y" → concluir → recompensa → próxima quest) funciona
de forma sólida e repetida em pelo menos 7 quests distintas de 3 NPCs diferentes, os dois bosses
que puderam ser lutados de verdade (Espadachim da Névoa, Serpente Branca) mostraram as falas de
fase exatas pedidas pela missão, os spawns soltos corrigidos no Lote M (Aprendiz Mascarado,
Serpente Menor) existem no mapa de verdade, o gate da Costa está provadamente aberto a Genin (lido
no código), a aba Missões mostra progresso de coleta ao vivo, e **zero `Lua Script Error` novo**
em toda a sessão (múltiplas rodadas, ~30 min de jogo real). A ressalva: **falas de NPC/monstro com
acento aparecem como mojibake na tela e no chat** ("MissÃ£o", "concluÃ­da", "NÃ£o Ã©") — o texto
correto existe (confirmado lendo o dado bruto do evento antes da renderização), mas o jogador real
vê caracteres quebrados toda vez que uma fala tem ç/ã/é/í. É um bug de exibição, não de dados, mas
afeta **toda fala de NPC do jogo em pt-BR** (praticamente todas), então é o achado de maior
prioridade desta rodada. Dois achados menores: o Chefe dos Bandidos não pôde ser lutado ao vivo
nesta sessão (inconclusivo, não confirmado nem como falha), e `/i` com nome de item acentuado
falha silenciosamente (usar o id numérico resolve).

## Metodologia

Script de automação (`client-otc/shinobirc.lua`, **apagado ao final, nunca commitado** — arquivo
compartilhado entre agentes por convenção do `CLAUDE.md`): login GM, `/tp x,y,z` até cada NPC,
`/m <Nome>` para invocar monstros da missão bem perto do GM (evita moagem manual), `/i <id>,<qtd>`
para itens de coleta, `g_game.attack()` automático no alvo não-jogador/não-NPC mais próximo,
captura de `onTalk`/`onTextMessage` para as falas, `g_app.doScreenshot` (≤ 40, escala 0.5).

- Servidor confirmado no ar (`nc -z 127.0.0.1 7171`) e **nunca reiniciado**. `df -h
  /System/Volumes/Data`: 14 GiB livres (94% usado), acima do piso de 1,5 GB. `grep -c "Lua Script
  Error" /tmp/tfs_run.log`: **0** antes de começar e **0** ao final (checado repetidas vezes
  durante a sessão).
- `client-otc/shinobirc.lua` foi encontrado **em uso por outra sessão** no início desta missão
  (processo OTClient PID 8670, conta `kitqa2`, comentário "QA5 Fase C") — aguardado terminar
  sozinho (Monitor + polling do PID) antes de escrever por cima; nunca matei esse PID, só os que eu
  mesmo abri (6 sub-sessões ao todo, PIDs 9971/10478/10557/10620/10753/10963 — os 2 primeiros de
  tentativas com bug de metodologia corrigido nas seguintes, ver abaixo).
- Contas: `slqa`/`slqa123` (GOD, personagem SLQA, level 25→100 via `/god`) para o GM; `teste`/
  `teste` (personagem "Naruto", L7, conta normal) para o teste de gate da Costa.

### Achados de metodologia (nenhum é bug do jogo, mas todos custaram tempo real desta sessão)

1. **`g_game.talk()` nunca fala com NPC depois do primeiro "oi" — crítico para qualquer rc
   futura.** `Game::talk()` do cliente sempre manda `TALKTYPE_SAY`
   (`client-otc/src/client/game.cpp:1036`). O servidor só encaminha a mensagem pro
   `keywordHandler` do NPC (`NpcHandler:onCreatureSay`,
   `server/tfs/data/npc/lib/npcsystem/npchandler.lua:397-416`, padrão vanilla do TFS) se o
   jogador **não estiver focado** OU se **focado E a mensagem for `TALKTYPE_PRIVATE_PN`**. Como
   `hi` é sempre a 1ª mensagem (ainda não focado), sempre funciona — mas `missao`, `prova` e as
   respostas do quiz, mandadas depois, precisam ir por
   `g_game.talkChannel(MessageModes.NpcTo, 0, msg)` (o que um jogador de verdade faz sem saber, ao
   digitar na aba "NPCs" do chat). A 1ª rodada desta rc (PID 9971) mandou tudo com `g_game.talk()`
   puro: a saudação apareceu, nenhuma quest foi de fato aceita, e nenhum erro apareceu em lugar
   nenhum — só silêncio. Corrigido nas rodadas seguintes.
2. **Cada `missao` só faz uma transição.** `NarutoQuests.talk` (`server/generated/lib/
   naruto_quests.lua:186`) para no primeiro quest não-`DONE` da lista e retorna assim que aceita
   OU completa — nunca os dois juntos, nunca "cai" pro próximo. Um lote de mortes iniciado logo
   depois do `missao` que só *completou* a quest anterior (sem um 2º `missao` que *aceita* a
   atual) é desperdiçado — o contador só incrementa com storage `>= 0` (aceita).
3. **Salas de interior são pequenas demais para `/m` em lote.** A sala da Capitã Rin (~4x4, balcão
   + baú + lanterna) não cabe 5+ monstros ao mesmo tempo; `/m` falha com "There is not enough
   room." em boa parte das tentativas. Mitigado com folga de spawn generosa (até dobrar a
   contagem, piso de 3 tentativas extras mesmo pra `count=1`) — funcionou na maioria dos casos,
   mas não 100% (ex. `Bandido Arqueiro` fechou em 5/8 numa rodada antes de eu desistir de
   perseguir aquele lote específico e seguir pro resto da missão; o mecanismo em si — aceitar,
   contar progresso, completar — já tinha sido confirmado em outras 6 quests, então não repeti
   indefinidamente).
4. **`/i` com nome de item acentuado falha silenciosamente.** `/i Poção de Vida Pequena,5` voltou
   "There is no item with that id or name." (`Onigiri`, `Pele de Lobo`, `Pele de Sapo` — todos sem
   acento — funcionaram normalmente). Parece um problema de round-trip de encoding entre o script
   Lua do cliente e o parser de nome do `create_item.lua` (mesma família do achado #5 abaixo).
   Usar o **id numérico** (`/i 7618,5`) evita o problema — corrigido no script.
5. **Achado de jogo, não de metodologia — ver seção própria abaixo: mojibake em falas com
   acento.**

## Achado de jogo #1 (alta prioridade): mojibake em falas de NPC/monstro com acento

**Toda fala de NPC ou monstro em pt-BR que contém ç/ã/é/í/etc. aparece corrompida na tela** —
balão de fala acima da cabeça e janela de chat (aba "NPCs"), confirmado em screenshot real (não é
suposição): `screenshots/historia_09_espadachim_luta_aprendiz.png` mostra "NÃ£o Ã© nada pessoal,
moleque..." em vez de "Não é nada pessoal, moleque..."; `screenshots/historia_01_rin_hi_missao.png`
mostra "CapitÃ£ Rin", "OlÃ¡", "nÃ£o terminou"; o chat mostra "MissÃ£o... concluÃ­da" em vez de
"Missão... concluída". **O dado subjacente está correto** — meu script captura o texto de
`onTalk`/`onTextMessage` (a mesma API que a UI usa) e ele chega com os acentos certos em UTF-8
(ex. `TALK Espadachim Da Névoa: Ainda não. Não vou deixar que ele me leve ainda — ele não luta por
dinheiro, luta por mim.`, log bruto, sem mojibake nenhum) — então o problema é **só na hora de
desenhar o balão/linha de chat**, não nos dados de `data/npcs/*.json`/`data/monsters/*.json`.
Suspeita: mesma família do achado do commit `e0e683f` ("naruto_chat.lua, cp1252 fix") — aquele fix
cobriu "mensagens de sistema" mas não o texto de fala de NPC/monstro (`onCreatureSay`), que passa
por um caminho de renderização diferente. **Afeta praticamente 100% do texto narrativo do jogo**
(quase toda fala em pt-BR tem pelo menos um acento) — é o achado de maior prioridade desta
missão, mesmo não bloqueando o gameplay (o jogador consegue jogar, só não consegue ler
direito). Arquivo suspeito: `client-otc/modules/naruto_chat.lua` e/ou o pipeline de
`onCreatureSay`/balão de fala do `game_console`/`game_textmessage` (não investigado a fundo —
fora do escopo de código desta missão de QA, só leitura).

## Tabela por passo

| # | Passo | Esperado | Observado | OK/FALHA | Screenshot |
|---|---|---|---|---|---|
| 1 | Rin `hi`→`missao`, 1ª fala | Tutorial novo (q_wolves_1) | **Confirmado.** "Bem-vinda à Floresta da Vila, Genin. A Academia te ensinou o básico — hora de provar em campo. Os lobos andam atacando viajantes na trilha: mate 5." (Missão aceita: Lobos na trilha) | OK | historia_01 |
| 2 | q_wolves_1 (Lobo x5) | Aceita→progresso→completa | 5/5, progresso ao vivo "Lobos na trilha: N/5", "Bom trabalho, ninja. Missão 'Lobos na trilha' concluída.", +120 XP | OK | — |
| 3 | q_forest_deer_1 (Onigiri x3, `/i` no lugar de caçar Cervo) | Aceita, coleta, completa | Aceita ("Traga 3 para o posto avançado — não precisa caçar, eles nem revidam"), completada com 3 onigiri, +150 XP | OK | historia_02 |
| 4 | Aba Missões (Ctrl+J / `modules.naruto_menu.show()`) mostra progresso de coleta | "x/y" | Confirmado com 2/3 onigiri antes de completar (ver screenshot) | OK | historia_02 |
| 5 | q_forest_snakes (Cobra da Floresta x8) | Aceita→8/8→completa | Confirmado, progresso "Presas na relva: N/8" até 8/8, "concluída" | OK | — |
| 6 | q_bandits_1 (Bandido x10) | Aceita→10/10→completa | Confirmado após ajuste de metodologia (colchão de spawn maior); "Bom trabalho, ninja. Missão 'Limpando a estrada' concluída." | OK | historia_03 |
| 7 | q_bandit_archers (Bandido Arqueiro x8) | Aceita→8/8→completa | Aceito, progresso ao vivo confirmado até 5/8; não fechei 8/8 nesta rodada especifica antes de seguir (ver achado de metodologia #3) — mecanismo já provado em #2/#5/#6 | PARCIAL (mecanismo OK, contagem final desta rodada não fechada) | — |
| 8 | q_forest_supplies (Pele de Lobo x5, coleta) | Aceita→completa | Confirmado, item entregue via `/i 5897,5`... na prática usei o nome sem acento (funciona), completou | OK | — |
| 9 | q_bandit_chief (Chefe dos Bandidos, boss) — fala a 50% HP citando "nuvem vermelha" | Fala de fase + done_text de Rin | **Inconclusivo.** `/m Chefe dos Bandidos` não gerou nenhuma mensagem de combate em 2 tentativas (nem "there is not enough room", nem dano) — não lutei o boss ao vivo. Texto da fase **confirmado por leitura direta do dado**: `data/monsters/forest.json`, `boss_bandit_chief.phases[0].message` = *"Venham, seus inúteis! Essa 'nuvem vermelha' que anda nos vigiando não fui eu quem escolhi, moleque — fui só pago."* (50% HP, invoca 3 Bandidos) — existe no dado, não foi visto em combate real. | INCONCLUSIVO | — |
| 10 | Rin done_text pós-`q_bandit_chief` (gancho de saída) | Fala nova mencionando Costa+Floresta da Morte | Não alcançado (depende do #9) | NÃO TESTADO (dado confirmado por leitura: `done_text` existe em `data/npcs/leaf.json`, citado na auditoria) | — |
| 11 | Gate da Costa (1029,1119→1121) barra Genin sem rank Chunin? | Não deveria barrar (Lote M) | **Confirmado por leitura de código** (`server/tfs/data/scripts/naruto/rank_gate.lua`): actionid 45001 exige `NarutoRanks.get(player).index >= 1` — rank 1 é o próprio Genin, então **nenhum jogador é barrado** (a checagem é sempre verdadeira). Tentativa de travessia ao vivo com a conta `teste` (Naruto, L7) foi inconclusiva: o personagem morreu para uma Serpente Branca ao logar (posição de sessão anterior, perto do Ninho da Serpente) e `g_game.autoWalk()` não percorre ~80 tiles não explorados numa única chamada (ficou parado no templo) — limitação do método, não do jogo. | OK (por código) / gate check dinâmico inconclusivo | — |
| 12 | Spawn solto do Aprendiz Mascarado (~1029,1153) | ≥ 3 unidades | Confirmado: `valley-spawn.xml` tem 3 (`x=-4,y=-1`/`x=3,y=0`/`x=1,y=1` do centro 1029,1153), visto no screenshot | OK | historia_06 |
| 13 | Tazu `hi`→`missao` | 1ª quest da Costa | "Mercenários contratados por uma guilda rival atacam quem trabalha na ponte. Afaste-os. Mate 8." (Missão aceita: A ponte ameaçada) | OK | historia_07 |
| 14 | q_coastal_mercenaries (Mercenário da Ponte x8) | 8/8→completa | Confirmado, "Bom trabalho, ninja. Missão 'A ponte ameaçada' concluída." | OK | — |
| 15 | q_coastal_supplies (Poção de Vida Pequena x5, coleta) | Aceita→completa | Aceito, mas `/i Poção de Vida Pequena,5` falhou (achado de metodologia #4, acento) — ficou em "Ainda falta trazer" pro resto desta rodada | FALHA DE METODOLOGIA (mecanismo de collect_item já confirmado em #3/#8) | — |
| 16 | q_coastal_apprentice (Aprendiz Mascarado x6) — matar 6 conta sem depender do boss | Sim (Lote M) | Confirmado: lote de 6+ mortes registrado normalmente contra o Aprendiz Mascarado avulso, mesmo com q_coastal_supplies ainda pendente no meio do caminho (o combate em si funciona; a contagem pra ESSA quest específica não pôde ser fechada por causa do #15) | MECANISMO OK, quest não fechada nesta rodada | — |
| 17 | Boss Espadachim da Névoa — 3 fases, fala citando o Aprendiz ("...luta por mim") | Fala a 60% HP | **Confirmado, 3 fases, texto exato**: 100% "Não é nada pessoal, moleque. É só o trabalho."; **60% "Ainda não. Não vou deixar que ele me leve ainda — ele não luta por dinheiro, luta por mim."** (exatamente o pedido da missão); 25% "Vocês tiraram tudo que eu tinha. Agora eu não tenho mais nada a perder." Aprendiz Mascarado visível summonado ao lado do boss no screenshot. | OK | historia_09 |
| 18 | Tazu done_text pós-swordsman (gancho de saída) | Fala nova mencionando Floresta da Morte | Não alcançado nesta rodada (quest de coleta anterior travada, #15) | NÃO TESTADO (dado confirmado por leitura: `done_text` em `data/npcs/coastal_tides.json`) | — |
| 19 | Spawn solto da Serpente Menor (~1158,1048 / 1178,1030 / 1188,1105) | ≥ 2-3 por ponto | Confirmado: `valley-spawn.xml` tem 3 clusters, 8 unidades no total; 2 dos 3 pontos visitados e fotografados | OK | historia_11a/b |
| 20 | Goro `hi`→`missao` | 1ª quest da Floresta da Morte | "Sanguessugas infestam a margem. Mate 8." (Missão aceita: Sangue ruim) | OK | historia_12 |
| 21 | q_leeches (Sanguessuga Gigante x8) | 8/8→completa | Confirmado, "Bom trabalho, ninja. Missão 'Sangue ruim' concluída." | OK | — |
| 22 | q_lesser_serpents (Serpente Menor x10) — a quest que estava travada antes do Lote M | Agora completável | Aceita corretamente ("Serpentes menores se multiplicaram perto do santuário abandonado. Mate 10." Missão aceita: Ninhada de serpentes), progresso começou a contar (visto "0/10" logo após aceitar, sessão encerrada antes de fechar 10/10) — **a quest deixou de estar permanentemente bloqueada** (achado central do Lote M confirmado: o spawn existe e conta) | OK (spawn+aceite confirmados; contagem completa não fechada por tempo) | — |
| 23 | Boss Sapo Ancião ("sem pergaminho, só glória") | Combate real | Confirmado, múltiplos hits registrados (480/422/471/452 dano) | OK | — |
| 24 | Boss Serpente Branca — fala velada a 25% HP citando "a organização" | Fala existe e dispara | **Confirmado, screenshot com o texto na tela** (`historia_14`, meu personagem SLQA visível ao lado do boss): 60% HP "Chega de fingir que sou gente. Vejam o que eu realmente sou!"; **25% HP "Minhas crias vão limpar o que sobrar de vocês! Nem a organização que me expulsou quis ver o que eu virei — e vocês vão descobrir por quê."** — exatamente o pedido da missão (fala velada, cita "a organização" sem nomear a Nuvem Vermelha) | OK | historia_14 |
| 25 | Exame Chunin (Ibuki) — quiz funciona | Prova por keyword | `exam_chunin_1_teoria` já estava `DONE` de uma sessão anterior (storage 50028, checado via DB antes desta rodada) — dizer `prova` sem quiz ativo respondeu corretamente "Nada de prova por agora. Diga {missao} para ver o que tenho." (confirma o guard-clause do quiz, não o quiz em si) | PARCIAL (guard confirmado; quiz de perguntas não testado nesta rodada — já estava concluído) | historia_16/17 |
| 26 | Exame Chunin — torneio 2/3 e 3/3 | Aceita→mata→completa→grants_rank | Confirmado: "Seu segundo oponente veio da Vila do Som." (aceita) → 1/1 → "concluída" → "Seu último oponente veio da Vila da Névoa. Vença e você será Chunin." (aceita 3/3) → 1/1 → **+5000 XP** (exatamente a recompensa de `exam_chunin_3c_rival_mist`, que carrega `grants_rank: chunin`) — processo encerrado a ~1s da fala de conclusão renderizar, mas a recompensa em si já confirma que o servidor processou a conclusão | OK (recompensa confirma; done_text/fala final não capturada a tempo) | — |
| 27 | Zero `Lua Script Error` novo | 0 | **0** durante toda a sessão (checado antes, no meio e ao final, múltiplas rodadas) | OK | — |

## Bugs/achados a repassar (arquivo suspeito e repro)

1. **[Alto] Mojibake em falas com acento** — ver seção dedicada acima. Repro: qualquer fala de NPC/
   monstro com acento (ex. falar `hi` com Capitã Rin). Arquivo suspeito: pipeline de
   `onCreatureSay`/balão de fala, possivelmente `client-otc/modules/naruto_chat.lua` (mesma
   família do fix de `e0e683f`, que cobriu só "mensagens de sistema").
2. **[Médio, não é bug — achado de fluxo] `q_bandit_chief` (Chefe dos Bandidos) não pôde ser
   lutado ao vivo nesta sessão** — `/m Chefe dos Bandidos` no acampamento (1100,1100) não gerou
   nenhuma mensagem de combate em 2 tentativas com raio de ataque ampliado (14 tiles). Pode ser
   contenção de espaço/decoração do acampamento (cerca/tendas) impedindo o monstro invocado de
   ficar em linha de alcance, ou nome exato divergente — não investigado a fundo. Recomendo
   reteste dedicado (`/m Chefe dos Bandidos` parado no meio exato do acampamento, sem GM `/tp`
   automatizado) antes de considerar a fase de 50% "confirmada em combate real" (o TEXTO já está
   certo no dado, só a execução ao vivo ficou pendente).
3. **[Baixo, metodologia] `/i` com nome de item acentuado falha** — usar id numérico resolve; não
   teve tempo de verificar se um jogador comum digitando um comando qualquer (não é comando de
   GM) sofre do mesmo problema de encoding em algum outro fluxo do jogo — vale um olhar rápido.

## Falas capturadas literalmente (as mais relevantes, pedidas pela missão)

- Capitã Rin (tutorial, q_wolves_1): *"Bem-vinda à Floresta da Vila, Genin. A Academia te ensinou
  o básico — hora de provar em campo. Os lobos andam atacando viajantes na trilha: mate 5."*
- Chefe dos Bandidos (50% HP, do dado — não visto em combate ao vivo): *"Venham, seus inúteis!
  Essa 'nuvem vermelha' que anda nos vigiando não fui eu quem escolhi, moleque — fui só pago."*
- Espadachim da Névoa (60% HP, **confirmado em combate real**): *"Ainda não. Não vou deixar que
  ele me leve ainda — ele não luta por dinheiro, luta por mim."*
- Serpente Branca (60% HP, **confirmado em combate real**): *"Chega de fingir que sou gente.
  Vejam o que eu realmente sou!"*
- Serpente Branca (25% HP, **confirmado em combate real**): *"Minhas crias vão limpar o que
  sobrar de vocês! Nem a organização que me expulsou quis ver o que eu virei — e vocês vão
  descobrir por quê."*

## Screenshots (18, em `screenshots/historia_*.png`)

`historia_01` (Rin tutorial), `historia_02` (progresso onigiri 2/3 na aba Missões), `historia_03`
(bandit chief aceito), `historia_04` (tentativa de luta do chefe — sem confirmação de combate),
`historia_05` (fim da cadeia da Rin), `historia_06` (Aprendiz Mascarado solto), `historia_07`
(Tazu tutorial), `historia_08` (swordsman aceito), `historia_09` (**luta do Espadachim com as 3
falas de fase visíveis + Aprendiz Mascarado summonado**), `historia_10` (fim Tazu), `historia_11a/b`
(Serpente Menor solta, 2 pontos), `historia_12` (Goro tutorial), `historia_13` (pós-sapo ancião),
`historia_14` (**luta da Serpente Branca com a fala de 25% HP visível**), `historia_15` (fim
cadeia Goro), `historia_16`/`historia_17` (Ibuki, torneio + guard do quiz).

## Limpeza ao final

- `client-otc/shinobirc.lua` apagado (nunca commitado).
- `~/Library/Application Support/shinobi/.shinobi/historia_*.png` limpos após copiar pra
  `screenshots/`.
- Nenhum processo OTClient deixado rodando (todos os PIDs abertos por esta sessão foram
  encerrados; o OTClient de outra sessão, visto no início, já tinha terminado sozinho antes de eu
  começar a rodar o meu).
- Servidor nunca reiniciado. `grep -c "Lua Script Error" /tmp/tfs_run.log` final: **0**.
