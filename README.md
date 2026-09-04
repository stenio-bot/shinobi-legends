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
| `docs/sistemas/` | Um documento por sistema: progressão, combate, itens, monstros... |
| `data/` | Conteúdo do jogo em JSON: jutsus, itens, monstros, tabela de XP |
| `data/schemas/` | JSON Schema que valida cada tipo de conteúdo |
| `client-otc/` | OTClient Redemption (C++/Lua). Módulos Naruto em `modules/naruto_*` |
| `server/` | TFS 1.4.2 em `server/tfs/` + conteúdo gerado em `server/generated/` |
| `client-godot/` | Protótipo Godot (Marcos 1–3), congelado, referência de regras |
| `tools/` | Scripts utilitários (validar dados, gerar tabelas) |
| `assets-src/` | Arte fonte (Aseprite, PSD, referências) |

## Como começar

1. Leia `docs/00-visao-geral.md`, `docs/01-roadmap.md` (Fase OT) e `docs/04-setup-ot.md`.
2. Valide o conteúdo: `.venv/bin/python tools/validate_data.py`.
3. Gere os arquivos do servidor: `python3 tools/export_tfs.py` → `server/generated/`.
4. Compile cliente e servidor seguindo `docs/04-setup-ot.md`.
