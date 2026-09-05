#!/usr/bin/env python3
"""Gera, por codigo (Pillow, ADR-002: nenhum pixel de terceiros), as animacoes de
EFEITOS e MISSEIS proprios dos jutsus Naruto e as registra em:

  - assets-src/sprites/effects_src/<key>/*.png   PNGs individuais (versionados)
  - assets-src/sprites/effects_src/_sheets/*.png folhas montadas (versionadas)
  - assets-src/sprites/effects.json               catalogo (ids, papel, aliases)
  - assets-src/sprites/overrides/50_effects_naruto.json
        override no MESMO esquema de assets-src/sprites/imports.json
        (root/build_dir/effects/missiles) -- tools/spr/build_assets.py ja varre
        assets-src/sprites/overrides/*.json e aplica cada um via imports.apply(),
        entao este arquivo entra no --dat sem precisar mexer em build_assets.py.
  - assets-src/sprites/effects/_sheet.png         folha de REVISAO (olhe antes
        de rodar build_assets.py!)

IDs (protocolo 10.98 manda effect/missile em U8, faixa 1..255 -- ver
docs/sistemas/arte-e-sprites.md e tools/spr/FORMATO.md):

  - CONST_ME_* vai ate 175 e CONST_ANI_* vai ate 54 (server/tfs/src/const.h);
    nada no TFS manda numero > isso para essas categorias, exceto o 0xFE (254)
    reservado ("internal use, don't send to client") para missile. Os efeitos e
    misseis NOVOS dos jutsus usam ids 200..226 (efeito) e 60..67 (missile) --
    bem acima do teto real, zero chance de colisao com qualquer script vanilla
    (que so consegue enviar os enums fixos ja compilados no C++).
  - Alem dos ids novos, este script tambem REDESENHA (nao renumera) um punhado
    de ids "slot compartilhado" que data/tfs_mapping.json (elemento -> combat/
    area_effect/shoot) e o servidor ja mandam por NOME em spells/monstros:
    CONST_ME_FIREAREA(7), ICEATTACK(44), ENERGYHIT(12), STONES(45), HOLYAREA(50),
    HITAREA(10), POFF(3), MAGIC_GREEN(15) e CONST_ANI_FIRE(4), ICE(29), ENERGY(5),
    EARTH(30), HOLY(31), THROWINGSTAR(8). Por que: `Monsters::deserializeSpell`
    (server/tfs/src/monsters.cpp) resolve shootEffect/areaEffect por NOME fixo
    (tools.cpp getMagicEffect/getShootType) -- nunca aceita numero cru. Como
    nenhum sprite deste projeto e "de verdade" (ADR-002), redesenhar o PIXEL
    desses ids com arte coerente por elemento resolve os ataques de MONSTRO sem
    precisar reescrever spells em Lua (risco alto com o playtest ao vivo). Os
    JUTSUS (Lua) usam os ids NOVOS (200+/60+) via numero cru -- mais variedade,
    um por `animation` do JSON (ver ALIASES).

Uso:
    .venv/bin/python tools/spr/gen_effects.py             # gera tudo + _sheet.png
    .venv/bin/python tools/spr/gen_effects.py --sheet-only   # so a folha de revisao
"""
import argparse
import json
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import char_synth as CS  # noqa: E402  (outline_1px)

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SPRITES = os.path.join(ROOT, "assets-src", "sprites")
SRC_DIR = os.path.join(SPRITES, "effects_src")
SHEETS_DIR = os.path.join(SRC_DIR, "_sheets")
REVIEW_DIR = os.path.join(SPRITES, "effects")
CATALOG_PATH = os.path.join(SPRITES, "effects.json")
OVERRIDE_PATH = os.path.join(SPRITES, "overrides", "50_effects_naruto.json")

CELL = 32
CX, CY = 16, 16.5   # centro da celula (y um pouco abaixo, "chao" em y=30)

# --------------------------------------------------------------------- cores
# Mesma familia de paleta de tools/spr/gen_jutsu_icons.py (ELEMENT_COLORS),
# com um 4o tom "dark" para sombra/contorno de preenchimento.
PALETTES = {
    "katon":    dict(main=(230, 96, 30),  glow=(255, 200, 96),  dark=(90, 30, 12)),
    "suiton":   dict(main=(58, 132, 224), glow=(170, 222, 255), dark=(16, 40, 72)),
    "raiton":   dict(main=(232, 208, 58), glow=(255, 248, 190), dark=(70, 60, 14)),
    "doton":    dict(main=(150, 106, 60), glow=(214, 178, 122), dark=(52, 36, 20)),
    "fuuton":   dict(main=(120, 202, 112), glow=(214, 248, 198), dark=(24, 46, 26)),
    "none":     dict(main=(206, 208, 216), glow=(244, 244, 248), dark=(40, 40, 46)),
    "heal":     dict(main=(88, 208, 118),  glow=(198, 255, 210), dark=(14, 46, 20)),
    "poison":   dict(main=(122, 172, 62),  glow=(196, 230, 118), dark=(28, 44, 14)),
    "seal":     dict(main=(224, 184, 108), glow=(255, 236, 182), dark=(52, 36, 16)),
    "shadow":   dict(main=(96, 66, 140),   glow=(180, 140, 220), dark=(14, 10, 20)),
}

OUTLINE = (18, 15, 20)


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


def canvas():
    return Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))


def outline(img):
    return CS.outline_1px(img, color=OUTLINE, strength=255)


