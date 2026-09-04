# 01 — Roadmap

Cada marco termina com algo **jogável e testável**. Não pule marcos.

## Marco 0 — Fundação ✅ (esta pasta)
- [x] Estrutura de pastas, README, CLAUDE.md
- [x] GDD resumido e documentos de sistema
- [x] Schemas JSON e conteúdo inicial (jutsus, itens, monstros)
- [x] Script de validação de dados

## Marco 1 — "Andar e bater" ✅
Objetivo: um ninja anda num mapa e mata um monstro.
- [x] Projeto Godot aberto, mapa 48x36 em grid 32px (placeholder desenhado em código)
- [x] Player com movimento em grid (4 direções, estilo Tibia)
- [x] Autoload `GameData` carregando `data/*.json`
- [x] Monstro com IA (idle/wander → persegue → ataca; covarde foge; arqueiro à distância)
- [x] Ataque básico corpo a corpo, HP, morte, respawn (player e monstros)
- [x] HUD: barra de HP e Chakra, alvo, log de combate, dano flutuante
- [x] Teste de fumaça automatizado (`client/tests/smoke_test.tscn`)
- [ ] Polimento: line-of-sight para arqueiro, corpo no chão, som

## Marco 2 — "Ficar forte" ✅
Objetivo: o loop de progressão fecha.
- [x] XP e level, perda de 10% de XP ao morrer
- [x] 5 skills que sobem com uso (bônus de vila aplicado)
- [x] Jutsus: hotbar (1-0), chakra, cooldown, projétil/alvo/área/linha/cone/self, elementos, status (burn, poison, slow, stun, paralyze, heal)
- [x] Inventário (20 slots, stacks) + equipamento (9 slots) com bônus de itens
- [x] Loot no corpo do monstro (tabela do JSON), ryo
- [x] NPC vendedor (compra e venda), NPC de missão placeholder
- [x] Save/load local (F5/F9, autosave ao fechar)
- [x] Boss da floresta spawnado (fases ainda não implementadas)
- [ ] Pendências: peso/capacidade, drop de itens ao morrer, fases de boss, line-of-sight

## Marco 3 — "Conteúdo" (em andamento)
- [x] Tela inicial de escolha de vila (3 vilas, jutsu e skill favorita diferentes)
- [x] Mapa definido em `data/maps/forest_valley.json` (96x40, spawns e zonas por level)
- [x] 2 áreas: Floresta da Vila (1–10) e Pântano Sombrio (10–25), com 9 monstros
- [x] 1 boss por área com fases (invocações, multiplicador de ataque, falas)
- [x] Missões sequenciais de caça em 2 NPCs (aceitar, progresso no HUD, entregar, recompensa)
- [x] Linha de visão (árvores bloqueiam aggro e ataques à distância)
- [x] Peso e capacidade; drop de 30% dos itens da mochila ao morrer (ficam no seu corpo)
- [ ] Áreas 25–50, 50–80, 80–100 (Ruínas, Montanha, Fortaleza)
- [x] Vila da Areia (Fuuton/Doton) e jutsus Doton/Fuuton
- [x] Áreas 25–50 (Ruínas do Clã) e 50–80 (Montanha do Trovão) no JSON
- [ ] Arte própria substituindo placeholders
- [ ] Som e música
- [ ] Mochila maior (+slots) como item, crafting básico

---
# Fase OT (a partir de 2026-09-03) — OTClient + TFS. Substitui os Marcos 4–5 abaixo.

## OT-0 — Fundação
- [x] OTClient Redemption em `client-otc/`, Godot congelado em `client-godot/`
- [x] ADR-005 documentando o pivô e o mapeamento de conceitos
- [x] `tools/export_tfs.py`: JSON → monstros XML, jutsus (spells) Lua, NPCs, itens, vocações, quests
- [x] Toolchain no Mac: CMake, Ninja, vcpkg instalados; OTClient compilando (preset macos-release)
- [x] TFS 1.4.2 em `server/tfs/` (7 patches Boost/CMake/arm64), compilado, MariaDB rodando, schema importado, contas de teste
- [x] Conteúdo Naruto instalado no TFS sem erros: 19 monstros, 24 jutsus, 77 itens (override dos vanilla), 9 NPCs, 15 missões, 4 vilas
- [x] Cliente conecta no servidor local com sprites placeholder próprios (login, mapa, MOTD, jutsu reconhecido) — 2026-09-03
- [x] Sprites placeholder próprios via tools/spr (mini ObjectBuilder em Python)
- [x] Teste ponta a ponta automatizado: tools/autotest_client.sh

## OT-1 — Cara de Naruto
- [x] Locale pt-BR: Mana→Chakra, Magic Level→Ninjutsu, skills renomeadas, "Spells"→"Jutsus"
- [x] Tela de login e fundo com identidade própria (`client_background`, `client_entergame`)
- [x] Módulos desnecessários desativados (market, store, prey, wheel, forge, imbuing, bot)
- [x] Vocações = vilas (Folha, Névoa, Nuvem, Areia) no `vocations.xml`
- [ ] Escolha de vila na criação de personagem (site/AAC ou NPC inicial)
- [ ] Efeitos anexados (auras) para modo chakra / rank

## OT-2 — Conteúdo no servidor
- [ ] Mapa `.otbm` do Vale (floresta + pântano) no Remere's Map Editor
- [ ] Monstros, jutsus, NPCs e missões gerados e testados in-game
- [ ] Sprites próprios em .spr/.dat (ObjectBuilder): personagem, 9 monstros, itens, efeitos de jutsu
- [ ] Bosses com fases via script Lua (onThink / onHealthChange)

## OT-3 — Multiplayer de verdade
- [ ] Contas, site de registro (ou AAC), hospedagem
- [ ] Party com XP compartilhada, clãs (guilds do TFS), chat
- [ ] Balanceamento com jogadores reais

---
# (Antigo) Marco 4 — Multiplayer no Godot — DESCARTADO pelo ADR-005
- [ ] Servidor autoritativo (ver `docs/02-arquitetura.md`)
- [ ] Login, personagens por conta
- [ ] Sincronização de posição e combate
- [ ] Chat
- [ ] Party/clã, XP compartilhada

## Marco 5 — Pós-lançamento
- [ ] PvP em áreas específicas
- [ ] Guerras de clã
- [ ] Mercado
- [ ] Eventos
