# Pesquisa — estrutura narrativa do Naruto clássico e Shippuden

Este documento resume a pesquisa feita para embasar `docs/lore/mundo.md` e
`docs/lore/progressao.md`. Objetivo: entender a estrutura real dos arcos, do
sistema de ranks e das vilas para que as regiões, monstros e a progressão do
Shinobi Legends façam sentido narrativo — não só numérico. Lembrete de ADR-002:
tudo aqui é **referência de estrutura**, não texto a copiar; nomes próprios do
jogo continuam inventados.

## 1. Arcos, em ordem, e o que puxamos de cada um

| # | Arco (fonte) | Nível de referência (nosso rank) | O que puxamos para o jogo |
|---|---|---|---|
| 1 | Academia + formação do Time 7 | Genin 1–10 | Tutorial, primeira missão "perigosa" na floresta perto da vila, mentor Jonin |
| 2 | País das Ondas (Zabuza/Haku) | Genin 12–19 | Região costeira nova, boss em dupla (espadachim + aprendiz mascarado) |
| 3 | Exame Chunin — 1ª prova (escrita) | Genin →Chunin | Prova teórica por palavras-chave com um NPC instrutor |
| 4 | Exame Chunin — 2ª prova (Floresta da Morte) | Genin →Chunin | Sobrevivência: coletar pergaminhos Céu/Terra de bosses da região |
| 5 | Exame Chunin — preliminares + torneio | Genin →Chunin | Torneio: derrotar 3 oponentes em sequência na arena |
| 6 | Invasão da Areia e do Som / Konoha Crush | Chunin 20–50 | Vilão infiltrado, tema "clã que usa marionetes" (liga Areia + traição) |
| 7 | Busca por Tsunade | Chunin 20–50 | NPC médica-ninja como mentora de cura (referência de papel, não de mapa) |
| 8 | Resgate do Sasuke / Quatro do Som | Chunin 20–50 | Mini-boss "desertor de elite" nas Ruínas, ecoando um gênio que desertou |
| 9 | Shippuden — Resgate do Kazekage (Akatsuki: dupla de marionetista e explosivos) | Jonin (transição) | Reforça o tema "marionetes" já usado nas Ruínas |
| 10 | Shippuden — Akatsuki: a dupla imortal | Jonin 50–80 | Boss secundário da Montanha do Trovão: parceiro amaldiçoado que "não morre" |
| 11 | Shippuden — Ataque de Pain | Anbu 80–99 | Um dos bosses do covil final: portador de olhos em anel |
| 12 | Cúpula dos Five Kage / Guerra | Anbu → Kage | Covil final: mascarado que manipula por trás, ancestral fundador |

## 2. Sistema de ranks (fonte oficial)

Genin → Chunin → Jonin, com Kage como topo de cada vila e ANBU como corpo de
elite/assassinato subordinado direto ao Kage (não é um "rank" numerado, é um
serviço de elite dentro ou logo abaixo do Jonin). Isso bate com o design que
pedimos: Genin (1–20) → Chunin (20–50) → Jonin (50–80) → Anbu (80–99) → Kage (100),
tratando ANBU como o topo operacional antes do posto político de Kage.

