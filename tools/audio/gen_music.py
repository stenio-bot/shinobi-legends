#!/usr/bin/env python3
"""Gera as 7 faixas de musica ambiente por regiao, 100% por sintese (ADR-002 - nada
de material de terceiros). Usa o motor reutilizavel de tools/audio/synth.py.

Saida:
  client-otc/data/sounds/naruto/music/*.ogg   (22050 Hz, OGG Vorbis, loop sem clique)
  assets-src/audio/music_catalog.json         (regiao -> arquivo/ganho/retangulo)

Uso: .venv/bin/python tools/audio/gen_music.py
"""
import json
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(__file__))
import synth as sy  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT_DIR = os.path.join(ROOT, "client-otc", "data", "sounds", "naruto", "music")
OUT_CATALOG = os.path.join(ROOT, "assets-src", "audio", "music_catalog.json")
RATE = sy.RATE
PEAK_DBFS = -12.0
LOOP_FADE_S = 3.0


# --------------------------------------------------------------------------- helpers de composicao
def stereo_buf(dur_s, rate=RATE):
    return np.zeros((int(dur_s * rate), 2), dtype=np.float64)


def pan_gains(pan):
    """pan em [-1,1] (equal power)."""
    pan = max(-1.0, min(1.0, pan))
    ang = (pan + 1.0) * (np.pi / 4.0)
    return np.cos(ang), np.sin(ang)


def add_mono(buf, t0_s, sig, pan=0.0, amp=1.0, rate=RATE):
    start = int(t0_s * rate)
    if start >= buf.shape[0]:
        return
    end = min(buf.shape[0], start + len(sig))
    seg = sig[: end - start] * amp
    lg, rg = pan_gains(pan)
    buf[start:end, 0] += seg * lg
    buf[start:end, 1] += seg * rg


def add_stereo(buf, t0_s, sig2, amp=1.0, rate=RATE):
    start = int(t0_s * rate)
    if start >= buf.shape[0]:
        return
    end = min(buf.shape[0], start + sig2.shape[0])
    buf[start:end, :] += sig2[: end - start, :] * amp


def note_sine(freq, dur, vibrato=False, attack=0.15, release=0.4, sustain=0.65, seed=0):
    t, n = sy.times(dur)
    sig = sy.sine_vibrato(t, freq, vibrato_hz=4.5, vibrato_depth=0.012) if vibrato else sy.sine(t, freq)
    env = sy.adsr(n, attack, max(0.05, dur * 0.25), sustain_level=sustain, release=release)
    return sy.apply_env(sig, env)


def note_triangle(freq, dur, attack=0.6, release=1.0, sustain=0.8):
    t, n = sy.times(dur)
    sig = sy.triangle(t, freq)
    sig = sy.one_pole_lowpass(sig, freq * 4)
    env = sy.adsr(n, attack, max(0.05, dur * 0.2), sustain_level=sustain, release=release)
    return sy.apply_env(sig, env)


def pluck(freq, dur, seed, damping=0.996, brightness=0.5, detune=1.0, amp_env_release=0.0):
    sig = sy.karplus_strong(freq, dur, rate=RATE, seed=seed, damping=damping, brightness=brightness, detune=detune)
    return sig


def taiko_hit(dur=0.4, freq=68, seed=1, punch=0.5):
    t, n = sy.times(dur)
    tone = sy.sine_sweep(t, freq * 1.5, freq * 0.7, dur)
    body = sy.noise(n, seed) * punch
    body = sy.one_pole_lowpass(body, 220)
    mixed = sy.mix((tone, 0.8), (body, 0.5))
    env = sy.adsr(n, 0.004, dur * 0.35, sustain_level=0.12, release=dur * 0.6)
    return sy.apply_env(mixed, env)


def bell_chord(freqs, dur=2.2, seed=1):
    t, n = sy.times(dur)
    parts = []
    for i, f in enumerate(freqs):
        parts.append((sy.sine(t, f), 1.0 / (i + 1)))
    sig = sy.mix(*parts)
    env = sy.adsr(n, 0.01, dur * 0.15, sustain_level=0.35, release=dur * 0.75)
    return sy.apply_env(sig, env)


