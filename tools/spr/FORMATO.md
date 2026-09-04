# Formato Tibia.spr / Tibia.dat 10.98 (fonte da verdade: código do OTClient Redemption)

Tudo aqui foi lido de `client-otc/src/client/`:

| Assunto | Arquivo | Função |
|---|---|---|
| Cabeçalho do .dat, ordem das categorias | `thingtypemanager.cpp` | `ThingTypeManager::loadDat` |
| Atributos e geometria de cada thing | `thingtype.cpp` | `ThingType::unserialize` (linha ~493) |
| Animação estendida | `animator.cpp` | `Animator::unserialize` |
| Cabeçalho e RLE do .spr | `spritemanager.cpp` | `loadRegularSpr`, `getSpriteImage` |
| Máscara de cores de outfit | `thingtype.cpp` `loadTexture` + `creature.cpp` `drawCreature` | — |
| Features ligadas por versão | `modules/game_features/features.lua` | `onClientVersionChange` |

Todos os inteiros são **little-endian** (`FileStream::getU16/U32` fazem leitura LE).

---

## 1. Features relevantes em 1098

De `modules/game_features/features.lua`:

| Feature | Ativa em 1098? | Efeito no arquivo |
|---|---|---|
| `GameSpritesU32` (>=960) | **sim** | contagem de sprites e ids de sprite no .dat são **U32** |
| `GameEnhancedAnimations` (>=1050) | **sim** | grupos com >1 fase carregam um bloco `Animator` |
| `GameIdleAnimations` (>=1057) | **sim** | criaturas têm **frame groups** (U8 de contagem + U8 de tipo por grupo) |
| `GameNegativeOffset` | **não** (comentada) | deslocamento é `U16`, não `int16` |
| `GameSpritesAlphaChannel` | **não** (nunca habilitada) | **pixels no .spr são RGB (3 bytes), sem alpha** |

> A dúvida "RGBA ou RGB?" fica resolvida: `spritemanager.cpp:280` faz
> `useAlpha = g_game.getFeature(Otc::GameSpritesAlphaChannel)` e essa feature não é
> habilitada em lugar nenhum (nem no C++ nem nos módulos Lua). Logo `channels = 3`.
> O cliente força `alpha = 0xFF` em todo pixel colorido.

`client_version` também precisa bater com o `.otb`: `items.otb` do TFS tem
`minorVersion = 57 = CLIENT_VERSION_1098`.

---

## 2. Tibia.spr

```
U32  signature                       (arbitrário; o cliente só guarda o valor)
U32  spriteCount                     (U16 se GameSpritesU32 desligada — em 1098 é U32)
U32  offset[spriteCount]             endereço absoluto de cada sprite; 0 = sprite vazio
... blobs de sprite ...
```

`offset[i]` corresponde ao **sprite id `i+1`** (`getSpriteImage` faz `seek((id-1)*4 + m_spritesOffset)`).
**Sprite id 0 é sempre "nada"** e não tem entrada na tabela.

Cada blob:

```
U8 U8 U8    cor-chave transparente (o cliente faz skip(3); pode ser 0xFF,0x00,0xFF)
U16         pixelDataSize — número de bytes do bloco RLE que vem a seguir
<RLE>       sequência de runs, até 32*32 pixels escritos
```

Um run:

```
U16  transparentPixels    quantos pixels transparentes pular
U16  coloredPixels        quantos pixels coloridos vêm a seguir
byte[coloredPixels * 3]   R,G,B de cada pixel (SEM alpha em 1098)
```

Pixels são escritos em ordem raster (linha por linha, esquerda→direita, topo→base).
O loop pára quando acabam os bytes (`offset + 4 <= pixelDataSize`) ou quando o
sprite enche (32*32*4 bytes de saída). Pixels não escritos ficam transparentes,
então **não é preciso fechar o sprite com um run final**.

Limite prático: `coloredPixels` é lido como U16 mas o cliente processa no máximo
4096 pixels por run (`MAX_PIXEL_BLOCK`) — como um sprite tem 1024 pixels, nunca é problema.

---

## 3. Tibia.dat

```
U32  signature            (m_contentRevision = 16 bits baixos)
U16  maxItemId
U16  maxCreatureId
U16  maxEffectId
U16  maxMissileId
<thing de item 100..maxItemId>
<thing de creature 1..maxCreatureId>
<thing de effect 1..maxEffectId>
<thing de missile 1..maxMissileId>
```

`loadDat` faz `count = getU16() + 1` e depois itera `id` de `firstId` até `count-1`,
com `firstId = 100` para itens e `1` para as demais categorias. Ou seja: **o U16 gravado
é o maior id da categoria** e é obrigatório existir um registro para *todo* id do intervalo.
Ordem das categorias = `ThingCategoryItem, Creature, Effect, Missile` (`const.h:1159`).

