#!/usr/bin/env python3
"""
Arte propria do Shinobi Legends (sem Pillow): escreve PNG RGBA na mao.
Tema: noite ninja - lua, montanhas, silhueta de vila, folhas ao vento.
Nada copiado de Naruto/Tibia; tudo gerado por codigo.
"""
import zlib, struct, math, random, sys

def write_png(path, w, h, pixels):
    raw = bytearray()
    for y in range(h):
        raw.append(0)                       # filter type 0 (None)
        raw += pixels[y*w*4:(y+1)*w*4]
    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    open(path, 'wb').write(png)

def clamp(v): return 0 if v < 0 else (255 if v > 255 else int(v))

class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.buf = bytearray(w*h*4)
    def set(self, x, y, r, g, b, a=255):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y*self.w + x)*4
            self.buf[i]=clamp(r); self.buf[i+1]=clamp(g); self.buf[i+2]=clamp(b); self.buf[i+3]=clamp(a)
    def get(self, x, y):
        i = (y*self.w + x)*4
        return self.buf[i], self.buf[i+1], self.buf[i+2]
    def blend(self, x, y, r, g, b, a):
        if not (0 <= x < self.w and 0 <= y < self.h) or a <= 0: return
        if a >= 1.0: self.set(x, y, r, g, b); return
        i = (y*self.w + x)*4
        self.buf[i]   = clamp(self.buf[i]  *(1-a) + r*a)
        self.buf[i+1] = clamp(self.buf[i+1]*(1-a) + g*a)
        self.buf[i+2] = clamp(self.buf[i+2]*(1-a) + b*a)
        self.buf[i+3] = 255

# ---------------------------------------------------------------- paleta
NIGHT_TOP    = (7,  10, 24)     # topo do ceu
NIGHT_MID    = (16, 28, 58)     # meio
NIGHT_HORIZ  = (44, 62, 96)     # horizonte
MOON         = (238, 244, 226)
CHAKRA       = (110, 200, 255)  # azul-claro do chakra
LEAF         = (86, 168, 96)

