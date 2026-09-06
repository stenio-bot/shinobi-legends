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

## Estado atual (2026-09-04)
Jogo roda ponta a ponta: OTClient compilado (client-otc/OTClient.app), TFS 1.4.2 com conteúdo Naruto,
mapa próprio `valley` (tools/map/build_valley.py), sprites placeholder + tiles próprios (tools/spr),
GM tools (/sl). Teste: `tools/autotest_client.sh god god` (precisa do servidor: tools/run_server.sh).
Pendências grandes: arte de verdade (usuário vai fornecer .spr/.dat ou PNGs em assets-src/import/),
mais mapas por faixa de level (ver docs/sistemas/mapas.md e o plano de 7 áreas), criação de conta.

## Armadilhas do TFS 1.4.2 já encontradas
- accounts.type: GOD = 6 (5 é Community Manager). Talkactions de GM checam >= ACCOUNT_TYPE_GOD.
- NPC: o servidor procura `data/npc/<Nome>.xml`; `script=` é relativo a `data/npc/scripts/`.
- items.xml: `weaponType fist` não existe (Taijutsu = sword); tipo `sign` não existe.
- Comentários OTML só em linha própria (`chave: valor  # x` quebra o parser).
- stdout do TFS é bufferizado quando redirecionado: use `script -q log ./build/tfs` para ver prints em tempo real.
- Regen de HP/mana no TFS puro só roda com comida; contornado com uma condição **permanente** (subId 9020) aplicada no login/level-up (`character_switch.lua` gerado) — não depende de comida.
- `firstitems.lua` (creaturescript vanilla) foi neutralizado para só dar a mochila de couro; senão disputa os slots com o kit da vila.
- `data/lib/*.lua` só carrega **no boot** do TFS — nenhum `/reload` (nem `all`) recarrega libs; um script recarregado que chama uma função nova de uma lib ainda não recarregada quebra com "attempt to call field ... (a nil value)" até o próximo restart.
- `/reload global` recria do zero as libs em memória (re-executa os `dofile`) — rodar DEPOIS de `/reload scripts` apaga métodos que o script já tinha colado nelas (ex. `NarutoCharacters.apply`); ordem certa: `/reload global` → `/reload scripts` → `/reload npcs`.
- `/reload scripts` **não** recarrega `data/creaturescripts/*.lua` (sistema clássico, não revscriptsys) — precisa de `/reload creaturescripts` ou `/reload all`.
- `openShopWindow`/`luaOpenShopWindow` usa `buy=-1`/`sell=-1` como sentinela e `getField<uint32_t>` explode com esse valor; patch em `server/tfs/src/npc.cpp` lê como `int32_t` e trunca em 0 (exige recompilar o servidor).
- `manapercent` no XML de spell faz o custo ser uma % do chakra máximo (`chakra_cost_percent` no JSON) em vez de um valor fixo — usado nos 5 jutsus tier 1 elementais desde a rodada 5 de balanceamento.
- Lua gerado por `tools/export_tfs.py` = cp1252 (para exibição no cliente); nomes que chegam do TFS em tempo de execução (`creature:getName()` etc., vindos do `name=` do XML) chegam em UTF-8 — sempre `NarutoText.utf8ToCp1252(nome)` antes de comparar/indexar contra um literal gerado, e `NarutoText.cp1252ToUtf8(nome)` na direção inversa (`Game.createMonster` de summon); ver `data/lib/naruto_json.lua` e `docs/sistemas/cliente-ux.md`.
- Cliente converte toda string do protocolo de UTF-8 para cp1252 na entrada (`InputMessage::getString`, por sequência via `stdext::utf8_to_cp1252`) — sem isso, nomes de NPC/criatura/item vindos do servidor viram mojibake nas fontes bitmap cp1252 do OTClient.
- FLAG_ALWAYSONTOP no `items.otb` precisa ser derivada do `topOrder` do item (não deixada no padrão) — bordas sem a flag empilham diferente entre cliente e servidor, `stackpos` diverge e o andar trava com "no creature found".
- Fúria de boss com dano real: `attack_multiplier` de uma fase agora multiplica `primaryDamage`/`secondaryDamage` de verdade via `CreatureEvent onHealthChange` do JOGADOR (não do monstro) — o TFS não deixa reescrever ataques de monstro em runtime, então o dano é multiplicado do outro lado.
- Testes headless por área: `tools/tests/run_quests_tests.sh` (motor de missões) e `tools/tests/run_boss_fury_tests.sh` (fúria de boss) — rodar depois de mexer em `quests_kill.lua`/`boss_phases.lua` gerados.

