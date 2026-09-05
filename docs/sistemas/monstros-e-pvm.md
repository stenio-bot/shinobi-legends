# Sistema: Monstros e PvM

> **Lore e visuais:** a história de cada região, os bosses de arco e a regra de
> "inimigo genérico nunca usa visual de personagem principal" vivem em
> `docs/lore/mundo.md` (bíblia do mundo) e `docs/lore/progressao.md` (ranks e
> exames). Este documento cobre só a mecânica (schema, IA, spawns, fórmulas de
> fase). Pesquisa de referência (arcos, ranks reais) em `docs/lore/pesquisa-naruto.md`.

## Anatomia de um monstro (`data/schemas/monster.schema.json`)
| Campo | Descrição |
|---|---|
| `id`, `name`, `level` | identidade e faixa |
| `hp`, `attack`, `defense`, `speed` | stats |
| `element` | fraqueza/força elemental |
| `xp` | XP ao morrer |
| `behavior` | `passive`, `aggressive`, `cowardly` (foge com HP baixo), `ranged` |
| `aggro_range`, `attack_range` | tiles |
| `attacks` | lista: `{name, damage_min, damage_max, cooldown_s, type, effects}` |
| `loot` | lista: `{item_id, chance, min, max}` |
| `respawn_s` | tempo de respawn |
| `boss` | true/false (bosses têm mecânicas em `phases`) |

## IA (máquina de estados simples)
```
IDLE ──(jogador em aggro_range)──► CHASE ──(em attack_range)──► ATTACK
  ▲                                   │                            │
  └──────(perdeu alvo por 5s)─────────┴────────────────────────────┘
COWARDLY: se hp < 20% → FLEE por 5s, depois volta a CHASE
```

## Categoria agressivo × passivo (behavior)
`tools/export_tfs.py` (`monster_xml`) traduz `behavior` para o XML do TFS:
- `aggressive`, `cowardly`, `ranged` → `<flag hostile="1">` (o monstro persegue e ataca sozinho).
- `passive` → `<flag hostile="0">` (só briga se você atacar primeiro; nunca inicia).
- `ranged` também define `targetdistance` = `attack_range` (mantém distância do alvo).
- `cowardly` define `runonhealth` = 20% do HP máximo (foge abaixo desse valor).
- Todos ganham `staticattack="90"` (perseguem o alvo com afinco em vez de vagar) e
  `targetchange interval="4000" chance="10"` (10% de chance a cada 4s de trocar de alvo).

| Monstro | `behavior` | Observação |
|---|---|---|
| Lobo (`wolf`) | aggressive | ataca ao entrar em `aggro_range` |
| Bandido (`bandit`) | aggressive | melee |
| Cobra da Floresta (`forest_snake`) | cowardly | foge com HP baixo |
| Bandido Arqueiro (`bandit_archer`) | ranged | mantém distância, atira |
| Chefe dos Bandidos (boss) | aggressive | invoca Bandidos na fase de 50% |
| Sanguessuga, Sapo Gigante, Ninja Renegado, Serpente Menor, bosses da Floresta da Morte | aggressive/ranged conforme JSON | ver `data/monsters/swamp.json` |
| Marionete de Combate, Sentinela de Pedra, Guerreiro Espectral, Xamã da Maldição, bosses das Ruínas | aggressive/ranged | ver `data/monsters/ruins.json` |
| Águia do Trovão, Oni da Geleira, Monge da Tempestade, Serpente de Magma, bosses da Montanha | aggressive/ranged | ver `data/monsters/mountain.json` |
| **Cervo (`forest_deer`)** | **passive** | **novo (2026-09-04): monstro de teste da categoria "passivo".** Nível 2, 30 HP, não inicia combate, spawn em `data/maps/forest_valley.json` perto do templo (Floresta da Vila). Sprite próprio procedural (looktype 941, `tools/spr/gen_animals.py`) desde 2026-09-05; antes reaproveitava o placeholder do Lobo (looktype 21). |

