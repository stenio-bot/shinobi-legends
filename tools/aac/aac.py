#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AAC minimo do Shinobi Legends (estilo os "Account Application/Creation" dos
servidores de Tibia, mas local e sem SQL manual).

Servidor HTTP em Python puro (http.server) + pymysql para falar com o mesmo
MariaDB do TFS 1.4.2 (server/tfs/schema.sql). Nao depende de framework web.

Rodar:
    tools/aac.sh                          # sobe em background, porta 8080
    .venv/bin/python3 tools/aac/aac.py    # primeiro plano (Ctrl+C para parar)

Paginas:
    /                 home com nome do jogo, frase da biblia, dados de conexao e links
    /criar-conta      formulario de criacao de conta (nome, senha, confirmacao, e-mail opcional)
    /criar-personagem escolha de vila (4) + personagem (9, com preview/elemento/jutsus) + nome + sexo
    /conta            login (conta+senha): lista personagens (nivel/vila/personagem/ultimo login)
                      + formulario de troca de senha
    /trocar-senha     POST-only, usado pelo formulario acima
    /sprite/<id>.png  preview PNG de um looktype de personagem inicial (whitelist)

Le, mas nunca edita: data/villages.json, data/tfs_mapping.json, data/characters.json,
data/element_sets.json, data/jutsus/personal.json, data/jutsus/neutral.json,
server/tfs/config.lua (credenciais/portas do banco e do servidor), server/tfs/schema.sql
(so leitura humana, nao parseado em runtime).
"""
import glob
import hashlib
import html
import json
import os
import re
import sys
import time
import traceback
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    sys.stderr.write(
        "ERRO: pymysql nao esta instalado no interpretador usado para rodar este script.\n"
        "Instale no venv do projeto e rode com ele:\n"
        "    .venv/bin/pip install pymysql\n"
        "    .venv/bin/python3 tools/aac/aac.py\n"
    )
    raise

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(ROOT, "data")
ASSETS_MUGEN = os.path.join(ROOT, "assets-src", "import", "extracted", "mugen")
TFS_CONFIG_PATH = os.path.join(ROOT, "server", "tfs", "config.lua")

PORT = int(os.environ.get("AAC_PORT", "8080"))
MAX_BODY = 16 * 1024  # limite de tamanho do corpo do POST (bytes)

GAME_TITLE = "Shinobi Legends"
CLIENT_PROTOCOL = "10.98"  # versao do OTClient (protocolo 1098) deste projeto (client-otc/)

# Frase da "biblia do jogo" (docs/00-biblia-do-jogo.md, secao 1 - Visao), usada na home.
BIBLE_QUOTE = (
    "Cada caçada dá XP, sobe skill por uso, dropa itens e ryo, e o jutsu certo "
    "na hora certa é o que faz a diferença entre uma matança rápida e "
    "uma corrida até a poção de vida."
)


# ---------------------------------------------------------------------------
# configuracao do banco/servidor: le server/tfs/config.lua (nunca editado por
# este script) em vez de hardcodar credenciais/portas, para nao divergir do
# servidor real que estiver no ar.
# ---------------------------------------------------------------------------
def _read_tfs_config():
    cfg = {
        "mysqlHost": "127.0.0.1",
        "mysqlUser": "tfs",
        "mysqlPass": "tfs",
        "mysqlDatabase": "forgottenserver",
        "mysqlPort": 3306,
        "ip": "127.0.0.1",
        "loginProtocolPort": 7171,
    }
    try:
        with open(TFS_CONFIG_PATH, encoding="utf-8") as f:
            text = f.read()
        for key in list(cfg):
            m = re.search(r'%s\s*=\s*"([^"]*)"' % re.escape(key), text)
            if m:
                cfg[key] = m.group(1)
                continue
            m = re.search(r"%s\s*=\s*(\d+)" % re.escape(key), text)
            if m:
                cfg[key] = int(m.group(1))
    except OSError:
        pass
    cfg["mysqlPort"] = int(cfg["mysqlPort"])
    cfg["loginProtocolPort"] = int(cfg["loginProtocolPort"])
    return cfg


DB_CFG = _read_tfs_config()
SERVER_IP = DB_CFG["ip"]
SERVER_PORT = DB_CFG["loginProtocolPort"]


def db_connect():
    return pymysql.connect(
        host=DB_CFG["mysqlHost"],
        port=DB_CFG["mysqlPort"],
        user=DB_CFG["mysqlUser"],
        password=DB_CFG["mysqlPass"],
        database=DB_CFG["mysqlDatabase"],
        charset="utf8mb4",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )


# ---------------------------------------------------------------------------
# dados de jogo (somente leitura): data/*.json e' a fonte da verdade do
# projeto (CLAUDE.md) -- este script nunca escreve nesses arquivos.
# ---------------------------------------------------------------------------
def _load_json(name):
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
        return json.load(f)


VILLAGES = _load_json("villages.json")
TFS_MAPPING = _load_json("tfs_mapping.json")
CHARACTERS = _load_json("characters.json")
ELEMENT_SETS = _load_json("element_sets.json")
JUTSUS_PERSONAL = _load_json(os.path.join("jutsus", "personal.json"))
JUTSUS_NEUTRAL = _load_json(os.path.join("jutsus", "neutral.json"))

VILLAGE_ORDER = ["leaf", "mist", "cloud", "sand"]
VILLAGE_NAME = {v["id"]: v["name"] for v in VILLAGES}
VILLAGE_BY_ID = {v["id"]: v for v in VILLAGES}
VILLAGE_TFS = TFS_MAPPING["villages"]  # leaf/mist/cloud/sand -> vocation_id, town_id, outfits, default_outfit

# rotulos pt-BR das skills-bonus de vila (data/villages.json.bonus_skill) e dos
# elementos (id do elemento -> nome em portugues, data/element_sets.json).
SKILL_LABEL = {
    "taijutsu": "Taijutsu",
    "ninjutsu": "Ninjutsu",
    "genjutsu": "Genjutsu",
    "shuriken": "Shuriken",
    "defense": "Defesa",
}
ELEMENT_NAME_PT = {e["id"]: e["name"] for e in ELEMENT_SETS}


def element_label(element_id):
    name_pt = ELEMENT_NAME_PT.get(element_id)
    if not name_pt:
        return element_id
    return "%s (%s)" % (element_id.capitalize(), name_pt)


CHARACTERS_BY_VILLAGE = {}
for c in CHARACTERS:
    CHARACTERS_BY_VILLAGE.setdefault(c["village"], []).append(c)
CHARACTERS_BY_ID = {c["id"]: c for c in CHARACTERS}
CHARACTERS_BY_LOOKTYPE = {c["looktype"]: c for c in CHARACTERS}

# looktypes com preview liberado (evita servir arquivo arbitrario por /sprite/)
PREVIEW_LOOKTYPES = {c["looktype"] for c in CHARACTERS}

# nome de exibicao de cada jutsu pessoal (data/jutsus/personal.json + neutral.json --
# alguns jutsus "universais" como kawarimi/punho_suave/fuuin_contencao moram em
# neutral.json, nao em personal.json, apesar de aparecerem em characters.json).
JUTSU_NAME_BY_ID = {}
for _src in (JUTSUS_PERSONAL, JUTSUS_NEUTRAL):
    for _j in _src:
        JUTSU_NAME_BY_ID[_j["id"]] = _j["name"]


def preview_path(looktype):
    """Caminho do PNG de preview (frame parado) de um looktype, ou None."""
    d = os.path.join(ASSETS_MUGEN, str(int(looktype)))
    if not os.path.isdir(d):
        return None
    for pattern in ("idle_*.png", "front_*.png"):
        matches = sorted(glob.glob(os.path.join(d, pattern)))
        if matches:
            return matches[0]
    return None


# ---------------------------------------------------------------------------
# validacao e senha
# ---------------------------------------------------------------------------
ACCOUNT_NAME_RE = re.compile(r"^[A-Za-z0-9_]{3,32}$")
# nome de personagem "estilo Tibia": 3-20 letras (com acentos) e espacos simples,
# sem espaco duplo, sem espaco nas pontas.
CHAR_NAME_RE = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ]+(?: [A-Za-zÀ-ÖØ-öø-ÿ]+)*$")


def sha1_hex(s: str) -> str:
    # TFS 1.4.2 nao tem passwordType configuravel: IOLoginData::loginserverAuthentication
    # e gameworldAuthentication (server/tfs/src/iologindata.cpp) sempre comparam com
    # transformToSHA1(password) -- este AAC grava/confere a senha do mesmo jeito.
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def valid_account_name(name: str):
    return bool(ACCOUNT_NAME_RE.match(name or ""))


def valid_character_name(name: str):
    name = (name or "").strip()
    if not (3 <= len(name) <= 20):
        return False
    if "  " in name:
        return False
    return bool(CHAR_NAME_RE.match(name))


def valid_password(pw: str):
    return bool(pw) and 4 <= len(pw) <= 64


# ---------------------------------------------------------------------------
# regras de conta / personagem
# ---------------------------------------------------------------------------
class AacError(Exception):
    pass


def create_account(name: str, password: str, password2: str, email: str):
    name = (name or "").strip()
    email = (email or "").strip()
    if not valid_account_name(name):
        raise AacError("Nome de conta invalido: use 3-32 letras, numeros ou _ (sem espacos).")
    if password != password2:
        raise AacError("As senhas nao sao iguais.")
    if not valid_password(password):
        raise AacError("A senha deve ter entre 4 e 64 caracteres.")
    if email and ("@" not in email or " " in email or len(email) > 255):
        raise AacError("E-mail invalido.")

    conn = db_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM accounts WHERE name=%s", (name,))
            if cur.fetchone():
                raise AacError("Ja existe uma conta com esse nome.")
            try:
                cur.execute(
                    "INSERT INTO accounts (name, password, type, email, creation) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (name, sha1_hex(password), 1, email, int(time.time())),
                )
            except pymysql.err.IntegrityError:
                raise AacError("Ja existe uma conta com esse nome.")
        return "Conta \"%s\" criada com sucesso. Agora crie um personagem." % name
    finally:
        conn.close()


def authenticate_account(conn, name: str, password: str):
    with conn.cursor() as cur:
        cur.execute("SELECT id, password FROM accounts WHERE name=%s", ((name or "").strip(),))
        row = cur.fetchone()
    if not row or row["password"] != sha1_hex(password or ""):
        raise AacError("Conta ou senha invalidos.")
    return row["id"]


def resolve_town(conn, town_id: int):
    """Posicao do templo de town_id. Se o mapa carregado ainda nao tiver essa
    town (so a Vila da Folha existe no forest_valley.json atual), cai para a
    primeira town que existir -- IMPORTANTE: TFS 1.4.2 REJEITA o login inteiro
    (IOLoginData::loadPlayer devolve false) se o personagem tiver town_id que
    nao existe no mapa carregado, entao o id usado no INSERT tem que ser o
    town_id resolvido (o que existe de fato), nunca o da vila "aspiracional"
    de data/tfs_mapping.json.
    Retorna (town_id_resolvido, posx, posy, posz, exato:bool).
    """
    with conn.cursor() as cur:
        cur.execute("SELECT id, posx, posy, posz FROM towns WHERE id=%s", (town_id,))
        row = cur.fetchone()
        if row:
            return row["id"], row["posx"], row["posy"], row["posz"], True
        cur.execute("SELECT id, posx, posy, posz FROM towns ORDER BY id LIMIT 1")
        row = cur.fetchone()
        if row:
            return row["id"], row["posx"], row["posy"], row["posz"], False
    # ultimo recurso (banco sem nenhuma town -- nao deveria acontecer com o
    # servidor no ar, mas nao trava a criacao por isso)
    return town_id, 0, 0, 7, False


# Storages lidas por server/tfs/data/scripts/naruto/character_switch.lua (gerado
# por tools/export_tfs.py a partir de data/*.json -- NAO editar esse gerador,
# so consumir os mesmos ids de storage que ele ja usa):
#   60000 STORAGE_ONBOARDED -- 1 depois da 1a aplicacao de personagem/elemento.
#   60001 STORAGE_CHARACTER -- looktype do personagem atual (NarutoCharacters.current).
#   60002 STORAGE_ELEMENT   -- indice (1-based) do elemento em NarutoElements.list.
# Este AAC grava SO a 60001 (looktype do personagem escolhido na criacao) --
# de proposito:
#   - NAO toca a 60000: enquanto ela nao existir, o login roda com
#     first_time=true (NarutoCharacters, onLogin) e o Menu Shinobi abre sozinho
#     no cliente para o jogador revisar/trocar personagem e elemento -- UX
#     documentada em docs/sistemas/cliente-ux.md.
#   - NAO precisa gravar a 60002 (elemento): NarutoCharacters.apply(), chamada
#     no login, cai em NarutoElements.byId[char.default_element] quando a 60002
#     nao existe -- ou seja, o elemento padrao do personagem escolhido (mesmo
#     campo default_element de data/characters.json) e' aplicado sozinho.
# Resultado: o personagem que o jogador escolheu no AAC e' o que aparece de
# verdade no 1o login (chakra, outfit e os 4+4 jutsus certos), sem perder a
# tela de revisao do Menu Shinobi.
STORAGE_CHARACTER = 60001


def create_character(account_name: str, account_password: str, char_name: str, sex: str, character_id: str):
    char_name = (char_name or "").strip()
    if not valid_character_name(char_name):
        raise AacError("Nome de personagem invalido: 3-20 letras/espacos (sem espaco duplo ou nas pontas).")

    char_def = CHARACTERS_BY_ID.get(character_id)
    if not char_def:
        raise AacError("Escolha um personagem inicial valido.")
    village = char_def["village"]
    vinfo = VILLAGE_TFS.get(village)
    if not vinfo:
        raise AacError("Vila invalida.")

    sex_val = 1 if sex == "m" else 0

    conn = db_connect()
    try:
        account_id = authenticate_account(conn, account_name, account_password)

        with conn.cursor() as cur:
            cur.execute("SELECT id FROM players WHERE name=%s", (char_name,))
            if cur.fetchone():
                raise AacError("Ja existe um personagem com esse nome.")

        town_id, posx, posy, posz, exact_town = resolve_town(conn, vinfo["town_id"])

        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO players
                        (name, group_id, account_id, level, vocation, experience,
                         health, healthmax, mana, manamax, cap,
                         town_id, posx, posy, posz, conditions,
                         lookbody, lookfeet, lookhead, looklegs, looktype, lookaddons,
                         direction, sex,
                         skill_fist, skill_fist_tries, skill_club, skill_club_tries,
                         skill_sword, skill_sword_tries, skill_axe, skill_axe_tries,
                         skill_dist, skill_dist_tries, skill_shielding, skill_shielding_tries,
                         skill_fishing, skill_fishing_tries)
                    VALUES
                        (%s, 1, %s, 1, %s, 0,
                         150, 150, 110, 110, 400,
                         %s, %s, %s, %s, NULL,
                         0, 0, 0, 0, %s, 0,
                         2, %s,
                         10, 0, 10, 0,
                         10, 0, 10, 0,
                         10, 0, 10, 0,
                         10, 0)
                    """,
                    (
                        char_name, account_id, vinfo["vocation_id"],
                        town_id, posx, posy, posz,
                        char_def["looktype"], sex_val,
                    ),
                )
            except pymysql.err.IntegrityError:
                raise AacError("Ja existe um personagem com esse nome.")
            player_id = cur.lastrowid
            # ver comentario longo acima de STORAGE_CHARACTER: so' esta storage,
            # o resto (elemento/onboarding) o proprio character_switch.lua resolve
            # sozinho no 1o login.
            cur.execute(
                "INSERT INTO player_storage (player_id, `key`, value) VALUES (%s, %s, %s)",
                (player_id, STORAGE_CHARACTER, char_def["looktype"]),
            )

        msg = 'Personagem "%s" criado na %s como %s! Nasce no templo (%d,%d,%d).' % (
            char_name, VILLAGE_NAME.get(village, village), char_def["name"], posx, posy, posz,
        )
        if not exact_town:
            msg += (
                " Aviso: o mapa atual (forest_valley) ainda so tem o templo da Vila da Folha "
                "pronto; o personagem nasceu la ate a vila escolhida ter mapa proprio."
            )
        return msg
    finally:
        conn.close()


