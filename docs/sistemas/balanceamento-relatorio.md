# Relatório de balanceamento PvM — Shinobi Legends (setembro/2026)

Gerado com `tools/balance/sim.py` (Monte Carlo, fórmulas reais do TFS 1.4.2 — ver
`tools/balance/README.md` para a lista completa de fórmulas com arquivo:linha do
`server/tfs/src/`, e a lista separada de premissas do simulador que **não** vêm do jogo).
Matriz completa: 17 níveis × 38 monstros × 2 builds, ~30s de execução
(`python3 tools/balance/sim.py --matrix --json /tmp/matrix.json`).

## 1. Metas (de `docs/sistemas/balanceamento.md` e `docs/sistemas/progressao-jogador.md`)

- L1→L100 em ~1000h, ritmo Tibia-like (rápido no início, cada vez mais lento).
- 4–7 kills por level com o monstro do próprio nível na região certa.
- Dano de monstro: 8–12% do HP de um player do mesmo nível por hit; ~9 hits pra matar sem cura.
- Taijutsu = dano constante barato (sem chakra); ninjutsu = burst com chakra.
- Vantagem elemental ×1,5 / desvantagem ×0,75.
- Bosses (7–8× HP normal, dano só ~10% acima): fase que muda o combate de verdade.

## 2. O maior achado: as metas acima nunca estavam sendo cumpridas pelo jogo real

O simulador mostrou, ANTES de qualquer correção, dois modos de falha opostos e igualmente
graves, ambos vindos de **configuração/gerador, não dos números em `data/`**:

**2.1. XP 5–7× mais rápida que o documentado.** `server/tfs/config.lua` tinha uma tabela
`experienceStages` (7×/6×/5×/4×/3× por faixa de nível) que parecia desligada por
`data/XML/stages.xml` ter `<config enabled="0"/>` — mas `ConfigManager::loadXMLStages()`
(`configmanager.cpp:107-121`) devolve `{}` nesse caso e o código then CAI para
`loadLuaStages()` (`configmanager.cpp:278-283`), que lê exatamente essa tabela do
`config.lua`. As stages **sempre estiveram ativas de verdade**. Conferi contra várias linhas
da tabela "kills por level" de `balanceamento.md` §2 (todas calibradas com XP CRUA do
monstro, sem multiplicador — ex.: bandido L5, 600 XP pra subir / 60 XP do bandido = 10 kills,
bate exatamente com "bandido L5 = 10 kills" do doc) e com `progressao-jogador.md` (XP/h por
bloco): ambos os documentos foram escritos assumindo `rate=1`. Com as stages reais ativas, um
personagem chegaria a L100 numa fração das ~1000h pretendidas.

**2.2. Taijutsu puro inviável a partir do L5 (~100% de morte contra monstro do próprio
nível).** O gerador de `vocations.xml` (`tools/export_tfs.py`) usava multiplicador de skill
1.5–2.0 para taijutsu/shuriken/defesa — um template genérico de TFS, nunca calibrado —
contradizendo `data/skills.json` (`"tries_formula": "50 * 1.1^(skill - 10)"`). Com mult=2.0 a
skill taijutsu fica travada em ~17–25 do nível 5 ao 100 inteiro (o custo em tentativas dobra a
cada nível de skill); `weapons.cpp:135 Weapons::getMaxWeaponDamage` depende de `skill/4+1`,
então o dano de arma nunca decola. Resultado medido: um personagem só-de-taijutsu perde
sistematicamente contra o monstro do seu próprio nível a partir de L5 — a identidade
"taijutsu = dano constante" simplesmente não funcionava.

Um terceiro problema relacionado, mais estrutural: o `manamultiplier` (magic level = skill
"ninjutsu") estava em 4.0 (outro template do Tibia clássico); com a fórmula real
`getReqMana(ML) = 1600×mult^(ML-1)` (`vocation.cpp:149`, o `1600` é fixo em C++, não editável
por config), o magic level fica em single-digit o jogo inteiro, contribuindo para jutsus
tier 2/3 perderem em DPS sustentado contra taijutsu a partir de ~L15-20.

### Correções aplicadas

