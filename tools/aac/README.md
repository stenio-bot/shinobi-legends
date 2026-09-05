# AAC do Shinobi Legends (`tools/aac/`)

Site local, minimo, para criar conta e personagem sem escrever SQL na mao
(estilo os "AAC" clássicos de servidor de Tibia). Serve em `http://127.0.0.1:8080/`
por padrão.

## Rodar

```bash
tools/aac.sh            # sobe em background (porta 8080)
tools/aac.sh status     # mostra se esta no ar
tools/aac.sh stop       # derruba
```

Ou em primeiro plano (Ctrl+C para parar), útil para ver os logs na hora:

```bash
.venv/bin/python3 tools/aac/aac.py
```

Precisa de:
- **MariaDB no ar** com o schema do TFS (`server/tfs/schema.sql`) já aplicado.
- **`pymysql`** no `.venv` do projeto: `.venv/bin/pip install pymysql` (já feito
  neste checkout; se o `.venv` for recriado, rode de novo).
- As credenciais do banco são lidas de `server/tfs/config.lua` (nunca hardcoded
  e nunca editado por este script) — se você mudar usuário/senha/porta do
  MySQL lá, o AAC acompanha sozinho.

Porta alternativa: `AAC_PORT=8090 tools/aac.sh`.

## Páginas

| Rota | Método | O que faz |
|---|---|---|
| `/` | GET | Home com instruções e links. |
| `/criar-conta` | GET/POST | Cria conta: nome (3-32 letras/números/`_`), senha (4-64), confirmação, e-mail opcional. |
| `/criar-personagem` | GET/POST | Escolhe vila (Folha/Névoa/Nuvem/Areia) → personagem inicial daquela vila (com preview do outfit) → nome do personagem (3-20 letras/espaços) + sexo + login/senha da conta dona do personagem. |
| `/conta` | GET/POST | Login (conta + senha) → lista os personagens dessa conta (nome, level, vila, sexo). |
| `/sprite/<looktype>.png` | GET | Preview PNG (frame parado) de um looktype de personagem inicial. Só serve os looktypes que aparecem em `data/characters.json` (whitelist) — não é um servidor de arquivos genérico. |

## De onde vêm os dados

Lido só para leitura, nunca escrito por este script:
- `data/villages.json` — nomes de exibição das vilas.
- `data/tfs_mapping.json` (`villages`) — `vocation_id`/`town_id`/outfits de cada vila.
- `data/characters.json` — personagens iniciais por vila (id, nome, descrição, `looktype`).
- `assets-src/import/extracted/mugen/<looktype>/idle_*.png` (ou `front_*.png` se
  não houver `idle_*`) — preview do outfit na tela de criação de personagem.
  Diretório privado do projeto; o AAC só expõe os looktypes que já aparecem em
  `characters.json`.
- `server/tfs/config.lua` — host/porta/usuário/senha/banco do MySQL.

## Regras aplicadas na criação de personagem

- **Senha em SHA1**: TFS 1.4.2 não tem `passwordType` configurável — o código
  (`server/tfs/src/iologindata.cpp`) sempre compara com `transformToSHA1(password)`.
  Este AAC grava e confere a senha da mesma forma (`hashlib.sha1(...).hexdigest()`).
- **Nome de personagem "estilo Tibia"**: 3 a 20 letras (com acentos) e espaços
  simples, sem espaço duplo nem nas pontas.
- **Colunas obrigatórias em `players`**: o INSERT preenche explicitamente
  `posx/posy/posz`, `town_id`, `conditions` (`NULL`, blob vazio),
  `lookbody/lookhead/looklegs/lookfeet` (0 — os looktypes 900+ são fantasias
  fechadas, não usam cor de doll) e `looktype` (do personagem escolhido),
  `vocation` (= `vocation_id` da vila), `health/healthmax` (150/150),
  `mana/manamax` (0/0), `cap` (400) — os valores base de nível 1 de qualquer
  vocação, já que o ganho por level das 4 vocações só começa a contar a partir
  do nível 2 (ver `gainhp`/`gainmana`/`gaincap` em `server/tfs/data/XML/vocations.xml`) —,
  `level=1`, `experience=0` e todos os `skill_*` em 10 / `skill_*_tries` em 0
  (os defaults "zerados" do TFS).
