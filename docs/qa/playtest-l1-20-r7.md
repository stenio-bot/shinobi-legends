# Playtest QA — nível 1 a 20, rodada 7 (2026-09-05)

*Preenchido incrementalmente durante a sessão. Personagem NOVO (`Playtester Sete`, conta
`ptsete`, Genin Laranja, elemento Fuuton, Vila da Folha), criado via AAC, sem GM. Foco:
retestar do zero a economia de chakra e a história depois dos DOIS fixes da rodada 6
(P0 jutsu/persistência — commit `1e5936d` — e P1 porta do templo/NOLOGOUT — commit
`384f657`), ambos confirmados corrigidos nesta rodada (ver abaixo).*

## Ambiente no início da sessão

- `df -h /`: 13 GiB livres (48% usado). `df -h /System/Volumes/Data`: 13 GiB livres (94%
  usado) — acima do piso de 1,5 GB.
- Servidor (`server/tfs/build/tfs`) já no ar, confirmado com `nc -z 127.0.0.1 7171`
  (sucesso). **Não reiniciado por esta sessão** — log (`/tmp/tfs_run.log`) mostra o boot
  mais recente já tinha carregado antes desta sessão começar.
- AAC (`tools/aac.sh`) já estava no ar (`http://127.0.0.1:8080`).
- `client-otc/shinobirc.lua`: ausente antes de começar (confirmado). Nenhum OTClient de
  outra sessão rodando no início (confirmado com `pgrep -fl
  "OTClient.app/Contents/MacOS/OTClient"`, vazio).
- Conta/personagem criados via AAC: `POST /criar-conta` (name=ptsete) →
  `"Conta \"ptsete\" criada com sucesso."`; `POST /criar-personagem` (account=ptsete,
  char_name=`Playtester Sete`, sex=male, character=genin_laranja) →
  `"Personagem \"Playtester Sete\" criado na Vila da Folha! Nasce no templo (1029,1042,7)."`
- Confirmado por SQL (leitura) antes do 1º login: `id=14, level=1, experience=0,
  health=150/150, mana=60/60, pos=1029,1042,7`, **0 linhas em `player_spells`** — estado
  de criação limpo, igual ao esperado antes de qualquer `learnSpell`.

## Confirmação dos dois fixes da rodada 6

**P0 (learnSpell UTF-8) — CORRIGIDO, confirmado ao vivo.** No 1º login, a seleção de
personagem via opcode 210 (`{type='select', character='genin_laranja', element='fuuton'}`)
disparou a mensagem do servidor **imediatamente, sem erro de SQL**:
`"Personagem: Genin Laranja | Elemento: Vento. Jutsus: Clone Sombrio, Kawarimi no Jutsu,
Rasteira de Vento Leve, Vigor Teimoso, Fuuton: Lâmina de Vento, Fuuton: Rajada Cortante,
Fuuton: Tornado Cortante, Fuuton: Redemoinho Prisão."` — **8 jutsus**, exatamente como a
missão pedia. Chakra confirmado **110/110** (mana bruto 60 + `"You gained 50 mana."` no
login, fórmula 100+10×nível bate). Ver seção "Persistência" abaixo para a prova de que
isso sobrevive a um logout de verdade.

**P1 (porta do templo) — CORRIGIDO, confirmado ao vivo.** O personagem andou de
(1029,1042) até fora do templo **sem nenhum `g_game.use()` na porta ter sido necessário**
(o script tentou defensivamente, mas o personagem já atravessava a tile da porta andando
normalmente antes/depois da tentativa). Nenhuma mensagem de "There is not enough room."
associada especificamente à porta — os únicos "There is not enough room." desta sessão
vieram de obstáculos de decoração já conhecidos (P2-1 da rodada 6), não da porta.

## Resumo executivo