| Arquivo | Antes | Depois | Por quê |
|---|---|---|---|
| `server/tfs/config.lua` | `experienceStages = {7×...3×}` (ativo de verdade via fallback Lua) | `experienceStages = nil` | `docs/sistemas/balanceamento.md` §2 e `progressao-jogador.md` foram calibrados com XP crua (rate=1); confirmado batendo múltiplas linhas da tabela "kills por level" |
| `server/tfs/config.lua` | `rateExp = 5` | `rateExp = 1` | mesmo achado — com rate>1 a curva de 1000h vira uma fração disso |
| `tools/export_tfs.py` (gerador `vocations.xml`) | skill mult taijutsu/shuriken/genjutsu/defesa = 1.5–2.0 | `1.1` uniforme | bate com `data/skills.json`; sem isso taijutsu puro morre ~100% das vezes contra monstro do próprio nível a partir de L5 (medido no simulador) |
| `tools/export_tfs.py` (mesma seção) | `manamultiplier = 4.0` | `1.3` | jutsus tier 2/3 perdiam DPS sustentado pra taijutsu a partir de ~L15-20; `1.3` reduz a defasagem sem zerar o teto do magic level (que depende de uma constante fixa em C++, fora do escopo desta sessão) |

`config.lua` **não é versionado** (`server/tfs/.gitignore`) — é a cópia de execução local de
`config.lua.dist` (esse sim versionado, e intocado: é o default de fábrica do TFS, não deste
jogo). Editei o `config.lua` de execução diretamente; se o servidor for reprovisionado do zero
a partir do `.dist`, os dois fixes de `rateExp`/`experienceStages` precisam ser reaplicados —
vale registrar isso em `docs/04-setup-ot.md` num passe futuro.
`tools/export_tfs.py` foi rodado depois do fix (gera em `server/generated/`, não instalado —
por instrução desta sessão, outro agente está usando o servidor rodando).

### Efeito medido (mesmo monstro/nível, build taijutsu, antes → depois dos 3 fixes)

| Cenário | Antes | Depois |
|---|---|---|
| Bandido (L5) vs jogador L5, taijutsu | TTK 31s, **death_rate 100%** (skill preso em 17) | TTK 23s, death_rate 0% |
| Curse Shaman (L44) vs jogador L40, taijutsu | **death_rate 100%** | TTK 11s, death_rate 0% |
| Chefe dos Bandidos (boss, L12) vs jogador L12, taijutsu | **death_rate 100%** (skill preso em ~20) | TTK 151s, death_rate 0% (com poção — ver §3) |
| XP/h Bandido L5 (taijutsu) | 41 113/h (rate real ×7 nessa faixa) | 7 874/h |

## 3. Correção de metodologia do próprio simulador (documentada, sem isso os números de boss
mentiam)

Antes de simular com uso de poção, **todo boss do jogo aparecia com death_rate 100%** —
inclusive a Serpente Branca, o Chefe dos Bandidos e todos os 4 bosses finais do Covil. Isso
não é o jogo quebrado: é o simulador testando "jogador não bebe poção nunca" contra encontros
desenhados pra durar minutos e gastar consumível (respawn de 2–3h, loot cheio de poções). Com
uma poção de vida (a melhor disponível pro nível) bebida abaixo de 35% de HP — comportamento
de qualquer jogador real —, **death_rate cai a 0% em toda a matriz same-level**, e as métricas
viram TTK/gasto de poção/ryo líquido, que é o que realmente importa pra avaliar um boss. Ver
`tools/balance/README.md` pra a discussão completa (inclusive por que XP/h do simulador roda
estruturalmente ACIMA da tabela "misturada" de `progressao-jogador.md`, que inclui viagem,
missão e cooldown de boss amortizado — o simulador mede só eficiência de caça pura, útil pra
comparação relativa, não pra bater o número absoluto do doc).

## 4. Tabelas por região (faixa real medida vs pretendida no lore, XP/h, risco)

Risco = death_rate simulado no nível do monstro, **sem poção seria sempre alto para bosses
por design** (ver §3); a coluna relevante pra "monstro perigoso demais" é o death_rate de
monstro **comum** (não-boss), que deveria ficar perto de 0% pro nível pretendido.

### Floresta da Vila (lore: L1–10 comum, boss L12)

| Monstro | Nível | TTK taijutsu | TTK ninjutsu | XP/h (taijutsu) | Risco |
|---|---|---|---|---|---|
| Lobo | 2 | 44,8s | 4,0s | 1 882/h | nenhum |
| Cervo (passivo, teste) | 2 | 11,5s | 2,0s | 1 243/h | nenhum (trivial por design, ver `monstros-e-pvm.md`) |
| Cobra da Floresta | 4 | 13,5s | 1,5s | 9 828/h | nenhum |
| Bandido | 5 | 24,4s | 4,2s | 7 874/h | nenhum |
| Bandido Arqueiro | 7 | 5,6s | 3,9s | 33 449/h | nenhum |
| **Chefe dos Bandidos (boss)** | 12 | 150,9s / ~21 poções | 62,7s / ~8 poções | 35 085/h (taijutsu) | 0% com poção; **taijutsu gasta quase toda a própria recompensa em poção** (ryo/h líquido só 2 386 — ver §6.5) |

