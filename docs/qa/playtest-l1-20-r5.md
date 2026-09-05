# Playtest QA — nível 1 a 20, rodada 5 (2026-09-05) — segunda tentativa

Sessão de playtest de um jogador comum, conta `kitqa2` (personagem **Kit QA Dois**, Genin
Laranja, Vila da Folha, L1, 110 chakra), retomando de onde a primeira tentativa desta rodada
(interrompida pela queda da própria sessão do agente, não do jogo) parou. Metodologia validada
pelas rodadas 3/4: `client-otc/shinobirc.lua` temporário (nunca commitado, apagado ao final de
cada sub-sessão), saltos curtos de `autoWalk` (≤10 tiles), passo manual através de portas
fechadas antes de confiar em `autoWalk` (achado da rodada 4), tratamento de morte/relogin
automático, `g_game.safeLogout()` ao encerrar, runner próprio que mata só o PID que ele mesmo
abriu (nunca `pkill -x OTClient` — há um OTClient do usuário rodando, PID diferente, intocado).

**Este documento é preenchido incrementalmente durante a sessão** — o esqueleto abaixo será
completado seção por seção conforme o playtest avança.

## Resumo executivo

_(preencher ao final)_

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
| 1 | (em andamento) | 0 | 1 (ver P1-5, morta pelo Bandido Arqueiro da Clareira Central em rota, sem engajar) | 0 | N/D | Navegação Vila→Bosque Norte consumiu a maior parte do tempo desta sub-sessão (ver P2-9/P2-10); combate real ainda não medido. |
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
| 1 | `fuuton lamina vento` | | | | | | |

**Veredito do cooldown de 9s**: _(preencher — hits de arma entre casts, sensação
arrastada/divertida, casts para matar 1 lobo)_

## Missões / tarefas / diária / loja

- `!conquistas` antes do 1º lobo:
- `!conquistas` depois do 1º lobo:
- `!conquistas` depois da entrega da missão dos lobos:
- Missão dos lobos (Mentor, `hi`/`missao`):
- Tarefa (Mestre Jiro, `hi`/`tarefas`/`tarefa`/`entregar`):
- Diária (Quadro, `hi`/`diaria`):
- Compras (Ichiro, `hi`/`trade`):

## L5→L10 (bandidos/cobras)

_(preencher — nota: o spawn file instalado tem "Bosque Norte" 1050,1010 ainda com Lobo x2, não
bandido/cobra; bandidos ficam em "Campina Oeste" 1006,1050 (3 Bandido) e "Clareira Central"
1070,1040 (2 Bandido Arqueiro); cobras em "Clareira do Riacho" 1085,1015 — a nomenclatura da
missão pode estar desatualizada em relação ao arquivo de spawn atualmente instalado; ver achado
correspondente)_

## Costa das Marés (se sobrar tempo)

_(preencher)_

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

## Comparação com `progressao-jogador.md`

_(preencher — tabela prevê ~536 XP/h e 2,8h para bloco 1-5)_

## O que faria um jogador desistir

_(preencher)_

## Metodologia e limitações

_(preencher)_

## Screenshots

_(preencher — prefixo `playtest5_`)_

## Espaço em disco

| Momento | Livre em `/System/Volumes/Data` |
|---|---|
| Antes da sessão | |
| Depois da sessão | |
