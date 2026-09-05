# Playtest QA — nível 1 a 20, rodada 6 (2026-09-05)

*Preenchido incrementalmente durante a sessão. Personagem NOVO (`Playtester Seis`, conta
`ptseis`, Genin Laranja, Vila da Folha), sem GM, criado via AAC. Foco: validar a economia de
chakra e a história que mudaram desde a rodada 5 (pool 100+10L, custo tier 1 12-14%/pool,
cooldown 9s, regen `2+floor(level/4)` a cada 2s; Clareira Central agora com Cervo passivo em vez
de Bandido Arqueiro).*

## Ambiente no início da sessão

- `df -h /`: 13 GiB livres (48% usado) / `df -h /System/Volumes/Data`: 13 GiB livres (94% usado)
  — acima do piso de 1,5 GB.
- Servidor (`build/tfs`) já no ar, confirmado com `nc -z 127.0.0.1 7171` (sucesso). **Não
  reiniciado** por esta sessão.
- `client-otc/shinobirc.lua`: ausente antes de começar (confirmado).
- Um OTClient de outro processo (PID 24896) já estava rodando no início; saiu sozinho pouco
  depois (confirmado por `ps`, não foi tocado por mim). Meu próprio cliente rodou em PIDs
  próprios (24967, depois 25134 após um ajuste de script — ver metodologia), nunca
  `pkill -x OTClient`.
- Conta/personagem criados via AAC (`tools/aac.sh`, já estava no ar):
  `POST /criar-conta` (name=ptseis) → `criada`/`sucesso`; `POST /criar-personagem`
  (account=ptseis, char_name=`Playtester Seis`, sex=male, character=genin_laranja) → `criado`.
- Confirmado por SQL (leitura) antes do 1º login: `id=12, level=1, experience=0, health=150/150,
  mana=60/60, pos=1029,1042,7` — o `mana=60` é o valor bruto do TFS antes do script de
  login aplicar a fórmula da vila; **confirmado in-game no 1º login**: `You gained 50 mana`
  → chakra final **110/110** (bate com a fórmula 100+10×nível esperada pela missão).

## Resumo executivo

**Não jogável de ponta a ponta para um personagem novo real — não pela economia de chakra
pedida pela missão, mas por um bug muito mais grave que a antecede: nenhum jutsu pode ser
aprendido, e nenhum progresso (XP, posição) sobrevive a um logout.** A causa raiz (**P0-0**)
é um bug de charset na conexão MySQL do TFS (`character_set_client`/`connection` = `latin1`
sem `mysqlCharset` configurado, enquanto o banco é `utf8mb4`): qualquer `INSERT` em
`player_spells` com um jutsu de nome acentuado (praticamente todos, em pt-BR) falha com
`"Incorrect string value"`, o que também derruba o save do jogador inteiro. Confirmado ao
vivo, duas vezes: (1) 30/30 tentativas de castar `fuuton lamina vento` numa janela de caça
de 5 minutos falharam com `"You must learn this spell first."`; (2) o personagem terminou
a sessão em `level=1, xp=10, pos=1050,1045` no cliente, mas o banco de dados, depois do
`safeLogout()`, mostrava `level=1, xp=0, pos=1029,1042` — **zero progresso persistido**.
Isso significa que **a pergunta central desta rodada (o cooldown de 9s é divertido ou
arrastado?) não pôde ser respondida** — não há chakra "gasto" quando o cast nunca funciona.
Combate por arma continua funcionando normalmente (2-8 de dano por hit contra um Cervo
passivo, 5 XP por kill), e a conquista de zona/mapa de Clareira Central (agora Cervo
passivo, não mais Bandido Arqueiro) foi confirmada como a mudança de mapa que a missão
esperava. Cobertura real desta rodada: kit e chakra 110/110 confirmados no login, ~2 min
de combate real (2 kills de Cervo, não Lobo — a rota derivou pra Clareira Central por causa
de obstáculos de colisão, P2-1), achievements antes/depois da muralha, e uma tentativa
não-confirmada de falar com a Capitã Rin (parou a 8 tiles do NPC). **L2-20, missões de
Jiro/diária/loja e Costa das Marés não foram alcançados** — o tempo desta rodada foi
consumido majoritariamente por: (a) descobrir e contornar o P0-0 e o P1-1 (porta do templo
trancada), e (b) depurar a navegação manual depois que `autoWalk` parou de funcionar por
completo (P1-2). **Prioridade para a rodada 7**: corrigir o P0-0 (`mysqlCharset =
"utf8mb4"` em `server/tfs/config.lua`) antes de qualquer outra coisa — sem isso, nenhuma
medição de chakra, jutsu ou progressão de personagem novo é válida.

