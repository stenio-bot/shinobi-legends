#!/usr/bin/env python3
"""Gera variantes de PALETA para looktypes humanoides IMPORTADOS que hoje sao
compartilhados por varios monstros SEM nenhuma diferenca visual (mesma arte,
mesma cor) — ver docs/backlog-sprites.md, secao de continuacao da missao de
criaturas procedurais.

Diferente de gen_animals.py (que desenha geometria nova em camada 0 clara +
camada 1 de mascara, layers=2, para o CLIENTE recolorir via head/body/legs/
feet), aqui a arte e IMPORTADA (assets-src/import/extracted/..., material
privado do usuario, fora do git — ADR-002: a arte em si nao muda) e ja vem
com layers=1 (cor final gravada no pixel — ver imports.py:Importer.creature,
FORMATO.md secao 3.5 confirma que so layers>=2 ganha mascara de outfit).
Para dar cores DIFERENTES a monstros que compartilham esse mesmo looktype
importado, a unica opcao e gerar uma copia do sprite com a matiz (HSV)
girada — por isso este script fica separado de gen_animals.py.

Como funciona:
1. Le a MESMA imagem-fonte que assets-src/sprites/imports.json ja usa para o
   looktype base (por exemplo id 129 "ninja_bandit" -> monsters_sheet/12.png).
2. Monta a folha exatamente como tools/spr/imports.py:Importer.creature() faz
   quando a entrada nao tem "directions": a MESMA imagem nas 4 direcoes e nas
   3 fases de andar (a arte importada nao tem direcao real nem ciclo de
   andar proprio — limitacao conhecida, ja documentada em docs/backlog-sprites.md;
   este script NAO tenta consertar isso, so a cor).
3. Calcula a matiz DOMINANTE dos pixels opacos e saturados da imagem (ignora
   cinzas/pretos de contorno e sombreado) e roda a matiz de TODO pixel opaco
   por um delta fixo que leva essa matiz ate a matiz-alvo (data/tibia_colors.py
   NAMED, convertido de indice de paleta Tibia para RGB). Saturacao e valor
   (brilho/sombra/contorno) ficam INTOCADOS — e o que "preserva sombreamento"
   pedido na missao.
4. Para o glacier_oni (looktype 12, folha 3x3), tambem reduz a caixa final
   para 2x2 (redimensiona a arte, mantendo proporcao, ancorada embaixo).

Uso:  .venv/bin/python tools/spr/gen_humanoid_variants.py
Saida: assets-src/sprites/creatures/look_9NN.png (layers=1, 1 arquivo por
       looktype novo) + assets-src/sprites/overrides/61_humanoid_variants.json
       (mesma chave "creature_sheets" de 60_animals.json — consumida por
       tools/spr/imports.py:apply()).

Os looktypes BASE (128/129/130/131/138/12) NAO sao tocados por este script:
continuam com a arte crua do import, sem hue-shift, e continuam servindo o
monstro "titular" de cada grupo (o que faz mais sentido lore-wise) + o
outfit padrao do jogador (128) — ver VARIANTS abaixo e o comentario de cada
entrada para o motivo da escolha.

Nenhum pixel vem da Tibia, de NTO ou de outro jogo (ADR-002): a arte de base
e material privado do usuario ja aprovado para o projeto (assets-src/import/),
e a unica transformacao aqui e uma rotacao de matiz por codigo.
"""
import json
import os
import sys
import colorsys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image

import imports as IMP          # noqa: E402  (fit, _trim, _binarize)
import tibia_colors as TC       # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SPRITES_DIR = os.path.join(ROOT, "assets-src", "sprites")
OUT = SPRITES_DIR
OVERRIDES_PATH = os.path.join(SPRITES_DIR, "overrides", "61_humanoid_variants.json")
IMPORTS_JSON_PATH = os.path.join(SPRITES_DIR, "imports.json")

CELL = 32
DIRECTIONS = 4
PHASES_IDLE = 1
PHASES_MOVING = 3


def _target_rgb(named_key):
    """RGB "de lore" (pre-quantizacao), nao o indice 0..132 da paleta de
    outfit. Ver comentario de tibia_colors.py:RAW — quantizar aqui faria o
    alvo do hue-shift virar cinza pra varias cores abafadas (oliva, navy,
    ardosia), porque a paleta real do outfit so tem 133 cores esparsas."""
    return TC.RAW[named_key]


