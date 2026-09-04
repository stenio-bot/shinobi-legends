# tools/spr — mini-ObjectBuilder em Python

Gera o par `Tibia.spr` / `Tibia.dat` **versão 10.98** que o OTClient Redemption
precisa em `client-otc/data/things/1098/`, a partir de PNGs e de um manifesto JSON.
Existe porque não temos ObjectBuilder no Mac e porque nenhum sprite da Tibia ou de
NTO pode ser redistribuído (ADR-002).

## Arquivos

| Arquivo | O que faz |
|---|---|
| `FORMATO.md` | **Especificação do formato**, derivada do código do cliente. Leia antes de mexer. |
| `sprformat.py` | Leitura/escrita de `.spr` e `.dat` (RLE, atributos, frame groups). |
| `otb.py` | Leitura **e escrita** do `items.otb` do TFS (serverId → clientId, flags, grupo, luz, speed). |
| `tiles.py` | Itens NOVOS de cenário: manifesto → item do OTB + thing do `.dat` + `<item>` do `items.xml`. |
| `gen_tiles.py` | Desenha os PNGs de `assets-src/sprites/tiles/` (Pillow). |
| `test_otb_roundtrip.py` | Prova que ler e reescrever o `items.otb` dá o mesmo arquivo, byte a byte. |
| `art.py` | Pixel art placeholder desenhada por código (Pillow). Nada é copiado de outro jogo. |
| `gen_terrain.py` | **Terreno** (chão tileável, árvores, paredes, portas, mobiliário) desenhado por código, estilo Tibia 7.x/8.x. Escreve `assets-src/sprites/terrain/`. |
| `gen_placeholders.py` | Desenha os PNGs em `assets-src/sprites/` e escreve o `manifest.json`. |
| `build_assets.py` | Lê o manifesto + PNGs + `items.otb` e escreve `Tibia.spr`/`Tibia.dat`. |
| `dump_dat.py` | Lê um par `.spr`/`.dat`, imprime estatísticas, valida e exporta PNGs. |
| `import_sheets.py` | Recorta sprites soltos de uma folha PNG (componentes conexos) + folha de revisão. |
| `imports.py` | Aplica `assets-src/sprites/imports.json` por cima do manifesto (arte importada). |

## Uso

```bash
# 0. (opcional) recortar as folhas de sprites do usuário em assets-src/import/
.venv/bin/python tools/spr/import_sheets.py

# 1. (re)desenhar os placeholders e regravar o manifesto
.venv/bin/python tools/spr/gen_placeholders.py

# 2. compilar spr + dat para o cliente
.venv/bin/python tools/spr/build_assets.py

# 2b. (opcional) redesenhar os tiles próprios de cenário
.venv/bin/python tools/spr/gen_tiles.py

# 2c. (opcional) redesenhar o terreno do mapa (grama, cobble, árvores, muros...)
.venv/bin/python tools/spr/gen_terrain.py

# 3. conferir o resultado
.venv/bin/python tools/spr/dump_dat.py
.venv/bin/python tools/spr/test_otb_roundtrip.py
.venv/bin/python tools/spr/dump_dat.py --thing creature:129 --thing item:3031
.venv/bin/python tools/spr/dump_dat.py --export 40 --export-dir /tmp/spr-dump
```

Dependência: `Pillow` (`.venv/bin/pip install pillow`).

Opções úteis:

- `build_assets.py --manifest <caminho> --out <pasta>` — gerar em outro lugar.
- `build_assets.py --no-otb` — não reescrever o `items.otb` (só `.spr`/`.dat`).
- `build_assets.py --tiles <caminho>` — outro manifesto de tiles.
- `build_assets.py --no-imports` — ignorar o `imports.json` (só placeholders).
- `dump_dat.py --dir <pasta>` — inspecionar outro par de arquivos.

## Manifesto (`assets-src/sprites/manifest.json`)

Gerado por `gen_placeholders.py`, mas é um arquivo comum — pode ser editado à mão
para apontar para arte definitiva.

