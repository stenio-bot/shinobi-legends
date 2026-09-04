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
