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
- [x] 2 áreas: Floresta da Vila (1–10) e Floresta da Morte (10–25, ex-"Pântano Sombrio"), com 11 monstros
- [x] 1 boss por área com fases (invocações, multiplicador de ataque, falas)
- [x] Missões sequenciais de caça em 2 NPCs (aceitar, progresso no HUD, entregar, recompensa)
- [x] Linha de visão (árvores bloqueiam aggro e ataques à distância)
- [x] Peso e capacidade; drop de 30% dos itens da mochila ao morrer (ficam no seu corpo)
- [x] Áreas 25–50, 50–80, 80–100 no mapa (Ruínas, Montanha do Trovão, Covil da Nuvem Vermelha) — v2.1, 2026-09-05
- [x] Vila da Areia (Fuuton/Doton) e jutsus Doton/Fuuton
- [x] Áreas 25–50 (Ruínas do Clã) e 50–80 (Montanha do Trovão) no JSON
- [ ] Arte própria substituindo placeholders
- [ ] Som e música
- [x] Tiles próprios de cenário via tools/spr (items.otb writer): tatame, terra de vila, paredes, torii, placa, lanterna, cerca
- [ ] Mochila maior (+slots) como item, crafting básico

---
## Lore (2026-09-04) — bíblia do mundo e progressão de rank
Feedback do usuário: a lógica de visuais estava errada (bandido/mobs comuns
usando personagens principais como Sasuke) e não havia progressão de rank de
verdade. Resolvido:
- [x] Pesquisa de arcos/ranks reais → `docs/lore/pesquisa-naruto.md`
- [x] Bíblia do mundo: 6 regiões (4 já implementadas + 2 novas com dados
      prontos) alinhadas aos arcos → `docs/lore/mundo.md`
- [x] Progressão Genin→Chunin→Jonin→Anbu→Kage com exames de várias etapas →
      `docs/lore/progressao.md`, `data/ranks.json`, `data/schemas/rank.schema.json`
- [x] Reatribuição de visuais: monstros/bosses comuns não usam mais
      personagem principal (só sprites genéricos); 900–926 ficou reservado a
      NPCs mentores e aos bosses de arco de verdade (Serpente Branca + os 4
      do covil final) → `data/tfs_mapping.json`, tabela em
      `docs/sistemas/monstros-e-pvm.md`
- [ ] Pendências para o exportador/servidor (não editado nesta missão — fora
      de escopo): objetivo de quest `keyword_quiz` de verdade, storage
      centralizado de rank, bônus de status por rank — ver
      `docs/lore/progressao.md`, seção "Pendências técnicas"
- [ ] Pendências para o agente de mapa: `data/maps/spawns_lore.json` pede
      2 regiões novas (Costa das Marés, Covil da Nuvem Vermelha) e spawns
      extras em 2 zonas existentes (Floresta da Morte, Montanha do Trovão)

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
- [x] Mapa `.otbm` Vale da Folha gerado por tools/map (vila murada, floresta, ponte, Floresta da Morte, torre, acampamento), instalado como `mapName = "valley"` — editável no Remere's
- [x] Monstros, jutsus, NPCs e missões gerados e testados in-game (NPCs corrigidos: `data/npc/<Nome>.xml` + `npc/scripts/naruto/`)
- [ ] Sprites próprios em .spr/.dat (ObjectBuilder): personagem, 9 monstros, itens, efeitos de jutsu
- [x] Bosses com fases via script Lua (`onHealthChange` → `boss_phases.lua`): falas, invocações,
      transformação por `looktype` e fase de fúria (cura + velocidade). Testado in-game na
      **Serpente Branca** (Floresta da Morte, L25) — 3 fases, outfit 132 → 890, 3+2 invocações

## OT-3 — Multiplayer de verdade
- [x] Contas + site de registro (AAC em `tools/aac`, porta 8080, sobe com `play.sh`) — hospedagem pendente
- [ ] Party com XP compartilhada, clãs (guilds do TFS), chat
- [ ] Balanceamento com jogadores reais