```jsonc
{
  "format": 1,
  "client_version": 1098,
  "sprite_size": 32,
  "dat_signature": "0x57BBD603",
  "sheet_root": "assets-src/sprites",

  "items": {
    "otb": "server/tfs/data/items/items.otb",
    "sheets":   { "<apelido>": "items/arquivo.png" },
    "rules":    [ { "style": "...", "when": {...}, "sheet": "<apelido ou template>" } ],
    "override_id_space": "server",
    "overrides": { "<serverId do TFS>": { "name": "...", "sheet": "items/own/x.png" } }
  },

  "things": [
    {
      "category": "creature",          // creature | effect | missile | item
      "id": 129,
      "name": "bandit_129",
      "width": 1, "height": 1, "exact_size": 32,
      "layers": 2,                      // 2 = base + template de cores de outfit
      "pattern_x": 4, "pattern_y": 1, "pattern_z": 1,
      "frame_groups": [
        { "type": 0, "phases": 1 },     // 0 = parado
        { "type": 1, "phases": 3,       // 1 = andando
          "animation": { "async": false, "loop_count": 0, "start_phase": 0,
                         "durations": [[220,220],[220,220],[220,220]] } }
      ],
      "sheets": ["creatures/look_129_l0.png", "creatures/look_129_l1.png"],
      "attrs": [["A_NOT_WALKABLE"], ["A_LIGHT", 6, 215]]   // opcional
    }
  ]
}
```

### Layout das folhas (PNG)

Cada `sheet` é uma grade; **um arquivo por camada**:

- largura = `pattern_x * width * 32`
- altura = `(soma das fases de todos os frame_groups) * pattern_z * pattern_y * height * 32`
- coluna = `x` (para criaturas: 0=Norte, 1=Leste, 2=Sul, 3=Oeste)
- linha = `((fase * pattern_z + z) * pattern_y + y)`, com as fases dos frame groups
  concatenadas na ordem em que aparecem

Cada célula tem `width*32 × height*32` px e é recortada em sprites de 32×32 pelo build.
O canal alpha é binário: `alpha < 128` vira transparente, o resto vira opaco
(o `.spr` de 1098 é RGB, sem alpha — ver `FORMATO.md`).

### Cores de outfit (camada 1)

Na camada 1 de uma criatura, pinte com estas cores **exatas**:

| Cor | Região colorida pelo servidor |
|---|---|
| `#FF0000` | body (colete) |
| `#00FF00` | legs (calça) |
| `#0000FF` | feet (sandália) |
| `#FFFF00` | head (cabelo/bandana) |

O cliente multiplica a cor do outfit sobre a base, então a região correspondente
na **camada 0 precisa ser clara** (quase branca) para a cor aparecer.

### Regras de item

Os things de item cobrem **todo clientId referenciado pelo `items.otb`**
(hoje 100..23725), porque o cliente lê o `.dat` sequencialmente — faltar um id
desalinha o arquivo inteiro. Pelo mesmo motivo, `gen_placeholders.py` varre
`server/tfs/data/monster/**/*.xml` e `server/tfs/data/npc/*.xml` atrás de
`look type="..."` e gera criaturas de 1 até o maior looktype encontrado, e gera
efeitos e missiles de **1 a 255** (o protocolo 10.98 manda esses ids em U8).

O estilo visual do item vem da primeira `rule` que casa:

```jsonc
{ "style": "wall",
  "when": { "group": "ground" | "group_in": [...],
            "flags_all": ["BLOCK_SOLID"], "flags_none": ["PICKUPABLE"],
            "flags_any": [...], "top_order": 2 },
  "sheet": "wall_{v3}",              // {v3}/{v4}/{v6}/{v8} = clientId % N
  "fallback_sheet": "wall_0" }       // usado se o apelido resolvido não existir
```

`{minimap_color}` também é aceito no nome da folha (usado nos chãos).

Os `overrides` são indexados pelo **server id do TFS** (o mesmo número que está em
`data/tfs_mapping.json`); o build traduz para clientId usando o `items.otb`.

## Adicionando arte de verdade