def list_characters(account_name: str, account_password: str):
    conn = db_connect()
    try:
        account_id = authenticate_account(conn, account_name, account_password)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name, level, vocation, looktype, town_id, sex, lastlogin "
                "FROM players WHERE account_id=%s AND deletion=0 ORDER BY name ASC",
                (account_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def change_password(account_name: str, current_password: str, new_password: str, new_password2: str):
    if new_password != new_password2:
        raise AacError("As novas senhas nao sao iguais.")
    if not valid_password(new_password):
        raise AacError("A nova senha deve ter entre 4 e 64 caracteres.")
    conn = db_connect()
    try:
        account_id = authenticate_account(conn, account_name, current_password)
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE accounts SET password=%s WHERE id=%s",
                (sha1_hex(new_password), account_id),
            )
        return "Senha alterada com sucesso."
    finally:
        conn.close()


VOCATION_TO_VILLAGE = {v["vocation_id"]: k for k, v in VILLAGE_TFS.items()}


def format_lastlogin(ts):
    if not ts:
        return "nunca"
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%d/%m/%Y %H:%M")
    except (ValueError, OSError):
        return "nunca"


# ---------------------------------------------------------------------------
# HTML (inline, tema "pergaminho/pedra" -- sobrio, coerente com o Tibia
# classico; sem frameworks/fontes/imagens externas, funciona 100% offline).
# ---------------------------------------------------------------------------
BASE_CSS = """
:root {
  color-scheme: light;
  --parchment: #ead9b3;
  --parchment-2: #e0cc9c;
  --parchment-dark: #d3ba86;
  --ink: #3a2a18;
  --ink-muted: #6b5a42;
  --wood: #6b4226;
  --wood-dark: #43290f;
  --stone: #78726420;
  --gold: #96691f;
  --accent: #8b1e1e;
  --ok: #2f6b30;
  --ok-bg: #dce9d6;
  --error: #8b1e1e;
  --error-bg: #ecd9d3;
}
* { box-sizing: border-box; }
body {
  background: radial-gradient(ellipse at top, #f2e6c4 0%, var(--parchment-dark) 78%, #b99a63 100%);
  color: var(--ink);
  font-family: Georgia, "Times New Roman", "Palatino Linotype", serif;
  margin: 0;
  padding: 0 16px 48px;
}
header.top {
  max-width: 900px;
  margin: 0 auto;
  padding: 30px 0 14px;
  text-align: center;
  border-bottom: 3px double var(--wood);
}
header.top h1 {
  font-size: 32px;
  letter-spacing: 2px;
  margin: 0;
  color: var(--wood-dark);
  text-shadow: 1px 1px 0 rgba(255,255,255,0.35);
  font-variant: small-caps;
}
header.top p.subtitle { color: var(--ink-muted); margin: 6px 0 0; font-style: italic; }
nav.tabs {
  max-width: 900px;
  margin: 18px auto 0;
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}
nav.tabs a {
  color: var(--parchment);
  background: linear-gradient(180deg, var(--wood) 0%, var(--wood-dark) 100%);
  border: 1px solid var(--wood-dark);
  padding: 9px 18px;
  border-radius: 4px;
  text-decoration: none;
  font-size: 14px;
  font-variant: small-caps;
  letter-spacing: 0.5px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.15);
}
nav.tabs a:hover { background: linear-gradient(180deg, var(--gold) 0%, var(--wood-dark) 100%); }
main {
  max-width: 900px;
  margin: 26px auto 0;
  background: linear-gradient(180deg, var(--parchment) 0%, var(--parchment-2) 100%);
  border: 1px solid var(--wood);
  outline: 1px solid var(--parchment-dark);
  outline-offset: -6px;
  border-radius: 6px;
  padding: 26px 30px;
  box-shadow: 0 6px 18px rgba(60,40,15,0.25);
}
h2 {
  color: var(--wood-dark);
  margin-top: 0;
  font-variant: small-caps;
  border-bottom: 2px solid var(--parchment-dark);
  padding-bottom: 8px;
}
h3 { color: var(--wood-dark); font-variant: small-caps; margin: 18px 0 6px; }
label { display: block; margin: 14px 0 6px; font-size: 14px; color: var(--ink-muted); font-weight: bold; }
input[type=text], input[type=password], input[type=email], select {
  width: 100%;
  padding: 9px 10px;
  border-radius: 4px;
  border: 1px solid var(--wood);
  background: #fbf3de;
  color: var(--ink);
  font-size: 14px;
  font-family: inherit;
}
input:focus, select:focus { outline: none; border-color: var(--accent); }
.row { display: flex; gap: 16px; flex-wrap: wrap; }
.row > div { flex: 1; min-width: 180px; }
button, .btn {
  margin-top: 22px;
  background: linear-gradient(180deg, var(--gold) 0%, var(--wood) 100%);
  color: #fff6e0;
  font-weight: bold;
  border: 1px solid var(--wood-dark);
  padding: 11px 22px;
  border-radius: 5px;
  font-size: 15px;
  font-variant: small-caps;
  letter-spacing: 0.5px;
  cursor: pointer;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.25);
}
button:hover, .btn:hover { filter: brightness(1.08); }
.msg-ok, .msg-error {
  padding: 12px 14px;
  border-radius: 5px;
  margin-bottom: 18px;
  font-size: 14px;
  border: 1px solid;
}
.msg-ok { background: var(--ok-bg); border-color: var(--ok); color: var(--ok); }
.msg-error { background: var(--error-bg); border-color: var(--error); color: var(--error); }
.conn-box {
  background: var(--parchment-dark);
  border: 1px solid var(--wood);
  border-radius: 6px;
  padding: 14px 18px;
  margin: 14px 0;
}
.conn-box dl { display: grid; grid-template-columns: max-content 1fr; gap: 4px 14px; margin: 0; }
.conn-box dt { color: var(--ink-muted); font-variant: small-caps; }
.conn-box dd { margin: 0; font-weight: bold; }
.village-tabs { display: flex; gap: 8px; flex-wrap: wrap; margin: 10px 0 4px; }
.village-tabs button.vtab {
  margin-top: 0;
  background: var(--parchment-2);
  color: var(--ink);
  border: 1px solid var(--wood);
  font-weight: normal;
  font-variant: small-caps;
  padding: 8px 16px;
  box-shadow: none;
}
.village-tabs button.vtab.active {
  background: linear-gradient(180deg, var(--gold) 0%, var(--wood) 100%);
  color: #fff6e0;
  border-color: var(--wood-dark);
}
.village-info {
  font-size: 13px;
  color: var(--ink-muted);
  margin: 0 0 14px;
  min-height: 18px;
}
.village-info b { color: var(--ink); }
.char-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 12px;
  margin-bottom: 8px;
}
.char-card {
  display: none;
  border: 2px solid var(--wood);
  border-radius: 6px;
  background: #fbf3de;
  padding: 14px 12px;
  text-align: center;
  cursor: pointer;
}
.char-card.visible { display: block; }
.char-card.selected { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(139,30,30,0.18); }
.char-card img {
  image-rendering: pixelated;
  width: 66px;
  height: 96px;
  object-fit: contain;
  background: #2a2013;
  border-radius: 4px;
  padding: 6px;
}
.char-card .cname { font-weight: bold; margin-top: 8px; font-size: 14px; color: var(--wood-dark); }
.char-card .celement { font-size: 11px; color: var(--gold); font-variant: small-caps; margin-top: 2px; }
.char-card .cdesc { font-size: 12px; color: var(--ink-muted); margin-top: 6px; min-height: 30px; }
.char-card .cjutsus { font-size: 11px; color: var(--ink-muted); margin-top: 8px; text-align: left; padding-left: 16px; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--wood); font-size: 14px; }
th { color: var(--wood-dark); font-weight: bold; font-variant: small-caps; }
.hint { color: var(--ink-muted); font-size: 13px; margin-top: 6px; }
code { background: var(--parchment-dark); padding: 1px 6px; border-radius: 4px; }
ol, ul { padding-left: 22px; }
ol li, ul li { margin-bottom: 6px; }
hr.sep { border: none; border-top: 2px double var(--wood); margin: 28px 0; }
footer { text-align: center; color: var(--ink-muted); font-size: 12px; margin-top: 26px; }
"""