Nenhum outro monstro do jogo era passivo antes disso — daí o sintoma "não existe categoria
agressivo/não agressivo" reportado: a categoria sempre existiu no schema/exportador, só não havia
nenhum monstro passivo *no jogo* para o jogador comparar.

## Spawns
Cada mapa tem `spawns.json`: `{monster_id, x, y, radius, count, respawn_s}`.
Monstros voltam no spawn, não onde morreram.

## Faixas de área (MVP e além)
Todas as áreas abaixo vivem no mesmo mapa `data/maps/forest_valley.json` (200×40), divididas
por `zones`. Números detalhados por faixa em `balanceamento.md`.

| Área | Zona (rect) | Level | Monstros (element) | Boss | Status |
|---|---|---|---|---|---|
| Floresta da Vila | 0,0,50,40 | 1–10 | lobo (none), cobra (doton), bandido (none), bandido arqueiro (none) | Chefe dos Bandidos (katon, L12) | implementada |
| Costa das Marés | — | 12–19 | mercenário da ponte, batedor da névoa, guardião da neblina (`data/monsters/coastal_tides.json`) | Espadachim da Névoa + Aprendiz Mascarado (suiton, L19) | no mapa desde v2.1 (x1000-1049/y1120-1169, ver `docs/sistemas/mapas.md`) |
| Floresta da Morte | 50,0,46,40 | 10–25 | sanguessuga (suiton), sapo gigante (suiton), ninja renegado (none), serpente menor (doton, L18), rivais do exame (`exam_rival_*`, L20) | **Serpente Branca** (doton, L25); Sapo Ancião (suiton, L25) é boss secundário | implementada |
| Ruínas do Clã Marionetista | 96,0,52,40 | 25–50 | marionete de combate (none, L27), sentinela de pedra (doton, L32), guerreiro espectral (raiton, L38), xamã da maldição (katon, L44), desertor de elite (katon, L46) | Marionetista das Ruínas (fuuton, L50) | implementada |
| Montanha do Trovão | 148,0,52,40 | 50–80 | águia do trovão (raiton, L54), oni da geleira (suiton, L60), monge da tempestade (fuuton, L68), serpente de magma (katon, L74) | O Sócio Eterno (doton, L70) + Oni Ancestral (raiton, L80) — "Dupla Imortal" | implementada (Sócio Eterno é novo) |
| Covil da Organização Nuvem Vermelha | — | 80–100 | clone branco, ninja elite da aurora (`data/monsters/akatsuki_lair.json`) | 4 bosses sequenciais: O Vigia Ilusório (L85), O Mascarado das Sombras (L90), O Portador dos Seis Caminhos (L95), O Ancestral da Nuvem Vermelha (L100, final) | no mapa desde v2.1 (x1400-1449/y1000-1049, gate Anbu actionid 45004; era "Fortaleza Akatsu") |

Ver `docs/lore/mundo.md` para a história de cada região, e
`docs/lore/progressao.md` para como as duas regiões (hoje já no mapa)
e os bosses novos se encaixam nos exames de rank (Genin→Chunin→Jonin→Anbu→Kage).

Cada área nova tem 1 mercador + 1 quest giver em `data/npcs/<area>.json` com 3–4 missões
sequenciais que acompanham a progressão de level da zona.

## Bosses
- Spawn fixo a cada 2–6h (`respawn_s`: 7200 nos bosses até L50, 10800 no Oni Ancestral), anúncio no chat.
- `phases`: lista de `{hp_percent, message, summons, attack_multiplier, looktype}` — muda
  comportamento conforme a vida cai. Uma fase com `hp_percent: 100` dispara no primeiro dano
  (serve para a fala de abertura).
- `looktype` (opcional, int): **transformação**. `tools/export_tfs.py` gera
  `boss_phases.lua`, que faz `creature:setOutfit({lookType = N})` quando a fase é atingida
  (zera head/body/legs/feet/addons para o outfit novo não herdar cores do humano).
  Usado pela Serpente Branca: outfit humano 132 → serpente 2x2 890.
