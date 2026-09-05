# Tabela de progressão do jogador — nível 1 a 100

Este documento traduz `data/progression.json` (fórmula `xp_total = 50*level² + 50*level`,
inalterada — ver nota no fim) e `docs/sistemas/balanceamento.md` em um guia prático,
bloco de 5 níveis por vez: onde caçar, quanto XP/h esperar, quantas horas o bloco leva,
que missões/tarefas fazer e que equipamento vestir. A curva é **Tibia-like de propósito**:
rápida no início (poucas horas por bloco), cada vez mais lenta perto do fim — a maior
parte das ~1000 horas totais está concentrada nos últimos 20 níveis, não distribuída
igualmente pelos 100.

**Como a curva foi calculada.** XP necessário por bloco vem direto da fórmula (fixa).
As horas por bloco não vêm de uma taxa de XP/h constante — vêm de uma curva de
eficiência de caça que **cai** conforme o nível sobe (monstros com mais HP, menos
alternativas de spot, bosses com cooldown de horas, exames que exigem preparo e não só
grind). O XP/h da tabela é o resultado (`xp_necessário ÷ horas`), não um valor
arbitrado à parte — por isso ele sobe do bloco 1 ao bloco 4 (o jogador ainda está
aprendendo a build) e depois cai o resto do jogo.

