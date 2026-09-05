#!/usr/bin/env python3
"""Gera a folha de icones dos jutsus para a Lista de Jutsus / barra de acao do OTClient.

Arte propria, desenhada por codigo (ADR-002): nenhum pixel vem da Tibia ou de outro jogo.

Saida: client-otc/data/images/game/spells/jutsus.png
Formato: tira horizontal de N icones 32x32 (o OTClient recorta com
`indexClip * 32 0 32 32`, ver Spells.getImageClip em modules/gamelib/spells.lua).

Ordem dos icones: MESMA de tools/export_tfs.py (jutsu_icon_order) — por elemento
(katon, suiton, raiton, doton, fuuton, none) e, dentro do elemento, por tier,
level exigido e id. O indice na tira vira o `clientId` da entrada em NarutoSpellInfo.

Cor por elemento; simbolo por tipo de jutsu:
  projectile / target -> bola      area -> anel
  beam                -> linha     self -> silhueta
  self que cura       -> cruz

Uso: .venv/bin/python tools/spr/gen_jutsu_icons.py
"""
import glob
import json
import os
import re
import sys

from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
DATA = os.path.join(ROOT, "data", "jutsus")
OUT = os.path.join(ROOT, "client-otc", "data", "images", "game", "spells", "jutsus.png")
ORDER_OUT = os.path.join(ROOT, "assets-src", "sprites", "jutsu_icon_order.json")
LUA_DATA = os.path.join(ROOT, "client-otc", "modules", "naruto_theme", "jutsus_data.lua")

CELL = 32

# ordem estavel dos elementos na folha
ELEMENT_ORDER = ["katon", "suiton", "raiton", "doton", "fuuton", "none"]

# (cor principal do simbolo, cor secundaria/brilho, cor de fundo escura)
ELEMENT_COLORS = {
    "katon": ((255, 138, 46), (255, 226, 150), (58, 22, 14)),
    "suiton": ((72, 150, 240), (176, 224, 255), (14, 30, 56)),
    "raiton": ((248, 220, 72), (255, 250, 200), (52, 46, 12)),
    "doton": ((166, 116, 66), (226, 190, 146), (46, 32, 18)),
    "fuuton": ((146, 226, 128), (216, 250, 200), (22, 46, 26)),
    "none": ((168, 172, 182), (232, 234, 240), (34, 34, 40)),
}

BORDER = (206, 200, 186, 255)
BORDER_DARK = (16, 14, 18, 255)


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


def load_jutsus():
    out = []
    for path in sorted(glob.glob(os.path.join(DATA, "*.json"))):
        with open(path, encoding="utf-8") as f:
            out.extend(json.load(f))
    return out


def jutsu_icon_order(jutsus):
    """Ordem estavel dos icones. Duplicada em tools/export_tfs.py — mantenha as duas iguais."""

    def key(j):
        el = j.get("element", "none")
        return (
            ELEMENT_ORDER.index(el) if el in ELEMENT_ORDER else len(ELEMENT_ORDER),
            int(j.get("tier", 1)),
            int(j.get("required_level", 1)),
            j["id"],
        )

    return sorted(jutsus, key=key)


def symbol_of(j):
    t = j.get("type", "projectile")
    if t == "self":
        for e in j.get("effects", []) or []:
            if "heal" in e.get("type", ""):
                return "cross"
        return "self"
    if t == "area":
        return "ring"
    if t == "beam":
        return "line"
    return "ball"  # projectile e target


def draw_frame(d, bg):
    """Fundo escuro com borda clara, estilo icone de spell da Tibia (mas desenhado do zero)."""
    d.rectangle([0, 0, CELL - 1, CELL - 1], fill=BORDER_DARK)
    d.rectangle([1, 1, CELL - 2, CELL - 2], fill=BORDER)
    d.rectangle([2, 2, CELL - 3, CELL - 3], fill=rgba(bg))
    # bisel: linha clara em cima/esquerda, escura em baixo/direita
    d.line([2, 2, CELL - 3, 2], fill=(255, 255, 255, 30))
    d.line([2, 2, 2, CELL - 3], fill=(255, 255, 255, 22))
    d.line([2, CELL - 3, CELL - 3, CELL - 3], fill=(0, 0, 0, 60))
    d.line([CELL - 3, 2, CELL - 3, CELL - 3], fill=(0, 0, 0, 60))


def draw_ball(d, main, glow):
    d.ellipse([9, 9, 23, 23], fill=rgba(main), outline=rgba(glow))
    d.ellipse([12, 12, 16, 16], fill=rgba(glow))


def draw_ring(d, main, glow):
    d.ellipse([6, 6, 26, 26], outline=rgba(main), width=3)
    d.ellipse([11, 11, 21, 21], outline=rgba(glow), width=1)


def draw_line(d, main, glow):
    d.line([6, 24, 25, 7], fill=rgba(main), width=5)
    d.line([7, 23, 24, 8], fill=rgba(glow), width=1)
    d.polygon([(25, 5), (28, 12), (21, 10)], fill=rgba(glow))


def draw_cross(d, main, glow):
    d.rectangle([14, 7, 18, 25], fill=rgba(main))
    d.rectangle([7, 14, 25, 18], fill=rgba(main))
    d.rectangle([15, 8, 17, 24], fill=rgba(glow))
    d.rectangle([8, 15, 24, 17], fill=rgba(glow))


def draw_self(d, main, glow):
    # silhueta de ninja: cabeca + tronco + bracos
    d.ellipse([13, 6, 19, 12], fill=rgba(glow))
    d.polygon([(16, 12), (23, 20), (21, 26), (11, 26), (9, 20)], fill=rgba(main))
    d.line([10, 15, 6, 21], fill=rgba(main), width=2)
    d.line([22, 15, 26, 21], fill=rgba(main), width=2)


