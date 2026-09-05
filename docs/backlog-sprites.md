# Backlog de sprites — priorizado

Lista de TODA a arte que o jogo precisa hoje, priorizada para um pixel artist decidir por
onde começar. Prioridade: **P0** bloqueia a experiência (jogador vê algo quebrado, errado
ou legalmente arriscado), **P1** importante (some do jogo mas o placeholder "engana" por
enquanto), **P2** polimento (o jogo funciona sem, mas fica melhor com).

**Status possíveis:** `placeholder` (sprite genérico do Tibia vanilla, sem relação
temática — ex. looktype 21 recolorido para o Lobo), `importado lateral` (sprite extraído
de material de terceiros em `assets-src/import/` — planilhas genéricas de "monsters_sheet"
ou o pacote MUGEN de personagens do Naruto), `procedural` (gerado por código/ferramenta
própria, ex. efeitos de partícula simples ou tiles via `tools/spr`), `ok` (arte própria,
comissionada ou desenhada para este jogo, pronta para produção).

## ⚠️ Achado que muda a prioridade de tudo: looktypes 900–926 (MUGEN) violam a ADR-002

`assets-src/sprites/mugen_looktypes.json` mapeia os looktypes 900–926 para uma pasta
**`assets-src/import/mugen`** (privada, fora do git) contendo sprites extraídos de um
jogo de luta MUGEN com personagens **do anime Naruto de verdade** (pastas literalmente
chamadas `Naruto/`, `Sasuke/Sasuke Rinnegan`, `Kakashi`, `Itachi`, `Pain`, `Obito`,
`Madara`...). Isso é **exatamente** o que a ADR-002 (`docs/03-decisoes-tecnicas.md`)
proíbe: *"Nada de sprites copiados de NTO ou do anime"*. Hoje esses looktypes são usados
em produção para: os 3 NPCs mentores (Mestre Hayato=Kakashi/906, Capitã Rin=Sakura/917,
Instrutora Ibuki=Sakura The Last/918, Capitã Anbu Suzu=Minato Edo/908) e 5 bosses de arco
(Serpente Branca=916, Desertor de Elite=915, e os 4 bosses finais do Covil=910/911/912/913).
**Isso é risco legal real, não só dívida técnica** — está marcado **P0** abaixo, acima até
dos monstros comuns, porque é o único item desta lista que pode gerar takedown.

## Monstros genéricos (38 — todos já implementados em `data/monsters/*.json`)

