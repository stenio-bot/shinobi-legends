# Sistema: Mapas (OTBM)

O mapa jogável do Shinobi Legends é um **OTBM** carregado pelo TFS 1.4.2 e editável no
**Remere's Map Editor**. Ele NÃO é gerado por `tools/export_tfs.py`: existe um pipeline
próprio em `tools/map/`, porque geometria de mapa não cabe em `data/*.json`.

| Arquivo | Papel |
|---|---|
| `tools/map/otbm.py` | leitor/gravador de OTBM (nós OTB, tiles, itens, towns, waypoints, house tiles) |
| `tools/map/items_otb.py` | leitor mínimo do `items.otb` (valida ids, grupo `ground`, flag de bloqueio) |
| `tools/map/spawn_xml.py` | gravador de `<mapa>-spawn.xml` e de `<mapa>-house.xml` vazio |
| `tools/map/build_valley.py` | gerador do mapa "Vale da Folha" |
| `server/generated/world/valley.otbm` | mapa gerado (não editar à mão) |
| `server/generated/world/valley-spawn.xml` | spawns de monstros e NPCs |
| `server/generated/world/valley-house.xml` | vazio e válido (o mapa não tem casas compráveis) |

## Formato OTBM (resumo)

```
"OTBM" ou \0\0\0\0            identificador (4 bytes)
0xFE <tipo> <props> [filhos] 0xFF     nó; 0xFD escapa 0xFD/0xFE/0xFF dentro de <props>

ROOT (tipo 0)        props: version(u32) width(u16) height(u16) major(u32) minor(u32)
  OTBM_MAP_DATA      props: DESCRIPTION / EXT_SPAWN_FILE / EXT_HOUSE_FILE
    OTBM_TILE_AREA   props: x(u16) y(u16) z(u8)  — blocos de 256x256 por andar
      OTBM_TILE      props: dx(u8) dy(u8) [ATTR_TILE_FLAGS] [ATTR_ITEM = chão]
      OTBM_HOUSETILE props: dx dy houseid(u32) …
        OTBM_ITEM    props: id(u16) + atributos (COUNT, ACTION_ID, UNIQUE_ID, TEXT,
                            TELE_DEST, DEPOT_ID, HOUSEDOORID, CHARGES, …)
    OTBM_TOWNS -> OTBM_TOWN        id(u32) nome(str) x(u16) y(u16) z(u8)
    OTBM_WAYPOINTS -> OTBM_WAYPOINT nome(str) x y z
```

Referência no código do servidor: `server/tfs/src/iomap.cpp`, `iomap.h` e `fileloader.cpp`.

`otbm.py` guarda os atributos de item como bytes crus na ordem original, então a
leitura + reescrita de um mapa é **fiel** (mesmo número de tiles, itens, flags,
house tiles, towns e waypoints).

## Layout do Vale da Folha

Cabeçalho 2048x2048 (OTBM v2, items 3.57). Todo o conteúdo está no **andar 7**,
na faixa **x 1000–1199, y 1000–1119** (200x120 = 24.000 tiles).

> O cabeçalho declara 2048x2048 e não 1024x1024 porque o conteúdo começa em
> (1000,1000) e vai até x=1199: o TFS ignora `width`/`height`, mas o Remere's usa
> esses valores para delimitar o canvas e recortaria tudo acima de 1023.

### Pontos de referência

| Lugar | Coordenadas (x, y, 7) |
|---|---|
| **Templo / posição da town 1 "Vila da Folha"** | **1029, 1042** |
| Prédio do templo (paredes de pedra) | 1025,1038 – 1033,1046, porta em 1029,1046 |
| Praça central (chão de pedra, zona de proteção) | 1022,1036 – 1036,1052 |
| Muralha da vila | 1010,1030 – 1049,1069 |
| Portão sul | 1028–1030, 1069 |
| Rua norte-sul (cobblestone) | x 1028–1030 |
| Rua leste-oeste (cobblestone) | y 1054–1056 |
| Loja do Ichiro, o Mercador | 1013,1038 – 1019,1043 (NPC em 1016,1041) |
| Loja do Mestre Hayato (pergaminhos) | 1039,1038 – 1045,1043 (NPC em 1042,1041) |
| Casa da Capitã Rin (missões) | 1039,1046 – 1045,1051 (NPC em 1042,1049) |
| Campo de treino (6 training dummies) | 1013,1046 – 1020,1052 |
| Depósito (depot chest) | 1024, 1051 |
| Casas de moradores (6, parede de madeira) | y 1032–1036 e y 1058–1063 |
| Rio (norte-sul, intransponível) | x 1125–1129 |
| **Ponte de pedra** (com parapeitos) | x 1124–1130, y 1058–1061 |
| Hub de NPCs do pântano | 1131,1055 – 1139,1064 |
| Velha Sumi / Rastreador Goro | 1133,1057 / 1135,1058 |
| **Torre de pedra** (interior 3x3) | 1163,1058 – 1167,1062, porta em 1163,1060 |
| Boss Sapo Ancião (dentro da torre) | 1165, 1060 |
| **Acampamento dos bandidos** | centro 1100, 1100 (raio 7) |
| Boss Chefe dos Bandidos | 1100, 1100 |

