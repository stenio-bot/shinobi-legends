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
| Torre do Líder (prédio importado) | 1027,1031 – 1031,1036, porta em 1029,1036 |
| Loja do Ichiro, o Mercador (`newbie_shop`) | 1014,1040 – 1017,1043 (NPC na rua, 1015,1044) |
| Loja do Mestre Hayato (`ramen_shop`) | 1040,1040 – 1043,1044 (NPC na rua, 1042,1045) |
| Casa da Capitã Rin (`blue_shop`) | 1040,1048 – 1042,1051 (NPC na rua, 1041,1052) |
| Prisão | 1013,1060 – 1016,1063, porta em 1014,1063 |
| Taverna | 1032,1059 – 1036,1063, porta em 1034,1063 |
| Campo de treino (6 training dummies) | 1013,1046 – 1020,1052 |
| Depósito (depot chest) | 1024, 1051 |
| Casas de moradores (prédios importados) | y 1031–1036 e y 1059–1063 |
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

### Prédios importados

As casas e lojas de **parede de madeira vanilla** (`b.building(...)`, ids 5261–5277)
foram substituídas por prédios recortados de `assets-src/import/village_buildings.png`
(material de referência privado, no `.gitignore`). O recorte é
`tools/spr/slice_buildings.py`; os templates ficam em
**`assets-src/sprites/buildings.json`** e cada célula 32x32 é um **item novo**
(`bld_*` em `assets-src/sprites/tiles.json`, server ids **30008–30249**).

**São fachadas, não interiores.** Em Tibia tudo do prédio bloqueia; só a célula de
porta é caminhável (`group: "door"`, `walkable: true`), e ela não leva a lugar
nenhum. Por isso os NPCs de loja ficam **na rua**, um tile à frente da porta — antes
eles ficavam dentro do prédio, atrás de uma porta de madeira.

`tools/map/build_valley.py` estampa com:

```python
stamp_building(b, tpls, sid, "tavern", 1032, 1063, ground=DIRT)
```

O ponto `(x, y)` é o **canto inferior esquerdo**: a célula `(col, row)` da matriz do
template cai em `(x + col, y - (altura - 1 - row))`. A função limpa os itens do
retângulo inteiro, troca o chão se `ground` for dado, empilha os itens e devolve a
posição absoluta da porta.

| Template | Tamanho (col x lin) | Onde | Porta |
|---|---|---|---|
| `tower` (Torre do Líder) | 5x6 | 1027,1036 — ao norte da praça | 1029,1036 |
| `big_house` | 5x6 | 1013,1036 | 1014,1036 |
| `house_green` | 4x4 | 1040,1036 | 1041,1036 |
| `newbie_shop` (Ichiro) | 4x4 | 1014,1043 | 1015,1043 |
| `ramen_shop` (Hayato) | 4x5 | 1040,1044 | 1042,1044 |
| `blue_shop` (Rin) | 3x4 | 1040,1051 | 1041,1051 |
| `prison` | 4x4 | 1013,1063 | 1014,1063 |
| `blue_house` | 3x4 | 1021,1063 e 1041,1063 | col 1 da base |
| `tavern` | 5x5 | 1032,1063 | 1034,1063 |
| `roof_orange` | 3x4 | 1037,1063 (galpão) | — |
| `lamp_post` | 1x4 | 1021,1053 e 1037,1053 | — |
| `tree` / `bushes` / `big_bush` / `grass_patch` | 1–3 tiles | praça, campo de treino, fora do portão | — |
| `green_gate_a/b/c`, `gate_east` | muros verdes | fora do portão sul | — |
| `shop_east` | 3x3 | 1132,1062 (hub do pântano) | — |

O **templo continua sendo a PZ** e a posição da town — a torre foi colocada ao lado
(ao norte da praça), sem tocar no templo nem no `flag_rect` de proteção.

Ordem obrigatória ao mexer nesses prédios:

```bash
.venv/bin/python tools/spr/slice_buildings.py   # fatia a folha, escreve tiles.json/buildings.json
.venv/bin/python tools/spr/allocate_ids.py      # aloca server/client ids (NÃO toca no OTB)
.venv/bin/python tools/map/build_valley.py      # gera o mapa com esses ids
.venv/bin/python tools/spr/build_assets.py      # grava items.otb + Tibia.dat/.spr + items.xml
tools/install_generated.sh                      # instala no servidor
```

