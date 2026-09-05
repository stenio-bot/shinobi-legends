# Bíblia do mundo — Shinobi Legends

Mapa narrativo do nosso mundo, região por região, alinhado aos arcos pesquisados em
`docs/lore/pesquisa-naruto.md`. Regra de ouro (ADR-002 + feedback do usuário):
**inimigo genérico nunca usa visual de personagem principal** (looktypes 900–926);
esse visual é reservado para NPCs mentores e para os poucos bosses de arco listados
abaixo. Toda região tem: história, inimigos genéricos, boss(es), NPCs e a
missão/exame que fecha a região.

Seis regiões: quatro já implementadas (mapa `forest_valley`, zonas existentes,
ver `docs/sistemas/mapas.md`), duas novas e ainda não desenhadas no mapa físico
(dados prontos em `data/`, pedido formal ao agente de mapa em
`data/maps/spawns_lore.json`).

---

## 1. Floresta da Vila (`floresta_da_vila`) — Genin, nível 1–10 [implementada]

**História.** A floresta que cerca a vila é o primeiro teste de qualquer genin
recém-formado: perto o bastante para uma equipe Jonin resgatar quem se meter em
apuros, perigosa o bastante para separar quem está pronto para o mundo lá fora.
Lobos, cobras e uma trilha comercial infestada de bandidos comuns dão o
primeiro sabor de combate real — nada aqui é obra de vilões lendários, só gente
e bicho tentando sobreviver perto demais da vila.

**Inimigos genéricos.**
| Monstro | Visual (sprite genérico) |
|---|---|
| Lobo (`wolf`) | looktype 21 (placeholder de fera) |
| Cobra da Floresta (`forest_snake`) | looktype 56 "serpent" |
| Bandido (`bandit`) | looktype 129 "ninja_bandit" |
| Bandido Arqueiro (`bandit_archer`) | looktype 129 "ninja_bandit" |
| Cervo (`forest_deer`, passivo) | looktype 21 recolorido |

**Boss.** Chefe dos Bandidos (`boss_bandit_chief`, nível 12) — não é ninja
renomado nenhum, é só o bandido mais experiente da estrada, armado e com
squad. Visual: looktype 131 "ninja_chief" (era 915/Sasuke Akatsuki — trocado
por ser exatamente o erro que o usuário reportou).

**NPCs.** Ichiro, o Mercador (loja) · Mestre Hayato, sensei de pergaminhos
(visual Kakashi, 906 — o Jonin de cabelo prateado como mestre de jutsus, uso
correto de personagem principal) · Capitã Rin, quem dá as missões da região
(visual Sakura, 917).

**O que fecha a região.** Nenhum exame formal — é onde o jogador nasce como
Genin. A saída natural é para a Costa das Marés ou direto para a Floresta da
Morte, quando pronto para o Exame Chunin.

---

## 2. Costa das Marés (`costa_das_mares`) — Genin, nível 12–19 [NOVA, dados prontos]

Inspirada no arco do **País das Ondas** (Zabuza/Haku). Ver pedido de spawn em
`data/maps/spawns_lore.json` — região ainda sem posição física no mapa.

**História.** Uma vila de pescadores e a ponte que a liga ao continente vivem
sob a sombra de uma guilda mercante rival que contratou um espadachim renegado
para sabotar a obra. Ele não trabalha sozinho: um aprendiz mascarado, ligado a
ele por uma dívida mais funda que dinheiro, aparece sempre que ele está perto
de cair, e luta como se a vida dele dependesse — de fato depende — da do
mestre.

Antes de chegar à ponte, o time precisa atravessar mercenários de baixo escalão
contratados às pressas e batedores que vigiam a estrada da costa, todos gente
comum tentando ganhar a vida do lado errado da lei — o mesmo princípio da
Floresta da Vila, agora numa paisagem de mar e neblina.

**Inimigos genéricos.**
| Monstro | Visual |
|---|---|
| Mercenário da Ponte (`mercenary_bridge`, nv 12) | looktype 129 "ninja_bandit" |
| Batedor da Névoa (`mist_scout`, nv 14, ranged) | looktype 128 "ninja_blue" |
| Guardião da Neblina (`mist_guardian`, nv 16, tanque) | looktype 131 "ninja_chief" |