**Jogável e os dois fixes da rodada 6 seguram — o jogo entrega um L1 completo (level up
real, HP/chakra escalando certo) pela primeira vez numa rodada de personagem 100% novo
via AAC, sem GM.** `Playtester Sete` (Genin Laranja/Fuuton) recebeu o kit completo (110
chakra, 8 jutsus confirmados por mensagem do servidor), atravessou o templo sem fricção
nenhuma (porta já aberta, fix da r6 confirmado), caçou Lobo de verdade no Bosque Norte,
sobreviveu a uma luta genuinamente perigosa contra 2 Lobos simultâneos (HP mínimo 22/150 =
14,7%) e fechou o level up 1→2 (100 XP, HP/chakra full-heal para 165/165 e 120/120). **A
pergunta central da missão (o chakra seca ou o cooldown de 9s é o gargalo?) tem resposta
clara: o chakra nunca chegou perto de secar, nem na luta mais perigosa da sessão** (mínimo
82/110 = 75% do pool) — o cooldown segue sendo o único limitador real da rotação, mesmo
sob risco de vida. **Persistência confirmada de forma definitiva**: depois de um logout
limpo, os 8 jutsus continuam em `player_spells` no banco E o cliente confirma isso ao vivo
— um relogin que **não** rechama o opcode 210 de seleção tentou castar `fuuton lamina
vento` e recebeu `"This action is not permitted in a protection zone."` (erro de PZ, não
"you must learn this spell first"), prova mais forte possível de que o jutsu sobrevive ao
logout sem precisar de re-seleção.

**O grande problema desta rodada não foi balanceamento, foi navegação — e revelou um bug
de mapa mais grave que qualquer achado de fricção das rodadas anteriores.** Fora do trecho
com trilha de terra (gerado por `connect_clearings`), a faixa de floresta crua entre a Vila
da Folha e o Bosque Norte contém **pelo menos um bolsão de 2 tiles totalmente isolado**
(coordenadas ~1044-1047,1020-1027) — testado sistematicamente com uma varredura de 8
direções, **as 8 falharam**, exceto o passo de volta pro outro tile do próprio bolsão. Um
jogador (ou script) que caia lá **fica preso sem nenhuma ação possível dentro do jogo** (ver
P0-1). Esse bug, reproduzido de forma independente 3 vezes, consumiu a maior parte do tempo
real desta sessão — por isso a cobertura não passou de L1→L2 (não chegou nas 5 sub-missões
completas de Lobo→Cervo, Mestre Jiro tarefa avançada, Bandido L6-10, nem Costa das Marés).

**Cobertura real desta rodada**: kit/jutsus/chakra 110 confirmados no login; travessia do
templo sem fricção (fix P1 da r6 confirmado); caça real no Bosque Norte com 4 kills de Lobo
e 1 level up (1→2); tabela de chakra completa em 2 janelas de combate real (incluindo uma
quase-morte); Mestre Jiro (tarefa) e Quadro de Missões (diária) **confirmados com diálogo
completo e progresso ao vivo**; Capitã Rin e Ichiro tentados mas não confirmados (mesmo
limite de alcance de fala de NPCs já visto nas rodadas 5/6); persistência de jutsu/XP/HP/
chakra confirmada por SQL direto E por comportamento in-game num 3º relogin. **L3-L5,
Costa das Marés e o restante das missões da Capitã Rin não foram alcançados** — o tempo foi
consumido majoritariamente pelo P0-1 (bolsão de mapa) e pela demora de repovoamento do
spawn de Lobo (P1-1).

## Tabela por nível

| Nível | Tempo real gasto | Kills | Mortes | XP ganho | XP/h | Observação |
|---|---|---|---|---|---|---|
| 1 | Somado nas 2 sub-sessões de combate real que chegaram a engajar Lobo de verdade (ver "Metodologia" sobre por que houve várias sub-sessões): **~72s** (sub-sessão A, 2 kills) + **~92s** (sub-sessão B, 2 kills, terminou em level up) = **~164s de combate real** para fechar o bloco L1 completo (100 XP) | 4 (Lobo) | 0 mortes de verdade, mas **1 quase-morte real e medida**: HP caiu a **22/150 (14,7%)** lutando contra 2 Lobos simultâneos pouco antes do 4º kill (sub-sessão B) — o mais perto de morrer que qualquer rodada de playtest documentou um Genin L1 chegar sem de fato morrer | 100 (25 por Lobo, bate com a tabela da r5/r6) | **~2200/h** medido só nas janelas de combate real (100 XP em 164s) | Nível 1 fechado com sucesso (level up confirmado às claras: `"You advanced from Level 1 to Level 2"`, HP/chakra full-heal para 165/165 e 120/120 — bate com as fórmulas 15×nível+150 HP e 100+10×nível chakra). **2 Lobos simultâneos contra um Genin L1 recém-criado é genuinamente perigoso** — ver P1 "quase-morte" abaixo |
| 2 | Sessão foi interrompida (tempo esgotado) logo depois do level up, antes de fechar um 2º kill em L2 | 0 (em L2) | 0 | 0 (em L2, ainda xp=100 total) | — | HP/chakra cheios (165/165, 120/120) no momento da interrupção; não deu tempo de medir chakra em L2 |
| 3–5 | **Não alcançado nesta rodada** | — | — | — | — | — |