> "Genin... newly graduated ninjas from the academy." / "Only after passing the
> Chūnin Exams is a person able to attain the rank of Chūnin." / "Jonin...
> generally highly experienced ninja... serve as military captains." / "The
> Kage is the highest official position... reserved only for a Hidden
> Village's official leader." / ANBU = "assassination squads that serve
> directly under the village's leader ... selected from exceptional Jonin and
> Chunin."
> — [CBR, "Naruto Ninja Rankings, Explained"](https://www.cbr.com/naruto-ninja-rankings/);
> [Narutopedia, "Shinobi Organisational System"](https://naruto.fandom.com/wiki/Shinobi_Organisational_System)

## 3. Estrutura do Exame Chunin (a base da nossa "Missão de Rank 1")

Três provas, cada uma virou uma etapa da nossa `exam_chunin`:

1. **Prova escrita** (Ibiki): não é sobre saber a resposta, é sobre não ser
   pego colando. Viramos isso em pergunta-resposta por palavra-chave com um
   NPC instrutor — o "colar" vira "prestar atenção ao que os NPCs da vila já
   ensinaram" (chakra, elemento, vila, ninjutsu, hokage).
2. **Floresta da Morte** (Anko): equipes recebem um pergaminho Céu OU Terra e
   precisam chegar à torre central com os dois, sobrevivendo 5 dias.
   Viramos isso em "mate os dois bosses da região e pegue um pergaminho de
   cada" — mais direto para PvM solo.
3. **Preliminares + torneio**: lutas individuais eliminatórias; só quem vence
   vira Chunin. Viramos isso em "derrote 3 oponentes em sequência na arena".

> "The Written Exam... is less about academic knowledge and more about a
> ninja's ability to gather information... proctored by Anko Mitarashi, the
> second stage takes place in the Forest of Death, where three-man teams are
> given either a Heaven Scroll or an Earth Scroll... In the preliminaries,
> individual ninja are randomly picked to fight each other."
> — [CBR, "What Are The Stages Of The Chunin Exams?"](https://www.cbr.com/naruto-chunin-exams-stages/);
> [Narutopedia, "Chūnin Exams"](https://naruto.fandom.com/wiki/Ch%C5%ABnin_Exams)

## 4. Arcos de Shippuden usados no covil final (Anbu/Kage)

Ordem canônica confirmada: Resgate do Kazekage (Sasori e Deidara sequestram o
Kazekage da Areia) → missão de reconhecimento a Tenchi Bridge → Supressão da
Akatsuki (Hidan e Kakuzu matam a hospedeira da Duas Caudas; Shikamaru e equipe
caçam a dupla) → Ataque de Pain → Cúpula dos Five Kage → Quarta Guerra Ninja.

> "Kazekage Rescue Mission — Sasori and Deidara, members of Akatsuki, locate
> Gaara and abduct him... Akatsuki Suppression Mission — Kakuzu and Hidan
> kill the host of Two-Tails... Pain's Assault... Five Kage Summit... Fourth
> Shinobi World War."
> — [Dashtoon, "Chronological Order of All Naruto Shippuden Arcs"](https://dashtoon.com/blog/naruto-shippuden-arcs-order/)

Isso deu a peça que faltava para a Montanha do Trovão (nossa área Jonin
50–80): em vez de inventar um segundo vilão do nada, o boss secundário virou
"o parceiro amaldiçoado que não morre" — a mesma fantasia de Hidan/Kakuzu
(imortalidade + caçador de recompensas), sem usar os nomes nem a aparência
deles.

## 5. Estrutura de vilas e o "elenco genérico" que cada uma produz

Toda vila grande (Folha, Areia, Névoa, Nuvem, Pedra, Som) tem: um Kage, um
conselho, um corpo Jonin, Chunin instrutores e uma massa de Genin — e é essa
massa de Genin/Chunin comuns, não os protagonistas, que vira "bandido",
"ninja renegado" ou "mercenário" quando a vila cai em desgraça ou expulsa
gente (como a Vila do Som de Orochimaru, formada por desertores). Isso confirma
a crítica do usuário: monstro comum = soldado anônimo daquela estrutura,
nunca um protagonista. Os "vilões genéricos" recorrentes nas fontes
consultadas (fandom wikis de arcos, guias de temporada) são: bandidos de
estrada, ninjas renegados/desertores, mercenários contratados, esquadrões de
elite de vilas rivais (o "Quatro do Som" é o exemplo mais citado), marionetes
de combate (clã Sasori/Kankuro), cobras e serpentes (motivo recorrente de
Orochimaru), sapos (motivo de Jiraiya/Monte Myouboku) e clones/duplicatas
(jutsu Bunshin, e no fim da série os "Zetsu brancos" clonados em massa) — todo
esse elenco já está ou vai para os monstros genéricos do jogo (ver
`docs/lore/mundo.md`).

## 6. O que NTO/Narutibia faziam (para a progressão de missões)

Servidores OT de tema Naruto (Narutibia, NTO — jogados por nós/comunidade,
sem fonte de texto citável específica por serem forks fechados) usam
tradicionalmente: **missões por letra** (D → C → B → A → S, crescendo em
recompensa e risco, D sendo "mate N bichos" e S sendo "derrote um boss único
com pré-requisito de nível/rank"), e a "prova de rank" como um evento
distinto do grind normal (o jogador precisa ativamente completar uma quest
de X etapas, não só chegar ao level). Replicamos essa letra D/C/B/A/S como
**categoria de dificuldade da missão**, não como rank em si (rank continua
sendo Genin/Chunin/Jonin/Anbu/Kage); ver a tabela de missões por letra em
`docs/lore/progressao.md`.

## Fontes

- [CBR — "Naruto Ninja Rankings, Explained"](https://www.cbr.com/naruto-ninja-rankings/)
- [CBR — "What Are The Stages Of The Chunin Exams?"](https://www.cbr.com/naruto-chunin-exams-stages/)
- [CBR — "Every Single Naruto & Shippuden Story Arc, In Chronological Order"](https://www.cbr.com/every-naruto-story-arc-chronological-order/)
- [Narutopedia — "Shinobi Organisational System"](https://naruto.fandom.com/wiki/Shinobi_Organisational_System)
- [Narutopedia — "Chūnin Exams"](https://naruto.fandom.com/wiki/Ch%C5%ABnin_Exams)
- [Dashtoon — "Chronological Order of All Naruto Shippuden Arcs"](https://dashtoon.com/blog/naruto-shippuden-arcs-order/)
- Base de dados interna do projeto: `data/monsters/*.json`, `data/tfs_mapping.json`,
  `assets-src/sprites/imports.json`, `assets-src/sprites/mugen_looktypes.json`
  (o que já existe em termos de sprite/visual disponível).