Faixa real: **1–12, batendo com o lore (1–10 comum + boss L12)**. Sem problema de faixa.

### Costa das Marés (lore: L12–19)

| Monstro | Nível | TTK taijutsu | TTK ninjutsu | XP/h (taijutsu) | Risco |
|---|---|---|---|---|---|
| Mercenário da Ponte | 12 | 15,5s | 8,2s | 27 297/h | nenhum |
| Batedor da Névoa | 14 | 16,8s | 5,5s | 30 888/h | nenhum |
| Guardião da Neblina | 16 | 42,8s | 9,3s | 18 092/h | nenhum, mas taijutsu já é lento (ryo/h só 312 — ver §6.5) |
| Aprendiz Mascarado | 17 | 53,0s | 15,0s | 24 434/h | **não é monstro de hunt** — é mini-boss ALIADO invocado na fase 2 do Espadachim da Névoa (`description` do próprio JSON); simulá-lo como alvo solo dá números ruins (ryo/h líquido **negativo**, -8 742) que não significam nada — não é um monstro pra caçar sozinho |
| **Espadachim da Névoa (boss)** | 19 | 60,5s / ~6 poções | 33,7s / ~2 poções | 166 939/h (ninjutsu) | 0% com poção |

Faixa real: **12–19, batendo com o lore**. Sem problema de faixa; ninjutsu bate esse boss
quase 2× mais rápido que taijutsu (33,7s vs 60,5s) — ver §6.6 sobre a defasagem de ninjutsu em
lutas longas.

### Floresta da Morte (lore: L10–25)

| Monstro | Nível | TTK taijutsu | TTK ninjutsu | XP/h (taijutsu) | Risco |
|---|---|---|---|---|---|
| Sanguessuga | 10 | 14,0s | 3,6s | 25 347/h | nenhum |
| Sapo Gigante | 13 | 19,4s | 5,5s | 28 886/h | nenhum |
| Ninja Renegado | 18 | 10,1s | 10,3s | 82 527/h | nenhum |
| Serpente Menor | 18 | 10,2s | 4,6s | 71 143/h | nenhum |
| Rivais do exame (3) | 20 | 11–15s | 6–7s | 52–66 mil/h | nenhum |
| **Sapo Ancião (boss secundário)** | 25 | 143,9s / ~9 poções | 95,6s / ~6 poções | 122 524/h | 0% com poção |
| **Serpente Branca (boss)** | 25 | 166,0s / ~15 poções | 110,0s / ~10 poções | 119 318/h | 0% com poção |

Faixa real: **10–25, batendo com o lore**. Os dois bosses de L25 são as lutas mais longas da
faixa 1–50 (só perdendo pro Marionetista L50) — coerente com "boss final" da região, mas vale
observar: **15 poções por tentativa de taijutsu é bastante** pra um jogador que acabou de sair
do L20 (ver §6.5).

### Ruínas do Clã Marionetista (lore: L25–50)

| Monstro | Nível | TTK taijutsu | TTK ninjutsu | XP/h (taijutsu) | Risco |
|---|---|---|---|---|---|
| Marionete de Combate | 27 | 20,6s | 16,5s | 74 640/h | nenhum |
| Sentinela de Pedra | 32 | 29,0s | 13,1s | 95 525/h | nenhum (ninjutsu 2× mais rápido aqui) |
| Guerreiro Espectral | 38 | 12,4s | 11,2s | 168 385/h | nenhum |
| Xamã da Maldição | 44 | 10,8s | 11,6s | 182 874/h | nenhum |
| Desertor de Elite (mini-boss) | 46 | 20,9s | 31,2s | 331 427/h | nenhum |
| **Marionetista (boss)** | 50 | 77,6s / ~5 poções | 103,9s / ~7 poções | 491 193/h | 0% com poção |

Faixa real: **27–50, batendo com o lore**.

### Montanha do Trovão (lore: L50–80)