def page(title, body_html, msg_ok=None, msg_error=None):
    msgs = ""
    if msg_ok:
        msgs += '<div class="msg-ok">%s</div>' % html.escape(msg_ok)
    if msg_error:
        msgs += '<div class="msg-error">%s</div>' % html.escape(msg_error)
    return """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s - %s</title>
<style>%s</style>
</head>
<body>
<header class="top">
  <h1>%s</h1>
  <p class="subtitle">Cria&ccedil;&atilde;o de conta e personagem</p>
</header>
<nav class="tabs">
  <a href="/">In&iacute;cio</a>
  <a href="/criar-conta">Criar conta</a>
  <a href="/criar-personagem">Criar personagem</a>
  <a href="/conta">Meus personagens</a>
</nav>
<main>
%s
%s
</main>
<footer>%s AAC &middot; servidor local %s:%s &middot; protocolo %s (OTClient)</footer>
</body>
</html>""" % (
        html.escape(title), GAME_TITLE, BASE_CSS, GAME_TITLE, msgs, body_html,
        GAME_TITLE, SERVER_IP, SERVER_PORT, CLIENT_PROTOCOL,
    )


def render_home():
    body = """
<h2>Bem-vindo(a) a %(title)s!</h2>
<p style="font-style:italic;color:var(--ink-muted);border-left:3px solid var(--wood);padding-left:14px;">
&ldquo;%(quote)s&rdquo;
</p>
<p>Este site cria contas e personagens para o servidor local do <b>%(title)s</b>
(The Forgotten Server 1.4.2), sem precisar mexer no banco de dados na mao.</p>

<h3>Como conectar</h3>
<div class="conn-box">
  <dl>
    <dt>Servidor</dt><dd>%(ip)s</dd>
    <dt>Porta</dt><dd>%(port)s</dd>
    <dt>Protocolo</dt><dd>%(proto)s</dd>
    <dt>Cliente</dt><dd>OTClient Redemption (client-otc/ deste projeto)</dd>
  </dl>
</div>

<h3>Primeiros passos</h3>
<ol>
  <li>Crie uma conta em <a href="/criar-conta">Criar conta</a> (nome + senha).</li>
  <li>Crie um personagem em <a href="/criar-personagem">Criar personagem</a>:
      escolha a vila, o personagem inicial e o nome do seu ninja.</li>
  <li>Abra o cliente (OTClient) e entre com os dados acima, usando a conta e a
      senha que voce criou.</li>
</ol>
<p class="hint">O personagem nasce no templo da vila, com o outfit do personagem inicial escolhido,
level 1. Na primeira entrada em jogo o <b>Menu Shinobi</b> abre sozinho para voce revisar
personagem/elemento/jutsus (pode manter a escolha feita aqui ou trocar na hora).</p>
<p>
  <a class="btn" href="/criar-conta" style="display:inline-block;text-decoration:none;">Criar minha conta &rarr;</a>
  <a class="btn" href="/conta" style="display:inline-block;text-decoration:none;margin-left:10px;">Ver meus personagens &rarr;</a>
</p>
""" % {
        "title": html.escape(GAME_TITLE),
        "quote": html.escape(BIBLE_QUOTE),
        "ip": html.escape(SERVER_IP),
        "port": SERVER_PORT,
        "proto": CLIENT_PROTOCOL,
    }
    return page("Início", body)


