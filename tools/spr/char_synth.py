#!/usr/bin/env python3
"""Utilidades de sintese de arte, compartilhadas por import_mugen.py e
import_player.py: vista de COSTAS a partir do perfil, fases de ANDAR sinteticas
(quando o rip nao tem ciclo) e o pipeline de nitidez usado no downscale final.

Nada aqui decide QUAL quadro usar — isso e o script de cada personagem. Este
modulo so faz operacoes de PIXEL sobre um quadro ja recortado (RGBA, alpha
binario ou nao).
"""
import numpy as np
from PIL import Image, ImageOps


# ------------------------------------------------------------------ cor
def is_skin(r, g, b):
    return (r > 95 and g > 40 and b > 20 and r > g and r > b
            and (max(r, g, b) - min(r, g, b)) > 15 and (r - g) > 15)


def _skin_mask(arr):
    """arr: HxWx4 uint8. Devolve mascara bool HxW de pele."""
    r, g, b = arr[:, :, 0].astype(int), arr[:, :, 1].astype(int), arr[:, :, 2].astype(int)
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    return (r > 95) & (g > 40) & (b > 20) & (r > g) & (r > b) & ((mx - mn) > 15) & ((r - g) > 15)


def _mode_color(px, bin_size=20):
    """Cor mais FREQUENTE (nao a media — media de amarelo+azul da cinza) entre
    pixels RGB Nx3, por histograma de bins grosseiros."""
    if px.size == 0:
        return None
    q = (px.astype(int) // bin_size)
    keys = q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2]
    uniq, counts = np.unique(keys, return_counts=True)
    best = uniq[counts.argmax()]
    bin_rgb = (best // 10000, (best // 100) % 100, best % 100)
    sel = (q[:, 0] == bin_rgb[0]) & (q[:, 1] == bin_rgb[1]) & (q[:, 2] == bin_rgb[2])
    return tuple(int(v) for v in px[sel].mean(axis=0))


def estimate_colors(imgs):
    """Pele e cabelo DOMINANTES a partir de uma lista de PIL.Image RGBA
    (tipicamente o parado + alguns quadros da mesma familia).

    Pele: cor mais frequente entre os pixels que passam no teste de tom de
    pele (rosto/maos), em qualquer regiao. Cabelo: cor mais frequente no TOPO
    da cabeca (0-22% da altura — os fios, acima de bandana/olhos/testa), entre
    os pixels opacos que NAO sao pele. Usar a MODA (nao a media) evita que
    amarelo (cabelo) + azul (bandana) virem um cinza sem sentido."""
    skin_px, hair_px = [], []
    for im in imgs:
        a = np.array(im.convert("RGBA"))
        op = a[:, :, 3] >= 128
        skin = op & _skin_mask(a)
        if skin.any():
            skin_px.append(a[:, :, :3][skin])
        y0, y1 = 0, max(1, int(im.height * 0.22))
        top = a[y0:y1]
        hop = top[:, :, 3] >= 128
        hskin = _skin_mask(top)
        hairish = hop & ~hskin
        if hairish.any():
            hair_px.append(top[:, :, :3][hairish])
    skin_all = np.concatenate(skin_px) if skin_px else np.zeros((0, 3))
    hair_all = np.concatenate(hair_px) if hair_px else np.zeros((0, 3))
    skin_rgb = _mode_color(skin_all) or (200, 160, 130)
    hair_rgb = _mode_color(hair_all) or (35, 35, 40)
    return skin_rgb, hair_rgb


def _dilate(mask, n=1):
    """Dilatacao binaria simples (sem scipy): OR com os 4 vizinhos, n vezes."""
    m = mask
    for _ in range(n):
        up = np.zeros_like(m); up[:-1, :] = m[1:, :]
        dn = np.zeros_like(m); dn[1:, :] = m[:-1, :]
        lf = np.zeros_like(m); lf[:, :-1] = m[:, 1:]
        rt = np.zeros_like(m); rt[:, 1:] = m[:, :-1]
        m = m | up | dn | lf | rt
    return m


# ------------------------------------------------------------------ costas
def synthesize_back(img, hair_rgb, mirror=True, darken=0.86, head_frac=0.46):
    """Vista de COSTAS a partir de um quadro de PERFIL (ou frontal).

    Tecnica (ver docs/sistemas/arte-e-sprites.md): espelha o quadro, detecta a
    regiao de PELE dentro da cabeca (terco/quase-metade superior — mais generoso
    que a classificacao de orientacao porque aqui queremos APAGAR rosto/pescoco
    inteiros, nao so medir), dilata a mascara 2px para pegar contorno de
    olhos/boca/sobrancelha que nao bate no teste de tom de pele, repinta essa
    regiao com a cor de CABELO do personagem (mantendo alguma variacao de
    luminancia para nao ficar chapado) e escurece o sprite inteiro ~14% (a nuca
    vira menos detalhes que o rosto). A SILHUETA (alpha) nao muda: o quadro
    continua alinhavel com o ciclo de andar original.
    """
    im = img.convert("RGBA")
    if mirror:
        im = ImageOps.mirror(im)
    a = np.array(im).astype(np.int16)
    h, w = a.shape[:2]
    op = a[:, :, 3] >= 128
    y1 = max(1, int(h * head_frac))
    head_skin = np.zeros((h, w), dtype=bool)
    head_skin[:y1] = _skin_mask(a[:y1].astype(np.uint8)) & op[:y1]
    mask = _dilate(head_skin, 3) & op

    if mask.any():
        # luminancia original (0..1) para preservar alguma sombra/luz no cabelo
        lum = (0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]) / 255.0
        lum_at = lum[mask]
        ref = lum_at.mean() if lum_at.size else 0.5
        shade = np.clip(0.65 + (lum_at - ref), 0.5, 1.15)
        hr, hg, hb = hair_rgb
        a[:, :, 0][mask] = np.clip(hr * shade, 0, 255)
        a[:, :, 1][mask] = np.clip(hg * shade, 0, 255)
        a[:, :, 2][mask] = np.clip(hb * shade, 0, 255)

    a[:, :, 0] = np.clip(a[:, :, 0] * darken, 0, 255)
    a[:, :, 1] = np.clip(a[:, :, 1] * darken, 0, 255)
    a[:, :, 2] = np.clip(a[:, :, 2] * darken, 0, 255)
    out = np.dstack([a[:, :, :3].astype(np.uint8), (op * 255).astype(np.uint8)])
    return Image.fromarray(out, "RGBA")


