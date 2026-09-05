# Playtest L1–20 — rodada 2 (2026-09-05)

Registro condensado pelo orquestrador: o agente de QA não conseguiu gravar o relatório porque o
disco da máquina encheu (ENOSPC) no meio da sessão. Cobertura real desta rodada: **onboarding +
parte da vila**; nenhum combate foi alcançado (sem dados de XP/h, TTK ou chakra em combate).

## Confirmado ao vivo (personagem novo "Playtester Dois", Vila da Folha)
- Chakra inicial 60/60 no primeiro login (fix da rodada 1).
- Menu Shinobi (Ctrl+J) abre; aba Personagem em pt-BR (Genin Laranja / Folha / Vento / 4 jutsus).
- Painel de Atributos mostra "Rank: Genin da vila".
- Zero `Lua Script Error` no servidor durante login, saudação e movimentação.

## Achados
| Sev. | Achado | Causa raiz | Status |
|---|---|---|---|
| P0 | Kit da vila entregue pela metade: body=jacket, left=club, back=bag (vanilla) — só bandana/calça/sandálias caíram nos slots | `creaturescripts/scripts/firstitems.lua` (vanilla) ocupava os slots antes do kit gerado em `character_switch.lua` | **Corrigido** (`92166a7`): firstitems agora dá só `backpack_leather`; kit da vila ocupa os slots. Verificado com personagem novo "Kit QA": slots = bandana, mochila de couro, colete de genin, kunai de ferro, calça ninja, sandálias ninja |
| P2 | NPCs só respondem a `hi`/`hello`; `oi` não foca | `FOCUS_GREETWORDS` em `npcsystem.lua`/`modules.lua` | **Corrigido** (`92166a7`): + `oi`, `ola`, `olá` |
| P2 | Fachada do Ichiro escrita "Newbie Shop" (arte do prédio) | textura importada em `assets-src` | Pendente (backlog de sprites) |
| Obs. | Script de navegação automatizada ficou preso em (1033,1053) em 3 execuções; OTBM não mostra bloqueio | provável artefato do `autoWalk` reemitido a cada ~900 ms | Verificar manualmente antes de priorizar |

## Chakra (sem combate)
Genin Laranja/Vento no L1 tem um único jutsu utilizável (`fuuton_lamina_vento`, 13 de chakra,
cd 2 s) → ~4 casts com os 60 iniciais, como previsto. Regeneração em combate: não medida.

## Pendências para a rodada 3
1. Repetir do zero com personagem novo (kit agora completo) e chegar aos lobos: XP/h L1–5 e
   L6–10, mortes, chakra até secar e tempo de regen por nível.
2. Script de navegação em saltos curtos + abertura de portas (aprendizado desta rodada).
3. Contas de teste no banco: `playtester`, `playtester2`, `kitqa` (podem ser apagadas).

## Ambiente
- O disco do Mac estava a 99% (147 MiB livres) antes da sessão e encheu de vez durante ela;
  `~/Library/Caches` tinha 20 GB (Spotify 11 GB, Google 4 GB). Ver `docs/04-setup-ot.md`.
