"""Pixel art procedural para os 9 PERSONAGENS JOGAVEIS (looktypes 900-909,
exceto 906 -- reservado para o NPC "Mestre Hayato", nao mexido nesta missao),
usada por `gen_players.py`.

Ate esta missao esses looktypes eram sprites MUGEN importados (`layers=1`,
`overrides/40_mugen.json`) -- violacao do ADR-002 (nada de sprite copiado de
NTO/anime) que bloqueava publicar o jogo. Este modulo desenha o mesmo "boneco
Tibia" de `humanoid_art.py` (cabeca 8-9px, tronco, bracos, pernas, 4 direcoes
reais, 3 fases de andar) mas com uma diferenca chave: aqui e `layers=2`
(base clara na camada 0 + mascara de cor na camada 1, FORMATO.md 3.5) --
COLORIVEL como um outfit de Tibia de verdade, igual `gen_animals.py`. Isso
significa que a cor final de cabelo(head)/roupa(body)/calca(legs)/
sandalia(feet) vem de `data/tfs_mapping.json` (indice 0..132 da paleta real
de outfit), NAO fica gravada no pixel -- e o jogador poderia trocar de cor
depois (mesma infraestrutura de outfit da Tibia).

Pele e olhos NUNCA sao coloriveis (fixos na base, fora da mascara) -- assim
como os 1-2 adereços fixos de cada personagem (bandana, luvas, pergaminho,
oculos escuros, laminas...): ficam com a MESMA cor sempre, para o personagem
continuar reconhecivel mesmo se o jogador trocar as cores do outfit.

Layer 0 ("base"): tons quase-brancos de `art.BASE` nas 4 regioes coloriveis
(MULTIPLY neutro do cliente), cor REAL fixa em tudo o mais (pele, olhos,
contorno, adereco). Layer 1 ("mascara"): so as 4 cores exatas de
`art.MASK_OF` nas regioes coloriveis, transparente em tudo o resto (mesma
tecnica de `animal_art.py`/`gen_animals.py`).

Nenhum pixel vem da Tibia, de NTO, do MUGEN ou de qualquer outro jogo
(ADR-002): tudo aqui e geometria desenhada por codigo.
"""
from PIL import Image

import art
from art import new_image, _rect, TRANSPARENT, outline_inner, MASK_OF, OUTLINE

CELL = 32

DEFAULT_SKIN = (224, 186, 150, 255)
DEFAULT_EYE = (22, 20, 28, 255)
PALE_EYE = (208, 224, 232, 255)     # Herdeira Hyuga: olhos claros, fixo na pele

# tons FIXOS (nao mascara) para adereco -- precisam de contraste garantido
# contra QUALQUER cor de outfit escolhida, entao nunca usam as regioes
# coloriveis (head/body/legs/feet).
GEAR_METAL = (150, 152, 160, 255)
GEAR_METAL_DARK = (86, 88, 98, 255)
GEAR_CLOTH_BLUE = (40, 62, 108, 255)      # bandana do Genin Laranja
GEAR_CLOTH_BLUE_DARK = (26, 42, 78, 255)
GEAR_WHITE = (232, 232, 226, 255)         # faixa de braco / luvas claras
GEAR_RED = (158, 42, 38, 255)             # marca do clã / selo
GEAR_BROWN = (122, 84, 46, 255)           # pergaminho
GEAR_BROWN_DARK = (82, 56, 30, 255)
GEAR_BLACK = (32, 30, 36, 255)            # oculos escuros / luvas escuras
GEAR_STRAW = (196, 172, 96, 255)          # chapeu conico
GEAR_STRAW_DARK = (150, 130, 68, 255)


def _c(v):
    return max(0, min(255, int(v)))


def _col(region, layer, fixed):
    """Resolve a cor de uma regiao para a camada pedida.

    `region` pode ser: uma das 4 strings coloriveis ("head"/"body"/"legs"/
    "feet" -> `art.BASE`/`art.MASK_OF`), uma string fixa ("skin"/"eye"/
    "outline", resolvida contra o dict `fixed` do personagem, SEMPRE
    transparente na camada 1), ou uma tupla RGBA literal (adereco fixo,
    idem: opaca na camada 0, transparente na camada 1)."""
    if isinstance(region, tuple):
        return region if layer == 0 else TRANSPARENT
    if region in ("head", "body", "legs", "feet"):
        return art.BASE[region] if layer == 0 else MASK_OF[region]
    if layer == 1:
        return TRANSPARENT
    if region == "skin":
        return fixed.get("skin", DEFAULT_SKIN)
    if region == "eye":
        return fixed.get("eye", DEFAULT_EYE)
    if region == "outline":
        return OUTLINE
    return TRANSPARENT