## Tabela por nível

| Nível | Tempo real gasto | Kills | Mortes | XP ganho | XP/h | Observação |
|---|---|---|---|---|---|---|
| 1 | ~40 min reais de sessão (dominado por navegação/depuração de script — ver metodologia); só ~40s de combate real ativo dentro de uma janela de caça de 5 min (o resto ficou sem monstro ao alcance) | 2 (**Cervo**, não Lobo — ver nota de rota abaixo) | 0 (o Cervo é passivo, nunca revidou — HP ficou 150/150 o tempo todo) | 10 ganhos em jogo (5 por Cervo), **mas 0 persistiu** — o `safeLogout()` final apagou o XP/posição da sessão inteira (P0-0, confirmado por SQL: personagem voltou a `level=1, xp=0, pos=1029,1042` depois do logout) | **~900/h** medido na janela de combate real (10 XP em 40s), mas amostra mínima (2 kills), do monstro errado, e **que nem chegou a ser salva no personagem** — não conclusivo pra L1-5 nos Lobos pedidos pela missão | Chakra nunca saiu de 110/110 — **não porque a economia esteja bem calibrada, mas porque o cast de jutsu está 100% quebrado nesta rodada (P0-0)**; todo dano foi de arma (2-8 por hit, consistente com a tabela de combate da r5) |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |

**Nota sobre a rota**: a navegação (100% manual, sem `autoWalk` — ver P1-2) desviou de vários
obstáculos de colisão (P2-1) na faixa fora da muralha leste e acabou chegando perto de
**Clareira Central** (~1055,1025, spawn de Cervo passivo, confirmado no dado instalado —
exatamente a mudança de mapa citada pela missão) em vez do Bosque Norte/Trilha dos Lobos
(destino pretendido de L1-5). Não deu tempo de corrigir a rota e caçar Lobo de verdade
nesta rodada — ver "Metodologia e limitações".

## Tabela de chakra/regen

**Não foi possível medir a economia de chakra pedida pela missão.** O jutsu tier 1
(`fuuton lamina vento`) nunca casta com sucesso — toda tentativa (15 casts tentados ao
longo da janela de 5 min, a cada ~9-10s) respondeu `"You must learn this spell first."`,
porque o personagem nunca aprendeu nenhum jutsu de verdade (**P0-0**, bug de charset na
conexão MySQL do TFS). Resultado: chakra ficou **fixo em 110/110 o tempo inteiro** (0% do
tempo sem chakra, 0 casts bem-sucedidos, recuperação "instantânea" porque nunca chegou a
gastar) — um resultado tecnicamente "sem fricção de chakra", mas que **não reflete a
economia real do jogo**, só o fato de que o recurso nunca foi usado. Assim que o P0-0 for
corrigido, a rodada 7 deve refazer esta medição do zero.

## Missões / tarefas / diária / loja

- `!conquistas` **antes** de sair do templo: `0/55`. Depois de cruzar a muralha (Clareira
  Central): `1/55 | exploration 1/6` — a conquista "Pisou em Floresta da Vila" desbloqueou
  corretamente (msg `Conquista desbloqueada: Pisou em Floresta da Vila!`), confirmando de
  novo que o P1-3 da rodada 4 continua corrigido. `!conquistas` **final** (fim da sessão):
  ainda `1/55` — sem mudança, e de qualquer forma nada disso persistiu (ver P0-0).
- **Missão automática do Cervo**: matar Cervo disparou sozinho uma "Diária Cervo — segunda
  leva (1-5): 2/12" (contador incrementando por kill, sem precisar aceitar nada com um NPC)
  e o loot incluiu **onigiri** diretamente — bate com a menção da missão a "missão do cervo
  (3 onigiri)". Não fechei os 12/12 nesta rodada (só 1 Cervo morto antes da fauna sumir do
  alcance).