- **Storage do onboarding não é tocado**: o AAC nunca escreve em
  `player_storage`. Isso é proposital — `server/tfs/data/scripts/naruto/character_switch.lua`
  considera `first_time = true` enquanto a storage 60000 (`STORAGE_ONBOARDED`)
  não existir, e é isso que faz o **Menu Shinobi abrir sozinho** no primeiro
  login (aba Personagem), confirmado no teste (ver screenshots).
- **`town_id` é resolvido contra o banco, não copiado direto de `tfs_mapping.json`**:
  `IOLoginData::loadPlayer` (`server/tfs/src/iologindata.cpp:347`) **rejeita o
  login inteiro** (`return false`) se o `town_id` do personagem não existir na
  tabela `towns` carregada do mapa atual. Hoje (mapa `forest_valley`) só existe
  a Vila da Folha (`towns.id = 1`); Névoa/Nuvem/Areia ainda não têm mapa/templo
  próprio. Por isso `resolve_town()` consulta a tabela `towns` pelo `town_id` da
  vila escolhida e, se não existir, cai para a primeira town que existir (hoje,
  sempre a 1) — tanto na posição quanto no **valor de `town_id` gravado**,
  nunca o aspiracional do JSON. O aviso "nasceu na Vila da Folha até a vila
  escolhida ter mapa próprio" aparece na tela quando isso acontece.
- **Sem SQL manual, sem exposição de senha**: todas as queries usam parâmetros
  (`pymysql`, nunca f-string/format dentro do SQL); a senha nunca é logada nem
  devolvida em nenhuma resposta; o corpo do POST é limitado a 16 KB.

## Pendências conhecidas

- Só a Vila da Folha tem templo de verdade no mapa atual. Personagens de
  Névoa/Nuvem/Areia nascem lá mesmo (aviso explícito na tela de criação) até
  essas vilas terem mapa próprio — ver `docs/sistemas/mapas.md` /
  `CLAUDE.md` ("Estado atual").
- Preview do outfit usa o PNG do frame parado extraído do MUGEN
  (`assets-src/import/extracted/mugen/<looktype>/idle_*.png`), não o sprite
  real do `.spr/.dat` do cliente — é só uma miniatura de referência na tela de
  criação, não afeta o outfit gravado no personagem (`looktype`).
- Não há recuperação de senha nem confirmação de e-mail (fora de escopo:
  ferramenta interna/local, não uma AAC pública).

## Teste feito nesta sessão

1. Subiu o AAC (`tools/aac.sh`), criou conta via `curl -X POST /criar-conta` e
   personagem (Vila da Folha, "Genin Laranja") via `curl -X POST /criar-personagem`.
2. Conferiu no banco (`mysql -u tfs -ptfs forgottenserver`): `level=1`,
   `vocation=1`, `town_id=1`, `posx/posy/posz` = templo real da Vila da Folha,
   `looktype=900`, senha em SHA1 (40 chars).
3. Testou erros: conta duplicada, senha errada na criação de personagem, nome
   de personagem inválido, personagem com nome duplicado — todos com mensagem
   amigável e HTTP 400.
4. Logou de verdade com essa conta/senha usando `tools/autotest_client.sh
   <conta> <senha>` (copia `client-otc/tests/autotest_rc.lua` para
   `client-otc/shinobirc.lua`, roda o OTClient, remove o rc ao final — nada
   deste teste editou `client-otc/tests/` nem `tools/autotest_client.sh`).
   Resultado: personagem nasceu no templo (1029, 1042, 7), com o outfit do
   "Genin Laranja" e o **Menu Shinobi abriu sozinho** (aba Personagem, "Genin
   Laranja" marcado como ATUAL, "Level 1 · Vila da Folha"). Screenshots em
   `screenshots/aac_01_spawn_templo.png` e `screenshots/aac_02_hud.png`.
5. Apagou a conta e o personagem de teste do banco ao final
   (`DELETE FROM players/accounts WHERE name = ...`).