def _walk(phase, lead):
    table = (0, -1, 0, 1)
    if lead:
        table = (0, 1, 0, -1)
    return table[phase % 4]


def _stride(phase, lead):
    table = (0, 2, 0, -2)
    if lead:
        table = (0, -2, 0, 2)
    return table[phase % 4]


# --------------------------------------------------------------------------
def draw_body(direction, phase, layer, char_id, fixed):
    """Boneco humanoide generico (mesma silhueta-base de
    `humanoid_art.draw_body`), redesenhado para produzir uma camada por vez
    (layer 0 = base, layer 1 = mascara) em vez de uma unica imagem ja
    colorida -- e o que permite `layers=2`."""
    img = new_image(1, 1)

    def rect(x0, y0, x1, y1, region):
        # SEMPRE desenha, mesmo transparente: um adereco FIXO (tupla RGBA)
        # desenhado por cima de uma regiao colorizavel (ex. bandana sobre o
        # cabelo) precisa APAGAR a mascara ali na camada 1 (senao o cliente
        # ainda tingiria aqueles pixels com a cor de cabelo escolhida, por
        # baixo do adereco) -- pular o desenho quando alpha=0 (como
        # `humanoid_art.py` faz, correto la porque e 1 camada so) deixaria a
        # mascara antiga intacta. Achado nesta missao: bandana do Genin
        # Laranja saindo tingida (quase invisivel) ate este ajuste.
        c = _col(region, layer, fixed)
        _rect(img, x0, y0, x1, y1, c)

    front = direction == 2
    back = direction == 0
    side = direction == 1

    if not side:
        l0, l1 = _walk(phase, 0), _walk(phase, 1)
        a0, a1 = _walk(phase, 1), _walk(phase, 0)

        rect(10, 30, 21, 30, "outline")

        # pernas + sandalias
        rect(11, 22, 14, 27 + l0, "legs")
        rect(17, 22, 20, 27 + l1, "legs")
        rect(11, 28 + l0, 15, 29 + l0, "feet")
        rect(17, 28 + l1, 21, 29 + l1, "feet")

        # tronco/roupa
        rect(10, 12, 21, 21, "body")
        rect(10, 20, 21, 20, "outline")        # cinto fino: fixo, quebra a silhueta
        # bracos (pele)
        rect(7, 14 + a0, 9, 20 + a0, "skin")
        rect(22, 14 + a1, 24, 20 + a1, "skin")

        # cabeca
        rect(11, 3, 20, 11, "skin")
        rect(11, 2, 20, 6, "head")             # cabelo/bandana cobre o topo

        if front:
            rect(13, 8, 14, 9, "eye")
            rect(17, 8, 18, 9, "eye")
            rect(14, 10, 17, 10, "outline")
        _gear(rect, char_id, direction, phase, front, back, side=False, fwd=0, bob=0)
    else:
        fwd = _stride(phase, True)
        bwd = _stride(phase, False)
        bob = 0 if phase == 0 else (1 if phase == 2 else 0)

        rect(11, 30, 22, 30, "outline")

        rect(12 + bwd // 2, 22, 15 + bwd // 2, 27, "legs")
        rect(12 + bwd // 2, 28, 16 + bwd // 2, 29, "feet")
        rect(15 + fwd // 2, 22, 18 + fwd // 2, 27, "legs")
        rect(15 + fwd // 2, 28, 19 + fwd // 2, 29, "feet")

        rect(11, 12 + bob, 20, 21 + bob, "body")
        rect(11, 20 + bob, 20, 20 + bob, "outline")
        rect(10, 14 + bob, 12, 19 + bob, "skin")
        rect(19 + max(0, fwd), 13 + bob - max(0, -fwd) // 2, 23 + max(0, fwd), 19 + bob, "skin")

        rect(12, 3 + bob, 19, 11 + bob, "skin")
        rect(12, 2 + bob, 19, 6 + bob, "head")
        rect(19, 6 + bob, 21, 8 + bob, "skin")
        rect(16, 8 + bob, 17, 9 + bob, "eye")

        _gear(rect, char_id, direction, phase, False, False, side=True, fwd=fwd, bob=bob)

    return img


# --------------------------------------------------------------------------
def _gear(rect, char_id, direction, phase, front, back, side, fwd, bob):
    """Cabelo + adereco por personagem. So mexe em pixels ALEM (ou por cima)
    da silhueta base -- nunca redesenha tronco/pernas -- entao funciona em
    qualquer direcao. Cabelo usa a regiao "head" (coloriza junto com a cor
    de cabelo escolhida); adereco usa cor FIXA (nao mascara), pra continuar
    reconhecivel em qualquer combinacao de cores."""

    if char_id == "genin_laranja":
        # cabelo espetado + bandana + jaqueta de gola alta.
        if side:
            rect(13, -1 + bob, 15, 2 + bob, "head")
            rect(16, -2 + bob, 18, 1 + bob, "head")
            rect(11, 11 + bob, 20, 12 + bob, "body")       # gola alta
            rect(13, 3 + bob, 20, 4 + bob, GEAR_CLOTH_BLUE)
            rect(19, 2 + bob, 21, 5 + bob, GEAR_CLOTH_BLUE_DARK)  # laco pendurado
        else:
            rect(12, -1, 14, 2, "head")
            rect(15, -2, 17, 1, "head")
            rect(18, -1, 20, 2, "head")
            rect(10, 11, 21, 12, "body")                   # gola alta
            rect(11, 4, 20, 5, GEAR_CLOTH_BLUE)
            rect(11, 5, 12, 6, GEAR_METAL) if front else None
            rect(15, 5, 16, 6, GEAR_METAL)                  # placa metalica na testa

    elif char_id == "genin_uchiha":
        # cabelo liso com franja + colarinho alto com fecho + faixa no braco.
        if side:
            rect(12, 1 + bob, 13, 7 + bob, "head")          # franja lateral longa
            rect(11, 11 + bob, 20, 12 + bob, "body")
            rect(19, 3 + bob, 20, 5 + bob, "head")
            rect(20 + max(0, fwd), 16 + bob, 22 + max(0, fwd), 17 + bob, GEAR_WHITE)
        else:
            rect(11, 1, 12, 7, "head")
            rect(19, 1, 20, 7, "head")                      # 2 tufos de franja
            rect(10, 11, 21, 12, "body")
            rect(15, 10, 16, 11, GEAR_METAL_DARK)           # fecho do colarinho
            arm_y = 16 if front else 16
            rect(7, arm_y, 9, arm_y + 1, GEAR_WHITE)
            rect(22, arm_y, 24, arm_y + 1, GEAR_WHITE)
            if front:
                rect(8, arm_y, 8, arm_y, GEAR_RED)

    elif char_id == "kunoichi_rosa":
        # cabelo medio + vestido com abertura no colo + luvas.
        if side:
            rect(10, 6 + bob, 12, 14 + bob, "head")         # cabelo desce ate o ombro
            rect(22 + max(0, fwd), 17 + bob, 23 + max(0, fwd), 18 + bob, GEAR_RED)
        else:
            rect(9, 6, 11, 15, "head")
            rect(20, 6, 22, 15, "head")
            if front:
                rect(14, 12, 17, 13, "skin")                # abertura triangular no colo
            rect(7, 19, 9, 20, GEAR_RED)                    # luvas
            rect(22, 19, 24, 20, GEAR_RED)

    elif char_id == "herdeira_hyuga":
        # cabelo longo escuro + casaco largo + olhos claros (fixed ja aplicado).
        # Cuidado: a mecha NAO pode invadir a coluna dos bracos (x=7-9/22-24)
        # nem cobrir os olhos de frente (1a versao virava um "poncho" solido
        # sem braco/rosto visivel -- ver docs, retrabalho desta missao).
        if side:
            rect(11, 1 + bob, 13, 13 + bob, "head")          # mecha caindo atras do rosto
        elif back:
            rect(10, 2, 21, 15, "head")                      # cabelo cobre toda a nuca/costas
            rect(9, 18, 9, 21, "body")                        # casaco levemente alargado (barra)
            rect(22, 18, 22, 21, "body")
        elif front:
            rect(11, 2, 20, 6, "head")                       # franja normal, nao cobre o rosto
            rect(10, 6, 11, 13, "head")                       # mecha lateral esquerda
            rect(20, 6, 21, 13, "head")                       # mecha lateral direita
            rect(9, 18, 9, 21, "body")
            rect(22, 18, 22, 21, "body")

    elif char_id == "ninja_verde":
        # corte de tigela (bowl cut) reto + bandagens nos punhos/tornozelos.
        if side:
            rect(12, 1 + bob, 19, 3 + bob, "head")           # franja reta e espessa
            rect(19 + max(0, fwd), 18 + bob, 23 + max(0, fwd), 19 + bob, GEAR_WHITE)
            rect(15 + fwd // 2, 26, 18 + fwd // 2, 27, GEAR_WHITE)
        else:
            rect(11, 1, 20, 3, "head")                       # franja reta cobrindo a testa toda
            rect(7, 18, 9, 19, GEAR_WHITE)                   # bandagem pulso
            rect(22, 18, 24, 19, GEAR_WHITE)
            rect(11, 26, 14, 27, GEAR_WHITE)                 # bandagem tornozelo
            rect(17, 26, 20, 27, GEAR_WHITE)

    elif char_id == "kunoichi_armas":
        # coques duplos + blusa chinesa (colarinho) + pergaminho nas costas.
        if side:
            rect(13, -2 + bob, 16, 1 + bob, "head")          # coque visivel de perfil
            rect(11, 11 + bob, 20, 12 + bob, "body")
            rect(9, 12 + bob, 10, 22 + bob, GEAR_BROWN)      # pergaminho a tiracolo
            rect(9, 12 + bob, 10, 13 + bob, GEAR_BROWN_DARK)
        else:
            rect(9, -1, 12, 2, "head")
            rect(19, -1, 22, 2, "head")                      # 2 coques
            rect(10, 11, 21, 12, "body")
            if back:
                rect(13, 13, 18, 24, GEAR_BROWN)             # pergaminho nas costas
                rect(13, 13, 18, 14, GEAR_BROWN_DARK)
                rect(13, 22, 18, 24, GEAR_BROWN_DARK)

    elif char_id == "sabio_loiro":
        # sabio errante: cabelo espetado longo e selvagem + pergaminho grande diagonal.
        if side:
            rect(12, -3 + bob, 15, 1 + bob, "head")
            rect(15, -4 + bob, 18, 0 + bob, "head")
            rect(9, 10 + bob, 22, 24, GEAR_BROWN) if back else None
        else:
            rect(9, -3, 12, 1, "head")
            rect(12, -4, 16, 0, "head")
            rect(16, -3, 19, 1, "head")
            rect(11, 1, 12, 2, "head")                       # topete descendo
            if back:
                rect(8, 9, 23, 25, GEAR_BROWN)                # pergaminho enorme, diagonal
                rect(8, 9, 23, 11, GEAR_BROWN_DARK)
                rect(8, 23, 23, 25, GEAR_BROWN_DARK)

    elif char_id == "sabio_cerimonial":
        # chapeu conico largo + selos cerimoniais no peito.
        if side:
            rect(9, -2 + bob, 22, 0 + bob, GEAR_STRAW)
            rect(11, -4 + bob, 20, -2 + bob, GEAR_STRAW)
            rect(9, 0 + bob, 22, 1 + bob, GEAR_STRAW_DARK)
        else:
            rect(8, -2, 23, 0, GEAR_STRAW)
            rect(11, -4, 20, -2, GEAR_STRAW)
            rect(8, 0, 23, 1, GEAR_STRAW_DARK)
            if front:
                rect(14, 14, 15, 15, GEAR_RED)                # selos no peito
                rect(16, 17, 17, 18, GEAR_RED)

    elif char_id == "ninja_abelha":
        # oculos escuros (cobrem os olhos) + 2 laminas cruzadas nas costas.
        if side:
            rect(12, 7 + bob, 20, 9 + bob, GEAR_BLACK)       # oculos de perfil
        else:
            if front:
                rect(12, 7, 19, 9, GEAR_BLACK)                # oculos cobrem os 2 olhos
            if back:
                rect(12, 13, 13, 22, GEAR_METAL)
                rect(18, 13, 19, 22, GEAR_METAL)
                rect(14, 12, 15, 13, GEAR_METAL_DARK)
                rect(16, 12, 17, 13, GEAR_METAL_DARK)


def render(direction, phase, layer, char_id, fixed=None):
    """Gera a celula final (uma camada) para qualquer uma das 4 direcoes:
    desenha so Norte/Leste/Sul e espelha Leste -> Oeste (mesma tecnica de
    `animal_art._finish`/`humanoid_art.render`). O contorno externo
    (`outline_inner`) so entra na camada 0 -- a camada 1 deve conter SOMENTE
    as 4 cores exatas de mascara (ou transparente), senao o cliente nao
    reconhece a regiao como coloriz vel (FORMATO.md 3.5)."""
    fixed = fixed or {}
    src_dir = 1 if direction == 3 else direction
    img = draw_body(src_dir, phase, layer, char_id, fixed)
    if direction == 3:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    if layer == 0:
        outline_inner(img, OUTLINE)
    return img