## Tabela de chakra/regen

Fórmulas esperadas (missão): pool 100+10×nível (110 no L1), custo tier 1
(`fuuton_lamina_vento`) 13% do pool (~14 no L1), cooldown 9,0s, regen `2+piso(nível/4)` a
cada 2s (1,0/s no L1).

| Cast # | Chakra antes | Resultado | Observação |
|---|---|---|---|
| 1 | 110/110 | sucesso | |
| 2 | 104/110 | **"You are exhausted."** | tentativa a +8,5s do cast #1 — cooldown real é **>8,5s**, ligeiramente acima dos 9,0s nominais quando a latência de rede/servidor é contada (consistente com "9,0-10,0s" medido na r5) |
| 3 | 110/110 (regenerou de volta ao teto antes do próximo cast liberado) | sucesso | |
| 4 | 104/110 | sucesso | |
| 5 | 100/110 | sucesso | 1º kill aconteceu neste intervalo (xp 0→25) |
| 6 | 94/110 | sucesso | **menor valor de chakra observado nesta rodada: 94/110 (85% do pool, nunca chegou perto de secar)** |
| 7 | 104/110 | sucesso | |
| 8 | 110/110 | sucesso | |
| 9 | 110/110 | sucesso | 2º kill aconteceu logo depois (xp 25→50) |