- **`attack_multiplier` aumenta o dano de verdade (2026-09-05).** O `onHealthChange` do TFS 1.4.2
  não consegue reescrever a lista de `<attack>`/spells do monstro em runtime (ela é lida uma única
  vez, no carregamento do XML) — mas dá pra multiplicar o dano do OUTRO lado: o
  `CreatureEvent onHealthChange` do JOGADOR (registrado no login, `player:registerEvent`) também é
  chamado quando o boss acerta o jogador (`attacker` = o boss), com `primaryDamage`/`secondaryDamage`
  já calculados — e o retorno da função troca o dano de verdade (`server/tfs/src/creatureevent.cpp`,
  `executeHealthChange`). `boss_phases.lua` (gerado por `tools/export_tfs.py`) usa isso:
  1. **`NarutoBossPhases`** (evento do MONSTRO, o de sempre): a cada fase com `mult > 1`, publica
     `NarutoBossPhases.state[bossId] = {name, mult}` — além de manter a cura pontual
     (`+ (mult - 1) * 10%` do HP máximo) e o aumento de velocidade (`changeSpeed`) como antes,
     que continuam valendo (fazem o boss alcançar e bater mais vezes por minuto).
  2. **`NarutoBossFury`** (evento novo, do JOGADOR): no `onHealthChange` do jogador, se
     `attacker` é um boss com `state.mult > 1` (nome revalidado contra `state.name`, pra não
     vazar o multiplicador se o `creature:getId()` do boss morto for reciclado por outro
     monstro), multiplica `primaryDamage` e `secondaryDamage` por `mult` (arredondado,
     `floor(x*mult+0.5)`) e devolve os dois. Cobre dano melee E de spell do boss (ambos chegam
     por `onHealthChange` do jogador do mesmo jeito). Summons invocados na fase **não** herdam
     o `mult` — só o `id` do boss original entra em `NarutoBossPhases.state`.
  3. `NarutoBossReset.onDeath` limpa `NarutoBossPhases.state[bossId]` (e o índice de fase) pra
     não vazar por `cid` reutilizado.
  Teste headless: `tools/tests/test_boss_fury_headless.lua` (`tools/tests/run_boss_fury_tests.sh`).
  **Efeito colateral esperado**: como a cura/velocidade da fase já estavam calibradas pra
  compensar a FALTA de dano real, somar o multiplicador de dano de verdade em cima sobe o TTK
  efetivo dos bosses acima do calibrado em `balanceamento-relatorio-v6.md` — ver nota de
  recalibração ali (rodada 7 deve cortar pela metade o excedente de `attack_multiplier`, ex.
  1.5 → 1.25, em `data/monsters/*.json`).
- Loot com itens exclusivos (`legendary`/`rare`) e pergaminhos.

### Serpente Branca (Floresta da Morte, L25)
Ninja renegado pálido que abandona a forma humana quando encurralado. 4 600 HP, 5 600 XP.

| Fase | Gatilho | O que acontece |
|---|---|---|
| 1 — forma humana | 100% (primeiro dano) | fala de abertura; ataca com veneno (melee + névoa em `circle_r2` + cuspe ácido com slow) |
| 2 — transformação | 60% | `looktype 890` (serpente 2×2), efeito verde, invoca **3 Cobras da Floresta** |
| 3 — fúria | 25% | `attack_multiplier 1.9`: dano real ×1,9 (`NarutoBossFury`), cura pontual +9% + velocidade, efeito vermelho, invoca **2 Serpentes Menores** (summons não herdam o ×1,9) |

Loot exclusivo: `white_serpent_fang` ("Presa da Serpente Branca", material raro, 100%) e
`scroll_doku_kiri` (pergaminho tier 2 de `doku_kiri`, 25%).

## Visuais dos bosses/monstros humanoides (looktypes 900–926)

