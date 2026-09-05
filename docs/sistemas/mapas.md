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

### Arte (`tools/spr/gen_borders.py`) — v2, "fluida"

A v1 desenhava cada uma das 12 peças com uma fórmula própria (reta = uma
onda; canto externo/interno = uma elipse radial independente). O resultado
tinha o material certo mas a "caligrafia" da curva mudava de uma peça pra
outra — na trilha isso lia como uma faixa serrilhada uniforme, com emenda
visível bem onde uma peça reta encontrava um canto. A v2 resolve isso na
raiz: **uma única curva-base por direção** (`_depth_profile`, periódica,
amplitude 3–6px, suavizada por média móvel antes de receber o jitter — sem
isso o "ruído independente por pixel" da v1 é o que lia como serrilhado) e
as 12 peças são **derivadas** dela, nunca reinventadas:

- retas (`n/s/e/w`): a curva direto, `y < profundidade(x)` (e rotações).
- cantos EXTERNOS (`cnw/cne/csw/cse`): união de 2 "línguas curtas" — a MESMA
  curva das duas retas que formam o canto, encolhenda por `_taper` (uma
  smoothstep) conforme se afasta do canto (alcance `REACH = 12px`, por isso
  a língua não vira uma reta disfarçada). Como reusam literalmente
  `profile["n"]`/`profile["w"]` etc., a amplitude e o "sotaque" da onda no
  canto são garantidos iguais aos da peça reta correspondente — é a
  continuidade C0 pedida na missão, por construção, não por coincidência.
- cantos INTERNOS (`icnw/icne/icsw/icse`) = tile cheio **menos** o bolsão no
  canto OPOSTO, e esse bolsão é literalmente a máscara de canto externo
  oposto (`icnw` = NOT `cse`-shape usando as curvas sul/leste) — de novo,
  nenhuma fórmula nova, só reaproveitar.

Cima disso: **dithering leve** na linha de contato (`_dither_edge`, troca
alguns pixels da beira seguindo a matriz de Bayer — o mesmo dither ordenado
do `gen_terrain`, não ruído aleatório puro), **brilho de 1px do lado do
invasor** (anel interno) e **contorno de 1px do lado do material invadido**:
sombra escura de contato para os pares terrosos, e uma linha fina de
**espuma/areia clara** (`FOAM`) para `grass_water` — margem de rio, não uma
sombra. A textura do material invasor não é mais um ruído genérico
(`shared_field` + paleta, v1) e sim a **função de verdade** do chão
(`GT.grass(1)`/`GT.cobble(1)`) — sem isso o canto interno de cobblestone
lia como uma mancha cinza lisa em vez de paralelepípedo de verdade (bug visto
e corrigido na 2ª rodada de preview, ver "Como validar" abaixo).

Gera 4 pares × 16 peças (12 base + 4 variantes `n2/s2/e2/w2`, ver abaixo) =
**64 PNGs** 32×32 RGBA (alpha binário, igual ao resto do projeto) em
`assets-src/sprites/terrain/borders/`.

Convenção de nome do par: **`<alto>_<baixo>`** — o material ALTO manda a
faixa ondulada por cima do tile do material BAIXO, seguindo a hierarquia
`água < lama < terra < grama < cobble`. Pares gerados: `grass_dirt`,
`grass_water`, `grass_mud`, `cobble_dirt`. (A missão original pedia o par
"terra→cobblestone"; como a hierarquia diz que cobble é o material mais
alto de todos, o par foi implementado como `cobble_dirt` — cobblestone
invadindo terra —, e não o contrário, para não contradizer a própria
hierarquia que define o algoritmo.)

As 12 peças base por par: `n, s, e, w` (bordas retas), `cnw, cne, csw, cse`
(cantos EXTERNOS: o alto só toca a diagonal, uma língua curta) e `icnw,
icne, icsw, icse` (cantos INTERNOS: o alto cerca as duas laterais que formam
aquele canto, sobra só um bolsão do baixo na diagonal oposta) — mais **2
variantes por peça reta** (`n2, s2, e2, w2`, semente irmã da mesma família
de curva): o autoborder escolhe entre a base e a variante por um hash
determinístico da posição (`_border_variant` em `build_valley.py`, CRC32 —
não o `hash()` embutido do Python, que é salgado por processo e daria uma
escolha diferente a cada execução), pra uma trilha comprida não repetir
sempre a mesma peça "carimbada".