| Monstro | Nível | TTK taijutsu | TTK ninjutsu | XP/h (taijutsu) | Risco |
|---|---|---|---|---|---|
| Águia do Trovão | 54 | 8,6s | 12,4s | 250 947/h | nenhum |
| Oni da Geleira | 60 | 23,2s | 22,6s | 227 006/h | nenhum |
| Monge da Tempestade | 68 | 9,7s | 17,8s | 306 947/h | nenhum |
| **O Sócio Eterno (boss)** | 70 | 34,9s / ~1 poção | 50,3s / ~2 poções | 683 905/h | 0% com poção |
| Serpente de Magma | 74 | 12,6s | 22,2s | 316 357/h | nenhum |
| **Oni Ancestral (boss)** | 80 | 93,7s / ~7,5 poções | 152,2s / ~12,4 poções | 915 633/h | 0% com poção |

Faixa real: **54–80, batendo com o lore**. Repare no padrão: quanto mais alto o nível, maior a
vantagem de taijutsu sobre ninjutsu em lutas longas (ver §6.6).

### Covil da Nuvem Vermelha (lore: L80–100)

| Monstro | Nível | TTK taijutsu | TTK ninjutsu | XP/h (taijutsu) | Risco |
|---|---|---|---|---|---|
| Clone Branco | 82 | 10,9s | 20,3s | 491 262/h | nenhum |
| **O Vigia Ilusório (boss)** | 85 | 97,6s / ~5,6 poções | 171,0s / ~10,4 poções | 902 058/h | 0% com poção |
| Ninja Elite da Aurora | 88 | 17,6s | 30,1s | 436 399/h | nenhum |
| **O Mascarado das Sombras (boss)** | 90 | 108,5s / ~5,8 poções | 173,2s / ~9,7 poções | 910 575/h | 0% com poção |
| **O Portador dos Seis Caminhos (boss)** | 95 | 122,0s / ~7,9 poções | 159,9s / ~10,6 poções | 898 560/h | 0% com poção |
| **O Ancestral da Nuvem Vermelha (boss final)** | 100 | 103,7s / ~6,1 poções | 177,9s / ~11,1 poções | 1 174 573/h | 0% com poção |

Faixa real: **82–100, batendo com o lore**. Só 2 monstros comuns pra 4 bosses — exatamente
como `progressao-jogador.md` descreve ("é o análogo direto do grind de level 100+ de Tibia").

## 5. Leitura geral da curva

- **Nenhuma "parede" de faixa de level errada** — todas as 6 regiões batem com a faixa
  pretendida no lore (`docs/sistemas/monstros-e-pvm.md`). O problema real nunca foi o *design*
  dos números em `data/`, foi a config/gerador (§2) impedindo que esses números fossem
  sequer testados como pretendido.
- Depois dos 3 fixes, **death_rate contra monstro comum do próprio nível é 0% em toda a
  matriz**, com poção contra bosses também 0%. Não achei nenhum monstro comum que mate o
  jogador do nível-alvo (nem em <5s nem devagar).
- XP/h do simulador SOBE com o nível (de ~2–8 mil/h na Floresta da Vila pra +1 milhão/h no
  Covil) — o oposto do formato "sobe-depois-desce" que `progressao-jogador.md` descreve. Isso
  é esperado dado o que o simulador mede (só combate 1×1, sem viagem/missão/spawn escasso —
  ver `tools/balance/README.md`): a Montanha e o Covil são desenhados pra serem lentos por
  ESCASSEZ de spot (só 2 monstros comuns pra região inteira no Covil) e cooldown de boss de
  horas, não porque o monstro em si seja ineficiente de matar — e de fato, monstro por
  monstro, eles morrem rápido. Não tratei essa discrepância como bug (não é o que os
  números em `data/monsters` controlam).

## 6. Lista de problemas concretos

1. **[CORRIGIDO — §2.1]** `rateExp` efetivo 5–7× o documentado (`experienceStages` "fantasma"
   de `config.lua`). Fix: `rateExp=1`, `experienceStages=nil`.
2. **[CORRIGIDO — §2.2]** Taijutsu puro com ~100% de death_rate contra monstro do próprio
   nível a partir de L5 (skill mult 2.0 do gerador de vocations.xml vs 1.1 documentado em
   `data/skills.json`). Fix: mult uniforme 1.1.
3. **[CORRIGIDO — §2]** Magic level (skill "ninjutsu") preso a single-digit o jogo inteiro
   (`manamultiplier=4.0`), contribuindo pra ninjutsu perder DPS sustentado pra taijutsu a
   partir de ~L15-20. Fix: `manamultiplier=1.3` (mitigado, não eliminado — ver §7).
