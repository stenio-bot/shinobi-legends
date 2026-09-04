# 03 — Decisões técnicas (ADR)

Formato: contexto → decisão → consequências. Adicione novas no final.

---
## ADR-001 — Engine: Godot 4 em vez de OTServ (TFS + OTClient)
**Contexto.** Narutibia/NTO reais são forks do Open Tibia Server (TFS em C++, spells
em Lua, monstros em XML, cliente OTClient com sprites .spr/.dat). É o caminho mais
"fiel", mas: exige C++ e build chato, formato de sprites arcaico, comunidade em
declínio e assets originais da Tibia têm problema legal.

**Decisão.** Godot 4 + GDScript, conteúdo em JSON, começar single-player.

**Consequências.**
- (+) Curva de aprendizado baixa, tooling moderno, exporta para PC/web/mobile.
- (+) Dono de 100% do código e do formato de dados.
- (−) Multiplayer precisa ser construído (Marco 4), não vem pronto como no TFS.
- (−) Sem o "feeling" exato de Tibia de graça; precisa reproduzir grid, etc.

Se no futuro quiser migrar para TFS, os dados em JSON são fáceis de converter
para os XML/Lua do OTServ.

---
## ADR-002 — Propriedade intelectual
**Contexto.** "Naruto" é marca da Shueisha/TV Tokyo. Fan games gratuitos costumam
ser tolerados, mas monetização gera risco de takedown.

**Decisão.** Universo **inspirado**, não licenciado. Nomes de vilas, personagens e
jutsus são próprios (ex.: "Vila da Folha" pode virar "Vila Kaede"). Elementos
(Katon, Suiton...) são termos japoneses genéricos e podem ficar. Nada de sprites
copiados de NTO ou do anime.

**Consequências.** Liberdade de monetizar depois; precisa criar arte própria.

---
## ADR-003 — Dados em JSON com JSON Schema
**Decisão.** Um schema por tipo em `data/schemas/`, validado por `tools/validate_data.py`.
**Consequências.** Erros de digitação pegos antes de rodar o jogo; possível gerar
editor de conteúdo depois.

---
## ADR-004 — Movimento em grid 32px, 4 direções
**Decisão.** Reproduzir Tibia. Sem física, sem diagonais livres.
**Consequências.** Combate previsível, fácil de sincronizar em rede depois.

---
## ADR-005 — Pivô: OTClient Redemption + servidor Open Tibia (substitui ADR-001)
**Data.** 2026-09-03.

**Contexto.** O usuário trouxe o código-fonte do **OTClient Redemption** (fork mehah/opentibiabr
do OTClient original, C++20 + Lua, MIT) e quer usá-lo como base: o objetivo é um jogo com a cara
e a sensação exata de Narutibia/NTO, que são jogos Open Tibia. O protótipo Godot (Marcos 1–3)
provou o loop de jogo e o balanceamento inicial, mas reimplementar o feeling de Tibia do zero
(walk, stackpos, containers, protocolo) custaria meses.

**Decisão.**
- **Cliente:** `client-otc/` (OTClient Redemption, cópia do zip fornecido). Customização via
  módulos Lua/OTUI, sem tocar no C++ enquanto possível.
- **Servidor:** **The Forgotten Server 1.4.2** (protocolo 10.98), em `server/tfs/`. É o servidor
  mais estável, com scripting Lua e formatos que a comunidade NTO domina. Canary (13+/protobuf)
  fica como opção futura; o OTClient suporta os dois.
- **Assets:** sprites em `.spr/.dat` (versão 1098), editados com **ObjectBuilder**. Fonte em
  `assets-src/`. Nenhum sprite da Tibia ou de NTO é redistribuído (ver ADR-002).
- **Conteúdo continua em `data/*.json`** como fonte da verdade. `tools/export_tfs.py` gera
  `monsters/*.xml`, `spells/scripts/*.lua`, `npc/*.xml|lua` e trechos de `items.xml` para o TFS.
  Assim o balanceamento feito no protótipo não se perde e o JSON segue validado.
- **Godot:** `client-godot/` fica como protótipo de referência (regras, IA, números). Não recebe
  mais features.

**Mapeamento de conceitos (JSON → Tibia/TFS).**
| Nosso conceito | Tibia/TFS |
|---|---|
| Chakra | Mana |
| Jutsu | Spell (instant, `spells.xml` + script Lua) |
| Skill Taijutsu | Fist fighting (`SKILL_FIST`) |
| Skill Shuriken | Distance fighting |
| Skill Ninjutsu | Magic level |
| Skill Genjutsu | Club (renomeada no cliente) |
| Skill Defesa | Shielding |
| Vila | Vocation (Folha/Névoa/Nuvem = vocation ids 1–3) + town |
| Elemento | Combat type (fire/ice/energy/earth) + resistências no monster XML |
| Ryo | Gold coin (item 2148) renomeado |
| Rank (Genin…) | Título via level, storage value |

**Consequências.**
- (+) Cliente completo e mantido, com hotkeys, containers, battle list, chat, minimapa, shaders,
  efeitos anexados (auras/asas → ótimo para chakra e modos), Android e web.
- (+) Multiplayer real desde o dia 1; TFS já é autoritativo.
- (−) Toolchain pesada: CMake + vcpkg + Ninja; primeira compilação de 30–60 min. TFS precisa de
  MySQL/MariaDB.
- (−) Sprites em .spr/.dat exigem ObjectBuilder; pipeline de arte mais chato que PNG solto.
- (−) Renomear Mana→Chakra, skills e vocações é feito no cliente (Lua/locales) e no servidor
  (vocations.xml); é cosmético, o protocolo continua falando "mana".