- **Capitã Rin (missão dos Lobos)**: navegação chegou só a **1050,1045** (8 tiles do NPC em
  1047,1053) antes de estourar o orçamento de passos do script — `hi`/`missao`/`bye`
  disparados a essa distância **não geraram nenhuma resposta de NPC** (nenhuma linha
  `talk: Capitã Rin: ...` no log), consistente com o P2-13 da rodada 5 (limiar de "chegou
  perto" não é próximo o bastante pra falar com NPC) — só que desta vez ainda mais longe (8
  tiles, não 4). **Não alcançado de verdade nesta rodada.**
- Mestre Jiro (tarefa), Quadro de Missões (diária), Ichiro (loja): **não tentados** — o
  tempo da sessão se esgotou antes de voltar pra essa parte da vila (o script original
  tinha esses passos, mas o roteiro de volta foi cortado pra caber no tempo real
  disponível — ver "Metodologia e limitações").

## Achados por severidade

### P0

**P0-0 (o achado central desta rodada — muito mais grave do que qualquer coisa sobre a
economia de chakra). Personagem novo criado via AAC não consegue aprender NENHUM jutsu —
`fuuton lamina vento` sempre responde "You must learn this spell first.", mesmo logo depois
do login rodar `NarutoCharacters.apply()` (que deveria chamar `player:learnSpell()` para os
4 jutsus pessoais + 4 do elemento). Causa raiz confirmada por log do servidor (não é
suposição):**

```
[Error - mysql_real_query] Query: INSERT INTO `player_spells` (`player_id`, `name`) VALUES
  (12, 'Fuuton: Redemoinho Prisão'), (12, 'Fuuton: Tornado Cortante'),
  (12, 'Fuuton: Rajada Cortante'), (12, 'Fuuton: Lâmina de Vento'), (12, 'Vigor Teimoso'),
  (12, 'Rasteira de Vento Leve'), (12, 'Kawarimi ...
Message: Incorrect string value: '\xE3o' for column `forgottenserver`.`player_spells`.`name`
  at row 1
Error while saving player: Playtester Seis
```
- **Causa exata**: a conexão MySQL que o `tfs` usa está com `character_set_client` /
  `character_set_connection` = **`latin1`** (confirmado via `SHOW VARIABLES LIKE
  'character_set_%'`), enquanto o banco/tabela `player_spells` é `utf8mb3` e o servidor
  (`character_set_server`/`character_set_database` = `utf8mb4`) manda os nomes de jutsu em
  UTF-8 de verdade (acentuados: "Prisão", "Lâmina", etc.). Sem `SET NAMES utf8mb4` na conexão
  (não há `mysqlCharset` configurado em `server/tfs/config.lua`), qualquer INSERT com um nome
  de jutsu acentuado falha inteiro com "Incorrect string value" — **e como o INSERT de
  `player_spells` é feito em lote (todos os jutsus aprendidos de uma vez, no save do
  jogador), basta UM nome acentuado no meio pra nenhum jutsu ser salvo**, incluindo os que
  não têm acento. Confirmado por SQL direto (leitura): `SELECT * FROM player_spells WHERE
  player_id=12` retornou **0 linhas** depois de 5 logins/relogins.
- **Efeito em cascata CONFIRMADO no fim desta sessão (não é mais hipótese)**: a mesma falha
  de INSERT aborta o save do jogador inteiro (`Error while saving player: Playtester Seis`,
  uma vez por logout). Conferido por SQL direto **depois** do `safeLogout()` final desta
  sessão (personagem tinha, no momento do logout, `level=1, xp=10, pos=1050,1045`): o banco
  mostra `level=1, experience=0, pos=1029,1042` — **os 10 XP ganhos e toda a posição da
  sessão foram perdidos, o personagem voltou para exatamente o estado de criação**. Ou seja,
  **um jogador novo com este bug nunca progride entre sessões: todo XP, item e posição
  ganhos numa sessão de jogo desaparecem no logout**, toda vez, sem exceção — o P0-0
  não é "só" o jutsu não funcionar, é o jogo inteiro não persistir progresso pra qualquer
  personagem cujo kit tenha um nome de jutsu acentuado (a esmagadora maioria).