# ------------------------------------------------------------- primitivas
def _star_points(cx, cy, r_out, r_in, n, rot=0.0):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / n
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def _bolt_points(x0, y0, x1, y1, jags, seed):
    """Linha em zigue-zague (raio) entre dois pontos."""
    pts = [(x0, y0)]
    for i in range(1, jags):
        t = i / jags
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        off = ((seed * (i + 3)) % 7 - 3) * 1.6
        nx, ny = -(y1 - y0), (x1 - x0)
        n = math.hypot(nx, ny) or 1
        pts.append((x + nx / n * off, y + ny / n * off))
    pts.append((x1, y1))
    return pts


# ----------------------------------------------------------- templates (fx)
def tpl_burst(pal, n=6, r0=2, r1=14, rays=6):
    """Explosao radial: anel crescendo + nucleo brilhante + faiscas voando."""
    frames = []
    for i in range(n):
        t = i / (n - 1)
        img = canvas()
        d = ImageDraw.Draw(img)
        r = r0 + (r1 - r0) * t
        core = max(1, int(r * 0.55 * (1 - 0.6 * t)))
        d.ellipse([CX - r, CY - r, CX + r, CY + r], outline=rgba(pal["main"]), width=3)
        if core > 0:
            d.ellipse([CX - core, CY - core, CX + core, CY + core], fill=rgba(pal["glow"]))
        if i < n - 1:
            for k in range(rays):
                a = k * (2 * math.pi / rays) + t * 0.6
                rr = r + 3
                x, y = CX + math.cos(a) * rr, CY + math.sin(a) * rr
                d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=rgba(pal["glow"]))
        frames.append(outline(img))
    return frames


def tpl_ring(pal, n=6, r0=4, r1=15):
    frames = []
    for i in range(n):
        t = i / (n - 1)
        img = canvas()
        d = ImageDraw.Draw(img)
        r = r0 + (r1 - r0) * t
        w = 3 if t < 0.7 else 2
        d.ellipse([CX - r, CY - r, CX + r, CY + r], outline=rgba(pal["main"]), width=w)
        d.ellipse([CX - r + 2, CY - r + 2, CX + r - 2, CY + r - 2],
                   outline=rgba(pal["glow"]), width=1)
        frames.append(outline(img))
    return frames


def tpl_cone(pal, n=5, half_angle=0.55, length=13, sweep=0.5):
    frames = []
    for i in range(n):
        t = i / (n - 1)
        img = canvas()
        d = ImageDraw.Draw(img)
        base = -math.pi / 2 + (t - 0.5) * sweep
        p1 = (CX, CY)
        p2 = (CX + math.cos(base - half_angle) * length, CY + math.sin(base - half_angle) * length)
        p3 = (CX + math.cos(base + half_angle) * length, CY + math.sin(base + half_angle) * length)
        d.polygon([p1, p2, p3], fill=rgba(pal["main"], 235))
        mid = (CX + math.cos(base) * length * 0.6, CY + math.sin(base) * length * 0.6)
        d.line([p1, mid], fill=rgba(pal["glow"]), width=2)
        frames.append(outline(img))
    return frames


def tpl_dragon(pal, n=7, length=15):
    """Cabeca serpenteando: onda + bolha de cabeca crescendo (beam num tile so)."""
    frames = []
    for i in range(n):
        t = i / (n - 1)
        img = canvas()
        d = ImageDraw.Draw(img)
        pts = []
        for k in range(9):
            f = k / 8.0
            x = CX - length + f * (length * 2)
            y = CY + math.sin(f * math.pi * 2 + t * 3) * (4 - 3 * abs(f - 0.5))
            pts.append((x, y))
        d.line(pts, fill=rgba(pal["main"]), width=3)
        head = pts[-1]
        r = 3 + int(4 * (1 - abs(t - 0.6)))
        d.ellipse([head[0] - r, head[1] - r, head[0] + r, head[1] + r], fill=rgba(pal["glow"]))
        frames.append(outline(img))
    return frames