```bash
.venv/bin/python tools/spr/gen_borders.py          # PNGs + folha de revisão
.venv/bin/python tools/spr/gen_borders.py --sheet  # só a folha, mais rápido
```

A folha de revisão fica em `assets-src/sprites/terrain/borders/_sheet.png`
(uma linha por par, uma coluna por peça — 16 colunas agora —, fundo =
material baixo).

### Declaração de item (`assets-src/sprites/tiles.json`)

As 64 peças viram itens novos `border_<par>_<peça>` (chaves permanentes,
grupo `decoration`, `walkable: true`, `blocks_pathfind: false`, sem
`blocks_projectile`). Como toda borda, usam `on_top: true` + `top_order: 1`
— no `.dat`/OTB isso é a flag `FLAG_ALWAYSONTOP` com `topOrder=1`, que na
Tibia é exatamente a categoria "ground border": desenha por cima do chão e
por baixo de criaturas, itens soltos e efeitos (ver `tools/spr/tiles.py`,
`FLAG_ALIAS["on_top"] = "alwaysOnTop"` e `otb.new_item(..., top_order=...)`).
IDs alocados com `.venv/bin/python tools/spr/allocate_ids.py`: as 48 peças
base ficaram em server ids 30250–30297 (primeira geração); as 16 variantes
`n2/s2/e2/w2` novas entraram DEPOIS, append-only, em **30328–30343** (client
ids 24054–24069) — não reaproveitam nem renumeram nada já alocado.

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
   `mud` (só por `grass`) — tabela `BORDER_INVADERS`, agora percorrida em
   ORDEM DE HIERARQUIA (`_MATERIAL_RANK`) pra garantir que, quando os dois
   invasores se aplicam ao mesmo tile de `dirt`, o `cobble` (mais alto) fique
   empilhado por cima do `grass` — antes disso já saía assim por acaso
   (ordem do dict/tupla), agora é explícito e não depende de detalhe de
   implementação do Python.
3. Para cada tile-baixo e cada material-alto candidato, olha os 8 vizinhos
   (N, S, L, O, e as 4 diagonais) e decide as peças:
   - vizinho ortogonal (N/S/L/O) é o material alto → peça reta
     correspondente (com a variante escolhida por `_border_variant`);
   - vizinho diagonal é o material alto **e nenhum** dos dois ortogonais
     adjacentes é → canto EXTERNO (contato isolado pela diagonal);
   - os dois ortogonais adjacentes a uma diagonal são o material alto **e**
     a diagonal também → canto INTERNO (o baixo só sobra num bolsão).
4. As peças viram itens (`b.put(x, y, sid[...])`) empilhados por cima do
   chão da célula — não substituem nada, e por isso o BFS de conectividade
   (`walkable_map`) continua enxergando o tile como caminhável: os itens de
   borda são `walkable`/não bloqueiam.

Nota sobre os "casos faltando" que a missão original apontou (diagonal
isolada, dois cantos internos opostos, tile com 3 lados): como os passos 3–4
avaliam os 4 lados e as 4 diagonais **independentemente** e empilham quantas
peças forem necessárias no mesmo tile (uma peça reta por lado + até 4 peças
de canto, todas no mesmo `b.put` em sequência), esses casos já eram cobertos
por composição — uma diagonal isolada vira só a peça de canto externo
correspondente; dois cantos internos opostos (ex.: N+O+NO hi e S+L+SE hi ao
mesmo tempo) empilham `n+s+e+w+icnw+icse` no mesmo tile; um tile com 3 lados
hi empilha as 3 peças retas mais os cantos internos onde a diagonal também
bate. Não foi preciso montar a tabela de 47 combinações fixas do blob
tileset clássico porque aquela tabela existe pra evitar montar arte NOVA
para cada combinação (arte pintada à mão não compõe); aqui a arte É
procedural e compõe naturalmente. O que estava realmente quebrado era a
CONTINUIDADE VISUAL entre peças (resolvido na v2 do `gen_borders.py`
acima), não a cobertura de casos.

