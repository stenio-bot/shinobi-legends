#!/usr/bin/env python3
"""Varredura EXAUSTIVA dos 26 personagens MUGEN: classifica TODO quadro util de
cada rip por (orientacao, pose) e gera uma folha de revisao por personagem.

Nao seleciona a arte final (isso e ``import_mugen.py`` + ``mugen_frames.json``);
so PROPOE candidatos, numerados, para o artista (eu) olhar com ``Read`` e decidir.

Heuristicas (best-effort; ver docs/sistemas/arte-e-sprites.md secao "Personagens
MUGEN — varredura exaustiva"):

* **orientacao** — pele (rosto) no terco superior da caixa: `perfil_esquerda` /
  `perfil_direita` quando concentrada de um lado, `frente` quando simetrica entre
  os dois lados, `costas` quando quase ausente, `3/4` no meio-termo.
* **pose** — combinacao de altura relativa ao "parado" do personagem, largura
  relativa a altura (golpes/corrida esticam a caixa na horizontal), MOVIMENTO
  entre quadros vizinhos (silhueta muda pouco = parado/andar, muda muito = golpe/
  especial) e posicao no arquivo (poses de vitoria/intro tendem a vir logo no
  comeco do rip). Poses alem de parado/andar (correr, pular, ataque, especial,
  dano, vitoria) sao PROPOSTAS, nao fatos — a palavra final e a inspecao visual.

Saidas (tudo em assets-src/import/extracted/mugen/, privado):

* ``_survey_<looktype>.png``  — folha de revisao: uma linha por orientacao,
  colunas = pose, celula = melhor candidato (numero do arquivo abaixo);
* ``_survey_<looktype>.json`` — classificacao crua de cada quadro (para uso
  programatico por import_mugen.py), com os clusters de pele/cabelo estimados.

Uso::

    .venv/bin/python tools/spr/survey_mugen.py            # todos os 26
    .venv/bin/python tools/spr/survey_mugen.py --only 913 922
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import import_mugen as M  # noqa: E402  (reaproveita Frame/load_bmp/list_bmps/pick_idle)

LOOKTYPES = "assets-src/sprites/mugen_looktypes.json"
SRC_ROOT = "assets-src/import/mugen"
OUT_ROOT = "assets-src/import/extracted/mugen"

ORIENTATIONS = ["frente", "perfil_direita", "perfil_esquerda", "3/4", "costas"]
POSES = ["parado", "andar", "correr", "pular", "ataque", "especial", "dano", "vitoria", "outro"]


# ------------------------------------------------------------------ leitura
def read_all_frames(folder):
    """TODOS os quadros uteis do rip (sem o teto SCAN_FILES do import_mugen).

    Mesmas peneiras de tamanho/densidade do import_mugen.read_frames, mas sem
    limite de quantidade — o pedido explicito e nao parar nos primeiros 120."""
    cand = []
    for name in M.list_bmps(folder):
        path = os.path.join(folder, name)
        with Image.open(path) as probe:
            if (probe.width > M.MAX_SIDE or probe.height > M.MAX_SIDE
                    or probe.width < M.MIN_SIDE[0] or probe.height < M.MIN_SIDE[1]):
                continue
        img = M.load_bmp(path)
        box = img.getbbox()
        if not box:
            continue
        img = img.crop(box)
        if img.width < M.MIN_SIDE[0] or img.height < M.MIN_SIDE[1]:
            continue
        f = M.Frame(M.frame_no(name), name, img)
        if f.pixels < M.MIN_PIX or not (M.FILL[0] <= f.fill <= M.FILL[1]):
            continue
        cand.append(f)
    if not cand:
        return [], 0
    hs = np.array([f.h for f in cand])
    counts = [(int(((hs >= h - 6) & (hs <= h + 6)).sum()), h) for h in hs]
    return cand, max(counts)[1]


# ------------------------------------------------------------------ clusters de cor
def color_clusters(frames, idle_i):
    """Estimativa grosseira de cor de PELE e de CABELO do personagem.

    Pele: media dos pixels que passam em `is_skin` no quadro parado + os 8
    quadros mais parecidos com ele (rgbsig). Cabelo: media dos pixels do terco
    SUPERIOR do quadro parado que (a) sao opacos, (b) NAO sao pele e (c) nao sao
    um tom muito saturado de vermelho/azul puro (bandana/roupa) — fica so o
    tom mais escuro/neutro tipico de cabelo."""
    base = frames[idle_i]
    close = sorted(frames, key=lambda f: -M.color_like(f, base))[:9]
    skin_px, hair_px = [], []
    for f in close:
        a = np.array(f.img)
        op = a[:, :, 3] >= 128
        r, g, b = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
        mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
        skin = op & (r > 95) & (g > 40) & (b > 20) & (r > g) & (r > b) & ((mx - mn) > 15) & ((r - g) > 15)
        if skin.any():
            skin_px.append(a[:, :, :3][skin])
    y1 = max(1, base.h // 3)
    a = np.array(base.img)[:y1]
    op = a[:, :, 3] >= 128
    r, g, b = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    skin = (r > 95) & (g > 40) & (b > 20) & (r > g) & (r > b) & ((mx - mn) > 15) & ((r - g) > 15)
    hairish = op & ~skin
    if hairish.any():
        hair_px.append(a[:, :, :3][hairish])
    skin_rgb = tuple(int(v) for v in np.concatenate(skin_px).mean(axis=0)) if skin_px else (200, 160, 130)
    hair_rgb = tuple(int(v) for v in np.concatenate(hair_px).mean(axis=0)) if hair_px else (40, 40, 40)
    return skin_rgb, hair_rgb


# ------------------------------------------------------------------ classificacao
def classify_orientation(f):
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


def classify_pose(frames, i, idle_i, idle_h, order_rank):
    f = frames[i]
    base = frames[idle_i]
    dh = abs(f.h - idle_h)
    wide = f.w > f.h * 1.05
    mv_prev = M.motion(frames[i - 1], f) if i > 0 else 0.0
    mv_next = M.motion(f, frames[i + 1]) if i + 1 < len(frames) else 0.0
    mv = max(mv_prev, mv_next)
    size_jump = f.pixels > base.pixels * 1.6 or f.w > base.w * 1.8
    color_off = M.color_like(f, base) < 0.55          # paleta bem diferente: fx grande
    if i == idle_i:
        return "parado"
    if dh <= M.H_TOL and not wide and 0.02 <= mv <= 0.22:
        return "andar"
    if dh <= 2 * M.H_TOL and wide and not size_jump and 0.02 <= mv <= 0.30:
        return "correr"
    if color_off or size_jump:
        return "especial"
    if order_rank is not None and order_rank < 10 and dh <= M.H_TOL and not wide and mv < 0.12:
        return "vitoria"
    if f.h < idle_h - M.H_TOL - 2 and not wide:
        return "pular"
    if wide and mv >= 0.20:
        return "ataque"
    if mv >= 0.35:
        return "dano"
    return "outro"


def analyse_survey(folder, lt):
    frames, typical = read_all_frames(folder)
    if len(frames) < 4:
        return None, "so %d quadros uteis" % len(frames), None
    idle_i, idle_run = M.pick_idle(frames, typical)
    idle_h = frames[idle_i].h
    skin_rgb, hair_rgb = color_clusters(frames, idle_i)

    buckets = {}   # (orient, pose) -> [frame index, ...]
    per_frame = []
    for i, f in enumerate(frames):
        orient = classify_orientation(f)
        pose = classify_pose(frames, i, idle_i, idle_h, i if i < 40 else None)
        buckets.setdefault((orient, pose), []).append(i)
        per_frame.append({"no": f.no, "w": f.w, "h": f.h, "orient": orient, "pose": pose})

    return {
        "frames": frames, "idle_i": idle_i, "idle_run": idle_run, "typical": typical,
        "buckets": buckets, "per_frame": per_frame,
        "skin_rgb": skin_rgb, "hair_rgb": hair_rgb,
    }, None, frames


def best_examples(sel, orient, pose, n=3):
    idx = sel["buckets"].get((orient, pose), [])
    if not idx:
        return []
    frames = sel["frames"]
    base_h = frames[sel["idle_i"]].h
    idx = sorted(idx, key=lambda i: abs(frames[i].h - base_h))
    out, seen_no = [], set()
    for i in idx:
        if len(out) >= n:
            break
        out.append(i)
    return out


# ------------------------------------------------------------------ folha de revisao
def review_sheet(lt, info, sel):
    import imports as I
    frames = sel["frames"]
    box, zoom, pad = 32, 3, 3
    cell = box * zoom
    ncols = 3
    header_h = 34
    row_h = cell + 16 + pad
    W = pad + 60 + ncols * (cell + pad)
    H = header_h + pad + len(ORIENTATIONS) * row_h + pad
    sh = Image.new("RGBA", (W, H), (24, 24, 30, 255))
    d = ImageDraw.Draw(sh)
    d.text((pad, 4), "%d %s  -- pele~%s cabelo~%s  (parado=%04d, %d quadros uteis)" % (
        lt, info["name"], sel["skin_rgb"], sel["hair_rgb"], frames[sel["idle_i"]].no,
        len(frames)), fill=(255, 235, 120, 255))
    d.text((pad, 18), "linhas=orientacao  colunas=melhores candidatos por pose (rotulo = pose:num_arquivo)",
           fill=(170, 170, 180, 255))
    for r, orient in enumerate(ORIENTATIONS):
        y = header_h + pad + r * row_h
        d.text((pad, y + cell // 2 - 6), orient, fill=(200, 220, 255, 255))
        # junta poses que tenham exemplo, prioridade parado/andar primeiro
        ordered_poses = [p for p in ("parado", "andar") if (orient, p) in sel["buckets"]]
        ordered_poses += [p for p in POSES if p not in ("parado", "andar") and (orient, p) in sel["buckets"]]
        col = 0
        for pose in ordered_poses:
            if col >= ncols:
                break
            ex = best_examples(sel, orient, pose, 1)
            if not ex:
                continue
            i = ex[0]
            f = frames[i]
            x = pad + 60 + col * (cell + pad)
            scale = min(box / float(f.w), box / float(f.h), 1.0)
            thumb = I.fit_uniform(f.img, box, scale, False)
            bg = Image.new("RGBA", (box, box), (66, 66, 74, 255))
            bg.alpha_composite(thumb)
            sh.paste(bg.resize((cell, cell), Image.NEAREST), (x, y))
            d.text((x, y + cell + 1), "%s:%04d" % (pose[:4], f.no), fill=(210, 210, 220, 255))
            col += 1
    return sh


# ------------------------------------------------------------------ principal
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", nargs="*", type=int)
    args = ap.parse_args()

    with open(os.path.join(ROOT, LOOKTYPES), encoding="utf-8") as fh:
        table = json.load(fh)["looktypes"]

    summary = {}
    for key in sorted(table, key=int):
        lt = int(key)
        if args.only and lt not in args.only:
            continue
        info = table[key]
        folder = os.path.join(ROOT, SRC_ROOT, info["folder"])
        if not os.path.isdir(folder):
            print("AVISO: %d %s: pasta ausente" % (lt, info["name"]))
            continue
        sel, err, frames = analyse_survey(folder, lt)
        if sel is None:
            print("AVISO: %d %s: %s" % (lt, info["name"], err))
            continue

        counts = {}
        for (o, p), idx in sel["buckets"].items():
            counts.setdefault(o, {})[p] = len(idx)
        print("%3d %-20s %5d quadros  parado=%04d  buckets: %s" % (
            lt, info["name"][:20], len(frames), frames[sel["idle_i"]].no,
            {o: sorted(v.items()) for o, v in counts.items()}))

        out_dir = os.path.join(ROOT, OUT_ROOT)
        os.makedirs(out_dir, exist_ok=True)
        review_sheet(lt, info, sel).save(os.path.join(out_dir, "_survey_%d.png" % lt))

        json_out = {
            "looktype": lt, "name": info["name"], "n_frames": len(frames),
            "idle_no": frames[sel["idle_i"]].no,
            "skin_rgb": sel["skin_rgb"], "hair_rgb": sel["hair_rgb"],
            "buckets": {"%s|%s" % (o, p): [frames[i].no for i in idx]
                        for (o, p), idx in sel["buckets"].items()},
            "per_frame": sel["per_frame"],
        }
        with open(os.path.join(out_dir, "_survey_%d.json" % lt), "w", encoding="utf-8") as fh:
            json.dump(json_out, fh, indent=1)
        summary[lt] = json_out

    print("\n%d personagens varridos." % len(summary))


if __name__ == "__main__":
    main()