def thunder_crack(dur=1.1, seed=1):
    t, n = sy.times(dur)
    noise = sy.noise(n, seed)
    crack = sy.highpass(noise, 2200)
    rumble = sy.one_pole_lowpass(sy.noise(n, seed + 1), 140)
    low_tone = sy.sine_sweep(t, 90, 40, dur) * 0.4
    sig = sy.mix((crack, 0.6), (rumble, 0.9), (low_tone, 1.0))
    env = sy.adsr(n, 0.002, dur * 0.15, sustain_level=0.35, release=dur * 0.75)
    return sy.apply_env(sig, env)


def bird_chirp(dur, seed, f0=2400, f1=3600):
    t, n = sy.times(dur)
    rng = np.random.default_rng(seed)
    sig = sy.sine_sweep(t, f0 * rng.uniform(0.85, 1.15), f1 * rng.uniform(0.85, 1.15), dur)
    env = sy.adsr(n, dur * 0.15, dur * 0.35, sustain_level=0.3, release=dur * 0.4)
    return sy.apply_env(sig, env) * 0.5


def drone(dur_s, freqs, detune_cents=6.0, lowpass_hz=700, seed=0, distortion=0.0, breathe_hz=0.06):
    t, n = sy.times(dur_s)
    ratio = 2 ** (detune_cents / 1200.0)
    parts = []
    for i, f in enumerate(freqs):
        parts.append((sy.sine(t, f * ratio), 0.5))
        parts.append((sy.sine(t, f / ratio), 0.5))
    sig = sy.mix(*parts)
    sig = sig + 0.35 * sy.one_pole_lowpass(sy.noise(n, seed), lowpass_hz * 0.5)
    sig = sy.one_pole_lowpass(sig, lowpass_hz)
    breathe = 0.75 + 0.25 * np.sin(2 * np.pi * breathe_hz * t + seed)
    sig = sig * breathe
    if distortion > 0:
        sig = np.tanh(sig * (1.0 + distortion * 4.0)) / np.tanh(1.0 + distortion * 4.0)
    return sig


def waves_layer(dur_s, seed=1, swell_hz=0.11, base_cut=550, cut_range=350, foam_gain=0.22):
    t, n = sy.times(dur_s)
    noise = sy.noise(n, seed)
    swell = 0.5 + 0.5 * np.sin(2 * np.pi * swell_hz * t)
    cutoff = base_cut + cut_range * swell
    body = sy.variable_lowpass(noise, cutoff)
    body = body * (0.55 + 0.45 * swell)
    foam_noise = sy.noise(n, seed + 7)
    foam = sy.bandpass(foam_noise, 2400, 1800) * (swell ** 3) * foam_gain
    return body * 0.6 + foam


def wind_layer(dur_s, seed=2, base=900, spread=700, lfo1_hz=0.05, lfo2_hz=0.13, amp=0.5):
    t, n = sy.times(dur_s)
    noise = sy.noise(n, seed)
    center = base + spread * (0.5 * np.sin(2 * np.pi * lfo1_hz * t) + 0.5 * np.sin(2 * np.pi * lfo2_hz * t + 1.3))
    width = 500 + 250 * np.sin(2 * np.pi * (lfo1_hz * 0.7) * t + 0.6)
    body = sy.variable_bandpass(noise, np.clip(center, 150, 4000), np.clip(width, 150, 1200))
    gust = 0.7 + 0.3 * np.sin(2 * np.pi * lfo2_hz * 1.7 * t + 2.0)
    return body * gust * amp


def seeded_times(rng, start, end, min_gap, max_gap):
    out = []
    t = start
    while t < end:
        out.append(t)
        t += rng.uniform(min_gap, max_gap)
    return out