1. Desenhe o PNG seguindo o layout de folha acima e salve em `assets-src/sprites/`.
2. Aponte a entrada do manifesto (ou o `override` do item) para o novo arquivo.
3. `.venv/bin/python tools/spr/build_assets.py`
4. `.venv/bin/python tools/spr/dump_dat.py` — precisam aparecer `validacao: OK`
   **e** `divergencias=0` nas quatro linhas da conferência contra o `items.otb`
   (stackable / fluid / splash / animation). Essas quatro decidem quantos bytes o
   cliente lê por item no pacote de mapa; ver `FORMATO.md` seção 5.

Não edite `Tibia.spr`/`Tibia.dat` à mão: eles são artefatos gerados.


## Itens NOVOS de cenário (`assets-src/sprites/tiles.json`)

O `manifest.json` só sabe dar arte a itens que **já existem** no `items.otb`. Para
casa de vila, portão, placa, tatame etc. é preciso **criar** o item: entrada nova
no `items.otb` (serverId + clientId + flags + grupo), thing no `.dat`/`.spr` e
entrada no `items.xml` do servidor. Isso é o `tiles.json`, um manifesto separado e
**mantido à mão** (o `gen_placeholders.py` reescreve o `manifest.json`, então
declarações manuais lá se perderiam).

```jsonc
{
  "format": 1,
  "server_id_base": 30000,      // items.otb vanilla vai até 26381
  "client_id_base": 23726,      // vanilla vai até 23725 — a faixa fica CONTÍGUA
  "tiles": [
    {
      "key": "paper_lantern",              // identidade permanente (chave do id)
      "name": "lanterna de papel",
      "group": "decoration",               // ground|wall|door|decoration|furniture|container
      "size": [1, 1],                      // tamanho do DESENHO em tiles
      "frames": ["tiles/paper_lantern_0.png",
                 "tiles/paper_lantern_1.png"],   // 1 PNG por fase de animação
      "animation": { "durations": [[600,600],[420,420]] },
      "light":  { "level": 7, "r": 255, "g": 204, "b": 102 },
      "elevation": 8,
      "flags": { "walkable": false, "movable": false, "has_height": true },
      "xml": { "description": "Chochin acesa; oscila devagar." }
    }
  ]
}
```

### Como adicionar um tile novo do zero

1. **Desenhe** o PNG. O caminho mais curto é acrescentar uma função em
   `tools/spr/gen_tiles.py` e registrá-la no dicionário `TILES` — assim a arte
   fica versionada como código e reprodutível. Um PNG externo também serve; ele
   só precisa ter `largura*32 × altura*32` px, RGBA com **alpha binário**
   (`alpha < 128` = transparente; o `.spr` de 1098 é RGB).
2. `.venv/bin/python tools/spr/gen_tiles.py` (se usou o gerador).
3. **Declare** o tile em `assets-src/sprites/tiles.json` com uma `key` nova.
4. `.venv/bin/python tools/spr/build_assets.py` — ele aloca os ids, reescreve o
   `items.otb`, põe o thing no `.dat`/`.spr` e gera
   `server/generated/items/items_tiles_naruto.xml`.
5. **Valide**: `dump_dat.py` precisa terminar em `validacao: OK` com
   `divergencias=0`, e `test_otb_roundtrip.py` em `RESULTADO: OK`.
6. Injete o XML no `server/tfs/data/items/items.xml` (é o
   `tools/install_generated.sh` que faz isso) e suba o servidor: não pode
   aparecer nenhum `[Warning - Items::…]`.

### Flags de alto nível → `itemflags_t`

