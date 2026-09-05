# Playtest QA — nível 1 a 20, rodada 5 (2026-09-05) — segunda tentativa

Sessão de playtest de um jogador comum, conta `kitqa2` (personagem **Kit QA Dois**, Genin
Laranja, Vila da Folha, L1, 110 chakra), retomando de onde a primeira tentativa desta rodada
(interrompida pela queda da própria sessão do agente, não do jogo) parou. Metodologia validada
pelas rodadas 3/4: `client-otc/shinobirc.lua` temporário (nunca commitado, apagado ao final de
cada sub-sessão), saltos curtos de `autoWalk` (≤10 tiles), passo manual através de portas
fechadas antes de confiar em `autoWalk` (achado da rodada 4), tratamento de morte/relogin
automático, `g_game.safeLogout()` ao encerrar, runner próprio que mata só o PID que ele mesmo
abriu (nunca `pkill -x OTClient` — há um OTClient do usuário rodando, PID diferente, intocado).

**Documento preenchido incrementalmente durante a sessão** — cada seção foi completada conforme
o playtest avançou, na ordem em que os dados ficaram disponíveis.

## Resumo executivo

**Jogável no L1, mas com um susto sério de balanceamento de mapa e uma pergunta central da
missão respondida com clareza.** O kit chegou completo (6 itens, HP 150/150, chakra 110/110),
o combate funciona (dano de arma 1-10, dano de jutsu 1-10, XP exato: 25 por Lobo), a conquista
de zona (P1-3 da rodada 4) está **confirmadamente corrigida** (0/55 no login, dispara só depois
de sair da muralha) e o achado central pedido pela missão — "o cooldown de 9s deixa a rotação
divertida ou arrastada" — tem resposta direta e medida: **o chakra nunca seca no L1** (9 casts
seguidos, sempre voltando a 108-110/110 antes do próximo estar liberado), então a rotação virou
"1 jutsu a cada 9s + 1-4 socos de preenchimento" sem nenhuma gestão real de recurso — nem
arrastada nem emocionante, apenas mecânica e previsível (detalhe na seção de chakra abaixo).

**O grande problema desta rodada não foi o L1 em si, foi a ROTA até ele.** A viagem a pé da
Vila da Folha até a Trilha dos Lobos/Bosque Norte — o destino óbvio de L1-5 — cruza, se o
jogador (ou um script) seguir o caminho mais natural pelo Portão Leste, uma faixa de terreno a
poucos tiles do spawn de **Bandido Arqueiro** da Clareira Central (monstro de faixa L6-10). Um
Genin L1 **morreu em 15 segundos reais só de passar por essa faixa**, sem nunca ter engajado
combate — isso é o tipo de morte que um jogador novo não entende e não esquece (ver P1-5). Uma
segunda morte aconteceu por um erro do meu próprio script (ficar parado perto do spawn de Lobo
sem lutar de volta, ver metodologia) — não é um achado de balanceamento, mas mostra que só
"ficar perto" de um spawn de L1-5 sem reagir já custa ~140 HP em ~2 minutos, o que é coerente
com o dano de Lobo mostrado na tabela de combate.

**Cobertura real desta rodada**: nível 1 completo (chakra/cooldown, 2 kills de Lobo, 50 XP,
achievements antes/depois de sair da vila), navegação completa e documentada (com 3 achados de
mapa/colisão reportáveis: P1-5, P1-6, P2-10), e uma tentativa de missões/NPCs da vila que **não
terminou em diálogo confirmado ao vivo** por dois motivos combinados: (a) a mesma área de
obstáculos perto da fonte/lojas que já tinha atrasado a navegação anterior, e (b) meu limiar de
"chegou perto o suficiente" (4 tiles) não é próximo o bastante para efetivamente falar com um
NPC. **Nível 2-10 e Costa das Marés não foram alcançados** — o tempo desta rodada foi consumido
majoritariamente por iteração de navegação (5 reescritas da rota até o Bosque Norte funcionarem
de forma confiável) e pelos dois incidentes de morte, não por falta de tentativa.

## Ambiente no início da sessão

- `df -h /System/Volumes/Data`: ver seção "Espaço em disco".
- Servidor (`build/tfs`, PID 1741) já rodando desde 13:11:16 (52 min antes do início desta
  sessão), não reiniciado por esta sessão.
- `client-otc/shinobirc.lua`: ausente antes de começar (confirmado).
- Personagem `Kit QA Dois` já existia no banco (retomado da 1ª tentativa desta rodada, que
  criou a conta/personagem mas caiu antes de jogar): L1, 0 XP, HP 150/150, chakra 110/110,
  posição (1017,1059,7) — dentro da muralha, perto da Academia/Prisão, kit de 6 itens no
  inventário (não decodificado por nome via SQL, a confirmar visualmente no 1º login).
