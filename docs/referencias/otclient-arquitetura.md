# Referência: OTClient Redemption — arquitetura C++ (resumo)

Levantamento de 2026-09-03 sobre `client-otc/src`. Fork **mehah/otclient "Redemption"** (snapshot opentibiabr),
base edubart rev 2.760, C++20/23, MIT. Não é edubart puro nem OTCv8 (mas portou features do V8).

## Framework (`src/framework`)
- **core**: `graphicalapplication` (g_app), `eventdispatcher` (g_dispatcher / g_mainDispatcher / g_textDispatcher,
  filas por thread), `modulemanager` (g_modules, `.otmod`, hot-reload), `resourcemanager` (g_resources sobre PhysFS,
  criptografia de assets, auto-update), `garbagecollection` (GC próprio para Lua/texturas/thingtypes), `otml/`.
- **graphics**: OpenGL 2/ES (macOS usa GLEW estático). **DrawPool**: 5 pools (MAP, CREATURE_INFORMATION, LIGHT,
  FOREGROUND_MAP, FOREGROUND) com hash do frame → só redesenha o que mudou. Texture atlas. Shaders GLSL com uniforms
  padronizados (item/outfit/mount/map). Partículas. APNG. Fontes bitmap e TTF.
- **ui**: `uimanager` (g_ui, estilos OTUI, `createWidget/loadUI`), `uiwidget` (1.1k linhas), layouts (anchor, box,
  grid, **flexbox**), **html/** (parser HTML+CSS próprio → widgets).
- **luaengine**: LuaJIT, `luabinder` gera bindings por template. API completa em `client-otc/meta.lua`.
- **net**: asio, XTEA, checksum, sequenced packets, compressão zlib, HTTP login JSON (11+), WebSocket (WASM),
  proxy multi-servidor, gravação/replay de pacotes.
- **platform**: win32, x11, **cocoa (macOS)**, android, browser. **sound**: OpenAL + ogg.

## Cliente (`src/client`)
- Modelo: `Thing` → `Item | Creature | Effect | Missile`; `Tile`; ambos são `AttachableObject` (aceitam attached
  effects, partículas e **widgets ancorados**). `Map` em blocos, `findPathAsync`. `LocalPlayer`, `Container`.
- `game.h/.cpp` (g_game): estado, `enableFeature`, todas as ações. Features 1–99 = compat por versão; **100+ =
  extensões do fork** (ItemShader, CreatureShader, CreatureAttachedEffect, WingsAurasEffectsShader, CreaturePaperdoll,
  NegativeOffset, AllowCustomBotScripts, AllowPreWalk, MapCache...). Liga em `modules/game_features/features.lua`.
- **Protocolo**: `protocolcodes.h` (opcode 50 = extended opcode; **51–99 = customizados do fork**: attached effect 52/53,
  creature shader 54, map shader 55, typing 56, paperdoll 60/61...). `protocolgameparse.cpp` (7.6k linhas) chama
  `onOpcode` no Lua **antes** do switch → dá pra interceptar qualquer pacote sem C++. Extended opcodes:
  `onExtendedOpcode(opcode, buffer)` no Lua; patch de servidor em `client-otc/tools/tfs_extendedopcode.patch`
  (TFS 1.x já tem `onExtendedOpcode` nativo).
- Versões suportadas: 740 → 1525 (`modules/gamelib/game.lua`). **TFS 1.4.2 = 10.98 funciona direto.**
- **Assets**: 3 caminhos: `.spr/.dat` clássico (`thingtypemanager::loadDat`, `spritemanager` com carga assíncrona,
  sprites HD, `.cwm`), appearances protobuf 12+/13+ (`catalog-content.json`), ou híbrido (`GameLoadSprInsteadProtobuf`).
  Offsets negativos (`GameNegativeOffset`) = compatível com ObjectBuilder 0.5.5 para sprites maiores que 32px.
- **Render do mapa**: `mapview` (floor fading, câmera adaptativa à latência, shaders com crossfade, highlight),
  `lightview` (luz por textura), `satellitemap` (minimapa estilo Cyclopedia).
- **Attached effects** (`attachedeffect*`): efeito por creature/tile/item, categoria Effect/Creature/**textura externa
  PNG/APNG**, offsets por direção, bounce/pulse/fade, shader, luz, `canDrawOnUI`. Registrados no Lua por id; servidor
  manda só o id. **É a ferramenta para auras de chakra, selos e modos.**

## Build
- `CMakePresets.json`: `macos-release` (Ninja, arm64-osx, Apple Clang, IPO OFF obrigatório, static libs).
- Deps via vcpkg manifest (`vcpkg.json`): asio, luajit, physfs, openal, libpng[apng], protobuf, openssl, glew...
- macOS: `cmake --preset macos-release && cmake --build --preset macos-release --target otclient`; gera `OTClient.app`
  (bundle, deployment target 11.0). Assinar ad-hoc: `xattr -cr OTClient.app && codesign --force --deep --sign - OTClient.app`.
- Também: Windows, Linux, Android (APK), Web (Emscripten/WebGL2). iOS não.

## Notável
DrawPool com hash, multi-thread real, GC próprio, HTML/CSS/flexbox para UI, aliases OTML, attached effects,
paperdoll, satellite map, som Tibia 13, proxy + replay de pacotes, criptografia de assets (insegura), Discord RPC,
modo editor (`FRAMEWORK_EDITOR`), `AGENTS.md` com regras para agentes de IA.