**Boss (dupla).** Espadachim da Névoa (`boss_mist_swordsman`, nível 19) — luta
sozinho até 60% de vida, quando invoca o Aprendiz Mascarado (`masked_apprentice`,
mini-boss aliado, nv 17) para protegê-lo; perder o aprendiz é o gatilho da fase
de fúria (25%, quando o espadachim luta como se não tivesse mais nada a
perder). Visuais: 132 "ninja_white" (espadachim) e 130 "ninja_pale" (aprendiz)
— nenhum dos dois usa personagem principal, são a dupla mais "pessoal" da
história do jogo e por isso merecem visual próprio, não emprestado.

**NPCs.** Um mercador de estrada (visual genérico 139 "merchant_green") e um
ancião da vila costeira que dá as missões da região (visual genérico 137
"elder_red").

**O que fecha a região.** Derrotar o Espadachim da Névoa (e, por consequência,
o Aprendiz Mascarado) é um dos dois requisitos do **Exame Jonin** (junto com o
Marionetista das Ruínas — ver `docs/lore/progressao.md`), então esta região só
"fecha" de verdade quando o jogador já é Chunin e volta aqui numa missão de
prova de nível A.

---

## 3. Floresta da Morte (`floresta_da_morte`) — Genin→Chunin, nível 10–25 [implementada]

**História.** A mesma floresta abriga o campo de provas mais temido da região:
gente entra em duplas ou trios e só sai — supostamente — depois de provar que
sobrevive sem apoio da vila. Sanguessugas e sapos gigantes são só o alarme;
ninjas renegados fizeram da mata um esconderijo permanente; e no fundo, perto
de um santuário abandonado, mora uma criatura que já foi humana e decidiu que
não precisa mais fingir.

É aqui, e só aqui, que a vila autoriza a segunda etapa do Exame Chunin: entrar
com um pergaminho, sair com dois.

**Inimigos genéricos.**
| Monstro | Visual |
|---|---|
| Sanguessuga Gigante (`leech`) | looktype 19 |
| Sapo Gigante (`giant_toad`) | looktype 60 "great_beast" |
| Ninja Renegado (`rogue_ninja`) | looktype 128 "ninja_blue" (era 914/Sasuke Taka) |
| Serpente Menor (`lesser_serpent`) | looktype 56 "serpent" |
| Rival do Exame — Pedra / Som / Névoa (`exam_rival_stone/sound/mist`, nv 20) | looktypes 128/129/130 |

**Bosses.** Serpente Branca (`boss_white_serpent`, nível 25) — o boss de arco
mais "canônico" do jogo, um ninja renegado de pele pálida que abandona a forma
humana quando encurralado (visual 916, Sasuke Rinnegan — **mantido**, é o uso
correto e intencional de personagem principal em boss de arco que o próprio
usuário validou como já certo). Sapo Ancião (`boss_elder_toad`, boss
secundário, nível 25).

**NPCs.** Velha Sumi (loja) · Rastreador Goro (missões de caça) · **NOVA:**
Instrutora Ibuki, a proctora do exame (visual 918, Sakura The Last — até então
sem uso), que conduz as três etapas do Exame Chunin (ver progressao.md).

**O que fecha a região.** O **Exame Chunin** inteiro roda aqui: prova
teórica com a Instrutora Ibuki, sobrevivência (pergaminhos Céu/Terra dos dois
bosses da região) e torneio (os 3 rivais do exame). Ver
`docs/lore/progressao.md` para o passo a passo.

---

## 4. Ruínas do Clã Marionetista (`ruinas_do_cla_marionetista`) — Chunin, nível 25–50 [implementada]

**História.** Um clã extinto que servia à Vila da Areia dominava a arte de
lutar através de bonecos de guerra — a mesma tradição, em menor escala, que
ainda se vê nos exércitos de marionetes usados durante a invasão que abalou o
exame Chunin. As ruínas do seu templo continuam de pé, os bonecos ainda
"vivos" pela última ordem que receberam, guardadas por sentinelas de pedra e
por espíritos que morreram defendendo o lugar e nunca aceitaram a derrota.

