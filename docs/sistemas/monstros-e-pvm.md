# Sistema: Monstros e PvM

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
| **Cervo (`forest_deer`)** | **passive** | **novo (2026-09-04): monstro de teste da categoria "passivo".** Nível 2, 30 HP, não inicia combate, spawn em `data/maps/forest_valley.json` perto do templo (Floresta da Vila). Reaproveita o sprite do Lobo (`looktype 21`, `mon_wolf`) recolorido — ver nota em `data/tfs_mapping.json` — para não depender de arte nova. |

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
| Floresta da Morte | 50,0,46,40 | 10–25 | sanguessuga (suiton), sapo gigante (suiton), ninja renegado (none), serpente menor (doton, L18) | **Serpente Branca** (doton, L25); Sapo Ancião (suiton, L25) é boss secundário | implementada |
| Ruínas do Clã | 96,0,52,40 | 25–50 | marionete de combate (none, L27), sentinela de pedra (doton, L32), guerreiro espectral (raiton, L38), xamã da maldição (katon, L44) | Marionetista das Ruínas (fuuton, L50) | implementada |
| Montanha do Trovão | 148,0,52,40 | 50–80 | águia do trovão (raiton, L54), oni da geleira (suiton, L60), monge da tempestade (fuuton, L68), serpente de magma (katon, L74) | Oni Ancestral (raiton, L80) | implementada |
| Fortaleza Akatsu | — | 80–100 | ninja de elite, bijuu menor | Líder da Fortaleza | planejada |

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
- **Limitação do `attack_multiplier`.** O evento `onHealthChange` do TFS 1.4.2 não consegue
  alterar o dano dos `<attack>` do monstro em runtime — a lista de ataques é lida uma única vez,
  no carregamento do XML. A fase de "fúria" é então aproximada por três coisas:
  1. **cura percentual**: `+ (mult - 1) * 10%` do HP máximo (mult 1.9 → +9%, 414 HP na Serpente Branca);
  2. **velocidade**: `creature:changeSpeed(baseSpeed * (mult - 1) * 0.5)` — o boss alcança o alvo
     e desfere mais golpes por minuto, que é o efeito prático de "bater mais forte";
  3. **registro** em `NarutoBossMult[monsterId] = mult`, para quem quiser ler o multiplicador de
     fora. Nenhum `onThink`/creaturescript extra é necessário.
  Se um dia quisermos o multiplicador de dano de verdade, o caminho é gerar uma cópia do monstro
  com os `<attack>` já multiplicados e trocar a criatura, não um `onThink`.
- Loot com itens exclusivos (`legendary`/`rare`) e pergaminhos.

### Serpente Branca (Floresta da Morte, L25)
Ninja renegado pálido que abandona a forma humana quando encurralado. 4 600 HP, 5 600 XP.

| Fase | Gatilho | O que acontece |
|---|---|---|
| 1 — forma humana | 100% (primeiro dano) | fala de abertura; ataca com veneno (melee + névoa em `circle_r2` + cuspe ácido com slow) |
| 2 — transformação | 60% | `looktype 890` (serpente 2×2), efeito verde, invoca **3 Cobras da Floresta** |
| 3 — fúria | 25% | `attack_multiplier 1.9` (cura +9% + velocidade), efeito vermelho, invoca **2 Serpentes Menores** |

Loot exclusivo: `white_serpent_fang` ("Presa da Serpente Branca", material raro, 100%) e
`scroll_doku_kiri` (pergaminho tier 2 de `doku_kiri`, 25%).

## Visuais dos bosses/monstros humanoides (looktypes 900–926)
Personagens importados (looktypes fixos 900–926, ver `assets-src/sprites/mugen_looktypes.json`)
são usados como **visual** de bosses e monstros humanoides — nunca como nome (ADR-002): o nome
do monstro no jogo continua o nosso, só o `looktype` em `data/tfs_mapping.json` (campo
`monsters.<id>`) muda.

| Nosso monstro/boss | Looktype | Sprite de origem | Onde fica |
|---|---|---|---|
| Chefe dos Bandidos (`boss_bandit_chief`) | 915 | Sasuke Akatsuki | Floresta da Vila (boss) |
| Serpente Branca, forma humana (`boss_white_serpent`) | 916 | Sasuke Rinnegan | Floresta da Morte (boss) |
| Marionetista das Ruínas (`boss_puppeteer`) | 910 | Itachi | Ruínas do Clã (boss) |
| Oni Ancestral (`boss_ancestral_oni`) | 913 | Madara | Montanha do Trovão (boss, único humanoide da área) |
| Ninja Renegado (`rogue_ninja`) | 914 | Sasuke Taka | Floresta da Morte (monstro comum) |
| Guerreiro Espectral (`spectral_warrior`) | 912 | Obito | Ruínas do Clã (monstro comum) |
| Xamã da Maldição (`curse_shaman`) | 911 | Pain | Ruínas do Clã (monstro comum) |

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