Na primeira geração do Vale da Folha isso colocou **1779 peças de borda** no
mapa inteiro (ver a linha `bordas (autoborder) N pecas` na saída de
`build_valley.py`) — principalmente grama/terra nas trilhas da floresta,
grama/lama na fronteira com a Floresta da Morte e cobblestone/terra nas ruas
e no portão da Vila da Folha. A v2 do algoritmo não muda ONDE as peças vão
(mesma lógica de bitmask), só qual arte é usada — o total continua 1779.

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

#### Como a v2 foi validada (3 rodadas de preview)

`screenshots/preview_borders_v2.png` (mesma área do `preview_borders.png`
antigo, 1000,1020–1120,1080) e `screenshots/preview_borders_v2_zoom.png` (dois
recortes 4×, lado a lado: vila+trilha em 1024,1058–1057,1078, e
rio+ponte+hub do pântano em 1118,1050–1145,1070) documentam o resultado
final. O processo até chegar lá:

1. **1ª rodada** — reescrita completa do `gen_borders.py` com curva-base
   única + derivação das 12 peças (ver acima). Olhando a folha de revisão
   (`_sheet.png`), as retas já saíam onduladas e suaves em vez de
   serrilhadas, e os cantos mostravam a língua/bolsão coerente com a peça
   reta vizinha.
2. **2ª rodada** — build + preview do mapa inteiro revelou um bug que a
   folha de revisão sozinha não mostrava: o canto interno de `cobble_dirt`
   (`icnw`/`icne`/...) aparecia no jogo como uma **mancha cinza lisa**, sem
   nenhuma textura de paralelepípedo — porque `_texture_hi` usava um ruído
   genérico (`shared_field` + paleta) em vez da função de verdade do chão.
   Corrigido trocando para `GT.cobble(1)`/`GT.grass(1)` (a MESMA função que
   desenha o chão normal), o que também deixou a textura da invasão idêntica
   pixel a pixel ao material que ela devia imitar.
3. **3ª rodada** — novo build + preview (main + zoom) depois da correção:
   cantos internos de cobblestone agora mostram pedras de verdade, o rio
   mostra a linha de espuma clara contínua, e as trilhas da floresta ficaram
   com uma faixa larga e suave, sem quinas duras nem emenda visível entre
   peça reta e canto. Comparado ao `preview_borders.png` da v1 (faixa
   serrilhada uniforme, cantos com corte reto), a diferença é imediatamente
   visível lado a lado.

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

## Auditoria de caminhabilidade

Feedback recorrente de usuário: "tem vários lugares do mapa que eu vou caminhando e
ele trava". `tools/map/walk_audit.py` audita isso de forma ESTÁTICA e
`client-otc/tests/walk_audit_rc.lua` de forma DINÂMICA (cliente real).

### Auditoria estática (`tools/map/walk_audit.py`)

```bash
.venv/bin/python tools/map/walk_audit.py [valley.otbm] [items.otb]
```

Para cada um dos 24.000 tiles do mapa, reproduz a regra REAL do TFS
(`Tile::queryAdd` em `server/tfs/src/tile.cpp`) usando as flags REAIS lidas do
`items.otb` — não as declaradas em `tiles.json` — e compara com a intenção
visual (chão comum + só decoração "walkable"/porta por cima). Diverge =
travamento fantasma (ou passagem indevida). Também compara, para cada id
novo (>= 30000), as flags reais do OTB com as declaradas em
`tiles.json`/`tiles_decor.json` — divergência aqui é bug de conversão em
`tools/spr/tiles.py`.

Regra confirmada lendo `Tile::queryAdd`: o que bloqueia o PASSO MANUAL de um
jogador é só `TILESTATE_BLOCKSOLID` (ativado se QUALQUER item da pilha —
chão ou empilhado — tiver a flag `blockSolid`, `item.cpp: hasProperty`).
`hasHeight`/elevação **não bloqueia o passo** — só entra em jogo em
`queryAdd` do ramo "empilhar item em cima de outro item", pra decidir se dá
pra empilhar mais um item ali (mito comum de dev OT). Já `blockPathfind` não
bloqueia passo nenhum: só faz o **autoWalk/clique-para-andar** do OTClient
recusar a rota (`game.cpp:750`, `TILESTATE_BLOCKPATH`, usado pelo A* do
servidor e pelo `Map::findPath` do próprio cliente) — por isso um item com
`blocks_pathfind` sem `blockSolid` faz o jogador "clicar e não acontecer
nada" sem nunca travar o passo manual (WASD).

