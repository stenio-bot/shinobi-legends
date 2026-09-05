# Referência: OTClient Redemption — módulos, UI e onde customizar

Resumo do levantamento feito em 2026-09-03 sobre `client-otc/` (mehah/otclient "Redemption",
base edubart rev 2.760, C++20 + Lua/OTUI + renderer HTML/CSS, MIT).

## Carregamento
- `init.lua` define app, search paths (`data/`, `modules/`, `mods/`), carrega `config.otml`, descobre módulos e
  carrega por faixas de prioridade: libs (≤99: corelib, gamelib, modulelib, startup) → `client` e `client_*` (≤499)
  → `game_interface` e `game_*` (≤999) → `client_mods` e mods (≤9999) → `otclientrc.lua`.
- `game_interface/interface.otmod` tem o `load-later` com ~55 módulos `game_*`. **Desativar módulo = comentar ali.**
- Cada módulo: pasta com `.otmod` (OTML: name, sandboxed, autoload, autoload-priority, scripts, dependencies,
  load-later, @onLoad/@onUnload). Módulos sandboxed expõem funções via `modules.<nome>.<fn>`.
- Padrão moderno: `Controller:new()` (modulelib) com `setUI/loadHtml`, `registerEvents`, `registerExtendedOpcode`,
  `scheduleEvent`, `bindKeyDown`; limpa tudo sozinho no terminate.

## Tela de jogo (game_interface)
- `gameinterface.otui`: `gameMapPanel` (UIGameMap) no centro; painéis laterais `gameLeftPanel`, `gameLeftExtraPanel`,
  `gameMainRightPanel` (minimapa), `gameRightPanel`, `gameRightExtraPanel` (UIMiniWindowContainer, 176px);
  `gameBottomPanel` (chat); barras de ação esquerda/direita/inferior; `statsbar`.
- Mouse: `widgets/uigamemap.lua` → `processMouseAction` (3 esquemas: regular, classic, smart left click).
  Menu de contexto: `createThingMenu`; **extensão oficial: `modules.game_interface.addMenuHook(cat, nome, cb, cond)`**.
- Teclado: `corelib/keybind.lua` (`Keybind.new/bind`), presets por vocação (Druid/Knight/Paladin/Sorcerer/Monk →
  trocar por vilas). Movimento em `game_walk/walk.lua`.
- Hotkeys: dois sistemas: `game_actionbar` (Tibia 12+, 9 barras, ~6k linhas) e `game_hotkeys` (clássico, Ctrl+K).
  Para jutsus, o clássico + barra própria pode ser mais barato.

## UI
- OTUI = OTML com herança (`Meu < UIButton`), âncoras, layouts (verticalBox/horizontalBox/grid), estados
  (`$hover`, `$!on`), campos Lua (`&campo`), handlers (`@onClick`), aliases globais (`&cor: #fff` → `$cor`).
- Estilos globais em `data/styles/NN-*.otui` (ordem numérica). `30-miniwindow.otui` é a base das janelinhas laterais.
  Tema próprio: criar `data/styles/50-ninja.otui` com paleta em aliases; trocar spritesheets em `data/images/ui/`,
  `topbuttons/`, `icons/`, `healthmana/`, `inventory/`.
- Lua: `g_ui.createWidget('Estilo', parent)`, `g_ui.loadUI`, `g_ui.displayUI`, `g_ui.importStyle`.
- **HTML/CSS** (`Controller:loadHtml`, `UIHTML`): bindings `*value`, `*if`, `*visible`, `{{ }}`, handlers `on*`.
  Exemplos: `game_questlog`, `game_forge`, `game_htmlsample`. CSS global em `data/styles/custom.css`.
- `dev_otui` (Ctrl+Alt+U): editor visual de OTUI dentro do cliente. Manter em dev, tirar em release.
- `data/setup.otml`: sprite-size 32, viewport 8x6, fontes. Primeiro arquivo a mexer se os sprites mudarem.

## Tradução
- Tudo passa por `tr()`. Dicionários em `data/locales/*.lua` (`locale = {name, translation = {["en"]="pt"}}`).
- `modules.client_locales.installLocale({name='pt', translation={...}})` **mescla** no idioma existente → é assim
  que `modules/naruto_theme` renomeia Mana→Chakra, skills e spells sem tocar nos módulos originais.
- `pt.lua` original é cp1252/Latin-1; o projeto deve migrar para UTF-8.

## O que fica / o que sai (aplicado em `interface.otmod` e `mods.otmod`)
- **Fica:** core, client_*, game_interface, walk, console, inventory, containers, healthinfo, healthcircle,
  creatureinformation, minimap, battle, textmessage, textwindow, hotkeys, actionbar, skills, outfit, playerdeath,
  modaldialog, npctrade, cooldown, spelllist, questlog, quickloot, analyser, **cyclopedia** (bestiário = PvM;
  analyser depende dele), shaders, attachedeffects, viplist, notifications, lootsplitter, playertrade.
