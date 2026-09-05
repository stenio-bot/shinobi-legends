# Progressão de rank — Genin → Kage

Modela em dados (`data/ranks.json`) a progressão de rank pedida pelo usuário:
"precisa... fazer algo que faça sentido, com progressão de Genin para Chunin"
— e daí para cima. Rank é uma camada **narrativa e de exame** por cima do
level; o level continua sendo a progressão numérica de sempre
(`docs/sistemas/balanceamento.md`), o rank é o que dá sentido de história a
cada faixa e obriga o jogador a provar competência, não só grindar.

## Visão geral

| Rank | Level mínimo | Exame para entrar | Região(ões) principal(is) |
|---|---|---|---|
| Genin | 1 | — (rank inicial) | Floresta da Vila |
| Chunin | 20 | Exame Chunin (3 etapas) | Floresta da Morte, depois Costa das Marés e Ruínas |
| Jonin | 50 | Exame Jonin (missão A) | Montanha do Trovão |
| Anbu | 80 | Exame Anbu (missão S) | Covil da Nuvem Vermelha (metade 1) |
| Kage | 100 | Exame Kage | Covil da Nuvem Vermelha (metade 2) |

Cada rank desbloqueia, via `data/ranks.json` (`unlocks`): um **título**
(mensagem exibida ao completar o exame), acesso à(s) **área(s)** daquele
patamar, o **tier de jutsu** de referência que o level já libera naturalmente
naquela faixa (os jutsus continuam gated por `required_level` em
`data/jutsus/*.json` — o rank só documenta/anuncia isso, não muda a mecânica
de jutsu) e um pequeno **bônus de status** fixo (HP/Chakra/defesa) que existe
só para o momento do exame ser sentido como uma virada, não como só mais um
level.

## Exame Chunin (nível ~20, Floresta da Morte)

Proctora: **Instrutora Ibuki** (NPC novo, `exam_proctor_forest`,
`data/npcs/leaf.json`). Três etapas, na ordem, como o exame real
(`docs/lore/pesquisa-naruto.md`, seção 3):

1. **Prova teórica** (`exam_chunin_1_teoria`) — a Instrutora Ibuki faz
   perguntas por palavra-chave sobre o que a vila já ensinou (chakra,
   elemento, vila, ninjutsu, hokage — ver campo `quiz` no NPC). Mecanicamente
   hoje isso vira um requisito de abate trivial (1 Cobra da Floresta) porque o
   exportador atual só entende objetivos `kill`; o campo `quiz` já está nos
   dados prontos para quando o diálogo por palavra-chave for implementado
   (ver pendências no relatório).
2. **Sobrevivência — pergaminhos Céu e Terra** — duas missões sequenciais:
   `exam_chunin_2a_pergaminho_ceu` (matar o Sapo Ancião, `boss_elder_toad`,
   recompensa = item `scroll_heaven`) e `exam_chunin_2b_pergaminho_terra`
   (matar a Serpente Branca, `boss_white_serpent`, recompensa = item
   `scroll_earth`). Só quando os DOIS pergaminhos estão na mochila é que a
   Instrutora libera a etapa 3 — no jogo isso é garantido pela ordem
   sequencial da lista de missões do NPC (regra já usada em todo o jogo:
   "sequenciais na ordem da lista", `CLAUDE.md`).
3. **Torneio** — três missões sequenciais, uma por rival:
   `exam_chunin_3a_rival_pedra`, `exam_chunin_3b_rival_som`,
   `exam_chunin_3c_rival_mist` (matar `exam_rival_stone`, `exam_rival_sound`,
   `exam_rival_mist`, nível 20 cada, `data/monsters/swamp.json`). A última
   missão da lista carrega a recompensa grande e o campo `grants_rank:
   "chunin"` (documentário — anúncio do título; a mudança de rank de verdade
   ainda depende de um storage dedicado no servidor, ver pendências).

## Exame Jonin (nível ~50, missão A)

Não tem uma proctora única — é a soma de duas provas de campo já existentes,
uma em cada região que o Chunin precisa ter limpado:

- Costa das Marés: derrotar o Espadachim da Névoa (`boss_mist_swordsman`,
  `data/npcs/coastal_tides.json`, quest `q_coastal_swordsman`).