| chave em `flags` | vira |
|---|---|
| `walkable: false` | `FLAG_BLOCK_SOLID` (+ `FLAG_BLOCK_PATHFIND`, salvo `blocks_pathfind: false`) |
| `blocks_projectile` | `FLAG_BLOCK_PROJECTILE` |
| `has_height` | `FLAG_HAS_HEIGHT` (a altura em pixels vem de `elevation`) |
| `on_top` (+ `top_order` 1–3) | `FLAG_ALWAYSONTOP` e o atributo `GroundBorder`/`OnBottom`/`OnTop` do `.dat` |
| `pickupable` / `stackable` / `movable` / `useable` | `FLAG_PICKUPABLE` / `STACKABLE` / `MOVEABLE` / `USEABLE` |
| `readable` (+ `allow_dist_read`) | `FLAG_READABLE` / `FLAG_ALLOWDISTREAD` |
| `rotatable`, `hangable`, `vertical`, `horizontal`, `force_use`, `look_through`, `cannot_decay`, `full_tile` | a flag homônima |
| `otb_flags: ["..."]` | escape hatch: nomes crus de `itemflags_t` |

`2+ frames` ligam **automaticamente** `FLAG_ANIMATION` no OTB e
`animationPhases = 2` no `.dat` — os dois **precisam** casar (seção 5 do
`FORMATO.md`).

O `group` do manifesto vira grupo do OTB assim: `ground`→`ground`,
`container`→`container`, todo o resto→`none`. `door` fica `none` de propósito:
o TFS 1.4.2 trata `ITEM_GROUP_DOOR` como deprecated e marca a porta pelo
`items.xml` (`<attribute key="type" value="door"/>`).

### Regras de id

- Server id a partir de **30000** (o `items.otb` vanilla vai até 26381).
- Client id a partir de **23726**, **sequencial e contíguo** — o `.dat` é lido
  sequencialmente, um buraco desalinha o arquivo inteiro.
- A alocação vive em **`assets-src/sprites/allocations.json`**, indexada pela
  `key`. É **append-only**: um id já alocado nunca é renumerado nem reaproveitado,
  senão mapas e saves já gravados passariam a apontar para outro item. Remover um
  tile do `tiles.json` apenas aposenta o id.
- `"server_id": N` no tile força um id específico (útil para itens que já estão
  num mapa). O build recusa se o id já estiver ocupado ou se contradisser o
  `allocations.json`.

### Backup do `items.otb`

Na primeira vez que grava itens novos, o build copia o `items.otb` original para
**`server/tfs/data/items/items.otb.vanilla`** (uma única vez, nunca sobrescrito).
A partir daí **o `.vanilla` é sempre a base** do build: os itens existentes são
regravados byte a byte a partir dele e os tiles são anexados no fim. Por isso
rodar o build duas vezes dá exatamente o mesmo arquivo, e nenhum tile duplica.

Para voltar ao OTB de fábrica: `cp items.otb.vanilla items.otb` e rode o build
com `--no-otb`.


## Arte importada (`assets-src/sprites/imports.json`)

Folhas de sprites reais do usuário ficam em `assets-src/import/` — pasta **no
`.gitignore`**, nada dali é versionado (ADR-002). O caminho é:

```bash
# 1. recorta cada sprite da folha e gera a folha de revisão numerada
.venv/bin/python tools/spr/import_sheets.py
#    -> assets-src/import/extracted/<folha>/<idx>.png
#    -> assets-src/import/extracted/<folha>_contact.png   <- CONFIRA ESTA
#    -> assets-src/import/extracted/<folha>.json

# 2. edite assets-src/sprites/imports.json ligando <idx> -> looktype/efeito/item
# 3. compile normalmente
.venv/bin/python tools/spr/build_assets.py
.venv/bin/python tools/spr/dump_dat.py
```

`import_sheets.py` detecta o fundo (cor mais comum + o verde `34,177,76` dos
retângulos de chroma key), dilata a máscara por `--dilate` px só para juntar
partes soltas do mesmo sprite, rotula os componentes conexos e recorta cada um
com alpha. O raio de dilatação é **por folha** (`DEFAULT_SHEETS`): 1 no
`monsters_sheet`, 0 no `npcs_sheet`. Se um sprite sair partido, aumente; se dois
colarem, diminua — e olhe a folha de revisão de novo.