def tpl_splash(pal, n=5):
    frames = []
    for i in range(n):
        t = i / (n - 1)
        img = canvas()
        d = ImageDraw.Draw(img)
        core = max(2, int(7 * (1 - 0.6 * t)))
        d.ellipse([CX - core, CY - 2 - core, CX + core, CY - 2 + core], fill=rgba(pal["main"]))
        d.ellipse([CX - core + 2, CY - 4 - core // 2, CX + core - 2, CY - 4 + core // 2],
                   fill=rgba(pal["glow"]))
        for k in range(6):
            a = k * math.pi / 3 + 0.3
            rr = 5 + 10 * t
            x, y = CX + math.cos(a) * rr, CY - 2 + math.sin(a) * rr * 0.6
            dotr = max(1, 3 - int(t * 1.5))
            d.ellipse([x - dotr, y - dotr, x + dotr, y + dotr], fill=rgba(pal["main"], 255))
        ring_r = 4 + 10 * t
        d.ellipse([CX - ring_r, CY + 7 - ring_r * 0.35, CX + ring_r, CY + 7 + ring_r * 0.35],
                   outline=rgba(pal["glow"], 255), width=1)
        frames.append(outline(img))
    return frames


def tpl_spikes(pal, n=5, count=5):
    frames = []
    for i in range(n):
        t = i / (n - 1)
        img = canvas()
        d = ImageDraw.Draw(img)
        h = 14 * min(1.0, t * 1.6)
        for k in range(count):
            x = 6 + k * (20 / (count - 1))
            hh = h * (0.7 + 0.3 * math.sin(k * 2.1 + 1))
            d.polygon([(x - 3, 30), (x, 30 - hh), (x + 3, 30)], fill=rgba(pal["main"]))
            d.line([(x, 30 - hh), (x, 30 - hh * 0.4)], fill=rgba(pal["glow"]), width=1)
        if t < 0.5:
            r = 10 * (t * 2)
            d.ellipse([CX - r, 29 - r * 0.3, CX + r, 29 + r * 0.3], fill=rgba(pal["dark"], 150))
        frames.append(outline(img))
    return frames


def tpl_collapse(pal, n=6):
    frames = []
    for i in range(n):
        t = i / (n - 1)
        img = canvas()
        d = ImageDraw.Draw(img)
        for k in range(6):
            a = k * math.pi / 3
            rr = 12 * min(1.0, t * 1.4)
            x, y = CX + math.cos(a) * rr, CY + math.sin(a) * rr * 0.6
            d.line([(CX, CY), (x, y)], fill=rgba(pal["dark"]), width=1)
        for k in range(5):
            f = (k + t * 4) % 5 / 5.0
            x = 8 + k * 4
            y = 8 + f * 16
            s = 2
            d.rectangle([x - s, y - s, x + s, y + s], fill=rgba(pal["main"]))
        r = 4 + 8 * t
        d.ellipse([CX - r, 27 - r * 0.4, CX + r, 27 + r * 0.4], fill=rgba(pal["dark"], int(180 * (1 - t * 0.6))))
        frames.append(outline(img))
    return frames


def tpl_vortex(pal, n=6, arms=3, r=12):
    frames = []
    for i in range(n):
        t = i / n
        img = canvas()
        d = ImageDraw.Draw(img)
        for a_i in range(arms):
            base = a_i * (2 * math.pi / arms) + t * 2 * math.pi
            pts = []
            for k in range(6):
                f = k / 5.0
                a = base + f * 2.2
                rr = 2 + r * f
                pts.append((CX + math.cos(a) * rr, CY + math.sin(a) * rr))
            d.line(pts, fill=rgba(pal["main"]), width=2)
        d.ellipse([CX - 2, CY - 2, CX + 2, CY + 2], fill=rgba(pal["glow"]))
        frames.append(outline(img))
    return frames


def tpl_tornado(pal, n=7, height=24, r=9):
    frames = []
    for i in range(n):
        t = i / n
        img = canvas()
        d = ImageDraw.Draw(img)
        for row in range(6):
            f = row / 5.0
            y = 29 - f * height
            rr = r * (1 - f * 0.7)
            ang = t * 2 * math.pi + row * 1.1
            x0 = CX + math.cos(ang) * rr
            x1 = CX - math.cos(ang) * rr
            d.line([(x0, y), (x1, y - 2)], fill=rgba(pal["main"], 220), width=2)
        d.line([(CX, 29), (CX, 29 - height)], fill=rgba(pal["glow"], 120), width=1)
        frames.append(outline(img))
    return frames


def tpl_poof(pal, n=6, min_alpha=30):
    frames = []
    for i in range(n):
        t = i / (n - 1)
        img = canvas()
        d = ImageDraw.Draw(img)
        if i == 0:
            r = 9
            d.ellipse([CX - r, CY - r, CX + r, CY + r], fill=rgba(pal["glow"], 235))
        else:
            for k in range(4):
                rr = 3 + k + int(5 * t)
                y = 27 - k * 4 - int(9 * t)
                a = 235 - int(70 * t)
                d.ellipse([CX - rr, y - rr // 2, CX + rr, y + rr // 2],
                          fill=rgba(pal["main"], max(min_alpha, a - k * 25)))
            d.ellipse([CX - 3, 28 - int(6 * t), CX + 3, 28 - int(6 * t) + 3],
                       fill=rgba(pal["dark"], max(0, 200 - int(160 * t))))
        frames.append(outline(img))
    return frames


def tpl_glow(pal, n=6):
    frames = []
    for i in range(n):
        t = i / n
        img = canvas()
        d = ImageDraw.Draw(img)
        r = 6 + 3 * abs(math.sin(t * math.pi))
        d.ellipse([CX - r, CY - r, CX + r, CY + r], fill=rgba(pal["main"], 90))
        r2 = r * 0.55
        d.ellipse([CX - r2, CY - r2, CX + r2, CY + r2], fill=rgba(pal["glow"], 220))
        d.ellipse([CX - r, CY - r, CX + r, CY + r], outline=rgba(pal["main"]), width=1)
        frames.append(outline(img))
    return frames


def tpl_mist(pal, n=6):
    frames = []
    for i in range(n):
        t = i / (n - 1)
        img = canvas()
        d = ImageDraw.Draw(img)
        for k in range(7):
            a = k * 0.9 + t * 1.5
            rr = 3 + 10 * t
            x = CX + math.cos(a) * rr
            y = 22 + math.sin(a * 0.6) * 4 - t * 6
            r = 3 + (k % 3)
            d.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6],
                      fill=rgba(pal["main"], max(40, 190 - int(120 * t))))
        frames.append(outline(img))
    return frames


def tpl_melee_hit(pal, n=5):
    frames = []
    for i in range(n):
        t = i / (n - 1)
        img = canvas()
        d = ImageDraw.Draw(img)
        r = 3 + 9 * min(1.0, t * 1.6)
        pts = _star_points(CX, CY, r, r * 0.4, 4, rot=t * 0.4)
        d.polygon(pts, fill=rgba(pal["glow"], int(255 * (1 - 0.5 * t))))
        d.line([(CX - r - 3, CY), (CX + r + 3, CY)], fill=rgba(pal["main"]), width=1)
        d.line([(CX, CY - r - 3), (CX, CY + r + 3)], fill=rgba(pal["main"]), width=1)
        frames.append(outline(img))
    return frames