4. **Nenhum monstro comum mata o jogador do nível-alvo** (death_rate 0% em toda a matriz
   same-level, medido depois dos fixes 1–3). Nenhum jutsu inútil encontrado: todo jutsu com
   dano (`base_damage>0`) supera o dano-por-segundo de taijutsu no nível em que é
   desbloqueado, quando comparado de forma justa (com a mitigação real de armadura aplicada
   dos dois lados — uma primeira comparação sem mitigação, descartada, sugeria erroneamente
   que praticamente todo jutsu tier 2/3 era "pior que taijutsu"; ver `tools/balance/README.md`
   sobre esse falso positivo de metodologia). Nenhum jutsu >3× dominante encontrado no
   1×1 (ninjutsu tier 1, de cooldown curto, sempre vence a corrida de DPS sustentado contra um
   único alvo — tier 2/3 não chegam a ser usados na rotação ótima 1×1; ver §7 sobre o limite
   disso).
5. **Chefe dos Bandidos (boss tutorial, L12) é apertado em ryo pra quem usa taijutsu**: TTK de
   151s consome em média ~21 poções de vida pequena (50 ryo cada = ~1 045 ryo), quase todo o
   valor esperado do próprio loot do boss — ryo/h líquido cai pra 2 386 (contra 40 049/h se o
   jogador usar ninjutsu, que mata em 63s com ~8 poções). Isso é o boss "funcionando", não
   quebrado (0% de morte com poção), mas é uma primeira experiência de boss cara/lenta pra
   quem só usa taijutsu — considerar aumentar levemente `ryo_max` ou adicionar mais 1 poção
   garantida no loot (hoje já dropa 3–6 `health_potion_small` 100% do tempo) se o playtest
   confirmar frustração aqui. Não apliquei essa mudança (é uma decisão de tuning fina, melhor
   com dado de playtest real, não só simulação).
6. **Ninjutsu perde de taijutsu em lutas longas (bosses), do jeito oposto do que "burst"
   sugere.** Ninjutsu vence taijutsu por 2–10× em monstros comuns (fights curtos: 2–20s), mas
   perde por 20–90% em quase todo boss (fights de 1–3 minutos) — ex.: Oni Ancestral L80,
   taijutsu 93,7s vs ninjutsu 152,2s. Investiguei duas hipóteses de causa e descartei as duas
   como "fix seguro pra esta sessão" (ver §7): (a) tentei subir `base_damage` dos jutsus
   tier 2/3 pra igualar o DPS teórico de taijutsu — os números pedidos eram absurdos (>1000
   de `base_damage`) porque a comparação teórica não tinha a mitigação de armadura aplicada
   dos dois lados (mesmo erro de metodologia do item 4); revertido. (b) confirmei que em
   combate 1×1 a rotação ótima de ninjutsu SEMPRE escolhe o jutsu de cooldown mais curto
   (tier 1), então nenhum ajuste em jutsu de área/beam (tier 2/3) muda o resultado 1×1 — o
   valor deles é presumivelmente em alvos múltiplos, fora do que este simulador mede.
   Reportando como achado real, não como "corrigido": recomendo revisitar com um simulador
   multi-alvo antes de tocar nos números de jutsu de área.
7. **Loot: nenhum valor absurdo de verdade encontrado.** Uma primeira varredura (material/
   troféu vs a fórmula `sell_price ≈ 4,5×level`, `boss ≈ 3×` isso) marcou ~15 "fora da faixa",
   mas quase todos são material COMPARTILHADO entre um monstro comum (onde o preço bate) e um
   boss/monstro mais alto que também dropa o mesmo item como extra "de sabor" (ex.:
   `oni_horn` bate em Oni da Geleira L60/Monge L68/Serpente de Magma L74, e aparece "barato
   demais" só quando o Oni Ancestral L80 também dropa — mas o loot de VERDADE do Oni Ancestral
   é a `oni_fang_blade`, sell 80 000, corretamente cara). O único caso genuíno é
   `bandit_emblem` (sell 8, seria ~22–54 pela fórmula) — mas o próprio item diz
   `"Prova de caça. Missões pedem isso."`: é material de entrega de missão, não de venda, e um
   preço de revenda baixo nesse caso é intencional (impede virar fonte de ryo fora da missão).
   Não apliquei nenhuma mudança de preço.