| Monstro | Região | Quadros necessários | Prioridade | Status atual | Fonte sugerida | Horas (pixel artist) |
|---|---|---|---|---|---|---|
| Lobo (`wolf`) | Floresta da Vila | 4 direções × 3 fases de andar × 1 tamanho = 12 | P1 | placeholder (looktype 21 genérico) | encomenda | 6 |
| Cervo (`forest_deer`) | Floresta da Vila | 12 (mesmo padrão) | P2 | placeholder (looktype 21 recolorido) | encomenda | 5 |
| Cobra da Floresta (`forest_snake`) | Floresta da Vila | 12 | P1 | importado lateral (looktype 56 "serpent", partilhado com `lesser_serpent`/`magma_serpent`) | encomenda (hoje 3 monstros parecem idênticos) | 6 |
| Bandido (`bandit`) | Floresta da Vila | 12 | P1 | importado lateral (looktype 129, partilhado com `bandit_archer`/`ruin_puppet`) | encomenda | 7 |
| Bandido Arqueiro (`bandit_archer`) | Floresta da Vila | 12 | P1 | importado lateral (looktype 129, idêntico ao Bandido) | encomenda | 7 |
| Chefe dos Bandidos (`boss_bandit_chief`) | Floresta da Vila (boss) | 12 + pose especial | P0 | importado lateral (looktype 131 "ninja_chief", partilhado com o Marionetista) | encomenda | 10 |
| Mercenário da Ponte (`mercenary_bridge`) | Costa das Marés | 12 | P1 | importado lateral (looktype 129, idêntico ao Bandido) | encomenda | 7 |
| Batedor da Névoa (`mist_scout`) | Costa das Marés | 12 | P1 | importado lateral (looktype 128 "ninja_blue", partilhado com `rogue_ninja`) | encomenda | 7 |
| Guardião da Neblina (`mist_guardian`) | Costa das Marés | 12 | P1 | importado lateral (looktype 131, idêntico ao Chefe dos Bandidos) | encomenda | 7 |
| Aprendiz Mascarado (`masked_apprentice`) | Costa das Marés (mini-boss) | 12 + pose especial | P0 | importado lateral (looktype 130 "ninja_pale", partilhado com `spectral_warrior`) | encomenda | 9 |
| Espadachim da Névoa (`boss_mist_swordsman`) | Costa das Marés (boss) | 12 + 2 fases de fúria | P0 | importado lateral (looktype 132 "ninja_white", único na sheet) | encomenda | 12 |
| Sanguessuga Gigante (`leech`) | Floresta da Morte | 12 | P1 | importado lateral (looktype 19, único) | encomenda | 6 |
| Sapo Gigante (`giant_toad`) | Floresta da Morte | 12 | P1 | importado lateral (looktype 60 "great_beast", partilhado com `boss_elder_toad`) | encomenda | 7 |
| Ninja Renegado (`rogue_ninja`) | Floresta da Morte | 12 | P1 | importado lateral (looktype 128, idêntico ao Batedor da Névoa) | encomenda | 7 |
| Serpente Menor (`lesser_serpent`) | Floresta da Morte | 12 | P1 | importado lateral (looktype 56, idêntico à Cobra da Floresta) | encomenda | 6 |
| Rival do Exame — Pedra/Som/Névoa (`exam_rival_*`) | Floresta da Morte | 12 × 3 = 36 | P2 | importado lateral (looktypes 128/129/130, reaproveitados) | encomenda (baixa urgência, aparecem só no exame) | 15 |
| Sapo Ancião (`boss_elder_toad`) | Floresta da Morte (boss) | 12 + pose especial | P0 | importado lateral (looktype 60, idêntico ao Sapo Gigante) | encomenda | 10 |
| Serpente Branca (`boss_white_serpent`) | Floresta da Morte (boss de arco) | 12 humano + 12 forma serpente 2×2 + 3 fases | P0 | **importado MUGEN (916, Sasuke Rinnegan)** — violação ADR-002 | encomenda urgente | 16 |
| Marionete de Combate (`ruin_puppet`) | Ruínas | 12 | P1 | importado lateral (looktype 129, idêntico ao Bandido) | encomenda | 7 |
| Sentinela de Pedra (`stone_sentinel`) | Ruínas | 12 | P1 | importado lateral (looktype 61 "stone_golem", único) | encomenda | 8 |
| Guerreiro Espectral (`spectral_warrior`) | Ruínas | 12 | P1 | importado lateral (looktype 130, idêntico ao Aprendiz Mascarado) | encomenda | 7 |
| Xamã da Maldição (`curse_shaman`) | Ruínas | 12 | P1 | importado lateral (looktype 138 "hooded_purple", partilhado com `boss_curse_partner`) | encomenda | 7 |
| Desertor de Elite (`elite_deserter`) | Ruínas (mini-boss) | 12 + pose especial | P0 | **importado MUGEN (915, Sasuke Akatsuki)** — violação ADR-002 | encomenda urgente | 12 |
| Marionetista das Ruínas (`boss_puppeteer`) | Ruínas (boss) | 12 + pose especial | P0 | importado lateral (looktype 131, idêntico ao Chefe dos Bandidos) | encomenda | 12 |
| Águia do Trovão (`thunder_eagle`) | Montanha do Trovão | 12 | P1 | placeholder (looktype 21 "placeholder de ave") | encomenda | 7 |
| Oni da Geleira (`glacier_oni`) | Montanha do Trovão | 12 | P1 | importado lateral (looktype 12 "oni_fox", partilhado com `boss_ancestral_oni`) | encomenda | 8 |
| Monge da Tempestade (`storm_monk`) | Montanha do Trovão | 12 | P1 | importado lateral (looktype 137 "elder_red", partilhado com 2 NPCs) | encomenda | 7 |
| Serpente de Magma (`magma_serpent`) | Montanha do Trovão | 12 | P1 | importado lateral (looktype 56, idêntico à Cobra da Floresta) | encomenda | 6 |
| O Sócio Eterno (`boss_curse_partner`) | Montanha do Trovão (boss) | 12 + 3 fases (75/50/25%) | P0 | importado lateral (looktype 138, idêntico ao Xamã) | encomenda | 14 |
| Oni Ancestral (`boss_ancestral_oni`) | Montanha do Trovão (boss final) | 12 + pose especial | P0 | **importado MUGEN (913, Madara)** — violação ADR-002 | encomenda urgente | 14 |
| Clone Branco (`white_clone`) | Covil da Nuvem Vermelha | 12 | P1 | importado lateral (looktype 130, idêntico ao Aprendiz Mascarado) | encomenda | 8 |
| Ninja Elite da Aurora (`elite_cloud_guard`) | Covil da Nuvem Vermelha | 12 | P1 | importado lateral (looktype 129, idêntico ao Bandido) | encomenda | 8 |
| O Vigia Ilusório (`boss_illusive_eye`) | Covil (boss 1/4) | 12 + pose especial | P0 | **importado MUGEN (910, Itachi)** — violação ADR-002 | encomenda urgente | 14 |
| O Mascarado das Sombras (`boss_masked_puppeteer`) | Covil (boss 2/4) | 12 + pose especial | P0 | **importado MUGEN (912, Obito)** — violação ADR-002 | encomenda urgente | 14 |
| O Portador dos Seis Caminhos (`boss_rings_bearer`) | Covil (boss 3/4) | 12 + pose especial | P0 | **importado MUGEN (911, Pain)** — violação ADR-002 | encomenda urgente | 14 |
| O Ancestral da Nuvem Vermelha (`boss_crimson_ancestor`) | Covil (boss final do jogo) | 12 + 2 fases | P0 | **importado MUGEN (913, Madara — reaproveitado do Oni Ancestral)** — violação ADR-002 | encomenda urgente, prioridade máxima (é o clímax do jogo) | 18 |