def tpl_seal(pal, n=6):
    frames = []
    for i in range(n):
        t = i / n
        img = canvas()
        d = ImageDraw.Draw(img)
        r = 11
        d.ellipse([CX - r, CY - r, CX + r, CY + r], outline=rgba(pal["main"]), width=2)
        for k in range(8):
            a = k * math.pi / 4 + t * 1.2
            x, y = CX + math.cos(a) * (r - 3), CY + math.sin(a) * (r - 3)
            d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=rgba(pal["glow"]))
        d.rectangle([CX - 5, CY - 7, CX + 5, CY + 7], outline=rgba(pal["dark"]))
        d.line([CX - 3, CY, CX + 3, CY], fill=rgba(pal["glow"]))
        frames.append(outline(img))
    return frames


def tpl_static_field(pal, n=6):
    frames = []
    for i in range(n):
        t = i / n
        img = canvas()
        d = ImageDraw.Draw(img)
        for k in range(4):
            a = k * math.pi / 2 + (t % 2) * 0.05
            x1, y1 = CX + math.cos(a) * 13, CY + math.sin(a) * 13
            pts = _bolt_points(CX, CY, x1, y1, 4, seed=k + i)
            d.line(pts, fill=rgba(pal["main"]), width=2)
        d.ellipse([CX - 2, CY - 2, CX + 2, CY + 2], fill=rgba(pal["glow"]))
        frames.append(outline(img))
    return frames


def tpl_lightning_strike(pal, n=5):
    frames = []
    for i in range(n):
        img = canvas()
        d = ImageDraw.Draw(img)
        pts = _bolt_points(CX, 2, CX, 30, 6, seed=i * 3 + 1)
        d.line(pts, fill=rgba(pal["glow"]), width=3)
        d.line(pts, fill=rgba(pal["main"]), width=1)
        if i < 2:
            r = 5 - i * 2
            d.ellipse([CX - r, 2 - r, CX + r, 2 + r], fill=rgba(pal["glow"], 220))
        frames.append(outline(img))
    return frames


def tpl_armor(pal, n=6, r=11):
    frames = []
    for i in range(n):
        t = i / n
        img = canvas()
        d = ImageDraw.Draw(img)
        d.ellipse([CX - r, CY - r + 2, CX + r, CY + r + 2], outline=rgba(pal["dark"], 160), width=1)
        for k in range(5):
            a = t * 2 * math.pi + k * (2 * math.pi / 5)
            x, y = CX + math.cos(a) * r, CY + math.sin(a) * r * 0.9
            d.line([(x, y), (x + math.cos(a + 1.4) * 3, y + math.sin(a + 1.4) * 3)],
                   fill=rgba(pal["main"]), width=1)
            d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=rgba(pal["glow"]))
        frames.append(outline(img))
    return frames


def tpl_stone_shell(pal, n=5, r=11):
    frames = []
    for i in range(n):
        t = i / (n - 1)
        img = canvas()
        d = ImageDraw.Draw(img)
        rr = r * min(1.0, t * 1.4)
        for k in range(6):
            a = k * math.pi / 3
            x, y = CX + math.cos(a) * rr, CY + math.sin(a) * rr * 0.85
            s = 3
            d.polygon([(x, y - s), (x + s, y), (x, y + s), (x - s, y)], fill=rgba(pal["main"]))
        frames.append(outline(img))
    return frames


def tpl_wind_prison(pal, n=6, r=11):
    frames = []
    for i in range(n):
        t = i / n
        img = canvas()
        d = ImageDraw.Draw(img)
        for k in range(3):
            a0 = t * 2 * math.pi + k * (2 * math.pi / 3)
            pts = []
            for f in range(6):
                a = a0 + f * 0.5
                rr = r - f * 0.6
                pts.append((CX + math.cos(a) * rr, CY + math.sin(a) * rr * 0.8))
            d.line(pts, fill=rgba(pal["glow"]), width=1)
        d.ellipse([CX - r, CY - r * 0.8, CX + r, CY + r * 0.8], outline=rgba(pal["main"]), width=1)
        frames.append(outline(img))
    return frames


def tpl_chakra_blade(pal, n=5, length=15):
    frames = []
    for i in range(n):
        t = i / (n - 1)
        img = canvas()
        d = ImageDraw.Draw(img)
        a = -0.7 + t * 0.15
        x0, y0 = CX - math.cos(a) * length, CY - math.sin(a) * length
        x1, y1 = CX + math.cos(a) * length, CY + math.sin(a) * length
        d.line([(x0, y0), (x1, y1)], fill=rgba((80, 220, 235)), width=5)
        d.line([(x0, y0), (x1, y1)], fill=rgba((235, 255, 255)), width=2)
        d.ellipse([x1 - 2, y1 - 2, x1 + 2, y1 + 2], fill=rgba((235, 255, 255)))
        frames.append(outline(img))
    return frames