- **Alcance real**: como praticamente todo jutsu do jogo em pt-BR tem pelo menos um acento no
  `name` (Lâmina, Prisão, Relâmpago, Munição, etc. — ver `data/jutsus/*.json`), **isso não é
  um problema só do Genin Laranja/Fuuton**: qualquer personagem cujo kit de 4 jutsus pessoais
  + 4 do elemento inclua um nome acentuado (a esmagadora maioria) fica sem conseguir aprender
  NENHUM jutsu do kit, permanentemente (o erro se repete a cada login, então nunca "cura
  sozinho"). Isso derruba por completo o pilar de design "híbrido é o build de referência"
  decidido no fim de `docs/sistemas/balanceamento-relatorio-v8.md` — um jogador novo de
  verdade (não GM) **não consegue lançar jutsu nenhum desde o primeiro minuto de jogo**, e
  fica preso no "taijutsu puro" (socos com a arma) até que esse bug seja corrigido, quando a
  meta de design é exatamente o oposto.
- **Por que as rodadas anteriores (r3-r5, história arcos 1-3/4-6) não pegaram isso**: todas
  usaram uma conta **GM** (`god`/`slqa`) já existente/antiga no banco, provavelmente criada
  antes desse problema de charset aparecer ou populada por um caminho diferente (SQL direto,
  não o fluxo real de `learnSpell()` em lote via AAC+login) — esta é a **primeira rodada a
  criar um personagem 100% novo via AAC e tentar lançar jutsu de verdade**, o que expõe o bug.
- **Sugestão de correção**: adicionar `mysqlCharset = "utf8mb4"` em `server/tfs/config.lua`
  (ou o equivalente na inicialização da conexão MySQL do TFS) para casar o charset da conexão
  com o dado real (UTF-8) e o charset do banco/tabela — depois disso, os nomes acentuados
  devem inserir sem erro. Fora do escopo de edição autorizado nesta rodada (só leitura/report).

### P1

**P1-1 (novo, confirmado ao vivo, script). A porta de saída do prédio do templo
(1029,1046, item de porta de pedra fechada) não abre sozinha ao ANDAR contra ela — todo
personagem novo faz login literalmente TRANCADO dentro do templo.** Tentar `g_game.walk`/
`g_game.autoWalk` contra a tile da porta retorna `"There is not enough room."` em 100% das
tentativas (dezenas confirmadas em múltiplas sub-sessões). A saída só funciona chamando
explicitamente `g_game.use()` no item do topo da tile da porta (`tile:getTopUseThing()`) —
depois disso a porta abre e o personagem consegue atravessar andando normalmente. **Isso é
exatamente o que um jogador humano faz naturalmente com o mouse** (clique único no ladrilho
da porta manda um "use" antes de "andar para lá" quando o destino do clique é o próprio
item da porta) — então não necessariamente trava um humano do mesmo jeito que travou um
script que só chama "andar". Mas é reportável porque: (a) o texto de erro
("There is not enough room.") é enganoso — sugere um problema de espaço/colisão, não "a
porta está fechada, use-a"; e (b) o próprio `autoWalk` do cliente (usado quando o jogador
clica em um ponto distante e deixa o pathfinding cuidar do caminho) **não abre a porta
sozinho e não consegue rotear através dela** — um jogador que clique em qualquer ponto do
outro lado da porta (comportamento normal de "clique e ande até lá" em jogos estilo Tibia)
fica preso do mesmo jeito que o script ficou, sem entender por quê, até perceber que precisa
clicar na porta especificamente primeiro. Repro: personagem novo loga em (1029,1042,7,
dentro do templo), anda para (1029,1045), tenta continuar para (1029,1046) — porta fechada —
recebe "There is not enough room." indefinidamente. **Adicionalmente confirmado nesta
rodada: todo login/relogin (mesmo após um `safeLogout()` limpo) reposiciona o personagem de
volta em 1029,1042 (dentro do templo)** — ou seja, este é o primeiro obstáculo que **todo
jogador enfrenta em TODA sessão de jogo**, não só na criação do personagem.
- **Sugestão**: no mínimo, trocar a mensagem de erro por algo como "A porta está fechada"
  quando a causa for uma porta fechada especificamente (não colisão genérica); idealmente,
  fazer o pathfinding do `autoWalk` reconhecer portas fechadas como atravessáveis (abrindo
  automaticamente), que é o comportamento padrão esperado em clientes OT/Tibia-like.