`imports.json` é **versionado** e só cita caminhos dentro de `extracted/`. O
`imports.py` o aplica por cima do `manifest.json` no build, com prioridade
**import > override de placeholder > regra de estilo**, e **ignora com aviso**
toda entrada cujo PNG não exista — numa máquina sem o material o build roda igual
e cai no placeholder.

Suporta criaturas de **1×1 a 4×4** (32/64/96/128 px). Criaturas importadas usam
`layers = 1` (a arte já vem colorida; o cliente só aplica as cores de outfit com
`layers = 2`), a mesma imagem nas 4 direções e nas fases de andar. O formato dos
campos (`src`, `frames`, `crop`, `tiles`, `grow`, `duration`, `rotate`,
`server_ids`) está em `docs/sistemas/arte-e-sprites.md`, seção
"Importar folhas de sprites".


## Terreno do mapa (`gen_terrain.py` + `overrides/10_terrain.json`)

O `valley.otbm` e feito de itens **vanilla** do `items.otb` (grama 4526–4531,
cobblestone 19744–19748, arvores 2700–2716, muro 1049–1051, agua 4608...). Sem
arte propria esses ids caiam nas *rules* de estilo e viravam quadrado chapado.

```bash
.venv/bin/python tools/spr/gen_terrain.py     # desenha assets-src/sprites/terrain/
.venv/bin/python tools/spr/build_assets.py
.venv/bin/python tools/spr/dump_dat.py        # validacao: OK, divergencias=0
```

O mapeamento server id -> PNG esta em
**`assets-src/sprites/overrides/10_terrain.json`**. O `build_assets.py` varre
`assets-src/sprites/overrides/*.json` em ordem alfabetica e aplica cada arquivo
com o **mesmo esquema do `imports.json`** — o prefixo numerico so define a ordem.

Diferente de `tiles.json`, isto **nao cria item nenhum**: o item ja existe no OTB,
so a arte muda. E diferente de `assets-src/import/`, a arte aqui e **versionada**
(desenhada por codigo, ADR-002).

### Campos de `items` aceitos pelo `imports.py`

Entrada simples (1x1, 1 quadro) so troca a folha do item. Qualquer um dos campos
abaixo faz a entrada virar um **thing de item completo** no manifesto (geometria
e atributos proprios); como o build aplica os `things` do manifesto **depois** de
`build_items()`, a arte de regra e substituida.

| Campo | Efeito |
|---|---|
| `"tiles": 2` | 64x64 = 2x2 tiles, ancorado no canto **inferior direito** (a arte sobe e vai para a esquerda, como as arvores da Tibia) |
| `"height": 64` | 1 tile de largura x 2 de altura — paredes/portas sobem 32px acima do tile |
| `"frames": [...]` + `"duration"` | animacao: `animationPhases > 1` com bloco `Animator` |
| `"displacement": [x, y]` | atributo `Displacement` do `.dat` |
| `"crop": [x, y, w, h]` | recorte da origem (herdado do `imports.json`) |

Grupo/flags/luz/`speed` vem do `items.otb` (`build_assets.item_attrs`), entao
chao continua sendo chao e porta continua sendo porta.

**`FLAG_ANIMATION` manda na contagem de fases** (secao 5 do `FORMATO.md`):

- item **sem** a flag + varios `frames` -> reduzido a 1 fase, com aviso
  `imports: AVISO: ...` na saida do build;
- item **com** a flag + 1 unico quadro -> duplicado para 2 fases.

A agua do mapa (`4608`, shallow water) **tem** a flag no `items.otb` — por isso as
3 fases de onda sao validas e nao foi preciso trocar o id no mapa.

### Estilo

Paleta limitada (4–6 tons), ruido de valor **periodico** em 32px (a emenda entre
tiles vizinhos some), dither de Bayer 4x4, contorno escuro de 1px nos objetos e
sombra **opaca** (o `.spr` de 1098 e RGB, nao existe alpha parcial). Todas as
variantes de um material partem de um campo base comum (`shared_field`), senao o
campo vira um xadrez de tiles claros e escuros visivel de longe.

`assets-src/sprites/terrain/_sheets/` e **gerado** pelo build; nao edite a mao.