EFFECT_TEMPLATES = {
    "fx_fire_burst":       (tpl_burst, dict(n=6), "katon"),
    "fx_fire_ring":        (tpl_ring, dict(n=6), "katon"),
    "fx_fire_cone":        (tpl_cone, dict(n=5), "katon"),
    "fx_fire_dragon":      (tpl_dragon, dict(n=7), "katon"),
    "fx_water_splash":     (tpl_splash, dict(n=5), "suiton"),
    "fx_water_dragon":     (tpl_dragon, dict(n=7), "suiton"),
    "fx_water_mist":       (tpl_mist, dict(n=6), "suiton"),
    "fx_water_vortex":     (tpl_vortex, dict(n=6), "suiton"),
    "fx_lightning_strike": (tpl_lightning_strike, dict(n=5), "raiton"),
    "fx_static_field":     (tpl_static_field, dict(n=6), "raiton"),
    "fx_lightning_lance":  (tpl_lightning_strike, dict(n=5), "raiton"),
    "fx_lightning_armor":  (tpl_armor, dict(n=6), "raiton"),
    "fx_earth_spikes":     (tpl_spikes, dict(n=5), "doton"),
    "fx_earth_collapse":   (tpl_collapse, dict(n=6), "doton"),
    "fx_stone_shell":      (tpl_stone_shell, dict(n=5), "doton"),
    "fx_mud_splash":       (tpl_splash, dict(n=5), "doton"),
    "fx_wind_slash":       (tpl_cone, dict(n=5, half_angle=0.32, sweep=0.9), "fuuton"),
    "fx_wind_tornado":     (tpl_tornado, dict(n=7), "fuuton"),
    "fx_wind_prison":      (tpl_wind_prison, dict(n=6), "fuuton"),
    "fx_chakra_focus":     (tpl_glow, dict(n=6), "suiton"),
    "fx_heal_green":       (tpl_glow, dict(n=6), "heal"),
    "fx_smoke_poof":       (tpl_poof, dict(n=6), "none"),
    "fx_seal_glow":        (tpl_seal, dict(n=6), "seal"),
    "fx_shadow_clone":     (tpl_poof, dict(n=6, min_alpha=110), "shadow"),
    "fx_melee_hit":        (tpl_melee_hit, dict(n=5), "none"),
    "fx_poison_mist":      (tpl_mist, dict(n=6), "poison"),
    "fx_chakra_blade":     (tpl_chakra_blade, dict(n=5), "none"),
}

EFFECT_DURATIONS = {
    "fx_fire_burst": 90, "fx_fire_ring": 100, "fx_fire_cone": 90, "fx_fire_dragon": 100,
    "fx_water_splash": 90, "fx_water_dragon": 100, "fx_water_mist": 110, "fx_water_vortex": 100,
    "fx_lightning_strike": 60, "fx_static_field": 80, "fx_lightning_lance": 60,
    "fx_lightning_armor": 100, "fx_earth_spikes": 100, "fx_earth_collapse": 100,
    "fx_stone_shell": 100, "fx_mud_splash": 90, "fx_wind_slash": 80, "fx_wind_tornado": 90,
    "fx_wind_prison": 100, "fx_chakra_focus": 120, "fx_heal_green": 120, "fx_smoke_poof": 110,
    "fx_seal_glow": 100, "fx_shadow_clone": 110, "fx_melee_hit": 70, "fx_poison_mist": 120,
    "fx_chakra_blade": 70,
}

EFFECT_ID_BASE = 200
EFFECT_ORDER = [
    "fx_fire_burst", "fx_fire_ring", "fx_fire_cone", "fx_fire_dragon",
    "fx_water_splash", "fx_water_dragon", "fx_water_mist", "fx_water_vortex",
    "fx_lightning_strike", "fx_static_field", "fx_lightning_lance", "fx_lightning_armor",
    "fx_earth_spikes", "fx_earth_collapse", "fx_stone_shell", "fx_mud_splash",
    "fx_wind_slash", "fx_wind_tornado", "fx_wind_prison",
    "fx_chakra_focus", "fx_heal_green", "fx_smoke_poof", "fx_seal_glow", "fx_shadow_clone",
    "fx_melee_hit", "fx_poison_mist", "fx_chakra_blade",
]
assert len(EFFECT_ORDER) == len(set(EFFECT_ORDER)) == len(EFFECT_TEMPLATES)
EFFECT_IDS = {k: EFFECT_ID_BASE + i for i, k in enumerate(EFFECT_ORDER)}


# ------------------------------------------------------------- templates (missile)
def missile_fireball(pal):
    img = canvas()
    d = ImageDraw.Draw(img)
    for i, r in enumerate((9, 6, 3)):
        x = CX - 4 + i * 3
        d.ellipse([x - r, CY - r, x + r, CY + r],
                  fill=rgba(pal["main"] if i else pal["dark"], 160 if i == 0 else 255))
    d.ellipse([CX + 3, CY - 4, CX + 9, CY + 4], fill=rgba(pal["glow"]))
    return outline(img)


def missile_water_bullet(pal):
    img = canvas()
    d = ImageDraw.Draw(img)
    d.ellipse([CX - 3, CY - 6, CX + 9, CY + 6], fill=rgba(pal["main"]))
    d.ellipse([CX + 1, CY - 3, CX + 7, CY + 1], fill=rgba(pal["glow"]))
    d.polygon([(CX - 3, CY - 3), (CX - 9, CY), (CX - 3, CY + 3)], fill=rgba(pal["main"], 150))
    return outline(img)


def missile_lightning_needle(pal):
    img = canvas()
    d = ImageDraw.Draw(img)
    pts = _bolt_points(CX - 12, CY, CX + 12, CY, 5, seed=2)
    d.line(pts, fill=rgba(pal["glow"]), width=4)
    d.line(pts, fill=rgba(pal["main"]), width=2)
    d.polygon([(CX + 13, CY), (CX + 7, CY - 3), (CX + 7, CY + 3)], fill=rgba(pal["glow"]))
    return outline(img)