# id novo (946..957) -> dados da variante. `base` = looktype importado de
# origem (chave em assets-src/sprites/imports.json:creatures, usada so pra
# achar src/tiles — a entrada BASE do manifesto continua intocada). `tiles_out`
# so aparece quando difere do tiles da base (glacier_oni: 3 -> 2).
VARIANTS = [
    # --- grupo 129 "ninja_bandit" — a arte-base (monsters_sheet/12.png) e
    # AZUL/ROXA como as outras (nao marrom!), entao os 4 monstros do grupo
    # ganham variante propria; base 129 fica sem uso por estes 4 (continua
    # servindo elite_cloud_guard/exam_rival_sound, fora do escopo desta
    # missao) ---
    dict(id=946, base=129, monster="bandit_archer",
         target=_target_rgb("olive_archer"),
         note="Bandido Arqueiro — verde-oliva (recolor de 129 'ninja_bandit')."),
    dict(id=947, base=129, monster="mercenary_bridge",
         target=_target_rgb("navy_mercenary"),
         note="Mercenário da Ponte — azul-marinho escuro (recolor de 129)."),
    dict(id=948, base=129, monster="ruin_puppet",
         target=_target_rgb("wood_puppet"),
         note="Marionete de Combate — tom de madeira (recolor de 129), reforça "
              "que é um boneco, não um humano."),
    dict(id=956, base=129, monster="bandit",
         target=_target_rgb("brown_bandit"),
         note="Bandido — marrom (recolor de 129), o próprio nome do looktype "
              "vanilla ('ninja_bandit') sugeria marrom mas a arte real é azul."),

    # --- grupo 128 "ninja_blue" (o outfit padrao do jogador TAMBEM e 128 —
    # por isso NENHUM monstro fica na base: os dois ganham variante propria) ---
    dict(id=949, base=128, monster="mist_scout",
         target=_target_rgb("mist_scout_teal"),
         note="Batedor da Névoa — verde-azulado enevoado (recolor de 128)."),
    dict(id=950, base=128, monster="rogue_ninja",
         target=_target_rgb("rogue_slate"),
         note="Ninja Renegado — cinza-ardósia (recolor de 128); antes usava o "
              "mesmo looktype do outfit do jogador, o que confundia em jogo."),

    # --- grupo 131 "ninja_chief" — a arte-base (monsters_sheet/9.png) e
    # bege/caqui (nao vermelho/preto nem azulado), entao os 3 monstros do
    # grupo ganham variante propria; base 131 fica sem uso por estes 3 ---
    dict(id=951, base=131, monster="mist_guardian",
         target=_target_rgb("mist_guardian_steel"),
         note="Guardião da Neblina — cinza-azulado de aço (recolor de 131)."),
    dict(id=952, base=131, monster="boss_puppeteer",
         target=_target_rgb("puppeteer_violet"),
         note="Marionetista das Ruínas — violeta (recolor de 131)."),
    dict(id=957, base=131, monster="boss_bandit_chief",
         target=_target_rgb("chief_red"),
         note="Chefe dos Bandidos — vermelho/preto (recolor de 131); distingue "
              "do Guardião da Neblina e do Marionetista, que também usam 131."),

    # --- grupo 130 "ninja_pale" (masked_apprentice fica na base, pálido, "
    # já combina com Haku) ---
    dict(id=953, base=130, monster="spectral_warrior",
         target=_target_rgb("spectral_pale_purple"),
         note="Guerreiro Espectral — roxo-pálido (recolor de 130)."),

    # --- grupo 138 "hooded_purple" (curse_shaman fica na base, roxo escuro,
    # já é a cor pedida pro xamã) ---
    dict(id=954, base=138, monster="boss_curse_partner",
         target=_target_rgb("curse_partner_red"),
         note="O Sócio Eterno — vermelho (recolor de 138), contraste com o "
              "roxo escuro do Xamã da Maldição (a outra metade da Dupla "
              "Imortal)."),

    # --- grupo 12 "oni_fox" (boss_ancestral_oni fica na base: raposa "
    # vermelha ancestral combina com a Nuvem Vermelha; glacier_oni precisa "
    # de gelo, nao de fogo, e reduz de 3x3 pra 2x2) ---
    dict(id=955, base=12, monster="glacier_oni",
         target=_target_rgb("oni_icy_blue"),
         tiles_out=2,
         note="Oni da Geleira — azul-gelo (recolor de 12 'oni_fox'), caixa "
              "reduzida de 3x3 para 2x2 (a raposa de origem é grande demais "
              "pro monstro de nível baixo que ele é)."),
]