# --------------------------------------------------------------------------- 1) Vila da Folha
def gen_vila():
    dur = 76.0
    tail = 8.0
    buf = stereo_buf(dur)
    root = -9  # C4
    scale = sy.SCALE_YO
    rng = np.random.default_rng(1001)

    # shakuhachi: frase pentatonica lenta e aconchegante, repetida com pequenas variacoes
    phrase = [0, 2, 3, 2, 4, 3, 2, 0]
    t = 3.0
    beat = 2.0
    melody_end = dur - tail
    pan_flip = -0.3
    while t < melody_end - 2.0:
        for deg in phrase:
            if t >= melody_end - 2.0:
                break
            note_dur = beat * rng.uniform(0.85, 1.05)
            f = sy.scale_freq(root, scale, deg, octave=0)
            sig = note_sine(f, note_dur * 1.3, vibrato=True, attack=0.25, release=note_dur * 0.9, sustain=0.55)
            add_mono(buf, t, sig, pan=pan_flip * 0.4, amp=0.30)
            t += note_dur
        pan_flip *= -1

    # koto pizzicato: plucks esparsos em contratempo, oitava acima
    koto_times = seeded_times(np.random.default_rng(1002), 1.0, melody_end, 2.6, 4.4)
    for i, tt in enumerate(koto_times):
        deg = int(rng.integers(0, len(scale)))
        f = sy.scale_freq(root, scale, deg, octave=1)
        sig = pluck(f, 1.4, seed=3000 + i, damping=0.994, brightness=0.55)
        add_mono(buf, tt, sig, pan=0.5 if i % 2 == 0 else -0.5, amp=0.22)

    buf = np.array([sy.synthetic_reverb(buf[:, ch], decay_s=0.9, mix=0.12, seed=50 + ch) for ch in range(2)]).T
    return dur, buf


# --------------------------------------------------------------------------- 2) Floresta da Vila
def gen_floresta_vila():
    dur = 76.0
    tail = 7.0
    buf = stereo_buf(dur)
    root = -9
    scale = sy.SCALE_YO
    rng = np.random.default_rng(2001)

    phrase = [4, 3, 4, 5, 3, 2, 4, 2]
    t = 2.0
    beat = 1.7
    melody_end = dur - tail
    pan_flip = 0.35
    while t < melody_end - 2.0:
        for deg in phrase:
            if t >= melody_end - 2.0:
                break
            note_dur = beat * rng.uniform(0.8, 1.05)
            f = sy.scale_freq(root, scale, deg, octave=1)
            sig = note_sine(f, note_dur * 1.15, vibrato=True, attack=0.12, release=note_dur * 0.7, sustain=0.6)
            add_mono(buf, t, sig, pan=pan_flip * 0.35, amp=0.26)
            t += note_dur
        pan_flip *= -1

    koto_times = seeded_times(np.random.default_rng(2002), 0.8, melody_end, 2.0, 3.4)
    for i, tt in enumerate(koto_times):
        deg = int(rng.integers(0, len(scale)))
        f = sy.scale_freq(root, scale, deg, octave=2)
        sig = pluck(f, 1.0, seed=4000 + i, damping=0.992, brightness=0.6)
        add_mono(buf, tt, sig, pan=-0.5 if i % 2 == 0 else 0.5, amp=0.18)

    # passaros esparsos, mais claros que a vila
    bird_times = seeded_times(np.random.default_rng(2003), 1.5, dur - 2.0, 3.5, 7.0)
    for i, tt in enumerate(bird_times):
        p = rng.uniform(-0.9, 0.9)
        chirp = bird_chirp(rng.uniform(0.18, 0.3), seed=5000 + i,
                            f0=rng.uniform(2200, 3200), f1=rng.uniform(3200, 4600))
        add_mono(buf, tt, chirp, pan=p, amp=0.28)
        if rng.uniform() > 0.5:
            add_mono(buf, tt + rng.uniform(0.1, 0.25), chirp * 0.7, pan=p + 0.1, amp=0.22)

    return dur, buf


