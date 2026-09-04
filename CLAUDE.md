# CLAUDE.md — contexto do projeto Shinobi Legends

## O que é
MMORPG 2D top-down (visão "Tibia"), tema ninja inspirado em Narutibia / NTO Ultimate.
Foco: **PvM** com progressão profunda (level, skills, jutsus, itens, vilas/clãs).
Idioma do projeto e da UI: **português (pt-BR)**. Código e identificadores em inglês.

## Stack (ADR-005 em docs/03-decisoes-tecnicas.md — PIVÔ em 2026-09-03)
- **Cliente:** `client-otc/` = OTClient Redemption (C++20 + Lua/OTUI). Customizar via módulos Lua.
- **Servidor:** The Forgotten Server 1.4.2 (protocolo 10.98) em `server/tfs/`. Lua para scripts.
- **Conteúdo** continua em `data/*.json` (fonte da verdade). `tools/export_tfs.py` gera os
  arquivos do TFS. Nunca edite os XML/Lua gerados à mão; edite o JSON e regenere.
- **Sprites:** .spr/.dat versão 1098 via ObjectBuilder. Fonte em `assets-src/`.
- `client-godot/` é o protótipo antigo (Marcos 1–3), referência de regras. Não evolui mais.

## Regras de trabalho
- Nunca coloque números de balanceamento hardcoded em GDScript. Vão em `data/`.
- Todo novo jutsu/item/monstro precisa passar em `python3 tools/validate_data.py`.
- IDs são `snake_case` únicos (ex.: `katon_goukakyuu`, `kunai_iron`, `bandit_lv5`).
- Documente decisões que mudam design em `docs/03-decisoes-tecnicas.md` (formato ADR).
- Ao criar sistema novo: primeiro o `.md` em `docs/sistemas/`, depois schema, depois código.
- Commits pequenos, em português, imperativo: "adiciona jutsu katon", "corrige dano crítico".

## Convenções OTClient
- Módulos próprios ficam em `client-otc/modules/naruto_*` (não editar os `game_*` originais
  além do mínimo; preferir sobrescrever via módulo próprio ou locale).
- Textos em pt-BR via `client-otc/modules/client_locales/locales/pt.lua` (Mana→Chakra etc.).
- Módulos removidos do jogo (market, store, prey, wheel, forge, imbuing, cyclopedia...) são
  desativados no `.otmod` do `game_interface`/`client`, não apagados, para facilitar merge upstream.

## Convenções TFS
- Scripts gerados: `server/tfs/data/monster/naruto/*.xml`, `server/tfs/data/spells/scripts/naruto/*.lua`,
  `server/tfs/data/npc/naruto/*`. Cabeçalho `-- GERADO por tools/export_tfs.py` em todos.
- Scripts manuais (eventos, quests) em `server/tfs/data/scripts/naruto/` (revscriptsys).

## Glossário
- **PvM**: player vs monster (caçar).
- **Chakra**: recurso gasto por jutsus (equivale a "mana").
- **Elemento**: Katon (fogo), Suiton (água), Doton (terra), Fuuton (vento), Raiton (raio).
- **Vila**: facção inicial do jogador (Folha, Areia, Névoa...). Influencia jutsus disponíveis.
- **Skill**: proficiência que sobe com uso (Taijutsu, Ninjutsu, Genjutsu, Defesa, Shuriken).

## Mapa do código do protótipo Godot (client-godot/scripts) — só referência
- `core/game_world.gd` — raiz da cena, grid/ocupação, spawns, input de alvo, eventos de morte.
- `core/world_map.gd` — mapa gerado de `data/maps/*.json` (`is_walkable`, `blocks_sight`, `has_line_of_sight`, `zone_at`).
- `ui/start_screen.gd` — escolha de vila quando não há save. `GameWorld.start_game(village, from_save)` cria tudo.
- `entities/entity.gd` — base: célula, movimento em grid com tween, HP, `take_damage`.
- `entities/player.gd` — input WASD, regen, auto-ataque no alvo, XP/level, respawn.
- `entities/monster.gd` — carrega `data/monsters`, FSM IDLE/CHASE/ATTACK/FLEE.
- `entities/corpse.gd` — corpo com loot (não bloqueia célula, some em 60s). `entities/npc.gd` — NPC de loja/missão.
- `combat/damage_calc.gd` — fórmulas puras. `combat/jutsu_executor.gd` — executa jutsus do JSON.
- `combat/shapes.gd` — células de área (circle_rN, cross_rN, line_N, cone_N). `combat/projectile.gd`.
- `progression/skill_system.gd` — skills sobem com uso. `core/inventory.gd` — mochila com stacks.
- `core/save_system.gd` — save em `user://save_slot_1.json` (F5/F9, autosave ao fechar).
- `ui/hud.gd`, `ui/hotbar.gd`, `ui/inventory_panel.gd`, `ui/shop_panel.gd`, `ui/floating_text.gd` — UI toda em código.
- `data/game_data.gd` — autoload; no editor lê `../data`, em export lê `res://data`.

## Testar
```
godot --headless --path client-godot --import          # 1ª vez ou após criar class_name novo
godot --headless --path client-godot res://tests/smoke_test.tscn   # teste de fumaça (exit 0 = ok)
```
Scripts rodados com `-s` NÃO enxergam autoloads; testes são cenas.

## Estado atual
Pivô para OTClient + TFS em andamento (ver docs/01-roadmap.md, "Fase OT"). O protótipo Godot
(Marcos 1–3) está completo e congelado em `client-godot/`.

## Como adicionar conteúdo
- Monstro: entrada em `data/monsters/<area>.json` + spawn em `data/maps/forest_valley.json` + cor em `Monster._color_for`.
- Missão: entrada em `quests` do NPC em `data/npcs/leaf.json` (sequenciais na ordem da lista).
- Jutsu: `data/jutsus/<elemento>.json`; tier 1 é aprendido automaticamente por level/vila, tier 2+ via pergaminho.
- Sempre rode `.venv/bin/python tools/validate_data.py` e o smoke test depois.

## Armadilhas já encontradas
- `var x := dict["k"]` não compila (tipo não inferível). Use `var x: float = dict["k"]`.
- Headless roda frames mais rápido que tempo real: testes não podem depender de "N frames = N/60 s".
- Jutsu "self" tem lógica por id em `JutsuExecutor._cast_self` (kawarimi, bunshin).
