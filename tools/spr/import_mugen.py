#!/usr/bin/env python3
"""Gera os outfits dos personagens MUGEN (looktypes 900..926).

MATERIAL (privado, fora do git — ADR-002): ``assets-src/import/mugen/<Personagem>/
[<Variacao>/]<nome>_NNNN.bmp`` — rips estilo MUGEN/JUS de um jogo de luta. Sao
BMPs paletados (modo ``P``) em que o **indice 0 da paleta e a cor-chave** de fundo
(a cor concreta varia por quadro: verde escuro, verde neon...). A vista e
**LATERAL**: o personagem olha para a direita ou para a esquerda, nunca de frente
nem de costas — confirmado pela varredura EXAUSTIVA (``survey_mugen.py``, todo
quadro do rip, nao so os primeiros ~200): a "vista de costas" nao existe em
NENHUM dos 27 personagens, so blobs de efeito (chakra, fumaca) sao classificados
como tal por falta de pele visivel. Por isso este script agora **sintetiza** a
vista de costas (``char_synth.synthesize_back``) em vez de so repetir o parado.

O layout dos rips e razoavelmente estavel: 0 = icone pequeno, 1 = retrato grande
(120x140), depois a pose **parada** (respirando), agachar, **andar**, correr,
pular e por fim dezenas de golpes. Este script nao confia nessa ordem: ele mede
cada quadro e escolhe por heuristica (ver ``pick_idle`` / ``pick_walk4``).

Saidas:

* ``assets-src/import/extracted/mugen/<looktype>/{idle,walk0..3,back_idle,
  back_walk0..3}.png`` — os quadros escolhidos/sintetizados, ja em RGBA;
* ``assets-src/import/extracted/mugen/_review_<looktype>.png`` — folha de
  revisao (parado + 4 fases de andar, N/L/S/O, ampliada 3x, ja passada pelo
  `fit_uniform` = o que o build vai gravar de verdade);
* ``assets-src/import/extracted/mugen/_review_all.png`` — folha geral;
* ``assets-src/sprites/mugen_frames.json`` — registro VERSIONADO da escolha
  final por personagem (idle/andar/costas/frente, cores de pele/cabelo, notas);
* ``assets-src/sprites/overrides/40_mugen.json`` — o que o build le de verdade;
  mesmo esquema do ``imports.json``, ignora com aviso toda entrada cujo PNG nao
  exista.

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

import char_synth as CS  # noqa: E402

LOOKTYPES = "assets-src/sprites/mugen_looktypes.json"
SRC_ROOT = "assets-src/import/mugen"
OUT_ROOT = "assets-src/import/extracted/mugen"
OVERRIDE = "assets-src/sprites/overrides/40_mugen.json"
FRAMES_DOC = "assets-src/sprites/mugen_frames.json"

MAX_SIDE = 96          # acima disso nao e o personagem (telas, efeitos de fundo)
MIN_SIDE = (12, 20)    # abaixo disso e faisca, poeira, icone
MIN_PIX = 60           # quadro praticamente vazio
FILL = (0.10, 0.75)    # densidade da caixa: <10% e poeira, >75% e uma bola solida
H_BAND = 14            # quanto a altura pode fugir da altura tipica do personagem
COLOR_MIN = 0.80       # semelhanca minima de paleta entre o andar e o parado
SCAN_ALL = 999999      # SEM TETO: varredura exaustiva (mission item 1)
SCAN_EARLY = 30        # ate onde uma corrida ainda conta como "comeco do rip"
SCAN_NEAR = 45         # onde o andar costuma estar (logo apos o parado)
SCAN_WALK = 120        # ate onde procurar o andar antes de abrir mao de vez
H_TOL = 3              # tolerancia de altura idle <-> walk (px)
SPAN_MIN = 3           # variacao minima do vao entre os pes para valer como passo

# Formas de bicho/quadrupede: a sintese de costas (repintar "rosto") nao faz
# sentido (nao ha rosto reconhecivel, e chakra/pelagem) — so escurece.
NO_FACE_SYNTH = {921, 922, 923, 926}


# ------------------------------------------------------------------ overrides
# Selecoes manuais, aplicadas quando a heuristica erra. Os numeros sao o NNNN do
# nome do arquivo (nao o indice na lista), para nao dependerem da filtragem.
#
#   "<looktype>": {"idle": N, "walk": [a, b, c, d?], "faces": "left"|"right",
#                   "front": N}
#
# Qualquer chave e opcional: o que nao estiver aqui continua vindo da heuristica.
# "walk" com 3 numeros ganha uma 4a fase SINTETICA (synth_walk_offset); com 4,
# usa os 4 quadros reais.
OVERRIDES = {
    # --- rips SEM ciclo de andar: o material tem parado, agachar, pular e
    #     golpes, e mais nada. Uso as proprias fases do RESPIRAR como andar
    #     (a 4a fase sintetica ajuda a nao ficar so "respirando" parado):
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


def classify_orientation(f):
    """frente / perfil_direita / perfil_esquerda / 3/4 / costas, pela pele do
    terco superior (mesma logica de survey_mugen.py — replicada aqui para nao
    criar import circular)."""
    total = f.skin_l + f.skin_r
    ratio = total / float(max(1, f.head_pix))
    if ratio < 0.015:
        return "costas"
    asym = abs(f.skin_l - f.skin_r) / float(total) if total else 1.0
    if asym < 0.20:
        return "frente"
    if asym < 0.55:
        return "3/4"
    return "perfil_direita" if f.skin_r > f.skin_l else "perfil_esquerda"


def read_frames(folder, limit=SCAN_ALL):
    """Quadros do personagem, na ordem do arquivo, ja medidos — VARREDURA
    EXAUSTIVA (sem teto de arquivos: mission item 1 pede o rip inteiro, nao so
    os primeiros ~200).

    Tres peneiras, nesta ordem:

    1. **tamanho** — acima de 96 px de lado e uma tela/efeito de fundo; abaixo de
       12x20 e faisca, poeira ou o icone do retrato;
    2. **densidade** — abaixo de 10% de preenchimento da caixa e fumaca ou
       fagulhas espalhadas; acima de 75% e uma bola/pedra solida (varios rips
       comecam com dezenas desses);
    Devolve tambem a **altura tipica** do personagem: a MODA das alturas do rip
    (ele aparece em centenas de quadros, cada efeito em poucos)."""
    cand = []
    for name in list_bmps(folder)[:limit]:
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
    return cand, max(counts)[1]


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
    """Pose parada = a animacao de RESPIRAR (ver docstring do modulo antigo:
    varias corridas de silhueta quase constante; a PRIMEIRA ganha)."""
    if not frames:
        return None, None
    floor = typical - H_BAND
    runs = (_idle_runs(frames, floor, 3) or _idle_runs(frames, floor, 2)
            or _idle_runs(frames, 0, 2))
    if not runs:
        i = max(range(len(frames)), key=lambda k: (frames[k].h, -k))
        return i, [i]
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
            continue
        base = frames[idle_i]
        if any(f.w > base.w * 1.9 or abs(f.pixels - base.pixels) > 0.45 * base.pixels
               for f in fs):
            continue
        if any(color_like(f, base) < COLOR_MIN for f in fs):
            continue
        spans = [f.span for f in fs]
        rng = max(spans) - min(spans)
        if rng < SPAN_MIN:
            continue
        mv = min(motion(fs[0], fs[1]), motion(fs[1], fs[2]))
        if mv < 0.03:
            continue
        shape = 1.0 if spans[1] == min(spans) else 0.0
        score = min(rng, 14) + 5.0 * shape + 60.0 * min(mv, 0.20) - 0.05 * i
        if best is None or score > best[0]:
            best = (score, win)
    return best[1] if best else None


def _walk4_in(frames, idle_i, banned, hi, htol=None):
    """Melhor janela de 4 quadros CONSECUTIVOS: contato-passagem-contato-
    passagem (2 alternancias do vao entre os pes), mesmos criterios do `_walk_in`
    mas exigindo um ciclo mais completo — e o que da as 4 fases REAIS quando o
    rip tem material suficiente (mission item 3: >=4 fases por direcao)."""
    h0 = frames[idle_i].h
    htol = H_TOL if htol is None else htol
    best = None
    for i in range(min(hi, len(frames) - 3)):
        win = [i, i + 1, i + 2, i + 3]
        if any(k in banned for k in win):
            continue
        fs = [frames[k] for k in win]
        if any(abs(f.h - h0) > htol for f in fs):
            continue
        if any(f.w > f.h * 1.05 for f in fs):
            continue
        base = frames[idle_i]
        if any(f.w > base.w * 1.9 or abs(f.pixels - base.pixels) > 0.45 * base.pixels
               for f in fs):
            continue
        if any(color_like(f, base) < COLOR_MIN for f in fs):
            continue
        spans = [f.span for f in fs]
        rng = max(spans) - min(spans)
        if rng < SPAN_MIN:
            continue
        mvs = [motion(fs[j], fs[j + 1]) for j in range(3)]
        if min(mvs) < 0.03:
            continue
        turns = sum(1 for j in range(1, 3)
                    if (spans[j] - spans[j - 1]) * (spans[j + 1] - spans[j]) < 0)
        score = min(rng, 14) + 8.0 * turns + 60.0 * min(min(mvs), 0.20) - 0.03 * i
        if best is None or score > best[0]:
            best = (score, win)
    return best[1] if best else None


def pick_walk(frames, idle_i, idle_run, want4=True):
    """Ciclo de andar. Tenta primeiro 4 fases REAIS (passadas da mais exigente
    para a mais tolerante); se nao houver material, cai para 3 fases (o
    criterio antigo, ainda o mais confiavel para o material MUGEN) — e quem
    chama completa a 4a fase por sintese (`char_synth.synth_walk_offset`).

    Devolve (lista_de_indices, "real4"|"real3"|None)."""
    banned = set(idle_run or [])
    if want4:
        w4 = (_walk4_in(frames, idle_i, banned, SCAN_NEAR)
              or _walk4_in(frames, idle_i, banned, SCAN_NEAR, 2 * H_TOL)
              or _walk4_in(frames, idle_i, banned, SCAN_WALK, 2 * H_TOL)
              or _walk4_in(frames, idle_i, banned, len(frames), 2 * H_TOL))
        if w4:
            return w4, "real4"
    w3 = (_walk_in(frames, idle_i, banned, SCAN_NEAR)
          or _walk_in(frames, idle_i, banned, SCAN_NEAR, 2 * H_TOL)
          or _walk_in(frames, idle_i, banned, SCAN_WALK, 2 * H_TOL))
    if w3:
        return w3, "real3"
    return None, None


def faces_right(frames, idx):
    """Para que lado o personagem olha: soma a pele do terco superior a
    esquerda e a direita do centro da caixa, nos quadros escolhidos."""
    l = sum(frames[i].skin_l for i in idx)
    r = sum(frames[i].skin_r for i in idx)
    if l + r < 8:
        return True, 0.0                     # sem pele visivel: assume direita
    return r >= l, abs(r - l) / float(l + r)


def pick_front(frames, idle_i, banned=()):
    """Candidato a "quadro de FRENTE" para a direcao Sul, em TODO o rip: melhor
    quadro classificado como `frente` ou `3/4` (orientacao), com altura parecida
    com o parado, paleta parecida (nao e um efeito) e nao gigante — mission item
    2: "escolha o quadro de 3/4 se existir ou o idle frontal do rip".

    Muitos rips tem uma pose de vitoria/intro de frente perto do comeco; a busca
    e no rip INTEIRO porque a posicao varia demais para confiar num intervalo
    fixo. Devolve (indice, orientacao) ou (None, None) se nao houver nada bom —
    nesse caso o Sul cai para o mesmo perfil do Leste (como antes)."""
    base = frames[idle_i]
    banned = set(banned)
    best = None
    for i, f in enumerate(frames):
        if i in banned:
            continue                          # mesma corrida do parado: nao e "outra" pose
        if abs(f.h - base.h) > 2 * H_TOL:
            continue
        if f.w > base.w * 1.6:
            continue
        orient = classify_orientation(f)
        if orient not in ("frente", "3/4"):
            continue
        cl = color_like(f, base)
        if cl < 0.55:
            continue
        mv = motion(f, base)
        if mv < 0.05:
            continue                          # quase identico ao parado: nao ajuda
        score = (2.0 if orient == "frente" else 1.0) + cl - 0.6 * mv
        if best is None or score > best[0]:
            best = (score, i, orient)
    return (best[1], best[2]) if best else (None, None)


# ------------------------------------------------------------------ montagem
def analyse(folder, lt):
    frames, typical = read_frames(folder)
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
    walk_kind = "auto4"
    if "walk" in ov and all(n in by_no for n in ov["walk"]):
        walk = [by_no[n] for n in ov["walk"]]
        src_walk = "override"
        walk_kind = "real4" if len(walk) >= 4 else "real3"
    else:
        walk, walk_kind = pick_walk(frames, idle_i, idle_run)
        src_walk = "auto"
    if not walk:
        walk = [idle_i, idle_i, idle_i]
        walk_kind = "none"
        src_walk = "fallback"
        notes.append("sem ciclo de andar: 4 fases SINTETIZADAS a partir do parado")
    elif len(walk) == 3:
        notes.append("so 3 fases reais de andar: 4a fase SINTETIZADA (deslocamento de pernas)")

    if "faces" in ov:
        right, conf = ov["faces"] == "right", 1.0
        src_face = "override"
    else:
        right, conf = faces_right(frames, [idle_i] + walk)
        src_face = "auto"
        if conf < 0.15:
            notes.append("lado ambiguo (conf %.2f): assumido %s"
                         % (conf, "direita" if right else "esquerda"))

    if "front" in ov and ov["front"] in by_no:
        front_i, front_orient = by_no[ov["front"]], "override"
    else:
        banned_front = set(idle_run or []) | set(walk) | {idle_i}
        front_i, front_orient = pick_front(frames, idle_i, banned_front)
    if front_i is None:
        notes.append("sem quadro de frente/3-4 no rip: Sul repete o perfil (Leste)")
    else:
        notes.append("Sul = quadro %s (arquivo %04d, classificado '%s')"
                     % ("de frente" if front_orient == "frente" else "3/4 virado",
                        frames[front_i].no, front_orient))

    skin_rgb, hair_rgb = CS.estimate_colors(
        [frames[idle_i].img] + [frames[k].img for k in walk[:3]])
    notes.append("sintese de costas: pele~%s cabelo~%s" % (skin_rgb, hair_rgb))

    return {
        "frames": frames, "idle": idle_i, "walk": walk, "walk_kind": walk_kind,
        "front": front_i, "faces_right": right, "conf": conf, "notes": notes,
        "src": (src_idle, src_walk, src_face), "skin_rgb": skin_rgb, "hair_rgb": hair_rgb,
    }, None


def _walk4_images(sel):
    """4 imagens (PIL) da fase de andar, na ORDEM certa, completando por
    sintese quando o real so deu 3 (ou 0) fases."""
    frames, walk = sel["frames"], sel["walk"]
    imgs = [frames[k].img for k in walk]
    if sel["walk_kind"] in ("real4",):
        return imgs[:4]
    if sel["walk_kind"] == "real3":
        # contato-L, passagem, contato-R + passagem-2 sintetica (deslocamento
        # oposto da passagem real, para nao repetir a mesma silhueta 2x)
        extra = CS.synth_walk_offset(imgs[1], leg_dx=-2, body_dy=1, shear=-1)
        return imgs[:3] + [extra]
    # "none"/fallback: idle vira as 4 fases via pequenos deslocamentos
    idle_img = frames[sel["idle"]].img
    return [
        idle_img,
        CS.synth_walk_offset(idle_img, leg_dx=2, body_dy=-1, shear=1),
        CS.synth_walk_offset(idle_img, leg_dx=0, body_dy=-2, shear=0),
        CS.synth_walk_offset(idle_img, leg_dx=-2, body_dy=-1, shear=-1),
    ]


def write_frames(sel, out_dir, lt):
    """Grava os PNGs recortados/sintetizados e devolve o nome de arquivo de
    cada papel (idle, walk0..3, back_idle, back_walk0..3, front_idle?)."""
    os.makedirs(out_dir, exist_ok=True)
    names = {}
    frames = sel["frames"]

    idle_img = frames[sel["idle"]].img
    idle_img.save(os.path.join(out_dir, "idle_%04d.png" % frames[sel["idle"]].no))
    names["idle"] = "idle_%04d.png" % frames[sel["idle"]].no

    walk_imgs = _walk4_images(sel)
    n_real = {"real4": 4, "real3": 3, None: 0}.get(sel["walk_kind"], 0)
    for i, im in enumerate(walk_imgs):
        if i < n_real:
            name = "walk%d_%04d.png" % (i, frames[sel["walk"][i]].no)
        else:
            name = "walk%d_synth.png" % i
        im.save(os.path.join(out_dir, name))
        names["walk%d" % i] = name

    hair_rgb = sel["hair_rgb"]
    darken = 0.86
    if lt in NO_FACE_SYNTH:
        # bicho/quadrupede: so escurece, sem tentar apagar "rosto" (nao ha)
        back_idle = CS.synthesize_back(idle_img, hair_rgb, mirror=False, darken=0.80, head_frac=0.0)
        back_walks = [CS.synthesize_back(im, hair_rgb, mirror=False, darken=0.80, head_frac=0.0)
                      for im in walk_imgs]
    else:
        back_idle = CS.synthesize_back(idle_img, hair_rgb, mirror=True, darken=darken)
        back_walks = [CS.synthesize_back(im, hair_rgb, mirror=True, darken=darken) for im in walk_imgs]
    back_idle.save(os.path.join(out_dir, "back_idle.png"))
    names["back_idle"] = "back_idle.png"
    for i, im in enumerate(back_walks):
        im.save(os.path.join(out_dir, "back_walk%d.png" % i))
        names["back_walk%d" % i] = "back_walk%d.png" % i

    if sel["front"] is not None:
        f = frames[sel["front"]]
        f.img.save(os.path.join(out_dir, "front_%04d.png" % f.no))
        names["front"] = "front_%04d.png" % f.no

    return names


def entry_json(lt, info, names, sel):
    """Uma entrada de `creatures` no esquema do imports.json."""
    mir = not sel["faces_right"]

    def q(role, force_mirror=None):
        m = mir if force_mirror is None else force_mirror
        return {"src": "../extracted/mugen/%d/%s" % (lt, names[role]), "mirror": True} \
            if m else "../extracted/mugen/%d/%s" % (lt, names[role])

    idle = q("idle")
    walk = [q("walk%d" % i) for i in range(4)]
    # sintese de costas: ja fizemos synthesize_back(mirror=True) EM CIMA da
    # imagem original (que ainda esta no "lado" faces_right) — entao o PNG
    # gravado ja esta espelhado fisicamente; aqui NAO aplicamos mirror de novo.
    back_idle = "../extracted/mugen/%d/%s" % (lt, names["back_idle"])
    back_walk = ["../extracted/mugen/%d/%s" % (lt, names["back_walk%d" % i]) for i in range(4)]

    if "front" in names:
        # o quadro de frente ja foi escolhido pela propria orientacao (frente/
        # 3-4); nao repete o espelhamento do perfil, que e outro "lado"
        south_idle = "../extracted/mugen/%d/%s" % (lt, names["front"])
    else:
        south_idle = idle

    f = sel["frames"]
    walk_desc = "/".join("%04d" % f[k].no for k in sel["walk"][:3])
    return {
        "id": lt,
        "name": "mugen_%d_%s" % (lt, re.sub(r"[^a-z0-9]+", "_", info["name"].lower()).strip("_")),
        "tiles": 1,
        "duration": 200,
        "_personagem": info["name"],
        "_quadros": "parado %04d; andar %s (%s); olha para %s%s" % (
            f[sel["idle"]].no, walk_desc, sel["walk_kind"],
            "a direita" if sel["faces_right"] else "a esquerda (tudo espelhado)",
            ("; " + "; ".join(sel["notes"])) if sel["notes"] else ""),
        "directions": {
            "0": {"_dir": "norte — vista de COSTAS SINTETIZADA (mirror + repintura "
                          "da regiao do rosto na cor do cabelo + escurecimento; ver "
                          "char_synth.synthesize_back). O rip nao tem costas real.",
                  "idle": back_idle, "walk": back_walk},
            "1": {"_dir": "leste — perfil olhando para a direita", "idle": idle, "walk": walk},
            "2": {"_dir": "sul — %s" % ("quadro de frente/3-4 do proprio rip"
                                        if "front" in names else
                                        "o material e lateral: mesmo perfil do leste"),
                  "idle": south_idle, "walk": walk},
            "3": {"_dir": "oeste — espelho do leste", "mirror_of": 1},
        },
    }


def frames_doc_entry(lt, info, sel):
    f = sel["frames"]
    return {
        "looktype": lt, "nome": info["name"],
        "idle_frame": f[sel["idle"]].no,
        "walk_frames": [f[k].no for k in sel["walk"]],
        "walk_kind": sel["walk_kind"],
        "faces_right": sel["faces_right"], "face_conf": round(sel["conf"], 2),
        "front_frame": f[sel["front"]].no if sel["front"] is not None else None,
        "skin_rgb": list(sel["skin_rgb"]), "hair_rgb": list(sel["hair_rgb"]),
        "notas": sel["notes"],
    }


# ------------------------------------------------------------------ revisao
def review_sheet(lt, info, sel, names):
    """idle + 4 fases de andar nas 4 direcoes (agora com costas sintetizada e,
    quando existe, frente real), ampliado 3x."""
    import imports as I
    box, zoom = 32, 3
    walk_imgs = _walk4_images(sel)
    idle_img = sel["frames"][sel["idle"]].img
    mir = not sel["faces_right"]

    # recarrega as imagens ja gravadas (evita duplicar a logica de sintese)
    out_dir = names["_out_dir"]
    back_idle = Image.open(os.path.join(out_dir, names["back_idle"]))
    back_walks = [Image.open(os.path.join(out_dir, names["back_walk%d" % i])) for i in range(4)]
    south_idle = Image.open(os.path.join(out_dir, names["front"])) if "front" in names else idle_img

    cols = [
        ("N", [(back_idle, False)] + [(im, False) for im in back_walks]),
        ("L", [(idle_img, mir)] + [(im, mir) for im in walk_imgs]),
        ("S", [(south_idle, False if "front" in names else mir)] + [(im, mir) for im in walk_imgs]),
        ("O", [(idle_img, not mir)] + [(im, not mir) for im in walk_imgs]),
    ]
    allimgs = [im for _, col in cols for im, _ in col]
    scale = min(box / float(max(i.width for i in allimgs)),
                box / float(max(i.height for i in allimgs)), 1.0)
    pad, head = 4, 16
    W = len(cols) * (box * zoom + pad) + pad
    H = head + 5 * (box * zoom + pad) + pad + 14
    sh = Image.new("RGBA", (W, H), (28, 28, 34, 255))
    d = ImageDraw.Draw(sh)
    d.text((pad, 3), "%d %s  parado+4 andar  %s  %s" % (
        lt, info["name"], "->" if sel["faces_right"] else "<- (espelhado)",
        sel["walk_kind"]), fill=(255, 235, 120, 255))
    for c, (lab, col) in enumerate(cols):
        x = pad + c * (box * zoom + pad)
        for r, (im, m) in enumerate(col):
            y = head + r * (box * zoom + pad)
            cell = I.fit_uniform(im, box, scale, m)
            bg = Image.new("RGBA", (box, box), (70, 70, 78, 255))
            bg.alpha_composite(cell)
            sh.paste(bg.resize((box * zoom, box * zoom), Image.NEAREST), (x, y))
        d.text((x + 2, H - 12), lab, fill=(190, 190, 200, 255))
    return sh


def general_sheet(rows):
    """Uma linha por personagem: parado + as 4 fases (leste), ampliado 2x."""
    import imports as I
    box, zoom, pad = 32, 2, 3
    cw = box * zoom + pad
    W = 150 + 5 * cw
    H = pad + len(rows) * (box * zoom + pad)
    sh = Image.new("RGBA", (W, H), (28, 28, 34, 255))
    d = ImageDraw.Draw(sh)
    for r, (lt, info, sel) in enumerate(rows):
        y = pad + r * (box * zoom + pad)
        mir = not sel["faces_right"]
        imgs = [sel["frames"][sel["idle"]].img] + _walk4_images(sel)
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

    creatures, rows, warn, frames_doc = [], [], [], {}
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
        print("%3d %-20s parado %4d (h%2d) andar[%s] %s frente=%s olha %s conf %.2f [%s/%s/%s]%s" % (
            lt, info["name"][:20], f[sel["idle"]].no, f[sel["idle"]].h,
            "/".join("%04d" % f[k].no for k in sel["walk"]), sel["walk_kind"],
            (f[sel["front"]].no if sel["front"] is not None else "-"),
            "->" if sel["faces_right"] else "<-", sel["conf"],
            sel["src"][0][:4], sel["src"][1][:4], sel["src"][2][:4],
            ("  ! " + "; ".join(sel["notes"])) if sel["notes"] else ""))
        rows.append((lt, info, sel))
        frames_doc[str(lt)] = frames_doc_entry(lt, info, sel)
        if args.report:
            continue
        out_dir = os.path.join(ROOT, OUT_ROOT, str(lt))
        names = write_frames(sel, out_dir, lt)
        names["_out_dir"] = out_dir
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

    # ---- mugen_frames.json (registro versionado da escolha final)
    frames_path = os.path.join(ROOT, FRAMES_DOC)
    if args.only and os.path.exists(frames_path):
        with open(frames_path, encoding="utf-8") as fh:
            old_doc = json.load(fh)
        old_ch = old_doc.get("personagens", {})
        old_ch.update(frames_doc)
        frames_doc = old_ch
    with open(frames_path, "w", encoding="utf-8") as fh:
        json.dump({
            "_doc": ("Registro VERSIONADO da escolha final de quadros por personagem "
                     "MUGEN (900-926), gerado por tools/spr/import_mugen.py a partir da "
                     "varredura de survey_mugen.py + heuristica deste script. So indices "
                     "e metadados (nenhuma imagem) — quem o build le de verdade e "
                     "overrides/40_mugen.json."),
            "format": 1,
            "personagens": {k: frames_doc[k] for k in sorted(frames_doc, key=int)},
        }, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    # ---- overrides/40_mugen.json (o que o build le)
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
                 "entao numa maquina sem o material o build cai no placeholder. "
                 "A escolha por personagem tambem fica documentada (com indices e "
                 "notas) em assets-src/sprites/mugen_frames.json."),
        "format": 1,
        "root": SRC_ROOT,
        "build_dir": OUT_ROOT + "/_sheets",
        "_doc_root": ("'root' aponta para o material bruto; os quadros JA "
                      "RECORTADOS/SINTETIZADOS ficam em "
                      "assets-src/import/extracted/mugen/<looktype>/, por isso os "
                      "'src' comecam com '../extracted/'."),
        "_doc_creatures": ("Mesmo esquema do overrides/30_player.json: 'directions' "
                           "0=Norte 1=Leste 2=Sul 3=Oeste, 'idle' = frame group 0 "
                           "(1 fase), 'walk' = frame group 1 (4 fases), 'mirror_of' "
                           "espelha outra direcao, layers=1 (a arte ja vem colorida). "
                           "Norte agora e uma vista de COSTAS SINTETIZADA (nao existe "
                           "no material); Sul usa um quadro de frente/3-4 do proprio "
                           "rip quando a heuristica acha um bom candidato, senao repete "
                           "o perfil do Leste."),
        "creatures": creatures,
    }
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("\n%d criaturas -> %s" % (len(creatures), OVERRIDE))
    print("%d personagens -> %s" % (len(frames_doc), FRAMES_DOC))


if __name__ == "__main__":
    main()