| Nível | Onde caçar | XP/h esperado | Horas do bloco | Horas acumuladas | Missões / tarefas | Equipamento a ter |
|---|---|---|---|---|---|---|
| 1–5 | Floresta da Vila: Lobo (`wolf`), Cervo (`forest_deer`, opcional/passivo) | ~536 | 2,8 h | 2,8 h | `q_wolves_1` · `q_forest_snakes` (nova) · `task_wolf_1` | Kit de genin: `bandana_leaf`, `vest_genin`, `pants_ninja`, `sandalias_ninja`, `kunai_iron`/`shuriken_iron`, `amuleto_academia` (droppa no Lobo/Bandido ou vem de `q_forest_snakes`) |
| 6–10 | Floresta da Vila: Bandido (`bandit`), Bandido Arqueiro (`bandit_archer`) | ~1290 | 3,1 h | 5,9 h | `q_bandits_1` · `q_bandit_archers` (nova) · `q_forest_supplies` (nova, entrega) · `task_bandit_1/2` | Trocar arma para `tanto_steel` (8); `gloves_taijutsu` (10) ao fechar o bloco |
| 11–15 | Floresta da Morte: Sanguessuga (`leech`), Sapo Gigante (`giant_toad`) · Costa das Marés: Mercenário da Ponte (`mercenary_bridge`) | ~1757 | 3,7 h | 9,6 h | `q_leeches` · `q_coastal_mercenaries` · `q_coastal_supplies` (nova) · `task_leech_1` | Set do Batedor completo (L10): `capuz_do_batedor`, `calca_do_batedor`, `vest_toad`, `boots_swamp`, `senbon_de_ferro`, `bracelete_do_viajante` |
| 16–20 | Costa: Batedor da Névoa (`mist_scout`), Guardião da Neblina (`mist_guardian`) · Floresta da Morte: Ninja Renegado (`rogue_ninja`), Serpente Menor (`lesser_serpent`) | ~1837 | 4,9 h | 14,5 h | `q_coastal_scouts` · `q_coastal_guardians` · `q_lesser_serpents` (nova) · início do **Exame Chunin** (`exam_chunin_1_teoria`) | Preparar troca para o set Chunin; manter poções médias no cinto |
| 21–25 | Floresta da Morte: Rivais do exame, Sapo Ancião (`boss_elder_toad`), Serpente Branca (`boss_white_serpent`) | ~1716 | 6,7 h | 21,2 h | `q_forest_death_collect` (nova) · `q_elder_toad_hunt` (nova) · `q_rogues` · `q_white_serpent` · **fecha o Exame Chunin** (`exam_chunin_2a/2b/3a-3c`) | Set Chunin completo: `vest_chuunin`, `bandana_chuunin`, `calca_chuunin`, `sandalia_chuunin`, `katana_ronin`, `fuuma_shuriken`, `ring_chakra` |
| 26–30 | Ruínas do Clã Marionetista: Marionete de Combate (`ruin_puppet`) | ~1522 | 9,2 h | 30,4 h | `q_ruins_intro` (nova, entrega) · `q_ruins_puppets` · `task_ruin_puppet_1/2` | Set das Ruínas completo: `mask_clan_ruins`, `robe_clan_ruins`, `greaves_clan_ruins`, `boots_clan_ruins`, `kodachi_ruins`/`chain_kunai`, `amulet_clan_seal` |
| 31–35 | Ruínas: Sentinela de Pedra (`stone_sentinel`) | ~1320 | 12,5 h | 42,9 h | `q_ruins_sentinels` · `task_stone_sentinel_1` | Upgrade de arma: `puppet_blade`; acessório alternativo `ring_stone_will` |
| 36–40 | Ruínas: Guerreiro Espectral (`spectral_warrior`) | ~1145 | 16,6 h | 59,5 h | `q_ruins_curse_lore` (nova, `keyword_quiz`) · `task_spectral_warrior_1` | Começa a droppar o set "Rastreador Sombrio" (L40) |
| 41–45 | Ruínas: Xamã da Maldição (`curse_shaman`) | ~991 | 21,7 h | 81,2 h | `q_ruins_shamans` · `task_curse_shaman_1` | Set Rastreador Sombrio completo: `mascara_rastreador_sombrio`, `manto_rastreador_sombrio`, `calca_rastreador_sombrio`, `botas_rastreador_sombrio`, `adaga_sombria`/`shuriken_sombria`, `colar_do_rastreador` |
| 46–50 | Ruínas: Desertor de Elite (`elite_deserter`), Marionetista das Ruínas (`boss_puppeteer`) — fecha metade do **Exame Jonin** | ~860 | 27,9 h | 109,1 h | `q_ruins_deserter` · `q_ruins_boss` · `task_elite_deserter_1` · `task_boss_puppeteer_1` | Set de Jonin: `mask_anbu` (drop do Marionetista), `colete_jonin`, `calca_jonin`, `botas_jonin`, `tanto_jonin`/`senbon_jonin`, `bracelete_jonin` |
| 51–55 | Montanha do Trovão: Águia do Trovão (`thunder_eagle`) | ~755 | 35,1 h | 144,2 h | `q_mountain_eagles` · `q_mountain_relics` (nova, entrega) · `task_thunder_eagle_1` | Fechar o set de Jonin; começar a guardar ryo para o set stormcaller (L60) |
| 56–60 | Montanha: Oni da Geleira (`glacier_oni`) | ~667 | 43,5 h | 187,7 h | `q_mountain_oni` · `task_glacier_oni_1` | Set stormcaller completo: `helm_stormcaller`, `mail_stormcaller`, `greaves_stormcaller`, `boots_stormcaller`, `necklace_storm_fang`, `thunder_katana`/`windblade_shuriken` |
| 61–65 | Montanha: Oni da Geleira (tarefa tier 2), rotação de spot | ~593 | 53,1 h | 240,8 h | `task_glacier_oni_2` | Manter stormcaller; trocar acessório para `ring_ancestral` se já tiver caído |
| 66–70 | Montanha: Monge da Tempestade (`storm_monk`), O Sócio Eterno (`boss_curse_partner`) | ~530 | 64,1 h | 304,9 h | `q_mountain_serpents` (início) · `q_mountain_lore` (nova, `keyword_quiz`) · `q_mountain_curse_partner` · `task_storm_monk_1` | Começa a droppar "Caçador de Onis" (L70); pegar `oni_kanabo` |
| 71–75 | Montanha: Serpente de Magma (`magma_serpent`) | ~478 | 76,4 h | 381,3 h | `q_mountain_serpents` · `task_magma_serpent_1` | Set Caçador de Onis completo: `elmo_cacador_de_onis`, `couraca_cacador_de_onis`, `grevas_cacador_de_onis`, `botas_cacador_de_onis`, `shuriken_congelante`, `talisma_cacador_de_onis` |
| 76–80 | Montanha: Oni Ancestral (`boss_ancestral_oni`) — fecha a metade "de campo" do **Exame Anbu** | ~433 | 90,1 h | 471,4 h | `q_mountain_boss` · `task_boss_ancestral_oni_1` | `oni_fang_blade` (drop); começa a droppar "Anbu Negro" (L80) |
| 81–85 | Covil da Nuvem Vermelha: Clone Branco (`white_clone`), O Vigia Ilusório (`boss_illusive_eye`) | ~394 | 105,4 h | 576,8 h | `q_lair_intro` (nova) · `q_lair_1_illusive_eye` | Set Anbu Negro completo: `capuz_anbu_negro`, `manto_anbu_negro`, `calca_anbu_negro`, `botas_anbu_negro`, `senbon_anbu_negro`, `emblema_anbu_negro` |
| 86–90 | Covil: Ninja Elite da Aurora (`elite_cloud_guard`), O Mascarado das Sombras (`boss_masked_puppeteer`) | ~360 | 122,1 h | 698,9 h | `q_lair_guards` (nova) · `q_lair_2_masked_puppeteer` | Começa a droppar "Aurora Carmesim" (L90) |
| 91–95 | Covil: O Portador dos Seis Caminhos (`boss_rings_bearer`) | ~331 | 140,5 h | 839,4 h | `q_lair_3_rings_bearer` · `task_boss_rings_bearer_1` | Set Aurora Carmesim completo: `capuz_aurora_carmesim`, `manto_aurora_carmesim`, `calca_aurora_carmesim`, `botas_aurora_carmesim`, `katana_aurora_carmesim`/`shuriken_aurora_carmesim`, `anel_aurora_carmesim` |
| 96–100 | Covil: O Ancestral da Nuvem Vermelha (`boss_crimson_ancestor`) — fecha o **Exame Kage** | ~305 | 160,6 h | **1000,0 h** | `q_lair_4_crimson_ancestor` · `task_boss_crimson_ancestor_1/2/3` | Set do Kage (fim de progressão): `chapeu_kage`, `manto_kage`, `calca_kage`, `sandalias_kage`, `lamina_do_kage`/`leque_de_lamina_kage`, `anel_do_kage` |

