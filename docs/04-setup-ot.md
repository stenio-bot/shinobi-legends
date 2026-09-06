# 04 — Setup do ambiente Open Tibia (macOS, Apple Silicon)

## Visão
```
[OTClient Redemption]  ──TCP 7171/7172──►  [TFS 1.4.2]  ──►  [MariaDB]
   client-otc/                                server/tfs/
   assets: data/things/1098/ (.spr/.dat)      data/: monstros, spells, npc, mapa .otbm
```

## 1. Toolchain (uma vez)
```bash
brew install cmake ninja pkg-config mariadb
git clone https://github.com/microsoft/vcpkg ~/vcpkg && ~/vcpkg/bootstrap-vcpkg.sh
echo 'export VCPKG_ROOT=$HOME/vcpkg' >> ~/.zshrc && source ~/.zshrc
```

## 2. Cliente
```bash
cd client-otc
cmake --preset macos-release        # 1ª vez baixa e compila dependências via vcpkg (30–60 min)
cmake --build --preset macos-release
```
Binário em `client-otc/build/macos-release/otclient`. Rode a partir de `client-otc/` (precisa de `init.lua`, `modules/`, `data/`).

### Cliente: como rodar

Compilar (a 1ª vez o vcpkg baixa e compila ~40 dependências; conte 30–60 min):

```bash
cd client-otc
export VCPKG_ROOT=$HOME/vcpkg
cmake --preset macos-release                              # configure + vcpkg
cmake --build --preset macos-release --target otclient    # compila só o cliente
```

Acompanhar uma compilação longa sem travar o terminal:

```bash
cd client-otc
export VCPKG_ROOT=$HOME/vcpkg
( cmake --preset macos-release > build-configure.log 2>&1
  echo "CONFIGURE_EXIT=$?" >> build-configure.log
  cmake --build --preset macos-release --target otclient > build-compile.log 2>&1
  echo "BUILD_EXIT=$?" >> build-compile.log ) &
tail -f client-otc/build-compile.log     # termina com BUILD_EXIT=0 se deu certo
```

Rodar. **Sempre a partir de `client-otc/`**: o cliente procura `init.lua`, `modules/` e `data/`
no diretório atual.

```bash
cd client-otc
./build/macos-release/otclient 2>&1 | tee shinobi.log
```

Se o build gerar um bundle `OTClient.app` em vez do binário solto, o Gatekeeper barra a
primeira execução (o binário não é assinado por um Developer ID). Limpe a quarentena e
assine localmente uma vez:

```bash
cd client-otc
xattr -cr build/macos-release/OTClient.app
codesign --force --deep --sign - build/macos-release/OTClient.app
./build/macos-release/OTClient.app/Contents/MacOS/otclient 2>&1 | tee shinobi.log
```

Checagens rápidas no `shinobi.log`:

- `naruto_theme: termos aplicados ... locale = pt_br` → o tema carregou.
- nenhuma linha `ERROR` de módulo (`Unable to load module`, `failed to load style`).
- `Unable to translate: "..."` é só `pdebug`, não é erro: indica termo sem tradução.

**Sem sprites o cliente não entra no jogo.** `data/things/1098/` está vazio (ver *Assets*
acima), então a conexão com o servidor falha ao carregar o `.dat`/`.spr`. A **tela de login
já aparece normalmente** — é ela que valida todo o trabalho de identidade visual.

Screenshot da janela. `screencapture` exige que o processo que o chama tenha permissão de
**Gravação de Tela** (Ajustes do Sistema → Privacidade e Segurança); sem isso ele falha com
`could not create image from display`. O caminho que sempre funciona é pedir ao próprio
cliente que salve o framebuffer dele — `g_app.doScreenshot(nome)` escreve no *write dir*:

```bash
cd client-otc
cat > shinobirc.lua <<'LUA'
scheduleEvent(function() g_app.doScreenshot('/screenshot_login.png') end, 6000)
LUA
./OTClient.app/Contents/MacOS/OTClient > shinobi.log 2>&1 &
sleep 20
cp ~/Library/Application\ Support/shinobi/.shinobi/screenshot_login.png screenshot_login.png
rm shinobirc.lua                      # é só um utilitário de captura, não versionar
```

> O arquivo de *runtime config* do cliente é `/<compactName>rc.lua`, e o compact name deste
> projeto é `shinobi` — ou seja, **`shinobirc.lua`**. O `otclientrc.lua` que veio do upstream
> não é mais carregado (`init.lua:175`).

O *write dir* é `~/Library/Application Support/shinobi/.shinobi/` — é lá que ficam também o
`config.otml` e os presets de controle em `controls/keybinds/` e `controls/hotkeys/`.

### Identidade visual (o que foi customizado)

| Arquivo | O que faz |
| --- | --- |
| `data/locales/pt_br.lua` | Locale pt-BR completo, **cp1252** (ver nota abaixo) |
| `modules/naruto_theme/` | Termos Tibia→Naruto (Mana→Chakra, skills, jutsus); define `pt_br` como padrão |
| `data/images/background.png` | Arte própria 1920×1080 da tela de login (vila ninja à noite) |
| `data/images/clienticon.png` | Ícone próprio (folha + shuriken de chakra) |
| `tools/gen_art_shinobi.py` | Gera as duas imagens acima por código (stdlib, sem Pillow) |
| `modules/client_background/` | Título `SHINOBI LEGENDS` + subtítulo `Narutibia PvM` |
| `data/styles/50-ninja.otui` | Paleta (`$chakraBlue`, `$leafGreen`, `$sandGold`, `$nightBg`…) e estilos do tema |
| `modules/game_healthinfo/` | Barras recoloridas: vida vermelho-alaranjado, chakra azul-claro |
| `modules/corelib/keybind.lua` | Presets de controle: `Folha`, `Nevoa`, `Nuvem`, `Areia` |