---
# (Antigo) Marco 4 — Multiplayer no Godot — DESCARTADO pelo ADR-005
- [ ] Servidor autoritativo (ver `docs/02-arquitetura.md`)
- [ ] Login, personagens por conta
- [ ] Sincronização de posição e combate
- [ ] Chat
- [ ] Party/clã, XP compartilhada

## Fila autônoma (2026-09-05) — "o melhor Narutibia do mundo"
Estado: checkpoint `fff60df`. Sistemas de rank/exame/tarefas/diárias/achievements no servidor; mapa v2.1
com 6 regiões; walk-cycle validado por filtro geométrico; 173 itens, 54 jutsus, 38 monstros, 21+8 NPCs.

**Checkpoint da tarde: `88ea822`** (servidor reinstalado com fúria real + balanceamento r6/r7 +
fix de encoding). Desde o checkpoint acima: história dos 6 arcos com ganchos de saída e Nuvem
Vermelha plantada (auditoria + Lotes A/B/C/M), motor de missões v2, humanoides procedurais v2 (4
direções reais), fix do andar travando (`FLAG_ALWAYSONTOP`), 2 playtests de história completos —
ver "Feito" abaixo.

Feito (com hash), ordem aproximada de quando fechou:
- [x] Decor v2: cadeira, estátua de santuário, lanterna de pedra, decor de praia; autoborder grama↔areia e areia↔água (`215721f`)
- [x] Cliente UX: aba "Missões" no Menu Shinobi via opcode 210 `get_progress`; rank na janela de atributos; mensagens de sistema em pt-BR + fix cp1252 (`e0e683f`)
- [x] Balanceamento rodada 1: simulador `tools/balance/sim.py`; stages de XP desligadas (eram 5–7×), skill mult 1.1, mana mult 1.3 (`eada82c`)
- [x] Balanceamento rodada 2: bug do seletor no simulador, N de grupo por monstro, tier 1 ×0.35, paridade elemental/pessoal (`d1d96f8`)
- [x] Balanceamento rodada 3: manamultiplier 1.1, tier 2/3 recalibrados, ninjutsu puro competitivo em L50–100 (`b9cd0ad`)
- [x] Mapa v3: 8 NPCs posicionados, gates de rank 45001–45005, identidade visual de Ruínas/Montanha/Covil, bordas dirt_sand e snow_rock (`b8b8ded`)
- [x] Playtest L1–20 rodada 1 (`docs/qa/playtest-l1-20.md`): achou 2 P0 (sem kit inicial; loja com erro Lua) — corrigidos em `1e4f280`
- [x] Playtest rodada 2 (`docs/qa/playtest-l1-20-r2.md`): achou kit pela metade (firstitems.lua vanilla) e saudação só em inglês — corrigidos em `92166a7`; sem dados de combate (disco cheio interrompeu)
- [x] Conquistas: 55 implementadas no servidor + seção na aba Missões (`e02aa0b`), 12 testes headless em luajit; validação in-game confirmada na rc `c2d716f`
- [x] Regeneração natural de HP/chakra (condição permanente por vocação no login) e spawns da Trilha dos Lobos reduzidos para 1–2 lobos por ponto (`77def75`, `c62e75e`)
- [x] Documento mãe do jogo `docs/00-biblia-do-jogo.md` (`2a0a261`)
- [x] VFX de jutsus: `tools/spr/gen_effects.py`, 27 effects (ids 200–226) + 8 missiles (60–67) + 14 slots vanilla redesenhados, mapeados no exportador (`1e4f280`/`c21a304`)
- [x] Criaturas procedurais: lobo/cervo/águia/serpente/sapo/sanguessuga (940–945) com máscara de cor e 4 direções reais + variantes de paleta para 12 humanoides (946–957), fix de cores dessaturadas em `tibia_colors` (`79881e0`); rc de validação pós-integração (`c2d716f`)
- [x] Som procedural: 51 SFX sintetizados (`tools/audio/gen_sfx.py` → ogg via `soundfile`), módulo `naruto_sounds` (opcode 210 `sfx` nos jutsus, level up, dano, morte de monstro, menu), opção "Sons do jogo" (`ef195b4`); falta música ambiente e sons de monstro (`docs/backlog-audio.md`)
- [x] Playtest rodada 3 (`docs/qa/playtest-l1-20-r3.md`): combate real no L1 (2 kills, XP/h medido); achou chakra sem regen natural e 4 lobos por spawn — ambos corrigidos nas entradas de regen/spawn acima
- [x] Balanceamento rodada 4 (`7dee1ac`): cenário de hunt 30 min com regen/pílulas no simulador, híbrido com cadências independentes, tier 1 com cooldown 3,5 s e escala por level, tier 2 recalibrado, wakizashi temperado (L15) fecha o platô de armas; custo de chakra do tier 1 ajustado para ×1,3 (não ×2) e hit L1 preservado
- [x] Playtest rodada 4 (`docs/qa/playtest-l1-20-r4.md`): interrompido por queda externa do servidor antes de qualquer combate; achou conquista de zona destravando dentro da muralha da vila — corrigido (`bea6efc`)
- [x] Balanceamento rodada 5 (`1a46739`): economia de chakra estrutural (pool 100+10L, regen por level reaplicada no advance, custo do tier 1 como % do pool via `manapercent`), tier 1 com cooldown 9 s e escala maior; ninjutsu puro 6/6 bosses na meta; entra no próximo reinício do servidor
- [x] Auditoria narrativa dos 6 arcos, na ordem da história: notas por arco, top 10 lacunas, plano em lotes (`5873bd3`)
- [x] Motor de missões v2: `collect_item` com drops condicionais, `talk_to` universal, `reach` (poll 7 s), `kill` any_of/boss, pré-requisitos cruzados com `locked_text`, textos condicionados, recompensas storage/outfit/addon/title, progresso na aba Missões; 63 testes headless (`184de6f`, `docs/sistemas/missoes.md`)
- [x] Lote B (Ruínas): chegada, clã virado marionetes, rastros, confronto; Marionetista revela a Nuvem Vermelha a 15% HP, gancho de saída pra Montanha; Serpente Branca com fala velada (`6f0893f`)
- [x] Lote C (Montanha + Covil): Montanha ensina a resposta antes do quiz, ganchos de saída, Sócio Eterno invoca serpentes de magma; Covil com quiz de fechamento, Portador invoca Caminhos Invocados, Ancestral invoca Eco Carmesim e revela a Grande Guerra; falas de encerramento e promoção a Kage (`006f3c3`)
- [x] Lote A (Floresta da Vila + Costa): tutorial, missão do cervo, batedores antecipam o Espadachim, semente da Nuvem Vermelha no Chefe dos Bandidos, Espadachim fala do Aprendiz, Goro/Ibuki referenciam a mesma prova, ganchos de saída via `done_text` (`1439749`)
- [x] Lote M: Kaito/Tsubaki/Yuki/Genzo posicionados no mapa, gate da Costa das Marés rebaixado de Chunin pra Genin (ordem da história), spawns de Aprendiz Mascarado/Serpente Menor/Cervo, validador cruzado missão↔spawn↔mapa `tools/map/validate_world.py` (`0dc49a5`)
- [x] Humanoides procedurais v2: boneco Tibia desenhado do zero (`humanoid_art.py`) com 4 direções reais, 3 fases de andar e adereço por classe pros 12 looktypes 946–957, sem material importado (`2ac02b3`)
- [x] Playtest de história arcos 1–3 (`docs/qa/playtest-historia-arcos1-3.md`): jogável de ponta a ponta; achou mojibake em falas de NPC/monstro
- [x] Balanceamento rodada 6 (`5fe6056`): híbrido ≤+15% em 6/6 bosses, kits pessoais ±12%, grupo 3+ parcial, summons do endgame ajustados; Lua gerado em cp1252 (fim do mojibake nas falas)
- [x] Fix do andar travando/nome sumindo (`bc20778`): bordas geradas (128 itens, topOrder 1) sem `FLAG_ALWAYSONTOP` no `items.otb` — stackpos divergente cliente↔servidor; flag derivada do topOrder, validador `dump_dat` confere ordem OTB↔DAT
- [x] Playtest de história arcos 4–6 (`docs/qa/playtest-historia-arcos4-6.md`, `4690797`): bosses/summons novos confirmados; achou regressão de encoding (kill com nome acentuado não conta pra missão) e mojibake residual em nomes de NPC/item
- [x] Balanceamento rodada 7 (`87c19a1`): fúria de boss com dano real via `onHealthChange` do jogador (19 testes headless); tier 1 reescalado pra 12–14% do pool (7–8 casts por pool cheio, recupera em ~73 s); relatório v7
- [x] Fix da regressão de encoding (`8147d69`): `NarutoText.utf8ToCp1252`/`.cp1252ToUtf8` normaliza nomes antes de comparar em missões/tarefas/diárias/conquistas/fases de boss; 52 testes headless
- [x] Cliente: `InputMessage::getString` converte UTF-8→cp1252 por sequência (`049981b`) — fim do mojibake em nomes de NPC, criatura e item na tela
- [x] Servidor instalado com fúria real + r7 + fix de encoding (`88ea822`)

