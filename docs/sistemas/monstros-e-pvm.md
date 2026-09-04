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

## Spawns
Cada mapa tem `spawns.json`: `{monster_id, x, y, radius, count, respawn_s}`.
Monstros voltam no spawn, não onde morreram.

## Faixas de área (MVP e além)
Todas as áreas abaixo vivem no mesmo mapa `data/maps/forest_valley.json` (200×40), divididas
por `zones`. Números detalhados por faixa em `balanceamento.md`.

| Área | Zona (rect) | Level | Monstros (element) | Boss | Status |
|---|---|---|---|---|---|
| Floresta da Vila | 0,0,50,40 | 1–10 | lobo (none), cobra (doton), bandido (none), bandido arqueiro (none) | Chefe dos Bandidos (katon, L12) | implementada |
| Pântano Sombrio | 50,0,46,40 | 10–25 | sanguessuga (suiton), sapo gigante (suiton), ninja renegado (none) | Sapo Ancião (suiton, L25) | implementada |
| Ruínas do Clã | 96,0,52,40 | 25–50 | marionete de combate (none, L27), sentinela de pedra (doton, L32), guerreiro espectral (raiton, L38), xamã da maldição (katon, L44) | Marionetista das Ruínas (fuuton, L50) | implementada |
| Montanha do Trovão | 148,0,52,40 | 50–80 | águia do trovão (raiton, L54), oni da geleira (suiton, L60), monge da tempestade (fuuton, L68), serpente de magma (katon, L74) | Oni Ancestral (raiton, L80) | implementada |
| Fortaleza Akatsu | — | 80–100 | ninja de elite, bijuu menor | Líder da Fortaleza | planejada |

Cada área nova tem 1 mercador + 1 quest giver em `data/npcs/<area>.json` com 3–4 missões
sequenciais que acompanham a progressão de level da zona.

## Bosses
- Spawn fixo a cada 2–6h (`respawn_s`: 7200 nos bosses até L50, 10800 no Oni Ancestral), anúncio no chat.
- `phases`: lista de `{hp_percent, attacks, summons}` — muda comportamento com a vida.
- Loot com itens exclusivos (`legendary`) e pergaminhos.

## Loot
- Rolagem independente por item: `chance` em 0–1.
- Ryo sempre cai (`ryo_min`, `ryo_max`).
- Corpo fica 60s no chão com o loot (estilo Tibia); multiplayer: só quem deu último hit/party abre nos primeiros 10s.