*Nota geral:* hoje **10 pares de monstros diferentes compartilham exatamente o mesmo
sprite** (ex. Bandido = Bandido Arqueiro = Mercenário da Ponte = Marionete de Combate =
Ninja Elite da Aurora, todos looktype 129). Isso é o motivo prático mais visível de
"o jogo parece incompleto" para quem joga — priorize desduplicar os monstros comuns de
menor level antes dos bosses raros, pois o jogador vê muito mais lobos que bosses.

## NPCs (21 já implementados em `data/npcs/*.json`)

| NPC | Papel | Quadros | Prioridade | Status atual | Fonte sugerida | Horas |
|---|---|---|---|---|---|---|
| Ichiro, o Mercador (`merchant_leaf`) | loja | 12 | P1 | importado lateral (128, igual ao Batedor da Névoa) | encomenda | 6 |
| Mestre Hayato (`scroll_master_leaf`) | loja de pergaminhos | 12 | P0 | **importado MUGEN (906, Kakashi)** — violação ADR-002 | encomenda urgente | 8 |
| Capitã Rin (`quest_giver_leaf`) | missões | 12 | P0 | **importado MUGEN (917, Sakura)** — violação ADR-002 | encomenda urgente | 8 |
| Velha Sumi (`merchant_swamp`) | loja | 12 | P1 | não mapeado em `imports.json` — provavelmente placeholder genérico | encomenda | 6 |
| Rastreador Goro (`quest_giver_swamp`) | missões | 12 | P1 | não mapeado — placeholder genérico | encomenda | 6 |
| Instrutora Ibuki (`exam_proctor_forest`) | proctora do Exame Chunin | 12 | P0 | **importado MUGEN (918, Sakura The Last)** — violação ADR-002 | encomenda urgente | 8 |
| Mestre de Tarefas Jiro (`task_master_leaf`) | quadro de tarefas | 12 | P1 | novo (2026-09-04), sem sprite ainda | encomenda | 6 |
| Mestre de Tarefas Ren (`task_master_swamp`) | quadro de tarefas | 12 | P1 | novo, sem sprite | encomenda | 6 |
| Quadro de Missões (`dailies_board_leaf`) | diárias (objeto/NPC?) | 1–12 (confirmar se é NPC ou item de cenário) | P2 | novo, sem sprite | encomenda ou aproveitar tile de cenário | 3 |
| Mercador Itsuki (`merchant_coastal`) | loja | 12 | P1 | placeholder genérico | encomenda | 6 |
| Ancião Tazu (`quest_giver_coastal`) | missões | 12 | P1 | importado lateral (137 "elder_red") | encomenda | 6 |
| Mestre de Tarefas Umi (`task_master_coastal`) | quadro de tarefas | 12 | P1 | novo, sem sprite | encomenda | 6 |
| Tsubaki, a Escavadora (`merchant_ruins`) | loja | 12 | P1 | placeholder genérico | encomenda | 6 |
| Ancião Kaito (`quest_giver_ruins`) | missões | 12 | P1 | placeholder genérico | encomenda | 6 |
| Mestre de Tarefas Dokan (`task_master_ruins`) | quadro de tarefas | 12 | P1 | novo, sem sprite | encomenda | 6 |
| Ferreiro Genzo (`merchant_mountain`) | loja | 12 | P1 | placeholder genérico | encomenda | 6 |
| Mestra Yuki (`quest_giver_mountain`) | missões | 12 | P1 | placeholder genérico | encomenda | 6 |
| Mestre de Tarefas Kaji (`task_master_mountain`) | quadro de tarefas | 12 | P1 | novo, sem sprite | encomenda | 6 |
| Fornecedor Enji (`merchant_akatsuki_lair`) | loja | 12 | P2 | placeholder genérico (139) | encomenda | 6 |
| Capitã Anbu Suzu (`quest_giver_akatsuki_lair`) | missões (Exames Anbu/Kage) | 12 | P0 | **importado MUGEN (908, Minato Edo)** — violação ADR-002 | encomenda urgente | 8 |
| Mestre de Tarefas Kuro (`task_master_lair`) | quadro de tarefas | 12 | P2 | novo, sem sprite | encomenda | 6 |

