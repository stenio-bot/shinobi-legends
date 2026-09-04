# 02 — Arquitetura

## Princípio: conteúdo é dado, não código
Jutsus, itens, monstros, tabela de XP e loot vivem em `data/*.json`. O código só sabe
**interpretar** esses dados. Isso permite balancear sem recompilar e, no futuro,
servir os mesmos dados para cliente e servidor.

```
data/*.json  ──►  GameData (autoload)  ──►  Sistemas (Combat, Progression, Inventory)
                                                     │
                                              Entidades (Player, Monster, Projectile)
                                                     │
                                                  Cenas / UI
```

## Fase 1 (single-player) — tudo no cliente Godot
```
client/
  scripts/core/         game_state.gd, save_system.gd, grid_movement.gd
  scripts/data/         game_data.gd (carrega JSON), loaders
  scripts/combat/       combat_system.gd, jutsu_executor.gd, damage_calc.gd
  scripts/progression/  xp_system.gd, skill_system.gd
  scenes/world/         maps, tilesets
  scenes/player/        player.tscn
  scenes/monsters/      monster_base.tscn
  scenes/ui/            hud.tscn, inventory.tscn, hotbar.tscn
```

## Fase 3 (multiplayer) — servidor autoritativo
- O servidor roda a **mesma lógica de combate/progressão** (por isso ela deve ser
  pura: funções que recebem estado e retornam resultado, sem depender de nós visuais).
- Cliente envia **intenções** (mover para X, usar jutsu Y no alvo Z).
- Servidor valida (cooldown, chakra, alcance, linha de visão) e envia **eventos**.
- Opções: Godot headless + ENet/MultiplayerAPI (mais simples, mesma linguagem)
  ou Node.js + Colyseus (mais ferramentas, duas linguagens).
- Persistência: PostgreSQL (contas, personagens, inventário). Supabase é aceitável
  para começar.

## Regras de fórmula (ver docs/sistemas/combate-e-jutsus.md)
Todas as fórmulas de dano/defesa/XP ficam em `scripts/combat/damage_calc.gd` e
`scripts/progression/xp_system.gd`, **sem estado**, testáveis via GUT
(Godot Unit Test).

## Movimento
Grid 32px, 4 direções, velocidade em tiles/segundo definida pelo personagem
(base 4, itens podem aumentar). Estilo Tibia: sem diagonal livre, sem física.
