#!/usr/bin/env python3
"""Gera os outfits dos personagens MUGEN (looktypes 900..926).

MATERIAL (privado, fora do git — ADR-002): ``assets-src/import/mugen/<Personagem>/
[<Variacao>/]<nome>_NNNN.bmp`` — rips estilo MUGEN/JUS de um jogo de luta. Sao
BMPs paletados (modo ``P``) em que o **indice 0 da paleta e a cor-chave** de fundo
(a cor concreta varia por quadro: verde escuro, verde neon...). A vista e
**LATERAL**: o personagem olha para a direita ou para a esquerda, nunca de frente
nem de costas.

O layout dos rips e razoavelmente estavel: 0 = icone pequeno, 1 = retrato grande
(120x140), depois a pose **parada** (respirando), agachar, **andar**, correr,
pular e por fim dezenas de golpes. Este script nao confia nessa ordem: ele mede
cada quadro e escolhe por heuristica (ver ``pick_idle`` / ``pick_walk``).

Saidas:

* ``assets-src/import/extracted/mugen/<looktype>/{idle,walk0,walk1,walk2}.png``
  — os quadros escolhidos, ja em RGBA com alpha binario;
* ``assets-src/import/extracted/mugen/_review_<looktype>.png`` — folha de revisao
  (idle + walk nas 4 direcoes, ampliada 3x);
* ``assets-src/import/extracted/mugen/_review_all.png`` — folha geral;
* ``assets-src/sprites/overrides/40_mugen.json`` — **este e o unico arquivo
  versionado**; o build (``build_assets.py``) o le com o mesmo esquema do
  ``imports.json`` e ignora com aviso toda entrada cujo PNG nao exista.

Uso::

    .venv/bin/python tools/spr/import_mugen.py            # tudo
    .venv/bin/python tools/spr/import_mugen.py --only 900 913
    .venv/bin/python tools/spr/import_mugen.py --report   # so o diagnostico
"""
import argparse
import json
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

LOOKTYPES = "assets-src/sprites/mugen_looktypes.json"
SRC_ROOT = "assets-src/import/mugen"
OUT_ROOT = "assets-src/import/extracted/mugen"
OVERRIDE = "assets-src/sprites/overrides/40_mugen.json"

MAX_SIDE = 96          # acima disso nao e o personagem (telas, efeitos de fundo)
MIN_SIDE = (12, 20)    # abaixo disso e faisca, poeira, icone
MIN_PIX = 60           # quadro praticamente vazio
FILL = (0.10, 0.75)    # densidade da caixa: <10% e poeira, >75% e uma bola solida
H_BAND = 14            # quanto a altura pode fugir da altura tipica do personagem
COLOR_MIN = 0.80       # semelhanca minima de paleta entre o andar e o parado
SCAN_FILES = 220       # arquivos lidos por personagem (o andar nunca esta alem)
SCAN_EARLY = 30        # ate onde uma corrida ainda conta como "comeco do rip"
SCAN_NEAR = 45         # onde o andar costuma estar (logo apos o parado)
SCAN_WALK = 120        # ate onde procurar o andar se nao houver nada perto
H_TOL = 3              # tolerancia de altura idle <-> walk (px)
SPAN_MIN = 3           # variacao minima do vao entre os pes para valer como passo