- **Sai:** prey, imbuing(+tracker), playermount, market, unjustifiedpoints, paperdolls, stash, shop, highscore,
  blessing, store, rewardwall, forge, tutorial, taskboard, wheel, proficiency, ruleviolation, **mods/game_bot**.
- Referências diretas em `gameinterface.lua` a módulos desativados foram protegidas com `modules.x and`.

## Identidade visual "jutsu" (sem C++)
- `game_attachedeffects`: auras/asas/partículas registradas no cliente por id (`AttachedEffectManager.register`);
  o servidor manda só o número. Requer feature `GameWingsAurasEffectsShader` + patch no TFS (ver README do OTC,
  "TFS 1.4.2 Compatible Aura Effect Wings Shader").
- `game_shaders`: shaders de outfit (rainbow, ghost...) e de mapa (fog, rain...). Ideal para modo chakra/elemento.
- `game_healthcircle`: círculo de vida/chakra em volta do personagem.

## Comunicação com servidor custom
- `Controller:registerExtendedOpcode(op, fn)` / `sendExtendedOpcode(op, json)` — padrão de `game_shop` e locales.
  Caminho mais barato para rank ninja, clãs, missões, elementos, sem tocar no protocolo C++.

## Módulos próprios do Shinobi Legends (`modules/naruto_*`)

Convenção: módulo próprio, `sandboxed: true`, nunca editar os `game_*` originais além do
mínimo. Cada um expõe suas funções globais do sandbox como `modules.<nome>.<fn>`.

| Módulo | Prioridade | O que faz |
|---|---|---|
| `naruto_theme` | 600 | traduções (Mana→Chakra, skills, vilas) via `installLocale`; registra o perfil de spelllist `Shinobi` e monta a barra de ação (`naruto_jutsus.lua`); dados gerados em `jutsus_data.lua` |
| `naruto_menu` | 1100 | janela **Shinobi** (Personagem / Elemento / Jutsus / Comandos) + noclip de GM; conversa com o servidor pelo **opcode estendido 210** |

### Faixas de `autoload-priority` (init.lua)

`autoLoadModules(99)` (libs) → `autoLoadModules(499)` + `client` → `autoLoadModules(999)` +
`game_interface` → `autoLoadModules(9999)` + `client_mods` → `<compactName>rc.lua`.
**Para carregar DEPOIS do `game_interface` (e portanto depois do `game_mainpanel`,
`game_actionbar` etc., que são `load-later` dele) a prioridade precisa estar em 1000–9999.**
É por isso que o `naruto_menu` usa 1100 e o `naruto_theme`, que só mexe em locale, usa 600.

### API usada pelo `naruto_menu` (bons exemplos para módulos futuros)

- `Controller:new()` + `menuController:init()/terminate()` no `.otmod`; o Controller limpa
  sozinho eventos, keybinds, scheduleEvents e opcodes no terminate.
- `controller:registerExtendedOpcode(210, fn)` / `controller:sendExtendedOpcode(210, json)`;
  o callback recebe `(protocol, code, buffer)`. `json.encode`/`json.decode` do corelib.
- `modules.game_mainpanel.addToggleButton(id, tooltip, image, callback, front, index)` para o
  botão no painel direito; `Keybind.new(cat, action, 'Ctrl+J', '')` + `Keybind.bind(...)` para
  o atalho (e `Keybind.delete` no terminate).
- `UICreature` (`setOutfit`, `setCreatureSize`, `setCenter`, `getCreature():setDirection`) para
  preview de personagem — mesmo widget do `game_outfit`.
- `UITabBar`: `setContentWidget(painel)` **antes** de `addTab(texto, painel)`; `getTab(texto)` e
  `selectTab(tab)`. `removeTab` destrói o `tabPanel` junto.

### Armadilhas de OTUI já encontradas

- **Lista rolável:** a `ScrollablePanel` é a *janela* (ancorada em cima e embaixo, altura fixa,
  `vertical-scrollbar: <id do irmão>`), e quem cresce é um `Panel` DENTRO dela com
  `layout: verticalBox` + `fit-children: true` — é o padrão do `MiniWindowContents`
  (`30-miniwindow.otui`). Pôr `fit-children` na própria `ScrollablePanel` ancorada
  top+bottom faz layout e âncoras brigarem para sempre: **o cliente trava antes de abrir a
  janela, sem nada no log**.
- Só **filhos diretos** com `id` viram campo Lua do pai (`UIWidget::setId` →
  `parent->setLuaField`). Neto precisa de `recursiveGetChildById` (ou guardar o atalho).
- Aliases `&cor` do OTML são **por documento**; por isso a paleta de `50-ninja.otui` é copiada
  dentro do `naruto_menu.otui`.
- Um `.otui` só instancia os nós SEM `<`; `Estilo < Base` é definição. O nó raiz instanciado
  (`MainWindow`) é o que o `g_ui.displayUI('naruto_menu')` devolve.
- Texto vindo do servidor é UTF-8; as fontes são bitmaps indexados por byte. Converter para
  cp1252 antes de exibir (`utf8ToCp1252` no `naruto_menu.lua`).