Um xamã mantém os selos de maldição ativos há gerações; e recentemente um
gênio desertor, fugindo da própria vila atrás de poder proibido, escolheu
estas ruínas como esconderijo antes de seguir para a Toca do Som — o mesmo
enredo, em miniatura, da perseguição que a vila lança atrás de desertores de
elite.

**Inimigos genéricos.**
| Monstro | Visual |
|---|---|
| Marionete de Combate (`ruin_puppet`) | looktype 129 "ninja_bandit" |
| Sentinela de Pedra (`stone_sentinel`) | looktype 61 "stone_golem" |
| Guerreiro Espectral (`spectral_warrior`) | looktype 130 "ninja_pale" (era 912/Obito) |
| Xamã da Maldição (`curse_shaman`) | looktype 138 "hooded_purple" (era 911/Pain) |

**Mini-boss e boss.** Desertor de Elite (`elite_deserter`, nível 46, **NOVO**)
— visual 915 "Sasuke Akatsuki" (liberado do Chefe dos Bandidos): um gênio que
abandonou a vila atrás de poder e agora recruta para a Toca do Som, eco direto
do arco de Resgate do Sasuke / Quatro do Som. Marionetista das Ruínas
(`boss_puppeteer`, nível 50, boss principal) — visual 131 "ninja_chief" (era
910/Itachi).

**NPCs.** Tsubaki, a Escavadora (loja) · Ancião Kaito (missões, agora com uma
missão extra contra o Desertor de Elite antes do boss final).

**O que fecha a região.** Derrotar o Marionetista das Ruínas é o segundo
requisito do Exame Jonin (junto com o Espadachim da Névoa da Costa das Marés).

---

## 5. Montanha do Trovão (`montanha_do_trovao`) — Jonin, nível 50–80 [implementada]

**História.** A trilha que sobe a montanha é onde jonins provam que aguentam
o próprio peso: águias territoriais, onis que descem do gelo, monges que
treinam a vida toda no penhasco e serpentes que vivem nas fendas de magma. No
topo, dois seres amaldiçoados por um pacto antigo dividem a montanha entre si
— um não sabe morrer, o outro cobra um preço por cada vida que consome — a
mesma fantasia da dupla imortal que a Organização da Nuvem Vermelha lançou
contra vilas inteiras durante a guerra.

Ninguém sabe se os dois nasceram assim ou se o pacto os transformou; o que se
sabe é que só caem juntos — matar um sem enfrentar o outro é perder tempo, o
sobrevivente simplesmente absorve a fúria do parceiro morto.

**Inimigos genéricos.**
| Monstro | Visual |
|---|---|
| Águia do Trovão (`thunder_eagle`) | looktype 21 (placeholder de ave) |
| Oni da Geleira (`glacier_oni`) | looktype 12 "oni_fox" |
| Monge da Tempestade (`storm_monk`) | looktype 137 "elder_red" |
| Serpente de Magma (`magma_serpent`) | looktype 56 "serpent" |

**Dupla de bosses.** O Sócio Eterno (`boss_curse_partner`, nível 70, **NOVO**)
— visual 138 "hooded_purple" (reaproveitado do Xamã, região diferente): a
metade "humana" do pacto, ganha uma fase nova a cada "coração" perdido (75%,
50%, 25% de vida). Oni Ancestral (`boss_ancestral_oni`, nível 80, boss final
da região) — visual 12 "oni_fox" (era 913/Madara, liberado para o boss final
de verdade): a metade "fera" do pacto, dorme entre as lutas e acorda com raiva
de gerações.

**NPCs.** Ferreiro Genzo (loja) · Mestra Yuki (missões, agora com uma missão
extra contra o Sócio Eterno antes do Oni Ancestral).

**O que fecha a região.** Derrotar os dois (Sócio Eterno + Oni Ancestral) é a
parte "de campo" do **Exame Anbu** — a outra metade acontece na entrada do
covil final.

---

## 6. Covil da Organização Nuvem Vermelha (`covil_nuvem_vermelha`) — Anbu/Kage, nível 80–100 [NOVA, dados prontos]

Antes chamada "Fortaleza Akatsu" (`docs/sistemas/monstros-e-pvm.md`, linha
"planejada") — mesmo conceito, agora nomeada e desenhada. Ver pedido de spawn
em `data/maps/spawns_lore.json`.