## Leitura da curva

- **Blocos 1–4 (nível 1–20, ~14,5 h acumuladas):** XP/h sobe (536 → 1837) porque o
  jogador ainda está ganhando eficiência de combate (jutsus tier 1, primeiras peças de
  equipamento) mais rápido do que o custo de XP por nível sobe. É a única parte do jogo
  em que XP/h cresce; é intencional, serve de "rampa de aprendizado".
- **Blocos 5–10 (nível 21–50, de 21,2 h a 109,1 h acumuladas, +88 h no meio do jogo):**
  XP/h cai de forma constante (1716 → 860) conforme HP de monstro cresce mais rápido que
  o dano do jogador recém-equipado — exatamente o comportamento descrito em
  `balanceamento.md` ("o termo `(1+(L-20)/100)`... para que o tempo de matar não caia").
- **Blocos 11–16 (nível 51–80, de 144 h a 471 h acumuladas, +327 h):** a Montanha do
  Trovão é a fase mais longa em horas absolutas — monstros tanque/ranged, bosses de
  cooldown longo (7200s) e o próprio requisito narrativo do Exame Anbu (precisa "sentir"
  como conquista, não só grind) desaceleram XP/h de 755 para 433.
- **Blocos 17–20 (nível 81–100, de 576,8 h a 1000 h acumuladas, +423 h — 42% do jogo
  inteiro nos últimos 20 níveis):** o Covil da Nuvem Vermelha é deliberadamente a parede
  final. Só dois monstros comuns (`white_clone`, `elite_cloud_guard`) e quatro bosses
  com respawn de 10800s sustentam a região inteira — é o análogo direto do "grind de
  level 100+" de Tibia, onde o jogador de fato passa a maior parte do tempo de jogo.

## Sobre a fórmula de XP (`data/progression.json`)

**Não foi alterada.** `xp_total = 50*level² + 50*level` já produz, sozinha, os ~1000 h
pedidos — o ajuste "Tibia-like" está inteiramente na curva de horas-por-bloco (isto é,
na eficiência de caça esperada por faixa, não no total de XP exigido). Mudar a fórmula
mudaria `hp_formula`/`chakra_formula` de referência cruzada em `balanceamento.md` e
quebraria os números já calibrados de HP/dano de monstro por nível — risco maior que o
benefício. Se o playtest mostrar que a curva real de XP/h diverge muito da tabela acima
(ver `balanceamento.md`, seção 8, "premissas a validar"), o lever certo continua sendo
o `ratio` de XP por monstro (balanceamento.md §2), não o expoente da fórmula de level.

## Dependência de missões e tarefas

As colunas "Missões / tarefas" desta tabela assumem as cadeias narrativas expandidas
em `data/npcs/*.json` (6–10 missões por região, rank D→S) e o sistema de tarefas
repetíveis em `data/tasks.json` (3 tiers por monstro) e diárias em `data/dailies.json`
— ver `docs/backlog-sprites.md` para o que falta de arte antes de cada bloco ficar
"pronto de verdade" e o relatório da missão para pendências de servidor
(`tools/export_tfs.py` ainda não lê `data/tasks.json`/`data/dailies.json`, ver
`docs/sistemas/progressao-servidor.md` do agente responsável pelo sistema).