## Personagens jogáveis (9, `data/characters.json` — 4 direções reais)

Diferente de monstros/NPCs (que no Tibia normalmente giram só de forma cosmética),
personagens jogáveis **precisam** de 4 direções reais + 3 fases de andar cada, porque o
jogador vê o próprio boneco a maior parte da sessão.

| Personagem | Vila | Quadros (4 dir × 3 fases × equip. base) | Prioridade | Status atual | Fonte sugerida | Horas |
|---|---|---|---|---|---|---|
| Genin Laranja (`genin_laranja`) | Folha/leaf | 12 base + variações de equip. | P0 | importado lateral (128, compartilhado com vários NPCs/monstros — outfit "padrão" do jogo hoje) | encomenda urgente (é o personagem mais visto do jogo) | 14 |
| Genin Uchiha (`genin_uchiha`) | Folha/leaf | 12 | P0 | provável placeholder/import | encomenda urgente | 14 |
| Kunoichi Rosa (`kunoichi_rosa`) | Folha/leaf | 12 | P0 | provável placeholder/import | encomenda urgente | 14 |
| Herdeira Hyuga (`herdeira_hyuga`) | Névoa/mist | 12 | P0 | provável placeholder/import | encomenda urgente | 14 |
| Kunoichi das Armas (`kunoichi_armas`) | Névoa/mist | 12 | P0 | provável placeholder/import | encomenda urgente | 14 |
| Ninja Verde (`ninja_verde`) | Nuvem/cloud | 12 | P0 | provável placeholder/import | encomenda urgente | 14 |
| Ninja Abelha (`ninja_abelha`) | Nuvem/cloud | 12 | P0 | provável placeholder/import | encomenda urgente | 14 |
| Sábio Loiro (`sabio_loiro`) | Areia/sand | 12 | P0 | provável placeholder/import | encomenda urgente | 14 |
| Sábio Cerimonial (`sabio_cerimonial`) | Areia/sand | 12 | P0 | provável placeholder/import | encomenda urgente | 14 |

*Confirmar no início do trabalho:* `data/tfs_mapping.json` e `assets-src/sprites/mugen_looktypes.json`
não citam looktypes específicos para os 9 personagens — checar se algum reaproveita
looktype 900/901/902 (Naruto Kid/Sasuke Kid/Sakura Kid do MUGEN), o que seria a MESMA
violação de ADR-002 dos NPCs/bosses acima, só que pior (o personagem jogável aparece
o tempo todo).

## Jutsus — efeitos de área/projétil (54 em `data/jutsus/*.json`)

Agrupado por categoria (um efeito reaproveitável por tipo de forma, não por jutsu
individual — mas a lista de "quais jutsus usam qual" está em `data/jutsus/*.json`,
campo `element`/`shape`).