# ------------------------------------------------------------------ overrides
# Selecoes manuais, aplicadas quando a heuristica erra. Os numeros sao o NNNN do
# nome do arquivo (nao o indice na lista), para nao dependerem da filtragem.
#
#   "<looktype>": {"idle": N, "walk": [a, b, c], "faces": "left"|"right"}
#
# Qualquer chave e opcional: o que nao estiver aqui continua vindo da heuristica.
OVERRIDES = {
    # --- rips SEM ciclo de andar: o material tem parado, agachar, pular e
    #     golpes, e mais nada. Uso as proprias fases do RESPIRAR como andar:
    #     o boneco balanca em vez de dar passos, mas nunca aparece um golpe.
    "902": {"idle": 4, "walk": [3, 4, 5], "faces": "right"},        # Sakura Kid (63 quadros so)
    "907": {"idle": 3, "walk": [3, 4, 5], "faces": "right"},        # Minato: so ha corrida deitada
    "908": {"idle": 5, "walk": [5, 6, 7], "faces": "right"},        # Minato Edo: idem
    "925": {"idle": 6, "walk": [5, 6, 7], "faces": "right"},        # Naruto Girl: 6 quadros de gente
    "915": {"idle": 3, "walk": [2, 3, 4], "faces": "right"},        # Sasuke Akatsuki: so golpes de espada

    # --- o primeiro loop de silhueta constante nao era o respirar
    "911": {"idle": 8, "faces": "right"},   # Pain: 4-6 e "apontar o braco" em loop; 7-9 e o parado

    # --- a heuristica achou um "andar" que era golpe com efeito grande
    "919": {"idle": 4, "walk": [14, 15, 16], "faces": "right"},     # Sennin: corrida 14-17
    "920": {"idle": 5, "walk": [19, 20, 21], "faces": "right"},     # KCM: andar 19-22

    # --- formas de raposa: o rip comeca com dezenas de efeitos e o bicho e
    #     quadrupede, entao nem o parado nem o andar caiam onde deviam
    "921": {"idle": 5, "walk": [12, 13, 14], "faces": "right"},     # 1 calda: corre de quatro
    "922": {"idle": 76, "walk": [79, 81, 82], "faces": "right"},    # 4 caldas: quadrupede
    "923": {"idle": 22, "walk": [30, 31, 32], "faces": "right"},    # 6 caldas: quadrupede
    "926": {"faces": "right"},                                      # Kid Fox: so o lado
}


# ------------------------------------------------------------------ utilidades
def frame_no(name):
    m = re.search(r"_(\d+)\.[bB][mM][pP]$", name)
    return int(m.group(1)) if m else -1


def list_bmps(folder):
    """BMPs da pasta em ordem NUMERICA (ha nomes com 2 e com 3 digitos)."""
    got = [f for f in os.listdir(folder) if f.lower().endswith(".bmp")]
    got.sort(key=lambda f: (frame_no(f), f))
    return got


def load_bmp(path):
    """BMP paletado -> RGBA com o fundo transparente.

    Chave dupla, por seguranca: o **indice 0** da paleta e, alem dele, a **cor
    exata do pixel (0,0)** (alguns rips remapeiam a paleta e o fundo deixa de ser
    o indice 0, mas o canto superior esquerdo sempre e fundo)."""
    with Image.open(path) as im:
        im.load()
        idx = np.array(im) if im.mode in ("P", "L") else None
        rgb = np.array(im.convert("RGB"))
    key = rgb[0, 0]
    bg = np.all(rgb == key, axis=2)
    if idx is not None:
        bg |= (idx == idx[0, 0])
    out = np.dstack([rgb, np.where(bg, 0, 255).astype(np.uint8)])
    return Image.fromarray(out, "RGBA")


def is_skin(p):
    """Heuristica classica de tom de pele (rosto/maos), em RGB."""
    r, g, b = p[0], p[1], p[2]
    return (r > 95 and g > 40 and b > 20 and r > g and r > b
            and (max(r, g, b) - min(r, g, b)) > 15 and (r - g) > 15)