def missile_mud_bullet(pal):
    img = canvas()
    d = ImageDraw.Draw(img)
    d.ellipse([CX - 6, CY - 5, CX + 8, CY + 6], fill=rgba(pal["main"]))
    d.ellipse([CX - 2, CY - 2, CX + 3, CY + 2], fill=rgba(pal["dark"]))
    d.polygon([(CX - 6, CY), (CX - 11, CY - 2), (CX - 11, CY + 2)], fill=rgba(pal["dark"], 150))
    return outline(img)


def missile_wind_blade(pal):
    img = canvas()
    d = ImageDraw.Draw(img)
    d.polygon([(CX - 10, CY), (CX + 10, CY - 5), (CX + 10, CY + 5)], fill=rgba(pal["glow"], 210))
    d.line([(CX - 10, CY), (CX + 10, CY)], fill=rgba(pal["main"]), width=1)
    return outline(img)


def missile_kunai(pal):
    img = canvas()
    d = ImageDraw.Draw(img)
    d.polygon([(CX - 11, CY), (CX + 3, CY - 3), (CX + 3, CY + 3)], fill=rgba((206, 210, 220)))
    d.rectangle([CX + 3, CY - 2, CX + 11, CY + 2], fill=rgba((110, 78, 46)))
    d.ellipse([CX + 9, CY - 2, CX + 13, CY + 2], outline=rgba((70, 50, 30)))
    return outline(img)


def missile_shuriken(pal):
    img = canvas()
    d = ImageDraw.Draw(img)
    pts = _star_points(CX, CY, 10, 3, 4, rot=0.3)
    d.polygon(pts, fill=rgba((198, 202, 212)))
    d.ellipse([CX - 2, CY - 2, CX + 2, CY + 2], fill=rgba((90, 92, 100)))
    return outline(img)


def missile_senbon(pal):
    img = canvas()
    d = ImageDraw.Draw(img)
    d.line([(CX - 13, CY - 1), (CX + 12, CY - 1)], fill=rgba((150, 152, 162)), width=2)
    d.line([(CX - 13, CY), (CX + 12, CY)], fill=rgba((228, 230, 238)), width=2)
    d.polygon([(CX + 13, CY), (CX + 6, CY - 3), (CX + 6, CY + 3)], fill=rgba((228, 230, 238)))
    return outline(img)


MISSILE_FUNCS = {
    "ms_fireball": (missile_fireball, "katon", 0),
    "ms_water_bullet": (missile_water_bullet, "suiton", 0),
    "ms_lightning_needle": (missile_lightning_needle, "raiton", 0),
    "ms_mud_bullet": (missile_mud_bullet, "doton", 0),
    "ms_wind_blade": (missile_wind_blade, "fuuton", 0),
    "ms_kunai": (missile_kunai, "none", 0),
    "ms_shuriken": (missile_shuriken, "none", 0),
    "ms_senbon": (missile_senbon, "none", 0),
}
MISSILE_ID_BASE = 60
MISSILE_ORDER = ["ms_fireball", "ms_water_bullet", "ms_lightning_needle", "ms_mud_bullet",
                 "ms_wind_blade", "ms_kunai", "ms_shuriken", "ms_senbon"]
assert len(MISSILE_ORDER) == len(MISSILE_FUNCS)
MISSILE_IDS = {k: MISSILE_ID_BASE + i for i, k in enumerate(MISSILE_ORDER)}

# --------------------------------------------------------- slots "vanilla" (nome fixo)
# const -> (id, kind, reusa a arte de qual key nova)
VANILLA_SLOTS = [
    ("CONST_ME_FIREAREA", 7, "effect", "fx_fire_ring"),
    ("CONST_ME_ICEATTACK", 44, "effect", "fx_water_splash"),
    ("CONST_ME_ENERGYHIT", 12, "effect", "fx_lightning_strike"),
    ("CONST_ME_STONES", 45, "effect", "fx_earth_spikes"),
    ("CONST_ME_HOLYAREA", 50, "effect", "fx_wind_slash"),
    ("CONST_ME_HITAREA", 10, "effect", "fx_melee_hit"),
    ("CONST_ME_POFF", 3, "effect", "fx_smoke_poof"),
    ("CONST_ME_MAGIC_GREEN", 15, "effect", "fx_heal_green"),
    ("CONST_ANI_FIRE", 4, "missile", "ms_fireball"),
    ("CONST_ANI_ICE", 29, "missile", "ms_water_bullet"),
    ("CONST_ANI_ENERGY", 5, "missile", "ms_lightning_needle"),
    ("CONST_ANI_EARTH", 30, "missile", "ms_mud_bullet"),
    ("CONST_ANI_HOLY", 31, "missile", "ms_wind_blade"),
    ("CONST_ANI_THROWINGSTAR", 8, "missile", "ms_shuriken"),
]