| Categoria | Elemento(s) | Qtde de jutsus que usam | Quadros por efeito | Prioridade | Status atual | Fonte sugerida | Horas totais |
|---|---|---|---|---|---|---|---|
| Projétil (bola/lança) | katon, suiton, doton, raiton, fuuton, none | ~18 | 1 fase × 9 direções (grade 3×3) | P1 | **`procedural` (concluído 2026-09-05)** — 8 misseis próprios (`tools/spr/gen_effects.py`), ids 60..67 | — | 0 |
| Área (explosão/círculo/cone) | katon, suiton, doton, raiton, fuuton | ~16 | 5–7 fases | P1 | **`procedural` (concluído 2026-09-05)** — efeitos próprios por papel (impacto/cone/anel/etc.), ids 200..226 | — | 0 |
| Beam/linha (`fuuton_tornado_cortante` e similares tier 3) | fuuton, raiton, katon, suiton, doton | 5 | 5–7 fases | P2 | **`procedural` (concluído 2026-09-05)** — `fx_fire_dragon`/`fx_water_dragon`/`fx_lightning_lance`/`fx_earth_collapse`/`fx_wind_tornado` | — | 0 |
| Self/buff (aura, cura, teleporte, fumaça) | todos (heal_over_time, paralyze, teleporte, kawarimi/bunshin) | ~16 | 5–6 fases | P2 | **`procedural` (concluído 2026-09-05)** — `fx_heal_green`, `fx_smoke_poof`, `fx_shadow_clone` (distinto do poof, ver nota), `fx_chakra_focus`, `fx_lightning_armor`, `fx_stone_shell` | — | 0 |
| Personagem (jutsus pessoais dos 9 personagens) | — | 20 (`data/jutsus/personal.json`) | reaproveita as categorias acima por alias (`fx_melee_hit`, `fx_chakra_blade`, `fx_seal_glow`...) | P2 | **`procedural` (concluído 2026-09-05)** — sem paleta própria por personagem ainda (ver limitações) | variação de cor por personagem, se o orçamento permitir | 8 |

*Atualização 2026-09-05:* os 54 jutsus agora têm efeito/missile PRÓPRIO (não mais os
genéricos rotativos de `gen_placeholders.py`), gerados por
`tools/spr/gen_effects.py` e catalogados em `assets-src/sprites/effects.json`
(27 efeitos, ids 200–226; 8 misseis, ids 60–67; mais 14 "slots vanilla"
`CONST_ME_*`/`CONST_ANI_*` redesenhados para os ataques elementais de MONSTRO,
que só aceitam nome fixo — ver `docs/sistemas/arte-e-sprites.md` §Efeitos e
`docs/sistemas/combate-e-jutsus.md` §Efeitos e misseis). Validado in-game com
screenshots em `screenshots/vfx_*.png` (todos os 5 elementos, projétil + beam,
kawarimi, bunshin, cura, lâmina de chakra, névoa venenosa). Limitações
honestas: `fx_wind_tornado` lê mais como uma linha ondulada que uma coluna
girando; jutsus "pessoais" sem elemento reaproveitam `fx_melee_hit`/
`fx_chakra_focus` genéricos (sem assinatura visual própria por personagem).

## Itens (173 em `data/items/*.json`, incluindo os 47 novos de equipamento + 38 troféus desta missão)

| Categoria | Qtde | Quadros por item | Prioridade | Status atual | Fonte sugerida | Horas totais |
|---|---|---|---|---|---|---|
| Armas melee (weapon_class=melee) | 15 | 1 (ícone) + 1 (sprite de chão) | P1 | placeholder (ícones genéricos do Tibia vanilla, campo `sprite` aponta para id não confirmado como existente) | pack livre de ícones + ajuste de paleta | 15 |
| Armas ranged (weapon_class=ranged) | 8 | 1 + 1 | P1 | placeholder | pack livre + ajuste | 8 |
| Armaduras (head/body/legs/feet) — 11 conjuntos completos (L1,10,20,30,40,50,60,70,80,90,100) | 44 | 1 ícone + variação visual no boneco (paperdoll) | P0 | placeholder — **sem variação visual no personagem, todo set "veste" igual visualmente hoje** | encomenda (é o que mais comunica progressão pro jogador) | 60 |
| Acessórios (anéis, colares, braceletes, bandanas) | ~20 | 1 ícone (a maioria não muda o visual do boneco) | P2 | placeholder | pack livre de ícones | 10 |
| Consumíveis (poções, pílulas, onigiri) | 8 | 1 ícone | P2 | placeholder | pack livre | 4 |
| Pergaminhos (scrolls) | 21 | 1 ícone (padrão, com selo colorido por elemento/tier) | P2 | placeholder | pack livre + variação de cor | 6 |
| Materiais de drop (peles, presas, núcleos, selos) | ~30 | 1 ícone | P2 | placeholder | pack livre | 8 |
| Troféus de tarefa (`trophy_*`, novos nesta missão) | 38 | 1 ícone (pode reaproveitar um template "medalha" + cor por raridade) | P2 | não existe — item 100% novo desta missão | gerar por código/template (1 base + tint por raridade) | 6 |

## Tiles das 6 regiões

