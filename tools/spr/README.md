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
| `otb.py` | Leitor mínimo do `items.otb` do TFS (serverId → clientId, flags, grupo). |
| `art.py` | Pixel art placeholder desenhada por código (Pillow). Nada é copiado de outro jogo. |
| `gen_placeholders.py` | Desenha os PNGs em `assets-src/sprites/` e escreve o `manifest.json`. |
| `build_assets.py` | Lê o manifesto + PNGs + `items.otb` e escreve `Tibia.spr`/`Tibia.dat`. |
| `dump_dat.py` | Lê um par `.spr`/`.dat`, imprime estatísticas, valida e exporta PNGs. |

## Uso

```bash
# 1. (re)desenhar os placeholders e regravar o manifesto
.venv/bin/python tools/spr/gen_placeholders.py

# 2. compilar spr + dat para o cliente
.venv/bin/python tools/spr/build_assets.py

# 3. conferir o resultado
.venv/bin/python tools/spr/dump_dat.py
.venv/bin/python tools/spr/dump_dat.py --thing creature:129 --thing item:3031
.venv/bin/python tools/spr/dump_dat.py --export 40 --export-dir /tmp/spr-dump
```

Dependência: `Pillow` (`.venv/bin/pip install pillow`).

Opções úteis:

- `build_assets.py --manifest <caminho> --out <pasta>` — gerar em outro lugar.
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