SYMBOLS = {
    "ball": draw_ball,
    "ring": draw_ring,
    "line": draw_line,
    "cross": draw_cross,
    "self": draw_self,
}


def icon(j):
    main, glow, bg = ELEMENT_COLORS.get(j.get("element", "none"), ELEMENT_COLORS["none"])
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    draw_frame(d, bg)
    SYMBOLS[symbol_of(j)](d, main, glow)
    # marcador de tier: pontinhos no canto inferior direito
    tier = max(1, min(3, int(j.get("tier", 1))))
    for k in range(tier):
        x = 27 - k * 4
        d.rectangle([x - 1, 26, x + 1, 28], fill=rgba(glow))
        d.point((x, 27), fill=rgba(main))
    return img


def write_order_file(jutsus):
    """Grava assets-src/sprites/jutsu_icon_order.json — fonte de verdade UNICA e
    versionada da ordem dos icones na folha. tools/export_tfs.py NAO le este
    arquivo (nao pode ser editado por este trabalho); ele recalcula a mesma
    ordem com a MESMA formula (jutsu_icon_order, duplicada de proposito nos
    dois lugares). Este arquivo serve para (1) auditar/diffar mudanca de ordem
    entre commits e (2) validar() abaixo, que compara este calculo contra o
    jutsus_data.lua ja gerado e falha ALTO (exit != 0) se divergir — em vez de
    um icone errado silencioso in-game (a causa raiz do bug historico: os dois
    arquivos gerados por comandos SEPARADOS, sem nada que garanta que rodam
    juntos apos data/jutsus/*.json mudar)."""
    order = [{"index": i, "id": j["id"], "element": j.get("element", "none"),
              "tier": int(j.get("tier", 1)), "required_level": int(j.get("required_level", 1))}
             for i, j in enumerate(jutsus)]
    doc = {
        "_doc": "Ordem CANONICA dos icones em client-otc/data/images/game/spells/jutsus.png, "
                "gerada por tools/spr/gen_jutsu_icons.py (funcao jutsu_icon_order). "
                "tools/export_tfs.py recalcula a MESMA ordem (mesma formula, duplicada) para "
                "preencher clientId em NarutoSpellInfo/jutsus_data.lua — os dois PRECISAM ficar "
                "iguais. Este arquivo e o registro auditavel dessa ordem; gen_jutsu_icons.py "
                "valida contra jutsus_data.lua toda vez que roda (ver validate_against_lua).",
        "count": len(order),
        "order": order,
    }
    os.makedirs(os.path.dirname(ORDER_OUT), exist_ok=True)
    with open(ORDER_OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return ORDER_OUT


def validate_against_lua(jutsus):
    """Compara a ordem calculada aqui contra o clientId/icon ja gravados em
    jutsus_data.lua (gerado por tools/export_tfs.py, que este trabalho NAO
    pode editar). Divergencia = a causa raiz do bug de icone cortado/errado:
    jutsus.png e jutsus_data.lua desalinhados porque um foi regenerado sem o
    outro depois que data/jutsus/*.json mudou de tamanho. Nao falha (so avisa)
    se o arquivo lua nao existir, para o script continuar util isoladamente."""
    if not os.path.exists(LUA_DATA):
        print("aviso: jutsus_data.lua nao encontrado, pulei a validacao de indice")
        return True
    with open(LUA_DATA, encoding="cp1252", errors="replace") as f:
        lua = f.read()
    pairs = re.findall(r"icon\s*=\s*'([^']*)'\s*,\s*clientId\s*=\s*(\d+)", lua)
    lua_by_index = {int(idx): icon_id for icon_id, idx in pairs}
    divergences = []
    if len(lua_by_index) != len(jutsus):
        divergences.append(
            f"contagem diferente: jutsus_data.lua tem {len(lua_by_index)} entradas, "
            f"data/jutsus/*.json tem {len(jutsus)} — jutsus.png teria {len(jutsus)} icones "
            f"({len(jutsus) * CELL}px) mas o clientId maximo no lua pressupoe outra largura"
        )
    for i, j in enumerate(jutsus):
        lua_id = lua_by_index.get(i)
        if lua_id is None:
            divergences.append(f"  indice {i} ({j['id']}): sem entrada correspondente em jutsus_data.lua")
        elif lua_id != j["id"]:
            divergences.append(f"  indice {i}: gen_jutsu_icons.py calcula '{j['id']}', jutsus_data.lua tem '{lua_id}'")
    if divergences:
        print("DIVERGENCIA jutsus.png x jutsus_data.lua (rode tools/export_tfs.py e gen_jutsu_icons.py "
              "juntos, na mesma versao de data/jutsus/*.json):")
        for d in divergences:
            print(" ", d)
        return False
    print(f"validacao de indice: OK, divergencias=0 ({len(jutsus)} jutsus, jutsus_data.lua e jutsus.png alinhados)")
    return True


def main():
    jutsus = jutsu_icon_order(load_jutsus())
    sheet = Image.new("RGBA", (CELL * len(jutsus), CELL), (0, 0, 0, 0))
    for i, j in enumerate(jutsus):
        sheet.paste(icon(j), (i * CELL, 0))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    sheet.save(OUT)
    print(f"{os.path.relpath(OUT, ROOT)}: {len(jutsus)} icones ({sheet.width}x{sheet.height})")
    for i, j in enumerate(jutsus):
        print(f"  [{i:2d}] {j['id']:28s} {j.get('element'):7s} {symbol_of(j)}")
    order_path = write_order_file(jutsus)
    print(f"{os.path.relpath(order_path, ROOT)}: gravado ({len(jutsus)} entradas)")
    ok = validate_against_lua(jutsus)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