## Ambiente compartilhado (servidor/cliente rodam para vários agentes)
- Nunca rode `pkill -x OTClient` (mata sessões de outros agentes); mate só o PID que você mesmo abriu.
- Nunca reinicie o servidor por conta própria — outra sessão de playtest/rc pode estar em andamento; o servidor às vezes cai ou reinicia sozinho por causa externa, não assuma que foi você.
- **Disco**: a máquina de dev vive perto de 100% (`df -h /System/Volumes/Data`). Antes de `build_assets.py`, sessões de screenshots ou agentes paralelos, confira que há >2 GB livres; com ENOSPC até o harness dos agentes para de funcionar. Limpezas seguras: `~/Library/Application Support/shinobi/.shinobi/*.png`, `/tmp/otc_*.log`, `brew cleanup -s`, `~/vcpkg/downloads`.

## Como adicionar conteúdo
- Monstro: entrada em `data/monsters/<area>.json` + spawn em `data/maps/forest_valley.json` + cor em `Monster._color_for`.
- Missão: entrada em `quests` do NPC em `data/npcs/leaf.json` (sequenciais na ordem da lista).
  Tipos suportados (`kill`/`any_of`/`boss`, `collect_item`+`drops_from`, `keyword_quiz`,
  `talk_to`, `reach`), `requires`, diálogo condicionado e recompensas extras: ver
  `docs/sistemas/missoes.md`.
- Jutsu: `data/jutsus/<elemento>.json`; tier 1 é aprendido automaticamente por level/vila, tier 2+ via pergaminho.
- Sempre rode `.venv/bin/python tools/validate_data.py` e o smoke test depois.
- Balanceamento (HP/dano de monstro, dano de jutsu, TTK, XP/h, ryo/h): `python3 tools/balance/sim.py --matrix --json /tmp/matrix.json` roda a matriz nível x monstro x build (~30s, fórmulas reais do TFS) — ver `tools/balance/README.md` e `docs/sistemas/balanceamento-relatorio.md`.
- Chakra sustentável numa caçada real (30 min, com/sem pílula): `python3 tools/balance/sim.py --hunt --json /tmp/hunt.json`.
- Som (SFX de jutsu/combate/UI, síntese própria, sem downloads — ADR-002): `.venv/bin/python tools/audio/gen_sfx.py` gera `client-otc/data/sounds/naruto/*.ogg` (único formato que o cliente carrega) + `assets-src/audio/sfx_catalog.json`; toque com `modules.naruto_sounds.play('sfx_id')`. Ver `docs/sistemas/audio.md`.
- Música ambiente por região (7 faixas em loop, síntese própria via `tools/audio/synth.py` — ADR-002): `.venv/bin/python tools/audio/gen_music.py` gera `client-otc/data/sounds/naruto/music/*.ogg` + `assets-src/audio/music_catalog.json`; `modules/naruto_sounds/naruto_music.lua` troca de faixa por posição do jogador. `tools/audio/analyze_music.py` valida por FFT/RMS + PNG de forma de onda/espectrograma. Ver `docs/sistemas/audio.md`.
- Sprites de criatura procedurais: `tools/spr/gen_animals.py` (animais dedicados 100% procedurais, looktypes 940–945), `tools/spr/gen_humanoid_variants.py` (variante de paleta por hue-shift do PNG importado, looktypes 946–957), `tools/spr/gen_effects.py` (efeitos/misseis próprios dos jutsus). Ver `docs/sistemas/arte-e-sprites.md`.
- Retrato de personagem/creature a partir do nosso `client-otc/data/things/1098/Tibia.spr`/`.dat` (nunca de `assets-src/import/`): `tools/spr/render_outfit.py --looktype <id> [--head/--body/--legs/--feet 0-132] --out arquivo.png --scale 4`. É o que alimenta `tools/aac/portraits/*.png` (retratos do AAC, versionados). Ver `docs/sistemas/arte-e-sprites.md`.
- Depois de `tools/map/build_valley.py`, rode `.venv/bin/python tools/map/validate_world.py` (cruza `data/npcs`/`data/tasks.json`/`data/dailies.json`/`data/monsters` com o `valley-spawn.xml`/`valley.otbm` gerado — monstro de missão sem spawn, NPC de missão/loja sem spawn, posição não caminhável; exit 1 em falha). Ver `docs/sistemas/mapas.md`.

## Armadilhas já encontradas
- `var x := dict["k"]` não compila (tipo não inferível). Use `var x: float = dict["k"]`.
- Headless roda frames mais rápido que tempo real: testes não podem depender de "N frames = N/60 s".
- Jutsu "self" tem lógica por id em `JutsuExecutor._cast_self` (kawarimi, bunshin).
- Disco: ver "Ambiente compartilhado" acima.
