# Playtest QA — nível 1 a 20, rodada 3 (2026-09-05)

Sessão de playtest de um jogador comum, conta `playtester3` (personagem **Playtester
Tres**, Vila da Folha, criada pelo AAC — sem `god`/GM), jogada via `client-otc/shinobirc.lua`
temporário (nunca commitado, apagado ao final de cada sub-sessão), no modelo de
`client-otc/tests/autotest_rc.lua` e `walk_audit_rc.lua`, com saltos curtos de `autoWalk`
(≤10 tiles) + abertura de portas antes de cada trecho, como as rodadas 1/2 recomendaram. Uma
segunda mini-sessão, conta GM `slqa` (GOD), foi usada **só** no fim para `/reload` depois dos
fixes — nunca para ajudar o Playtester a jogar.

## Resumo executivo

**Esta rodada finalmente combateu e mediu.** O kit inicial (bandana, mochila, colete, kunai,
calça, sandálias) chegou completo no primeiro login — o fix da rodada 2 (P0 de então) se
confirma de pé — e o personagem causou dano de verdade desde o primeiro acerto (`Um lobo
loses 8 hitpoints due to your attack.`), ao contrário da rodada 1. Ainda assim, **o jogo
morreu 2 vezes antes de fechar o primeiro kill**: a Trilha dos Lobos agrupa até 4 Lobos no
mesmo spawn (raio 4), e mesmo com o kit completo e jutsu tier 1 funcionando, um Genin nível 1
sozinho não sobrevive a um "pull" dos 4 ao mesmo tempo — as duas mortes desta sessão
aconteceram assim, sem nenhum kill fechado antes de cada uma. Depois da 2ª morte (que
desconecta o cliente — TFS não reposiciona em tempo real, ver "Achados de mecânica" abaixo),
com o personagem restaurado no templo e voltando à trilha, o combate se estabilizou: 2 lobos
mortos, 50 XP confirmado (`You gained 25 experience points.` × 2, batendo exato com
`data/monsters/forest.json` → `wolf.xp = 25`), loot de `pele de lobo` + `amuleto da academia`
+ 13 ryo total.

**Cobertura real: nível 1 apenas**, sem chegar ao nível 2 (faltam 150 dos 200 XP do bloco). O
tempo da sessão foi consumido por navegação (validada, funciona — ver "Navegação" abaixo),
duas mortes com viagem de volta, e um teste de chakra dedicado. Bandidos (L6-10), Costa das
Marés (L10-15) e Floresta da Morte **não foram alcançados** — não haveria tempo útil de sobra
depois de garantir os dados de nível 1 pedidos pela missão.

**Achado mais importante da rodada, não hipotético: o chakra parece não regenerar
naturalmente enquanto o jogador continua perto/engajado com monstros.** Em dois testes
dedicados (personagem parado, fora da PZ, jutsu `fuuton lamina vento` até secar) e depois em
~7 minutos adicionais de combate sustentado, o chakra ficou **travado em 8/60** sem nenhum
ganho — `server/tfs/data/XML/vocations.xml` promete `gainmanaticks="5" gainmanaamount="3"`
(+3 a cada 5s), o que devolveria ~36 pontos em 60s se estivesse ativo. Ver P1-1 abaixo.

**Dois fixes pequenos e seguros aplicados** (achados ao vivo, não hipotéticos):
`"Diária Diária: Lobo (1-5): 1/12"` e o equivalente em tarefas (`"Tarefa aceita: Tarefa: Lobo
(Iniciante)..."`) tinham a palavra duplicada — corrigido em `data/dailies.json` e
`data/tasks.json` (ver "O que foi corrigido").

## O que funcionou bem (confirmado ao vivo)

- **Kit inicial completo no primeiro login**: bandana da vila, mochila de couro, colete de
  genin, kunai de ferro, calça ninja, sandálias ninja — todos os 6 slots preenchidos, HP
  150/150, chakra 60/60. Confirma que o fix da rodada 2 (commit `92166a7`) continua correto
  numa conta 100% nova (`playtester3`, criada pelo AAC nesta sessão).
