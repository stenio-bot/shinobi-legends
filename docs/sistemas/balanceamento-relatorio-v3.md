# Relatório de balanceamento PvM — rodada 3 (setembro/2026)

Continuação direta da rodada 2 (`docs/sistemas/balanceamento-relatorio-v2.md`), que fechou
admitindo o problema estrutural que esta rodada resolve: *"de L50 em diante o build ninjutsu
'empata' só porque degenera em taijutsu puro"* (pendência #4 do relatório v2 e do
`tools/balance/README.md`). Ver `tools/balance/README.md` (seção "o que é fórmula real e o que
é premissa") antes de questionar qualquer número aqui.

Comandos usados (mantidos <120s):

```bash
python3 tools/balance/sim.py --matrix --json /tmp/matrix.json          # 1938 sims, ~60s
python3 tools/balance/sim.py --group-matrix --json /tmp/group.json     # 36 grupo + 18 boss, ~1.3s
python3 tools/balance/sim.py --level 60 --monster boss_ancestral_oni --build ninjutsu --no-fallback  # diagnóstico
python3 tools/validate_data.py
python3 tools/export_tfs.py     # gera server/generated/, NÃO instalado (agente de playtest jogando)
```

## 0. Arquivos tocados

`tools/balance/sim.py` (`--no-fallback`, `jutsu_dps_pure_mean`, fix do teto `ml>60`,
`MANA_MULT`), `tools/export_tfs.py` (`manamultiplier`), `data/element_sets.json` (kit de
raiton), `data/jutsus/{katon,fuuton,raiton,doton,suiton,neutral,personal}.json` (escalas,
chakra, forma de 2 jutsus), `tools/balance/README.md`, `docs/sistemas/balanceamento.md`, este
relatório. **Não editei** `data/monsters`, `data/maps`, `tools/map`, nem rodei
`install_generated.sh` — como instruído.

## 1. Diagnóstico: a curva pura de ninjutsu (`--no-fallback`)

A missão pediu pra medir ninjutsu SEM permitir que a rotação desista do jutsu no meio da conta
(o que a rodada 2 fazia sempre que o jutsu não batia o DPS de arma estimado — daí o "empate" em
L50+ do relatório v2 §2). Adicionei `--no-fallback` a `tools/balance/sim.py`
(`pick_ninjutsu_jutsu(..., no_fallback=True)`): a build ninjutsu sempre usa o melhor jutsu do
kit elemental quando há chakra, mesmo que ele faça menos dano/s que a arma — só cai pra taijutsu
quando o chakra **de verdade** acaba (não por escolha racional). Rodando essa curva **antes de
qualquer mudança nesta sessão** (`manamultiplier=1.3`, herdado das rodadas 1/2), monstro comum
do nível + boss da região, em todos os pares de `GROUP_SCENARIOS` (rodada 2 §1):

| Nível | Monstro | Tipo | TTK taijutsu | TTK ninjutsu (puro) | Diferença |
|---|---|---|---|---|---|
| 2 | wolf | comum | 13,5s | 10,1s | **-25,2%** (forte demais) |
| 5 | bandit | comum | 24,4s | 18,9s | -22,6% |
| 12 | boss_bandit_chief | **boss** | 150,9s | 145,7s | -3,5% (dentro da meta) |
| 12 | mercenary_bridge | comum | 15,5s | 24,9s | +61,1% |
| 18 | lesser_serpent | comum | 24,6s | 11,2s | -54,4% |
| 19 | boss_mist_swordsman | **boss** | 158,6s | 137,3s | -13,4% (dentro, no limite) |
| 25 | boss_white_serpent | **boss** | 166,0s | 171,0s | +3,0% (dentro) |
| 27 | ruin_puppet | comum | 19,4s | 36,2s | +87,0% |
| 44 | curse_shaman | comum | 10,8s | 22,4s | **+107,8%** |
| **50** | **boss_puppeteer** | **boss** | 77,6s | 136,2s | **+75,5%** |
| 54 | thunder_eagle | comum | 8,4s | 27,7s | +228,8% |
| 68 | storm_monk | comum | 16,4s | 40,2s | +145,3% |
| **80** | **boss_ancestral_oni** | **boss** | 93,7s | 194,2s | **+107,2%** |
| 82 | white_clone | comum | 11,0s | 52,7s | +379,4% |
| 88 | elite_cloud_guard | comum | 18,1s | 77,0s | +325,4% |
| **100** | **boss_crimson_ancestor** | **boss** | 103,7s | 225,2s | **+117,3%** |

**A confirmação exata do problema**: nos 3 bosses de L50+ (metade dos 6 testados), ninjutsu puro
é 75-117% MAIS LENTO que taijutsu — cai abaixo da meta de -15%/+10% por uma margem enorme.
Comparando com o relatório v2 (que usava fallback racional e via "empate" nesses mesmos 3
bosses): o build simplesmente parava de tentar usar jutsu. É a mesma curva por baixo, só que a
rodada 2 mediu "o jogador desistiu" e chamou de "0% de diferença" — tecnicamente dentro da meta,
mas escondendo que o jutsu real, se forçado, perde de lavada. Isso bate com a missão: *"o
jogador precisa SENTIR que o jutsu evolui do L1 ao L100"* — um jutsu que só existe pra ser
abandonado não evolui nada.

**Causa raiz** (confirmada com `weapons.cpp:135`/`vocation.cpp:149`, ver §2): o magic level
(skill "ninjutsu") cresce de ~16 (L15) a ~34 (L100) com `manamultiplier=1.3` — menos de 2,2× em
85 níveis — enquanto o dano de arma (`weapon_max_damage`, depende de `skill/4+1 × attack` da
arma de tier) cresce ~40× no mesmo intervalo. `maglevel*skill_scale` nunca acompanha; só
`level*level_scale` cresceria, mas os `level_scale` herdados das rodadas 1/2 foram calibrados
pra L12-25 (onde jutsu já dominava demais, ver relatório v2 §2), não pra L50+.

## 2. Correção estrutural: (a) `manamultiplier` + recalibração de escalas

Segui a ordem de preferência da missão.

### (a) `manamultiplier`: 1.3 → 1.1

`tools/export_tfs.py` (gerador de `XML/vocations.xml`) e `tools/balance/sim.py` (`MANA_MULT`).
`Vocation::getReqMana(ML) = 1600 * manamultiplier^(ML-1)` (`server/tfs/src/vocation.cpp:149`,
constante `1600` fixa no C++, confirmada — não editável fora de recompilar o servidor). Baixar
o multiplicador pra 1.1 (igual `data/skills.json`: `"tries_formula": "50 * 1.1^(skill - 10)"`,
usado por taijutsu/shuriken/defesa desde a rodada 1) muda a curva de magic level real:

| Nível | maglevel (mult=1.3, rodadas 1-2) | maglevel (mult=1.1, rodada 3) | skill taijutsu (mult=1.1, referência) |
|---|---|---|---|
| 5 | 12 | 23 | 40 |
| 15 | 16 | 35 | 52 |
| 30 | 21 | 47 | 64 |
| 50 | 26 | 60 | 77 |
| 70 | 30 | 71 | 88 |
| 100 | 34 | 83 | 101 |

Com mult=1.1, o magic level real passa a crescer na **mesma ordem de grandeza** do taijutsu
(83 vs 101 no L100 — antes 34 vs 101, uma diferença de 3×) — pela primeira vez `skill_scale`
volta a ser um lever de verdade, não um decimal residual.

### Bug encontrado durante a validação: teto `ml > 60`

`_maglevel_from_mana` (`tools/balance/sim.py`) tinha uma trava de iteração `ml > 60` que nunca
binda com `mult=1.3` (maglevel real ficava em ~34) — mas com `mult=1.1` o valor real quer chegar
a ~83 no L100, e o simulador estava **truncando silenciosamente** em 60/61. Corrigido pra
`ml > 300` (mesmo espírito do `skill > 200` de `_skill_from_tries`: uma trava de segurança que
nunca deve bindar de verdade). Sem esse fix, toda a calibração de tier 2/3 abaixo (§3) teria sido
feita contra um magic level artificialmente baixo em L60+ — pego e corrigido ANTES de fechar os
números, não depois.

### Recalibração de `level_scale`/`skill_scale` (jutsus tier 2/3, `data/jutsus/*.json`)

Baixar só o `manamultiplier` não bastou sozinho (dobrar o magic level ainda deixa
`maglevel*skill_scale` pequeno perto do salto de dano de arma) — segui a ordem (b) da missão:
o `level_scale` de tier 2/3 (não só `skill_scale`) precisou subir, porque é o único termo
determinístico (não depende de premissa de "jogador médio" nenhuma) capaz de acompanhar o dano
de arma, que também é puramente função de nível/skill/tier de item.

Processo de calibração (busca em grade, script descartável — não faz parte do repo — comparando
`sim.simulate()`/`simulate_group()` reais, não só a fórmula analítica, pros 6 bosses +
`GROUP_SCENARIOS`): um multiplicador ÚNICO por tier (como a rodada 2 usou: `tier1_mult`,
`tier23_mult`) **não fecha mais** com o novo `manamultiplier` — a resposta de cada elemento/nível
ao mesmo multiplicador não é uniforme (ex.: um multiplicador que acerta o boss L50 de katon
supera em +40% o boss L68 de fuuton, ou vice-versa). Precisei de multiplicadores **por família**:

| Família | Jutsus | `level_scale` | `skill_scale` | `chakra_cost` |
|---|---|---|---|---|
| Tier 1 ofensivo | `katon_goukakyuu`, `fuuton_lamina_vento`, `raiton_hari`, `doton_bala_lama`, `suiton_mizudan` + os 2 que mudaram de forma (§4) | **inalterado** | inalterado | inalterado (2 mudaram, ver §4) |
| Tier 2 "normal" (elemento tem tier 3 atrás) | `katon_housenka`, `katon_anel_chamas`, `fuuton_rajada_cortante`, `doton_estacas_terra` | ×2,07–3,1 | ×1,0 | ×3,5 |
| Tier 2 "teto do elemento" (sem tier 3 no kit) | `raiton_lanca_relampago` (mantém-se relevante em L18-25, antes de `punho_trovao`), `suiton_suiryuudan` (único lever de suiton) | ×1,0 / ×7,05 | ×1,5 / ×1,45 | inalterado / ×3,5 |
| Tier 3 | `katon_karyuu_endan`, `doton_colapso_terreno`, `fuuton_tornado_cortante`, `raiton_punho_trovao` (novo no kit, §2.1) | ×11,4–13,6 (antes do ajuste de paridade elemental, §5) | ×0,2–0,37 | ×2,4–3,5 |

**Por que tier 1 ficou intocado**: testei subir o `level_scale` de tier 1 pra fechar o requisito
de burst (item 2 da missão, ver §6) e isso piorou boss L12/L19 (que ainda usam tier 1 puro,
antes de tier 2 desbloquear) — subir tier 1 pra resolver burst empurra 1×1 de baixo nível pra
fora da meta pelo lado "forte demais". Documentado como tensão real, não ignorada (§10).

**Por que `chakra_cost` subiu junto**: sem isso, o `level_scale` maior deixava tier 2/3 batendo
dano de boss **de graça**, e em grupo (onde `hits`×`dano` multiplica) isso virava um "apaga tudo
num cast só" mesmo contra pulls pequenos — ver §6/§10. Subir o custo ~2,4-3,5× faz o chakra
finito (pool `50+level*10`) esgotar mais cedo, empurrando a luta de volta pra taijutsu depois do
burst inicial — o próprio mecanismo que sustenta a paridade em lutas longas (boss) sem
inviabilizar completamente o burst (chega a 3-5 casts de tier 3 num boss L60-100, ver §8).

### Resultado: boss 1×1 puro (`--no-fallback`), depois do fix

| Nível | Boss | TTK taijutsu | TTK ninjutsu (puro) | Diferença | Dentro de -15%/+10%? |
|---|---|---|---|---|---|
| 12 | Chefe dos Bandidos | 150,9s | 129,2s | -14,4% | ✅ |
| 19 | Espadachim da Névoa | 158,6s | 117,7s | -25,8% | ❌ (platô de tier de arma L15-20, pendência herdada da rodada 2, ver §10) |
| 25 | Serpente Branca | 166,0s | 168,0s | +1,2% | ✅ |
| 50 | Marionetista | 77,6s | 80,3s | +3,0% | ✅ |
| 80 | Oni Ancestral | 93,7s | 100,4s | +7,1% | ✅ |
| 100 | Ancestral da Nuvem Vermelha | 103,7s | 111,5s | +7,6% | ✅ |

**5 dos 6 bosses dentro da meta** — os 3 que antes degeneravam (L50/80/100, de +75%/+107%/+117%
pra +3,0%/+7,1%/+7,6%) agora competem de verdade. O único fora (L19) é uma pendência **herdada**
da rodada 2 (platô de tier de arma em `data/items/*.json`, fora do escopo desta sessão —
`jutsus/element_sets/characters` só), não um efeito colateral desta rodada.

## 3. Raiton ganhou um tier 3 de verdade no kit

Achado paralelo durante a calibração: `data/element_sets.json` tinha
`raiton_armadura_eletrica` (self, `base_damage=0`, nunca é candidato de dano em
`pick_ninjutsu_jutsu`) na 4ª vaga do kit de raiton, em vez de `raiton_punho_trovao` (tier 3, req
30) — que já existe em `data/jutsus/raiton.json` e já tem pergaminho mapeado
(`scroll_raiton_punho_trovao` em `data/tfs_mapping.json`), só nunca foi posto no "kit livre" do
elemento. `docs/sistemas/combate-e-jutsus.md` já documentava isso como decisão deliberada da
rodada de criação de conteúdo ("candidato a loot/pergaminho de bônus no futuro") — mas isso
deixava **raiton sem nenhum tier 3 no kit automático**, igual suiton, só que sem a compensação
extra que dei a `suiton_suiryuudan` (§2). Troquei a 4ª vaga: `raiton_armadura_eletrica` →
`raiton_punho_trovao`. `armadura_eletrica` continua um jutsu válido (`data/jutsus/raiton.json`
inalterado), só fica fora do kit "livre por elemento" — mesmo status dos outros sobressalentes
já documentados (`katon_sopro_brasas` também fica de fora do kit de katon, por exemplo).

Esse swap sozinho resolveu boa parte da degeneração em monstros de elemento doton (que usam o
kit de raiton por vantagem elemental) em L50+: `white_clone` (L82) foi de -35% (ninjutsu forte
demais, raiton preso em tier 2) pra dentro de ±10% num teste intermediário desta sessão (o valor
final ficou deslocado de novo pelo ajuste de paridade elemental do §5, mas a causa raiz —
"elemento sem tier 3" — está resolvida).

**Suiton continua sem tier 3 no kit** (`suiton_vortice_devorador` também fica de fora, por
design documentado) — recebeu compensação via `suiton_suiryuudan` (seu único tier 2) em vez de
ganhar um novo membro de kit, porque trocar sua 4ª vaga (`suiton_prisao_agua`, controle) tiraria
o único jutsu de controle do elemento, e trocar a 2ª vaga (`suiton_nevoa_cortante`) quebraria a
categoria "área/cone" documentada em `combate-e-jutsus.md` (projétil→área→beam→utilitário). Ficou
como pendência de design pra uma rodada futura decidir se vale mudar a estrutura do kit de
suiton (não só os números) — ver §10.

## 4. Papel dos 3 jutsus "nunca escolhidos" da rodada 2

- **`fuuton_tornado_cortante` (tier 3) — resolvido por NÚMERO.** Recebeu o mesmo tratamento de
  tier 3 do §2 (`level_scale` ×0,8 depois do ajuste de paridade do §5, partindo de ×13,5) e agora
  é o pick de verdade em monstros/bosses de elemento raiton em L54-100 (`thunder_eagle`,
  `boss_ancestral_oni`, `elite_cloud_guard`, `boss_crimson_ancestor` — confirmado via
  `pick_ninjutsu_jutsu` real, não estimativa).
- **`raiton_corrente_estatica` e `suiton_nevoa_cortante` (tier 1 de área) — resolvidos por
  FORMA.** Mudei cooldown, alcance de área e efeito (não o `level_scale`/`skill_scale`, que
  ficou igual ao resto do tier 1 — não competem em DPS puro por design, mesmo raciocínio que a
  rodada 2 já aplicou a `fuuton_redemoinho_prisao`/`suiton_prisao_agua`):

  | Jutsu | Antes (rodada 2) | Depois (rodada 3) |
  |---|---|---|
  | `raiton_corrente_estatica` | `cross_r1`, cd 2,5s, paralyze 20%/1,0s | `cross_r2`, cd **1,3s**, paralyze **50%/2,0s** |
  | `suiton_nevoa_cortante` | `cone_2`, cd 3,0s, slow 35%/3s/30% | `cone_3`, cd **1,6s**, slow **60%/5s/45%** |

  Viram a opção de **controle de área rápido** do kit tier 1 (cooldown quase metade do projétil
  irmão, chance/duração de efeito bem maiores) em vez de tentar vencer uma corrida de DPS que a
  matemática do jogo não permite (área e projétil do mesmo tier têm o mesmo `level_scale`/
  `skill_scale` desde a rodada 1 — só cooldown/forma diferenciam). Confirmado com
  `--group-matrix`: `raiton_corrente_estatica` já aparece escolhido em pelo menos 1 cenário real
  depois da mudança. `suiton_nevoa_cortante` não tem, nos `GROUP_SCENARIOS` atuais, nenhum
  monstro comum de elemento katon no nível 6-24 (a janela em que ele compete antes de
  `suiryuudan` desbloquear) — mudança de forma bem fundamentada, mas não confirmada pelo
  simulador nesta sessão por falta de cenário de teste, não por falha do jutsu (ver §10).

## 5. Paridade elemental (meta ±10%)

Depois do §2/§3, os 5 elementos ficaram bem desiguais entre si (cada tier 3/"teto do elemento"
foi calibrado contra um boss de elemento diferente): raiton/fuuton fortes demais, suiton fraco
demais.

| Elemento | Antes do ajuste (desvio, L70) | Depois do ajuste (desvio, L70) |
|---|---|---|
| Katon | -12,6% | -0,2% |
| Fuuton | +24,6% | -0,2% |
| Raiton | +29,7% | 0,0% |
| Doton | -10,9% | -0,1% |
| Suiton | -30,8% | +0,4% |

Corrigido com um multiplicador extra no jutsu "campeão" de cada kit (o que efetivamente carrega
o elemento em L50+): `katon_karyuu_endan` ×1,14, `fuuton_tornado_cortante` ×0,80,
`raiton_punho_trovao` ×0,77, `doton_colapso_terreno` ×1,12, `suiton_suiryuudan` ×1,45 (aplicado
sobre os valores já recalibrados do §2, não sobre o baseline original). Resultado: os 5
elementos ficam dentro de **±2,4%** entre si de L50 a L100 (testado em L50/70/80/100) — bem mais
apertado que a meta de ±10% da missão. Os valores absolutos finais de `base_damage`/
`level_scale`/`skill_scale` desses 5 jutsus já refletem esse ajuste (não há um "multiplicador
pendente" escondido — `data/jutsus/*.json` é a fonte da verdade).

## 6. Grupos de 3+ (meta: ninjutsu +30–60%) — melhora parcial, tensão real documentada

| Monstro | Nível | N | Antes (rodada 2) | Depois (rodada 3) | Dentro de +30-60%? |
|---|---|---|---|---|---|
| `wolf` | 2 | 3 | +6,9% | +11,5% | ❌ (abaixo, mesma direção que a rodada 2 já reportava) |
| `ruin_puppet` | 27 | 3 | +56,9% | +24,6% | ❌ (perto, mas abaixo — o rebalanceamento de tier 2/3 "normal" ficou mais conservador que a rodada 2 pra não estourar boss L50, ver §2) |
| `thunder_eagle` | 54 | 3 | +1,0% | **+442,5%** | ❌ (estourou pro outro lado) |

`thunder_eagle` é o achado mais importante desta seção: o MESMO `level_scale` de
`fuuton_tornado_cortante` que fecha a paridade 1×1 contra um **boss** (HP na casa de milhares)
faz um cast só **quase eliminar um pull de 3 `thunder_eagle`** (HP total 3.480) — a luta em grupo
dura 1,9s contra 8,4s de taijutsu. Testei duas correções antes de desistir de resolver só com
número: (1) aumentar `chakra_cost` — funciona bem pra `ruin_puppet` (que precisa de vários casts
pra fechar a luta, então o chakra realmente limita) mas não move `thunder_eagle` nem um pouco
(`oom_s_mean=None`: o chakra nunca chega a faltar porque **um único cast já mata o grupo antes de
precisar de um segundo**); (2) reduzir cooldown E dano proporcionalmente (mantém o DPS sustentado
de boss igual, já que `dano/cooldown` não muda) — melhora `thunder_eagle` de +508% pra ~+250-350%
mas não chega perto de +60%, pelo mesmo motivo: mesmo um cast "menor" ainda excede o HP do pull
inteiro. **Isso é uma tensão estrutural, não um número errado**: o mesmo valor de dano precisa
simultaneamente (a) bater o DPS de um alvo com milhares de HP numa luta de minutos e (b) não
apagar um pull de HP baixo numa luta de segundos — os dois objetivos da missão (item 1: boss 1×1;
item 2: grupo +30-60%) empurram o mesmo número em direções opostas quando o HP do grupo é baixo
o bastante. Ver §10 pras opções de correção fora do escopo desta sessão.

Híbrido continua "perto do melhor" (6-19% atrás do melhor build por boss, igual à rodada 2 —
não regrediu).

## 7. Chakra: economia, quantos jutsus até secar, pílulas

Regen passivo (`gainmanaticks=5 gainmanaamount=3` em `tools/export_tfs.py`, igual em toda vila,
**não escala com level**) = 0,6 chakra/s, contra um pool `50+level*10`. Com os custos do §2
(105-245 pra tier 2/3), a rotação seca bem antes dos 30s citados na missão, em praticamente todo
nível — mas isso é o mecanismo, não um bug (ver abaixo):

| Nível | Chakra máx. | Jutsu típico usado | Custo | Casts até secar | Tempo até secar | Regen completo do zero |
|---|---|---|---|---|---|---|
| 5 | 100 | `katon_goukakyuu` (t1) | 15 | 6 | 12s | 167s |
| 10 | 150 | `katon_goukakyuu` (t1) | 15 | 10 | 20s | 250s |
| 15 | 200 | `katon_housenka` (t2) | 105 | 1 | 4s | 333s |
| 30 | 350 | `katon_anel_chamas` (t2) | 147 | 2 | 12s | 583s |
| 60 | 650 | `katon_karyuu_endan` (t3) | 210 | 3 | 24s | 1083s |
| 100 | 1050 | `katon_karyuu_endan` (t3) | 210 | 5 | 40s | 1750s |

**Isso é intencional**: é o mecanismo que faz o `level_scale` grande do §2 (necessário pra bater
o dano de arma) não virar DPS sustentado de graça — um boss L100 dá conta de ~5 casts de tier 3
(40s de burst puro, ~38% de um TTK de ~105s) e passa o resto da luta em taijutsu, o que já é
exatamente o que o §2 mostrou dar ~+7,6% de diferença (dentro da meta). Regen natural do zero ao
cheio (167s a 1750s) é lento demais pra importar no meio de uma luta — é recuperação entre
lutas, não um lever de combate.

**Pílulas de chakra** (`data/items/consumables.json`, `data/items/ruins.json`) são o lever real
de combate: `chakra_pill_medium` (req 15, 150 CK), `chakra_pill_large` (req 30, 350 CK). Uma
Pílula Grande no meio de uma luta longa (L30+) dá **~1,7 cast extra de tier 3** (350/210 no
L60-100) — meaningful, mas não dobra a rotina sozinha. **Pendência**: `tools/balance/sim.py`
não simula o jogador bebendo pílula de chakra em combate (só `_HP_POTIONS`/HP) — a tabela acima
foi calculada analiticamente (mesmas fórmulas do simulador, aplicadas à mão), não pelo Monte
Carlo. Adicionar isso ao simulador (mesmo padrão de `_HP_POTIONS`/`use_potions`) é natural pra
uma rodada 4.

Não mexi em `gainmana`/`gainmanaamount` (regen) — toda a calibração de `chakra_cost` do §2
assumiu esse regen como está; subir o regen sem recalibrar tudo de novo desfaria a paridade 1×1
recém-alcançada (mais chakra disponível = mais casts de tier 3 por luta = ninjutsu forte demais
de novo em boss).

## 8. Burst: per-hit de tier 1 ≥ 1,3× o hit médio de arma (meta parcialmente atingida)

| Nível | Hit médio de arma | Hit médio de tier 1 (c/ vantagem elemental) | Razão |
|---|---|---|---|
| 1 | 5,0 | 13,8 | 2,75× ✅ |
| 5 | 15,5 | 25,9 | 1,67× ✅ |
| 10 | 34,5 | 32,0 | 0,93× ❌ |
| 15 | 38,0 | 37,3 | 0,98× ❌ (perto) |
| 20 | 76,5 | 42,1 | 0,55× ❌ |
| 50 | 285,5 | 69,8 | 0,24× ❌ |
| 100 | 681,5 | 111,0 | 0,16× ❌ |

**Meta não atingida em todos os níveis** — só L1-5 (e quase L15) batem 1,3×. Testei subir o
`level_scale` de tier 1 pra fechar essa meta em todos os níveis (§2 já explica por quê) e isso
piora boss L12/L19 (que ainda usam tier 1 puro) pro lado "forte demais" — uma tensão real entre
"burst sempre alto" e "paridade sustentada em 1×1 de baixo nível", quando tier 1 e o attack
interval do player têm o MESMO cooldown (2,0s, normalizado desde a rodada 2): se
`dano_tier1/cooldown ≈ dano_arma/attack_interval` (a meta de paridade sustentada), e
`cooldown == attack_interval`, então **necessariamente** `dano_tier1 ≈ dano_arma` por hit — as
duas metas da missão (paridade sustentada E burst 1,3×) são matematicamente incompatíveis quando
o cooldown do jutsu iguala o intervalo de ataque, a menos que o jogador tenha uma reserva de
chakra que NUNCA acabe (o que reintroduziria a "domina demais em L12-25" da rodada 2). Prioridade
foi manter a paridade sustentada em boss de baixo nível (mission item 1, primeiro na lista) —
documentado honestamente como meta não fechada (§10), não escondido atrás de um número que
pareceria bom só no L1-5.

## 9. Personagens: 9 jutsus pessoais, ±15%

O `manamultiplier` menor (§2) mexeu indiretamente no valor de 2 grupos de personagens que a
rodada 2 já tinha calibrado: jutsus pessoais com `skill=ninjutsu` ganharam dano de graça (magic
level maior), e a métrica-proxy de jutsu utilitário (`(chakra_cost/cooldown) × dano-médio-por-
chakra-do-pool-de-jutsus-de-dano`, mesma fórmula da rodada 2) mudou de baseline porque o pool de
jutsus de dano inteiro ficou mais forte (§2).

**Antes** (só com o `manamultiplier`/tier2-3 do §2 aplicados, sem correção de personagem):

| Personagem | Desvio | Causa |
|---|---|---|
| `kunoichi_armas` | **+22,5%** | `doku_kiri` (skill=ninjutsu) ganhou dano de graça com o magic level maior |
| `sabio_cerimonial` | **-21,5%** | proxy de utilitário subiu de baseline (jutsus únicos dele não acompanharam) |
| `genin_laranja` | **-18,7%** | mesmo motivo |

**Depois** (ajustei só o(s) jutsu não-compartilhado(s) de cada um, mesma disciplina da rodada 2 —
`kawarimi`/`punho_suave`/`fuuin_contencao`, compartilhados por 2+ personagens, ficaram intocados):

| Personagem | Desvio | Jutsu ajustado |
|---|---|---|
| `sabio_loiro` | -8,6% | (sem ajuste) |
| `genin_uchiha` | -5,5% | (sem ajuste) |
| `herdeira_hyuga` | -4,4% | (sem ajuste) |
| `genin_laranja` | -1,3% | `fuuton_rasteira_vento` ×1,6 |
| `sabio_cerimonial` | +1,1% | `selo_de_exorcismo`/`circulo_de_selos` ×1,4 |
| `ninja_verde` | +1,6% | (sem ajuste) |
| `kunoichi_armas` | +3,2% | `doku_kiri` (base_damage/level_scale ×0,55, skill_scale ×0,2) |
| `kunoichi_rosa` | +3,7% | (sem ajuste) |
| `ninja_abelha` | +10,2% | (sem ajuste) |

Todos os 9 dentro de ±15% (mais apertado que a rodada 2 conseguiu, na verdade — ±10,2% no pior
caso).

## 10. Pendências honestas

1. **Boss L19 fora da meta (-25,8%)** — platô de tier de arma em `data/items/*.json` L15-20,
   herdado da rodada 2, fora do escopo desta sessão (`jutsus/element_sets/characters` só).
2. **Tensão real entre paridade 1×1 de boss e paridade de grupo pra pulls de HP baixo**
   (`thunder_eagle`, §6): o mesmo número que fecha o boss apaga o grupo pequeno num cast só.
   Duas correções tentadas (subir `chakra_cost`, reduzir cooldown+dano proporcionalmente) não
   resolveram porque a luta acaba rápido demais pro chakra faltar OU pro HP do grupo sobreviver
   a um cast só. Opções fora do escopo desta sessão: (a) subir o HP dos monstros desse pull
   especificamente (`data/monsters`, não autorizado); (b) uma regra de dano decrescente contra
   grupos de HP total baixo (precisaria de mudança de engine/C++, não só dado — proposta, não
   aplicada); (c) reduzir a `area_capacity` efetiva de jutsus de altíssimo tier pra não escalar
   com N tão livremente. `wolf` (+11,5%) e `ruin_puppet` (+24,6%) seguem abaixo de +30%, mesma
   direção que a rodada 2 já reportava — não pioraram, mas também não fecharam a meta.
3. **`suiton_nevoa_cortante` mudou de forma mas não foi exercitada por nenhum cenário real**
   (nenhum monstro comum de elemento katon no nível 6-24 em `GROUP_SCENARIOS`) — mudança
   fundamentada (mesmo raciocínio de `raiton_corrente_estatica`, que FOI confirmada), mas
   pendente de validação quando houver cobertura de cenário.
4. **Burst de tier 1 (meta ≥1,3×) só bate em L1-5** (§8) — incompatibilidade matemática real com
   a meta de paridade sustentada quando `cooldown_tier1 == attack_interval`, documentada com a
   prova; resolver de verdade exigiria ou cooldown de tier 1 menor que o attack interval do
   player (mudança de identidade do jutsu — deixaria de ser "1 cast por troca de golpe") ou
   aceitar paridade sustentada pior em L10+ só para o tier 1. Não escolhi nenhuma das duas sem
   uma decisão de design explícita — reportando, não decidindo sozinho.
5. **`tools/balance/sim.py` não simula pílula de chakra em combate** (§7) — a checagem "seca em
   <30s" foi feita analiticamente; adicionar ao Monte Carlo (mesmo padrão de `_HP_POTIONS`) fica
   pra uma rodada 4.
6. **Regen de chakra não escala com level** (§7) — vira irrelevante em nível alto; não mexi
   porque a calibração de `chakra_cost` (§2) assumiu o regen atual — mudar os dois juntos sem
   orçamento pra recalibrar desfaria a paridade recém-alcançada.
7. **Suiton segue sem tier 3 no kit automático** (`suiton_vortice_devorador` fora, §3) — resolvi
   com compensação numérica no tier 2 (`suiryuudan`), não com uma mudança de estrutura do kit
   (trocar `suiton_prisao_agua` ou `suiton_nevoa_cortante` por ele quebraria a categoria
   projétil/área/beam/utilitário documentada em `combate-e-jutsus.md`) — decisão de design pra
   uma rodada futura, não numérica.
8. **Costa das Marés e Covil da Nuvem Vermelha continuam sem mapa físico** (herdado da rodada
   2) — `GROUP_SCENARIOS` usa N=2 placeholder pra essas regiões.

## 11. Como reproduzir

```bash
cd /Users/stenioz/Projetos/shinobi-legends
python3 tools/balance/sim.py --matrix --json /tmp/matrix.json          # ~60s
python3 tools/balance/sim.py --group-matrix --json /tmp/group.json     # ~1.3s
python3 tools/balance/sim.py --level 60 --monster boss_ancestral_oni --build ninjutsu --no-fallback  # diagnóstico pontual
python3 tools/validate_data.py
python3 tools/export_tfs.py       # escreve em server/generated/, não instala
```