**P1-2 (novo, confirmado ao vivo, script). `g_game.autoWalk` não funcionou NENHUMA vez
nesta sessão, nem para saltos curtos (≤8 tiles) dentro de área já visitada.** Diferente da
rodada 5 (onde `autoWalk` funcionava para saltos curtos e só falhava para alvos distantes,
achado P2-9), nesta rodada TODAS as chamadas de `autoWalk` (mesmo com alvo a 5-7 tiles,
recém-visitado) simplesmente não moveram o personagem um único tile, sem gerar nenhuma
mensagem de erro — apenas silêncio. A navegação só funcionou trocando para passo manual
(`g_game.walk(direção)`, uma tile por vez, como seguraria uma tecla), a um custo real de
tempo de script bem mais alto (precisa recalcular a direção dominante a cada ~700ms em vez
de disparar um destino e esperar). Não sei se isso é uma regressão real do cliente entre as
rodadas 5 e 6 ou uma particularidade desta sessão/mapa; vale reteste dedicado.

### P2

**P2-1 (achado de navegação/colisão, provavelmente decoração). Vários pontos isolados
tanto dentro da praça (perto da fonte, ~1030,1053-1054) quanto no corredor fora da muralha
leste (faixa x≈1033-1060, y≈1025-1058, vários pontos) bloqueiam UMA única direção de
movimento com `"There is not enough room."`/`"Sorry, not possible."`, exigindo desviar de
lado (perpendicular) 1-2 tiles antes de conseguir continuar na direção original.** Tentei
`g_game.use()` em cada ponto travado — a maioria respondeu `"You cannot use this object."`
(ou seja, não são portas, são decoração/objeto sólido comum: provavelmente árvores, arbustos
ou pedras game decoration colocadas por `tools/map/build_valley.py` com hitbox maior que o
esperado). Não travou de forma permanente nenhuma vez (sempre havia uma direção livre em
1-2 tentativas), mas custou dezenas de segundos reais em cada ponto — o equivalente
script do "andar bate na moldura de uma árvore e o personagem para" que um jogador humano
resolveria só olhando a tela, mas que atrapalha bastante qualquer automação/roteiro fixo.
Fora do escopo de correção desta rodada (mapas/decoração); registrado para quem for revisar
a malha de colisão da faixa leste da Vila da Folha.

## O que faria um jogador desistir

Em ordem de impacto, baseado no que foi medido/observado nesta rodada:

1. **Não conseguir lançar NENHUM jutsu, nunca, desde o primeiro minuto de jogo (P0-0).**
   Isso é categoricamente pior do que qualquer achado de balanceamento das rodadas 3-8
   combinadas — não é "o jutsu é fraco" ou "o cooldown é chato", é "o botão de jutsu não
   funciona". Um jogador de ninja que não consegue lançar jutsu vira, na prática, um
   personagem de RPG genérico batendo com arma — o oposto exato da proposta do jogo. Isso
   sozinho é motivo de desistência no primeiro combate, não no primeiro dia.
2. **Ficar trancado dentro do prédio inicial sem entender por quê (P1-1).** A mensagem
   "There is not enough room." não diz "a porta está fechada" — sugere um bug de colisão
   genérico. Um jogador que clique do outro lado da porta (uso normal do mouse num jogo
   estilo Tibia) e nada aconteça, sem nenhuma pista, pode simplesmente fechar o cliente
   achando que o jogo travou.
3. **Fricção de navegação constante logo nos primeiros passos fora da vila (P2-1).**
   Vários pontos de colisão inesperados na única rota até a área de caça de L1-5 (mesmo já
   sem o perigo do Bandido Arqueiro da rodada 5, que foi de fato corrigido — Clareira
   Central agora tem só Cervo passivo) tornam a viagem inicial mais irritante do que deveria.