# --------------------------------------------------------------------------- 3) Costa das Mares
def gen_costa():
    dur = 80.0
    tail = 6.0
    buf = stereo_buf(dur)
    root = -2  # A#3-ish, so raiz do modo dorico
    scale = sy.SCALE_DORIAN
    rng = np.random.default_rng(3001)

    waves_mono = waves_layer(dur, seed=31, swell_hz=0.1)
    add_mono(buf, 0.0, waves_mono, pan=0.0, amp=0.55)
    waves_mono2 = waves_layer(dur, seed=37, swell_hz=0.085)
    add_mono(buf, 0.0, waves_mono2, pan=0.2, amp=0.3)

    # taiko esparso e irregular
    taiko_times = seeded_times(np.random.default_rng(3002), 6.0, dur - tail, 8.0, 13.0)
    for i, tt in enumerate(taiko_times):
        add_mono(buf, tt, taiko_hit(dur=0.5, freq=64, seed=6000 + i, punch=0.4), pan=0.0, amp=0.4)

    # melodia dorica esparsa (entra so depois da introducao de ondas)
    melody_end = dur - tail
    phrase = [0, 2, 3, 5, 3, 2, 0]
    t = 9.0
    beat = 2.3
    while t < melody_end - 2.0:
        for deg in phrase:
            if t >= melody_end - 2.0:
                break
            note_dur = beat * rng.uniform(0.85, 1.1)
            f = sy.scale_freq(root, scale, deg, octave=0)
            sig = note_sine(f, note_dur * 1.2, vibrato=True, attack=0.3, release=note_dur, sustain=0.5)
            add_mono(buf, t, sig, pan=rng.uniform(-0.3, 0.3), amp=0.24)
            t += note_dur
        t += beat * 1.5  # respiro entre frases (mare que recua)

    return dur, buf


# --------------------------------------------------------------------------- 4) Floresta da Morte
def gen_floresta_morte():
    dur = 78.0
    buf = stereo_buf(dur)
    rng = np.random.default_rng(4001)

    d = drone(dur, freqs=[55.0, 27.5], detune_cents=9.0, lowpass_hz=260, seed=41,
              distortion=0.0, breathe_hz=0.045)
    add_mono(buf, 0.0, d, pan=0.0, amp=0.42)

    # nota dissonante esparsa (segunda menor / trítono em relacao a raiz do drone)
    dissonant_degrees_semi = [1, 6, 8]  # semitons acima da raiz (55Hz)
    diss_times = seeded_times(np.random.default_rng(4002), 5.0, dur - 4.0, 6.0, 11.0)
    for i, tt in enumerate(diss_times):
        semi = dissonant_degrees_semi[i % len(dissonant_degrees_semi)]
        f = 55.0 * (2 ** (semi / 12.0)) * 4  # sobe 2 oitavas p/ ficar audivel/incomodo
        sig = note_triangle(f, dur=rng.uniform(2.2, 3.6), attack=0.7, release=1.6, sustain=0.7)
        add_mono(buf, tt, sig, pan=rng.uniform(-0.5, 0.5), amp=0.16)

    # tambor irregular (sem pulso fixo)
    drum_times = seeded_times(np.random.default_rng(4003), 3.0, dur - 3.0, 3.5, 8.5)
    for i, tt in enumerate(drum_times):
        add_mono(buf, tt, taiko_hit(dur=0.6, freq=48, seed=7000 + i, punch=0.65), pan=0.0, amp=0.5)

    # chiado alto muito baixo, tensao de fundo
    t, n = sy.times(dur)
    hiss = sy.highpass(sy.noise(n, 4004), 4500) * 0.04
    add_mono(buf, 0.0, hiss, pan=0.0, amp=1.0)

    return dur, buf