- Um OTClient do usuário já está aberto (PID 2149) — **não tocado** em nenhum momento.

## Tabela por nível

| Nível | Tempo real gasto | Kills | Mortes | XP ganho | XP/h | Observação |
|---|---|---|---|---|---|---|
| 1 | ~4 min de combate real espalhados em 2 sub-sessões (a maior parte do tempo total foi navegação, não combate — ver metodologia) | 2 (Lobo) | 2 (P1-5: Bandido Arqueiro em rota, sem engajar; P2-12: ficou parado perto do spawn sem lutar de volta, dano acumulado de Lobo) | 50 | **~2170/h** medido na janela de combate real (50 XP em ~83s, do 1º ao 2º kill) — **acima** da tabela (~536/h), mas amostra pequena (2 kills) e não sustentada por tempo suficiente pra ser conclusivo | Chakra nunca limitou a caça (ver tabela de chakra); L2 não foi alcançado (faltam 150 XP dos 200 do nível) |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |
| 6 | | | | | | |
| 7 | | | | | | |
| 8 | | | | | | |
| 9 | | | | | | |
| 10 | | | | | | |

## Tabela de chakra/regen

Fórmulas esperadas (`docs/sistemas/balanceamento-relatorio-v5.md`): pool = 100+level×10 (110 em
L1), regen = [3+level//4] a cada 2s (1,5/s em L1), custo `fuuton_lamina_vento` = 2,75% do pool
(3 em L1), cooldown tier 1 = 9,0s.

| Nível | Jutsu | Custo medido | Cooldown medido | Casts até secar | Chakra final | Regen medido (10 em 10s) | Tempo pool cheio parado |
|---|---|---|---|---|---|---|---|
| 1 | `fuuton lamina vento` | **2** (110→108, confirmado 1x na janela entre ticks) | **~9,0-10,0s real** (9 casts em 84s corridos: t=1,11,21,31,41,51,61,71,81s — gaps de 10,0s exatos, o script só permite recastar a cada ≥9,2s e o servidor nunca rejeitou por cooldown ainda ativo) | **Não secou em 9 casts consecutivos** (~84s), sempre lutando contra 1-2 Lobos por perto — ver texto abaixo | **Nunca abaixo de 108/110** (ficou cheio/quase cheio o tempo todo) | **Não aplicável do jeito pedido** — o chakra nunca chegou a ficar vazio parado, porque a cada 10s (intervalo do cooldown) ele já tinha regenerado de sobra | **Não medido isolado** — em combate real (com Lobo por perto), o chakra ficou permanentemente em 108-110/110 |

**Achado central desta rodada (responde a pergunta #1 da missão): ao nível 1, com as fórmulas
da rodada 5 de balanceamento (pool 100+level×10, regen `[3+level//4]` a cada 2s, custo de
`fuuton_lamina_vento` = 2,75% do pool), o chakra NUNCA seca de verdade em combate sustentado.**
Medido ao vivo: 9 casts consecutivos de `fuuton lamina vento` (o único jutsu do L1) contra Lobos
de verdade (2 kills fechados no meio do teste), sempre gastando **2 de chakra** (110→108) e
sempre voltando a 110/110 **antes do próximo cast estar liberado** — o custo (2) é tão pequeno
frente ao regen (1,5/s = 3 a cada 2s) que o pool volta cheio em ~1,3s, muito mais rápido que os
~9-10s do cooldown entre casts. Isso é o oposto exato do achado da rodada 3 (chakra travado em
8/60 por 7 minutos sem regenerar nem uma vez) — a rodada 5 de balanceamento resolveu esse P1-1
por completo no nível 1, só que **na direção oposta ao esperado**: em vez de "regen suficiente
para sustentar o jutsu", o jutsu virou uma ação que nunca é limitada por chakra no L1 — o único
limitador real da rotação agora é o cooldown de 9s, não o recurso.

**Veredito do cooldown de 9s: a rotação vira "1 jutsu a cada 9s + socos de preenchimento",
sustentável indefinidamente, mas o jutsu deixou de ser um recurso escasso.** Contando hits de
arma entre casts nos 9 intervalos medidos: **1 a 4 hits de arma por janela de 9-10s** (variação
alta — às vezes o lobo morre rápido e some antes do 3º/4º hit, às vezes o script demora a
re-adquirir alvo). Dano típico por hit de arma: 1-10 (a maioria 1-4, ocasionalmente 7-10).
O jutsu sozinho causou 1-10 por cast (média ~6-7, ex.: casts trouxeram hits de "9", "8", "9",
"7", "3", "9", "8", "10", "2" no log — a variação inclui alguns casts que erraram o alvo por
troca de lobo). O **1º Lobo morreu ao redor do 4º cast** (~31s de combate), contando dano de
jutsu+arma combinados — puramente de jutsu (sem arma) provavelmente levaria uns 5-6 casts
(45-54s) dado o dano médio do jutsu sozinho. **Sensação**: nem "arrastada" nem "empolgante" —
é uma rotação mecânica e previsível (cast, 3-4 socos, cast, repete) que nunca é interrompida
por falta de chakra; a "decisão" de gerenciar recurso que a rodada 3/4 descreviam (guardar
chakra pro burst, evitar gastar à toa) **deixou de existir no L1** — o jogador só precisa
apertar o jutsu sempre que ele estiver disponível, sem nunca temer ficar seco. Isso é bom para
"nunca mais travar" (resolve de vez o P1-1 antigo), mas troca "gerenciar chakra" por "não há
mais nada pra gerenciar" — uma sensação mais próxima de "soco com efeito colateral de vez em
quando" do que de "jutsu como recurso tático". Recomendo considerar, para uma rodada futura de
balanceamento, se o custo de 2,75% é baixo demais especificamente no L1 (onde o pool de 110 é
pequeno o bastante pra regenerar rápido em termos absolutos, mesmo a taxa "certa" em %) — nos
níveis mais altos da tabela do relatório v5 (L20+) o problema pode não se repetir, já que o
regen chakra/s cresce mais devagar que o custo absoluto por cast.

## Missões / tarefas / diária / loja

- `!conquistas` **antes** do 1º lobo (login inicial, dentro da muralha): `0/55 | exploration
  0/6 | ...` — confirma que o P1-3 da rodada 4 (zona de exploração destravando no spawn) está
  **corrigido** (ver "O que foi corrigido" abaixo).
- `!conquistas` **depois** do 1º lobo (já fora da muralha, no Bosque Norte, relogin
  subsequente): `1/55 | exploration 1/6 | ...` — a conquista "Pisou em Floresta da Vila"
  desbloqueou corretamente **só depois** de cruzar a muralha, com a mensagem
  `Conquista desbloqueada: Pisou em Floresta da Vila!` aparecendo no momento certo da sessão.
- `!conquistas` depois da entrega da missão dos lobos: **não alcançado** (missão não entregue
  nesta rodada, ver abaixo).
- Missão dos lobos (Capitã Rin, `hi`/`missao`, NPC em 1047,1053 — interior 1320-1325,1000-1005):
  **tentado, não confirmado por diálogo ao vivo.** O personagem chegou a ~4 tiles da entrada
  (limiar de "chegou perto o suficiente" da navegação) duas vezes, mas o `g_game.talk('hi')`
  disparado a essa distância não gerou nenhuma resposta de NPC no log — o alcance de fala de um
  NPC no OTClient parece exigir estar bem mais próximo (provavelmente ≤1-2 tiles, ou em cima do
  pad de teleporte que leva para dentro da loja) do que o limiar de 4 tiles que a navegação usa
  para "chegar" num waypoint comum. Ver P2-13.
- Tarefa (Mestre Jiro, `hi`/`tarefas`/`tarefa`/`entregar`, 1030,1067): **não alcançado** — a
  navegação até Jiro não completou dentro do tempo desta rodada (ver metodologia).
- Diária (Quadro de Missões, `hi`/`diaria`, 1035,1040): **tentado, mesma limitação do alcance de
  fala** — o personagem chegou a 1031,1040 (4 tiles do NPC), `hi`/`diaria` não geraram resposta.
- Compras (Ichiro, `hi`/`trade`, 1038,1053): **tentado 1x** (durante a sub-sessão que também
  teve o incidente de referência de personagem errada, P2-11) — sem resposta de diálogo
  confirmada nem erro de `Lua Script Error` no log do cliente; screenshot tirado
  (`playtest5_07_ichiro_trade.png`) mas não dá para confirmar visualmente se a loja abriu.
- **Nenhum destes 4 NPCs teve diálogo de texto confirmado nesta rodada** — diferente das
  rodadas 1 e 3, que confirmaram aceite de tarefa do Jiro e o fluxo completo do Quadro de
  Missões respectivamente. Não há motivo para achar que os sistemas quebraram (nenhuma
  alteração de escopo tocou `data/npcs/*.json` desde então, e o `!conquistas`/combate
  continuam funcionando normalmente) — a causa mais provável é puramente metodológica (P2-13),
  não um bug de jogo novo. Fica como pendência nº 1 da próxima rodada.

## L5→L10 (bandidos/cobras)

**Não alcançado como caça planejada** — o personagem nunca chegou ao L5 nesta rodada (parou em
L1, 50 XP). O único contato real com a fauna de L6-10 foi **não intencional e fatal** (P1-5): ao
tentar contornar a Clareira Central (1070,1040, 2 Bandido Arqueiro) a caminho do Bosque Norte,
o personagem L1 foi alvejado e morto em 15s sem nunca ter entrado propositalmente em combate —
ver a tabela de dano no P1-5. Isso serve como um dado real, ainda que involuntário, sobre o
monstro de L6-10 mais próximo da rota de L1-5: o dano por hit (5-12) e a cadência (~1 hit a cada
2-3s) são consistentes com um monstro pensado para um personagem bem mais forte que um Genin L1
recém-saído da vila.

**Nota sobre a nomenclatura da missão vs. o arquivo de spawn instalado**: a missão pediu para
caçar bandidos/cobras em "Bosque Norte/Clareira Central", mas o `valley-spawn.xml` atualmente
instalado (`server/tfs/data/world/valley-spawn.xml`) tem **Lobo×2** no Bosque Norte (1050,1010)
— igual à Trilha dos Lobos (1012,1012) — e só a **Clareira Central** (1070,1040) tem Bandido
Arqueiro de fato; bandidos comuns ficam na "Campina Oeste" (1006,1050, 3 Bandido) e cobras na
"Clareira do Riacho" (1085,1015). Ou seja, "Bosque Norte" citado pela missão como área de L5-10
é, no arquivo instalado hoje, uma área de Lobo (L1-5) — a nomenclatura da missão parece estar
descrita a partir de uma versão anterior do mapa/spawns. Usei o Bosque Norte como meu segundo
spot de Lobo L1-5 (ver acima) exatamente por essa razão, e recomendo que quem for revisar
`docs/sistemas/mapas.md`/`tools/map/build_valley.py` confirme se a intenção de design era
mesmo essa ou se houve uma regressão nos spawns dessa clareira específica.

**Pendência para a próxima rodada**: medir de verdade a Campina Oeste (bandidos) e a Clareira
do Riacho (cobras) com um personagem já em L5+, com uma rota que dê uma folga de pelo menos
8-10 tiles do centro da Clareira Central (P1-5) — a rota seguindo x≈1055 (em vez de x≈1065)
usada nesta rodada para chegar ao Bosque Norte evitou o problema com sucesso e pode servir de
referência de distância segura.

## Costa das Marés (se sobrar tempo)

**Não alcançado** — não sobrou tempo desta rodada depois dos dois incidentes de morte e da
iteração extensa de navegação. Coordenadas confirmadas por inspeção de `docs/sistemas/mapas.md`
para quem retomar: região `build_coastal_tides`, x 1000-1049, y 1120-1169; liga à Vila da Folha
pela trilha sul (1029,1069 → 1029,1090 → bifurcação em 1025,1091 → 1029,1142); cais de madeira
com o boss Espadachim da Névoa em (1025,1163-1033,1168).

## Achados por severidade

### P0

Nenhum até agora (kit completo confirmado, spawn/regen funcionando).

### P1

**P1-5 (novo, confirmado ao vivo, morte real). Um Genin L1 pode morrer só de PASSAR perto do
spawn de Bandido Arqueiro da Clareira Central (1070,1040, raio 4, 2 arqueiros), sem nunca ter
engajado o combate.**

- **Repro**: sair da Vila da Folha pelo Portão Leste (1049,1055) e seguir para o norte por fora
  da muralha com x≈1063-1065 (a ~5-7 tiles do centro do spawn 1070,1040) — não é preciso se
  aproximar do centro do spawn nem atacar nada.
- **Medido**: HP caiu de 150/150 para 0 em ~15 segundos reais (14:29:30 a 14:29:45), levando
  hits de "um bandido arqueiro" de 5 a 12 de dano cada, a cada ~3s, sem nenhuma chance real de
  reagir a tempo com um Genin L1 (150 HP, sem jutsu de cura pronto). Log completo:
  `HB hp=150→119→81→43→28→23→14→9→2→0` entre 14:29:00 e 14:29:45, terminando em
  `MSG: You are dead.`
- **Causa provável**: o alcance de agressão/tiro do Bandido Arqueiro (monstro L6-10) parece ir
  bem além do raio de 4 tiles do próprio spawn — um personagem que nunca entrou no raio do
  spawn, só passou a ~5-7 tiles de distância em rota para outra área, foi alvejado e morto sem
  aviso. Isso é especialmente grave porque a rota mais curta e natural da Vila da Folha (Portão
  Leste) para a Trilha dos Lobos/Bosque Norte (destino de L1-5) passa exatamente por essa faixa
  de coordenadas.
- **Efeito**: um jogador novo de L1 que ande a pé do Portão Leste até a Trilha dos Lobos (rota
  natural, sem conhecer o mapa) tem chance real de morrer para um monstro de uma faixa de nível
  muito mais alta antes mesmo de chegar à área que deveria caçar — isso é o tipo de coisa que
  faz um jogador desistir no primeiro dia (ver seção correspondente).
- **Sugestão**: (a) reduzir o alcance de agressão a distância do `bandit_archer` para não
  ultrapassar muito o raio do próprio spawn, ou (b) aumentar a distância entre a Clareira
  Central e a rota mais óbvia entre a Vila da Folha e a Trilha dos Lobos/Bosque Norte, ou (c)
  no mínimo documentar em `docs/sistemas/mapas.md` que a faixa x=1060-1075,y=1030-1050 fora da
  muralha é perigosa para personagens abaixo de L6 e não deveria ficar no caminho direto entre
  a vila e a área de L1-5. Fora do escopo de edição autorizado nesta rodada (monstros/mapas).

**P1-6 (novo, achado de navegação/mapa, não confirmado como bug de jogador humano).** Pelo menos
uma posição junto ao Portão Sul, por fora da muralha (**1028,1070**, 1 tile a sudoeste do arco
torii em 1030,1070), rejeitou **toda tentativa de movimento** (`autoWalk` e `g_game.walk` manual
nas 8 direções) com `RETURNVALUE_NOTENOUGHROOM` ("There is not enough room.") por >3 minutos
seguidos, incluindo uma tentativa de `autoWalk` de volta ao templo (rota que deveria ser trivial).
Só foi possível escapar dali numa sessão seguinte, chegando por um ângulo ligeiramente diferente
(via 1021,1070/1025,1070 em vez de descer reto pelo portão). Não confirmei se um jogador humano
clicando normalmente ficaria preso do mesmo jeito (o clique humano manda uma única localização-
alvo por vez, igual ao nosso `autoWalk`, então o risco é real, mas não testei com mouse de
verdade). Registrado para quem for revisar a malha de colisão fora do Portão Sul —
possivelmente um item decorativo (tocha, placa ou o próprio arco torii) com hitbox maior que o
esperado, ou uma célula não conectada ao resto do exterior por engano.

### P2

**P2-11 (novo, achado sério de metodologia/cliente, sem dano real). Depois de um ciclo
`GAME END` (morte) seguido de relogin automático, `g_game.getLocalPlayer()` retornou por
alguns segundos a referência de uma criatura ERRADA — o personagem GM de outro agente
(conta `god`, personagem "GM", L20, 98800 XP, 1815/1815 HP), não o meu próprio `Kit QA Dois`.**

- **Repro**: script mata o personagem, espera 5s, refaz `EnterGame.doLogin()`. No log do
  cliente, junto com um erro C++ (`got a thing with invalid stackpos`,
  `Tile::checkForDetachableThing`, `ProtocolGame::parseCreatureOutfit`), o heartbeat do script
  passou a reportar `hp=1815/1815 chakra=1110/1110 lvl=20 xp=98800 pos=1030,1105`, e uma
  mensagem de GM apareceu no chat ("Arena em 1030,1097,7. Use /m Lobo para invocar.") — nem o
  HP/level nem a mensagem batem com `Kit QA Dois` (L1, 110 de chakra).
- **Confirmado que NÃO houve dano real**: consultei `forgottenserver.players` direto por SQL
  (leitura, sem alterar nada) — `Kit QA Dois` permaneceu o tempo todo em `level=1, xp=50,
  pos=(1029,1042,7)` (o templo), exatamente onde deveria estar depois do respawn. O personagem
  "GM" da conta `god` (outro agente, log do servidor confirma `GM has logged in.` no mesmo
  instante) nunca teve sua posição alterada por mim — os comandos de `autoWalk` que meu script
  disparou nessa janela confusa não moveram nem o meu personagem (ele ficou parado no templo)
  nem, presumivelmente, o do outro agente (a movimentação de um jogador só é aceita pelo
  servidor na conexão de rede dona daquele personagem — o meu socket não pode mover o
  personagem de outra sessão). **Ou seja: foi um bug de exibição/referência local no cliente,
  não uma invasão de sessão real** — mas por um triz o script tomou decisões (rota, distância)
  baseadas em dados de outro jogador, o que poderia ter mascarado um problema real se o
  personagem certo tivesse, de fato, se movido.
- **Causa provável**: o "GM" de outro agente provavelmente estava parado bem em cima ou perto
  do tile de spawn (templo, 1029,1042) no instante exato do meu relogin — o parser de
  `parseCreatureOutfit` bateu num "thing" com stackpos inválido nessa mesma mensagem de rede,
  sugerindo que o cliente confundiu qual criatura era "eu" ao processar a descrição do piso
  logo após reconectar, quando duas entidades (a minha, recém-criada, e a do GM, já existente)
  disputam a mesma pilha de criaturas na tile.
- **Efeito prático para quem for escrever o próximo script de QA**: depois de qualquer
  relogin automático, **não confie cegamente no primeiro heartbeat** — valide que
  `getName()`/`getLevel()` batem com o personagem esperado antes de tomar qualquer decisão de
  navegação ou combate baseada nele; se não bater, espere mais um ou dois ciclos antes de agir.
  Isso é ainda mais importante no ambiente compartilhado desta missão, onde outros agentes
  podem estar logados como GM ao mesmo tempo.
- **Sugestão**: fora do escopo de edição autorizado (é um bug de baixo nível do cliente OTC,
  não dos módulos `naruto_*`) — registrado para quem for revisar `ProtocolGame::parseCreatureOutfit`/
  `Tile::checkForDetachableThing` em `client-otc/src/client/`.

**P2-9 (novo, metodologia de navegação).** `LocalPlayer:autoWalk` para um alvo distante (>15-20
tiles, fora do que o cliente já "conhece") não retorna erro de forma síncrona nem gera nenhuma
mensagem — o personagem simplesmente não anda, ficando preso ("dist" nunca diminui). Confirmado
2x: (1) alvo "Trilha dos Lobos" logo depois do login, quando o cliente só conhecia a vizinhança
do spawn; (2) rota inicial tentando pular direto da praça pro Bosque Norte. **Aprendizado para a
próxima rodada**: nunca mirar um `autoWalk` a mais de ~10 tiles de distância da posição atual;
sempre recalcular um hop intermediário a cada ciclo (não uma lista fixa de waypoints distantes)
e monitorar a posição real para confirmar progresso, não só disparar o comando e assumir que
funcionou.

**P2-10 (novo, metodologia/mapa).** A fileira de lojas da Rua dos Mercadores (fachadas do
Ichiro/Hayato, x≈1037-1045,y≈1049-1053) tem pelo menos um ponto (**1041,1053**, entre as
fachadas do Ichiro e do Hayato) onde o personagem ficou fisicamente preso por several ciclos,
sem conseguir andar em NENHUMA das 8 direções (`There is not enough room.` em todas). Andar
"por acidente" para dentro do teleporte de entrada da loja do Hayato (1044,1053 → interior
1310-1317,1000-1005) também aconteceu 1x ao tentar cortar caminho por essa fileira — o
personagem só voltou pro lado de fora por sorte, quando um hop calculado por engano bateu no
pad de saída do interior. **Sugestão de rota**: quem for escrever o próximo script de QA deve
evitar cortar caminho rente às fachadas de loja (y=1049-1053 entre x=1037-1048) — ou contornar
por y≥1058 (rua aberta) ou sair pelo Portão Leste com uma folga de pelo menos 5-6 tiles das
fachadas antes de virar para o norte/sul.

**P2-12 (novo, achado de metodologia/dano). Ficar parado perto do spawn de Lobo (raio 4) sem
lutar de volta custa ~140 HP em ~2 minutos.** Numa sub-sessão em que o script tentava navegar
para fora do Bosque Norte sem reengajar o alvo (sem chamar `g_game.attack`), o personagem foi
golpeado repetidamente por 1 Lobo parado a distância curta (a maioria dos hits 1-4 HP, alguns
5-6), levando de 150/150 a 0 em pouco mais de 90s reais, terminando em `You are dead.`. Isso não
é um bug — é o comportamento esperado de ficar num raio de agressão sem lutar — mas quantifica
concretamente o "custo de não reagir" nessa área: um jogador que tropece no meio de um combate e
tente fugir sem saber que o Lobo persegue por perto tem ~90s antes de morrer, não é instantâneo,
mas também não é trivial de ignorar.

**P2-13 (novo, achado de metodologia). O limiar de "chegou perto o suficiente" (4 tiles) usado
pela navegação adaptativa não é próximo o bastante para efetivamente falar com um NPC.**
Confirmado 2x (Quadro de Missões e Capitã Rin): o personagem parou a 4 tiles do NPC, `g_game.talk`
foi disparado, e nenhuma resposta de diálogo apareceu no log. **Aprendizado para a próxima
rodada**: usar um limiar de chegada bem mais apertado (≤1-2 tiles, ou melhor, tentar pisar
exatamente no pad de teleporte/posição do NPC quando aplicável) antes de disparar qualquer
`g_game.talk` — os 4 tiles usados para "considerar uma rota completa" servem bem para pontos de
passagem genéricos, mas não para interação de NPC.

## O que foi corrigido nesta sessão

Nada foi editado nos dados/scripts (fora do escopo autorizado nesta rodada — `export_tfs.py`/
`install_generated.sh`/`/reload` explicitamente vetados). O único "conserto" confirmado foi de
**outra equipe, entre as rodadas 4 e 5**: o P1-3 da rodada 4 (conquista de exploração
desbloqueando no spawn, dentro da muralha) foi corrigido em
`server/tfs/data/lib/naruto_achievements.lua` com um `zoneExclude` explícito para o retângulo da
Vila da Folha (1010,1030-1049,1069), com um comentário no próprio arquivo referenciando "playtest
r4" — exatamente a sugestão que a rodada 4 tinha registrado. Confirmei o efeito ao vivo nesta
rodada: `0/55` no login (dentro da vila) → `1/55, exploration 1/6` só depois de cruzar a
muralha, com a mensagem de desbloqueio aparecendo no momento certo.

## Comparação com `progressao-jogador.md`

A tabela prevê **~536 XP/h** e **2,8h** para o bloco 1-5 inteiro (Lobo/Cervo na Floresta da
Vila). Os números reais desta rodada:

- **XP/h na janela de combate real**: ~2170/h (50 XP em ~83s do 1º ao 2º kill) — **4x acima**
  da tabela. Amostra pequena (2 kills), mas consistente com a rodada 3 (que também mediu acima
  da tabela na janela sem mortes, 717-1895/h) — o padrão de "dano do personagem bem calibrado ou
  generoso para L1" parece se repetir.
- **XP/h contando as mortes e a navegação**: **muito abaixo** da tabela — em ~50 minutos reais
  de sessão (entre todas as sub-sessões desta rodada), só 50 XP líquidos ficaram no personagem
  ao final. A esmagadora maioria do tempo foi navegação (não combate) e duas recuperações de
  morte, não combate propriamente dito. Isso não é um problema de balanceamento de XP — é um
  problema de **fricção para chegar ao combate**, que a tabela de progressão não modela (ela
  assume implicitamente que o jogador já está no spot de caça).
- **Chakra/regen**: a tabela de balanceamento v5 (não a de progressão) previa "≥4 casts, recupera
  em ≤90s parado" como meta mínima para L1 — o que foi medido (9 casts sem nunca secar, sempre
  cheio) **excede a meta com folga enorme**, na direção de "chakra deixou de ser um limitador",
  como discutido na seção de chakra acima.

## O que faria um jogador desistir

Em ordem de impacto, baseado no que foi medido/observado nesta rodada:

1. **Morrer para um monstro de nível muito mais alto, sem aviso, só de passar perto dele numa
   rota que parece a mais óbvia entre a vila e a área de caça de L1-5** (P1-5). Isso é,
   disparado, o pior tipo de primeira impressão: o jogador não fez nada de errado (não atacou
   ninguém, não se aproximou de propósito) e ainda assim morreu em 15 segundos. Diferente de
   "esse monstro é difícil" (frustração aceitável), isso lê como "o jogo me matou sem eu
   entender por quê" — o tipo de morte que faz alguém fechar o cliente e não voltar.
2. **A viagem até a área de caça consumir a maior parte do tempo de sessão.** Mesmo sem contar
   os incidentes, a rota da vila até o Bosque Norte levou minutos de navegação real (mesmo já
   sabendo o caminho) — um jogador novo, sem mapa, provavelmente leva ainda mais. Isso não é
   necessariamente ruim para um jogador humano com mouse/teclado (que anda mais eficientemente
   que os saltos de `autoWalk` script), mas o tempo de viagem em si, somado ao risco do item 1,
   é uma fricção real de início de jogo.
3. **O chakra nunca ser um fator de decisão no L1** (achado central desta rodada) — não é um
   motivo de desistência por si só (ninguém desiste porque um recurso é fácil demais), mas é uma
   oportunidade perdida de profundidade nos primeiros minutos de jogo: o jutsu, que deveria ser
   a "novidade" do combate ninja, vira apenas "mais um botão que sempre está disponível".
4. Pontos herdados de rodadas anteriores, não retestados a fundo nesta rodada: `{tarefas}`
   travando o chat do cliente (P1-2 da rodada 1/3, não confirmado nem desmentido aqui).

## Metodologia e limitações

- **Script de automação**: 5 versões sucessivas de `client-otc/shinobirc.lua` (fases A-D, cada
  uma nunca commitada, apagada ao final de cada sub-sessão), rodadas por um runner próprio
  (`run_qa.sh`, com retry automático se o processo terminar em <60s) que mata **só o PID que
  ele mesmo abriu** — nunca `pkill -x OTClient`. A navegação evoluiu de waypoints fixos distantes
  (fase A, falhou — `autoWalk` não anda para destinos desconhecidos do cliente, P2-9) para saltos
  curtos recalculados a cada ciclo com detecção de "preso" e troca de direção (fases B-D).
- **Ambiente compartilhado, confirmado na prática**: por volta de 14:13, o OTClient do usuário
  (PID 2149, aberto antes desta sessão começar) **fechou por conta própria** (o usuário
  aparentemente trocou de atividade — abriu o Riot Client no mesmo horário) — não foi causado
  por mim, confirmado por `pgrep`/`ps` antes e depois. Também confirmei, via log do servidor e
  SQL, que outro agente estava logado como GM (conta `god`) durante parte desta sessão — o que
  motivou o achado P2-11 (referência de personagem local trocada por engano após um relogin).
- **5 quedas do próprio processo `OTClient`** ao longo da sessão: 1 aparentemente por contenção
  de estado/config compartilhado ao abrir uma 2ª instância (~42s de vida, sem crash report),
  algumas por eu mesmo matar sessões travadas em loops de navegação sem saída, e nenhuma
  segfault registrada em `~/Library/Logs/DiagnosticReports` durante esta sessão (diferente do
  P2-6 da rodada 4). O runner com retry automático absorveu a maioria sem intervenção manual.
- **2 mortes reais tratadas como dado, não como falha do script** (conforme pedido pela missão):
  P1-5 (Bandido Arqueiro em rota) e uma morte por ficar parado perto do spawn de Lobo sem lutar
  de volta (P2-12) — ambas com relogin automático confirmado funcionando (`onGameEnd` → espera
  5s → `EnterGame.doLogin()` de novo), sem intervenção manual.
- **`safeLogout()`**: usado com sucesso ao fim das sub-sessões que terminaram por timeout
  controlado (não por morte/kill -9) — sem erro.
- **Conta `kitqa2`**: mantida no banco (não apagada) para a rodada 6 continuar — personagem "Kit
  QA Dois", L1, 50 XP, HP 150/150, chakra 110/110, posição salva (1029,1042,7) — no templo,
  pronta pra tentar de novo a rota até os NPCs (agora com o limiar de fala corrigido, ver P2-13)
  sem precisar refazer o combate/chakra já medidos.
- **Bug de script corrigido em andamento** (não do jogo): `findNearest()` quebrava com
  `attempt to index local 'cp' (a nil value)` quando `creature:getPosition()` retornava nil para
  uma criatura já removida da lista de espectadores — corrigido nas fases C/D com `pcall` em
  volta de `getName()`/`getPosition()`.

## Screenshots

Em `screenshots/`, prefixo `playtest5_` (7 no total, bem abaixo do limite de 40):
`playtest5_01_spawn.png` (kit + stats confirmados no 1º login), `playtest5_02_bosque_norte.png`
(chegada no spot de Lobo, antes do teste de chakra), `playtest5_04b_spawn2.png`/
`playtest5_04c_spawn3.png` (relogins após as duas mortes), `playtest5_05_quadro.png` (tentativa
de diálogo no Quadro de Missões, ~4 tiles de distância — ver P2-13),
`playtest5_06_rin_missao.png` (idem, Capitã Rin), `playtest5_07_ichiro_trade.png` (idem,
Ichiro). Originais em `~/Library/Application Support/shinobi/.shinobi/*.png` apagados ao final
(só os meus, prefixo `playtest5_` — os de outras rodadas/agentes, `autotest_*`/`valid4_*`/
`playtest2_*`/`som_timeout.png`, não foram tocados).

## Espaço em disco

| Momento | Livre em `/System/Volumes/Data` |
|---|---|
| Antes da sessão | 16 GB |
| Durante (checagens intermediárias) | 15-14 GB |
| Depois da sessão (após limpeza de screenshots e `shinobirc.lua`) | 14 GB |

Variação pequena (~2 GB, majoritariamente logs/screenshots temporários já limpos) — sempre bem
acima do limiar de 1,5 GB da regra de disco. Nenhum sinal de ENOSPC em nenhum momento.

## Para o usuário / próxima rodada (r6), em ordem de impacto

1. **P1-5 (morte por Bandido Arqueiro em rota) é o achado de maior impacto desta rodada** —
   considerar reduzir o alcance de agressão a distância do `bandit_archer` ou afastar a rota
   natural vila→Trilha dos Lobos/Bosque Norte do spawn da Clareira Central (1070,1040).
2. **Corrigir/confirmar o limiar de fala com NPC** no próximo script de QA (P2-13) — é a
   pendência nº 1 de metodologia, bloqueou missão/tarefa/diária/loja por completo nesta rodada.
3. Retomar de onde esta rodada parou: personagem "Kit QA Dois" já no templo (1029,1042,7), L1,
   50 XP, HP/chakra cheios — a rota vila→Bosque Norte via Portão Leste com x≈1055 (evitando a
   Clareira Central) já está validada, e o teste de chakra/cooldown já está fechado (não precisa
   repetir) — focar em fechar missão/tarefa/diária/loja e avançar L2-L10.
4. Medir de verdade Campina Oeste (bandidos) e Clareira do Riacho (cobras) para o bloco L5-10,
   com a folga de distância aprendida no item 1.
5. Considerar se o achado do chakra (nunca seca no L1) é intencional — se não for, o lever mais
   direto é revisar `chakra_cost_percent` especificamente para o nível 1 (o resto da tabela do
   relatório v5, L5+, não foi tocado por este achado).
6. P2-11 (referência de personagem trocada após relogin) é um bug de cliente de baixo nível,
   fora do escopo desta missão, mas vale registrar para quem for revisar
   `ProtocolGame::parseCreatureOutfit` em `client-otc/src/client/`.