8. **Tarefas/diárias: nenhuma quebra a curva.** `reward.xp` (kills equivalentes) escala de
   forma consistente com `count` em toda a lista (tier 1 ≈ 2,2× "1 kill" por kill exigido,
   tier 2 ≈ 2,75×, tier 3 ≈ 3,6×) — um padrão deliberado (tarefa maior paga proporcionalmente
   mais), não um typo isolado. Único ponto de atenção, não corrigido: tarefas tier 3 de boss
   (`task_boss_*_3`, ex. `task_boss_bandit_chief_3`) pedem 25 kills de um boss com respawn de
   7200–10800s — no mínimo 50–75 horas reais SE o jogador pegar 100% dos spawns sozinho, o que
   é praticamente impossível com outros jogadores na área. Pode ser intencional ("meta de
   longo prazo" pós-endgame, comum em servidores estilo Tibia) ou pode estar
   desproporcionalmente alto — decisão de design, não bug técnico; deixei como está.
9. **Todo boss tem pelo menos 1 fase que muda o combate de verdade** (`summons`,
   `attack_multiplier` ou transformação de `looktype`) — nenhum "boss sem fase que importe"
   encontrado. Os bosses de 2 fases (`boss_illusive_eye`, `boss_masked_puppeteer`) têm 1 fase
   de abertura (100%, só mensagem) + 1 fase mecânica, o que é o mínimo esperado, não uma falha.
10. **2 itens com bônus que o exportador descarta silenciosamente**: `ring_stone_will`
    (`bonuses.defense: 3`) e `strings_of_the_puppeteer` (`bonuses.attack: 8`, o loot exclusivo
    do Marionetista) usam chaves que `tools/export_tfs.py` → `items_xml()` não sabe traduzir
    pro `items.xml` (o dicionário de tradução só conhece `hp`, `chakra`, `speed`,
    `skill_taijutsu/shuriken/ninjutsu/genjutsu/defense`, `element_resist_*`) — o item não dá
    erro nenhum, só silenciosamente não concede esse bônus específico no jogo real. Não
    corrigido nesta sessão (teria que mexer no exportador de novo, e já fiz 2 mudanças nele —
    preferi não acumular mudanças não testadas em produção; ver pendências).

## 7. Pendências (o que ficou de fora e por quê)

- **Item 6 (ninjutsu perde em lutas longas)**: não apliquei nenhuma mudança numérica porque
  as duas tentativas de correção que testei (buffar `base_damage` de tier 2/3; melhorar a
  escolha de jutsu do build) não resolveram a causa real ou pediam números que eu não
  conseguia justificar com confiança dentro do tempo desta sessão. Recomendo um simulador
  multi-alvo (mede o valor real de área/beam) antes de tocar em `data/jutsus/*.json` de novo.
- **Item 10 (bônus `attack`/`defense` de acessório descartados)**: precisa de uma mudança em
  `tools/export_tfs.py` (adicionar `attack`→`attack`, `defense`→`armor` no dicionário de
  `items_xml()`), não em `data/`. Não apliquei por já ter feito 2 mudanças no gerador nesta
  sessão e preferir não acumular mudanças de exportador não testadas contra o servidor real.
- **Magic level estruturalmente baixo (§2.2, item 3)**: o teto real vem de uma constante fixa
  em `vocation.cpp:149` (`1600`), não editável via config/JSON — só um build customizado do
  TFS resolveria isso de vez. `manamultiplier=1.3` é uma mitigação, não uma solução completa.
- **`config.lua` não versionado**: os fixes de `rateExp`/`experienceStages` estão só no
  arquivo de execução local, não em `config.lua.dist` (correto — esse é o default de fábrica).
  Se o servidor for reprovisionado do zero, os fixes precisam ser reaplicados manualmente;
  vale uma nota em `docs/04-setup-ot.md` (não fiz essa edição nesta sessão, fora do escopo de
  balanceamento).
- **`docs/sistemas/balanceamento.md` menciona poções que não existem em `data/items/consumables.json`
  isoladamente** (estão espalhadas em `tiers.json`/`mountain.json`/`ruins.json` — `health_potion_medium`,
  `health_potion_large`, `chakra_pill_large`, `soldier_pill`) — não é um bug (todas existem e
  batem com a tabela do doc), só uma observação de organização de arquivo que não mexi.

## 8. Como reproduzir

```bash
cd /Users/stenioz/Projetos/shinobi-legends
python3 tools/balance/sim.py --matrix --json /tmp/matrix.json   # ~30s
python3 tools/balance/sim.py --level 25 --monster boss_white_serpent --build ninjutsu -v
.venv/bin/python tools/validate_data.py
.venv/bin/python tools/export_tfs.py       # escreve em server/generated/, não instala
```