def build_background(w=1920, h=1080, seed=1098):
    rnd = random.Random(seed)
    c = Canvas(w, h)
    horizon = int(h*0.72)

    # ceu com gradiente vertical em 3 paradas
    for y in range(h):
        if y < horizon:
            t = y/horizon
            if t < 0.62:
                k = t/0.62
                r = NIGHT_TOP[0]+(NIGHT_MID[0]-NIGHT_TOP[0])*k
                g = NIGHT_TOP[1]+(NIGHT_MID[1]-NIGHT_TOP[1])*k
                b = NIGHT_TOP[2]+(NIGHT_MID[2]-NIGHT_TOP[2])*k
            else:
                k = (t-0.62)/0.38
                r = NIGHT_MID[0]+(NIGHT_HORIZ[0]-NIGHT_MID[0])*k
                g = NIGHT_MID[1]+(NIGHT_HORIZ[1]-NIGHT_MID[1])*k
                b = NIGHT_MID[2]+(NIGHT_HORIZ[2]-NIGHT_MID[2])*k
        else:
            k = (y-horizon)/max(1,(h-horizon))
            r = NIGHT_HORIZ[0]*(1-k)*0.30
            g = NIGHT_HORIZ[1]*(1-k)*0.34
            b = NIGHT_HORIZ[2]*(1-k)*0.42
        for x in range(w):
            c.set(x, y, r, g, b)

    # estrelas
    for _ in range(1400):
        x = rnd.randrange(w); y = rnd.randrange(int(horizon*0.92))
        br = rnd.uniform(0.15, 1.0) * (1.0 - y/horizon*0.55)
        c.blend(x, y, 255, 255, 240, br*0.9)
        if br > 0.85:
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                c.blend(x+dx, y+dy, 200, 226, 255, br*0.28)

    # lua + halo
    mx, my, mr = int(w*0.735), int(h*0.235), int(h*0.115)
    for y in range(my-mr*5, my+mr*5):
        for x in range(mx-mr*5, mx+mr*5):
            d = math.hypot(x-mx, y-my)
            if d > mr:
                glow = max(0.0, 1.0 - (d-mr)/(mr*4.0))**2.6
                if glow > 0.002:
                    c.blend(x, y, 150, 190, 235, glow*0.55)
    for y in range(my-mr-2, my+mr+2):
        for x in range(mx-mr-2, mx+mr+2):
            d = math.hypot(x-mx, y-my)
            if d <= mr:
                edge = min(1.0, (mr-d)/2.0)
                # crateras suaves
                shade = 1.0
                for cxr, cyr, crr in ((-0.28,-0.20,0.20),(0.24,0.12,0.16),(-0.05,0.36,0.13),(0.34,-0.34,0.10)):
                    cd = math.hypot(x-(mx+cxr*mr), y-(my+cyr*mr))
                    if cd < crr*mr:
                        shade -= 0.10*(1.0-cd/(crr*mr))
                c.blend(x, y, MOON[0]*shade, MOON[1]*shade, MOON[2]*shade, edge)

    # tres cordilheiras (mais claras ao fundo, mais escuras a frente)
    def ridge(base_y, amp, rough, col, alpha, seed_off):
        r2 = random.Random(seed+seed_off)
        ph = [r2.uniform(0, math.tau) for _ in range(5)]
        fr = [1.0, 2.3, 4.7, 9.1, 17.0]
        top = []
        for x in range(w):
            u = x/w
            v = 0.0
            for i in range(5):
                v += math.sin(u*math.tau*fr[i] + ph[i]) * (rough**i)
            top.append(int(base_y - amp*v/2.2))
        for x in range(w):
            for y in range(max(0, top[x]), h):
                fade = 1.0 - min(1.0, (y-top[x])/(h*0.55))*0.45
                c.blend(x, y, col[0]*fade, col[1]*fade, col[2]*fade, alpha)
        return top

    ridge(int(h*0.60), h*0.085, 0.62, (30, 44, 74), 0.80, 11)
    ridge(int(h*0.68), h*0.070, 0.58, (18, 27, 48), 0.88, 23)
    ground_top = ridge(int(h*0.79), h*0.045, 0.55, (8, 12, 24), 0.96, 37)

    # silhueta da vila: telhados escalonados sobre a ultima crista
    def house(x0, bw, bh, roof_h, col, alpha, lights):
        base = ground_top[min(w-1, max(0, x0 + bw//2))] + int(h*0.015)
        top = base - bh
        for x in range(x0, x0+bw):
            if not (0 <= x < w): continue
            for y in range(top, base):
                c.blend(x, y, col[0], col[1], col[2], alpha)
        # telhado inclinado (duas aguas, beiral saliente)
        eave = int(bw*0.18)
        for i in range(roof_h):
            k = i/max(1, roof_h-1)
            half = int((bw/2 + eave) * (0.10 + 0.90*k))
            yy = top - roof_h + i
            for x in range(x0+bw//2-half, x0+bw//2+half+1):
                c.blend(x, yy, col[0]*0.72, col[1]*0.72, col[2]*0.72, alpha)
        # janelas acesas (chakra)
        for _ in range(lights):
            wx = rnd.randrange(x0+3, max(x0+4, x0+bw-5))
            wy = rnd.randrange(top+4, max(top+5, base-4))
            ww, wh = rnd.choice(((4,5),(5,6),(3,4)))
            for yy in range(wy, wy+wh):
                for xx in range(wx, wx+ww):
                    c.blend(xx, yy, 255, 206, 122, 0.72)
            for yy in range(wy-3, wy+wh+3):
                for xx in range(wx-3, wx+ww+3):
                    d = max(abs(xx-(wx+ww/2)), abs(yy-(wy+wh/2)))
                    c.blend(xx, yy, 255, 190, 110, max(0.0, 0.30-0.05*d))

    x = -40
    while x < w+40:
        bw = rnd.randrange(46, 120)
        bh = rnd.randrange(int(h*0.045), int(h*0.13))
        house(x, bw, bh, rnd.randrange(14, 30), (5, 8, 16), 0.97, rnd.randrange(1, 5))
        x += bw + rnd.randrange(6, 34)

    # torre de vigia central (mais alta), com mastro
    tx, tbw = int(w*0.47), 96
    house(tx, tbw, int(h*0.24), 40, (4, 6, 13), 0.98, 6)
    for y in range(int(h*0.79)-int(h*0.24)-70, int(h*0.79)-int(h*0.24)-38):
        for xx in range(tx+tbw//2-2, tx+tbw//2+2):
            c.blend(xx, y, 4, 6, 13, 0.98)

    # folhas ao vento (silhuetas com brilho de chakra)
    def leaf(cx, cy, size, ang, col, alpha):
        ca, sa = math.cos(ang), math.sin(ang)
        for yy in range(-size, size+1):
            for xx in range(-size*2, size*2+1):
                # forma de folha: dois arcos que se encontram nas pontas
                u = (xx*ca + yy*sa)/(size*1.9)
                v = (-xx*sa + yy*ca)/(size*0.78)
                if abs(u) <= 1.0:
                    lim = math.sqrt(max(0.0, 1.0-u*u)) * (1.0-abs(u)*0.35)
                    if abs(v) <= lim:
                        soft = min(1.0, (lim-abs(v))*7.0)
                        c.blend(cx+xx, cy+yy, col[0], col[1], col[2], alpha*soft)

    placed = 0
    while placed < 46:
        lx = rnd.randrange(0, w); ly = rnd.randrange(0, int(h*0.85))
        if math.hypot(lx-mx, ly-my) < mr*1.35:   # nao desenhar folha sobre a lua
            continue
        placed += 1
        s  = rnd.randrange(5, 17)
        a  = rnd.uniform(0, math.tau)
        depth = rnd.uniform(0.18, 0.60)
        leaf(lx, ly, s, a, (int(LEAF[0]*depth), int(LEAF[1]*depth), int(LEAF[2]*depth)), 0.85)
        # rastro de chakra em algumas
        if rnd.random() < 0.35:
            leaf(lx+int(s*1.6), ly-int(s*0.4), max(2, s//2), a,
                 (CHAKRA[0], CHAKRA[1], CHAKRA[2]), 0.16)

    # neblina baixa
    for y in range(int(h*0.70), h):
        k = (y-int(h*0.70))/max(1,(h-int(h*0.70)))
        a = 0.16*math.sin(k*math.pi)
        for x in range(w):
            n = 0.55 + 0.45*math.sin(x*0.004 + y*0.02)
            c.blend(x, y, 90, 130, 175, a*n)

    # vinheta
    cx, cy = w/2, h/2
    maxd = math.hypot(cx, cy)
    for y in range(h):
        for x in range(w):
            d = math.hypot(x-cx, y-cy)/maxd
            if d > 0.55:
                a = (d-0.55)/0.45
                c.blend(x, y, 0, 0, 0, min(0.72, a*a*0.80))
    return c

def build_icon(size=256, seed=7):
    """Icone proprio: folha estilizada com uma shuriken de chakra no centro."""
    c = Canvas(size, size)
    cx = cy = size/2.0
    R = size*0.46
    for y in range(size):
        for x in range(size):
            d = math.hypot(x-cx, y-cy)
            if d <= R:
                k = d/R
                # disco noturno com leve gradiente
                r = 14 + 20*(1-k); g = 24 + 34*(1-k); b = 46 + 62*(1-k)
                a = min(1.0, (R-d)/2.0)
                c.blend(x, y, r, g, b, a)
                if R-d < 6:
                    c.blend(x, y, CHAKRA[0], CHAKRA[1], CHAKRA[2], (1.0-(R-d)/6.0)*0.85*a)

    # folha (mesma forma da arte de fundo), inclinada
    ang = -math.pi/4
    S = size*0.30
    ca, sa = math.cos(ang), math.sin(ang)
    for y in range(size):
        for x in range(size):
            xx, yy = x-cx, y-cy
            u = (xx*ca + yy*sa)/(S*1.35)
            v = (-xx*sa + yy*ca)/(S*0.62)
            if abs(u) <= 1.0:
                lim = math.sqrt(max(0.0, 1.0-u*u))*(1.0-abs(u)*0.30)
                if abs(v) <= lim:
                    soft = min(1.0, (lim-abs(v))*9.0)
                    sh = 0.72 + 0.28*(1.0-abs(v)/max(1e-6, lim))
                    c.blend(x, y, LEAF[0]*sh, LEAF[1]*sh, LEAF[2]*sh, soft)
                    # nervura central
                    if abs(v) < 0.055:
                        c.blend(x, y, 210, 245, 215, 0.55*soft)

    # shuriken de chakra: 4 pontas finas girando 45 graus
    for i in range(4):
        a0 = i*math.pi/2 + math.pi/4
        for t in range(int(size*0.34)):
            rr = t
            px = cx + math.cos(a0)*rr
            py = cy + math.sin(a0)*rr
            width = max(1.0, (size*0.34 - t)/ (size*0.34) * size*0.045)
            for oy in range(-int(width), int(width)+1):
                for ox in range(-int(width), int(width)+1):
                    if math.hypot(ox, oy) <= width:
                        f = 1.0 - math.hypot(ox, oy)/max(1e-6, width)
                        c.blend(int(px+ox), int(py+oy), CHAKRA[0], CHAKRA[1], CHAKRA[2], 0.55*f)
    # nucleo
    for y in range(size):
        for x in range(size):
            d = math.hypot(x-cx, y-cy)
            if d < size*0.085:
                c.blend(x, y, 235, 250, 255, min(1.0, (size*0.085-d)/3.0))
            elif d < size*0.12:
                c.blend(x, y, CHAKRA[0], CHAKRA[1], CHAKRA[2], (size*0.12-d)/(size*0.035)*0.6)
    return c

if __name__ == '__main__':
    bg = build_background()
    write_png(sys.argv[1], bg.w, bg.h, bg.buf)
    ic = build_icon()
    write_png(sys.argv[2], ic.w, ic.h, ic.buf)
    print('ok')