Em andamento:
- [ ] Re-teste de história arcos 4–6 numa sessão nova, do zero, confirmando o fix de encoding em combate sustentado (o playtest de hoje rodou antes do fix estar 100% validado ao vivo)
- [ ] Playtest de combate rodada 6: medir XP/h contra `docs/sistemas/progressao-jogador.md` com dados completos, agora com tier 1 a 12–14% do pool

Próximos (ordem de valor):
- [ ] Balanceamento rodada 8: recalibrar `attack_multiplier` de boss pós-fúria-real (TTK subiu acima do calibrado nas rodadas 5/6); buscar a alavanca que fecha o tempo-sem-chakra em hunt híbrida (0% medido contra meta 15-25%, relatório v7 §5)
- [ ] Música ambiente (`tools/audio/gen_music.py`, ainda não escrita — candidata a ferramenta separada de `gen_sfx.py`) e sons de monstro (`docs/backlog-audio.md`)
- [ ] Polimento mapa v3: bordas neve↔rocha e gelo↔rocha ainda retas em vários trechos; textura de pedra rachada das Ruínas um pouco "ocupada"; antecâmaras do Covil com 1 tile
- [ ] Vista de costas real para o personagem padrão (128) — hoje sintetizada; precisa de arte
- [ ] Templos/vilas 2–4 no mapa (hoje só a Folha existe fisicamente)
- [x] Substituir os 9 looktypes MUGEN de personagem jogável (900–909, exceto 906) por outfits procedurais coloríveis (`tools/spr/gen_players.py`, `player_art.py`) — commit pendente nesta sessão
- [ ] Substituir os 18 looktypes MUGEN restantes (906, 910–926 — NPCs/bosses de endgame) — risco legal de ADR-002, P0 de arte
- [ ] Party com XP compartilhada, clãs, PvP em arena

## Marco 5 — Pós-lançamento
- [ ] PvP em áreas específicas
- [ ] Guerras de clã
- [ ] Mercado
- [ ] Eventos

- [x] Balanceamento r9 (`79d9b3d`) e r10 (`5029269`): híbrido como referência; escada de armas L5–40
- [x] Mapa: trilhas de 2 tiles, sem bolsões, lobos 30 s (`f4e46a4`); templo com porta aberta (`384f657`)
- [x] AAC polido com escolha de vila/personagem (`c9f4776`)
- [x] AAC: retratos renderizados do nosso `.spr` (`tools/spr/render_outfit.py` + `tools/aac/portraits/*.png` versionados; `aac.py` não lê mais `assets-src/import/`) — e agora os 9 looktypes de personagem também são arte própria (ver linha acima), sem nenhuma pendência de terceiro nesse fluxo
- [ ] Balanceamento r11: teto estrutural do taijutsu puro em L5/10/15/20/35; L41–77; `boss_puppeteer` 59 s