> **Aviso do gerador.** Enquanto os ids novos não estiverem no `items.otb`, o
> `build_valley.py` imprime `AVISO: N server ids de tiles novos ainda NAO existem no
> items.otb` e valida esses ids (>= 30000, presentes em `allocations.json`) usando as
> flags declaradas em `tiles.json`. Isso é deliberado, para o mapa poder ser gerado
> antes do build de assets. **Instalar o mapa sem rodar `build_assets.py` faz o TFS
> recusar os itens.**

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

- algum id usado não existir no `items.otb` **nem** em `allocations.json` com id
  >= 30000 (esse é o relaxamento descrito em "Prédios importados");
- algum chão não for do grupo `ground`;
- o templo, algum centro de spawn, alguma criatura ou algum NPC não for alcançável a
  pé a partir do templo (BFS de 4 vizinhos sobre tiles caminháveis — portas contam
  como passáveis; água, paredes, árvores e arbustos bloqueiam).

Para inspecionar um OTBM qualquer:

```bash
.venv/bin/python tools/map/otbm.py server/generated/world/valley.otbm
```

## Autoborder

Sem isso, grama, terra, lama e água terminavam em uma linha reta exatamente no
limite do tile — o "efeito xadrez" que denuncia mapa gerado por código. A
Tibia resolve isso com **tiles de borda** (autoborder): um item de
DECORAÇÃO, desenhado por cima do chão, com uma faixa irregular do material
"de cima" invadindo o tile do material "de baixo". `tools/map/build_valley.py`
tem um passe final, `apply_borders(b, sid)`, chamado depois de
`carve_clearings`/`connect_clearings` e antes de `build_spawns`/`validate`.

### Arte (`tools/spr/gen_borders.py`)

Gera 4 pares × 12 peças = 48 PNGs 32×32 RGBA (alpha binário, igual ao resto do
projeto) em `assets-src/sprites/terrain/borders/`, reusando as MESMAS paletas
e funções de ruído de `tools/spr/gen_terrain.py` (`P_GRASS`, `P_DIRT`,
`P_WATER`, `P_MUD`, `P_COBBLE`, `shared_field`, `quantize`, `Rnd`) — a borda
precisa casar pixel a pixel com o chão que ela cobre.

Convenção de nome do par: **`<alto>_<baixo>`** — o material ALTO manda a
faixa ondulada por cima do tile do material BAIXO, seguindo a hierarquia
`água < lama < terra < grama < cobble`. Pares gerados: `grass_dirt`,
`grass_water`, `grass_mud`, `cobble_dirt`. (A missão original pedia o par
"terra→cobblestone"; como a hierarquia diz que cobble é o material mais
alto de todos, o par foi implementado como `cobble_dirt` — cobblestone
invadindo terra —, e não o contrário, para não contradizer a própria
hierarquia que define o algoritmo.)

As 12 peças por par: `n, s, e, w` (bordas retas — o vizinho nessa direção é o
material alto), `cnw, cne, csw, cse` (cantos EXTERNOS: o alto só toca a
diagonal, uma língua curta) e `icnw, icne, icsw, icse` (cantos INTERNOS: o
alto cerca as duas laterais que formam aquele canto, sobra só um bolsão do
baixo na diagonal oposta).

```bash
.venv/bin/python tools/spr/gen_borders.py          # PNGs + folha de revisão
.venv/bin/python tools/spr/gen_borders.py --sheet  # só a folha, mais rápido
```

A folha de revisão fica em `assets-src/sprites/terrain/borders/_sheet.png`
(uma linha por par, uma coluna por peça, fundo = material baixo).

### Declaração de item (`assets-src/sprites/tiles.json`)

