# Auditoria da história do jogador — Shinobi Legends

*Autor: narrative/quest designer sênior (sessão de auditoria). Data: 2026-09-05.
Escopo: jornada narrativa completa, arco por arco, na ordem em que o jogador a vive
(ver "Ordem canônica" abaixo). Só leitura de `data/`/`server/generated`/`tools/` — nenhum
dado ou código foi alterado nesta missão. Toda afirmação sobre estado atual cita
arquivo (e id/linha quando aplicável); toda proposta é marcada claramente como proposta.*

*Fontes principais: `CLAUDE.md`; `docs/00-biblia-do-jogo.md` (seções 2 "História", 4
"Jornada", 6 "Bestiário", 8 "Personagens e NPCs", 13 "Inconsistências"); `docs/lore/mundo.md`;
`docs/lore/progressao.md`; `docs/sistemas/progressao-jogador.md`; `docs/sistemas/progressao-servidor.md`;
`docs/sistemas/mapas.md`; `docs/sistemas/monstros-e-pvm.md`; `docs/qa/playtest-l1-20-r3.md`;
`data/npcs/*.json`; `data/monsters/*.json`; `data/tasks.json`; `data/dailies.json`;
`data/achievements.json`; `data/ranks.json`; `data/maps/spawns_lore.json`;
`server/generated/lib/naruto_quests.lua`, `naruto_ranks.lua`; `tools/map/build_valley.py`,
`build_regions.py`; `tools/export_tfs.py`.*

## Ordem canônica usada nesta auditoria

O pedido original numera 7 arcos (Academia → Floresta da Vila → Costa → Exame Chunin → Ruínas →
Montanha → Covil). **Achado estrutural #0, antes de tudo**: nos dados reais, "Academia" e
"Floresta da Vila" **não são dois arcos** — são a mesma região, o mesmo NPC dador de missão
(`quest_giver_leaf` = Capitã Rin, `data/npcs/leaf.json`) e a mesma cadeia sequencial de 6 quests
(`q_wolves_1` → `q_bandit_chief`). Esta auditoria trata os dois como **Arco 1 "Academia / Floresta
da Vila"** e segue com a numeração do pedido a partir daí (Arco 2 = Costa das Marés, etc.), mas
preserva a referência "7 arcos" nos títulos de seção para não perder o mapeamento com o pedido
original.