### 3.1 Bloco de atributos

Lista de bytes de atributo terminada por `0xFF` (`ThingLastAttr`). Alguns carregam dados.
Como a versão é >= 1000, `unserialize` **remapeia** o byte lido:

```
f == 16   -> NoMoveAnimation(253)
f == 254  -> Usable(34)
f == 35   -> DefaultAction(251)
f  > 16   -> f - 1
senão     -> f
```

Para **gravar**, aplique o inverso (é o que `build_assets.py` faz em `ATTR_TO_FILE`):

| Atributo (enum interno `const.h:1180`) | byte no arquivo | dados |
|---|---|---|
| Ground = 0 | 0 | U16 groundSpeed |
| GroundBorder = 1 | 1 | — |
| OnBottom = 2 | 2 | — |
| OnTop = 3 | 3 | — |
| Container = 4 | 4 | — |
| Stackable = 5 | 5 | — |
| ForceUse = 6 | 6 | — |
| MultiUse = 7 | 7 | — |
| Writable = 8 | 8 | U16 maxTextLength |
| WritableOnce = 9 | 9 | U16 maxTextLength |
| FluidContainer = 10 | 10 | — |
| Splash = 11 | 11 | — |
| NotWalkable = 12 | 12 | — |
| NotMoveable = 13 | 13 | — |
| BlockProjectile = 14 | 14 | — |
| NotPathable = 15 | 15 | — |
| Pickupable = 16 | **17** | — |
| Hangable = 17 | 18 | — |
| HookSouth = 18 | 19 | — |
| HookEast = 19 | 20 | — |
| Rotateable = 20 | 21 | — |
| Light = 21 | 22 | U16 intensity, U16 color |
| DontHide = 22 | 23 | — |
| Translucent = 23 | 24 | — |
| Displacement = 24 | 25 | U16 x, U16 y (U16 porque GameNegativeOffset está off) |
| Elevation = 25 | 26 | U16 |
| LyingCorpse = 26 | 27 | — |
| AnimateAlways = 27 | 28 | — |
| MinimapColor = 28 | 29 | U16 |
| LensHelp = 29 | 30 | U16 |
| FullGround = 30 | 31 | — |
| Look (ignore look) = 31 | 32 | — |
| Cloth = 32 | 33 | U16 slot |
| Market = 33 | 34 | U16 cat, U16 tradeAs, U16 showAs, string nome, U16 vocação, U16 level |
| Usable = 34 | **254** | — |
| NoMoveAnimation = 253 | **16** | — |
| DefaultAction = 251 | **35** | U16 |
| *fim da lista* | **255** | — |

Strings no `.dat` são `U16 tamanho + bytes`.

Se o byte 255 nunca aparecer em `ThingLastAttr` iterações (255), o cliente lança
`corrupt data (...)` — é o erro mais comum de .dat mal gerado.

### 3.2 Geometria

```
[só para creature, porque GameIdleAnimations está ligada]
U8 groupCount
para cada grupo:
    U8 frameGroupType        (0 = Idle/Default, 1 = Moving)
    U8 width
    U8 height
    U8 exactSize             <-- SÓ existe se width > 1 OU height > 1
    U8 layers
    U8 patternX
    U8 patternY
    U8 patternZ              (existe porque clientVersion >= 755)
    U8 animationPhases
    [se animationPhases > 1 e GameEnhancedAnimations:]
        U8   async           (0 = assíncrono; 1 = sincronizado)
        S32  loopCount
        S8   startPhase      (-1 = aleatório)
        para cada fase: U32 durationMin, U32 durationMax
    U32 spriteId[ width*height*layers*patternX*patternY*patternZ*animationPhases ]
```

Para item/effect/missile não existe `groupCount`/`frameGroupType`: é um grupo só.

Limite: soma de sprites de todos os grupos <= 4096, senão o cliente lança exceção.

### 3.3 Ordem dos sprite ids

`ThingType::getSpriteIndex` (thingtype.cpp:1014):

```
index = ((((((a % phases) * patternZ + z) * patternY + y) * patternX + x) * layers + l)
          * height + h) * width + w
```

Ou seja, gravar nos laços aninhados nesta ordem (mais externo → mais interno):
**fase `a` → `z` → `y` → `x` → camada `l` → `h` → `w`**.

`h`/`w` são contados a partir do **canto inferior direito**: o cliente desenha o
sprite `(w,h)` na posição `(width-w-1, height-h-1) * 32`.

Com vários frame groups, os blocos são simplesmente concatenados e `a` percorre
`idlePhases + movingPhases` (por isso `getIdleAnimationPhases()` = total − fases do animator).

### 3.4 Padrões por categoria