As 48 peças viram itens novos `border_<par>_<peça>` (chaves permanentes,
grupo `decoration`, `walkable: true`, `blocks_pathfind: false`, sem
`blocks_projectile`). Como toda borda, usam `on_top: true` + `top_order: 1`
— no `.dat`/OTB isso é a flag `FLAG_ALWAYSONTOP` com `topOrder=1`, que na
Tibia é exatamente a categoria "ground border": desenha por cima do chão e
por baixo de criaturas, itens soltos e efeitos (ver `tools/spr/tiles.py`,
`FLAG_ALIAS["on_top"] = "alwaysOnTop"` e `otb.new_item(..., top_order=...)`).
IDs alocados com `.venv/bin/python tools/spr/allocate_ids.py` (server ids
30250–30297 na primeira geração) — append-only, igual a todo o resto do
`tiles.json`.

### Algoritmo (`apply_borders` em `build_valley.py`)

Autoborder clássico por bitmask de 8 vizinhos (estilo Remere's Map Editor),
rodando **depois** que todo o chão final já foi pintado (florestas, trilhas,
vila, clareiras, ponte, pântano):

1. Cada tile de chão é classificado (`classify_ground`) em um dos 5
   materiais conhecidos (`grass`, `dirt`, `cobble`, `mud`, `water`) a partir
   dos ids vanilla usados em `GRASS`/`DIRT`/`COBBLE`/`MUD`/`WATER`; chão de
   pedra/madeira (praça, templo, interiores) não entra no autoborder — fica
   `None` e é ignorado.
2. Só materiais que aparecem como "baixo" em algum par têm vizinhos
   testados: `dirt` (pode ser invadido por `grass` OU `cobble`), `water` e
   `mud` (só por `grass`) — tabela `BORDER_INVADERS`.
3. Para cada tile-baixo e cada material-alto candidato, olha os 8 vizinhos
   (N, S, L, O, e as 4 diagonais) e decide as peças:
   - vizinho ortogonal (N/S/L/O) é o material alto → peça reta
     correspondente;
   - vizinho diagonal é o material alto **e nenhum** dos dois ortogonais
     adjacentes é → canto EXTERNO (contato isolado pela diagonal);
   - os dois ortogonais adjacentes a uma diagonal são o material alto **e**
     a diagonal também → canto INTERNO (o baixo só sobra num bolsão).
4. As peças viram itens (`b.put(x, y, sid[...])`) empilhados por cima do
   chão da célula — não substituem nada, e por isso o BFS de conectividade
   (`walkable_map`) continua enxergando o tile como caminhável: os itens de
   borda são `walkable`/não bloqueiam.

Na primeira geração do Vale da Folha isso colocou **1779 peças de borda** no
mapa inteiro (ver a linha `bordas (autoborder) N pecas` na saída de
`build_valley.py`) — principalmente grama/terra nas trilhas da floresta,
grama/lama na fronteira com a Floresta da Morte e cobblestone/terra nas ruas
e no portão da Vila da Folha.

### Visualizar sem o cliente (`tools/map/render_preview.py`)

```bash
.venv/bin/python tools/map/render_preview.py
# ou uma área específica:
.venv/bin/python tools/map/render_preview.py --area 1000 1020 1120 1080 \
    --out screenshots/preview_borders.png
```

Roda `build_valley` como biblioteca (mesma sequência exata do build real:
`build` → `carve_clearings` → `connect_clearings` → `apply_borders`) e
desenha 32px por tile usando os PNGs de `assets-src/sprites/terrain/`
(chão/objetos vanilla, via `assets-src/sprites/overrides/10_terrain.json`) e
de `tiles.json` (bordas, prédios importados, mobiliário). Servidor id sem PNG
conhecido é desenhado em magenta — sinal de que falta mapear alguma peça. É
assim que a arte das bordas foi ajustada e conferida (`Read` no PNG gerado)
sem precisar compilar assets nem abrir o OTClient.

## Decoração e ponte

Itens NOVOS de cenário — ponte de madeira, pedras, tocos, flores, tufos de
grama, cogumelos, galho caído, poça decorativa, tocha de rua em poste, placa
de trilha, barril, caixote, cerca de madeira e caminho de pedras soltas —
ficam em `assets-src/sprites/tiles_decor.json` (mesmo esquema do
`tiles.json`, arquivo **separado** de propósito: outro agente edita
`tiles.json` ao mesmo tempo para as bordas). O coordenador mescla as duas
listas antes de rodar `tools/spr/allocate_ids.py` (que só lê `tiles.json`) —
por isso as entradas de `tiles_decor.json` **não têm `server_id`/`client_id`**
ainda.

### Arte (`tools/spr/gen_decor.py`)

```bash
.venv/bin/python tools/spr/gen_decor.py
```

Desenha 31 PNGs 32×32 (`stone_large` é 64×64, 2×2) em
`assets-src/sprites/terrain/decor/`, reaproveitando as paletas e primitivas
de `tools/spr/gen_terrain.py` (`P_WOOD`, `P_STONE`, `P_BARK`, `P_GRASS_DOT`,
`P_FLOWER`, `P_PUDDLE`, `Rnd`, `put`, `rect`, `ellipse`, `outline`, `shade`,
`fbm`) em vez de duplicá-las. Fogueira do acampamento (id vanilla 1428) e
tendas (id vanilla 7605) **já existem** em `gen_terrain.py`/
`overrides/10_terrain.json` — não foram redesenhadas de novo.

### Ponte de madeira

Substitui o piso de pedra (431) + cerca (1533) usados hoje pela travessia do
rio (`build_valley.RIVER_X0/X1`, `BRIDGE_Y0/Y1`) por 5 tiles novos:

| Tile | Grupo | Flags |
|---|---|---|
| `bridge_wood_center` | `ground`, `speed: 100` | `walkable: true` |
| `bridge_wood_head_west` / `_east` | `ground`, `speed: 100` | `walkable: true` (cabeceiras, viga de ancoragem visual) |
| `bridge_wood_rail_north` / `_south` | `wall` | `walkable: false`, `has_height: true` (corrimão — item, não chão; bloqueia 1 tile) |

O chão cobre a mesma faixa que o piso de pedra ocupa hoje (`RIVER_X0-1` até
`RIVER_X1+1`, `BRIDGE_Y0` até `BRIDGE_Y1`); os corrimões ficam nas linhas
`BRIDGE_Y0-1` e `BRIDGE_Y1+1`, onde hoje está a cerca vanilla. `speed: 100`
casa com o piso de pedra/madeira vanilla (405/431), então atravessar a ponte
não muda a velocidade do personagem.

### Placement (`tools/map/decor.py`)

Funções **puras** — recebem o `Builder` já construído por
`build_valley.build(...)` e um dict `key -> server_id` — chamadas pelo
coordenador de dentro de `build_valley.py` (este módulo só **importa**
`build_valley`, nunca o edita):

| Função | O que coloca | Onde |
|---|---|---|
| `place_bridge(b, ids)` | ponte de madeira (chão + corrimão) | trecho do rio já usado pela ponte |
| `place_forest_decor(b, ids, rng)` | pedras/tocos/flores/tufos/cogumelos/galho/poça, densidade baixa (1.2%); pedras soltas (6%) sobre as trilhas de terra | floresta a oeste do rio, só em tiles de grama/terra sem item, fora da vila, fora das áreas protegidas (`b.is_protected`) e fora de um raio de segurança em torno de cada clareira de spawn (`CLEARINGS`) |
| `place_camp_decor(b, ids)` | barril/caixote junto a cada tenda + caixote perto da fogueira + trecho de cerca de madeira nova completando a paliçada ao sul | acampamento dos bandidos (`CAMP_CENTER`); fogueira/tendas vanilla **reaproveitadas**, não duplicadas |
| `place_village_decor(b, ids)` | tochas de rua (poste) nas 4 quinas da praça + placa de trilha perto do portão sul; tochas + placa extras no hub do pântano | vila da Folha (`PLAZA`) e hub de NPCs (`HUB`) |

`tools/map/decor.py` roda sozinho (`.venv/bin/python tools/map/decor.py`):
monta ids **fictícios** (30900+, só para o teste — nada é gravado em
`allocations.json`), roda `build_valley.build()` +
`carve_clearings`/`connect_clearings`, aplica as 4 funções acima e valida a
conectividade com o **mesmo BFS** de `build_valley.validate` — sem gravar
nenhum `.otbm`. Na primeira rodada: ponte com 42 tiles, ~72 itens de floresta
+ 78 pedras de trilha, 9 itens novos no acampamento, 8 tochas/placas novas em
vila+hub, sem regressão de conectividade (95.5% alcançável do templo, contra
95.6% do mapa sem esta decoração).

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