# ------------------------------------------------------------------ andar sintetico
def _shift_rows(arr, dx_top, dx_bottom, y0):
    """Desloca horizontalmente as linhas a partir de y0, com dx interpolado
    linearmente de dx_top (em y0) a dx_bottom (na ultima linha). Preenche com
    transparente. arr: HxWx4."""
    h, w = arr.shape[:2]
    out = arr.copy()
    if y0 >= h:
        return out
    rows = np.arange(y0, h)
    if h - 1 - y0 > 0:
        dx = dx_top + (dx_bottom - dx_top) * (rows - y0) / float(h - 1 - y0)
    else:
        dx = np.full(rows.shape, dx_top, dtype=float)
    for i, y in enumerate(rows):
        d = int(round(dx[i]))
        if d == 0:
            continue
        row = arr[y]
        shifted = np.zeros_like(row)
        if d > 0:
            shifted[d:] = row[:w - d]
        else:
            shifted[:w + d] = row[-d:]
        out[y] = shifted
    return out


def synth_walk_offset(img, leg_dx=0, body_dy=0, shear=0, leg_frac=0.55):
    """4a fase (ou 2a/3a) de um ciclo de andar SINTETICO, quando o rip nao tem
    quadros de passada de verdade: desloca a METADE INFERIOR (pernas/pes)
    horizontalmente `leg_dx` px, com uma inclinacao (`shear`) que cresce da
    cintura ate o pe (perna de tras "arrasta" um pouco mais), e desloca o corpo
    INTEIRO `body_dy` px na vertical (o baloico do passo). Pequeno de proposito
    (1-3 px): o objetivo e parecer um passo, nao tremer."""
    a = np.array(img.convert("RGBA"))
    h, w = a.shape[:2]
    y0 = int(h * leg_frac)
    out = _shift_rows(a, leg_dx * 0.4 + shear * 0.0, leg_dx + shear, y0)
    if body_dy:
        body = np.zeros_like(out)
        if body_dy > 0:
            body[body_dy:] = out[:h - body_dy]
        else:
            body[:h + body_dy] = out[-body_dy:]
        out = body
    return Image.fromarray(out, "RGBA")