**História.** No topo da cadeia de poder do mundo shinobi está uma organização
de renegados de capa preta e nuvens vermelhas, que colecionam portadores de
poder para um plano que nenhum Kage sozinho consegue deter. Só quem prova ser
Anbu — o corpo de elite que age direto sob as ordens do Kage, sem as regras de
uma missão comum — recebe autorização para entrar no covil. Quatro figuras
guardam os corredores, cada uma um espectro de um poder que a vila enfrentou
uma vez e nunca mais quis enfrentar de novo: o olho que prende quem olha
demais, o mascarado que puxa os fios de todos os outros eventos de longe, o
portador de olhos em anel que multiplica a própria vontade em vários corpos, e
o ancestral que fundou a própria ideia da organização.

Ninguém que entra aqui como Chunin sai vivo — este é o teste final antes do
posto de Kage, e a vila só manda quem já provou, na Montanha do Trovão, que
aguenta enfrentar dois monstros ao mesmo tempo.

**Inimigos genéricos.**
| Monstro | Visual |
|---|---|
| Clone Branco (`white_clone`, nv 82) | looktype 130 "ninja_pale" |
| Ninja Elite da Aurora (`elite_cloud_guard`, nv 88) | looktype 129 "ninja_bandit" |

**Bosses (quatro, na ordem da masmorra).**
| Boss | Nível | Visual | Inspiração (ADR-002: só estrutura, nome próprio) |
|---|---|---|---|
| O Vigia Ilusório (`boss_illusive_eye`) | 85 | 910 (Itachi, liberado do Marionetista das Ruínas) | genjutsu/olho que prende |
| O Mascarado das Sombras (`boss_masked_puppeteer`) | 90 | 912 (Obito) | manipula tudo de longe, "puxa os fios" políticos |
| O Portador dos Seis Caminhos (`boss_rings_bearer`) | 95 | 911 (Pain) | olhos em anel, invoca "caminhos" |
| O Ancestral da Nuvem Vermelha (`boss_crimson_ancestor`) | 100, boss final | 913 (Madara) | fundador, luta final antes do posto de Kage |

Esses quatro looktypes (910–913) são os ÚNICOS lugares do jogo, fora da
Serpente Branca (916), onde um visual de personagem principal aparece — e
aqui faz sentido total: são literalmente os chefes da organização mais
poderosa do mundo, o clímax de progressão do jogo. Looktype 915 (Sasuke
Akatsuki) foi remanejado para o Desertor de Elite das Ruínas; 914 (Sasuke
Taka) fica **reservado e sem uso** — proposta no relatório para uma futura
squad "Quatro do Som".

**NPCs.** Capitã Anbu (visual Minato Edo, 908 — um Hokage/general de elite
guiando a prova final) dá as quatro missões sequenciais (uma por boss);
fornecedor de suprimentos de guerra (visual genérico 139).

**O que fecha a região.** Derrotar O Vigia Ilusório + O Mascarado das Sombras
= **Exame Anbu** (nível 80–99, "missão S"). Derrotar O Portador dos Seis
Caminhos + O Ancestral da Nuvem Vermelha = **Exame Kage** (nível 100, fim da
progressão de rank). Ver `docs/lore/progressao.md`.

---

## Regiões futuras (só conceito, sem dados ainda)

Citadas aqui para não perder o fio, mas **não implementadas** (nem em
`data/`, nem pedidas em `spawns_lore.json`) — ficam para uma próxima
missão de lore quando o jogo tiver mais faixas de level livres:

- **Deserto da Areia** — território da Vila da Areia entre a invasão do
  Exame Chunin e o resgate do Kazekage; encaixaria entre Ruínas (25–50) e
  Montanha (50–80) ou como rota alternativa de Chunin.
- **Quatro do Som** — esquadrão de elite reaproveitando o looktype 914
  (Sasuke Taka, hoje sem uso) e mais 2–3 looktypes genéricos ainda não
  recortados da folha (índices 15–20, 36–45 de `monsters_sheet.json` — ver
  pendências no relatório final).
- **Guerra / Aliança Shinobi** — conteúdo de fim de jogo pós-Kage, PvP e
  eventos de clã (já previsto em `docs/01-roadmap.md`, Marco 5).