Regenerar a arte (determinística, mesma seed → mesma imagem):

```bash
cd client-otc
python3 tools/gen_art_shinobi.py data/images/background.png data/images/clienticon.png
```

> **Encoding: use cp1252, não UTF-8.** As fontes do OTClient são bitmaps indexados por
> **byte** (`src/framework/graphics/ttfloader.cpp` gera glifos só de 32 a 255, e
> `bitmapfont.cpp` indexa com `static_cast<uint8_t>(text[i])`). Texto UTF-8 com acento
> ocupa 2 bytes e sai como mojibake na tela. O campo `charset` das tabelas de locale é
> decorativo — nada no código o lê. Por isso `data/locales/pt_br.lua` e
> `modules/naruto_theme/naruto_theme.lua` estão gravados em cp1252, como os demais
> locales do upstream. Ao editar, preserve o encoding:
> `iconv -f cp1252 -t utf-8 arquivo.lua` para ler, e converta de volta ao salvar.

> **Presets de keybind em ASCII.** O nome do preset vira nome de arquivo
> (`/controls/keybinds/<nome>.otml`), então `Nevoa` vai sem acento de propósito: um `é` em
> cp1252 produziria um nome de arquivo inválido em UTF-8 no macOS.

### Interface: o que foi removido (limpeza "Tibia clássico", 2026-09-04)

Regra: nada de branding de terceiros e nenhum botão que só faz sentido no Tibia oficial.
Módulos **não são apagados** — são desativados no `.otmod` (facilita merge com o upstream).

**Tela de login**

| Onde | O que saiu |
| --- | --- |
| `modules/client_topmenu/topmenu.otui` | Widgets `topLeftDiscord`, `topLeftYoutube` e `topLeftOnlinePlayers` (ícones/links de Discord e YouTube e o contador "players online"). O `leftButtonsPanel` passou a ancorar em `parent.left` (antes era `prev.right`, que apontava para o bloco do YouTube). |
| `modules/client_topmenu/topmenu.lua` | Variáveis e `recursiveGetChildById` desses widgets; `setPlayersOnline/setDiscordStreams/setYoutubeStreams/setYoutubeViewers/setLinkYoutube/setLinkDiscord` viraram **no-op** (client_entergame ainda as chama quando há `Services.status`); `extendedView()` não mexe mais neles. |
| `modules/client/client.otmod` | `client_bottommenu` comentado do `load-later` — some o painel inferior inteiro (Boosted Creature, Boosted Boss, Event Schedule/calendário e o card de "hints" que linkava `github.com/mehah/otclient/wiki`). |
| `modules/client_entergame/entergame.lua` | As três checagens `g_modules.getModule("client_bottommenu"):isLoaded()` passaram por um helper `isBottomMenuLoaded()` tolerante a `nil`. |
| `modules/client_options/styles/misc/help.otui` | Botões **Wiki** e **Info** (abriam `github.com/mehah/otclient/wiki`). Sobraram "Clear Cache" e "Change language". |

"players online" dependia do webservice (`Services.status`, comentado em `init.lua`), então saiu junto.

**Barra de topo (ícones da direita)**

Sobraram só os padrão Tibia: **áudio, opções, sair**. Os ícones de ferramenta de dev foram
escondidos (`:hide()` logo após o `addTopRightToggleButton`) — os módulos continuam carregados
e acessíveis por atalho:

| Módulo | Botão escondido | Atalho que continua valendo |
| --- | --- | --- |
| `modules/client_terminal/terminal.lua` | `terminalButton` | `Ctrl+T` |
| `modules/client_debug_info/debug_info.lua` | `debugInfoButton` | `Ctrl+Alt+D` |
| `modules/dev_otui/dev_otui.lua` | `otuiEditorButton` | `Ctrl+Alt+U` |

**Em jogo (`game_mainpanel`)**

| Onde | O que saiu |
| --- | --- |
| `modules/game_mainpanel/mainpanel.lua` | O botão grande **"Store shop"** (`createButton_large` no `optionsController:onInit`) e a função `toggleStore()`. |
| `modules/game_interface/interface.otmod` | `game_cyclopedia` comentado (juntou-se a prey, imbuing, market, shop, store, highscore, blessing, rewardwall, forge, taskboard, wheel, proficiency, que já estavam). |
| `modules/game_cyclopedia/game_cyclopedia.otmod`, `game_analyser/analyser.otmod`, `game_taskboard/tasks.otmod`, `game_proficiency/proficiency.otmod` | `autoload: true` → `autoload: false`. **Esses quatro tinham `autoload`**, ou seja, carregavam sozinhos mesmo estando comentados no `interface.otmod` — era daí que vinham os botões órfãos (Cyclopedia, Boss Slots, Bosstiary, trackers, Task Hunt, Kill Tracker, Weapon Proficiency, Analyser). |
| `modules/game_quickloot/quickloot.otui` | Painel `vipPanel` ("Get Premium", que chamava `toggleStore`) com `visible: false` — o widget continua existindo porque `quickloot.lua` o referencia. |

Chamadas que apontavam para módulos agora desativados ganharam guarda (`modules.x and ...`):

- `modules/game_minimap/minimap.lua` → `openCyclopediaMap()` cai sempre no `fullscreen()`.
- `modules/game_interface/gameinterface.lua` → `toggleInternalFocus()` / `modules.game_analyser`.
- `modules/game_quickloot/quickloot.otui` → `modules.game_cyclopedia.show("items")`.

> Atenção com OTML: comentário **só em linha própria** (`# ...`). Um `#` no fim de uma linha de
> valor (`autoload: false   # nota`) quebra o parser com
> `Unable to discover module from file ...: OTML error`.