- Ruínas do Clã Marionetista: derrotar o Marionetista das Ruínas
  (`boss_puppeteer`, `data/npcs/ruins.json`, quest `q_ruins_boss`, já
  existia — só ganhou o significado de prova de Jonin).

O jogo já rastreia as duas mortes via as quests regionais normais; o
"exame" em si é a soma das duas, anunciada por texto (ver pendência: um
storage central que confirme as duas antes de exibir o título Jonin).

## Exame Anbu (nível ~80, missão S)

Metade de campo: derrotar a dupla imortal da Montanha do Trovão — O Sócio
Eterno (`boss_curse_partner`, quest nova `q_mountain_curse_partner`) e o Oni
Ancestral (`boss_ancestral_oni`, quest `q_mountain_boss`, já existia).

Metade final: entrar no Covil da Nuvem Vermelha e derrotar os dois primeiros
guardiões — O Vigia Ilusório e O Mascarado das Sombras (NPC novo
`quest_giver_akatsuki_lair`, `data/npcs/akatsuki_lair.json`, quests
`q_lair_1_illusive_eye` e `q_lair_2_masked_puppeteer`).

## Exame Kage (nível 100, fim da progressão)

Os dois guardiões finais do covil: O Portador dos Seis Caminhos e O Ancestral
da Nuvem Vermelha (mesmo NPC, quests `q_lair_3_rings_bearer` e
`q_lair_4_crimson_ancestor`). Derrotar os dois é o clímax do jogo hoje —
tornar-se Kage de verdade (posto político, não só um título) é conteúdo de
pós-jogo (`docs/01-roadmap.md`, Marco 5).

## `data/ranks.json` — schema e conteúdo

Ver `data/schemas/rank.schema.json`. Cada entrada:
`{rank, min_level, quest_id, unlocks: {title, areas[], jutsu_tier, status_bonus{}}}`.
`quest_id` é só documentário por enquanto (não existe storage de "rank atual"
no servidor ainda) — aponta para o exame descrito acima. O exportador poderá
consumir isso no futuro para: (1) gerar uma mensagem de título ao completar a
última quest do exame, (2) gravar um storage `NarutoRank[player] = rank` e
(3) aplicar `status_bonus` como um bônus fixo de HP/Chakra/defesa somado ao
cálculo normal de `personagem-e-progressao.md`. Nada disso existe no
`tools/export_tfs.py` hoje — ver pendências no relatório da missão.

## Pendências técnicas (atualizado 2026-09-05)

> Nota: `keyword_quiz`, `collect_item`, `talk_to`, confirmação de rank centralizada (`NarutoRanks.promote`) e bônus de status **já estão implementados** em `tools/export_tfs.py`/`naruto_quests.lua`/`naruto_ranks.lua` (ver `docs/design/auditoria-historia.md`, seção Sistemas). O texto original abaixo ficou como histórico.

 (fora do escopo desta missão — não editei `tools/`)

1. **Objetivo de quest novo `keyword_quiz`**: a prova teórica precisa de um
   NPC que aceite respostas por palavra-chave e só libere a missão seguinte
   se acertar N perguntas. O TFS já usa `keywordHandler` para o menu de
   missão (`tools/export_tfs.py`, função `npc_files`) — dá para estender.
2. **Confirmação de rank centralizada**: hoje cada quest tem seu próprio
   storage independente; não existe um storage único "rank atual do
   jogador". Precisa de um pequeno script (`data/scripts/naruto/rank_check.lua`
   fora do `tools/`, ou uma função nova em `export_tfs.py`) que, ao completar
   a(s) quest(s)-chave de cada exame, grave o rank e dispare a mensagem de
   título.
3. **Bônus de rank (`status_bonus`)**: precisa ser somado no cálculo de
   HP/Chakra do personagem — hoje só `level` entra na fórmula
   (`balanceamento.md`, seção "Referências fixas").
4. **Schema de quest formal**: criei `data/schemas/quest.schema.json` como
   documentação do formato alvo (`objective` com `kind: kill | collect_item |
   keyword_quiz`), mas `tools/validate_data.py` ainda não valida `npcs/*.json`
   contra ele (só faz checagens ad-hoc hoje). Não editei `validate_data.py`
   por estar fora do escopo autorizado desta missão.
