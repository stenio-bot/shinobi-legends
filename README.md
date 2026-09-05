# Shinobi Legends (nome provisório)

MMORPG Open Tibia com tema Naruto, no estilo **Narutibia / NTO Ultimate**, com foco em **PvM**
(caça de monstros), progressão de personagem, jutsus, skills e itens.

Base técnica: **OTClient Redemption** (cliente) + **The Forgotten Server 1.4.2** (servidor).
Ver `docs/03-decisoes-tecnicas.md` (ADR-005).

> Nome, universo e sprites são provisórios. Ver `docs/03-decisoes-tecnicas.md`
> sobre propriedade intelectual (Naruto é marca registrada).

## Onde estão as coisas

| Pasta | O que tem |
|---|---|
| `CLAUDE.md` | Contexto do projeto para o Claude Code (leia primeiro) |
| `docs/` | Design do jogo (GDD), roadmap, arquitetura, decisões |
| [`docs/00-biblia-do-jogo.md`](docs/00-biblia-do-jogo.md) | **Documento mãe**: mundo, história, progressão, sistemas, bestiário, grimório e estado atual num só lugar |
| `docs/sistemas/` | Um documento por sistema: progressão, combate, itens, monstros... |
| `docs/qa/` | Relatórios de playtest (L1–20, rodadas sucessivas) |
| `docs/lore/` | Mundo, pesquisa de referência e progressão de rank em prosa |
| `docs/referencias/` | Notas técnicas sobre OTClient e o NTO/Narutibia original |
| `data/` | Conteúdo do jogo em JSON: jutsus, itens, monstros, tabela de XP |
| `data/schemas/` | JSON Schema que valida cada tipo de conteúdo |
| `client-otc/` | OTClient Redemption (C++/Lua). Módulos Naruto em `modules/naruto_*` |
| `server/` | TFS 1.4.2 em `server/tfs/` + conteúdo gerado em `server/generated/` |
| `client-godot/` | Protótipo Godot (Marcos 1–3), congelado, referência de regras |
| `tools/` | Scripts utilitários (validar dados, exportar pro TFS, balanceamento, sprites, áudio, mapa) |
| `assets-src/` | Arte e áudio fonte (PNGs proceduais, catálogos JSON, referências) |

## Índice de documentação

**Visão geral e roadmap**
- [`docs/00-biblia-do-jogo.md`](docs/00-biblia-do-jogo.md) — documento mãe (leia primeiro)
- [`docs/00-visao-geral.md`](docs/00-visao-geral.md) — visão geral resumida
- [`docs/01-roadmap.md`](docs/01-roadmap.md) — marcos e fila autônoma de trabalho
- [`docs/02-arquitetura.md`](docs/02-arquitetura.md) — arquitetura técnica
- [`docs/03-decisoes-tecnicas.md`](docs/03-decisoes-tecnicas.md) — ADRs (decisões de design/arquitetura)
- [`docs/04-setup-ot.md`](docs/04-setup-ot.md) — setup do ambiente (cliente/servidor), notas de QA

**Sistemas** (`docs/sistemas/`)
- [`progressao-servidor.md`](docs/sistemas/progressao-servidor.md) — rank, quiz, tarefas, diárias, conquistas
- [`progressao-jogador.md`](docs/sistemas/progressao-jogador.md) — curva de XP/h e horas por nível
- [`combate-e-jutsus.md`](docs/sistemas/combate-e-jutsus.md) — fórmulas de combate e protocolo de jutsu
- [`personagem-e-progressao.md`](docs/sistemas/personagem-e-progressao.md) — fórmulas de HP/chakra (histórico, ver nota no topo)
- [`vilas-e-clas.md`](docs/sistemas/vilas-e-clas.md) — vilas, personagens, clãs
- [`monstros-e-pvm.md`](docs/sistemas/monstros-e-pvm.md) — bestiário e comportamento de PvM
- [`itens-e-equipamentos.md`](docs/sistemas/itens-e-equipamentos.md) — itens, tiers, sets de equipamento
- [`economia.md`](docs/sistemas/economia.md) — ryo, preços de referência, anti-inflação
- [`mapas.md`](docs/sistemas/mapas.md) — as 6 regiões, gates de rank, pipeline de mapa
- [`cliente-ux.md`](docs/sistemas/cliente-ux.md) — Menu Shinobi, rank em tela, chat pt-BR
- [`arte-e-sprites.md`](docs/sistemas/arte-e-sprites.md) — pipeline procedural de sprites/tiles/efeitos
- [`audio.md`](docs/sistemas/audio.md) — pipeline de som procedural (SFX)
- [`balanceamento.md`](docs/sistemas/balanceamento.md) — fórmulas e estado atual do balanceamento
- [`balanceamento-relatorio-v5.md`](docs/sistemas/balanceamento-relatorio-v5.md) — relatório da rodada mais recente (v2/v3/v4 no mesmo diretório, histórico)

**QA** (`docs/qa/`)
- [`playtest-l1-20-r4.md`](docs/qa/playtest-l1-20-r4.md) — rodada mais recente (r1/r2/r3 no mesmo diretório, histórico)

**Lore** (`docs/lore/`)
- [`mundo.md`](docs/lore/mundo.md) — as 6 regiões, bestiário narrativo, NPCs e bosses
- [`progressao.md`](docs/lore/progressao.md) — ranks e exames em prosa
- [`pesquisa-naruto.md`](docs/lore/pesquisa-naruto.md) — pesquisa de referência dos arcos/ranks

**Backlogs**
- [`docs/backlog-sprites.md`](docs/backlog-sprites.md) — arte pendente (prioridade: looktypes MUGEN)
- [`docs/backlog-audio.md`](docs/backlog-audio.md) — som pendente (música, sons de monstro)

## Como começar

1. Leia `docs/00-biblia-do-jogo.md` (documento mãe), `docs/01-roadmap.md` (Fase OT) e `docs/04-setup-ot.md`.
2. Valide o conteúdo: `.venv/bin/python tools/validate_data.py`.
3. Gere os arquivos do servidor: `python3 tools/export_tfs.py` → `server/generated/`.
4. Compile cliente e servidor seguindo `docs/04-setup-ot.md`.
5. Suba servidor + AAC (site de conta) + cliente num comando só: `tools/play.sh`.