| Região | Mapa | Status atual | Prioridade | Fonte sugerida | Horas |
|---|---|---|---|---|---|
| Floresta da Vila | `forest_valley` (zona 0,0,50,40) | ok — tiles próprios via `tools/spr`, mapa implementado | — | já feito | 0 |
| Floresta da Morte | `forest_valley` (zona 50,0,46,40) | ok — mesmo mapa físico, reskin de zona | — | já feito | 0 |
| Ruínas do Clã Marionetista | `forest_valley` (zona 96,0,52,40) | ok — implementado | — | já feito | 0 |
| Montanha do Trovão | `forest_valley` (zona 148,0,52,40) | ok — implementado | — | já feito | 0 |
| Costa das Marés | sem mapa físico ainda (pedido em `data/maps/spawns_lore.json`) | **inexistente** | P0 | encomenda + geração via `tools/map` (pedir ao agente de mapas) | 25 (tileset de praia/ponte/neblina) |
| Covil da Organização Nuvem Vermelha | sem mapa físico ainda (pedido em `data/maps/spawns_lore.json`) | **inexistente** | P0 | encomenda + geração via `tools/map` (tileset de masmorra/covil) | 30 (tileset de covil/pedra escura) |

## UI

| Elemento | Descrição | Prioridade | Status atual | Fonte sugerida | Horas |
|---|---|---|---|---|---|
| Ícones de rank (Genin/Chunin/Jonin/Anbu/Kage) | 5 ícones pequenos, exibidos no HUD/perfil ao subir de rank (`data/ranks.json`) | P1 | inexistente | encomenda (5 ícones simples) | 5 |
| Moldura/tema geral (`naruto_theme` module) | painéis, bordas, fontes já com `.otmod` próprio | P2 | parcialmente feito (`client-otc/modules/naruto_theme/` existe com lógica, mas usa estilos herdados do `game_*` vanilla) | ajuste incremental, não greenfield | 20 |
| Ícone de conquista (achievements, novo nesta missão) | 1 template + variação por categoria (kill/boss/quest/exam/exploration/collection/task/daily/level = 9 categorias) | P2 | inexistente | gerar por código (1 base + 9 variações de cor/ícone) | 8 |
| Ícone de tarefa (task board) | usado pelos 6 NPCs `task_master_*` no diálogo/UI | P1 | inexistente | encomenda ou reaproveitar ícone genérico de "quest" | 3 |
| Ícone de diária (dailies board) | usado por `dailies_board_leaf` (e futuros por região) | P2 | inexistente | encomenda ou reaproveitar ícone de "quest" com selo de calendário | 3 |
| Barra de XP com curva visível (nível 1–100) | opcional: indicador visual de que a barra "anda mais devagar" em levels altos, para não parecer bug | P2 | inexistente | ajuste de UI, não arte pixel | 4 |

## Resumo executivo para o pixel artist

1. **Comece pelos 5 P0 de personagem jogável + os 8 P0 de NPC/boss em looktype MUGEN
   (900–926)** — é simultaneamente o maior risco legal (ADR-002) e o que mais aparece
   na tela.
2. **Depois, os pares de monstros idênticos** (Bandido = Bandido Arqueiro = Mercenário
   da Ponte = Marionete de Combate = Ninja Elite da Aurora, todos looktype 129; e mais
   4 grupos parecidos) — maior ganho de percepção por hora de trabalho.
3. **Os 44 quadros de armadura com variação no boneco (paperdoll)** são o item de maior
   volume (60h) mas também o que mais comunica progressão de level pro jogador — sem
   isso, vestir o "Manto do Kage" parece igual a vestir o "Vest Genin" de level 1.
4. **Tiles das 2 regiões sem mapa físico** (Costa das Marés, Covil da Nuvem Vermelha)
   bloqueiam o agente de mapas, não só a experiência visual — sem tileset, essas duas
   regiões não podem virar mapa jogável de jeito nenhum.
5. Jutsus e a maioria dos ícones de item já têm um "bom o suficiente" procedural/placeholder
   — deixe por último.

**Total estimado:** ~38 monstros (≈340h) + 21 NPCs (≈135h) + 9 personagens (≈126h) +
jutsus agrupados (≈87h) + itens agrupados (≈117h) + tiles das 2 regiões novas (≈55h) +
UI (≈43h) ≈ **900 horas de pixel artist** para zerar o backlog inteiro — coerente com
"jogo de 1000 horas de conteúdo" ter também ~900 horas de arte por trás.