| # nesta auditoria | Arco | Nível | Rank do jogador | Arquivos de dados |
|---|---|---|---|---|
| 1 | Academia / Floresta da Vila | 1–10 (+até 12 p/ boss) | Genin | `data/npcs/leaf.json` (Capitã Rin), `data/monsters/forest.json` |
| 2 | Costa das Marés | 12–19 | Genin (mas gate exige Chunin — ver Achado #1) | `data/npcs/coastal_tides.json`, `data/monsters/coastal_tides.json` |
| 3 | Floresta da Morte / Exame Chunin | 10–25 | Genin→Chunin | `data/npcs/leaf.json` (Velha Sumi, Rastreador Goro, Instrutora Ibuki), `data/monsters/swamp.json` |
| 4 | Ruínas do Clã Marionetista | 25–50 | Chunin | `data/npcs/ruins.json`, `data/monsters/ruins.json` |
| 5 | Montanha do Trovão | 50–80 | Jonin | `data/npcs/mountain.json`, `data/monsters/mountain.json` |
| 6 | Covil da Nuvem Vermelha | 80–100 | Anbu→Kage | `data/npcs/akatsuki_lair.json`, `data/monsters/akatsuki_lair.json` |

*(6 arcos jogáveis distintos no total — o pedido original conta 7 porque separa Academia de
Floresta da Vila; nos dados eles são um só, ver Achado #0.)*

---

## Sumário executivo

A jornada, no papel (dados de missão, fases de boss, itens de recompensa), é bem mais completa do
que costuma acontecer nesse estágio de projeto: os 6 arcos têm cadeias de missão de 6-7 passos,
quase todos com pelo menos 1 objetivo de `collect_item` ou `keyword_quiz` além de `kill`, e 15 dos
16 bosses/mini-bosses do jogo têm fases reais com falas, invocação de reforços e/ou escalada de
dano — não é um esqueleto. O problema real do jogo hoje **não é falta de conteúdo escrito, é
conteúdo escrito que nunca chega ao jogador**: 3 bugs de dados/mapa confirmados no artefato final
(`server/generated/world/valley-spawn.xml`) tornam 2 arcos inteiros sem dador de missão (Ruínas,
Montanha) e 2 missões de outros arcos matematicamente quase impossíveis (Aprendiz Mascarado na
Costa, Serpente Menor na Floresta da Morte) — e um 4º achado, de nível de mapa/gate, inverte a
ordem pretendida dos 2 primeiros arcos pós-tutorial (Costa das Marés fica gated atrás do próprio
Exame Chunin que ela deveria preceder). Ao lado disso, um problema transversal de narrativa: a
"Organização Nuvem Vermelha" — o fio que a bíblia e o doc de lore descrevem como unindo os 6 arcos
— está **ausente de quase todo diálogo real do jogo**, só aparecendo como resposta de quiz na
Montanha (arco 5 de 6) e por nome no Covil (arco final).

### Nota de completude narrativa por arco (0–10)

| Arco | Nota | Por quê (1 linha) |
|---|---|---|
| 1. Academia / Floresta da Vila | **8** | Cadeia de 6 missões fechada, boss com fases, todo bestiário spawnado — só falta gancho de saída e a semente da Nuvem Vermelha |
| 2. Costa das Marés | **4** | Gate de rank barra o próprio nível que a região foi desenhada para atender (Achado #1); 1 das 6 missões (Aprendiz Mascarado) provavelmente incompletável |
| 3. Floresta da Morte / Exame Chunin | **7** | Exame Chunin completo e funcional (quiz, pergaminhos, torneio); 1 missão secundária (Serpente Menor) sem spawn solto no artefato final; boss duplicado entre 2 quests |
| 4. Ruínas do Clã Marionetista | **3** | Bestiário e boss 100% no mapa, mas o dador de missão (Ancião Kaito) e o mercador (Tsubaki) **nunca foram posicionados** — nenhuma das 7 missões é aceitável hoje, bloqueando metade do Exame Jonin |
| 5. Montanha do Trovão | **3** | Mesmo problema do Arco 4 (Mestra Yuki/Ferreiro Genzo ausentes do mapa), bloqueando as 2 metades do Exame Anbu; some o quiz pede uma resposta nunca ensinada ao jogador |
| 6. Covil da Nuvem Vermelha | **7** | Único arco com os 2 NPCs-chave e bestiário 100% presentes; falta só polimento de clímax (o boss final é o menos elaborado mecanicamente do jogo) e variedade de objetivo |

*(Nota de 0-10 mede completude narrativa jogável hoje — presença física no mapa, missão
aceitável/completável, gancho de progressão — não a qualidade do texto escrito, que é
consistentemente boa em todos os 6 arcos.)*

### Top 10 lacunas do jogo (visão geral, com referência cruzada)

1. **Ancião Kaito e Tsubaki nunca foram posicionados no mapa** (Arco 4) — bloqueia as 7 missões
   das Ruínas e metade do Exame Jonin. Confirmado em `valley-spawn.xml`. Ver Arco 4, item B1.
2. **Mestra Yuki e Ferreiro Genzo nunca foram posicionados no mapa** (Arco 5) — bloqueia as 7
   missões da Montanha e as 2 metades do Exame Anbu. Confirmado em `valley-spawn.xml`. Ver Arco 5,
   item C1.
3. **Gate de rank Chunin na entrada da Costa das Marés contradiz o nível do próprio conteúdo**
   (Arco 2) — região nível 12-19 fica inacessível a quem ela foi desenhada para atender. Ver Arco
   2, Achado #1, item A1.
4. **`Serpente Menor` (`lesser_serpent`) sem spawn solto no mapa publicado** (Arco 3) — `q_lesser_
   serpents` (10 mortes) só é alimentável pelos 2 summons por luta do boss `boss_white_serpent`
   (respawn 1h). Ver Arco 3, item B2.
5. **`Aprendiz Mascarado` (`masked_apprentice`) sem spawn solto no mapa publicado** (Arco 2) — `q_
   coastal_apprentice` (6 mortes) só é alimentável pelo summon único do boss `boss_mist_swordsman`
   por luta. Ver Arco 2, item A2.
6. **O fio da "Nuvem Vermelha" é essencialmente invisível ao jogador** até o Arco 5 (resposta de
   quiz) e o Arco 6 (nome do boss) — apesar de a bíblia/lore descrever os 4 primeiros arcos como
   pontos de infiltração da organização, nenhuma fala de NPC nos Arcos 1-4 nomeia isso.
7. **Nenhum arco tem gancho de saída** — nenhuma fala de NPC, em nenhum dos 6 arcos, aponta
   explicitamente para o próximo destino depois da última missão da cadeia local.
8. **Boss duplicado entre 2 cadeias de missão na Floresta da Morte** (Arco 3) — `boss_elder_toad`
   e `boss_white_serpent` cada um precisa morrer 2 vezes (uma para a Goro, outra para o Exame) por
   causa de storages independentes, multiplicando tempo de respawn desnecessariamente.
9. **Quiz da Montanha pergunta uma resposta que o jogo nunca ensinou** (Arco 5) — a pergunta sobre
   quem lançou "a dupla imortal" espera "Nuvem Vermelha"/"organização", mas nenhuma fala anterior
   ensinou isso ao jogador (agrava o achado #6 transformando-o em obstáculo de gameplay).
10. **O boss final do jogo (`boss_crimson_ancestor`) é mecanicamente o mais raso dos bosses do
    Covil** (Arco 6) — só escalada de `attack_multiplier`, sem summon nem transformação, abaixo do
    nível de elaboração de bosses de arcos anteriores (Ruínas, Montanha).

### Plano de execução em 3 lotes (resumo)

- **Lote A** (Arcos 1-2, Academia/Floresta da Vila + Costa das Marés): corrige o gate da Costa
  (#3) e o Aprendiz Mascarado (#5), planta a semente da Nuvem Vermelha e os 2 primeiros ganchos de
  saída. Arquivos: `data/npcs/leaf.json` (só Capitã Rin), `data/npcs/coastal_tides.json`,
  `data/monsters/forest.json`, `data/monsters/coastal_tides.json`,
  `tools/map/build_regions.py` (só `build_coastal_tides`).
- **Lote B** (Arcos 3-4, Floresta da Morte/Exame Chunin + Ruínas): corrige a Serpente Menor (#4) e
  posiciona Ancião Kaito/Tsubaki (#1, o achado mais crítico do jogo — desbloqueia metade do Exame
  Jonin), remove a redundância de boss (#8) e adiciona 2 ganchos de saída. Arquivos:
  `data/npcs/leaf.json` (só Velha Sumi/Rastreador Goro/Instrutora Ibuki — coordenar com Lote A),
  `data/npcs/ruins.json`, `data/monsters/swamp.json`, `data/monsters/ruins.json`,
  `tools/map/build_valley.py` (só `DEATH_SETS`), `tools/map/build_regions.py` (só `build_ruins`).
- **Lote C** (Arcos 5-6, Montanha do Trovão + Covil): posiciona Mestra Yuki/Ferreiro Genzo (#2, tão
  crítico quanto #1 — desbloqueia as 2 metades do Exame Anbu), corrige o quiz que pergunta o que
  nunca foi ensinado (#9), e dá polimento de clímax ao boss final (#10). Arquivos:
  `data/npcs/mountain.json`, `data/npcs/akatsuki_lair.json`, `data/monsters/mountain.json`,
  `data/monsters/akatsuki_lair.json`, `tools/map/build_regions.py` (só `build_mountain`).

Ver seção "Plano de execução em 3 lotes paralelos" (ao final deste documento) para a tabela
completa de missões/mudanças, falas-chave e critérios de aceite testáveis in-game.

---

## Arco 1 — Academia / Floresta da Vila (nível 1–12, Genin)

### Fluxo atual real

1. O jogador nasce Genin no templo/praça da Vila da Folha (`docs/sistemas/mapas.md`, zona
   "Floresta da Vila", templo em 1029,1042) com o kit inicial já equipado (`character_switch.lua`
   gerado — bandana, colete de genin, calça ninja, sandálias, kunai/shuriken de ferro, amuleto da
   Academia; confirmado em 3 playtests, `docs/qa/playtest-l1-20-r2/r3/r4.md`).
2. Na praça/rua comercial (`SHOP_ROW_Y`, `tools/map/build_valley.py:322-327`) ficam lado a lado
   **Ichiro, o Mercador** (`merchant_leaf`, loja, ~1037,1053), **Mestre Hayato** (`scroll_master_leaf`,
   vende pergaminhos de jutsu fora do kit automático, ~1042,1053) e **Capitã Rin**
   (`quest_giver_leaf`, ~1046,1053) — os três NPCs relevantes do arco ficam a poucos passos um do
   outro, fácil de descobrir.
3. Capitã Rin dá 6 missões **sequenciais** (`data/npcs/leaf.json`, array `quests` de
   `quest_giver_leaf`, ordem = ordem da lista, regra do `CLAUDE.md`):
   - `q_wolves_1` — matar 5 Lobos (`wolf`, L2). Recompensa: 120 XP, 60 ryo, 1 poção pequena.
   - `q_forest_snakes` (rank D) — matar 8 Cobras da Floresta (`forest_snake`, L4). 260 XP, 90 ryo,
     `amuleto_academia`.
   - `q_bandits_1` — matar 10 Bandidos (`bandit`, L5). 400 XP, 200 ryo, `scroll_kawarimi`.
   - `q_bandit_archers` (rank C) — matar 8 Bandidos Arqueiros (`bandit_archer`, L7). 500 XP,
     220 ryo, `shuriken_iron`.
   - `q_forest_supplies` (rank C) — **entregar** 5 `wolf_pelt` (item que o próprio Lobo dropa,
     `data/monsters/forest.json` loot) — a única missão de coleta/entrega do arco, mecanicamente
     suportada por `objective.kind: collect_item` (`tools/export_tfs.py:1823` e ss.).
   - `q_bandit_chief` — matar **O Chefe dos Bandidos** (`boss_bandit_chief`, L12, boss). 1500 XP,
     800 ryo, `backpack_leather`.
4. O Chefe dos Bandidos fica no "acampamento", cercado por Bandidos comuns
   (`tools/map/build_valley.py:1144-1149`, grupo de spawn em `CAMP_CENTER`, respawn 3600s) — texto
   da missão ("no sudeste da floresta") bate com a posição real do acampamento no mapa.
5. Boss tem 2 fases reais (`data/monsters/forest.json`, `boss_bandit_chief.phases`): 50% HP invoca
   3 Bandidos ("Venham, seus inúteis!"), 20% HP `attack_multiplier: 1.5` ("Não vou cair para um
   genin!") — mecânica de fase funcionando, não é só um monstro com HP alto.
6. Achievements fecham o arco: `chain_floresta_da_vila` (`quest_chain_complete`, target
   `quest_giver_leaf` — só conta as 6 quests da Rin, não as de Goro/Ibuki que moram no mesmo
   arquivo mas noutro NPC id) e `boss_boss_bandit_chief` (`kill_specific`) — ambos com lógica real
   no servidor (`docs/00-biblia-do-jogo.md` §5 "Tarefas, diárias e conquistas").
7. Tarefas repetíveis (Mestre de Tarefas Jiro, `task_master_leaf`, ~1030,1067) cobrem `wolf`,
   `bandit`, `bandit_archer`, `forest_deer`, `forest_snake` em 3 tiers cada (`data/tasks.json`) —
   dá o que fazer depois de esgotar as 6 quests de história sem sair da região.

### Lacunas e incoerências

- **Sem gancho de saída.** O texto de `q_bandit_chief` ("Acabe com o Chefe dos Bandidos no sudeste
  da floresta") não aponta para nenhum arco seguinte — nem Capitã Rin, nem nenhum outro NPC da
  Vila da Folha tem uma fala pós-`q_bandit_chief` que diga "vá para a Costa" ou "procure a Floresta
  da Morte" (`data/npcs/leaf.json`, checado: não existe campo de diálogo pós-quest, só o texto da
  própria missão). Um jogador que termina o arco 1 não recebe nenhuma pista in-game de onde
  continuar — precisa descobrir Floresta da Morte/Costa por conta própria ou por wiki externa.
- **O fio da Nuvem Vermelha nunca aparece aqui.** `docs/lore/mundo.md` e a bíblia (§2, "novo")
  descrevem o Chefe dos Bandidos como "um eco pequeno demais do que está por vir" — uma pista
  deliberada de que a Organização Nuvem Vermelha já está se infiltrando. Nenhuma fala de Rin, do
  próprio Chefe (ele não tem `phases[].message` que mencione nada disso) ou de qualquer outro NPC
  do arco 1 sequer alude a isso. A conexão existe só no documento de lore, invisível ao jogador —
  ver "Achado transversal" no Sumário executivo.
- **Cervo (`forest_deer`) não tem missão nenhuma** — monstro passivo, puramente decorativo/XP
  opcional (consistente com a bíblia, que já o marca como "opcional"; não é bug, mas é uma
  oportunidade perdida de missão de coleta trivial de tutorial, ex. "traga 3 onigiri").
- **Posições de Rin/Hayato não estão na bíblia.** `docs/00-biblia-do-jogo.md` §8 documenta a
  posição exata da Instrutora Ibuki e da Capitã Suzu, mas não a de Capitã Rin/Mestre Hayato — as
  coordenadas só existem em `tools/map/build_valley.py:324-326` (~1046,1053 e ~1042,1053). Lacuna
  de documentação, não de jogo (o NPC existe e está posicionado; só não está resumido na bíblia).

### O que falta para ficar completo como história

O arco já é, dos 6, o **mais fechado** (começo → meio com 2 tipos de objetivo → boss com fases →
loot temático → tarefas de long-tail). Falta pouco, e é tudo de baixo esforço:

1. **Gancho de saída (P).** Adicionar 1 linha de diálogo em `q_bandit_chief` (texto de recompensa)
   ou criar uma 7ª entrada "pós-quest" (mensagem, sem objetivo novo) em que Capitã Rin diz algo como
   *"Bom trabalho, Genin. Mas isso foi só a estrada perto de casa — a Floresta da Morte separa
   quem está pronto do resto do mundo, e ouvi dizer que mercadores da Costa das Marés estão
   contratando gente como você."* — aponta para os arcos 2 e 3 sem forçar ordem.
2. **1 linha que planta a semente da Nuvem Vermelha (P).** No `phases` do Chefe dos Bandidos (50%
   HP, já tem `message`), trocar ou complementar a fala para incluir uma referência sutil — ex.
   *"Não fui eu quem escolheu essa 'nuvem vermelha' nos vigiando, moleque — fui só pago."* — planta
   a pista sem entregar a resposta, coerente com o resto do jogo (a resposta só aparece perto do
   fim, no quiz da Montanha e no Covil).
3. **Missão trivial do Cervo (P, opcional).** `q_forest_deer_1`: entregar 3 onigiri (item que o
   Cervo já dropa) a Capitã Rin — mais uma variedade de `collect_item` bem no começo do jogo, sem
   custo de sistema novo.

### Esforço e dependências

Esforço total do arco: **P** (pequeno) — é só texto/dados em `data/npcs/leaf.json`, sem sistema
novo, sem sprite novo, sem mapa novo. Nenhuma dependência de mapa/sprite/sistema pendente.

## Arco 2 — Costa das Marés (nível 12–19, Genin — mas ver Achado #1)

### Fluxo atual real

1. Do Portão Sul da Vila da Folha, uma trilha (`COAST_PATH_X=1029`, `tools/map/build_regions.py:443`)
   desce direto para a vila de pescadores (4 `blue_house`, patio de areia, barcos puxados na praia
   — `build_regions.py:456-505`), com uma placa "Costa das Marés - vila de pescadores (nível 12-19)"
   (`build_regions.py:466`).
2. **Antes de chegar lá**, porém, a trilha atravessa um **gate de rank Chunin** na borda da região
   (`build_regions.py:452-455`, `place_rank_gate(..., "chunin", ...)`, actionid 45002) — ver Achado
   #1 abaixo, é a lacuna mais séria encontrada nesta auditoria.
3. Na vila: **Mercador Itsuki** (loja, `merchant_coastal`, ~1026,1145) e **Ancião Tazu**
   (`quest_giver_coastal`, ~1032,1145) lado a lado; **Mestre de Tarefas Umi** (`task_master_coastal`)
   um pouco atrás (~1029,1147).
4. Ancião Tazu dá 6 missões sequenciais (`data/npcs/coastal_tides.json`):
   - `q_coastal_mercenaries` — matar 8 `mercenary_bridge` (L12). 900 XP, 250 ryo, poção pequena.
   - `q_coastal_supplies` (rank D) — **entregar** 5 `health_potion_small` ao Ancião. 700 XP, 200 ryo,
     `bracelete_do_viajante`.
   - `q_coastal_scouts` — matar 8 `mist_scout` (L14). 1300 XP, 350 ryo, `shuriken_iron`.
   - `q_coastal_guardians` — matar 8 `mist_guardian` (L16). 1800 XP, 500 ryo, poção média.
   - `q_coastal_apprentice` (rank B) — matar 6 `masked_apprentice` (L17). 3200 XP, 900 ryo,
     `calca_do_batedor`. **Ver Achado #2 — provavelmente impossível de completar hoje.**
   - `q_coastal_swordsman` — matar **O Espadachim da Névoa** (`boss_mist_swordsman`, L19). 12000 XP,
     4000 ryo, `katana_ronin`, `grants_rank_progress: "jonin"` (metade do Exame Jonin, junto com o
     Marionetista das Ruínas, sem ordem entre si — `docs/lore/progressao.md`).
5. O boss fica numa plataforma de pedra no fim de um cais de madeira ("Arena do Espadachim da
   Névoa - ponte inacabada", `build_regions.py:520-521`) — há também uma 2ª ponte, só cenográfica,
   "sabotada pelos mercenários da guilda rival" (`build_regions.py:540-542`), reforço visual do
   motivo do arco.
6. Boss tem 3 fases reais (`data/monsters/coastal_tides.json`): 100% intro ("Não é nada pessoal,
   moleque"), **60% HP invoca o Aprendiz Mascarado** (1×, "Ainda não. Não vou deixar que ele me
   leve ainda."), 25% `attack_multiplier: 1.6` ("Vocês tiraram tudo que eu tinha..."). É o único
   boss do jogo cujo "ajudante" (o Aprendiz) é mecanicamente **só um summon de fase**, nunca um
   monstro solto no mapa — dado explícito em `data/maps/spawns_lore.json` ("requests"): *"a
   Aprendiz Mascarado, masked_apprentice, é só invocado em combate — não precisa de spawn
   próprio"*.
7. Spawns confirmados no mapa (`build_regions.py:565-577`): `mercenary_bridge` ×6 num grupo,
   `mist_scout` ×4, `mist_guardian` ×3, `boss_mist_swordsman` ×1 (respawn 7200s). **Nenhum grupo de
   `masked_apprentice`** é criado como monstro solto em lugar nenhum do mapa.

### Lacunas e incoerências

**Achado #1 (crítico, o maior da auditoria): o gate de entrada contradiz o nível do próprio
conteúdo e a curva de XP oficial do jogo.** A Costa das Marés é nível 12–19 (placa in-game,
`data/monsters/coastal_tides.json`, e a própria tabela "Jornada do jogador" da bíblia, que
intercala conteúdo da Costa nos blocos **11–15** e **16–20**, lado a lado com Floresta da Morte,
como conteúdo paralelo de Genin/Chunin recém-promovido). Mas o tile de entrada da região exige
rank **Chunin** (`tools/map/build_regions.py:452-455`, `RANK_GATE_ACTIONID["chunin"] = 45002`,
`docs/sistemas/mapas.md` confirma na tabela de gates). Rank Chunin só se obtém com **nível mínimo
20** e o Exame Chunin completo — que roda inteiro dentro da **Floresta da Morte**, a única região
sem gate (`docs/sistemas/mapas.md`: *"— (Exame Chunin roda dentro dela; gatear a entrada criaria
paradoxo)"*). Ou seja: hoje, um Genin literal **não consegue fisicamente entrar na Costa das
Marés** antes de já ter virado Chunin (nível 20+) em outra região — o oposto do que a própria
tabela de XP do jogo descreve como plano ("nível 11–20: Costa das Marés e Floresta da Morte em
paralelo"). Na prática, isso empurra 100% dos jogadores a fazer Floresta da Morte inteira primeiro
e só visitar a Costa depois, já Chunin e várias vezes acima do nível dos monstros de lá (L12–19),
tornando a região inteira (5 missões + boss) trivial e o loot dela (bracelete, shuriken de ferro,
poção média, `calca_do_batedor`) obsoleto no momento em que se torna acessível. É uma contradição
entre três fontes do próprio projeto (a tabela de Jornada da bíblia, a placa in-game "nível 12-19",
e o código do gate) — não uma opinião desta auditoria.

**Achado #2 (alto): `q_coastal_apprentice` (e as tarefas equivalentes) provavelmente não são
completáveis.** A quest pede matar 6 `masked_apprentice`, e `data/tasks.json` tem 3 tiers de tarefa
repetível para o mesmo monstro (`monster_id: "masked_apprentice"`, como qualquer outro monstro
comum). Mas o próprio arquivo de planejamento de spawns (`data/maps/spawns_lore.json`, campo
`requests`) documenta explicitamente que o Aprendiz **só existe como summon de fase do boss**, e a
implementação em `tools/map/build_regions.py` confirma: não há nenhum `add_monster("Aprendiz
Mascarado", ...)` fora do grupo do próprio boss. Com o boss tendo respawn de 7200s (2h) e invocando
**1 único** Aprendiz por luta (na fase de 60% HP), juntar 6 mortes exigiria ~6 lutas completas
contra o Espadachim (12h de respawn só de espera, sem contar o tempo de matar o boss 6 vezes) — na
prática, uma missão "de matar 6" that's design-intended para um monstro raso, não para um
summon de boss raro. Isso é quase certamente um bug de dados (a intenção provável era um monstro
solto, nível 17, entre `mist_guardian` e o boss — o próprio nome da missão, "antes de chegar ao
Espadachim, alguém precisa afastar o aprendiz que protege os flancos dele", sugere isso).

- **Nomeação:** `Ancião Tazu` é analogamente ao "Tazuna" do arco real de Naruto que inspira este
  arco (Onda/Wave) — nome próprio diferente, dentro da regra do ADR-002, sem violação.
- **Sem gancho de saída** aqui também: o texto de `q_coastal_swordsman` fecha em "Derrote os dois"
  — nenhuma fala aponta de volta para a Floresta da Morte/Exame Chunin nem para frente (Ruínas/
  Montanha). Mesmo padrão do Arco 1.
- **O fio da Nuvem Vermelha não aparece aqui.** Nem Ancião Tazu, nem o Espadachim (`phases[].message`
  já citadas acima) mencionam a organização — apesar de a bíblia/lore descrever explicitamente o
  Espadachim como "contratado por uma guilda rival" que, no doc de lore (`docs/lore/mundo.md`),
  é na verdade um dos 4 pontos de infiltração da Nuvem Vermelha. No jogo, ele é só "uma guilda
  mercante rival" — a mesma desconexão do Arco 1.

### O que falta para ficar completo como história

O arco já tem um arco de 3 atos reconhecível (chegar → proteger a vila/ponte de mercenários e
batedores → confronto com boss+aprendiz) — falta consertar o que está quebrado, não inventar
missões novas:

1. **Corrigir o gate (G, mudança de dados/mapa, não de sistema).** Trocar o rank exigido no tile de
   entrada de "chunin" para nenhum (igual à Floresta da Morte) ou, no mínimo, para "genin" —
   preservando a barreira física só como decoração de fronteira, sem bloqueio real. Arquivo:
   `tools/map/build_regions.py:452-455` (`place_rank_gate(..., "chunin", ...)` → remover a chamada
   ou trocar o argumento). *Fora do escopo desta missão editar — só documentado aqui.*
2. **Corrigir `q_coastal_apprentice` (M).** Duas opções, ambas de esforço pequeno-médio: (a) dar ao
   Aprendiz Mascarado um spawn solto próprio (2–3 unidades, nível 17, entre `mist_guardian` e a
   arena do boss) — aí a missão de matar 6 volta a fazer sentido como está; ou (b) reduzir a missão
   para refletir a realidade atual (`count: 1`, matando o summon numa única luta do Espadachim, ou
   trocar o objetivo por outro monstro comum da região). Recomendação: opção (a), porque também
   resolve o "aprendiz sem lugar no mundo" narrativamente (ele devia rondar os flancos ANTES do
   confronto final, como o próprio texto da missão diz).
3. **Gancho de saída (P).** 1 fala nova no fim de `q_coastal_swordsman` — ex. Ancião Tazu:
   *"Vocês salvaram esta ponte. Mas ouvi um batedor comentar, antes de cair, sobre uma 'floresta
   que mata os fracos' rio acima — cuidado."* — aponta para a Floresta da Morte/Exame Chunin sem
   forçar ordem (o jogador pode já ter feito).

### Esforço e dependências

Esforço do arco: **M** — a correção do gate e do Aprendiz são as únicas mudanças reais; ambas em
dados/mapa já existentes (`tools/map/build_regions.py`, `data/npcs/coastal_tides.json`), sem
sistema novo. Depende só de decisão de design (nível-alvo real da Costa) antes de mexer no gate —
ver "Sistemas necessários" ao final para a recomendação técnica.

## Arco 3 — Floresta da Morte / Exame Chunin (nível 10–25, Genin→Chunin)

### Fluxo atual real

1. A mesma mata da Floresta da Vila continua para leste/sul num terreno mais pantanoso
   (`docs/sistemas/mapas.md`: zona "Floresta da Morte", sem gate — *"Exame Chunin roda dentro
   dela; gatear a entrada criaria paradoxo"*). Um Hub intermediário (`HUB`,
   `tools/map/build_valley.py:299`) recebe **Velha Sumi** (`merchant_swamp`, loja) e **Rastreador
   Goro** (`quest_giver_swamp`), além do **Mestre de Tarefas Ren** (`task_master_swamp`).
2. Rastreador Goro dá 7 missões sequenciais (`data/npcs/leaf.json`, NPC `quest_giver_swamp`):
   `q_leeches` (8× `leech` L10) → `q_lesser_serpents` (rank D, 10× `lesser_serpent` L18 —
   **ver Achado, provavelmente impossível hoje**) → `q_forest_death_collect` (rank C, entregar 6
   `toad_skin`) → `q_toads` (10× `giant_toad` L13) → `q_elder_toad_hunt` (rank B, matar
   `boss_elder_toad` sozinho, "sem pergaminho em jogo, só glória") → `q_rogues` (8×
   `rogue_ninja` L18) → `q_white_serpent` (matar `boss_white_serpent`, a missão-título do arco).
3. Em paralelo, **Instrutora Ibuki** (`exam_proctor_forest`, posição `(ACADEMY_GATE_TP[0]-2,
   ACADEMY_GATE_TP[1]-1)` — perto do portão da Academia na Vila da Folha, não dentro da própria
   Floresta da Morte, o que faz sentido narrativamente: o briefing do exame acontece antes de
   entrar) dá o **Exame Chunin** em 3 etapas, também via `data/npcs/leaf.json`:
   - `exam_chunin_1_teoria` — prova por palavra-chave (`kind: keyword_quiz`, 5 perguntas sobre
     chakra/elemento/mestre/ninjutsu/hokage), implementada de verdade (`tools/export_tfs.py:1552-
     1978`: keyword_quiz não conta mortes, só respostas certas — ver "Sistemas necessários" para o
     que ainda é "de compat").
   - `exam_chunin_2a_pergaminho_ceu` (matar `boss_elder_toad`, dá `scroll_heaven`) e
     `exam_chunin_2b_pergaminho_terra` (matar `boss_white_serpent`, dá `scroll_earth`) — **os
     mesmos dois bosses que Rastreador Goro já manda matar** em `q_elder_toad_hunt`/`q_white_serpent`
     (ver Lacunas).
   - `exam_chunin_3a/3b/3c` — torneio contra os 3 rivais (`exam_rival_stone/sound/mist`, L20,
     2× cada, arena dedicada perto da Instrutora — `tools/map/build_valley.py:1160-1172`), a
     última etapa carrega `grants_rank: "chunin"` e o item `vest_chuunin`.
4. Bosses com fases reais: `boss_elder_toad` (60% invoca 2 `giant_toad`, 30% `attack_multiplier
   1.6` + invoca 3 `leech`) e `boss_white_serpent` (60% **transforma** — `looktype: 890` — e invoca
   3 `forest_snake`, 25% `attack_multiplier 1.9` + invoca 2 `lesser_serpent`; 3 fases no total,
   "o boss mais canônico do jogo" per a bíblia).
5. Achievements: `chain_floresta_da_morte` (`quest_chain_complete`, target `quest_giver_swamp` —
   só as 7 quests do Goro), `exam_chunin` (`grants_rank`, target `chunin`), `boss_boss_elder_toad`
   e `boss_boss_white_serpent` (`kill_specific`).

### Lacunas e incoerências

**Achado (crítico, confirmado no artefato final): `Serpente Menor` (`lesser_serpent`), exigida por
`q_lesser_serpents` (10 mortes), não tem NENHUM spawn solto no mapa realmente publicado.**
Conferido nas 3 camadas: (1) `data/maps/forest_valley.json` — o JSON "fonte da verdade" original
tem 3 pontos de spawn dedicados a `lesser_serpent` (linhas 242-254: x=74,y=18 / x=82,y=8 /
x=86,y=34); (2) mas `tools/map/build_valley.py`, o script que de fato gera o mapa em produção,
usa suas próprias listas hardcoded (`FOREST_SETS`, `DEATH_SETS`, linhas 1099-1120) que **nunca
leem `forest_valley.json`** para posicionar monstro nenhum — e `lesser_serpent`/"Serpente Menor"
não aparece em nenhuma dessas listas; (3) o artefato final publicado,
`server/generated/world/valley-spawn.xml` (o spawn realmente carregado pelo TFS em produção),
confirma isso por contagem: **zero** ocorrências de `name="Serpente Menor"` no arquivo inteiro (só
existe como `summons` de fase do próprio boss `boss_white_serpent`, 2 unidades a cada luta, respawn
do boss 3600s). Ou seja, hoje, completar `q_lesser_serpents` (10 mortes) exigiria matar a Serpente
Branca **≥5 vezes** só para essa uma quest secundária — uma quest de rank D, pensada para vir
*antes* de sequer chegar perto do boss de fim de arco. Isso é quase certamente perda de dados na
migração do protótipo Godot (`forest_valley.json`) para o gerador de mapa do TFS
(`build_valley.py`), não uma decisão de design.

- **Redundância de abate entre a quest de Goro e a de Ibuki.** `q_elder_toad_hunt` (Goro, "prove
  que sobrevive ao Sapo Ancião sozinho — sem pergaminho em jogo, só glória") e
  `exam_chunin_2a_pergaminho_ceu` (Ibuki, mesma morte, dá o pergaminho) **pedem a morte do mesmo
  boss em duas quests separadas com storages independentes** — mesma coisa para
  `q_white_serpent`/`exam_chunin_2b_pergaminho_terra`. Cada boss tem respawn de 3600s (1h); um
  jogador seguindo as duas cadeias precisa matar cada boss **2 vezes** (2h+ de espera de respawn só
  entre as duas mortes, sem contar o tempo de luta), mesmo que narrativamente uma das duas seja
  "só glória, sem pergaminho em jogo" — o texto da quest de Goro já reconhece que é uma repetição
  ("sem pergaminho em jogo"), mas o custo real de tempo (respawn) não foi pensado junto.
- **Sem gancho de saída** para Ruínas/Costa (mesmo padrão dos arcos 1 e 2) — nem Goro nem Ibuki
  mencionam o próximo destino depois do torneio.
- **O fio da Nuvem Vermelha não aparece aqui** — nem o texto de Goro, nem as falas de fase da
  Serpente Branca, nem o quiz de Ibuki tocam no assunto (mesmo padrão dos arcos anteriores).

### O que falta para ficar completo como história

1. **Corrigir o spawn da Serpente Menor (P/M).** Portar os 3 pontos já desenhados em
   `data/maps/forest_valley.json` (x=74,y=18 / x=82,y=8 / x=86,y=34, coordenadas locais da zona)
   para `DEATH_SETS`/`DEATH_CLEARINGS` de `tools/map/build_valley.py` — o desenho já existe, só
   não foi portado. Sem isso, `q_lesser_serpents` deveria ser considerada **bloqueada** em
   qualquer relatório de QA atual.
2. **Resolver a redundância de boss (P, decisão de design).** Recomendação: trocar o objetivo de
   `q_elder_toad_hunt`/`q_white_serpent` (as quests da Goro) de `kill` duplicado para
   `quest_chain_complete` — checar se `exam_chunin_2a/2b` já foi concluída em vez de exigir uma
   segunda morte. Preserva o texto ("prove que sobrevive... sem pergaminho em jogo") como
   flavor, sem dobrar o tempo de espera de respawn.
3. **Gancho de saída (P).** 1 fala nova de Instrutora Ibuki ao conceder `grants_rank: "chunin"":
   *"Chunin. Agora sim pode seguir — a Costa das Marés precisa de gente como você, e as Ruínas do
   Clã Marionetista não vão esperar."*

### Esforço e dependências

Esforço: **M** — o conserto do spawn é mecânico (mapa já desenhado, só falta portar), a redundância
de boss é uma mudança de `objective.kind` em `data/npcs/leaf.json` bem localizada. Nenhuma
dependência de sistema novo.

## Arco 4 — Ruínas do Clã Marionetista (nível 25–50, Chunin)

### Fluxo atual real

1. Um portal/trilha na fronteira leste (`RUINS_X0=1200`, `tools/map/build_regions.py:613-658`)
   leva às ruínas, atrás de um gate de rank Chunin (dois marcadores em `RUINS_GATE_Y = (1020,
   1021)`, actionid 45002 — **este gate faz sentido**: o conteúdo é nível 25-50, bem acima do
   nível mínimo de Chunin (20), sem o paradoxo do Achado #1 da Costa).
2. **Tsubaki, a Escavadora** (`merchant_ruins`) e **Ancião Kaito** (`quest_giver_ruins`) deveriam
   ficar logo depois do gate — só o **Mestre de Tarefas Dokan** (`task_master_ruins`) tem posição
   real gerada (`dokan_pos = (x0+2, RUINS_GATE_Y[0])`, `build_regions.py:655`, e aparece na lista
   `npcs = [("Mestre de Tarefas Dokan", dokan_pos)]`, linha 758). **Ver Achado abaixo — os outros
   dois nunca são adicionados.**
3. Ancião Kaito dá 7 missões sequenciais (`data/npcs/ruins.json`): `q_ruins_intro` (rank D,
   entregar 8 `puppet_joint`) → `q_ruins_puppets` (12× `ruin_puppet` L27) → `q_ruins_sentinels`
   (10× `stone_sentinel` L32) → `q_ruins_curse_lore` (rank C, `keyword_quiz` de 3 perguntas sobre
   a maldição do clã — inclusive uma pergunta cuja resposta é *"para onde o gênio desertor
   pretende fugir depois das Ruínas?"*, keywords `"toca do som"`/`"som"` — referência direta à Vila
   do Som, coerente com o torneio do Exame Chunin ter um rival "da Vila do Som"; ADR-002: nome de
   lugar inspirado, não nome próprio de personagem, ok) → `q_ruins_shamans` (8× `curse_shaman`
   L44) → `q_ruins_deserter` (matar `elite_deserter`, mini-boss L46, "recrutando para a Toca do
   Som") → `q_ruins_boss` (matar `boss_puppeteer`, `grants_rank_progress: "jonin"`).
4. Bosses com fases reais: `elite_deserter` (40% HP `attack_multiplier 1.3`, 1 fase só, mini-boss
   mesmo) e `boss_puppeteer` (70% invoca 2 `ruin_puppet`, 40% invoca 1 `stone_sentinel` + 2
   `ruin_puppet`, 15% `attack_multiplier 1.5` — 3 fases, escalada de invocações coerente com "o
   marionetista comanda os bonecos do salão").
5. Todos os 6 monstros comuns + os 2 bosses **estão** no spawn final (`ruin_puppet` ×6,
   `stone_sentinel` ×4, `spectral_warrior` ×3, `curse_shaman` ×3, `elite_deserter` ×1,
   `boss_puppeteer` ×1 — conferido em `server/generated/world/valley-spawn.xml`), diferente do
   Arco 3 — o problema aqui não é o bestiário, é o dador de missão.

### Lacunas e incoerências

**Achado (crítico, o segundo maior da auditoria, e ele se repete idêntico no Arco 5): Ancião
Kaito e Tsubaki NUNCA são colocados no mapa — o arco inteiro não tem NPC de missão nem loja em
produção.** Buscando por esses dois nomes em `tools/map/build_regions.py` (o único script que
constrói a região "Ruínas", já que ela é "nova" e não vem de `build_valley.py`), **nenhuma
ocorrência** aparece — só o Mestre de Tarefas Dokan é adicionado à lista `npcs` retornada por
`build_ruins()` (linha 758). Confirmado no artefato final: `grep -o 'name="[^"]*"'
server/generated/world/valley-spawn.xml` **não lista `Tsubaki` nem `Ancião Kaito` em lugar
nenhum** — só `Mestre de Tarefas Dokan` está lá. Na prática, hoje: (a) não existe loja nas Ruínas
(Tsubaki nunca existe), e (b) **nenhuma das 7 missões do arco pode ser aceita** — um jogador pode
entrar na região, matar os monstros e até o boss (eles estão todos spawnados), mas sem o NPC que
dá a missão, não há como "aceitar" nada, o que nesta arquitetura de quest (storage por NPC,
`tools/export_tfs.py`) normalmente significa que as mortes **não contam para nenhum objetivo**,
nenhuma recompensa é entregue, a conquista `chain_ruinas_do_cla_marionetista` nunca fecha, e —
mais grave — **a metade "Ruínas" do Exame Jonin (`grants_rank_progress: "jonin"` de
`q_ruins_boss`) nunca é concedida**, o que бloqueia a promoção a Jonin do jogo inteiro hoje, já
que o Exame Jonin exige as duas metades (Costa **e** Ruínas, sem ordem entre si —
`docs/lore/progressao.md`) e uma das duas é inacessível.
- **`data/npcs/ruins.json` tem uma nota interna que já sinalizava isso e ficou sem seguimento**:
  o campo `_note` do NPC (`"PENDENTE de posição real"`, ver texto idêntico em
  `data/npcs/akatsuki_lair.json` para Suzu/Enji — mas aqueles **foram** resolvidos em
  `build_regions.py:1099-1100`; os das Ruínas e da Montanha, não).
- **Sem gancho de saída** (mesmo padrão de todos os arcos anteriores) — mas dado o Achado acima,
  é a menor das preocupações deste arco.
- **O fio da Nuvem Vermelha aparece por tabela, não por diálogo direto**: o Desertor de Elite é
  descrito na bíblia como "a caminho de recrutar para a organização maior", e o texto da própria
  quest (`q_ruins_deserter`) já diz "recrutando para a Toca do Som" — mas nunca nomeia "Nuvem
  Vermelha"/"Akatsuki" explicitamente, então o jogador não conecta os pontos sem ler os documentos
  de lore.
- **ADR-002 (ver Bestiário, seção 6 da bíblia):** `elite_deserter` usa looktype 915 ("Sasuke
  Akatsuki", MUGEN) — nome próprio de personagem real do anime reaproveitado como sprite, violação
  documentada e já sinalizada pela própria bíblia como pendência de arte, não desta auditoria.

### O que falta para ficar completo como história

A história em si (7 missões, boss com 3 fases, quiz de lore, mini-boss antes do boss) já é uma das
cadeias mais completas do jogo **no papel** — o problema não é falta de conteúdo, é o conteúdo
nunca chegar ao jogador:

1. **Posicionar Ancião Kaito e Tsubaki (M, mapa).** Adicionar as duas entradas que faltam à lista
   `npcs` retornada por `build_ruins()` em `tools/map/build_regions.py`, no mesmo padrão do
   Mestre de Tarefas Dokan (perto do gate/entrada, ambos visíveis logo ao atravessar) —
   sem isso, nada mais neste arco importa.
2. **Gancho de saída (P)**, só depois do Achado acima resolvido: Ancião Kaito, ao conceder
   `grants_rank_progress: "jonin"`, poderia dizer *"Metade do caminho. Se o Espadachim da Névoa
   também caiu, a Montanha do Trovão está esperando por você."* — referencia explicitamente a
   outra metade do exame (Costa), reforçando que as duas quests não têm ordem entre si.

### Esforço e dependências

Esforço: **P** para o conserto crítico (é só adicionar 2 entradas de coordenada num script Python
já existente, mesmo padrão usado para o Mestre de Tarefas Dokan há poucas linhas de distância) —
mas é o **maior risco de bloqueio de progressão do jogo hoje** (sem ele, ninguém vira Jonin pelo
caminho da história). Sem dependência de sistema novo.

## Arco 5 — Montanha do Trovão (nível 50–80, Jonin)

### Fluxo atual real

1. Do topo das Ruínas (ou por trilha própria), o jogador sobe a Montanha do Trovão atrás de um
   gate de rank **Jonin** (`RANK_GATE_ACTIONID["jonin"] = 45003`, `tools/map/build_regions.py:999`
   — coerente com o conteúdo, nível 50-80, sem paradoxo).
2. **Ferreiro Genzo** (`merchant_mountain`) e **Mestra Yuki** (`quest_giver_mountain`) deveriam
   ficar na região — só o **Mestre de Tarefas Kaji** (`task_master_mountain`) tem posição real
   (`kaji_pos`, `build_regions.py:1028`, lista `npcs = [("Mestre de Tarefas Kaji", kaji_pos)]`).
   **Mesmo Achado do Arco 4, se repete idêntico aqui.**
3. Mestra Yuki dá 7 missões sequenciais (`data/npcs/mountain.json`): `q_mountain_eagles` (15×
   `thunder_eagle` L54) → `q_mountain_relics` (rank B, entregar 8 `thunder_feather`) →
   `q_mountain_oni` (10× `glacier_oni` L60) → `q_mountain_serpents` (10× `magma_serpent` L74) →
   `q_mountain_lore` (rank A, `keyword_quiz` de 3 perguntas) → `q_mountain_curse_partner` (matar
   `boss_curse_partner` L70, `grants_rank_progress: "anbu"`) → `q_mountain_boss` (matar
   `boss_ancestral_oni` L80, `grants_rank_progress: "anbu"`).
4. O quiz de `q_mountain_lore` é a **primeira vez no jogo em que a resposta certa nomeia a
   organização de verdade**: uma das 3 perguntas é *"Quem lançou essa dupla imortal contra vilas
   inteiras na guerra?"*, com keywords aceitas `"nuvem vermelha"`/`"organizacao"`/`"organização"`
   (`data/npcs/mountain.json`) — mas ver Lacunas, o jogo nunca ensinou essa resposta antes de
   perguntar.
5. Bosses com fases reais e as mais elaboradas do jogo em número de invocações:
   `boss_curse_partner` (75%/50%/25% HP, escala só de `attack_multiplier`, sem summons — a "metade
   que ainda parece gente" luta sozinha, coerente com a fantasia) e `boss_ancestral_oni` (70%
   invoca 3 `thunder_eagle`, 40% invoca 2 `glacier_oni`, 15% `attack_multiplier 1.7` + invoca 2
   `storm_monk` — 3 fases, cada uma puxando um monstro comum diferente da própria região, "a
   montanha inteira vem comigo").
6. Todos os 5 monstros comuns + os 2 bosses estão no spawn final (conferido em
   `valley-spawn.xml`) — de novo, o bestiário está completo, só o dador de missão não existe.

### Lacunas e incoerências

**Achado (crítico, idêntico ao do Arco 4): Mestra Yuki e Ferreiro Genzo nunca são colocados no
mapa.** Mesma checagem, mesmo resultado: nenhuma ocorrência de `"Mestra Yuki"`/`"Ferreiro Genzo"`
em `tools/map/build_regions.py`, e `server/generated/world/valley-spawn.xml` não lista nenhum dos
dois (só `Mestre de Tarefas Kaji`). Consequência em cascata, ainda mais grave que no Arco 4: com
`q_mountain_curse_partner` e `q_mountain_boss` inacessíveis (não há como aceitar a quest sem o NPC),
**nenhuma das duas metades "de campo" do Exame Anbu é concedida** — e como o Exame Anbu já depende
de o jogador ter virado Jonin primeiro (que por sua vez depende do Achado do Arco 4 estar
resolvido), esta região está **duplamente bloqueada** na cadeia de progressão de rank de hoje.
Mesmo um jogador GM/nível 80 que chegasse até os bosses por conta própria não teria como fechar
`chain_montanha_do_trovao` nem progredir o storage de rank.

- **O quiz pergunta uma resposta que o jogo nunca ensinou.** A pergunta sobre "quem lançou a dupla
  imortal" espera que o jogador já saiba responder "Nuvem Vermelha"/"organização" — mas até este
  ponto da jornada (mesmo assumindo os Achados dos Arcos 1-4 corrigidos), **nenhuma fala de NPC**
  nomeou essa organização explicitamente (só o texto de lore, que o jogador não lê). É a mesma
  lacuna transversal ("o fio da Nuvem Vermelha é invisível") batendo de frente com um mecanismo que
  exige que o jogador já conheça a resposta — o pior lugar possível para essa desconexão acontecer,
  porque aqui ela vira um obstáculo de gameplay (quiz que não dá pra responder sem sair do jogo e
  ler a wiki/lore), não só uma perda de imersão.
- **Sem gancho de saída** (mesmo padrão) — mas, de novo, secundário ao Achado crítico.
- **ADR-002:** `boss_ancestral_oni` usa looktype 913 ("Madara", MUGEN) — mesmo looktype é
  reaproveitado depois no `boss_crimson_ancestor` do Covil (ver Arco 6) — dois bosses diferentes
  com a cara idêntica, o que também é uma inconsistência visual (bíblia já sinaliza isso como
  pendência de arte, "prioridade máxima").

### O que falta para ficar completo como história

1. **Posicionar Mestra Yuki e Ferreiro Genzo (M, mapa).** Mesmo conserto do Arco 4, no
   `build_mountain()` de `tools/map/build_regions.py` — prioridade igual ou maior que o Arco 4,
   porque bloqueia 2 ranks em vez de 1.
2. **Dar ao jogador a resposta antes do quiz (P).** A própria Mestra Yuki, na *fala de introdução*
   (antes do quiz aceitar respostas), pode contar a história que a pergunta cobra — ex.: *"Vocês
   vão enfrentar uma dupla que a Nuvem Vermelha já usou contra vilas inteiras, há uma geração.
   Prove que prestou atenção."* — aí a pergunta testa se o jogador **leu o que ela acabou de
   dizer**, não conhecimento externo. Resolve o quiz e começa a puxar o fio da organização para
   dentro do jogo de verdade.
3. **Gancho de saída (P)**, ao conceder o 2º `grants_rank_progress: "anbu"`: *"Isso é só metade do
   que te espera no Covil da Nuvem Vermelha — e agora vocês já sabem o nome de quem enfrentam."*

### Esforço e dependências

Esforço: **P** para o conserto crítico do mapa (idêntico ao Arco 4). **P** para as 2 falas novas.
Nenhuma dependência de sistema novo — é o mesmo padrão de correção do Arco 4, só em outro arquivo.

## Arco 6 — Covil da Nuvem Vermelha (nível 80–100, Anbu→Kage)

### Fluxo atual real

1. Um teletransporte gated no topo da Montanha do Trovão (`COVIL_GATE_ACTIONID = 45004`,
   `tools/map/build_regions.py:765`, `link_mountain_to_lair`, linha 1237) leva a uma masmorra
   isolada (sem trilha a pé, só o portal). **Capitã Anbu Suzu** (`quest_giver_akatsuki_lair`) e
   **Fornecedor Enji** (`merchant_akatsuki_lair`) — diferente dos Arcos 4 e 5, **os dois estão
   presentes** no spawn final (`valley-spawn.xml` lista ambos), posicionados perto da entrada
   (`build_regions.py:1099-1100`).
2. Capitã Anbu Suzu dá 6 missões sequenciais, todas `kind: kill` (`data/npcs/akatsuki_lair.json`):
   `q_lair_intro` (rank S, 10× `white_clone` L82) → `q_lair_guards` (rank S, 8× `elite_cloud_guard`
   L88) → `q_lair_1_illusive_eye` (matar `boss_illusive_eye` L85, `grants_rank_progress: "anbu"`) →
   `q_lair_2_masked_puppeteer` (matar `boss_masked_puppeteer` L90, `grants_rank: "anbu"`) →
   `q_lair_3_rings_bearer` (matar `boss_rings_bearer` L95, `grants_rank_progress: "kage"`) →
   `q_lair_4_crimson_ancestor` (matar `boss_crimson_ancestor` L100, `grants_rank: "kage"`, o fim
   da progressão de rank do jogo hoje).
3. Todos os 3 monstros comuns + 4 bosses estão no spawn final (`white_clone` ×10, `elite_cloud_
   guard` ×6, e os 4 bosses ×1 cada — conferido em `valley-spawn.xml`).
4. Fases de boss (`data/monsters/akatsuki_lair.json`): `boss_illusive_eye` (2 fases, só
   `attack_multiplier`, sem summons), `boss_masked_puppeteer` (2 fases, idem, sem summons),
   `boss_rings_bearer` (3 fases, 60% invoca 2 `elite_cloud_guard`), `boss_crimson_ancestor` (3
   fases, só `attack_multiplier` escalando 1.3→1.7, sem summon nenhum).

### Lacunas e incoerências

- **O clímax do jogo é, mecanicamente, o menos elaborado dos 4 bosses do Covil — e um dos menos
  elaborados do jogo inteiro.** `boss_crimson_ancestor` (nível 100, "o fundador da própria ideia da
  organização", o boss final de toda a progressão) tem só escalada de `attack_multiplier` nas 3
  fases, sem summon, sem transformação de `looktype`, sem nenhum elemento visual/mecânico distinto
  — comparado a `boss_ancestral_oni` (Montanha, 3 tipos de summon diferentes um por fase),
  `boss_puppeteer` (Ruínas, summons escalando + boss secundário invocado) ou até
  `boss_white_serpent` (Floresta da Morte, transformação de `looktype` + 2 tipos de summon), o
  boss final é o mais raso. Para um encontro pensado como "clímax de progressão do jogo" (bíblia,
  §2), isso é uma lacuna de sensação de final, não um bug.
- **Descompasso temático em `boss_rings_bearer`.** A bíblia descreve esse boss como "o portador de
  olhos em anel que multiplica a própria vontade em vários corpos" (referência a multiplicar
  cópias de si mesmo) — mas a fase de 60% HP invoca 2 `elite_cloud_guard` (o mob comum genérico da
  região), não uma cópia/eco do próprio boss. Mecânica genérica onde a fantasia pedia algo
  específico (ex.: invocar 2 versões fracas de si mesmo, reaproveitando o próprio `looktype` do
  boss em HP reduzido).
- **É o único arco do jogo sem nenhuma variedade de objetivo** — as 6 missões são todas
  `kind: kill`; nenhum `collect_item`, nenhum `keyword_quiz` (todos os outros 5 arcos têm pelo
  menos uma missão de coleta, e a maioria também tem quiz). Para o arco final do jogo, é a cadeia
  narrativamente mais "plana" em termos de variedade mecânica de missão, mesmo com o melhor
  bestiário de fases.
- **Ordem de nível não é estritamente crescente**: `q_lair_guards` (matar `elite_cloud_guard`,
  L88) vem **antes** de `q_lair_1_illusive_eye` (boss, L85) na sequência obrigatória — um jogador
  precisa treinar contra mobs de nível mais alto (88) do que o primeiro boss (85) antes de
  enfrentá-lo. Inversão pequena, mas real (compare com o resto do jogo, onde a sequência de
  missão é sempre não-decrescente em nível).
- **Nenhuma missão pede explicitamente para "recrutar" ou revelar a motivação de cada guardião**
  além do que já está nas falas de fase — o jogador mata os 4 guardiões em sequência sem nenhum
  momento de diálogo entre eles que explique por que estão ali além do que a bíblia já documenta
  (a motivação de cada um é só um resumo de design, não texto in-game).

### O que falta para ficar completo como história

Este é o arco mais "fechado" tecnicamente (única região onde os dois NPCs-chave e todo o
bestiário já estão no mapa) — o trabalho aqui é de **polimento de clímax**, não de correção de
bug:

1. **Dar ao `boss_crimson_ancestor` pelo menos 1 summon ou transformação (M).** Ex.: na fase de
   25% HP, invocar 1 `elite_cloud_guard` **com o próprio `looktype` do boss reduzido** (mesmo
   truque que a Serpente Branca já usa) — ou, mais simples, uma fala + efeito visual (`fx_seal_glow`
   já existe no sistema de conquistas) marcando a transição para "modo final".
2. **Trocar o summon de `boss_rings_bearer` por uma cópia dele mesmo (P/M)**, reaproveitando o
   próprio monstro em HP reduzido em vez de `elite_cloud_guard` — reforça a fantasia de "multiplica
   a própria vontade" sem precisar de sprite novo (mesmo looktype, só um segundo spawn).
3. **1 quest de coleta ou quiz no meio da cadeia (P/M, opcional)** — ex. um `keyword_quiz` da
   própria Capitã Suzu perguntando sobre os 3 bosses já derrotados no jogo (Serpente Branca,
   Marionetista, Sócio Eterno/Oni Ancestral) antes de liberar o guardião final — fecharia o círculo
   narrativo citando os próprios arcos anteriores, e resolveria a "falta de variedade" apontada
   acima.

### Esforço e dependências

Esforço: **M** — mudanças de dados em `data/monsters/akatsuki_lair.json` (phases) e
`data/npcs/akatsuki_lair.json` (quiz novo), sem sistema novo. Nenhuma dependência de mapa/sprite
adicional (o `looktype` reduzido do próprio boss já existe).

---

## Sistemas necessários

### O que já existe (e as correções acima **não** precisam de sistema novo)

`tools/export_tfs.py` já suporta, hoje, 4 tipos de objetivo de quest (`objective.kind`), todos
gerados em `server/generated/lib/naruto_quests.lua` e com script NPC funcional
(`npc_files()`, linha 1525 em diante):

- **`kill`** (implícito quando só há campo `kill`) — a maioria das missões do jogo.
- **`collect_item`** (linha ~1823) — entrega de item(ns) ao NPC; já usado em 5 arcos (`q_forest_
  supplies`, `q_coastal_supplies`, `q_forest_death_collect`, `q_ruins_intro`, `q_mountain_relics`).
- **`keyword_quiz`** (linha ~1552 em diante) — prova por palavra-chave, N perguntas, aprovação por
  acertos mínimos; já usado em 3 arcos (Exame Chunin, Ruínas, Montanha), com tratamento robusto de
  estado por jogador (bug de `cid` instável já resolvido e documentado no próprio código).
- **`talk_to`** (linha ~1536) — completar por falar uma keyword com **qualquer** NPC do jogo, não
  só quem deu a missão; implementado mas **nenhuma quest usa isso ainda** (`TALK_TO_QUESTS` fica
  vazio hoje) — disponível para uma futura missão tipo "leve esta carta ao Ferreiro Genzo".

Isso **contradiz** `docs/lore/progressao.md` ("Pendências técnicas"), que lista `keyword_quiz`,
confirmação de rank centralizada e bônus de status como não implementados — todos os três **já
estão implementados** (`naruto_ranks.lua` tem storage de rank real, `NarutoRanks.promote`/
`applyBonus`, chamado a partir de `naruto_quests.lua:78` sempre que uma quest com `grantsRank`/
`grantsRankProgress` completa). Esse documento de lore está desatualizado e deveria ser corrigido
(fora do escopo desta auditoria editar `docs/`; sinalizo aqui como achado, igual à seção 13 da
bíblia já faz para outros documentos). Boss-com-ajudante-por-fase (Achado usado em várias
propostas acima) também **já existe** como sistema — `phases[].summons` em
`data/monsters/*.json` — não precisa de nada novo, só de dados (ex. o Sócio Eterno propositalmente
não invoca ninguém; dar-lhe 1 fase de summon seria só editar o JSON).

### O que falta de verdade

1. **Diálogo de epílogo condicionado por storage ("gancho de saída").** Todas as propostas de
   "gancho de saída" desta auditoria (1 por arco) pedem que o NPC diga uma fala diferente **depois**
   de a última quest da cadeia estar `DONE`. Hoje `npc_files()` monta a saudação (`MESSAGE_GREET`)
   de forma estática por tipo de NPC (`shop` sempre a mesma frase; `quest` não foi auditado a fundo
   nesta missão, mas nenhuma quest do jogo hoje declara um campo de "texto pós-conclusão" em
   `data/npcs/*.json`). **Recomendação de implementação**: um campo novo opcional na última quest
   de cada cadeia (`data/schemas/quest.schema.json` já existe como alvo formal, mas
   `validate_data.py` ainda não valida `npcs/*.json` contra ele — ver bíblia §13): `epilogue_text`
   (string). Em `tools/export_tfs.py::npc_files()`, ao montar `MESSAGE_GREET` do NPC tipo `quest`,
   checar `player:getStorageValue(lastQuest.storage) == NarutoQuests.DONE` e, se verdadeiro, usar
   `epilogue_text` em vez da saudação padrão. Esforço: **P/M**, self-contido, não precisa de mapa
   novo.
2. **Validação cruzada quest↔spawn e npc↔mapa em `tools/validate_data.py`.** Os 3 bugs mais graves
   desta auditoria (Serpente Menor sem spawn, Aprendiz Mascarado sem spawn, os 4 NPCs de Ruínas/
   Montanha nunca posicionados) são todos do mesmo tipo: **um id referenciado em `data/*.json`
   nunca chega ao artefato final** (`server/generated/world/valley-spawn.xml`). Nenhum desses 3
   quebra o `python3 tools/validate_data.py` hoje (o script valida schema, não presença física no
   mundo) nem o smoke test (que não entra no mapa novo). Recomendação: um passo de validação novo
   (rodado depois de `tools/map/build_valley.py`/`build_regions.py`, antes de considerar o mapa
   "pronto") que: (a) para cada `monster_id` referenciado em `objective.kill` de qualquer quest/
   task, confirme `count(name in valley-spawn.xml) > 0`; (b) para cada `id` de NPC em
   `data/npcs/*.json` com `quests` não-vazio, confirme o mesmo. Esforço: **M**, é um script Python
   novo e pequeno (não altera `tools/export_tfs.py` nem os builders), mas depende de rodar contra o
   artefato final gerado (`server/generated/world/valley-spawn.xml`), então precisa ser chamado
   depois do build de mapa no fluxo de CI/checklist do projeto.
3. **Escolta (`objective.kind: 'escort'`), sistema novo, não crítico.** Nenhuma quest do jogo hoje
   implementa proteção real de um NPC em trânsito — o padrão usado (Costa das Marés, "proteja quem
   trabalha na ponte") é sempre "mate N mercenários numa área", não uma escolta de verdade (NPC
   anda por um caminho, jogador defende). Isso é fiel ao pedido da missão original só parcialmente
   — funciona bem para "proteger a ponte" mas não permitiria, por exemplo, uma missão futura tipo
   "escolte o Ancião Tazu até o meio da ponte inacabada". **Não recomendo para nenhuma correção
   listada nesta auditoria** (todos os problemas encontrados são resolvíveis sem esse sistema) —
   deixo registrado como sistema em aberto para uma futura missão de conteúdo, não como bloqueio.
   Esforço estimado se decidido: **G** (precisa de movimentação de NPC por waypoints + objetivo
   novo em `export_tfs.py` + checagem de "NPC sobreviveu até o fim" — bem mais caro que os itens 1
   e 2 acima).

---

## Plano de execução em 3 lotes paralelos

Critério de corte: **nenhum dos 3 lotes edita o mesmo arquivo de dados que outro**, com uma única
exceção documentada abaixo (`data/npcs/leaf.json`, compartilhado entre Lote A e Lote B porque o
arquivo físico mistura NPCs de duas regiões narrativas diferentes — Capitã Rin, da Floresta da
Vila, e Velha Sumi/Rastreador Goro/Instrutora Ibuki, da Floresta da Morte). Os nomes de arquivo
abaixo são os **reais** do repositório (o pedido original citava `death_forest.json`/`lair.json`,
que não existem — a Floresta da Morte mora dentro de `leaf.json`, o Covil é `akatsuki_lair.json`).

### Exceção de arquivo compartilhado: `data/npcs/leaf.json`

Lote A só toca o objeto do NPC `quest_giver_leaf` (Capitã Rin) nesse arquivo; Lote B só toca
`merchant_swamp`/`quest_giver_swamp`/`exam_proctor_forest` (Velha Sumi/Rastreador Goro/Instrutora
Ibuki). São objetos diferentes do mesmo array JSON — sem conflito de **lógica**, mas ainda existe
risco de conflito de **merge de arquivo** se os dois lotes editarem em paralelo sem coordenação.
Recomendação: Lote A aplica suas 2 mudanças primeiro (são só adições no fim do array de quests da
Rin, baixo risco), Lote B faz rebase por cima antes de aplicar as suas.

---

### Lote A — Academia / Floresta da Vila + Costa das Marés

**Arquivos:** `data/npcs/leaf.json` (só `quest_giver_leaf`), `data/npcs/coastal_tides.json`,
`data/monsters/forest.json`, `data/monsters/coastal_tides.json`,
`tools/map/build_regions.py` (só a função `build_coastal_tides` e a chamada `place_rank_gate`
dentro dela).

| # | Ação | Arquivo | Item afetado | Objetivo/mudança | Pré-requisito | Critério de aceite |
|---|---|---|---|---|---|---|
| A1 | **Crítico** — remover/rebaixar o gate de rank da Costa | `tools/map/build_regions.py:452-455` | `place_rank_gate(..., "chunin", ...)` | Trocar para sem gate (igual à Floresta da Morte) ou `"genin"` | nenhum | Um personagem Genin nível 12 (sem rank Chunin) consegue atravessar o marcador de entrada da Costa das Marés sem ser barrado/teleportado de volta |
| A2 | **Alto** — dar spawn solto ao Aprendiz Mascarado | `tools/map/build_regions.py` (`build_coastal_tides`, bloco de spawns) | `masked_apprentice` | Adicionar grupo de spawn próprio, 2-3 unidades, nível 17, entre `mist_guardian` e a arena do boss | A1 (senão ninguém no nível certo consegue caçar lá) | `grep -o 'name="Aprendiz Mascarado"' valley-spawn.xml` retorna ≥2; matar 6 conta para `q_coastal_apprentice` sem depender do boss |
| A3 | Semente da Nuvem Vermelha | `data/monsters/forest.json` | `boss_bandit_chief.phases[0]` (50% HP) | Trocar/complementar `message` para citar "nuvem vermelha" de forma sutil | nenhum | Fala aparece no chat de combate ao boss cruzar 50% HP (checar em log de combate/playtest) |
| A4 | Gancho de saída — Floresta da Vila | `data/npcs/leaf.json` (`quest_giver_leaf`) | nova entrada de diálogo/quest final | Ver texto proposto no Arco 1 (aponta Costa + Floresta da Morte) | nenhum | Falar com Capitã Rin depois de `q_bandit_chief` concluída mostra a nova fala |
| A5 | (Opcional) Missão do Cervo | `data/npcs/leaf.json` (`quest_giver_leaf`) | `q_forest_deer_1` | `collect_item`: 3 `onigiri` | nenhum | Missão aceitável, completável, entrega recompensa |
| A6 | Gancho de saída — Costa | `data/npcs/coastal_tides.json` (`quest_giver_coastal`) | fala pós-`q_coastal_swordsman` | Ver texto proposto no Arco 2 (aponta Floresta da Morte) | A1, A2 | Falar com Ancião Tazu depois do Espadachim morto mostra a nova fala |

**Falas-chave propostas (pt-BR, tom da bíblia):**
- Capitã Rin (A4): *"Bom trabalho, Genin. Mas isso foi só a estrada perto de casa — a Floresta da
  Morte separa quem está pronto do resto do mundo, e ouvi dizer que mercadores da Costa das Marés
  estão contratando gente como você."*
- Chefe dos Bandidos (A3, 50% HP): *"Não fui eu quem escolheu essa 'nuvem vermelha' nos vigiando,
  moleque — fui só pago."*
- Ancião Tazu (A6): *"Vocês salvaram esta ponte. Mas ouvi um batedor comentar, antes de cair,
  sobre uma floresta que mata os fracos rio acima — cuidado."*

---

### Lote B — Floresta da Morte / Exame Chunin + Ruínas do Clã Marionetista

**Arquivos:** `data/npcs/leaf.json` (só `merchant_swamp`/`quest_giver_swamp`/`exam_proctor_forest`),
`data/npcs/ruins.json`, `data/monsters/swamp.json`, `data/monsters/ruins.json`,
`tools/map/build_valley.py` (só `DEATH_SETS`/`DEATH_CLEARINGS`), `tools/map/build_regions.py`
(só a função `build_ruins`, lista `npcs` de retorno).

| # | Ação | Arquivo | Item afetado | Objetivo/mudança | Pré-requisito | Critério de aceite |
|---|---|---|---|---|---|---|
| B1 | **Crítico** — posicionar Ancião Kaito e Tsubaki | `tools/map/build_regions.py` (`build_ruins`, lista `npcs`) | NPCs `quest_giver_ruins`/`merchant_ruins` | Adicionar as 2 entradas que faltam à lista `npcs` retornada, perto do gate/entrada (mesmo padrão do Mestre de Tarefas Dokan) | nenhum | `grep -o 'name="Ancião Kaito"' valley-spawn.xml` e `name="Tsubaki, a Escavadora"` retornam 1 cada; falar com Kaito abre o menu de missão |
| B2 | **Crítico** — portar spawn da Serpente Menor | `tools/map/build_valley.py` (`DEATH_SETS`/`DEATH_CLEARINGS`) | `lesser_serpent` | Portar os 3 pontos já desenhados em `data/maps/forest_valley.json` (x=74,y=18 / x=82,y=8 / x=86,y=34, coords locais da zona) | nenhum | `grep -o 'name="Serpente Menor"' valley-spawn.xml` retorna ≥3; matar conta para `q_lesser_serpents` sem depender do boss |
| B3 | Remover redundância de boss (Goro × Ibuki) | `data/npcs/leaf.json` (`quest_giver_swamp`) | `q_elder_toad_hunt`, `q_white_serpent` | Trocar `objective.kind` de `kill` duplicado para checagem de `quest_chain_complete` da respectiva etapa do exame (`exam_chunin_2a`/`2b`) | B2 não depende, mas ideal aplicar junto | Completar a etapa do exame também completa a quest da Goro, sem exigir 2ª morte do mesmo boss |
| B4 | Gancho de saída — Exame Chunin | `data/npcs/leaf.json` (`exam_proctor_forest`) | fala em `exam_chunin_3c_rival_mist` (pós-`grants_rank`) | Ver texto proposto no Arco 3 | nenhum | Falar com Ibuki depois do torneio mostra a nova fala |
| B5 | Gancho de saída — Ruínas | `data/npcs/ruins.json` (`quest_giver_ruins`) | fala em `q_ruins_boss` (pós-`grants_rank_progress`) | Ver texto proposto no Arco 4 | B1 | Falar com Kaito depois do Marionetista morto mostra a nova fala |

**Falas-chave propostas:**
- Instrutora Ibuki (B4): *"Chunin. Agora sim pode seguir — a Costa das Marés precisa de gente como
  você, e as Ruínas do Clã Marionetista não vão esperar."*
- Ancião Kaito (B5): *"Metade do caminho. Se o Espadachim da Névoa também caiu, a Montanha do
  Trovão está esperando por você."*

---

### Lote C — Montanha do Trovão + Covil da Nuvem Vermelha

**Arquivos:** `data/npcs/mountain.json`, `data/npcs/akatsuki_lair.json`,
`data/monsters/mountain.json`, `data/monsters/akatsuki_lair.json`, `tools/map/build_regions.py`
(só a função `build_mountain`, lista `npcs` de retorno).

| # | Ação | Arquivo | Item afetado | Objetivo/mudança | Pré-requisito | Critério de aceite |
|---|---|---|---|---|---|---|
| C1 | **Crítico** — posicionar Mestra Yuki e Ferreiro Genzo | `tools/map/build_regions.py` (`build_mountain`, lista `npcs`) | NPCs `quest_giver_mountain`/`merchant_mountain` | Adicionar as 2 entradas que faltam (mesmo padrão do Mestre de Tarefas Kaji) | nenhum | `grep -o 'name="Mestra Yuki"' valley-spawn.xml` e `name="Ferreiro Genzo"` retornam 1 cada; falar com Yuki abre o menu de missão |
| C2 | Ensinar a resposta antes do quiz | `data/npcs/mountain.json` (`quest_giver_mountain`) | texto de introdução de `q_mountain_lore` | Adicionar a informação que a pergunta cobra antes de abrir o quiz | C1 | Um jogador que nunca leu a lore consegue responder certo só com o que Yuki acabou de dizer |
| C3 | Gancho de saída — Montanha | `data/npcs/mountain.json` (`quest_giver_mountain`) | fala em `q_mountain_boss` (pós-`grants_rank_progress`) | Ver texto proposto no Arco 5 | C1 | Falar com Yuki depois do Oni Ancestral morto mostra a nova fala |
| C4 | Dar mecânica de summon ao boss final | `data/monsters/akatsuki_lair.json` | `boss_crimson_ancestor.phases` | Adicionar summon/transformação na fase de 25% HP (ex.: `elite_cloud_guard` com o próprio `looktype` reduzido) | nenhum | Fase de 25% HP invoca reforço visível em combate |
| C5 | Trocar summon genérico por cópia do próprio boss | `data/monsters/akatsuki_lair.json` | `boss_rings_bearer.phases[1]` (60% HP) | Trocar `elite_cloud_guard` por um summon com o `looktype` do próprio boss (HP reduzido) | nenhum | Fase de 60% HP invoca uma versão visualmente idêntica ao boss |
| C6 | (Opcional) Quiz de fechamento do Covil | `data/npcs/akatsuki_lair.json` (`quest_giver_akatsuki_lair`) | nova quest `keyword_quiz` antes de `q_lair_3_rings_bearer` | 3 perguntas citando Serpente Branca/Marionetista/Sócio Eterno-Oni Ancestral | nenhum | Quiz aceitável e completável, referencia os 3 bosses anteriores |

**Falas-chave propostas:**
- Mestra Yuki (C2, antes do quiz): *"Vocês vão enfrentar uma dupla que a Nuvem Vermelha já usou
  contra vilas inteiras, há uma geração. Prove que prestou atenção."*
- Mestra Yuki (C3): *"Isso é só metade do que te espera no Covil da Nuvem Vermelha — e agora vocês
  já sabem o nome de quem enfrentam."*

---

### Ordem recomendada entre lotes

Os 3 lotes são **independentes entre si** (arquivos diferentes, exceto a exceção documentada de
`leaf.json` entre A e B) e podem rodar em paralelo. Dentro de cada lote, os itens marcados
**Crítico** (A1, A2, B1, B2, C1) devem ser feitos **antes** dos ganchos de saída/falas daquele
mesmo lote, porque várias falas propostas pressupõem que o jogador consiga de fato chegar à quest
(sem sentido revisar o diálogo de saída de uma quest inacessível).