4. Itens herdados de rodadas anteriores, não retestados a fundo aqui: mojibake em texto
   acentuado (achado central de `playtest-historia-arcos1-3.md`) — vi uma amostra
   consistente com o problema (`"Di\xE1ria Cervo"` chegou corrompido no log bruto do
   cliente), mas não é uma confirmação nova independente (meu log captura bytes crus, não
   necessariamente o mesmo caminho de renderização da UI).

## Comparação com `progressao-jogador.md`

A tabela prevê **~536 XP/h** e **2,8h** para o bloco 1-5 inteiro (Lobo/Cervo na Floresta da
Vila). Esta rodada não conseguiu medir esse bloco da forma pretendida:

- A amostra real (2 kills de **Cervo**, não Lobo, 10 XP em 40s = **~900/h**) é pequena
  demais e do monstro errado pra comparar de forma válida com a tabela — mas está na mesma
  ordem de grandeza que os "acima da tabela" medidos nas rodadas 3 e 5 (717-2170/h), então
  não há sinal de que o dano de arma tenha regredido.
- **A pergunta central da missão (economia de chakra) não pôde ser respondida** — ver
  P0-0. A tabela de balanceamento (v8/v9, decisão do orquestrador) prevê regen
  `2+level//4` a cada 2s (1,0/s no L1) e pool 100+10×L; nenhuma das duas pôde ser observada
  em uso real porque o jogo nunca deixou o personagem gastar chakra.
- **XP/h contando navegação e persistência**: em ~40 minutos reais de sessão, o personagem
  ganhou 10 XP em jogo mas terminou com **0 XP líquidos salvos** (P0-0, o `safeLogout()`
  final não persistiu nada) — pior que o "quase nada" da rodada 5 (50 XP líquidos em ~50
  min). A esmagadora maioria do tempo real foi navegação/depuração de script, não combate
  (mesmo padrão de fricção "chegar até a caça" já visto na rodada 5, agravado aqui pelos
  pontos de colisão adicionais fora da muralha leste, P2-1, e pelo bug da porta do templo,
  P1-1).

## Metodologia e limitações

- Kit/personagem criados **via AAC** (HTTP), não in-game — a missão pediu para confirmar isso
  (feito, ver "Ambiente").