# --------------------------------------------------------------------------- 5) Ruinas do Cla Marionetista
def gen_ruinas():
    dur = 85.0
    buf = stereo_buf(dur)
    root = -9
    scale = sy.SCALE_IN
    rng = np.random.default_rng(5001)

    # vento distante muito baixo, textura de fundo
    bg = wind_layer(dur, seed=51, base=500, spread=300, amp=0.14)
    add_mono(buf, 0.0, bg, pan=0.0, amp=1.0)

    # frases curtas de koto desafinado, com silencio marcado entre elas
    t = 4.0
    phrase_pool = [[0, 2, 1], [4, 2, 0], [1, 0, 3], [2, 4, 1, 0]]
    i = 0
    while t < dur - 6.0:
        phrase = phrase_pool[i % len(phrase_pool)]
        for deg in phrase:
            if t >= dur - 6.0:
                break
            f = sy.scale_freq(root, scale, deg, octave=1)
            detune = 1.0 + rng.uniform(-0.03, 0.03)
            sig = pluck(f, 2.0, seed=8000 + i, damping=0.997, brightness=0.45, detune=detune)
            add_mono(buf, t, sig, pan=rng.uniform(-0.4, 0.4), amp=0.34)
            t += rng.uniform(0.9, 1.3)
        t += rng.uniform(6.0, 10.0)  # silencio longo entre frases
        i += 1

    # reverb longa por convolucao sintetica (camara de pedra)
    buf = np.array([sy.synthetic_reverb(buf[:, ch], decay_s=2.6, mix=0.45, seed=90 + ch) for ch in range(2)]).T
    return dur, buf


# --------------------------------------------------------------------------- 6) Montanha do Trovao
def gen_montanha():
    dur = 80.0
    buf = stereo_buf(dur)
    rng = np.random.default_rng(6001)

    wind = wind_layer(dur, seed=61, base=1000, spread=750, amp=0.42)
    add_mono(buf, 0.0, wind, pan=0.0, amp=1.0)
    wind2 = wind_layer(dur, seed=67, base=1300, spread=500, amp=0.2, lfo1_hz=0.07, lfo2_hz=0.17)
    add_mono(buf, 0.0, wind2, pan=0.3, amp=1.0)

    # trovao ocasional (2-3 eventos, longe do inicio/fim p/ nao atrapalhar o loop)
    thunder_times = [dur * 0.28, dur * 0.55, dur * 0.78]
    for i, tt in enumerate(thunder_times):
        add_mono(buf, tt, thunder_crack(dur=1.3, seed=9000 + i), pan=rng.uniform(-0.6, 0.6), amp=0.55)

    # taiko cerimonial, esparso
    taiko_times = seeded_times(np.random.default_rng(6002), 5.0, dur - 5.0, 9.0, 15.0)
    for i, tt in enumerate(taiko_times):
        add_mono(buf, tt, taiko_hit(dur=0.55, freq=58, seed=10000 + i, punch=0.55), pan=0.0, amp=0.42)

    # sino distante muito esparso (cor extra, nao substitui os 3 elementos pedidos)
    bell_times = seeded_times(np.random.default_rng(6003), 10.0, dur - 8.0, 18.0, 26.0)
    for i, tt in enumerate(bell_times):
        add_mono(buf, tt, bell_chord([523.25, 784.0, 1046.5], dur=2.6, seed=11000 + i), pan=0.4, amp=0.12)

    return dur, buf


# --------------------------------------------------------------------------- 7) Covil da Nuvem Vermelha
def gen_covil():
    dur = 80.0
    buf = stereo_buf(dur)
    root_hz = 41.2  # E1
    rng = np.random.default_rng(7001)

    d = drone(dur, freqs=[root_hz, root_hz / 2], detune_cents=14.0, lowpass_hz=200, seed=71,
              distortion=0.35, breathe_hz=0.05)
    add_mono(buf, 0.0, d, pan=0.0, amp=0.5)

    # shamisen agressivo: ostinato curto e repetido, escala menor pentatonica
    scale = sy.SCALE_MINOR_PENTA
    root = -21  # bem grave, sobe nas notas
    riff_degrees = [0, 0, 3, 2, 0, 4, 3, 0]
    riff_len = len(riff_degrees)
    note_dur = 0.42
    t = 3.0
    i = 0
    while t < dur - 5.0:
        deg = riff_degrees[i % riff_len]
        f = sy.scale_freq(root, scale, deg, octave=2)
        sig = pluck(f, note_dur * 1.6, seed=12000 + i, damping=0.985, brightness=0.75)
        add_mono(buf, t, sig, pan=rng.uniform(-0.2, 0.2), amp=0.28)
        t += note_dur
        i += 1
        if i % (riff_len * 2) == 0:
            t += note_dur * 1.5  # respiro a cada 2 voltas do riff

    # batida lenta e pesada (tensao) - 2 golpes por ciclo, tipo batimento cardiaco
    cycle = 2.6
    tt = 1.0
    j = 0
    while tt < dur - 3.0:
        add_mono(buf, tt, taiko_hit(dur=0.5, freq=44, seed=13000 + j, punch=0.7), pan=0.0, amp=0.55)
        add_mono(buf, tt + 0.32, taiko_hit(dur=0.35, freq=50, seed=13500 + j, punch=0.5), pan=0.0, amp=0.35)
        tt += cycle
        j += 1

    return dur, buf


