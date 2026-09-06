#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compoe um PNG (fundo transparente) de um looktype de creature a partir do
PAR NOSSO `client-otc/data/things/1098/Tibia.dat`/`Tibia.spr` -- nao le nada
de `assets-src/import/` (material de terceiros, ver ADR-002 em
docs/03-decisoes-tecnicas.md).

Reaproveita a leitura de `.spr`/`.dat` de `sprformat.py` (mesmo modulo que
`dump_dat.py` usa) e a logica de composicao MULTIPLY (base * mascara de
outfit) documentada em `FORMATO.md` secao 3.5 e ja implementada em
`review_animals.py::composite` -- este script generaliza a mesma ideia para
qualquer looktype/direcao/fase/addon lido direto do .dat, em vez de desenhar
a arte on-the-fly.

Formula de indice de sprite (ThingType::getSpriteIndex, thingtype.cpp:1014):

    index = ((((((fase % phases) * patternZ + z) * patternY + y) * patternX + x)
              * layers + l) * height + h) * width + w

`patternX` = direcao do enum Otc::Direction (0=Norte 1=Leste 2=Sul 3=Oeste),
`patternY` = addon, `patternZ` = montaria. O tile (w,h) e desenhado no canvas
na posicao ((width-w-1)*32, (height-h-1)*32) -- contagem a partir do canto
inferior direito (FORMATO.md secao 3.3).

Se `layers >= 2`, layer 0 e a base e layer 1 e o template de mascara: pixels
EXATOS (255,0,0)=body (0,255,0)=legs (0,0,255)=feet (255,255,0)=head viram a
cor de outfit via MULTIPLY (resultado = base * cor/255); qualquer outro pixel
do template fica igual ao layer 0 (FORMATO.md secao 3.5). Cores default (sem
--head/--body/--legs/--feet) sao brancas = MULTIPLY neutro (base aparece sem
recolorir).

Uso:
    # um looktype, saida unica
    .venv/bin/python tools/spr/render_outfit.py --looktype 900 --out /tmp/900.png --scale 4

    # varios de uma vez (reaproveita o .dat/.spr carregado uma unica vez)
    .venv/bin/python tools/spr/render_outfit.py \\
        --looktype 900 901 902 903 904 905 907 908 909 \\
        --outdir tools/aac/portraits --scale 4

    # looktype com cores de outfit (indices 0..132 de tibia_colors.py, ex.: bandit 129)
    .venv/bin/python tools/spr/render_outfit.py --looktype 129 \\
        --head 78 --body 39 --legs 10 --feet 0 --out /tmp/129.png
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image  # noqa: E402

import sprformat as S  # noqa: E402
import tibia_colors as TC  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DEFAULT_THINGS_DIR = os.path.join(ROOT, "client-otc", "data", "things", "1098")

# cores exatas que Image::overwriteMask procura no template (layer 1) -- mesma
# tabela de tools/spr/art.py (MASK_BODY/LEGS/FEET/HEAD) e FORMATO.md secao 3.5.
MASK_COLOR_TO_REGION = {
    (255, 0, 0): "body",
    (0, 255, 0): "legs",
    (0, 0, 255): "feet",
    (255, 255, 0): "head",
}

DIRECTION_NAMES = {"norte": 0, "leste": 1, "sul": 2, "oeste": 3,
                    "north": 0, "east": 1, "south": 2, "west": 3}


class RenderError(Exception):
    pass


def load_things(things_dir=DEFAULT_THINGS_DIR):
    """Le Tibia.dat/Tibia.spr uma vez. Devolve (tables, spr) -- tables[1] =
    dict{looktype: Thing} da categoria creature (ver sprformat.CATEGORY_CREATURE)."""
    dat_path = os.path.join(things_dir, "Tibia.dat")
    spr_path = os.path.join(things_dir, "Tibia.spr")
    if not os.path.exists(dat_path) or not os.path.exists(spr_path):
        raise RenderError("nao encontrei %s / %s -- rode tools/spr/build_assets.py" % (dat_path, spr_path))
    _sig, tables = S.read_dat(dat_path)
    spr = S.read_spr(spr_path)
    return tables, spr


def find_thing(tables, looktype):
    thing = tables[S.CATEGORY_CREATURE].get(int(looktype))
    if thing is None:
        raise RenderError("looktype %s nao existe na categoria creature do .dat" % looktype)
    return thing


def _pick_group(thing, prefer_type):
    """type 0 = Idle/Default, type 1 = Moving (FORMATO.md secao 3.2). Se o grupo
    preferido nao existir (thing sem animacao "parada" separada), cai no outro."""
    by_type = {g.type: g for g in thing.groups}
    if prefer_type in by_type:
        return by_type[prefer_type]
    if thing.groups:
        return thing.groups[0]
    raise RenderError("thing sem frame group nenhum")


def _layer_image(g, spr, layer, x, y, z, phase):
    """Compoe o canvas width*32 x height*32 de UMA camada, para uma
    direcao/addon/montaria/fase fixos, colando os tiles 32x32 na ordem
    correta (canto inferior direito primeiro -- FORMATO.md 3.3)."""
    img = Image.new("RGBA", (g.width * 32, g.height * 32), (0, 0, 0, 0))
    phases = max(1, g.phases)
    a = phase % phases
    for h in range(g.height):
        for w in range(g.width):
            idx = ((((((a * g.pattern_z + z) * g.pattern_y + y) * g.pattern_x + x)
                     * g.layers + layer) * g.height + h) * g.width + w)
            if idx >= len(g.sprites):
                continue
            sprite_id = g.sprites[idx]
            if not sprite_id:
                continue
            px = S.spr_get_sprite(spr, sprite_id)
            if px is None:
                continue
            tile = Image.frombytes("RGBA", (32, 32), bytes(px))
            pos_x = (g.width - w - 1) * 32
            pos_y = (g.height - h - 1) * 32
            img.paste(tile, (pos_x, pos_y), tile)
    return img