def _load_imports_json():
    with open(IMPORTS_JSON_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _base_entry(imports_cfg, looktype):
    for e in imports_cfg.get("creatures", []):
        if e["id"] == looktype:
            return e
    raise SystemExit("gen_humanoid_variants: looktype base %d nao existe em "
                      "imports.json:creatures" % looktype)


def _open_source(imports_cfg, entry):
    src_root = os.path.join(ROOT, imports_cfg.get("root", "assets-src/import/extracted"))
    path = os.path.join(src_root, entry["src"])
    if not os.path.exists(path):
        print("gen_humanoid_variants: AVISO: fonte ausente (%s) — pulando %s"
              % (path, entry.get("name")))
        return None
    img = Image.open(path).convert("RGBA")
    crop = entry.get("crop")
    if crop:
        img = img.crop((crop[0], crop[1], crop[0] + crop[2], crop[1] + crop[3]))
    return img


def _dominant_hue(img, min_sat=0.15, min_alpha=128, bins=72, win_radius=6):
    """Matiz "principal" da roupa/pelagem: histograma de matiz (so pixels
    opacos e minimamente saturados, pra ignorar contorno/sombra quase cinza),
    depois acha a JANELA circular de +-win_radius bins com mais pixels no
    total (nao o bin isolado mais alto — um brasao/cinto pequeno mas bem
    saturado pode ter um bin mais alto que qualquer bin isolado da roupa,
    mas a ROUPA (area grande, matiz espalhada pela sombra) ganha em soma de
    janela). O valor final e a media circular ponderada dentro dessa janela."""
    import math
    px = img.load()
    hist = [0.0] * bins
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a < min_alpha:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            if s < min_sat or v < 0.08:
                continue
            hist[int(h * bins) % bins] += 1
    if not any(hist):
        return 0.0

    totals = []
    for c in range(bins):
        totals.append(sum(hist[(c + off) % bins] for off in range(-win_radius, win_radius + 1)))
    peak = max(range(bins), key=lambda i: totals[i])

    sum_sin = sum_cos = wsum = 0.0
    for off in range(-win_radius, win_radius + 1):
        i = (peak + off) % bins
        w = hist[i]
        if w <= 0:
            continue
        hcenter = (i + 0.5) / bins
        ang = hcenter * 2 * math.pi
        sum_sin += math.sin(ang) * w
        sum_cos += math.cos(ang) * w
        wsum += w
    if wsum <= 0:
        return (peak + 0.5) / bins
    ang = math.atan2(sum_sin, sum_cos)
    if ang < 0:
        ang += 2 * math.pi
    return ang / (2 * math.pi)


def hue_shift(img, target_rgb, tol_in_deg=38.0, tol_out_deg=58.0, min_alpha=1,
              sat_boost=1.6):
    """Roda a matiz SO dos pixels perto da matiz dominante (a "roupa"), por um
    delta fixo que leva essa matiz ate a matiz-alvo. Pele, cabelo escuro/preto
    (baixa saturacao, ja ignorado), metal de arma e qualquer acento de cor bem
    diferente (ex: um brasao vermelho isolado numa roupa azul) ficam FORA da
    janela de tolerancia e continuam com a cor original — do contrario girar
    a matiz da roupa por ~180 graus (azul -> oliva, por exemplo) giraria a
    pele junto e o resultado saia sujo/errado. Entre tol_in e tol_out a
    influencia cai suavemente (sem risco de corte duro pixel a pixel).

    Valor (brilho/sombra) SEMPRE fica intocado: e o que preserva sombreamento.
    Saturacao ganha um empurrao (`sat_boost`, tambem ponderado por `weight`):
    varias roupas de origem sao bem dessaturadas (azul-acinzentado, bege), e
    so girar a matiz sem realcar a saturacao da um tom "sujo"/lavado que nao
    lembra a cor-alvo pedida (ex: "vermelho" saindo cinza-rosado)."""
    th, ts, tv = colorsys.rgb_to_hsv(target_rgb[0] / 255.0, target_rgb[1] / 255.0,
                                      target_rgb[2] / 255.0)
    src_h = _dominant_hue(img)
    delta = (th - src_h) % 1.0
    if delta > 0.5:
        delta -= 1.0                 # caminho mais curto no circulo (pode ser negativo)

    tol_in = tol_in_deg / 360.0
    tol_out = tol_out_deg / 360.0

    out = img.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a < min_alpha:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            if s < 0.03:
                continue                     # cinza/preto puro: nao tem matiz p/ girar
            dist = abs(h - src_h)
            dist = min(dist, 1.0 - dist)     # distancia circular
            if dist >= tol_out:
                continue                     # fora da janela: pixel nao eh "roupa", nao mexe
            if dist <= tol_in:
                weight = 1.0
            else:
                weight = 1.0 - (dist - tol_in) / (tol_out - tol_in)
            h = (h + delta * weight) % 1.0
            s_boosted = min(1.0, s * sat_boost)
            s = s + (s_boosted - s) * weight
            nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
            px[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255), a)
    return out