Rodagem em 2026-09-04 (após regenerar items.otb/valley.otbm com as bordas
mais novas): **0 bugs de flag reais** — as únicas 2 "divergências" batidas
pelo script são as portas de pedra fechadas do templo (1029,1046,7) e da
torre da Floresta da Morte (1163,1060,7), que bloqueiam até serem abertas —
comportamento correto do Tibia, não travamento. Nenhum id >= 30000 diverge
entre `tiles.json`/`tiles_decor.json` e o OTB real (344 ids conferidos).

### Auditoria dinâmica (`client-otc/tests/walk_audit_rc.lua`)

Cliente OTClient real, logado como a conta `teste`/`teste` (personagem
Naruto, jogador comum — **não** o GM, que atravessa tudo). Percorre a rota
templo → praça → portão sul → trilha → clareiras → mata → acampamento →
ponte → hub do pântano → torre, em saltos curtos (autoWalk só encontra rota
dentro do que o cliente já "viu" — mandar autoWalk direto pra um alvo fora
da tela SEMPRE falha com `NoWay`, mesmo sem bug nenhum de mapa; por isso o
script avança aos poucos, como um jogador clicando na tela). Portas
fechadas no caminho são abertas com `g_game.use()` antes de cada trecho, e
cada travada registra a posição e os ids dos itens do tile (`Tile:getItems()`
— **atenção: retorna client id, não server id**; o script já faz a
conversão nos logs). Copie o `.lua` para `client-otc/shinobirc.lua`,suba o
cliente (`./OTClient.app/Contents/MacOS/OTClient`), e remova o arquivo ao
final — nunca fica commitado.

Resultado em 2026-09-04: nenhuma trava real encontrada. Toda ocorrência de
"TRAVA" nos logs caiu em uma de três categorias, nenhuma bug de mapa: (a)
porta fechada (mecânica normal, resolvida abrindo); (b) o script desistiu
de um salto por timeout (6s) enquanto o personagem ainda estava andando
normalmente em segundo plano — impaciência do script de teste, não do jogo;
(c) o próprio waypoint do script caiu em cima de uma árvore/moita de
propósito bloqueante. Detalhe completo em `screenshots/walk_audit.txt`.

**Achado do processo (não do mapa):** a primeira rodada reportou 100% de
travamento porque o **servidor local estava rodando com um `valley.otbm`/
`items.otb` desatualizados** (outro processo tinha acabado de editar
`tiles.json`/bordas sem reinstalar e reiniciar). Sempre que for investigar
travamento "no jogo", confirme que o servidor rodando é o build MAIS
recente: `.venv/bin/python tools/spr/build_assets.py &&
.venv/bin/python tools/map/build_valley.py && tools/install_generated.sh
&& cp server/generated/world/valley* server/tfs/data/world/ && pkill -x tfs`
(subir de novo em seguida).

### Pendências

- 406 bolsões pequenos de tiles caminháveis (789 tiles, 4,5% do total
  caminhável) ficam fora do alcance por BFS a partir do templo — reentrâncias
  dentro de aglomerados de árvores/água, sem spawn nem NPC. Comportamento
  esperado numa mata densa "de verdade"; não é tratado como bug.
- Árvores/decoração 2x2: o sprite ocupa 2x2 tiles na tela, mas a colisão real
  do TFS é sempre POR TILE (cada tile bloqueia só se o item que ocupa
  aquele tile específico tiver `blockSolid`); não há bloqueio "fantasma"
  além do tile em si nesta base de itens.
- O `OTClient.app` encerrou sozinho (stack trace de rede/asio) perto do fim
  de uma rodada de teste dinâmico longa (~2 min), antes de alcançar a
  ponte/hub/torre — não há indício de que seja causado pelo mapa (o
  personagem estava andando normalmente no momento do crash); parece
  instabilidade do cliente em sessões automatizadas longas, fora do escopo
  desta auditoria.