def render_create_account_form(msg_ok=None, msg_error=None, values=None):
    values = values or {}
    body = """
<h2>Criar conta</h2>
<form method="post" action="/criar-conta">
  <label for="name">Nome da conta (3-32, letras/numeros/_)</label>
  <input type="text" id="name" name="name" maxlength="32" required value="%s">
  <div class="row">
    <div>
      <label for="password">Senha (4-64 caracteres)</label>
      <input type="password" id="password" name="password" maxlength="64" required>
    </div>
    <div>
      <label for="password2">Confirmar senha</label>
      <input type="password" id="password2" name="password2" maxlength="64" required>
    </div>
  </div>
  <label for="email">E-mail (opcional)</label>
  <input type="email" id="email" name="email" maxlength="255" value="%s">
  <button type="submit">Criar conta</button>
</form>
<p class="hint">A senha e' guardada como SHA1 (e' o que o TFS 1.4.2 usa para autenticar login,
sem opcao de configurar outro algoritmo).</p>
""" % (html.escape(values.get("name", "")), html.escape(values.get("email", "")))
    return page("Criar conta", body, msg_ok, msg_error)


def _village_tab_html(vid, active):
    vname = VILLAGE_NAME.get(vid, vid)
    return (
        '<button type="button" class="vtab %s" data-village="%s" '
        'onclick="showVillage(\'%s\')">%s</button>'
    ) % (
        "active" if active else "",
        vid,
        vid,
        html.escape(vname),
    )