- **item**: `patternX/Y/Z` são variações visuais (bordas de chão, pilhas). 1×1×1 basta.
- **creature**: `patternX` = direção, na ordem do enum `Otc::Direction`: **0=Norte, 1=Leste,
  2=Sul, 3=Oeste** (`creature.cpp:897`). `patternY` = addons (0 = base, 1..3 = addons,
  desenhados por cima). `patternZ` = montaria (1 = sem montaria).
- **effect**: 1×1×1, várias fases (a animação roda sozinha).
- **missile**: `patternX = 3`, `patternY = 3` — grade 3×3 de direções de voo
  (índice = 1 + sinal do deslocamento em x/y), 1 fase.

### 3.5 Cores de outfit (layers = 2)

`ThingType::loadTexture` (thingtype.cpp:856): se a categoria é creature e `layers >= 2`,
o cliente expande para 5 camadas de textura: **base + 4 máscaras**. A camada 1 do .dat
(o "template") é reutilizada nas 4 máscaras via `Image::overwriteMask(cor)`:
pixels **exatamente iguais** à cor procurada viram branco opaco, o resto vira transparente.
Depois `creature.cpp:436` desenha cada máscara com `CompositionMode::MULTIPLY`:

| Cor no sprite template (exata, alpha 255) | Pintada com |
|---|---|
| `255,0,0` vermelho | **body** (`getBodyColor`) |
| `0,255,0` verde | **legs** |
| `0,0,255` azul | **feet** |
| `255,255,0` amarelo | **head** |

Qualquer outro pixel do template é ignorado. Como o resultado é MULTIPLY sobre a base,
a área a ser colorida deve ser **clara (quase branca)** na camada 0, senão a cor não aparece.

---

## 4. Armadilhas encontradas

1. **RGB, não RGBA.** Escrever 4 bytes por pixel produz sprites embaralhados.
2. **Todo id do intervalo precisa existir** no .dat, inclusive os que "não usamos" —
   `loadDat` lê sequencialmente. Um id a menos desalinha o arquivo inteiro.
3. **`exactSize` só existe quando width>1 ou height>1.** Gravar sempre desalinha os 2×2.
4. **Itens começam no id 100.** Os ids 0..99 não existem no arquivo.
5. **Sprite id é 1-based**; 0 significa "célula vazia" e é válido no `.dat`.
6. O módulo `game_things` tem um *fallback* que reativa features e tenta de novo
   (`tryLoadDatWithFallbacks`) — ou seja, um .dat errado pode "carregar" com as features
   erradas e desenhar lixo em vez de dar erro. Sempre valide com `dump_dat.py`.

---

## 5. O `.dat` também precisa bater com o protocolo (não só carregar)

Um `.dat` pode carregar sem erro e **mesmo assim quebrar o jogo**: o servidor decide
quantos bytes extras manda por item a partir do `items.otb`, e o cliente decide
quantos ler a partir do `.dat`. Qualquer divergência desalinha o pacote de mapa e
aparece como `ProtocolGame::getThing: invalid thing id`.

`NetworkMessage::addItem` (`server/tfs/src/networkmessage.cpp:101`) manda:

```
U16  clientId
U8   0xFF                       (MARK_UNMARKED)
U8   contagem                   se it.stackable
U8   subtipo (fluidMap)         senão, se it.isSplash() || it.isFluidContainer()
U8   0xFE                       se it.isAnimation
```

`ProtocolGame::getItem` (`client-otc/src/client/protocolgameparse.cpp:4321`) lê:

```
U16  clientId
U8   mark                       se GameThingMarks (>= 1000)  -> sim em 1098
U8   contagem                   se isStackable() || isFluidContainer() || isSplash() || isChargeable()
U8   fase                       se GameItemAnimationPhase (>= 910) E getAnimationPhases() > 1
U8+  tipo de contêiner          se GameContainerTypes (>= 1320) -> NÃO em 1098
```

Traduzindo para o gerador:

| Origem no `items.otb` | Obrigatório no `.dat` |
|---|---|
| `FLAG_STACKABLE` (1<<7) | atributo `Stackable` |
| grupo `ITEM_GROUP_FLUID` | atributo `FluidContainer` |
| grupo `ITEM_GROUP_SPLASH` | atributo `Splash` |
| **`FLAG_ANIMATION` (1<<24)** | **`animationPhases >= 2`** (+ bloco `Animator`) |

O caso do `FLAG_ANIMATION` é o mais traiçoeiro porque não é um atributo, é a
**geometria**: se o thing tem 1 fase, o cliente não lê o `0xFE` e sobra 1 byte por
item animado (água, tochas, fogo, teleportes...). As duas fases podem apontar para
o mesmo sprite — o que importa é a contagem.

`isChargeable` não é alcançável em 1098 (o byte 254 do arquivo vira `Usable`), e
`GameCountU16` não é habilitada, então a contagem é sempre `U8`.

`dump_dat.py` confere esses quatro flags **item a item** contra o `items.otb`.