Waypoints gravados no OTBM: `Templo`, `Praca`, `Portao Sul`, `Ponte`, `Torre`,
`Acampamento`, `Hub Pantano`.

### Zonas

- **Vila da Folha** — muralha de pedra, ruas de cobblestone com tochas, praça e templo
  em **zona de proteção** (o interior do templo também tem `no-logout`).
- **Floresta** (level 1–10) — grama com manchas densas de árvores, trilhas de terra e um
  anel de trilha em volta da vila (y 1025 / y 1075, x 1005 / x 1055). Clareiras com
  Lobo, Bandido, Cobra da Floresta e Bandido Arqueiro. A sudeste, o acampamento dos
  bandidos com tendas, fogueira e cerca, guardado por bandidos.
- **Floresta da Morte** (level 10–25) — a leste do rio: chão de lama/pântano, árvores
  mortas, juncos e poças d'água. Sanguessuga Gigante, Sapo Gigante e Ninja Renegado,
  mais a **Serpente Branca** numa clareira isolada ("Ninho da Serpente", 1190,1015).

### Spawns

26 grupos, 58 monstros, 5 NPCs. Raio 3–4, `spawntime` 60–120 s para monstros comuns
e 3600 s para bosses.

| Monstro | Qtd |
|---|---|
| Lobo | 12 |
| Bandido | 10 |
| Cobra da Floresta | 7 |
| Bandido Arqueiro | 7 |
| Sanguessuga Gigante | 7 |
| Sapo Gigante | 7 |
| Ninja Renegado | 5 |
| Serpente Branca (boss) | 1 |
| Chefe dos Bandidos (boss) | 1 |
| Sapo Ancião (boss) | 1 |

## Como regenerar

```bash
.venv/bin/python tools/map/build_valley.py
```

O build **falha** (exit 1, nada é gravado) se:

- algum id usado não existir no `items.otb`;
- algum chão não for do grupo `ground`;
- o templo, algum centro de spawn, alguma criatura ou algum NPC não for alcançável a
  pé a partir do templo (BFS de 4 vizinhos sobre tiles caminháveis — portas contam
  como passáveis; água, paredes, árvores e arbustos bloqueiam).

Para inspecionar um OTBM qualquer:

```bash
.venv/bin/python tools/map/otbm.py server/generated/world/valley.otbm
```

## Como abrir no Remere's Map Editor

1. O RME precisa achar o mesmo `items.otb`/`items.xml` do servidor
   (`server/tfs/data/items/`) e os sprites 10.98 (`.spr`/`.dat`).
2. `File > Open` em `server/generated/world/valley.otbm`. Os arquivos
   `valley-spawn.xml` e `valley-house.xml` precisam estar **na mesma pasta** — os nomes
   vêm gravados no cabeçalho do OTBM (`OTBM_ATTR_EXT_SPAWN_FILE` / `EXT_HOUSE_FILE`).
3. Vá até o templo com `Search > Go to Position` → `1029, 1042, 7`.
4. Editar à mão é possível, mas o próximo `build_valley.py` sobrescreve tudo: mudanças
   permanentes devem ir para o gerador.

## Como instalar no servidor

```bash
cp server/generated/world/valley.otbm       server/tfs/data/world/
cp server/generated/world/valley-spawn.xml  server/tfs/data/world/
cp server/generated/world/valley-house.xml  server/tfs/data/world/
```

E em `server/tfs/config.lua`:

```lua
mapName = "valley"      -- sem o .otbm
```

O TFS resolve `valley-spawn.xml` e `valley-house.xml` pelo cabeçalho do OTBM
(caminhos relativos à pasta do mapa).

### Pré-requisito: NPCs

O TFS instancia NPC por nome: `<npc name="Ichiro, o Mercador"/>` no spawn procura
`data/npc/Ichiro, o Mercador.xml`. Hoje `tools/export_tfs.py` grava os NPCs em
`data/npc/naruto/<id>.xml` e aponta `script="naruto/<id>.lua"`, mas o TFS procura
scripts em `data/npc/scripts/`. Enquanto isso não for corrigido no exportador, os
NPCs não aparecem (o TFS os descarta em silêncio). Duas coisas precisam existir:

- `data/npc/<Nome do NPC>.xml` (pode ser cópia ou symlink do arquivo em `naruto/`);
- `data/npc/scripts/naruto/<id>.lua` (ou o `script=` apontando para o lugar certo).

## Testar sem mexer no servidor principal

`build_valley.py` não instala nada. Para validar o mapa isoladamente, crie uma pasta
com symlinks para `data/` e `build/`, um `config.lua` próprio com `mapName = "valley"`
e portas diferentes (7271/7272), e rode `./build/tfs` de dentro dela — o TFS lê o
`config.lua` do diretório atual.