def _char_card_html(char, vid_index, selected_char):
    visible = "visible" if vid_index == 0 else ""
    selected = "selected" if char["id"] == selected_char else ""
    jutsu_names = [JUTSU_NAME_BY_ID.get(j, j) for j in char.get("personal_jutsus", [])]
    jutsus_html = "".join("<li>%s</li>" % html.escape(j) for j in jutsu_names)
    return """
<div class="char-card %s %s" data-village="%s" onclick="selectCharacter(this, '%s')">
  <img src="/sprite/%d.png" alt="%s" loading="lazy">
  <div class="cname">%s</div>
  <div class="celement">%s</div>
  <div class="cdesc">%s</div>
  <ul class="cjutsus">%s</ul>
</div>""" % (
        visible, selected, char["village"], char["id"], char["looktype"],
        html.escape(char["name"]), html.escape(char["name"]),
        html.escape(element_label(char.get("default_element", ""))),
        html.escape(char.get("description", "")),
        jutsus_html,
    )


def render_create_character_form(msg_ok=None, msg_error=None, values=None):
    values = values or {}
    selected_char = values.get("character", "")

    village_buttons = [
        _village_tab_html(vid, i == 0) for i, vid in enumerate(VILLAGE_ORDER)
    ]
    char_cards = []
    for i, vid in enumerate(VILLAGE_ORDER):
        for char in CHARACTERS_BY_VILLAGE.get(vid, []):
            char_cards.append(_char_card_html(char, i, selected_char))

    body = """
<h2>Criar personagem</h2>
<form method="post" action="/criar-personagem" id="charForm">
  <label>1. Escolha a vila</label>
  <div class="village-tabs">%s</div>
  <p class="village-info" id="villageInfo"></p>
  <div class="char-grid">%s</div>
  <input type="hidden" name="character" id="characterInput" value="%s" required>
  <p class="hint" id="pickHint">Clique em um personagem para escolhe-lo (voce podera revisar
  personagem e elemento de novo no primeiro login, no Menu Shinobi).</p>

  <label>2. Dados do seu ninja</label>
  <div class="row">
    <div>
      <label for="char_name">Nome do personagem (3-20 letras/espacos)</label>
      <input type="text" id="char_name" name="char_name" maxlength="20" required value="%s">
    </div>
    <div>
      <label for="sex">Sexo</label>
      <select id="sex" name="sex">
        <option value="m">Masculino</option>
        <option value="f">Feminino</option>
      </select>
    </div>
  </div>

  <label>3. Sua conta</label>
  <div class="row">
    <div>
      <label for="account">Conta</label>
      <input type="text" id="account" name="account" maxlength="32" required value="%s">
    </div>
    <div>
      <label for="account_password">Senha da conta</label>
      <input type="password" id="account_password" name="account_password" maxlength="64" required>
    </div>
  </div>
  <button type="submit">Criar personagem</button>
</form>
<script>
var VILLAGE_INFO = {%s};
function showVillage(vid) {
  document.querySelectorAll('.vtab').forEach(function(b) {
    b.classList.toggle('active', b.dataset.village === vid);
  });
  document.querySelectorAll('.char-card').forEach(function(c) {
    c.classList.toggle('visible', c.dataset.village === vid);
  });
  document.getElementById('villageInfo').innerHTML = VILLAGE_INFO[vid] || '';
}
function selectCharacter(el, id) {
  document.querySelectorAll('.char-card').forEach(function(c) { c.classList.remove('selected'); });
  el.classList.add('selected');
  document.getElementById('characterInput').value = id;
  document.getElementById('pickHint').textContent = 'Personagem escolhido: ' + el.querySelector('.cname').textContent;
}
showVillage('%s');
</script>
""" % (
        "".join(village_buttons),
        "".join(char_cards),
        html.escape(selected_char),
        html.escape(values.get("char_name", "")),
        html.escape(values.get("account", "")),
        ",".join(
            "'%s': '%s'" % (vid, VILLAGE_BY_ID.get(vid, {}) and _village_info_js(vid))
            for vid in VILLAGE_ORDER
        ),
        VILLAGE_ORDER[0],
    )
    return page("Criar personagem", body, msg_ok, msg_error)