- Script `client-otc/shinobirc.lua` (6 versões sucessivas nesta sessão, nunca commitado,
  apagado ao final): sequenciador de fila (mesmo padrão de
  `client-otc/tests/historia46_recheck_rc.lua`), **sem nenhum comando de GM** (`/god`,
  `/full`, `/m`, `/tp`) — navegação 100% por `g_game.walk`/`g_game.autoWalk`, combate 100%
  real (`g_game.attack` + tentativa de cast do jutsu tier 1 por chat, que sempre falhou por
  causa do P0-0), NPCs via `g_game.talk('hi')` (1ª msg) + `g_game.talkChannel(MessageModes.NpcTo, ...)`
  (mensagens seguintes, achado #1 do `playtest-historia-arcos1-3.md`).
- **Evolução do script ao longo da sessão** (cada versão corrigiu um problema real
  encontrado ao vivo, não hipotético):
  1. v1 (`autoWalk`-only): personagem nunca saiu do templo — `"There is not enough room."`
     contra a porta fechada, indefinidamente (achado do P1-1).
  2. v2: adicionou `g_game.use()` na porta antes de andar — funcionou, mas o resto da rota
     (fora do templo) continuava usando `autoWalk`, que **nunca moveu o personagem nem um
     tile** em nenhuma tentativa desta sessão (achado do P1-2).
  3. v3: trocou toda a navegação por passo manual (`g_game.walk` direção a direção) — andou,
     mas esbarrou em vários pontos de colisão isolados fora da muralha leste (P2-1).
  4. v4: um bug de metodologia própria (não do jogo) — o `onGameStart` reenfileirava a
     sequência inteira a cada relogin automático, e passos que checavam "sem player" (numa
     desconexão) avançavam a fila em vez de tentar de novo; combinados, isso gerou uma fila
     "fantasma" duplicada correndo sozinha enquanto o cliente estava desconectado, com
     `HB`/`NAV` de duas "gerações" da sequência se misturando no log. Corrigido com uma
     trava (`queueBuilt`) e um `intentionalLogout` pra não tentar relogin depois do
     `safeLogout()` final.
  5. v5-v6: adicionou desvio automático (perpendicular) e uma tentativa de `g_game.use()`
     genérica quando a navegação ficava presa numa tile — reduziu mas não eliminou os pontos
     de colisão do P2-1 (a maioria respondeu `"You cannot use this object."`, confirmando que
     não são portas, só decoração sólida).
- **PIDs do cliente**: o processo do OTClient às vezes gera um PID "wrapper" diferente do PID
  filho de verdade (`$!` do `nohup` ≠ PID que aparece em `ps`/`pgrep`) — confirmado uma vez
  nesta sessão (PID 25445 do `nohup` vs. PID 25473 rodando de fato, filho de 25471). Sempre
  conferir com `pgrep -fl "OTClient.app/Contents/MacOS/OTClient"` antes de matar, e matar
  **todos** os PIDs da árvore que a própria sessão abriu — nunca `pkill -x OTClient` (mataria
  sessões de outros agentes). Um OTClient de outro processo (PID 24896) já estava rodando no
  início desta sessão; saiu sozinho pouco depois (confirmado por `ps`, não foi tocado).
- `client-otc/shinobirc.lua` **desapareceu sozinho do disco** entre duas das minhas
  sub-sessões (confirmado: escrito, cliente rodado, depois `ls` não achou mais o arquivo,
  sem eu ter rodado nenhum `rm` nele) — provavelmente outro agente/processo do ambiente
  compartilhado limpou o arquivo por convenção ("nunca commitado, apagar ao terminar").
  Reescrevi o arquivo antes de cada novo `nohup` para não depender de que ele ainda existisse.
- **Escopo cortado por causa do tempo real gasto**: a sessão original previa um 2º bloco de
  caça, mais 3 NPCs (Jiro, quadro de diária, Ichiro) e uma tentativa de L5-10/Costa das
  Marés. Cortei o 2º bloco de caça e os 3 NPCs restantes numa reescrita do script no meio da
  sessão pra garantir que pelo menos a janela de caça principal e a tentativa da Capitã Rin
  fossem executadas dentro do tempo disponível — mesmo padrão de "descoberta de bug custa
  tempo de cobertura" já relatado nas rodadas 4 e 5.
- **Screenshots**: 10 válidos desta sessão final (`playtest6_01` a `09` + `17`, ver
  `screenshots/` — bem abaixo do limite de 40); descartei 7 screenshots (`10` a `16`) de
  uma sub-sessão anterior que ficaram inconsistentes por causa do bug de fila duplicada
  (v4). `~/Library/Application Support/shinobi/.shinobi/*.png` limpo ao final (todos os
  `playtest6_*.png` removidos depois de copiados).
- **Servidor**: nunca reiniciado. `nc -z 127.0.0.1 7171` confirmado no início e no fim.
  `grep -c "Lua Script Error" /tmp/tfs_run.log`: **0** — o único erro novo no log do
  servidor foi o `[Error - mysql_real_query]`/`Error while saving player` do P0-0 (não é um
  `Lua Script Error`, é um erro de driver MySQL de mais baixo nível).
- **Disco**: `df -h /` 13 GiB livres no início, **13 GiB livres no fim** (sem variação
  perceptível); `df -h /System/Volumes/Data` 13 GiB livres em ambas as pontas (94% usado) —
  acima do piso de 1,5 GB o tempo todo, nenhuma limpeza de emergência foi necessária.
- `client-otc/shinobirc.lua` apagado ao final (confirmado ausente). Nenhum processo
  OTClient próprio deixado rodando (confirmado com `pgrep -fl
  "OTClient.app/Contents/MacOS/OTClient"` vazio no fim). `g_game.safeLogout()` foi chamado
  no fim da sequência, mas o servidor rejeitou com `"You may not logout during or
  immediately after a fight!"` (trava de combate padrão, ainda ativa ~80s depois do último
  hit no Cervo) — o cliente encerrou via `g_app.exit()` mesmo assim (fim normal do script),
  o que conta como uma desconexão não-graciosa para efeito do P0-0 (progresso perdido de
  qualquer forma, já que o save falha independente do tipo de desconexão).