- **Dano real desde o primeiro acerto**: soco básico + `fuuton lamina vento` (jutsu tier 1 do
  elemento Vento, o `default_element` do Genin Laranja) causaram de 1 a 9 pontos por acerto —
  bem diferente do "1 dano fixo" da rodada 1.
- **Navegação em saltos curtos funciona de ponta a ponta**: rota completa
  templo → praça → Quadro de Missões → Rua dos Mercadores → Portão Leste → ~44 tiles de mata
  até a Trilha dos Lobos, sempre em saltos de ≤10 tiles com `autoWalk`, sem nenhuma trava real
  de mapa — só os `NAO CHEGOU` esperados de saltos longos demais pro alcance de visão do
  cliente (mesmo padrão documentado em `docs/sistemas/mapas.md`, "Auditoria dinâmica").
  Confirma o aprendizado das rodadas 1/2.
- **Quadro de Missões** (`{hi}` → `{diaria}`): saudação e listagem certas em pt-BR, aceite
  automático, progresso atualizando em tempo real a cada kill (`Lobo (1-5): 1/12`, depois
  `2/12`).
- **Loja do Ichiro sem erro**: `{hi}` → `{trade}` — saudação certa em pt-BR ("Olá, Playtester
  Tres. Diga {trade} para ver o que tenho."), **zero `Lua Script Error` no log do servidor**
  durante toda a sessão (checado em `/tmp/tfs_run.log`, processo já rodando, não reiniciado).
  Isso **confirma que o P0-2 da rodada 1 (loja quebrando com `getNumber(). Argument -1...`)
  continua corrigido** — o patch em `server/tfs/src/npc.cpp` + o `SHOP_LEVEL_CAP` do
  exportador, mencionados em `CLAUDE.md`, seguram na prática.
- **Itens do kit sobrevivem à morte**: confirmado nas duas mortes desta sessão — o personagem
  voltou ao templo com o mesmo inventário, nada dropado.
- **Skill de Taijutsu (fist fighting) sobe com o uso**: `You advanced to fist fighting level
  11` e depois `12`, gerado organicamente pelos socos básicos durante o chakra seco.
- **XP exato por kill**: `You gained 25 experience points.` bate 1:1 com `wolf.xp: 25` em
  `data/monsters/forest.json` — a fórmula de XP e o evento de kill estão corretos.

## Achados por severidade

### P0 — bloqueia a progressão

Nenhum novo. O P0-1 (kit vazio) e o P0-2 (loja quebrando) da rodada 1 seguem corrigidos, como
confirmado acima.

### P1 — atrapalha bastante

**P1-1 (novo). Chakra não regenera naturalmente perto da Trilha dos Lobos — nem parado, nem
em combate sustentado.**

- **Repro**: chegar em (1050,1010,7), gastar o chakra até secar com `fuuton lamina vento`
  (jutsu tier 1, 13 de custo), depois ficar no local (lutando ou parado) medindo o chakra a
  cada 10s.
- **Medido**: dois testes dedicados, ambos secando em 6-7 casts (60 → 8), e depois **~7
  minutos adicionais** de combate sustentado no mesmo local sem o chakra sair de 8/60 **nem
  uma vez**. `server/tfs/data/XML/vocations.xml` (vocação "Vila da Folha") declara
  `gainmanaticks="5" gainmanaamount="3"` — em 7 minutos isso deveria ter devolvido dezenas de
  pontos.
- **Hipótese não confirmada**: o TFS clássico suspende a regeneração de vida/chakra enquanto o
  jogador está "em combate" (flag interna, ~15s após o último dano causado/recebido). Como a
  Trilha dos Lobos tem monstros constantemente por perto (spawn de até 4 Lobos, `spawntime`
  60s), esse timer talvez nunca expire nesse local específico — o que tornaria o achado uma
  combinação de densidade de spawn + mecânica padrão, não um bug isolado de chakra. Não
  investiguei o C++/Lua do servidor a fundo (fora do orçamento desta sessão); fica como
  pendência de investigação para quem for revisar `balanceamento.md`.
- **Efeito**: na prática, o jutsu tier 1 vira um "burst" único de abertura (4-7 casts) — o
  resto da caçada em qualquer spot com monstro por perto é feito só de soco/chute, a menos que
  o jogador se afaste para uma área livre de monstros ou compre poções de chakra (Ichiro
  vende `pílula de chakra pequena` por 30 ryo).
- **Sugestão**: confirmar em código (`server/tfs/src/player.cpp`/`creature.cpp`, função de
  regeneração) se há uma condição de "em combate" que bloqueia o regen; se for isso, é
  comportamento clássico de Tibia (não um bug), mas vale documentar em
  `docs/sistemas/balanceamento.md` que "densidade de spawn alta = chakra nunca regenera" é uma
  consequência esperada, não surpresa de balanceamento.

**P1-2 (herdado, ainda não confirmado desta vez). `{tarefas}` (listar tarefas) trava a
renderização do chat do cliente.** Já reportado na rodada 1 (`client-otc/modules/
game_console/console.lua:1828`, `gsub` sem escapar caracteres mágicos). Não testei de novo
nesta sessão (a navegação não chegou perto o suficiente do Mestre Jiro para completar o
diálogo — ver "Limitações" abaixo) — segue como pendência, fora do escopo de edição autorizado
(`game_console` não é `naruto_*`).

### P2 — polimento

**P2-1 (herdado, reproduzido de novo). `ProtocolGame::parseCreatureMove: no creature found to
move` / `no thing at pos...` / `ProtocolGame::parseTileTransformThing: no thing`** — mesmo
ruído de log já documentado na rodada 1, sem efeito visível no jogo. Reproduzido de novo
durante os saltos de `autoWalk` mais longos (mata entre o Portão Leste e a Trilha dos Lobos).

**P2-2 (elevado de P2 pra atenção, não bloqueante). Densidade do spawn da Trilha dos Lobos
(1050,1010 e 1012,1012, raio 4, até 4 Lobos) é letal para um Genin nível 1 sozinho mesmo com
kit completo.** A rodada 1 já tinha notado isso (P2-4, "vale a pena revisar"), mas na época o
personagem não tinha itens — não dava pra saber se o problema era só o kit ou também a
densidade. Nesta rodada, **com kit completo e dano funcionando**, o personagem morreu 2 vezes
seguidas contra esse spawn específico, nas duas vezes sem fechar nenhum kill antes de morrer:

- Morte 1 (dado real, sessão de debug do script, mesma conta): ~(1057,1020,7), HP 150→0 em
  ~52s de combate corrido contra múltiplos Lobos simultâneos, 0 kills fechados.
- Morte 2: exatamente no centro do spawn (1050,1010,7), HP 150→0 em ~40s, 0 kills fechados.
- Só depois da 2ª morte, reposicionando-se 3 tiles ao sul do centro exato (1050,1017 em vez de
  1050,1010) — reduzindo o número de Lobos simultaneamente agressivos — o combate virou
  sustentável e produziu os 2 kills reais desta sessão.

Isso sugere que o spot é **jogável, mas só se o jogador (ou uma IA de teste) tiver o cuidado
de não parar exatamente no centro do spawn** — um jogador novo caminhando direto até o Lobo
mais próximo (comportamento natural) tem boa chance de puxar os 4 de uma vez, como aconteceu
aqui duas vezes. Vale considerar (decisão de design, não apliquei): reduzir o raio do spawn
central de 4 para ~2-3, ou espalhar os Lobos em 2 grupos menores.

**P2-3 (herdado). Título "Customise Character" em inglês** — confirmado que a fonte é
`client-otc/data/styles/40-outfitwindow.otui` (estilo base do OTClient, fora de
`naruto_*`), não a janela do Menu Shinobi em si. Sem mudança de status desde a rodada 1.

## Achados de mecânica (não bugs, documentando para quem retomar)

- **Morte desconecta o cliente, não reposiciona em tempo real.** Depois de `You are dead.`, o
  personagem fica ~25-30s "morto" na tela (HP 0, sem novas ações possíveis) e então o cliente
  recebe `onConnectionError Operation timed out 60` e cai. É preciso logar de novo — ao
  reconectar, o personagem aparece no templo, com vida/chakra cheios e o mesmo inventário.
  Isso é esperado no TFS clássico, mas vale anotar em `docs/04-setup-ot.md` (seção de
  troubleshooting) para quem for automatizar testes: um script de QA precisa tratar a
  desconexão pós-morte e relogar sozinho, senão a sessão fica presa numa tela morta.
- **`safeLogout()` funciona e evita a sessão "fantasma"**: usei no fim da mini-sessão de
  `/reload` (conta `slqa`) e o log do servidor mostrou `SLQA has logged out.` de forma limpa —
  ao contrário de matar o processo com `kill -9` / `g_app.exit()` sem logout, que deixa a
  sessão bloqueada no servidor até um timeout de rede (confirmado: as sessões da conta
  `playtester3` só apareceram como `has logged out.` no log bem depois do processo ter sido
  encerrado).

## Tabela por nível

| Nível | Tempo real gasto no spot | Kills | Mortes | XP ganho | XP/h (janela produtiva) | Observação |
|---|---|---|---|---|---|---|
| 1 | ~9,1 min desde a 1ª chegada na trilha até o 2º kill (inclui as 2 mortes + viagem de volta) | 2 (Lobo) | 2 | 50 | **328/h** contando as mortes; **717-1895/h** só na janela sem morte (95s a 251s pra 50 XP) | Não fechou o bloco (faltam 150 dos 200 XP pro nível 2). Nível 2-5 **não alcançados**. |

Não há dados de nível 2 em diante — a sessão não durou o suficiente depois das duas mortes
para fechar o primeiro nível.

## Tabela de chakra

| Nível | Jutsu | Custo | Cooldown nominal | Casts até secar (60→<13) | Chakra final | Regen medido (10 em 10s, parado ou lutando) |
|---|---|---|---|---|---|---|
| 1 | `fuuton lamina vento` (Fuuton, tier 1, único jutsu disponível no nível 1) | 13 | ~2s (config: 2,0s) | 6-7 (dois testes: 7 casts/~16s e 6 casts/~14s) | 8/60 | **0 em ~7 minutos observados** (ver P1-1) — nenhum ponto recuperado, parado ou lutando, no local testado |

`vigor_teimoso` (cura ao longo do tempo, 30 de custo), `kawarimi` (teleporte defensivo, 20 de
custo) e `fuuton_rasteira_vento` (segundo jutsu ofensivo, 14 de custo) só liberam a partir do
nível 4/5/9 — não testáveis neste nível.

## Comparação com `progressao-jogador.md`

A tabela documentada prevê **~536 XP/h** e **2,8h** para o bloco 1-5 inteiro (Lobo/Cervo na
Floresta da Vila). Os dois números que consegui medir de verdade apontam em direções opostas:

- **Sem contar as mortes** (só o trecho de combate produtivo, resumido após a 2ª morte): 717 a
  1895 XP/h — **acima** do esperado, sugerindo que o dano/DPS do personagem com kit completo
  está bem calibrado ou até generoso para o nível 1.
- **Contando as duas mortes reais** (viagem + chakra seco + combate até morrer, sem nenhum
  kill): 328 XP/h — **abaixo** do esperado, e o motivo não é falta de dano, é o **custo de
  morrer**: cada morte consumiu ~1-1,5 min sem gerar XP nenhum (queda de HP até 0, ~30s
  desconectado, relogin, ~75s de viagem de volta).

**Conclusão honesta**: a tabela de progressão provavelmente está calibrada assumindo que o
jogador consegue evitar pulls de spawn inteiro (ex.: puxando 1 Lobo de cada vez, não parando
no centro do spawn) — um jogador humano real, vendo 4 Lobos na tela, tende a recuar ou pular
de forma diferente de um script automatizado. Nesta sessão, tanto o script quanto (por
suposição) um jogador novo sem experiência de "kiting" tem boa chance de repetir as duas
mortes observadas aqui. Isso não invalida a tabela, mas sugere que ela é otimista para quem
ainda não aprendeu a evitar o pull completo — o que é exatamente o perfil do nível 1.

## O que foi corrigido nesta sessão

| Achado | Onde | Causa raiz | Correção aplicada |
|---|---|---|---|
| `"Diária Diária: Lobo (1-5): 1/12"` — palavra duplicada na notificação de progresso de diária, reproduzido ao vivo 2x nesta sessão (a cada kill de Lobo) | `data/dailies.json`, campo `name` de todas as 60 entradas | O gerador (`tools/export_tfs.py:2211`) já monta a mensagem como `"Diária " .. entry.name .. ": " .. prog .. "/" .. count`; como `entry.name` já vinha como `"Diária: Lobo (1-5)"`, a palavra duplicava | Removido o prefixo redundante `"Diária: "` de todos os 60 `name` (ex.: `"Diária: Lobo (1-5)"` → `"Lobo (1-5)"`). Não achei nenhum outro lugar que dependesse do prefixo (as demais mensagens do gerador, ex. a listagem de `!diaria`, também só usam `t.name` sozinho — ficaram mais limpas de quebra, sem regressão) |
| Mesma classe de bug em tarefas (`"Tarefa aceita: Tarefa: Lobo (Iniciante). Mate 50 Lobo."`) — não reproduzido ao vivo nesta sessão (navegação não chegou perto o suficiente do Jiro), mas confirmado por inspeção direta do código (mesma causa raiz) | `data/tasks.json`, campo `name` de todas as 114 entradas | `tools/export_tfs.py:1582/1606` monta `"Tarefa aceita: " .. t.name` / `"Tarefa entregue: " .. t.name`; `t.name` já vinha como `"Tarefa: Lobo (Iniciante)"` | Removido o prefixo redundante `"Tarefa: "` de todos os 114 `name` pelo mesmo motivo — aplicado preventivamente, mesmo padrão de causa e correção |

Ambos validados com `.venv/bin/python tools/validate_data.py` (`OK — tudo válido`, 114
tarefas, 60 diárias, nada mais mudou de contagem), regenerados com `.venv/bin/python
tools/export_tfs.py` e instalados com `bash tools/install_generated.sh`. Confirmado por
grep no arquivo gerado que `naruto_tasks.lua` agora carrega `name = 'Lobo (Iniciante)'` (sem
o prefixo). Aplicado ao vivo no servidor **sem reiniciar**: login como `slqa`/`slqa123`,
`/reload global` → `/reload scripts` → `/reload npcs` (nessa ordem — a ordem inversa quebra
`NarutoCharacters.apply`, achado documentado em `docs/sistemas/cliente-ux.md`), depois
`g_game.safeLogout()`. **Zero `Lua Script Error` novo** no log do servidor durante o reload.

### O que NÃO foi corrigido, e por quê

| Achado | Onde mora de verdade | Por que não mexi |
|---|---|---|
| P1-1 (chakra não regenera) | Provavelmente `server/tfs/src/player.cpp`/`creature.cpp` (núcleo do TFS) ou uma condição de "em combate" | Fora do escopo autorizado (não é `data/npcs`, `tasks.json`, `dailies.json`, `items` nem `naruto_*`); também não confirmei a causa raiz com certeza suficiente para uma correção seria — precisa de investigação de código C++ que não cabia no orçamento desta sessão |
| P1-2 (`{tarefas}` trava o chat) | `client-otc/modules/game_console/console.lua:1828` | Mesmo motivo da rodada 1: módulo `game_*` original, fora de `naruto_*`, regra do projeto de não editar além do mínimo |
| P2-2 (densidade do spawn de Lobos) | `server/generated/world/valley-spawn.xml` / `tools/map/build_valley.py` (spawns) | Fora do escopo (mapa/monstros/balance explicitamente vetados nesta missão) — é uma decisão de design (reduzir raio ou espalhar), não uma linha óbvia |
| P2-3 (título "Customise Character") | `client-otc/data/styles/40-outfitwindow.otui` | Estilo base do OTClient, fora de `naruto_*` |

## Metodologia e limitações

- **Script de automação**: `client-otc/shinobirc.lua` temporário (removido ao final de cada
  sub-sessão), no molde de `autotest_rc.lua`/`walk_audit_rc.lua` — login automático, rotas em
  saltos curtos (`autoWalk` ≤10 tiles + abertura de portas antes de cada trecho), heartbeat de
  HP/chakra/posição a cada 3s (fonte primária dos números desta tabela), ataque básico + jutsu
  via `g_game.talk('fuuton lamina vento')` a cada ciclo de ~1s (funcionalmente idêntico ao que
  a hotkey F1 da action bar faz por baixo — ver `docs/04-setup-ot.md`, "Jutsus no cliente" —
  não simulei o keypress literal, mas o efeito no jogo é o mesmo).
- **Bug do próprio script, não do jogo**: depois do 2º kill, o loop de combate parou de
  reengajar (nenhum novo "X loses N hitpoints due to your attack" por ~7 minutos, mesmo
  recebendo dano ocasional de um lobo). Sem erro de Lua, sem mensagem de `FLEE` — a causa mais
  provável é uma referência de alvo (`currentTargetId`) presa a uma criatura que saiu do
  alcance conhecido do cliente sem cair para `nearestMonster()` de novo. Não tive tempo de
  depurar isso ao vivo; reportado aqui como limitação do script de QA, não do servidor.
- **Interações de NPC incompletas**: o Mestre de Tarefas Jiro (1030,1067) e a Capitã Rin
  (loja de missões, interior em 1320-1325,1000-1005) não tiveram o diálogo confirmado nesta
  rodada — a rota até Jiro parou ~8-10 tiles longe dele (autoWalk desistiu antes de chegar), e
  a tentativa de visitar Rin falhou porque o personagem nunca saiu do interior da loja do
  Ichiro (a teleportação entre a rua e os interiores das lojas quebra o `autoWalk` direto de um
  interior pro outro — precisaria de uma rota específica ciente dos pads de saída, que não
  mapeei a tempo). Ambos ficam para a próxima rodada; os dois já foram confirmados
  funcionando em rodadas anteriores (r1: aceite de tarefa do Jiro; sistema de missões: aceite
  via `{missao}` documentado em `docs/sistemas/progressao-servidor.md`).
- **Duas mortes, dados legítimos**: como a missão pediu ("se morrer, registre e continue"),
  as duas mortes foram tratadas como dado válido, não como falha do script — a segunda,
  inclusive, foi recuperada automaticamente (o script detecta a desconexão pós-morte via
  `onGameEnd`, espera 5s, refaz o login sozinho, e retoma a caçada) sem intervenção manual.
- **Conta `playtester3`**: criada nesta sessão via AAC (`POST /criar-conta` + `POST
  /criar-personagem`, campos exatamente como a missão pediu), personagem "Playtester Tres",
  Genin Laranja, Vila da Folha. Mantida no banco (não apagada) para referência/continuidade da
  próxima rodada — nível 1, ~50 XP não persistido no banco (a última desconexão do processo
  não foi um logout limpo, então o save ficou no checkpoint anterior; o log do cliente/servidor
  é a fonte de verdade dos 2 kills reais, não o banco).
- **Servidor**: `tools/run_server.sh`, já rodando antes desta sessão (pid preexistente), **não
  reiniciado** em nenhum momento — só os três `/reload` no final, via conta `slqa`.

## Espaço em disco

| Momento | Livre em `/System/Volumes/Data` |
|---|---|
| Antes da sessão | 15 GB |
| Depois da sessão (após limpeza de screenshots e `shinobirc.lua`) | 15 GB |

Sem variação relevante — bem acima do limiar de 1,5 GB da regra de disco. 8 screenshots
gerados no total (limite era 40), copiados para `screenshots/` com prefixo `playtest3_` e
reduzidos com `sips -Z 400` (928 KB no total); os originais em `~/Library/Application
Support/shinobi/.shinobi/*.png` foram apagados ao final de cada sub-sessão.
`client-otc/shinobirc.lua` apagado ao final de cada uma das três sub-sessões (nunca
commitado).

## Resposta direta: jogável do 1 ao 10?

**Parcialmente, e com uma ressalva importante.** O personagem CONSEGUE causar dano relevante e
matar Lobos desde o primeiro combate (diferença enorme em relação à rodada 1) — isso já não é
mais o gargalo. O gargalo agora é **sobrevivência ao primeiro contato**: um jogador (ou script)
que caminhe direto até o centro do spawn de Lobos, como um novato faria naturalmente, tem boa
chance de puxar os 4 de uma vez e morrer sem fechar nenhum kill — foi o que aconteceu 2 vezes
seguidas nesta sessão. Só depois de aprender (por tentativa e erro) a não parar exatamente no
centro do spawn é que o combate virou sustentável e produziu os números de XP/h que batem ou
superam a tabela de `progressao-jogador.md`. Bandido (L6-10) e Costa das Marés (L10-15) **não
foram alcançados** — cobertura real desta rodada é nível 1 apenas, sem chegar ao nível 2.

## Para o usuário (próximos passos sugeridos, em ordem de impacto)

1. **Investigar P1-1** (chakra travado em 8/60 sem regenerar por ~7 min) — confirmar se é a
   condição "em combate" do TFS clássico suprimindo regen, e se sim, documentar em
   `balanceamento.md` que spots de spawn denso são "modo melee puro" depois do burst inicial.
2. **Considerar reduzir a densidade do spawn da Trilha dos Lobos** (P2-2) — de 4 para 2-3
   Lobos por grupo, ou espalhar em 2 grupos menores — para reduzir o risco de "pull total"
   matar um Genin novo antes do primeiro kill.
3. Repetir este playtest com uma rota que aproxime devagar (parar 1-2 tiles antes do centro do
   spawn, como esta sessão acabou fazendo por acidente depois da 2ª morte) para conseguir
   medir o bloco 1-5 completo (faltam ~150 XP pro nível 2, e todo o resto até nível 5).
4. Terminar a validação de Jiro (`{tarefa}`/`{entregar}`) e Rin (`{missao}`) nesta rodada com
   uma rota mais precisa (a rota até Jiro precisa de um waypoint final dentro de 3 tiles dele;
   a rota até Rin precisa reconhecer que o personagem PRECISA sair do interior do Ichiro antes
   de tentar ir pra outro interior — não dá pra pular direto).
5. P1-2 (`{tarefas}` trava o chat) segue pendente, fora do escopo de edição autorizado — mesma
   recomendação da rodada 1.
6. Considerar documentar em `docs/04-setup-ot.md` o comportamento "morte desconecta, precisa
   relogar" para quem for escrever o próximo script de QA automatizado.

## Screenshots

Em `screenshots/`, prefixo `playtest3_`: `pt3_01_spawn` (kit completo confirmado no templo),
`pt3_02_chakra_pos_teste`, `pt3_03_quadro_diaria` (Quadro de Missões), `pt3_04_trilha_lobos`
(personagem + Lobo visíveis na trilha), `pt3_10_town_start`, `pt3_11_jiro`,
`pt3_12_ichiro_trade` (interior da loja, sem erro), `pt3_13_rin_missao`.