def _village_info_js(vid):
    v = VILLAGE_BY_ID.get(vid, {})
    vname = VILLAGE_NAME.get(vid, vid)
    text = "%s &middot; elemento <b>%s</b> &middot; bonus +20%% em <b>%s</b>" % (
        vname,
        element_label(v.get("element", "")),
        SKILL_LABEL.get(v.get("bonus_skill", ""), v.get("bonus_skill", "")),
    )
    # aspas simples do JS: o texto nao contem "'" (nomes/rotulos do projeto), mas
    # escapamos mesmo assim por seguranca.
    return text.replace("'", "&#39;")


def render_account_form(msg_ok=None, msg_error=None, values=None, characters=None):
    values = values or {}
    body = """
<h2>Meus personagens</h2>
<form method="post" action="/conta">
  <div class="row">
    <div>
      <label for="account">Conta</label>
      <input type="text" id="account" name="account" maxlength="32" required value="%s">
    </div>
    <div>
      <label for="account_password">Senha</label>
      <input type="password" id="account_password" name="account_password" maxlength="64" required>
    </div>
  </div>
  <button type="submit">Ver personagens</button>
</form>
""" % html.escape(values.get("account", ""))

    if characters is not None:
        if not characters:
            body += '<p class="hint">Essa conta ainda nao tem personagens. Crie um em <a href="/criar-personagem">Criar personagem</a>.</p>'
        else:
            rows = ""
            for ch in characters:
                village = VOCATION_TO_VILLAGE.get(ch["vocation"], "?")
                vname = VILLAGE_NAME.get(village, "vocacao %s" % ch["vocation"])
                char_def = CHARACTERS_BY_LOOKTYPE.get(ch["looktype"])
                cname = char_def["name"] if char_def else "-"
                rows += "<tr><td>%s</td><td>%d</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                    html.escape(ch["name"]), ch["level"], html.escape(vname),
                    html.escape(cname), format_lastlogin(ch.get("lastlogin")),
                )
            body += """
<table>
<thead><tr><th>Nome</th><th>Level</th><th>Vila</th><th>Personagem</th><th>Ultimo login</th></tr></thead>
<tbody>%s</tbody>
</table>""" % rows

    body += """
<hr class="sep">
<h3>Trocar senha</h3>
<form method="post" action="/trocar-senha">
  <div class="row">
    <div>
      <label for="pw_account">Conta</label>
      <input type="text" id="pw_account" name="account" maxlength="32" required value="%s">
    </div>
    <div>
      <label for="pw_current">Senha atual</label>
      <input type="password" id="pw_current" name="current_password" maxlength="64" required>
    </div>
  </div>
  <div class="row">
    <div>
      <label for="pw_new">Nova senha (4-64 caracteres)</label>
      <input type="password" id="pw_new" name="new_password" maxlength="64" required>
    </div>
    <div>
      <label for="pw_new2">Confirmar nova senha</label>
      <input type="password" id="pw_new2" name="new_password2" maxlength="64" required>
    </div>
  </div>
  <button type="submit">Trocar senha</button>
</form>
""" % html.escape(values.get("account", ""))
    return page("Meus personagens", body, msg_ok, msg_error)


