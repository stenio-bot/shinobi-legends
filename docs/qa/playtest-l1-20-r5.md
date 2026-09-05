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
| 1 | | | | | | |
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

### P1

### P2

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
