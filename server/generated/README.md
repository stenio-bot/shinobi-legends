# server/generated — conteúdo gerado do TFS 1.4.2

Gerado por `tools/export_tfs.py` a partir de `data/*.json`. **Não edite à mão**; edite o JSON e regenere.

| Pasta | Destino no TFS | Como instalar |
|---|---|---|
| `monster/naruto/*.xml` | `data/monster/naruto/` | copiar a pasta |
| `monster/monsters_naruto.xml` | `data/monster/monsters.xml` | colar as linhas dentro de `<monsters>` |
| `spells/spells_naruto.xml` | `data/spells/spells.xml` | colar dentro de `<spells>` |
| `spells/scripts/naruto/*.lua` | `data/spells/scripts/naruto/` | copiar a pasta |
| `items/items_naruto.xml` | `data/items/items.xml` | colar (ids placeholder: ver `data/tfs_mapping.json`) |
| `XML/vocations.xml` | `data/XML/vocations.xml` | substituir o arquivo |
| `XML/outfits.xml` | `data/XML/outfits.xml` | substituir o arquivo (PENDENTE no install_generated.sh, ver relatório) |
| `lib/naruto_villages.lua` | `data/lib/` + `dofile` em `lib.lua` | PENDENTE no install_generated.sh, ver relatório |
| `npc/naruto/*` | `data/npc/naruto/` | copiar a pasta |
| `lib/naruto_quests.lua` | `data/lib/` + `dofile` em `lib.lua` | ver cabeçalho |
| `scripts/naruto/*.lua` | `data/scripts/naruto/` | revscriptsys carrega sozinho |
| `world/*-spawn.xml` | referência para o Remere's Map Editor | manual |

Totais: 21 monstros, 25 jutsus, 80 itens, 9 NPCs, 15 missões, 4 vocações.