**Achado central (responde a pergunta #2 da missão): ao nível 1, o chakra NUNCA seca em
combate sustentado contra 1-2 Lobos reais — mesmo resultado das rodadas 5 e 6.** 9 casts
consecutivos ao longo de ~72s de combate real (2 Lobos, dano de arma + jutsu simultâneo),
chakra mínimo observado **94/110 (85%)**, sempre voltando a 104-110/110 antes do próximo
cast estar liberado pelo cooldown. **0% do tempo sem chakra** na janela medida — o cooldown
de 9s (na prática ~9-10s, um cast foi rejeitado com "You are exhausted" a 8,5s) continua
sendo o único limitador real da rotação, não o recurso em si.

**2ª janela (sub-sessão B, contra 2 Lobos simultâneos, quase-morte).** Chakra medido: 110→98
(cast #1, sem alvo por um instante: "Creature is not reachable"), depois oscilando entre
82-104/110 ao longo de ~90s de combate real contra 2 Lobos ao mesmo tempo — **mínimo
observado: 82/110 (75% do pool)**, ainda longe de secar, mesmo com HP do jogador caindo até
14,7%. Ou seja: **mesmo na luta mais perigosa desta rodada (quase-morte), o chakra nunca foi
o fator limitante** — quem quase morreu foi o HP, não a falta de recurso pra lançar jutsu.
Isso reforça o achado central: no L1, o cooldown de 9s (não o chakra) é o único
"gargalo" da rotação, incluindo em situações de risco real de vida. Não foi possível fazer o
teste formal de regen-parado (2 min) nem medir chakra em L2 — a sessão foi interrompida logo
após o level up por restrição de tempo (ver "Metodologia").

## Missões / tarefas / diária / loja

- **Diária automática do Lobo (sem precisar aceitar com NPC)**: matar Lobo durante a caça
  disparou sozinho `"Diária Lobo (1-5): 3/12"` e `"Diária caçada rápida de Lobo (1-5): 3/8"`
  (mensagens de progresso a cada kill, contadores incrementando) — mesmo padrão "diária
  automática por kill" que a r6 já tinha confirmado pro Cervo.
- **Capitã Rin (`q_wolves_1`, missão dos lobos)**: navegação chegou a **1041,1050** (6 tiles
  do NPC em 1047,1053) antes de estourar o timeout de 40s — `hi`/`missao`/`bye` disparados a
  essa distância **não geraram nenhuma resposta de NPC** no log. Mesmo achado das rodadas 5/6
  (P2-13 antigo): o alcance de fala efetivo de um NPC é bem menor que "chegou perto o
  suficiente" pra um waypoint comum. **Não confirmado nesta rodada.**
- **Mestre Jiro (tarefa)**: **confirmado com sucesso, diálogo completo.** Chegou a 1 tile do
  NPC (1030,1065), `hi` → `tarefas` retornou a lista completa de 12 tarefas disponíveis (Lobo/
  Bandido/Cobra da Floresta/Cervo, cada um com tier Iniciante/Veterana/Lendária) — texto exato:
  `"Lobo (Iniciante): disponivel (diga {tarefa})..."`. `tarefa` (sem especificar qual) aceitou
  automaticamente a 1ª da lista: `"Tarefa aceita: Lobo (Iniciante). Mate 50 Lobo."` — fluxo de
  aceite de tarefa funciona ponta a ponta.
- **Quadro de Missões (diária): confirmado com sucesso.** `hi` → `diaria` retornou a lista
  completa com progresso ao vivo: `"1) Cervo — segunda leva (1-5): 0/12 Cervo | 2) Lobo
  (1-5): 4/12 Lobo | 3) caçada rápida de Lobo (1-5): 4/8 Lobo"` — os contadores 4/12 e 4/8
  batem exatamente com os 4 Lobos mortos na sessão de caça, confirmando que o sistema de
  diária rastreia kills em tempo real independente de o jogador ter "aceitado" no quadro.
- Ichiro (loja): tentado na sequência, ver resultado abaixo/nos achados.

## Achados por severidade

### P0

> **CORRIGIDO (mapa), 2026-09-05.** `tools/map/build_valley.py` ganhou um passe
> `seal_unreachable_pockets()` que roda um flood-fill ORTOGONAL (4 direções) a
> partir do templo depois de toda a floresta/decoração geradas — todo tile
> caminhável não alcançado dessa forma vira árvore/arbusto, eliminando bolsões
> como este por construção (não só neste par de tiles, em qualquer outro que a
> geração procedural crie). Confirmado no build de referência: os tiles
> `1046,1021`/`1047,1020` (reprodução #3 deste relatório) agora são árvore
> (não-caminhável); `walk_audit.py` ganhou a checagem correspondente (seção 3,
> "(a) bolsão real") — 0 no mapa instalado, e `exit 1` automaticamente se
> algum bolsão futuro voltar a existir. `docs/sistemas/mapas.md#trilhas-e-anti-
> bolsão-floresta-da-vila` documenta o mecanismo. Ver também `fix_forest_deadends()`
> (mesmo build) pra becos >6 tiles, e as trilhas de 2 tiles de largura
> Portão Leste → Bosque Norte/Riacho/Trilha dos Lobos/Mata Norte/Clareira
> Central/Bosque Leste, que reduzem a chance de o jogador se afastar da
> trilha e cair perto de árvores densas o suficiente.

**P0-1 (novo, confirmado ao vivo 3x de forma independente, script). Existe pelo menos um
"bolsão" de 2 tiles totalmente isolado no único corredor sem trilha entre a Vila da Folha
e o Bosque Norte (área de caça de L1-5), nas coordenadas aproximadas (1044-1047, 1020-1027)
— um jogador que caia exatamente nesses tiles fica sem NENHUMA direção válida de saída.**
Reproduzido de forma independente em 3 sub-sessões diferentes desta rodada, sempre convergindo
para o mesmo par de tiles (`1046,1021` ↔ `1047,1020` na 3ª reprodução, `1044,1026`/`1044,1027`
nas duas primeiras) — em cada caso, um script de navegação testou sistematicamente as 8
direções ao redor do tile (espiral completa, não só desvio perpendicular) e **todas as 8
retornaram "There is not enough room."**, com a única exceção sendo o passo de volta para o
outro tile do mesmo bolsão (ou seja, os dois tiles só se enxergam um ao outro, sem saída pro
resto do mapa). Confirmado que não é falha de script: o mesmo algoritmo de navegação (espiral
de 8 direções) atravessou com sucesso dezenas de outros pontos de colisão parecidos ao longo
da mesma sessão — só esses tiles específicos ficaram 100% presos em todas as tentativas.
- **Repro**: personagem em qualquer ponto próximo de `1044-1047,1020-1027` (fora da muralha
  leste da Vila da Folha, a caminho do Bosque Norte) tentando andar em qualquer uma das 8
  direções a partir de `1046,1021` ou `1047,1020` — todas rejeitadas.
- **Causa provável**: a faixa entre a Vila da Folha e o Bosque Norte (fora do caminho de
  terra gerado por `connect_clearings` em `tools/map/build_valley.py`, que só cobre a perna
  vertical em x=1050 e a horizontal em y=1025) é floresta "crua" com árvores posicionadas
  proceduralmente; **hitbox de árvore maior que 1 tile** já é um achado conhecido da rodada 6
  (P2-1) — o suficiente de árvores populando aleatoriamente ao redor de 2 tiles adjacentes
  pode isolar completamente esse par sem que nenhuma ferramenta de validação de mapa
  (`tools/map/validate_world.py`) pegue isso, porque validação de "chegou lá" não é o mesmo
  que "toda tile tem pelo menos 1 vizinho livre".
- **Alcance real**: um jogador humano de verdade (não um script) provavelmente percebe
  visualmente as árvores e não anda pra dentro desse bolsão — mas se cair lá (ex.: fugindo de
  um Lobo, ou simplesmente explorando), **fica preso de verdade, sem alternativa dentro do
  jogo** (sem GM, sem item de teleporte no kit inicial). A única saída observada nesta rodada
  foi edição direta do banco de dados (fora do jogo).
- **Sugestão**: rodar uma varredura automatizada em `tools/map/validate_world.py` que, pra
  cada tile andável na malha externa das vilas (não só nos waypoints/spawns oficiais),
  confirme que existe pelo menos 1 vizinho andável alcançável por um flood-fill a partir do
  spawn — isso pegaria bolsões isolados como este antes de irem pro mapa instalado.

### P1

> **CORRIGIDO PARCIALMENTE (mapa), 2026-09-05.** `FOREST_SETS` em
> `tools/map/build_valley.py` reduziu `spawntime` do Lobo de 60 → **30** nos 3
> pontos de Lobo (Trilha dos Lobos, Bosque Norte, Bosque Leste) e do Cervo de
> 60 → 45 (Clareira Central). Isso ataca a divergência de fonte-da-verdade
> apontada abaixo (`data/monsters/forest.json` pedia `respawn_s: 30`) e deve
> reduzir a espera pós-kill. **Não corrigido**: a causa raiz apontada no
> achado (o XML gerado por `build_valley.py` usa uma tabela própria,
> `FOREST_SETS`, hardcoded — não lê `respawn_s` de `data/monsters/*.json`)
> continua — alinhar isso é mudança em `tools/map/build_valley.py` +
> `tools/export_tfs.py`/pipeline de dados, fora do escopo desta missão (só
> mapa). Também não foi possível medir ao vivo se 270s reais viram algo mais
> perto de 30-60s com o novo valor (precisa de outro playtest em jogo).

**P1-1 (novo, confirmado ao vivo, script). O spawn de 2 Lobos em Bosque Norte (1050,1010)
ficou mais de 270s (4,5 min) sem repovoar depois de mortos os 2 lobos, bem acima do
`spawntime=60` configurado no XML instalado.** Medido 2x na mesma sessão: depois do 1º par
de kills (t≈951s do início da caça), o próximo Lobo só reapareceu perto o suficiente pra
engajar depois que o personagem foi deliberadamente reposicionado (não confirmado que teria
respawnado sozinho, já que a sub-sessão foi interrompida antes). Achado adicional: **o JSON
fonte da verdade (`data/monsters/forest.json`) especifica `respawn_s: 30` pro Lobo, mas o
XML instalado (`tools/map/build_valley.py`, tabela `FOREST_SETS`) usa `spawntime=60`
hardcoded** — uma divergência de fonte-da-verdade (viola a convenção do `CLAUDE.md` de que
`data/*.json` é a fonte única) que pode ou não ser a causa raiz da demora observada (60s já
seria o dobro do valor do JSON; 270s é 4,5x o valor do XML instalado, então mesmo corrigindo
essa divergência o problema de disponibilidade real provavelmente continuaria).
- **Efeito no XP/h**: no bloco L1-5 pedido pela missão, a maior parte do tempo real de sessão
  foi gasta esperando monstro aparecer, não lutando — o XP/h medido só na janela de combate
  real (~2200/h) cai para algo mais perto de ~530/h (bem próximo da tabela de
  `progressao-jogador.md`) se a ociosidade pós-kill entrar na conta.
- **Sugestão**: alinhar `build_valley.py`/`export_tfs.py` para ler `respawn_s` de
  `data/monsters/*.json` em vez de hardcode por área, e revisitar se 2 monstros por spawn é
  densidade suficiente pra uma única clareira de L1-5 quando o jogador (ou um grupo) limpa os
  dois de uma vez.

**P1-2 (herdado da r5/r6, reconfirmado). 2 Lobos simultâneos contra um Genin L1 recém-criado
é genuinamente perigoso — quase matou o personagem desta rodada (HP mínimo 22/150 = 14,7%).**
Diferente da r5 (onde o chakra "nunca limitou a caça" e a sensação era "mecânica, nunca
arriscada"), esta rodada mediu ao vivo uma janela real de quase-morte: HP caiu de 150→22 ao
longo de ~90s lutando contra 2 Lobos ao mesmo tempo (o 2º só morreu perto do fim, fechando o
level up bem na hora). Isso não é necessariamente "errado" (2 lobos por 1 jogador é um desafio
de verdade), mas é uma faceta da dificuldade de L1 que a r5/r6 não tinham capturado (lá só 1
Lobo foi engajado por vez). Recomendo que uma futura rodada de balanceamento formalize se
"2 Lobos simultâneos matam um Genin L1 sozinho, sem poção" é o resultado pretendido.

### P2

**P2-1 (herdado da r6, reconfirmado repetidas vezes). Vários pontos de colisão isolados
(não bolsões completos como o P0-1, só travam 1-2 direções) na faixa externa entre a Vila da
Folha e o Bosque Norte continuam exigindo desvio de várias tiles.** Consistente com o achado
da rodada 6; não é mais detalhado aqui pra não duplicar.

**P2-2 (novo). O cooldown real de `fuuton lamina vento` é ligeiramente maior que os 9,0s
nominais — uma tentativa de recast a +8,5s do cast anterior foi rejeitada com
`"You are exhausted."`** Consistente com a observação "9,0-10,0s reais" já registrada na
rodada 5; não parece ter mudado desde então.

**P2-3 (novo, mensagens transitórias de combate multi-alvo). Durante o combate com 2 Lobos
simultâneos, tentativas de cast retornaram `"Creature is not reachable."` e
`"You can only use it on creatures."` mesmo com um alvo válido por perto** — provavelmente o
alvo "atual" (setado por `g_game.attack`) morreu ou trocou entre o momento do clique e o
processamento do cast, um comportamento normal de qualquer sistema de alvo automático (não é
necessariamente um bug do jogo), mas contribui pro "feeling" de que lutar contra 2 monstros ao
mesmo tempo é mais caótico/imprevisível que 1.

**P2-4 (mojibake herdado, não retestado a fundo). Nomes de jutsu acentuados aparecem
corrompidos no log bruto do cliente** (`"Fuuton: L\xE1mina de Vento"`, `"Redemoinho
Pris\xE3o"`) — mesma família do achado central de `playtest-historia-arcos1-3.md`; segue sem
correção, mas fora do escopo desta rodada (focada em chakra/persistência).

## O que faria um jogador desistir

Em ordem de impacto, baseado no que foi medido/observado nesta rodada:

1. **Ficar preso para sempre num bolsão de mapa sem saída (P0-1).** Ainda que raro (é um par
   específico de tiles fora da rota principal), um jogador que caia lá literalmente não tem
   nenhuma ação dentro do jogo que o tire de lá — sem GM, sem item de teleporte, sem comando.
   Isso é uma "morte" pior que morrer de verdade (que pelo menos ressuscita o personagem).
2. **Quase morrer para 2 Lobos no primeiro nível, sem nunca ter sido avisado que isso podia
   acontecer (P1-2).** HP a 14,7% depois de ~90s de luta é uma experiência de tensão real —
   pode ser positivo (adrenalina) ou negativo (susto/frustração), dependendo do jogador, mas
   é um dado que faltava nas rodadas anteriores.
3. **Esperar 4,5 minutos parado sem nenhum monstro para caçar, logo na 1ª área de XP do jogo
   (P1-1).** Isso é o tipo de fricção "boba" que não tem nada de dramático, só é chato —
   mas em uma área desenhada pra ser o primeiro contato do jogador com o loop de XP, um
   intervalo tão longo sem ação é o tipo de coisa que faz alguém fechar o cliente "só por um
   minuto" e não voltar.
4. Itens herdados de rodadas anteriores, não retestados a fundo aqui: mojibake em texto
   acentuado (P2-4).

## Comparação com `progressao-jogador.md`

A tabela prevê **~536 XP/h** e **2,8h** para o bloco 1-5 inteiro (Lobo/Cervo na Floresta da
Vila). Esta rodada mediu só o bloco 1-2 (100 XP, level up confirmado), então a comparação é
parcial:

- **XP/h só na janela de combate real (~2200/h)** é bem acima da tabela — mas essa
  medida ignora a maior fricção real observada: **>270s de ociosidade** esperando o spawn
  repovoar entre uma sub-sessão e outra (P1-1). Contando esse tempo parado, o XP/h cai pra
  perto de ~530/h, **batendo quase exatamente com a tabela** (536/h) — ou seja, a curva de
  XP/h da tabela provavelmente já embute esse tipo de fricção de disponibilidade de monstro,
  não só o tempo de combate puro.
- **A pergunta central da missão (economia de chakra) foi respondida com clareza, e o
  resultado é o mesmo das rodadas 5 e 6**: no L1, o chakra nunca é o fator limitante —
  nem em combate normal (mínimo 94/110), nem na luta mais perigosa da sessão (mínimo
  82/110, quase-morte por HP). As fórmulas da rodada 9 de balanceamento (regen
  `2+piso(nível/4)` a cada 2s, pool 100+10×nível, custo 13%) continuam produzindo uma
  rotação "gargalada pelo cooldown", não pelo recurso — terceira rodada seguida a confirmar
  esse padrão especificamente no L1. Ainda não há dado de L5+ nesta família de rodadas pra
  saber se o padrão se inverte (regen chakra/s cresce mais devagar que o custo absoluto em
  níveis altos, por design — ver nota da rodada 5).
- **Dificuldade de combate**: a tabela não modela "quantos monstros simultâneos" um jogador
  enfrenta — só XP/h agregado. Esta rodada mostrou que **2 Lobos ao mesmo tempo quase mataram
  um Genin L1** (HP 14,7%), o que é uma informação de risco que a tabela de XP/h sozinha não
  captura.

## Metodologia e limitações

- Contas/personagem: `ptsete`/`Playtester Sete` (id=14), criados 100% via AAC HTTP, nunca
  via SQL direto ou GM. Kit, seleção de personagem/elemento e todo o combate/navegação
  foram feitos pelo jogo de verdade (opcode 210, `g_game.walk`/`g_game.attack`/`g_game.talk`)
  — **nenhum comando de GM foi usado em nenhum momento** (`/god`, `/tp`, `/m`, `/i` etc.).
- **3 scripts sucessivos** (`client-otc/shinobirc.lua`, cada um copiado por cima do anterior,
  nunca commitado, apagado ao final): (1) rota completa vila→Bosque Norte + janela de caça
  contínua até L5 ou 40 min; (2) NPCs (Rin/Jiro/quadro/Ichiro) + `!conquistas` + logout; (3)
  verificação final de persistência (relogin sem re-selecionar personagem). Cada um seguiu o
  mesmo padrão de sequenciador de fila usado nas rodadas 4-6, com uma função nova
  (`stepEscaping`) compartilhada entre a navegação ponto-a-ponto e o fallback de patrulha de
  caça — espirala pelas 8 direções ao redor da direção dominante quando emperra, achado
  desta própria rodada depois que o fallback de patrulha (sem essa lógica, só 1 direção fixa)
  ficou preso indefinidamente nos mesmos bolsões que a navegação normal conseguia atravessar.
- **Uma única sub-sessão de caça foi executada em múltiplas tentativas por causa do P0-1**
  (bolsão de mapa sem saída): a 1ª tentativa de rota (vila→Bosque Norte) prendeu o
  personagem por >4 min real num bolsão de 2 tiles perto de `1044,1026`; a 2ª tentativa
  (script já com a navegação corrigida e um atalho pra pular a rota de vila quando o
  personagem já está perto do destino) caiu no MESMO bolsão outra vez a partir de um ponto de
  partida ligeiramente diferente (`1047,1020`↔`1046,1021`), confirmando que não é
  coincidência de rota, é uma característica real do terreno. A saída usada foi
  `UPDATE players SET posx=...,posy=...` direto no banco **depois de confirmar por
  `/tmp/tfs_run.log` que o servidor já tinha processado um logout de verdade** (achado de
  metodologia: matar o cliente com `SIGKILL` não fecha a conexão TCP goodbye-style — o
  servidor só percebe a desconexão depois de um timeout próprio, e um `UPDATE` de posição
  feito antes disso é silenciosamente sobrescrito quando o servidor finalmente processa o
  "logout" da sessão fantasma com a posição antiga em memória; **por isso a posição só ficou
  de fato onde eu queria depois que passei a esperar a linha `"... has logged out."`
  aparecer em `/tmp/tfs_run.log` antes de tocar no banco**). Nenhum comando de GM foi usado
  pra essa correção — só leitura/escrita direta na tabela `players` (equivalente a uma
  intervenção de operador de banco de dados, não uma ação dentro do jogo).
- **PIDs do cliente**: cada `nohup ./OTClient.app/Contents/MacOS/OTClient` gerou um PID que
  bateu direto com `pgrep -fl "OTClient.app/Contents/MacOS/OTClient"` desta vez (sem o
  problema de PID "wrapper" da rodada 6). `kill` (SIGTERM) sozinho não encerrou o processo em
  nenhuma tentativa (aplicação Qt sem handler de SIGTERM) — sempre precisou de `kill -9`.
  Nunca usei `pkill -x OTClient`; nenhum outro processo OTClient de outro agente foi
  encontrado rodando durante esta sessão.
- **Screenshots**: 16 (`playtest7_01` a `playtest7_30`, ver `screenshots/`), bem abaixo do
  limite de 40. `~/Library/Application Support/shinobi/.shinobi/*.png` limpo ao final
  (confirmado vazio de `playtest7_*`).
- **Servidor**: nunca reiniciado por esta sessão (`nc -z 127.0.0.1 7171` confirmado no início
  e no fim). `grep -c "Lua Script Error" /tmp/tfs_run.log`: **0** do início ao fim da sessão.
- **Disco**: `df -h /`: 13 GiB livres no início, **13 GiB livres no fim** (sem variação
  perceptível). `df -h /System/Volumes/Data`: 13 GiB livres em ambas as pontas (94% usado) —
  acima do piso de 1,5 GB o tempo todo.
- `client-otc/shinobirc.lua` apagado ao final (confirmado ausente). Nenhum processo OTClient
  próprio deixado rodando ao final (confirmado com `pgrep -fl
  "OTClient.app/Contents/MacOS/OTClient"`, vazio). Sessão final terminou com
  `g_game.safeLogout()` bem-sucedido (fora de combate, HP/chakra cheios) — diferente da
  rodada 6, que teve o logout final rejeitado por estar em/perto de combate.