def _multiply_mask(base, mask, colors):
    """resultado = base * (cor_outfit/255) nos pixels cuja mascara bata EXATAMENTE
    uma das 4 cores de template; o resto do pixel fica igual ao layer0 (nunca
    recolore olho/linha/sombra) -- replica Creature::internalDraw + Image::overwriteMask,
    mesmo algoritmo de tools/spr/review_animals.py::composite."""
    out = base.copy()
    bp = base.load()
    mp = mask.load()
    op = out.load()
    w, h = base.size
    for yy in range(h):
        for xx in range(w):
            mc = mp[xx, yy]
            if mc[3] == 0:
                continue
            region = MASK_COLOR_TO_REGION.get((mc[0], mc[1], mc[2]))
            if region is None:
                continue
            r, gg, b, a = bp[xx, yy]
            if a == 0:
                continue
            tr, tg, tb = colors[region]
            op[xx, yy] = (r * tr // 255, gg * tg // 255, b * tb // 255, a)
    return out


def render_outfit(tables, spr, looktype, direction=2, addon=0, mount=0,
                   group="idle", phase=0, head=None, body=None, legs=None, feet=None):
    """Devolve uma imagem PIL RGBA (width*32 x height*32, sem escala) do
    looktype pedido. head/body/legs/feet sao indices 0..132 da paleta de
    outfit (tibia_colors.color_rgb) ou None (= branco, MULTIPLY neutro)."""
    thing = find_thing(tables, looktype)
    prefer_type = 0 if group == "idle" else 1
    g = _pick_group(thing, prefer_type)
    if direction >= g.pattern_x:
        direction = direction % max(1, g.pattern_x)
    if addon >= g.pattern_y:
        addon = 0
    if mount >= g.pattern_z:
        mount = 0

    base = _layer_image(g, spr, 0, direction, addon, mount, phase)
    if g.layers < 2:
        return base

    mask = _layer_image(g, spr, 1, direction, addon, mount, phase)
    colors = {
        "head": TC.color_rgb(head) if head is not None else (255, 255, 255),
        "body": TC.color_rgb(body) if body is not None else (255, 255, 255),
        "legs": TC.color_rgb(legs) if legs is not None else (255, 255, 255),
        "feet": TC.color_rgb(feet) if feet is not None else (255, 255, 255),
    }
    return _multiply_mask(base, mask, colors)


def save_portrait(img, out_path, scale=1):
    if scale and scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path)


def _parse_direction(v):
    v = v.strip().lower()
    if v in DIRECTION_NAMES:
        return DIRECTION_NAMES[v]
    return int(v)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=DEFAULT_THINGS_DIR,
                     help="pasta com Tibia.dat/Tibia.spr (default: client-otc/data/things/1098)")
    ap.add_argument("--looktype", type=int, nargs="+", required=True,
                     help="um ou mais looktypes de creature")
    ap.add_argument("--direction", default="sul", type=_parse_direction,
                     help="0/norte 1/leste 2/sul(padrao) 3/oeste")
    ap.add_argument("--addon", type=int, default=0, help="patternY (0 = sem addon)")
    ap.add_argument("--mount", type=int, default=0, help="patternZ (0 = sem montaria)")
    ap.add_argument("--group", choices=["idle", "moving"], default="idle",
                     help="frame group: idle (parado, padrao) ou moving (andando)")
    ap.add_argument("--phase", type=int, default=0, help="fase dentro do grupo (padrao 0)")
    ap.add_argument("--head", type=int, default=None, help="indice de cor 0..132 (mascara amarela)")
    ap.add_argument("--body", type=int, default=None, help="indice de cor 0..132 (mascara vermelha)")
    ap.add_argument("--legs", type=int, default=None, help="indice de cor 0..132 (mascara verde)")
    ap.add_argument("--feet", type=int, default=None, help="indice de cor 0..132 (mascara azul)")
    ap.add_argument("--scale", type=int, default=1, help="upscale nearest-neighbor (ex.: 4 para retrato)")
    ap.add_argument("--out", default=None, help="arquivo de saida (so com 1 --looktype)")
    ap.add_argument("--outdir", default=None, help="pasta de saida: grava <outdir>/<looktype>.png")
    args = ap.parse_args()

    if len(args.looktype) == 1 and args.out:
        pass
    elif not args.outdir:
        ap.error("use --out (com 1 --looktype) ou --outdir (com 1 ou mais)")

    tables, spr = load_things(args.dir)

    for lt in args.looktype:
        img = render_outfit(
            tables, spr, lt,
            direction=args.direction, addon=args.addon, mount=args.mount,
            group=args.group, phase=args.phase,
            head=args.head, body=args.body, legs=args.legs, feet=args.feet,
        )
        if len(args.looktype) == 1 and args.out:
            out_path = args.out
        else:
            out_path = os.path.join(args.outdir, "%d.png" % lt)
        save_portrait(img, out_path, scale=args.scale)
        print("looktype %-5d -> %s (%dx%d)" % (lt, out_path, img.width * args.scale, img.height * args.scale))


if __name__ == "__main__":
    try:
        main()
    except RenderError as e:
        print("erro: %s" % e, file=sys.stderr)
        sys.exit(1)