# ---------------------------------------------------------------------------
# servidor HTTP
# ---------------------------------------------------------------------------
class AacHandler(BaseHTTPRequestHandler):
    server_version = "ShinobiAAC/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("[aac] %s - %s\n" % (self.address_string(), fmt % args))

    def _send_html(self, html_text, status=200):
        data = html_text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_png(self, path):
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError:
            self.send_error(404, "sprite nao encontrado")
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=86400")
        self.end_headers()
        self.wfile.write(data)

    def _read_form(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        if length > MAX_BODY:
            raise AacError("Requisicao grande demais.")
        raw = self.rfile.read(length)
        fields = parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
        return {k: v[0] for k, v in fields.items()}

    # ---- GET ----
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            if path == "/" or path == "":
                return self._send_html(render_home())
            if path == "/criar-conta":
                return self._send_html(render_create_account_form())
            if path == "/criar-personagem":
                return self._send_html(render_create_character_form())
            if path == "/conta":
                return self._send_html(render_account_form())
            if path.startswith("/sprite/") and path.endswith(".png"):
                raw_id = path[len("/sprite/"):-len(".png")]
                if not raw_id.isdigit():
                    return self.send_error(400, "id invalido")
                looktype = int(raw_id)
                if looktype not in PREVIEW_LOOKTYPES:
                    return self.send_error(404, "looktype nao liberado")
                p = preview_path(looktype)
                if not p:
                    return self.send_error(404, "sprite nao encontrado")
                return self._send_png(p)
            return self.send_error(404, "pagina nao encontrada")
        except Exception:
            traceback.print_exc()
            return self.send_error(500, "erro interno")

    # ---- POST ----
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            fields = self._read_form()
        except AacError as e:
            return self._send_html(page("Erro", "", msg_error=str(e)), status=400)

        try:
            if path == "/criar-conta":
                try:
                    msg = create_account(
                        fields.get("name", ""), fields.get("password", ""),
                        fields.get("password2", ""), fields.get("email", ""),
                    )
                    return self._send_html(render_create_account_form(msg_ok=msg))
                except AacError as e:
                    return self._send_html(
                        render_create_account_form(msg_error=str(e), values=fields), status=400
                    )

            if path == "/criar-personagem":
                try:
                    msg = create_character(
                        fields.get("account", ""), fields.get("account_password", ""),
                        fields.get("char_name", ""), fields.get("sex", "m"),
                        fields.get("character", ""),
                    )
                    return self._send_html(render_create_character_form(msg_ok=msg))
                except AacError as e:
                    return self._send_html(
                        render_create_character_form(msg_error=str(e), values=fields), status=400
                    )

            if path == "/conta":
                try:
                    chars = list_characters(fields.get("account", ""), fields.get("account_password", ""))
                    return self._send_html(
                        render_account_form(values=fields, characters=chars)
                    )
                except AacError as e:
                    return self._send_html(
                        render_account_form(msg_error=str(e), values=fields), status=400
                    )

            if path == "/trocar-senha":
                account = fields.get("account", "")
                try:
                    msg = change_password(
                        account, fields.get("current_password", ""),
                        fields.get("new_password", ""), fields.get("new_password2", ""),
                    )
                    # recarrega a lista de personagens com a senha nova, de brinde.
                    try:
                        chars = list_characters(account, fields.get("new_password", ""))
                    except AacError:
                        chars = None
                    return self._send_html(
                        render_account_form(msg_ok=msg, values={"account": account}, characters=chars)
                    )
                except AacError as e:
                    return self._send_html(
                        render_account_form(msg_error=str(e), values={"account": account}), status=400
                    )

            return self.send_error(404, "pagina nao encontrada")
        except Exception:
            traceback.print_exc()
            return self.send_error(500, "erro interno")


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), AacHandler)
    print("Shinobi Legends AAC em http://127.0.0.1:%d/ (banco: %s@%s:%d/%s; jogo em %s:%s)" % (
        PORT, DB_CFG["mysqlUser"], DB_CFG["mysqlHost"], DB_CFG["mysqlPort"], DB_CFG["mysqlDatabase"],
        SERVER_IP, SERVER_PORT,
    ))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