# --------------------------------------------------------------------------- catalogo / regioes
REGIONS = {
    "vila": {"x1": 1010, "x2": 1049, "y1": 1030, "y2": 1069, "title": "Vila da Folha", "priority": 10},
    "floresta_morte": {"x1": 1130, "x2": 1199, "y1": 1000, "y2": 1119, "title": "Floresta da Morte", "priority": 8},
    "costa": {"x1": 1000, "x2": 1049, "y1": 1120, "y2": 1169, "title": "Costa das Mares", "priority": 8},
    "ruinas": {"x1": 1200, "x2": 1249, "y1": 1000, "y2": 1049, "title": "Ruinas do Cla Marionetista", "priority": 8},
    "montanha": {"x1": 1200, "x2": 1249, "y1": 1060, "y2": 1109, "title": "Montanha do Trovao", "priority": 8},
    "covil": {"x1": 1400, "x2": 1449, "y1": 1000, "y2": 1049, "title": "Covil da Nuvem Vermelha", "priority": 8},
    "floresta_vila": {"x1": 1000, "x2": 1129, "y1": 1000, "y2": 1119, "title": "Floresta da Vila", "priority": 1},
}
# ordem de resolucao: mais especifico primeiro (vila fica DENTRO do retangulo da
# floresta da vila - tem que ser checada antes)
RESOLVE_ORDER = ["vila", "floresta_morte", "costa", "ruinas", "montanha", "covil", "floresta_vila"]

TRACKS = {
    "vila": ("vila.ogg", gen_vila, 0.35),
    "floresta_vila": ("floresta_vila.ogg", gen_floresta_vila, 0.32),
    "costa": ("costa.ogg", gen_costa, 0.38),
    "floresta_morte": ("floresta_morte.ogg", gen_floresta_morte, 0.4),
    "ruinas": ("ruinas.ogg", gen_ruinas, 0.38),
    "montanha": ("montanha.ogg", gen_montanha, 0.4),
    "covil": ("covil.ogg", gen_covil, 0.42),
}


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    catalog = {
        "rate": RATE,
        "peak_dbfs": PEAK_DBFS,
        "loop_fade_s": LOOP_FADE_S,
        "resolve_order": RESOLVE_ORDER,
        "tracks": {},
    }

    for region_id, (filename, gen_fn, gain) in TRACKS.items():
        print(f"gerando {region_id}...")
        dur, buf = gen_fn()
        buf = sy.crossfade_loop_stereo(buf, LOOP_FADE_S, rate=RATE)
        buf = sy.peak_normalize_db(buf, PEAK_DBFS)
        buf = np.clip(buf, -1.0, 1.0)
        out_path = os.path.join(OUT_DIR, filename)
        sf.write(out_path, buf, RATE, format="OGG", subtype="VORBIS")
        size_kb = os.path.getsize(out_path) / 1024.0
        print(f"  -> {out_path} ({dur:.1f}s, {size_kb:.0f} KB)")

        rgn = REGIONS[region_id]
        catalog["tracks"][region_id] = {
            "file": f"naruto/music/{filename}",
            "gain": gain,
            "title": rgn["title"],
            "priority": rgn["priority"],
            "duration_s": round(dur, 2),
            "region": {"x1": rgn["x1"], "x2": rgn["x2"], "y1": rgn["y1"], "y2": rgn["y2"]},
        }

    os.makedirs(os.path.dirname(OUT_CATALOG), exist_ok=True)
    with open(OUT_CATALOG, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"catalogo escrito em {OUT_CATALOG}")


if __name__ == "__main__":
    main()