class Frame(object):
    """Um quadro util, ja recortado na bbox, com as medidas da triagem."""

    def __init__(self, no, name, img):
        self.no = no
        self.name = name
        self.img = img
        self.w, self.h = img.size
        a = np.array(img)
        op = a[:, :, 3] >= 128
        self.pixels = int(op.sum())
        self.fill = self.pixels / float(max(1, self.w * self.h))
        # --- vao entre os pes: extremos opacos do terco inferior
        y0 = max(0, self.h - max(4, self.h // 3))
        cols = np.where(op[y0:].any(axis=0))[0]
        self.span = int(cols[-1] - cols[0] + 1) if cols.size else 0
        self.foot_pix = int(op[y0:].sum())
        # --- pele na CABECA (terco superior): de que lado esta o rosto
        y1 = max(1, self.h // 3)
        head, hop = a[:y1], op[:y1]
        r, g, b = (head[:, :, 0].astype(int), head[:, :, 1].astype(int),
                   head[:, :, 2].astype(int))
        mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
        skin = hop & (r > 95) & (g > 40) & (b > 20) & (r > g) & (r > b) \
            & ((mx - mn) > 15) & ((r - g) > 15)
        half = self.w // 2
        self.skin_l = int(skin[:, :half].sum())
        self.skin_r = int(skin[:, half:].sum())
        self.head_pix = int(hop.sum())
        # --- assinatura de cor: histograma RGB 4x4x4 dos pixels opacos,
        # normalizado. Dois quadros do MESMO personagem tem assinaturas quase
        # iguais; um quadro com espada de chakra, manto de raposa ou pergaminho
        # gigante nao tem.
        q = (a[:, :, :3][op] // 64).astype(int)
        hist = np.zeros(64)
        if q.size:
            np.add.at(hist, q[:, 0] * 16 + q[:, 1] * 4 + q[:, 2], 1)
        n = np.linalg.norm(hist)
        self.rgbsig = hist / n if n else hist
        self._mask = None

    @property
    def mask(self):
        """Silhueta normalizada 24x32 (binaria) — para medir se dois quadros
        sao a MESMA pose. Sem isso, tres quadros de respirar passam pelo teste
        de 'anda' tanto quanto tres quadros de passada."""
        if self._mask is None:
            m = self.img.split()[3].point(lambda v: 255 if v >= 128 else 0)
            self._mask = np.array(m.resize((24, 32), Image.NEAREST)) > 0
        return self._mask


def color_like(a, b):
    """Semelhanca de paleta entre dois quadros (cosseno, 0..1)."""
    return float(np.dot(a.rgbsig, b.rgbsig))


def motion(a, b):
    """Fracao de pixels da silhueta que mudam entre dois quadros (0..1)."""
    return float((a.mask != b.mask).mean())


def read_frames(folder, limit):
    """Quadros do personagem, na ordem do arquivo, ja medidos.

    Tres peneiras, nesta ordem:

    1. **tamanho** — acima de 96 px de lado e uma tela/efeito de fundo; abaixo de
       12x20 e faisca, poeira ou o icone do retrato;
    2. **densidade** — abaixo de 10% de preenchimento da caixa e fumaca ou
       fagulhas espalhadas; acima de 75% e uma bola/pedra solida (varios rips
       comecam com dezenas desses);
    Devolve tambem a **altura tipica** do personagem: a MODA das alturas do rip
    (ele aparece em centenas de quadros, cada efeito em poucos). Serve de piso
    para a busca da pose parada — e o que impede rips como o "Naruto 4 Caldas",
    cujos ~70 primeiros arquivos sao bolas de chakra, pedras e fumaca, de eleger
    uma bola como personagem."""
    cand = []
    for name in list_bmps(folder)[:SCAN_FILES]:
        path = os.path.join(folder, name)
        with Image.open(path) as probe:
            if (probe.width > MAX_SIDE or probe.height > MAX_SIDE
                    or probe.width < MIN_SIDE[0] or probe.height < MIN_SIDE[1]):
                continue
        img = load_bmp(path)
        box = img.getbbox()
        if not box:
            continue                          # quadro vazio
        img = img.crop(box)
        if img.width < MIN_SIDE[0] or img.height < MIN_SIDE[1]:
            continue
        f = Frame(frame_no(name), name, img)
        if f.pixels < MIN_PIX or not (FILL[0] <= f.fill <= FILL[1]):
            continue
        cand.append(f)
    if not cand:
        return [], 0
    hs = np.array([f.h for f in cand])
    counts = [(int(((hs >= h - 6) & (hs <= h + 6)).sum()), h) for h in hs]
    return cand[:limit], max(counts)[1]       # empate na moda: a maior altura


# ------------------------------------------------------------------ heuristica
def _runs(idx):
    """Agrupa uma lista crescente de indices em corridas consecutivas."""
    runs, cur = [], []
    for i in idx:
        if cur and i == cur[-1] + 1:
            cur.append(i)
        else:
            if cur:
                runs.append(cur)
            cur = [i]
    if cur:
        runs.append(cur)
    return runs


def _idle_runs(frames, floor, minlen):
    """Corridas de quadros consecutivos com a silhueta quase constante."""
    ok = [i for i, f in enumerate(frames)
          if f.w <= f.h * 0.90 and f.h >= floor]
    out = []
    for run in _runs(ok):
        for a in range(len(run)):
            for b in range(a + minlen, len(run) + 1):
                seg = run[a:b]
                hs = [frames[i].h for i in seg]
                ws = [frames[i].w for i in seg]
                if max(hs) - min(hs) > 4 or max(ws) - min(ws) > 4:
                    continue
                out.append(seg)
    return out


def pick_idle(frames, typical):
    """Pose parada = a animacao de RESPIRAR.

    Marca registrada dela: **varios quadros consecutivos com a silhueta quase
    constante** (altura e largura variando poucos px) e mais alta que larga. E
    bem mais robusto que "o quadro mais alto": um pulo ou um golpe erguido
    tambem e alto, mas nao se repete com a mesma caixa 3, 4, 8 vezes seguidas —
    e uma bola de chakra, que se repete, e quadrada e cai no teste `w <= 0.90h`.

    A busca varre o rip inteiro (nao so o comeco): em varias variacoes o
    personagem so aparece depois de dezenas de quadros de efeito. O piso de
    altura e a moda das alturas do rip menos `H_BAND`.

    Dentro da corrida escolhida fica o quadro **mediano** pelo vao entre os pes —
    o mais tipico da pose, nem o extremo de inspirar nem o de expirar."""
    if not frames:
        return None, None
    floor = typical - H_BAND
    runs = (_idle_runs(frames, floor, 3) or _idle_runs(frames, floor, 2)
            or _idle_runs(frames, 0, 2))
    if not runs:
        i = max(range(len(frames)), key=lambda k: (frames[k].h, -k))
        return i, [i]
    # A PRIMEIRA corrida ganha: o respirar e a primeira silhueta que se repete no
    # rip. Testei tambem "a mais longa" e "a mais estreita" — as duas erram mais:
    # a mais longa pega o ciclo de andar do Kakashi, a mais estreita pega uma
    # pose inclinada do Naruto Kid. Quando a primeira corrida e um "apontar o
    # braco" em loop (Pain), a correcao vai no dicionario OVERRIDES.
    run = min(runs, key=lambda r: (r[0], -len(r)))
    mid = sorted(run, key=lambda i: (frames[i].span, i))[len(run) // 2]
    return mid, run


def _walk_in(frames, idle_i, banned, hi, htol=None):
    """Melhor janela de 3 quadros consecutivos ate o indice `hi`."""
    h0 = frames[idle_i].h
    htol = H_TOL if htol is None else htol
    best = None
    for i in range(min(hi, len(frames) - 2)):
        win = [i, i + 1, i + 2]
        if any(k in banned for k in win):
            continue
        fs = [frames[k] for k in win]
        if any(abs(f.h - h0) > htol for f in fs):
            continue
        if any(f.w > f.h * 1.05 for f in fs):
            continue                  # caixa mais larga que alta = golpe esticado
        base = frames[idle_i]
        if any(f.w > base.w * 1.9 or abs(f.pixels - base.pixels) > 0.45 * base.pixels
               for f in fs):
            continue                  # nuvem de chakra / espada / susanoo: outro bicho
        if any(color_like(f, base) < COLOR_MIN for f in fs):
            continue                  # paleta diferente da do parado: efeito grande
        spans = [f.span for f in fs]
        rng = max(spans) - min(spans)
        if rng < SPAN_MIN:
            continue
        # desenho ideal do passo: contato (vao largo) -> passagem (estreito) ->
        # contato oposto (largo). Vale um bonus, mas nao e obrigatorio.
        mv = min(motion(fs[0], fs[1]), motion(fs[1], fs[2]))
        if mv < 0.03:
            continue                  # mesma pose repetida: e o respirar, nao o andar
        shape = 1.0 if spans[1] == min(spans) else 0.0
        score = min(rng, 14) + 5.0 * shape + 60.0 * min(mv, 0.20) - 0.05 * i
        if best is None or score > best[0]:
            best = (score, win)
    return best[1] if best else None


def pick_walk(frames, idle_i, idle_run):
    """Ciclo de andar: 3 quadros CONSECUTIVOS com a mesma altura do parado
    (+-3 px) e com o **vao entre os pes oscilando** — mesmo criterio do outfit do
    jogador (30_player).

    Procura em tres passadas, da mais exigente para a mais tolerante — nos rips
    MUGEN/JUS o andar vem logo depois do parado e do agachar, e mais adiante so
    ha golpes (que tambem passam no teste de altura e enganariam o criterio):

    1. primeiros ~45 quadros, altura +-3 px (o criterio do 30_player);
    2. primeiros ~45 quadros, altura +-6 px (em varios personagens a cabeca
       abaixa um pouco na passada e o ciclo inteiro cai fora do +-3);
    3. ate o quadro ~120, altura +-6 px."""
    banned = set(idle_run or [])
    return (_walk_in(frames, idle_i, banned, SCAN_NEAR)
            or _walk_in(frames, idle_i, banned, SCAN_NEAR, 2 * H_TOL)
            or _walk_in(frames, idle_i, banned, SCAN_WALK, 2 * H_TOL))


def faces_right(frames, idx):
    """Para que lado o personagem olha: soma a pele do terco superior a
    esquerda e a direita do centro da caixa, nos quadros escolhidos."""
    l = sum(frames[i].skin_l for i in idx)
    r = sum(frames[i].skin_r for i in idx)
    if l + r < 8:
        return True, 0.0                     # sem pele visivel: assume direita
    return r >= l, abs(r - l) / float(l + r)


def pick_back(frames, idle_i):
    """Quadro de COSTAS, se houver: mesma altura do parado, largura parecida e
    praticamente sem pele na cabeca (a nuca esconde o rosto). Raro."""
    base = frames[idle_i]
    ref = (base.skin_l + base.skin_r) / float(max(1, base.head_pix))
    if ref < 0.02:
        return None                          # o parado ja nao mostra pele: sem base
    best = None
    for i, f in enumerate(frames):
        if abs(f.h - base.h) > H_TOL or abs(f.w - base.w) > 6:
            continue
        ratio = (f.skin_l + f.skin_r) / float(max(1, f.head_pix))
        if ratio > 0.15 * ref:
            continue
        if best is None or ratio < best[1]:
            best = (i, ratio)
    return best[0] if best else None


# ------------------------------------------------------------------ montagem
def analyse(folder, lt):
    frames, typical = read_frames(folder, SCAN_WALK)
    if len(frames) < 4:
        return None, "so %d quadros uteis" % len(frames)
    ov = OVERRIDES.get(str(lt), {})
    by_no = {f.no: i for i, f in enumerate(frames)}

    if "idle" in ov and ov["idle"] in by_no:
        idle_i, idle_run = by_no[ov["idle"]], [by_no[ov["idle"]]]
        src_idle = "override"
    else:
        idle_i, idle_run = pick_idle(frames, typical)
        src_idle = "auto"
    if idle_i is None:
        return None, "sem pose parada"

    notes = []
    if "walk" in ov and all(n in by_no for n in ov["walk"]):
        walk = [by_no[n] for n in ov["walk"]]
        src_walk = "override"
    else:
        walk = pick_walk(frames, idle_i, idle_run)
        src_walk = "auto"
    if not walk:
        walk = [idle_i, idle_i, idle_i]
        src_walk = "fallback"
        notes.append("sem ciclo de andar: usa o parado nas 3 fases")

    if "faces" in ov:
        right, conf = ov["faces"] == "right", 1.0
        src_face = "override"
    else:
        right, conf = faces_right(frames, [idle_i] + walk)
        src_face = "auto"
        if conf < 0.15:
            notes.append("lado ambiguo (conf %.2f): assumido %s"
                         % (conf, "direita" if right else "esquerda"))

    back = by_no.get(ov.get("back", -1))
    if back is None:
        notes.append("sem vista de costas: o norte repete o parado")

    return {
        "frames": frames, "idle": idle_i, "walk": walk, "back": back,
        "faces_right": right, "conf": conf, "notes": notes,
        "src": (src_idle, src_walk, src_face),
    }, None


def write_frames(sel, out_dir):
    """Grava os PNGs recortados e devolve o nome de arquivo de cada papel."""
    os.makedirs(out_dir, exist_ok=True)
    names = {}
    todo = [("idle", sel["idle"])] + [("walk%d" % i, k) for i, k in enumerate(sel["walk"])]
    if sel["back"] is not None:
        todo.append(("back", sel["back"]))
    for role, i in todo:
        f = sel["frames"][i]
        name = "%s_%04d.png" % (role, f.no)
        f.img.save(os.path.join(out_dir, name))
        names[role] = name
    return names


def entry_json(lt, info, names, sel):
    """Uma entrada de `creatures` no esquema do imports.json."""
    mir = not sel["faces_right"]

    def q(role):
        return {"src": "../extracted/mugen/%d/%s" % (lt, names[role]), "mirror": True} \
            if mir else "../extracted/mugen/%d/%s" % (lt, names[role])

    idle, walk = q("idle"), [q("walk%d" % i) for i in range(3)]
    north = {"_dir": "norte — vista de costas do material", "idle": q("back"),
             "walk": [q("back")] * 3} if "back" in names else \
            {"_dir": "norte — NAO ha vista de costas no material lateral: repete o parado",
             "idle": idle, "walk": walk}
    f = sel["frames"]
    return {
        "id": lt,
        "name": "mugen_%d_%s" % (lt, re.sub(r"[^a-z0-9]+", "_", info["name"].lower()).strip("_")),
        "tiles": 1,
        "duration": 200,
        "_personagem": info["name"],
        "_quadros": "parado %04d; andar %04d/%04d/%04d; olha para %s%s" % (
            f[sel["idle"]].no, f[sel["walk"][0]].no, f[sel["walk"][1]].no,
            f[sel["walk"][2]].no,
            "a direita" if sel["faces_right"] else "a esquerda (tudo espelhado)",
            ("; " + "; ".join(sel["notes"])) if sel["notes"] else ""),
        "directions": {
            "0": north,
            "1": {"_dir": "leste — perfil olhando para a direita", "idle": idle, "walk": walk},
            "2": {"_dir": "sul — o material e lateral: mesmo perfil do leste",
                  "idle": idle, "walk": walk},
            "3": {"_dir": "oeste — espelho do leste", "mirror_of": 1},
        },
    }


# ------------------------------------------------------------------ revisao
def _cell(img, box, scale):
    """Reproduz o encaixe do imports.fit_uniform, para a revisao mostrar o que
    o build vai gravar de verdade."""
    import imports as I
    return I.fit_uniform(img, box, scale)


def review_sheet(lt, info, sel, names):
    """idle + 3 fases de andar nas 4 direcoes, ampliado 3x."""
    import imports as I
    box, zoom = 32, 3
    f = sel["frames"]
    mir = not sel["faces_right"]
    roles = [("idle", sel["idle"])] + [("walk%d" % i, k) for i, k in enumerate(sel["walk"])]
    back = sel["back"]
    cols = [                                   # (rotulo, [(img, mirror) x4])
        ("N", [(f[back].img if back is not None else f[i].img, mir) for _, i in roles]),
        ("L", [(f[i].img, mir) for _, i in roles]),
        ("S", [(f[i].img, mir) for _, i in roles]),
        ("O", [(f[i].img, not mir) for _, i in roles]),
    ]
    allimgs = [im for _, col in cols for im, _ in col]
    scale = min(box / float(max(i.width for i in allimgs)),
                box / float(max(i.height for i in allimgs)), 1.0)
    pad, head = 4, 16
    W = len(cols) * (box * zoom + pad) + pad
    H = head + 4 * (box * zoom + pad) + pad + 14
    sh = Image.new("RGBA", (W, H), (28, 28, 34, 255))
    d = ImageDraw.Draw(sh)
    d.text((pad, 3), "%d %s  parado %04d  andar %04d/%04d/%04d  %s" % (
        lt, info["name"], f[sel["idle"]].no, f[sel["walk"][0]].no,
        f[sel["walk"][1]].no, f[sel["walk"][2]].no,
        "->" if sel["faces_right"] else "<- (espelhado)"), fill=(255, 235, 120, 255))
    for c, (lab, col) in enumerate(cols):
        x = pad + c * (box * zoom + pad)
        for r, (im, m) in enumerate(col):
            y = head + r * (box * zoom + pad)
            cell = I.fit_uniform(im, box, scale, m)
            bg = Image.new("RGBA", (box, box), (70, 70, 78, 255))
            bg.alpha_composite(cell)
            sh.paste(bg.resize((box * zoom, box * zoom), Image.NEAREST), (x, y))
        d.text((x + 2, H - 12), lab + " " + ("parado/andar" if c == 0 else ""),
               fill=(190, 190, 200, 255))
    return sh


def general_sheet(rows):
    """Uma linha por personagem: parado + as 3 fases (leste), ampliado 2x."""
    import imports as I
    box, zoom, pad = 32, 2, 3
    cw = box * zoom + pad
    W = 150 + 4 * cw
    H = pad + len(rows) * (box * zoom + pad)
    sh = Image.new("RGBA", (W, H), (28, 28, 34, 255))
    d = ImageDraw.Draw(sh)
    for r, (lt, info, sel) in enumerate(rows):
        y = pad + r * (box * zoom + pad)
        f = sel["frames"]
        mir = not sel["faces_right"]
        imgs = [f[sel["idle"]].img] + [f[k].img for k in sel["walk"]]
        scale = min(box / float(max(i.width for i in imgs)),
                    box / float(max(i.height for i in imgs)), 1.0)
        d.text((4, y + 12), "%d %s" % (lt, info["name"][:20]), fill=(255, 235, 120, 255))
        for c, im in enumerate(imgs):
            bg = Image.new("RGBA", (box, box), (70, 70, 78, 255))
            bg.alpha_composite(I.fit_uniform(im, box, scale, mir))
            sh.paste(bg.resize((box * zoom, box * zoom), Image.NEAREST),
                     (150 + c * cw, y))
    return sh


# ------------------------------------------------------------------ principal
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", nargs="*", type=int, help="so estes looktypes")
    ap.add_argument("--report", action="store_true",
                    help="so imprime o diagnostico, nao grava nada")
    ap.add_argument("--no-review", action="store_true", help="nao gerar as folhas")
    args = ap.parse_args()

    with open(os.path.join(ROOT, LOOKTYPES), encoding="utf-8") as fh:
        table = json.load(fh)["looktypes"]

    creatures, rows, warn = [], [], []
    for key in sorted(table, key=int):
        lt = int(key)
        if args.only and lt not in args.only:
            continue
        info = table[key]
        folder = os.path.join(ROOT, SRC_ROOT, info["folder"])
        if not os.path.isdir(folder):
            warn.append("%d %s: pasta ausente (%s)" % (lt, info["name"], info["folder"]))
            continue
        sel, err = analyse(folder, lt)
        if sel is None:
            warn.append("%d %s: %s" % (lt, info["name"], err))
            continue
        f = sel["frames"]
        print("%3d %-20s parado %4d (h%2d) andar %4d/%4d/%4d vao %2d/%2d/%2d "
              "olha %s conf %.2f costas %s [%s/%s/%s]%s" % (
                  lt, info["name"][:20], f[sel["idle"]].no, f[sel["idle"]].h,
                  f[sel["walk"][0]].no, f[sel["walk"][1]].no, f[sel["walk"][2]].no,
                  f[sel["walk"][0]].span, f[sel["walk"][1]].span, f[sel["walk"][2]].span,
                  "->" if sel["faces_right"] else "<-", sel["conf"],
                  f[sel["back"]].no if sel["back"] is not None else "-",
                  sel["src"][0][:4], sel["src"][1][:4], sel["src"][2][:4],
                  ("  ! " + "; ".join(sel["notes"])) if sel["notes"] else ""))
        rows.append((lt, info, sel))
        if args.report:
            continue
        names = write_frames(sel, os.path.join(ROOT, OUT_ROOT, str(lt)))
        creatures.append(entry_json(lt, info, names, sel))
        if not args.no_review:
            review_sheet(lt, info, sel, names).save(
                os.path.join(ROOT, OUT_ROOT, "_review_%d.png" % lt))

    for w in warn:
        print("AVISO:", w)
    if args.report:
        return

    if rows and not args.no_review:
        general_sheet(rows).save(os.path.join(ROOT, OUT_ROOT, "_review_all.png"))

    out = os.path.join(ROOT, OVERRIDE)
    if args.only and os.path.exists(out):          # merge: nao perde os outros
        with open(out, encoding="utf-8") as fh:
            old = json.load(fh)
        keep = [c for c in old.get("creatures", [])
                if c["id"] not in {c2["id"] for c2 in creatures}]
        creatures = sorted(creatures + keep, key=lambda c: c["id"])
    doc = {
        "_doc": ("Outfits dos personagens MUGEN (looktypes 900..926), GERADO por "
                 "tools/spr/import_mugen.py a partir do material privado em "
                 "assets-src/import/mugen (fora do git, ADR-002). Nao edite a mao: "
                 "ajuste a heuristica ou o dicionario OVERRIDES do script e rode de "
                 "novo. Toda entrada cujo PNG nao existir e ignorada com aviso, "
                 "entao numa maquina sem o material o build cai no placeholder."),
        "format": 1,
        "root": SRC_ROOT,
        "build_dir": OUT_ROOT + "/_sheets",
        "_doc_root": ("'root' aponta para o material bruto; os quadros JA "
                      "RECORTADOS ficam em assets-src/import/extracted/mugen/<looktype>/, "
                      "por isso os 'src' comecam com '../extracted/'."),
        "_doc_creatures": ("Mesmo esquema do overrides/30_player.json: 'directions' "
                           "0=Norte 1=Leste 2=Sul 3=Oeste, 'idle' = frame group 0 "
                           "(1 fase), 'walk' = frame group 1 (3 fases), 'mirror_of' "
                           "espelha outra direcao, layers=1 (a arte ja vem colorida). "
                           "O material e LATERAL: N/L/S usam o mesmo perfil e so o "
                           "oeste e espelhado."),
        "creatures": creatures,
    }
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("\n%d criaturas -> %s" % (len(creatures), OVERRIDE))


if __name__ == "__main__":
    main()