# ------------------------------------------------- aliases: animation do jutsu -> key
# (data/jutsus/*.json ja tem o campo `animation` preenchido para os 54 jutsus;
#  este mapa escolhe, para cada string, qual arte do catalogo usar. Cobertura
#  completa dos 54 -- ver docs/sistemas/combate-e-jutsus.md.)
ALIASES = {
    "fx_mud_bullet": "ms_mud_bullet",
    "fx_stone_shell": "fx_stone_shell",
    "fx_earth_spikes": "fx_earth_spikes",
    "fx_earth_collapse": "fx_earth_collapse",
    "fx_wind_blade": "ms_wind_blade",
    "fx_wind_cone": "fx_wind_slash",
    "fx_wind_tornado": "fx_wind_tornado",
    "fx_wind_prison": "fx_wind_prison",
    "fx_fireball": "ms_fireball",
    "fx_fire_cone": "fx_fire_cone",
    "fx_fire_dragon": "fx_fire_dragon",
    "fx_ember_cone": "fx_fire_cone",
    "fx_fire_ring": "fx_fire_ring",
    "fx_log_poof": "fx_smoke_poof",
    "fx_clone_poof": "fx_shadow_clone",
    "fx_heal_glow": "fx_heal_green",
    "fx_seal_paper": "fx_seal_glow",
    "fx_poison_mist": "fx_poison_mist",
    "fx_smoke_puff": "fx_smoke_poof",
    "fx_taijutsu_hit": "fx_melee_hit",
    "fx_taijutsu_spin": "fx_melee_hit",
    "fx_needles": "ms_senbon",
    "fx_chakra_blade": "fx_chakra_blade",
    "fx_lightning_bolt": "ms_lightning_needle",
    "fx_wind_sweep": "fx_wind_slash",
    "fx_aura_orange": "fx_chakra_focus",
    "fx_eye_glow": "fx_chakra_focus",
    "fx_burning_needles": "ms_senbon",
    "fx_counter_strike": "fx_melee_hit",
    "fx_ground_crack": "fx_earth_collapse",
    "fx_palm_strike": "fx_melee_hit",
    "fx_eye_veins": "fx_chakra_focus",
    "fx_double_palm": "fx_melee_hit",
    "fx_heavy_punch": "fx_melee_hit",
    "fx_rising_kick": "fx_melee_hit",
    "fx_sword_spark": "fx_lightning_strike",
    "fx_double_slash": "fx_melee_hit",
    "fx_lightning_armor": "fx_lightning_armor",
    "fx_marked_kunai": "ms_kunai",
    "fx_flash_teleport": "fx_smoke_poof",
    "fx_seal_explosion": "fx_seal_glow",
    "fx_barrier_glow": "fx_chakra_focus",
    "fx_seal_circle": "fx_seal_glow",
    "fx_lightning_needle": "ms_lightning_needle",
    "fx_thunder_fist": "fx_lightning_strike",
    "fx_static_cross": "fx_static_field",
    "fx_lightning_lance": "fx_lightning_lance",
    "fx_water_bullet": "ms_water_bullet",
    "fx_water_dragon": "fx_water_dragon",
    "fx_mist_cone": "fx_water_mist",
    "fx_water_prison": "fx_water_vortex",
    "fx_water_vortex": "fx_water_vortex",
}

ELEMENT_DEFAULTS = {
    "katon": {"effect": "fx_fire_burst", "missile": "ms_fireball"},
    "suiton": {"effect": "fx_water_splash", "missile": "ms_water_bullet"},
    "raiton": {"effect": "fx_lightning_strike", "missile": "ms_lightning_needle"},
    "doton": {"effect": "fx_mud_splash", "missile": "ms_mud_bullet"},
    "fuuton": {"effect": "fx_wind_slash", "missile": "ms_wind_blade"},
    "none": {"effect": "fx_melee_hit", "missile": "ms_senbon"},
}


# ---------------------------------------------------------------------- build
def gen_frames():
    """key -> list[Image] (32x32 RGBA)."""
    out = {}
    for key, (fn, kwargs, elem) in EFFECT_TEMPLATES.items():
        out[key] = fn(PALETTES[elem], **kwargs)
    for key, (fn, elem, _rot) in MISSILE_FUNCS.items():
        out[key] = [fn(PALETTES[elem])]
    return out


def save_pngs(frames):
    os.makedirs(SRC_DIR, exist_ok=True)
    for key, imgs in frames.items():
        d = os.path.join(SRC_DIR, key)
        os.makedirs(d, exist_ok=True)
        for i, img in enumerate(imgs):
            img.save(os.path.join(d, "f%d.png" % i))