**Regra corrigida em 2026-09-04** (feedback do usuário: monstros genéricos — o
Chefe dos Bandidos, um bandido comum — estavam usando o visual do Sasuke, entre
outros personagens principais em mobs comuns). A partir de agora: **personagens
importados (looktypes fixos 900–926, ver `assets-src/sprites/mugen_looktypes.json`)
só aparecem em NPCs mentores e em bosses de arco de verdade** (a Serpente Branca
e os 4 bosses do covil final); todo o resto — inclusive bosses "menores" como o
Chefe dos Bandidos e o Marionetista — usa sprites genéricos já extraídos em
`assets-src/sprites/imports.json` (looktypes 128–139, 12, 19, 56, 60, 61). Ver
`docs/lore/mundo.md` para a explicação região por região.

| Nosso monstro/boss | Looktype | Sprite de origem | Onde fica |
|---|---|---|---|
| Chefe dos Bandidos (`boss_bandit_chief`) | 131 | genérico "ninja_chief" | Floresta da Vila (boss) — **corrigido**, era 915/Sasuke Akatsuki |
| Marionetista das Ruínas (`boss_puppeteer`) | 131 | genérico "ninja_chief" | Ruínas do Clã Marionetista (boss) — **corrigido**, era 910/Itachi |
| Espadachim da Névoa (`boss_mist_swordsman`) | 132 | genérico "ninja_white" | Costa das Marés (boss, novo) |
| Serpente Branca, forma humana (`boss_white_serpent`) | 916 | Sasuke Rinnegan | Floresta da Morte (boss de arco — mantido, uso correto) |
| O Sócio Eterno (`boss_curse_partner`) | 138 | genérico "hooded_purple" | Montanha do Trovão (boss, novo) |
| Oni Ancestral (`boss_ancestral_oni`) | 12 | genérico "oni_fox" | Montanha do Trovão (boss) — **corrigido**, era 913/Madara |
| Ninja Renegado (`rogue_ninja`) | 128 | genérico "ninja_blue" | Floresta da Morte (monstro comum) — **corrigido**, era 914/Sasuke Taka |
| Guerreiro Espectral (`spectral_warrior`) | 130 | genérico "ninja_pale" | Ruínas do Clã Marionetista (monstro comum) — **corrigido**, era 912/Obito |
| Xamã da Maldição (`curse_shaman`) | 138 | genérico "hooded_purple" | Ruínas do Clã Marionetista (monstro comum) — **corrigido**, era 911/Pain |
| Desertor de Elite (`elite_deserter`, novo) | 915 | Sasuke Akatsuki | Ruínas do Clã Marionetista (mini-boss) — uso correto: é um gênio desertor de elite, não um mob comum |
| O Vigia Ilusório / O Mascarado das Sombras / O Portador dos Seis Caminhos / O Ancestral da Nuvem Vermelha (novos) | 910 / 912 / 911 / 913 | Itachi / Obito / Pain / Madara | Covil da Organização Nuvem Vermelha — os 4 bosses finais do jogo, uso correto (endgame de verdade) |

A forma de serpente 2×2 da Serpente Branca (fase 60%, looktype 890) continua sendo aplicada em
runtime por `boss_phases.lua`, sem relação com a faixa 900–926.

## Testando PvM como GM
A conta GM (grupo `god`, id 6) tem as flags `ignoredbymonsters`/`cannotbeattacked`
(`server/tfs/data/XML/groups.xml`) — por design do TFS, nenhum monstro ataca ou consegue
acertar um GM normal. Para testar combate como GM, use `/pvm` (`gm_tools.lua`): ele alterna para
o grupo `god vulneravel` (id 7, mesmas flags menos essas duas), permitindo levar dano. Veja
"GM: /pvm" em `docs/04-setup-ot.md` para detalhes e a armadilha do `updateTargetList` (é preciso
andar um passo depois de ligar `/pvm` para o monstro perceber a mudança).

## Loot
- Rolagem independente por item: `chance` em 0–1.
- Ryo sempre cai (`ryo_min`, `ryo_max`).
- Corpo fica 60s no chão com o loot (estilo Tibia); multiplayer: só quem deu último hit/party abre nos primeiros 10s.