**O que ficou em jogo:** inventário, skills, battle, minimapa, VIP, quest log, lista de jutsus
(spelllist), hotkeys, opções, sair, chat, action bar, health/chakra. Confirmado em runtime — os
únicos botões do painel direito são `hotkeysWindowButton`, `vipListButton`, `battleButton`,
`skillsButton`, `spelllistButton`, `questLogButton` (+ `optionsMainButton` e `logoutButton` no
painel de "specials").

Validação: `tools/autotest_client.sh god god` → **erros do cliente: 0**, screenshots em
`screenshots/autotest_0*.png`. A tela de login não é capturada pelo autotest; use o truque do
`shinobirc.lua` temporário descrito acima (`screenshots/autotest_00_login.png`).

### Jutsus no cliente (lista de jutsus + barra de ação)

O OTClient traz só as spells da Tibia, então a Lista de Jutsus e a `game_actionbar` nasceriam
vazias. O módulo `client-otc/modules/naruto_theme` resolve isso (detalhes e formato em
`docs/sistemas/combate-e-jutsus.md`, seção "Hotbar"):

| Arquivo | O que é | Como regerar |
|---|---|---|
| `client-otc/modules/naruto_theme/jutsus_data.lua` | GERADO. Perfil `'Shinobi'` de `SpellInfo`/`SpelllistSettings` com os 25 jutsus + `NarutoVillages`. | `python3 tools/export_tfs.py` |
| `client-otc/data/images/game/spells/jutsus.png` | Folha de ícones 32×32 (arte própria, versionada). | `.venv/bin/python tools/spr/gen_jutsu_icons.py` |
| `client-otc/modules/naruto_theme/naruto_jutsus.lua` | Registra o perfil, troca a Lista de Jutsus para ele e preenche a barra inferior 1. | manual |

As duas gerações usam a **mesma ordem** de jutsus (elemento → tier → level → id); ao mexer em
`data/jutsus/*.json` rode as duas.