def _resize_tiles(img, tiles_in, tiles_out):
    """Reduz (ou aumenta) a caixa final de tiles_in*32 para tiles_out*32,
    mantendo proporcao e ancorando embaixo (mesma convencao de imports.fit)."""
    box_in = tiles_in * CELL
    box_out = tiles_out * CELL
    trimmed = IMP._trim(img)
    s = min(box_out / trimmed.width, box_out / trimmed.height, box_out / float(box_in))
    if s < 1.0 or (tiles_out < tiles_in):
        scale = box_out / float(box_in)
        new_w = max(1, round(trimmed.width * scale))
        new_h = max(1, round(trimmed.height * scale))
        trimmed = trimmed.resize((new_w, new_h), Image.LANCZOS)
    out = Image.new("RGBA", (box_out, box_out), (0, 0, 0, 0))
    x = (box_out - trimmed.width) // 2
    y = box_out - trimmed.height
    out.paste(trimmed, (x, max(0, y)))
    return out


def save(img, relpath):
    path = os.path.join(OUT, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return relpath.replace(os.sep, "/")


def build_variant(imports_cfg, spec):
    base_entry = _base_entry(imports_cfg, spec["base"])
    src = _open_source(imports_cfg, base_entry)
    if src is None:
        return None

    tiles_in = int(base_entry.get("tiles") or 1)
    tiles_out = int(spec.get("tiles_out") or tiles_in)

    cell = IMP.fit(src, tiles_in)
    recolored = hue_shift(cell, spec["target"])
    if tiles_out != tiles_in:
        recolored = _resize_tiles(recolored, tiles_in, tiles_out)
    box = tiles_out * CELL

    rows = PHASES_IDLE + PHASES_MOVING
    sh = Image.new("RGBA", (DIRECTIONS * box, rows * box), (0, 0, 0, 0))
    for row in range(rows):
        for d in range(DIRECTIONS):
            sh.paste(recolored, (d * box, row * box))
    rel = save(sh, "creatures/look_%03d.png" % spec["id"])

    return {
        "category": "creature",
        "id": spec["id"],
        "name": "variant_%s_%03d" % (spec["monster"], spec["id"]),
        "width": tiles_out, "height": tiles_out, "exact_size": min(255, box),
        "layers": 1,                # recolor de arte importada, sem mascara
        "pattern_x": DIRECTIONS, "pattern_y": 1, "pattern_z": 1,
        "frame_groups": [
            {"type": 0, "phases": PHASES_IDLE},
            {"type": 1, "phases": PHASES_MOVING,
             "animation": {"async": False, "loop_count": 0, "start_phase": 0,
                           "durations": [[220, 220]] * PHASES_MOVING}},
        ],
        "sheets": [rel],
        "_doc": "%s. Base: looktype %d (%s, %s). Gerado por "
                "tools/spr/gen_humanoid_variants.py — nao editar a mao."
                % (spec["note"], spec["base"], base_entry["name"], base_entry["src"]),
    }


def write_overrides(things):
    cfg = {
        "format": 1,
        "_doc": (
            "Variantes de PALETA (hue-shift) para looktypes humanoides importados "
            "que ficariam com cor identica compartilhando o mesmo looktype base "
            "(veja assets-src/sprites/imports.json:creatures) — gerado por "
            "tools/spr/gen_humanoid_variants.py. Mesmo mecanismo de overrides/"
            "60_animals.json ('creature_sheets', aplicado por build_assets.py via "
            "imports.apply()), mas aqui layers=1 (arte importada ja colorida: a "
            "cor final vem GRAVADA no pixel na hora da geracao, nao de "
            "data/tfs_mapping.json head/body/legs/feet — esses campos nao tem "
            "efeito em looktype layers=1). Nao editar a mao: rode "
            "tools/spr/gen_humanoid_variants.py de novo."
        ),
        "root": "assets-src/sprites",
        "build_dir": "assets-src/sprites/creatures",
        "creature_sheets": things,
    }
    os.makedirs(os.path.dirname(OVERRIDES_PATH), exist_ok=True)
    with open(OVERRIDES_PATH, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return OVERRIDES_PATH


def main():
    imports_cfg = _load_imports_json()
    things = []
    skipped = []
    for spec in VARIANTS:
        thing = build_variant(imports_cfg, spec)
        if thing is None:
            skipped.append(spec["monster"])
            continue
        things.append(thing)
    path = write_overrides(things)
    print("gerado:", path)
    for spec in VARIANTS:
        print("  looktype %d = %s (base %d)" % (spec["id"], spec["monster"], spec["base"]))
    if skipped:
        print("PULADOS (fonte ausente):", ", ".join(skipped))


if __name__ == "__main__":
    main()