# ------------------------------------------------------------------ nitidez
def extract_palette(imgs, k=16):
    """Paleta representativa (lista de (r,g,b)) a partir de uma lista de
    PIL.Image RGBA, via quantizacao mediancut do PIL — SO sobre os pixels
    OPACOS (empacotados numa tira 1D; incluir o fundo transparente-vira-preto
    do mosaico derrubava a paleta inteira para tons escuros/errados)."""
    px = []
    for im in imgs:
        if im is None:
            continue
        a = np.array(im.convert("RGBA"))
        op = a[:, :, 3] >= 128
        if op.any():
            px.append(a[:, :, :3][op])
    if not px:
        return None
    flat = np.concatenate(px)
    n = flat.shape[0]
    side = int(np.ceil(np.sqrt(n)))
    pad = side * side - n
    if pad:
        flat = np.concatenate([flat, np.tile(flat[-1:], (pad, 1))])
    strip = Image.fromarray(flat.reshape(side, side, 3).astype(np.uint8), "RGB")
    q = strip.quantize(colors=min(k, 256), method=Image.MEDIANCUT)
    pal = q.getpalette()[:k * 3]
    return [tuple(pal[i:i + 3]) for i in range(0, len(pal), 3)]


def quantize_to_palette(img, palette):
    """Empurra cada pixel OPACO para a cor mais proxima da paleta (distancia
    euclidiana em RGB). Evita tons intermediarios criados pelo LANCZOS que nao
    existiam no material original."""
    if not palette:
        return img
    a = np.array(img.convert("RGBA"))
    op = a[:, :, 3] >= 128
    if not op.any():
        return img
    pal = np.array(palette, dtype=np.int16)
    px = a[:, :, :3][op].astype(np.int16)
    # distancia de cada pixel a cada cor da paleta (N x K), N pode ser so 1024
    d = ((px[:, None, :] - pal[None, :, :]) ** 2).sum(axis=2)
    nearest = pal[d.argmin(axis=1)]
    out = a.copy()
    out[:, :, :3][op] = nearest.astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def unsharp(img, amount=0.6, radius=1):
    """Realce simples: pixel + amount*(pixel - blur(pixel)), só no RGB, alpha
    preservado. Usa um blur de caixa 3x3 feito a mao (sem depender de
    ImageFilter em imagens RGBA pequenas com alpha binario, que o GaussianBlur
    do PIL borra)."""
    a = np.array(img.convert("RGBA")).astype(np.float32)
    rgb = a[:, :, :3]
    h, w = rgb.shape[:2]
    acc = np.zeros_like(rgb)
    cnt = np.zeros((h, w, 1), dtype=np.float32)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            y0, y1 = max(0, oy), h + min(0, oy)
            x0, x1 = max(0, ox), w + min(0, ox)
            ys0, ys1 = max(0, -oy), h + min(0, -oy)
            xs0, xs1 = max(0, -ox), w + min(0, -ox)
            acc[ys0:ys1, xs0:xs1] += rgb[y0:y1, x0:x1]
            cnt[ys0:ys1, xs0:xs1] += 1
    blur = acc / np.maximum(cnt, 1)
    sharp = rgb + amount * (rgb - blur)
    a[:, :, :3] = np.clip(sharp, 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


# ------------------------------------------------------------------ validacao do ciclo
"""Filtro obrigatorio de quadros do ciclo de andar (feedback do orquestrador:
golpes/agachamentos vazando para dentro do ciclo). Cinco regras:

  (a) altura da bbox dentro de +-H_TOL_WALK px da altura do idle;
  (b) largura <= W_RATIO_WALK x a largura do idle;
  (c) centroide X da regiao de pele/cabeca (topo HEAD_FRAC da caixa), medido
      em relacao ao centroide X do apoio dos pes (rodape FOOT_FRAC), variando
      <= HEAD_TOL px em relacao ao mesmo offset no idle — um soco/chute que
      inclina o tronco desloca a cabeca em relacao ao apoio muito mais que um
      passo normal;
  (d) fracao de pixels 'de efeito' (fora da paleta do PROPRIO personagem — a
      paleta e extraida do idle — e saturados/claros o bastante para serem
      chama/chakra/brilho, nao pano) abaixo de EFFECT_FRAC_MAX;
  (e) diferenca de mascara (silhueta 24x32) entre quadros CONSECUTIVOS do ciclo
      (fechando o loop ultimo->primeiro) entre MOTION_LO e MOTION_HI — menos
      que isso e quadro duplicado, mais e uma pose diferente (chute/salto).

As tolerancias em PIXELS (a, c) sao definidas para o sprite FINAL de 32px (o
que o jogador realmente ve) — os rips MUGEN chegam em resolucoes bem maiores
(40 a 90px de altura conforme o personagem), entao (a) e (c) sao convertidas
para a resolucao do RECORTE por um fator de escala derivado do proprio idle
(`scale = min(32/max(largura,altura do idle), 1)`), a MESMA logica de
`imports.fit_uniform`. (b) e (e) ja sao proporcoes/fracoes normalizadas —
independem de resolucao, sem necessidade de escala."""
H_TOL_WALK = 2
W_RATIO_WALK = 1.25
HEAD_FRAC = 0.25
FOOT_FRAC = 0.34
HEAD_TOL = 3.0    # calibrado: 2.0 rejeitava o proprio ciclo ja curado/testado do
                  # 128 (offsets de 2.7-3.4px de balanco NORMAL do passo real);
                  # os golpes/chutes MUGEN encontrados na revisao ficam bem
                  # acima disso (4-20px), entao a folga nao deixa passar golpe
EFFECT_DIST = 70
EFFECT_SAT_MIN = 0.55
EFFECT_VAL_MIN = 0.45
EFFECT_FRAC_MAX = 0.05
MOTION_LO = 0.03
MOTION_HI = 0.28  # calibrado: 0.25 cortava a transicao 0 do proprio ciclo
                  # curado do 128 (27%, passo real); nos rips MUGEN o gap entre
                  # passo real (5-18%) e golpe/agachamento (28-49%) e largo, a
                  # folga de 3 pontos nao deixa golpe nenhum passar


def validation_scale(idle_bbox, target=32):
    """Fator de escala do recorte idle ate o sprite final (mesma conta de
    `imports.fit_uniform`), usado para converter as tolerancias absolutas de
    pixel (a, c) — definidas para o sprite de 32px — para a resolucao do
    recorte bruto."""
    iw, ih = idle_bbox[2] - idle_bbox[0], idle_bbox[3] - idle_bbox[1]
    return min(target / float(max(iw, ih, 1)), 1.0)


def head_foot_offset(img, head_frac=HEAD_FRAC, foot_frac=FOOT_FRAC):
    """Centroide X da pele/cabeca (topo `head_frac` da bbox) MENOS o centroide X
    do apoio dos pes (rodape `foot_frac`) — um numero estavel entre quadros de um
    andar normal (o corpo balanca pouco em torno do apoio), que dispara alto num
    soco/chute (torso inclina, braco/perna estende para um lado so)."""
    a = np.array(img.convert("RGBA"))
    op = a[:, :, 3] >= 128
    h, w = op.shape
    y1 = max(1, int(h * head_frac))
    hys, hxs = np.where(op[:y1])
    head_cx = float(hxs.mean()) if hxs.size else w / 2.0
    fy0 = max(0, h - max(2, int(h * foot_frac)))
    fys, fxs = np.where(op[fy0:])
    foot_cx = float(fxs.mean()) if fxs.size else w / 2.0
    return head_cx - foot_cx


def effect_pixel_fraction(img, palette, dist=EFFECT_DIST, sat_min=EFFECT_SAT_MIN,
                           val_min=EFFECT_VAL_MIN):
    """Fracao de pixels opacos que NAO batem com a paleta do personagem (`palette`,
    extraida do idle) E sao saturados/claros o bastante para serem efeito (chama,
    chakra, brilho de golpe) — o pano/pele do proprio personagem, mesmo que
    escuro ou colorido, ja esta representado na paleta."""
    a = np.array(img.convert("RGBA"))
    op = a[:, :, 3] >= 128
    if not op.any() or not palette:
        return 0.0
    px = a[:, :, :3][op].astype(np.float32)
    mx = px.max(axis=1)
    mn = px.min(axis=1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    val = mx / 255.0
    pal = np.array(palette, dtype=np.float32)
    d = np.sqrt(((px[:, None, :] - pal[None, :, :]) ** 2).sum(axis=2).min(axis=1))
    is_effect = (d > dist) & (sat > sat_min) & (val > val_min)
    return float(is_effect.mean())


def mask24(img):
    m = img.split()[3].point(lambda v: 255 if v >= 128 else 0)
    return np.array(m.resize((24, 32), Image.NEAREST)) > 0


def mask_diff(img_a, img_b):
    return float((mask24(img_a) != mask24(img_b)).mean())


def validate_frame(img, idle_img, idle_bbox, idle_offset, palette, scale=1.0):
    """Valida UM quadro de andar contra o idle (regras a/b/c/d). `scale` (ver
    `validation_scale`) converte as tolerancias absolutas de pixel (a, c),
    definidas para o sprite final de 32px, para a resolucao do recorte bruto
    deste personagem. Devolve (ok: bool, motivos: list[str])."""
    reasons = []
    b = img.getbbox()
    if not b:
        return False, ["quadro vazio"]
    w, h = b[2] - b[0], b[3] - b[1]
    iw, ih = idle_bbox[2] - idle_bbox[0], idle_bbox[3] - idle_bbox[1]
    h_tol = H_TOL_WALK / scale
    head_tol = HEAD_TOL / scale
    if abs(h - ih) > h_tol:
        reasons.append("altura %dpx difere do idle %dpx (tolerancia %.1fpx)" % (h, ih, h_tol))
    if w > iw * W_RATIO_WALK:
        reasons.append("largura %dpx > %.2fx a largura do idle (%dpx)" % (w, W_RATIO_WALK, iw))
    off = head_foot_offset(img)
    if abs(off - idle_offset) > head_tol:
        reasons.append("centroide da cabeca desloca %.1fpx do idle (tolerancia %.1fpx) — "
                        "pose de golpe/chute provavel" % (abs(off - idle_offset), head_tol))
    ef = effect_pixel_fraction(img, palette)
    if ef > EFFECT_FRAC_MAX:
        reasons.append("%.0f%% de pixels de efeito fora da paleta do personagem" % (ef * 100))
    return (len(reasons) == 0), reasons


def validate_cycle(walk_imgs, idle_img):
    """Valida as regras (a-d) quadro a quadro contra o idle e (e) quadro a
    quadro CONSECUTIVO do ciclo (fecha o loop ultimo->primeiro). Devolve lista
    paralela a `walk_imgs` de (ok, motivos)."""
    idle_bbox = idle_img.getbbox() or (0, 0, idle_img.width, idle_img.height)
    idle_offset = head_foot_offset(idle_img)
    palette = extract_palette([idle_img], k=12)
    scale = validation_scale(idle_bbox)
    results = [list(validate_frame(im, idle_img, idle_bbox, idle_offset, palette, scale))
               for im in walk_imgs]
    n = len(walk_imgs)
    for i in range(n):
        j = (i + 1) % n
        md = mask_diff(walk_imgs[i], walk_imgs[j])
        if md < MOTION_LO:
            results[i][0] = False
            results[i][1].append("quase identico ao proximo quadro do ciclo (%.0f%% < %.0f%%): "
                                  "duplicado" % (md * 100, MOTION_LO * 100))
        elif md > MOTION_HI:
            results[i][0] = False
            results[i][1].append("muito diferente do proximo quadro do ciclo (%.0f%% > %.0f%%): "
                                  "pose distinta (golpe/agachamento/pulo provavel)"
                                  % (md * 100, MOTION_HI * 100))
    return [(ok, reasons) for ok, reasons in results]


def repair_cycle(items, idle_img, candidates, rejected_log, cycle_label):
    """Versao generica de `import_mugen.repair_window` — para material com
    poucos quadros ja curados a mao (ex.: o outfit do jogador, `import_player.py`),
    onde nao ha uma lista `Frame` com `.no`/indice sequencial para procurar
    vizinhos; aqui quem chama passa o pool de candidatos direto.

    `items`: lista de (rotulo, PIL.Image) — o ciclo escolhido (idle + walk, ou
    so o walk; quem valida e SEMPRE contra `idle_img`), pode reprovar.
    `candidates`: lista de (rotulo, PIL.Image) — outros quadros disponiveis
    para substituir (tipicamente todo o material, exceto os que ja estao no
    ciclo). Mesmas DUAS passadas de `repair_window` (troca por candidato real
    valido; so DEPOIS sintetiza a partir do vizinho REAL mais proximo do
    ciclo, nunca de outra sintese). Devolve (imgs, labels)."""
    labels = [lbl for lbl, _ in items]
    imgs = [im for _, im in items]
    n = len(imgs)
    idle_bbox = idle_img.getbbox() or (0, 0, idle_img.width, idle_img.height)
    idle_offset = head_foot_offset(idle_img)
    palette = extract_palette([idle_img], k=12)
    scale = validation_scale(idle_bbox)
    used = set(labels)

    # ---- passada 1: troca por candidato REAL que passe nas regras a-d E
    # mantenha a continuidade (regra e) com quem ja esta nas posicoes vizinhas
    # neste momento — sem isso o substituto e escolhido so pelo tamanho, sem
    # relacao de movimento com o resto do ciclo, e a passada 2 acaba
    # sintetizando o ciclo INTEIRO em vez de so o quadro ruim.
    for pos in range(n):
        ok, reasons = validate_frame(imgs[pos], idle_img, idle_bbox, idle_offset, palette, scale)
        if ok:
            continue
        orig_label = labels[pos]
        for lbl, cand_img in candidates:
            if lbl in used:
                continue
            ok2, _ = validate_frame(cand_img, idle_img, idle_bbox, idle_offset, palette, scale)
            if not ok2:
                continue
            good = True
            if pos > 0:
                good = good and MOTION_LO <= mask_diff(imgs[pos - 1], cand_img) <= MOTION_HI
            if pos + 1 < n:
                good = good and MOTION_LO <= mask_diff(cand_img, imgs[pos + 1]) <= MOTION_HI
            if not good:
                continue
            rejected_log.append({
                "ciclo": cycle_label, "posicao": pos, "quadro_rejeitado": str(orig_label),
                "motivos": reasons, "substituido_por": lbl,
            })
            imgs[pos] = cand_img
            labels[pos] = lbl
            used.add(lbl)
            break

    # ---- passada 2: continuidade (regra e); sintetiza do vizinho REAL do
    # ciclo mais proximo (nunca de outra sintese) quando ainda reprovar
    results = validate_cycle(imgs, idle_img)
    for pos, (ok, reasons) in enumerate(results):
        if ok:
            continue
        orig_label = labels[pos]
        real_neighbors = [p for p in (pos - 1, (pos + 1) % n)
                          if not str(labels[p]).startswith("synth")]
        if real_neighbors:
            src_pos = real_neighbors[0]
            base_img, base_label = imgs[src_pos], labels[src_pos]
        else:
            base_img, base_label = idle_img, "idle"
        dx = 2 if pos % 2 == 0 else -2
        synth_img = synth_walk_offset(base_img, leg_dx=dx, body_dy=1 if dx > 0 else -1, shear=dx // 2)
        rejected_log.append({
            "ciclo": cycle_label, "posicao": pos, "quadro_rejeitado": str(orig_label),
            "motivos": reasons,
            "substituido_por": "synth (deslocamento de pernas sobre %s)" % base_label,
        })
        imgs[pos] = synth_img
        labels[pos] = "synth:%s" % base_label
    return imgs, labels


def outline_1px(img, color=(20, 16, 18), strength=255):
    """Redesenha um contorno escuro de 1px na borda da silhueta (pixels
    TRANSPARENTES adjacentes a pixels opacos viram opacos com `color`, so onde
    ainda nao ha nada desenhado ali). Aplicado DEPOIS da reducao: o contorno do
    material original se perde no downscale, isso devolve a leitura de silhueta
    que o estilo Tibia depende."""
    a = np.array(img.convert("RGBA"))
    op = a[:, :, 3] >= 128
    border = _dilate(op, 1) & ~op
    out = a.copy()
    if border.any():
        out[:, :, 0][border] = color[0]
        out[:, :, 1][border] = color[1]
        out[:, :, 2][border] = color[2]
        out[:, :, 3][border] = strength
    return Image.fromarray(out, "RGBA")