Mudanças mínimas em módulos originais (documentadas aqui porque fogem da regra "não editar
`game_*`"):

- `modules/gamelib/spells.lua`: nova função `Spells.getSpellProfileOf(spellData)` (descobre a
  qual perfil uma entrada pertence).
- `modules/game_actionbar/logics/ActionButtonLogic.lua` e `logics/ActionAssignmentWindows.lua`:
  o perfil da folha de ícones deixou de ser fixo em `'Default'` e passa a vir do próprio
  `spellData` / do perfil ativo da spelllist. Sem isso o slot com jutsu mostraria o ícone errado.

O conjunto de hotkeys fica em `~/Library/Application Support/shinobi/.shinobi/settings/clientoptions.json`
(um conjunto por vila: `Vila da Folha`, `Vila da Nevoa`, `Vila da Nuvem`, `Vila da Areia`). Para
testar o preenchimento do zero, apague o conjunto da vila desse JSON e relogue.

Validação (2026-09-04, servidor em 127.0.0.1:7171): login `god`, `/vila folha`, `/lvl 40`,
`/jutsus`, relog → barra inferior 1 com 10 jutsus em F1–F10, Lista de Jutsus com 25 entradas
(10 visíveis no filtro da vila), clique no slot 1 → `GM: katon goukakyuu` e dano no Lobo.
**0 erros no log do cliente.** Screenshots: `screenshots/actionbar_barra.png`,
`screenshots/actionbar_lista.png`, `screenshots/actionbar_cast.png`.

### Menu Shinobi (`client-otc/modules/naruto_menu/`)

Janela única com abas, estilo Tibia clássico (`MainWindow` + `TabBar` do `data/styles/`),
título **Shinobi**. Módulo próprio, `sandboxed`, `autoload-priority: 1100` — a faixa
1000–9999 é a única que o `init.lua` carrega **depois** do `game_interface`
(`autoLoadModules(999)` → `ensureModuleLoaded('game_interface')` → `autoLoadModules(9999)`).

Arquivos:

| Arquivo | O que tem |
|---|---|
| `naruto_menu.otmod` | módulo (autoload 1100, `menuController:init()`) |
| `naruto_menu.otui` | estilos + a janela; paleta copiada de `data/styles/50-ninja.otui` |
| `naruto_menu.lua` | Controller, opcode 210, abas, noclip |
| `client-otc/data/images/game/shinobi_menu.png` | ícone 20x20 do botão (bandana + folha) |

**Como abrir:** botão `Shinobi` no `game_mainpanel` (`addToggleButton('shinobiMenu', ...)`),
atalho **Ctrl+J** (`Keybind.new('Windows', 'Show/hide Shinobi menu', 'Ctrl+J', '')`) e
**automaticamente** quando chega um `state` com `first_time = true` (abre na aba Personagem).

**Abas**

- **Personagem** — uma linha por personagem do `state.characters`, com preview `UICreature`
  (mesmo widget do `game_outfit`) usando o `looktype`, nome + vila, descrição, elemento padrão
  e nº de jutsus. O atual fica marcado com borda verde e "ATUAL"; nos outros o botão
  **Escolher** manda `{"type":"select","character":"<id>"}`.
- **Elemento** — 5 botões grandes (Fogo/Água/Raio/Terra/Vento) com as cores da paleta ninja;
  clicar num deles lista os 4 jutsus daquele elemento (vindos do `state.elements`), com selos,
  chakra e recarga. **Escolher** manda `{"type":"select","element":"<id>"}`.
- **Jutsus** — os 8 `active_jutsus`, com ícone tirado da folha
  `data/images/game/spells/jutsus.png`. O índice do ícone vem de `NarutoSpellIcons` /
  `NarutoSpellInfo` (`jutsus_data.lua`): casa o `id` do servidor com o campo `.icon` do jutsu;
  se o id não existir no cliente a linha aparece sem ícone (sem erro). **Usar** fala os selos
  (`g_game.talk`) e **Preencher barra** chama
  `modules.naruto_theme.fillActionBarWithWords(words, 'shinobi_menu')`, que grava os 8 selos
  na barra de ação inferior 1 (F1..F8) num conjunto de hotkeys próprio.
- **Comandos** — só aparece quando o `state` diz `is_gm: true`. Botões `/god`, `/full`,
  `/arena`, `/pvm`, `/lvl 50`, `/lvl 100`, campo + `/m <nome>`, campo + `/tp x,y,z`, e o
  toggle **Atravessar tudo (noclip)**.

**Enquanto o servidor não responde** a janela abre vazia com "Aguardando servidor..." e
nenhum erro no log. Ela pede o estado com `{"type":"get_state"}` ao abrir e 2,5 s depois do
login, caso nada tenha chegado.

**Encoding:** o servidor manda JSON em UTF-8, mas as fontes do OTClient são bitmaps indexados
por byte. O módulo converte **toda string recebida de UTF-8 para cp1252** (`utf8ToCp1252`)
antes de mostrar; sem isso "adversário" aparece como "adversÃ¡rio".

#### Noclip de GM — como o truque funciona

O TFS não tem "noclip". O que existe é o `/tp x,y,z` do `gm_tools.lua`, que só responde para
conta GOD. Com o toggle ligado, quando um passo do jogador é recusado o cliente calcula o tile
de destino (posição + direção do passo) e manda `g_game.talk('/tp x,y,z')` para lá — o servidor
teleporta 1 tile e o efeito é o de ter atravessado a parede/árvore. Na prática, o mapa inteiro
fica desbloqueado na versão do GM.

São **dois gatilhos**, porque um só não cobre tudo:

1. `LocalPlayer.onCancelWalk` — `src/client/localplayer.cpp` faz
   `callLuaField("onCancelWalk", direction)` dentro de `cancelWalk()`. Dispara quando o
   **servidor** recusa o passo (`0xB5 GameServerCancelWalk`): PZ, criatura no caminho etc.
2. Gatilho de "passo barrado pelo próprio cliente". Com a feature `GameAllowPreWalk` ligada
   (o `game_features/features.lua` liga sempre), o `game_walk/walk.lua` testa
   `toTile:isWalkable()` e dá `return false` **antes** de mandar qualquer coisa para o
   servidor — ou seja, contra uma árvore o evento de cancel walk nunca acontece. Por isso o
   módulo também escuta as teclas de andar (o `corelib/keyboard.lua` aceita vários callbacks
   por combo, então isso convive com o `game_walk`) e, se o tile de destino existe mas não é
   andável, faz o `/tp`.

Limites: no máximo 1 tentativa a cada 300 ms (1 por passo) e só para tiles que existem em
`g_map.getTile` — não teleporta para fora do mapa carregado. O toggle é desligado a cada
`onGameEnd` e só funciona se o `state` disser `is_gm`.

#### Teste

Rodado em 2026-09-04 contra `127.0.0.1:7171` com uma cópia temporária de
`client-otc/tests/autotest_rc.lua` em `client-otc/shinobirc.lua` (o OTClient executa
`<compactName>rc.lua` depois de carregar os módulos; o arquivo foi removido no fim).
Resultado: **0 erros no log**, screenshots em `screenshots/menu_*.png`
(`menu_01_personagem`, `menu_02_elemento`, `menu_03_elemento_raiton`, `menu_04_jutsus`,
`menu_05_jutsus_barra`, `menu_06_comandos`, `menu_07_state_falso`, `menu_08/09_noclip`,
`menu_10_select_real`). Verificado: `state` real chegando do servidor (9 personagens, 5
elementos, 8 jutsus ativos), `select` real trocando `genin_laranja` → `genin_uchiha`, injeção
de um `state` falso pelo rc (`modules.naruto_menu.onState(json.decode(...))`), botão do
mainpanel e Ctrl+J registrados, barra de ação preenchida com 8 jutsus, e o noclip atravessando
uma árvore (1050,1057,7 → 1050,1056,7).

### Assets (sprites)
- Coloque `Tibia.spr` e `Tibia.dat` versão **10.98** em `client-otc/data/things/1098/`.
- Para desenvolvimento, use um par 10.98 legítimo que você possua; para distribuir, só sprites próprios (ADR-002).
- Desative o auto-install em `init.lua` (`clientAssets.enabled = false`) para não baixar assets 13.x.
- Sprites próprios: ObjectBuilder 0.5.5 (cria/edita .spr/.dat; abre em Windows/macOS via AIR).

## 3. Servidor
```bash
cd server
git clone --branch v1.4.2 --depth 1 https://github.com/otland/forgottenserver tfs
cd tfs && mkdir build && cd build
cmake -DCMAKE_TOOLCHAIN_FILE=$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake .. && cmake --build . -j8
cp ../config.lua.dist ../config.lua
```
> Dependências via Homebrew: `boost cryptopp fmt pugixml luajit mariadb-connector-c`.
> Configure: `cmake -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="/opt/homebrew;/opt/homebrew/opt/mariadb-connector-c;/opt/homebrew/opt/luajit" -DUSE_LUAJIT=ON ..`

### Patches aplicados no fonte do TFS (2026-09-03)
O TFS 1.4.2 é de 2022 e não compila/roda sem ajustes com as versões atuais de Boost, fmt,
CMake e Apple Clang no Apple Silicon. Cada patch abaixo é o mínimo necessário.

| # | Arquivo(s) | Problema | Correção |
|---|-----------|----------|----------|
| 1 | `src/connection.h`, `src/server.h`, `src/signals.h`, `src/connection.cpp`, `src/server.cpp` | Boost ≥1.87 removeu `boost::asio::io_service` e `io_service.post()` (Homebrew tem 1.92) | `io_context` + `boost::asio::post(...)` |
| 2 | `src/connection.cpp` | `deadline_timer::expires_from_now` removido | `steady_timer::expires_after` |
| 3 | Rede | `to_uint` / `make_address_v4` mudaram de assinatura | atualizado para a API nova |
| 4 | `src/otpch.h` | fmt ≥10 não formata mais enums sem escopo implicitamente. `iomapserialize.cpp`, `iomarket.cpp` passam `AccessList_t`, `MarketAction_t`, `MarketOfferState_t` direto para `fmt::format("{:d}", ...)` → `type_is_unformattable_for` | `formatter` genérico para `std::is_enum_v<E>` que delega ao `underlying_type_t`, adicionado no fim do PCH. Envolvido em `#ifndef FS_ENUM_FORMATTER_PATCH` porque `otpch.h` não tem include guard e é ao mesmo tempo force-included como PCH e `#include`ado em cada `.cpp` (sem o guard: "redefinition of formatter") |
| 5 | `src/scheduler.cpp`, `src/server.cpp` | `timer.expires_from_now(...)` em `basic_waitable_timer` | `timer.expires_after(...)` |
| 6 | `src/signals.cpp` | `Signals::Signals(boost::asio::io_service&)` sobrou do patch 1 (o `.h` já era `io_context`) | `boost::asio::io_context&` |
| 7 | `CMakeLists.txt` (bloco `FORCE_LUAJIT`) | **Em arm64 o binário morria instantaneamente com SIGKILL (exit 137) e zero saída.** O TFS passa `-pagezero_size 10000 -image_base 100000000` no APPLE para o LuaJIT x86_64 alocar nos 2 GB baixos; o linker já avisava `Linking with PIE, -image_base will be ignored` e o kernel do macOS mata o executável resultante | flags aplicadas só quando `CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64"`. Em Apple Silicon o LuaJIT usa GC64 e não precisa do hack |

Patch no gerador (não no TFS): `tools/export_tfs.py` agora lê `server/tfs/data/items/items.xml`
(ignorando o bloco `NARUTO:BEGIN/END`) e **pula** os ids que já existem no items.xml vanilla,
eliminando os 35 avisos `[Warning - Items::parseItemNode] Duplicate item with id`. Os ids pulados
são listados no fim da execução do gerador — são placeholders de `data/tfs_mapping.json` que
devem ser trocados por ids livres quando houver sprite próprio.

Banco (o MariaDB do Homebrew autentica o seu usuário do macOS, não `root`):
```bash
brew services start mariadb
mysql -u "$USER" -e "CREATE DATABASE forgottenserver; CREATE USER 'tfs'@'localhost' IDENTIFIED BY 'tfs'; GRANT ALL ON forgottenserver.* TO 'tfs'@'localhost';"
mysql -u tfs -ptfs forgottenserver < schema.sql
```
Em `config.lua`: `mysqlUser = "tfs"`, `mysqlPass = "tfs"`, `mysqlDatabase = "forgottenserver"`.

Também em `config.lua` (não versionado — ao reprovisionar a partir do `.dist`, reaplicar):
`experienceStages = nil` e `rateExp = 1`. Motivo: `docs/sistemas/balanceamento.md` e
`progressao-jogador.md` foram calibrados com a XP crua do monstro; o `.dist` traz stages 7×–3×
que ficam ativas mesmo com `stages.xml` desligado (fallback Lua em `configmanager.cpp`), o que
encurtava a curva de ~1000h para uma fração (achado do simulador `tools/balance/sim.py`,
ver `docs/sistemas/balanceamento-relatorio.md`).

### Instalar o conteúdo gerado
```bash
python3 tools/export_tfs.py
cp -R server/generated/monster/naruto server/tfs/data/monster/
cp -R server/generated/spells/scripts/naruto server/tfs/data/spells/scripts/
cp -R server/generated/npc/naruto server/tfs/data/npc/
cp -R server/generated/scripts/naruto server/tfs/data/scripts/
cp server/generated/lib/naruto_quests.lua server/tfs/data/lib/
cp server/generated/lib/naruto_json.lua server/tfs/data/lib/          # JSON puro em Lua (opcode 210)
cp server/generated/lib/naruto_characters.lua server/tfs/data/lib/    # personagens + sets de elemento
cp server/generated/XML/vocations.xml server/tfs/data/XML/vocations.xml
```
E manualmente: colar `monsters_naruto.xml` em `monsters.xml`, `spells_naruto.xml` em `spells.xml`,
`items_naruto.xml` em `items.xml`, e `dofile('data/lib/naruto_quests.lua')` em `data/lib/lib.lua`.
Ou simplesmente: `tools/install_generated.sh` (faz tudo isso, idempotente, blocos marcados `NARUTO:BEGIN/END`).

## 4. Conectar
No cliente: Enter Game → servidor `127.0.0.1`, porta `7171`, versão `1098`. Conta padrão do schema: `god` / `god`.

## 5. Como rodar

O TFS **precisa** ser executado com o cwd em `server/tfs` (procura `config.lua`, `data/` e
`key.pem` relativos ao diretório atual). Use o script:

```bash
tools/run_server.sh            # sobe o servidor (Ctrl+C para parar)
tools/run_server.sh --build    # recompila antes de subir
```

Equivalente manual:
```bash
brew services start mariadb                 # o banco precisa estar no ar
cd server/tfs && ./build/tfs
```

Recompilar apenas:
```bash
cd server/tfs/build && cmake --build . -j8
```

Reinstalar o conteúdo Naruto gerado (sempre que `data/*.json` mudar):
```bash
tools/install_generated.sh                  # roda export_tfs.py + instala em server/tfs/data
```

Parar o servidor:
```bash
pkill -f 'build/tfs'
```

Verificar que está aceitando conexão:
```bash
nc -z 127.0.0.1 7171 && echo ok
```

### Log de inicialização esperado
```
>> Loading config
>> Loading RSA key
>> Establishing database connection... MySQL 3.4.10
>> Loading vocations
>> Loading items
>> Loading script systems / Using LuaJIT 2.1
>> Loading lua libs / lua scripts / monsters / lua monsters / outfits
>> Checking world type... PVP
>> Loading map        (Map size: 2048x2048)
>> Initializing gamestate
>> Loaded all modules, server starting up...
>> Shinobi Legends Server Online!
```
Nenhum aviso de item duplicado, de XML mal formado ou de erro Lua nos arquivos Naruto.
Ainda aparecem ~400 avisos `[Warning - Spell::configureSpell] Wrong vocation name: Knight/Druid/...`:
são as **spells vanilla** do TFS referenciando as vocações originais, que o nosso
`vocations.xml` gerado substituiu. Inofensivo; some quando as spells vanilla forem removidas.

### Contas de teste (criadas em 2026-09-03)
| Conta | Senha | Personagem | Level | Vocação | Town | group_id | Posição |
|-------|-------|-----------|-------|---------|------|----------|---------|
| `teste` | `teste` | `Naruto` | 8 | 1 (Vila da Folha) | 1 (Trekolt) | 1 (player) | 95, 117, 7 |
| `god` | `god` | `GM` | 8 | 1 (Vila da Folha) | 1 (Trekolt) | 6 (god) | 95, 117, 7 |

Senhas em SHA1 (TFS 1.4 usa sha1 fixo, sem opção `passwordType`). A posição é o templo do
town 1 do `forgotten.otbm` que vem com o TFS — a tabela `towns` é preenchida pelo servidor a
partir do mapa; confira com `mysql -u tfs -ptfs forgottenserver -e "SELECT * FROM towns;"`.

Recriar/resetar as contas:
```bash
mysql -u tfs -ptfs forgottenserver <<'SQL'
INSERT INTO accounts (name, password, type, email, creation)
VALUES ('teste', SHA1('teste'), 1, '', UNIX_TIMESTAMP())
ON DUPLICATE KEY UPDATE password = SHA1('teste'), type = 1;
INSERT INTO accounts (name, password, type, email, creation)
VALUES ('god', SHA1('god'), 5, '', UNIX_TIMESTAMP())
ON DUPLICATE KEY UPDATE password = SHA1('god'), type = 5;
INSERT INTO players (name, group_id, account_id, level, vocation, experience,
                     health, healthmax, mana, manamax, cap, town_id, posx, posy, posz, looktype, sex)
VALUES ('Naruto', 1, (SELECT id FROM accounts WHERE name='teste'),
        8, 1, 4200, 255, 255, 70, 70, 4400, 1, 95, 117, 7, 128, 1)
ON DUPLICATE KEY UPDATE level=8, vocation=1, town_id=1, posx=95, posy=117, posz=7;
INSERT INTO players (name, group_id, account_id, level, vocation, experience,
                     health, healthmax, mana, manamax, cap, town_id, posx, posy, posz, looktype, sex)
VALUES ('GM', 6, (SELECT id FROM accounts WHERE name='god'),
        8, 1, 4200, 255, 255, 70, 70, 4400, 1, 95, 117, 7, 128, 1)
ON DUPLICATE KEY UPDATE group_id=6, town_id=1, posx=95, posy=117, posz=7;
SQL
```
> `experience = 4200` é o total exato do level 8 pela fórmula do TFS
> (`(50*n^3 - 150*n^2 + 400*n)/3`, com `n = level-1`). Level e experiência precisam bater,
> senão o servidor recalcula o level no primeiro login.

## 6. Mapa
Remere's Map Editor (RME) para criar `data/world/forgotten.otbm`. `server/generated/world/*-spawn.xml`
tem as posições relativas do protótipo como referência.

## Comandos de GM próprios (data/scripts/naruto/gm_tools.lua)
`/sl` lista. `/god` = level 100, skills no teto prático (fist/shield 100, sword 90, club/axe/dist ~70 por causa dos multiplicadores das vocações), Ninjutsu ~30, os 8 jutsus atuais (personagem + elemento), 1.000.000 ryo no banco, mochila com todos os itens e melhor equipamento vestido. `/arena`, `/tp x,y,z`, `/lvl N`, `/jutsus` (os 8 atuais: 4 do personagem + 4 do elemento), `/full`, `/vila folha|nevoa|nuvem|areia`, `/personagem <id|nome>` (troca de personagem; GM ignora a vila), `/elemento <katon|suiton|raiton|doton|fuuton>` (troca o set elemental), `/pvm` (liga/desliga ser atacado por monstros — ver seção "GM: /pvm" abaixo). Para jogadores normais: `!personagem` (lista os da própria vila) / `!personagem <nome>` (troca) e `!elemento` (lista) / `!elemento <katon|suiton|raiton|doton|fuuton>` (troca). Tudo isso também está no menu Shinobi do cliente, que fala com o servidor pelo opcode estendido 210 — protocolo em `docs/sistemas/combate-e-jutsus.md` → "Protocolo opcode 210". Vanilla: `/m nome`, `/i id`, `/goto`, `/c`, `/ghost`, `/reload`.

### GM: /pvm (por que os monstros não atacavam o GM)
O grupo `god` (id 6, `server/tfs/data/XML/groups.xml`) tem as flags `ignoredbymonsters="1"` e
`cannotbeattacked="1"`. `ignoredbymonsters` vira `PlayerFlag_IgnoredByMonsters`, que
`Monster::isOpponent` (`server/tfs/src/monster.cpp`) checa explicitamente para nunca considerar
o jogador como alvo — **por design do TFS, e não um bug do nosso conteúdo**: é assim que GMs
normais ficam "invisíveis" para monstros. `cannotbeattacked` bloqueia o dano em
`Player::isAttackable`/`Player::canBeAttacked` mesmo que algo tente acertá-lo. Ambas as flags
juntas explicam 100% do sintoma "os bonecos não me atacam de volta" quando testado com a conta
`god`. **A categoria agressivo/passivo já existe** (campo `behavior` em `data/monsters/*.json`,
ver `docs/sistemas/monstros-e-pvm.md`) — o problema nunca foi o monstro, foi a conta de teste.

`/pvm` alterna o GM entre o grupo `god` (id 6, normal) e um novo grupo `god vulneravel` (id 7,
mesmas flags do `god` **menos** `ignoredbymonsters` e `cannotbeattacked`) via
`player:setGroup(Group(7))`. O `accountType` da conta continua 6 (ACCOUNT_TYPE_GOD) então todos
os outros comandos de GM (`/arena`, `/god`, etc., que checam `getAccountType() >= ACCOUNT_TYPE_GOD`)
continuam funcionando normalmente com `/pvm` ligado; o grupo 7 mantém `access="1"` para isso.

**Armadilha:** o TFS só reavalia a lista de alvos de um monstro (`Monster::updateTargetList`) em
`onCreatureAppear`/`onCreatureMove` — ligar `/pvm` parado, sem andar, não faz o monstro que já
estava por perto notar a mudança até o próximo passo do jogador (ou dele). Ande um passo depois
de `/pvm` (ou re-invoque o monstro) para ver o ataque de imediato.

## Avisos esperados no boot
- `Unknown loot item "meat"` etc. (≈70): são monstros **vanilla** do TFS (que ainda povoam o mapa `forgotten.otbm`)
  procurando loot pelo nome de itens que nós sobrescrevemos (ex.: 2666 "meat" virou "onigiri"). Somem quando o mapa
  próprio substituir o vanilla. Não é erro do nosso conteúdo.
- `spells.xml` agora contém **só** os jutsus (o installer descarta as spells vanilla, que referenciavam vocações Knight/Druid).

## Teste ponta a ponta (2026-09-03, funcionando)
`tools/autotest_client.sh [conta] [senha]` — sobe o cliente com login automático, entra no jogo, anda, mira o monstro
mais próximo, lança `katon goukakyuu` e `kawarimi`, loga stats e salva screenshots em `screenshots/`.
Resultado de referência: 0 erros no cliente, `A rat loses 20 hitpoints due to your attack`, hp 255/255 chakra 70/70.
Armadilhas já resolvidas: (1) `EnterGame.setAccountName` espera valor criptografado — preencher o widget direto;
(2) todo item com FLAG_ANIMATION no OTB precisa de ≥2 fases no .dat, senão o pacote de mapa desalinha;
(3) `/a N` (andar) falha contra paredes — no templo padrão use `/m` ou saia andando.

## 6. Modo GM (explorar o jogo)
Conta `god`/`god`, personagem `GM`. **accounts.type precisa ser 6** (ACCOUNT_TYPE_GOD no TFS 1.4.2; 5 é Community Manager).
Comandos próprios (`server/tfs/data/scripts/naruto/gm_tools.lua`):

| Comando | Efeito |
|---|---|
| `/sl` | lista os comandos |
| `/arena` | teleporta para o tile livre mais próximo fora de zona de proteção (3x3 livre) |
| `/tp x,y,z` | teleporta para **qualquer tile existente**, inclusive bloqueado ou dentro de PZ (`player:teleportTo(pos, false)`; só recusa quando não há tile na posição) |
| `/lvl N` | vai para o level N (vida/chakra cheios) |
| `/jutsus` | aprende os **8 jutsus atuais** (4 do personagem + 4 do elemento) e reenvia o `state` |
| `/full` | vida e chakra cheios |
| `/vila folha\|nevoa\|nuvem\|areia` | troca de vila (vocação) |
| `/personagem <id\|nome>` | troca de personagem (GM troca de qualquer vila) |
| `/elemento katon\|suiton\|raiton\|doton\|fuuton` | troca o set de 4 jutsus elementais |
| `/pvm` | liga/desliga ser atacado por monstros (grupo God ↔ God Vulnerável, id 7) — ver "GM: /pvm" acima |
| `/npc Nome Exato` | invoca (`Game.createNpc`) o NPC do lado do GM — testa diálogo de NPCs sem posição física no mapa ainda |
| `/storage key [value]` | lê (sem `value`) ou grava um storage do próprio GM — depuração de quests/tarefas/diárias/rank |
| `/rank [rankId]` | mostra o rank atual (+ HP/chakra) ou força uma promoção de teste (bypassa `NarutoQuests.rankGroups`) |
| `/zonecheck zona` | mostra se o rank atual deixaria entrar na área nomeada (`NarutoRanks.canEnter`) |

Jogadores normais (não-GM) trocam de personagem DENTRO da própria vila com `!personagem`
(lista) / `!personagem <nome>` (troca) e de elemento com `!elemento` (lista) /
`!elemento <katon|suiton|raiton|doton|fuuton>` — cada troca reaprende os 8 jutsus (4 pessoais
+ 4 do elemento) e reenvia o `state` pelo opcode 210. Ver `docs/sistemas/vilas-e-clas.md` →
"Personagens e jutsus" e `docs/sistemas/combate-e-jutsus.md` → "Protocolo opcode 210".

### Comandos de progressão (`docs/sistemas/progressao-servidor.md`)

| Comando | Efeito |
|---|---|
| `!tarefas` | lista as tarefas ATIVAS do jogador (aceitas com um Mestre de Tarefas da região) com progresso |
| `!diaria` | mostra as 3 missões diárias de hoje (sorteadas por faixa de level, já auto-aceitas) com progresso |
| `!diaria entregar` | entrega todas as diárias do dia que já estiverem prontas |
| `!pos` | (já existia, vanilla) mostra a posição atual |

Tarefas: fale com o "Mestre de Tarefas" da região (`{tarefas}` lista o catálogo completo,
`{tarefa}` aceita a primeira elegível, `{entregar}` entrega a primeira pronta). Diárias: o NPC
"Quadro de Missões" da praça responde às mesmas palavras-chave (`{diaria}`/`{entregar}`) que
`!diaria`. Exame Chunin (e futuros exames por quiz): fale com o NPC do exame, `{missao}` aceita
a etapa, `{prova}` começa a prova por palavra-chave quando a etapa for do tipo quiz.

Padrão TFS que importa: `/m Nome` (invoca monstro; patch: procura tile livre em volta), `/i nome do item`, `/goto Jogador`,
`/c Jogador` (puxa), `/ghost`, `/reload talkactions|spells|monsters`, `/pos`. Nomes dos monstros: os do JSON ("Lobo",
"Sapo Gigante", "Ninja Renegado", "Chefe dos Bandidos", "Sapo Ancião"...). Jutsus: os selos são o id com espaço
(`katon goukakyuu`, `suiton mizudan`, `kawarimi`, `shousen`).

Teste automatizado do fluxo: `tools/autotest_client.sh` (servidor no ar) — loga como GM, `/arena`, `/lvl 20`, invoca
Lobo e Sapo Gigante, ataca, solta jutsu, tira screenshots em `screenshots/`.

## 7. Criar conta pelo site (AAC)

Em vez de inserir conta/personagem na mão via `mysql`, use o AAC local
(`tools/aac/`): um site em Python puro (`http.server` + `pymysql`, sem
framework) que cria conta e personagem direto no mesmo banco do TFS.

```bash
tools/aac.sh                    # sobe em background em http://127.0.0.1:8080/
tools/aac.sh status             # confere se está no ar
tools/aac.sh stop                # derruba
```

Precisa de `pymysql` no `.venv` do projeto (`.venv/bin/pip install pymysql`,
já instalado neste checkout) — as credenciais do banco são lidas de
`server/tfs/config.lua`, nunca hardcoded.

Páginas: `/` (instruções), `/criar-conta` (nome/senha/confirmação/e-mail
opcional), `/criar-personagem` (escolhe vila → personagem inicial daquela
vila, com preview do outfit → nome do personagem + sexo + login da conta),
`/conta` (login → lista os personagens). Detalhes de cada coluna gravada em
`players`/`accounts`, das validações e das pendências conhecidas (só a Vila da
Folha tem templo de verdade no mapa atual — as outras 3 vilas nascem lá até
terem mapa próprio) estão em `tools/aac/README.md`.

Depois de criar a conta e o personagem no site, entre no cliente com
servidor `127.0.0.1`, porta `7171`, protocolo `1098`, usando a conta e a
senha criadas — o personagem nasce no templo da vila, level 1, com o outfit
escolhido, e o **Menu Shinobi abre sozinho** na aba Personagem (primeira
entrada em jogo, `first_time`).

Testado em 2026-09-04: conta + personagem criados via `curl -X POST`,
conferidos no banco (`level=1`, `vocation`/`town_id`/`looktype` corretos,
senha em SHA1) e logados de verdade com `tools/autotest_client.sh <conta>
<senha>` — o personagem nasceu no templo da Vila da Folha com o outfit do
"Genin Laranja" e o Menu Shinobi abriu sozinho (screenshots
`screenshots/aac_01_spawn_templo.png` e `screenshots/aac_02_hud.png`). Conta
de teste apagada do banco ao final.


## Notas de QA (2026-09-05, playtest L1–20)

- **Kit inicial**: o AAC/TFS criam o jogador só com o kit vanilla; o kit da vila
  (`data/villages.json.starting_items`) é entregue no **primeiro login** por
  `character_switch.lua` (gerado), junto com o piso de 60 de chakra.
- **Loja (`{trade}`)**: o `ShopModule` vanilla usa `buy=-1`/`sell=-1` como sentinela e o
  `getField<uint32_t>` do TFS 1.4.2 loga `Argument -1 has out-of-range value` a cada abertura de
  loja. Patch em `server/tfs/src/npc.cpp` (`luaOpenShopWindow`/`luaNpcOpenShopWindow`): lê como
  `int32_t` e trunca em 0. Exige recompilar o servidor (`cmake --build --preset macos-release`).
  Além disso o exportador limita o que cada mercador compra de volta ao teto de level da região
  (`SHOP_LEVEL_CAP` em `tools/export_tfs.py`) e nunca compra troféus.
- **macOS**: matar o OTClient com `kill -9` repetidamente faz o próximo lançamento parar num
  diálogo nativo "reabrir janelas?". Contorno aplicado na máquina de dev:
  `defaults write com.otclient ApplePersistenceIgnoreState -bool YES` (ajuste o bundle id se o
  app usar outro; o valor global `-g` também funciona).

- **Morte desconecta**: após "You are dead." o cliente fica ~30 s parado e cai por timeout; ao
  relogar o personagem está no templo com HP/chakra cheios. É o comportamento do TFS clássico.
  Scripts de QA precisam tratar a queda e relogar. Use `g_game.safeLogout()` ao encerrar sessões
  automatizadas — `kill -9` deixa a sessão "fantasma" no servidor até o timeout de rede.
- **Regeneração**: no TFS a regeneração de HP/mana só roda com comida. No Shinobi Legends o
  `character_switch.lua` (gerado) adiciona no login uma condição permanente (subId 9020) com os
  valores da vocação, então HP e chakra voltam sozinhos; comida soma por cima.
- **`g_game.autoWalk` em scripts de QA**: só acha caminho dentro do minimapa já conhecido pelo cliente; num cliente novo ele retorna NoWay para qualquer alvo fora da tela. Nos rcs de teste ande tile a tile com `g_game.walk(North|South|East|West)` (ver `client-otc/tests/walk_trails_rc.lua`).