def write_review_sheet(frames):
    """Uma folha so para OLHAR (Read) antes de integrar: uma linha por efeito/
    missile, colunas = fases, nome escrito ao lado (label como frame extra)."""
    os.makedirs(REVIEW_DIR, exist_ok=True)
    keys = EFFECT_ORDER + MISSILE_ORDER
    max_frames = max(len(v) for v in frames.values())
    label_w = 108
    row_h = CELL + 4
    sheet = Image.new("RGBA", (label_w + max_frames * (CELL + 2), len(keys) * row_h),
                       (40, 40, 46, 255))
    from PIL import ImageFont
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    d = ImageDraw.Draw(sheet)
    for row, key in enumerate(keys):
        y = row * row_h
        cid = EFFECT_IDS.get(key) or MISSILE_IDS.get(key)
        d.text((4, y + row_h // 2 - 5), "%3d %s" % (cid, key), fill=(230, 230, 230, 255), font=font)
        for i, img in enumerate(frames[key]):
            sheet.paste(img, (label_w + i * (CELL + 2), y), img)
    sheet.save(os.path.join(REVIEW_DIR, "_sheet.png"))
    print("folha de revisao: %s (%dx%d) -- OLHE antes de integrar"
          % (os.path.relpath(os.path.join(REVIEW_DIR, "_sheet.png"), ROOT),
             sheet.width, sheet.height))


def build_missile_sheet(key):
    """Roda o unico frame (aponta p/ direita, angulo 0) em 3x3 -- mesma tecnica
    de imports.py Importer.missile()."""
    frame_path = os.path.join(SRC_DIR, key, "f0.png")
    return os.path.relpath(frame_path, SPRITES).replace(os.sep, "/")


def write_effects_json():
    entries = []
    for key in EFFECT_ORDER:
        entries.append({
            "key": key, "kind": "effect", "id": EFFECT_IDS[key],
            "element": EFFECT_TEMPLATES[key][2],
            "frames": len(gen_frames_cache[key]),
            "duration_ms": EFFECT_DURATIONS[key],
        })
    for key in MISSILE_ORDER:
        entries.append({
            "key": key, "kind": "missile", "id": MISSILE_IDS[key],
            "element": MISSILE_FUNCS[key][1], "frames": 1, "duration_ms": None,
        })
    doc = {
        "_doc": ("Catalogo de efeitos/misseis proprios (ADR-002, arte por codigo). "
                 "Gerado por tools/spr/gen_effects.py -- NAO EDITE A MAO os PNGs em "
                 "assets-src/sprites/effects_src/; edite o script e rode de novo. "
                 "IDs sao PERMANENTES (protocolo 10.98, effect/missile = u8): nunca "
                 "renumere uma key ja publicada, so adicione novas no fim de "
                 "EFFECT_ORDER/MISSILE_ORDER. `aliases` mapeia o campo `animation` de "
                 "data/jutsus/*.json para uma key deste catalogo; `element_defaults` "
                 "e o fallback (impacto de projetil, elemento sem alias especifico). "
                 "`vanilla_slots` documenta os ids CONST_ME_*/CONST_ANI_* que o "
                 "servidor referencia por NOME (data/tfs_mapping.json, monstros) e que "
                 "tambem foram redesenhados (mesma arte de uma key nova, so replicada "
                 "no id antigo) porque Monsters::deserializeSpell so aceita nome fixo, "
                 "nunca numero cru (server/tfs/src/monsters.cpp + tools.cpp)."),
        "effect_id_base": EFFECT_ID_BASE, "missile_id_base": MISSILE_ID_BASE,
        "entries": entries,
        "vanilla_slots": [{"const": c, "id": i, "kind": k, "reuses": r}
                          for c, i, k, r in VANILLA_SLOTS],
        "element_defaults": ELEMENT_DEFAULTS,
        "aliases": ALIASES,
    }
    with open(CATALOG_PATH, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("%s: %d efeitos + %d misseis + %d slots vanilla"
          % (os.path.relpath(CATALOG_PATH, ROOT), len(EFFECT_ORDER), len(MISSILE_ORDER),
             len(VANILLA_SLOTS)))


def write_override():
    """Escreve assets-src/sprites/overrides/50_effects_naruto.json no MESMO
    esquema de imports.json (root/build_dir/effects/missiles) -- build_assets.py
    ja varre assets-src/sprites/overrides/*.json e aplica cada um via
    imports.apply(); nao precisa mudar build_assets.py."""
    root_rel = os.path.relpath(SRC_DIR, ROOT).replace(os.sep, "/")
    build_dir_rel = os.path.relpath(SHEETS_DIR, ROOT).replace(os.sep, "/")

    def frame_rel(key, i):
        return "%s/f%d.png" % (key, i)

    effects = []
    for key in EFFECT_ORDER:
        n = len(gen_frames_cache[key])
        effects.append({
            "id": EFFECT_IDS[key], "name": key,
            "frames": [frame_rel(key, i) for i in range(n)],
            "duration": EFFECT_DURATIONS[key],
        })
    for const, cid, kind, reuse_key in VANILLA_SLOTS:
        if kind != "effect":
            continue
        n = len(gen_frames_cache[reuse_key])
        effects.append({
            "id": cid, "name": "%s_slot" % reuse_key,
            "frames": [frame_rel(reuse_key, i) for i in range(n)],
            "duration": EFFECT_DURATIONS[reuse_key],
        })
    missiles = []
    for key in MISSILE_ORDER:
        missiles.append({
            "id": MISSILE_IDS[key], "name": key,
            "src": frame_rel(key, 0), "rotate": 0,
        })
    for const, cid, kind, reuse_key in VANILLA_SLOTS:
        if kind != "missile":
            continue
        missiles.append({
            "id": cid, "name": "%s_slot" % reuse_key,
            "src": frame_rel(reuse_key, 0), "rotate": 0,
        })

    cfg = {
        "_doc": ("GERADO por tools/spr/gen_effects.py -- NAO EDITE A MAO. Mesmo "
                 "esquema de assets-src/sprites/imports.json (root/build_dir/effects/"
                 "missiles); tools/spr/build_assets.py aplica todo *.json de "
                 "assets-src/sprites/overrides/ automaticamente."),
        "root": root_rel, "build_dir": build_dir_rel,
        "effects": effects, "missiles": missiles,
    }
    os.makedirs(os.path.dirname(OVERRIDE_PATH), exist_ok=True)
    with open(OVERRIDE_PATH, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("%s: %d efeitos + %d misseis (inclui %d slots vanilla redesenhados)"
          % (os.path.relpath(OVERRIDE_PATH, ROOT), len(effects), len(missiles),
             len(VANILLA_SLOTS)))


gen_frames_cache = {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet-only", action="store_true",
                    help="so regenera a folha de revisao (nao mexe no catalogo/override)")
    args = ap.parse_args()

    global gen_frames_cache
    frames = gen_frames()
    gen_frames_cache = frames

    save_pngs(frames)
    write_review_sheet(frames)
    if args.sheet_only:
        return
    write_effects_json()
    write_override()

    total = sum(len(v) for v in frames.values())
    print("total: %d chaves, %d PNGs de fase" % (len(frames), total))
    print("ids novos: efeitos %d..%d, misseis %d..%d"
          % (EFFECT_ID_BASE, EFFECT_ID_BASE + len(EFFECT_ORDER) - 1,
             MISSILE_ID_BASE, MISSILE_ID_BASE + len(MISSILE_ORDER) - 1))


if __name__ == "__main__":
    main()
