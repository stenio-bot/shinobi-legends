#!/usr/bin/env python3
"""Gera todos os SFX do jogo por sintese proceduralm (sem material de terceiros - ADR-002).

Le os `sfx` unicos de data/jutsus/*.json + um conjunto base (combate, UI, itens,
progressao). Sintetiza cada um com osciladores/ruido filtrado + envelope em
numpy, normaliza a -6 dBFS, escreve um WAV de staging (nao versionado) e
converte para OGG Vorbis (unico formato que o cliente carrega - ver
client-otc/src/framework/sound/soundfile.cpp) via a biblioteca `soundfile`
(libsndfile, tem encoder Vorbis embutido no wheel - nao precisa ffmpeg/sox/brew).

Saida:
  client-otc/data/sounds/naruto/*.ogg   (versionavel: sintese propria)
  assets-src/audio/sfx_catalog.json     (nome -> arquivo/variacoes, ganho, canal)

Uso: .venv/bin/python tools/audio/gen_sfx.py [--rate 22050] [--keep-wav]
"""
import argparse
import glob
import json
import math
import os
import struct
import wave

try:
    import numpy as np
except ImportError:
    np = None

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
DATA = os.path.join(ROOT, "data")
OUT_OGG_DIR = os.path.join(ROOT, "client-otc", "data", "sounds", "naruto")
OUT_CATALOG = os.path.join(ROOT, "assets-src", "audio", "sfx_catalog.json")
OUT_CATALOG_LUA = os.path.join(ROOT, "client-otc", "modules", "naruto_sounds", "sfx_catalog.lua")
RATE = 22050
PEAK_DBFS = -6.0
PEAK_LINEAR = 10 ** (PEAK_DBFS / 20.0)  # ~0.5012


# --------------------------------------------------------------------------- coleta dos sfx referenciados
def collect_jutsu_sfx():
    names = set()
    for path in sorted(glob.glob(os.path.join(DATA, "jutsus", "*.json"))):
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
        for it in items:
            sfx = it.get("sfx")
            if sfx:
                names.add(sfx)
    return names


# --------------------------------------------------------------------------- DSP basico (numpy se disponivel, senao math/array puro)
def _times(dur):
    n = max(1, int(RATE * dur))
    if np is not None:
        return np.arange(n) / RATE, n
    return [i / RATE for i in range(n)], n


def _zeros(n):
    return np.zeros(n) if np is not None else [0.0] * n


def _sine(t, freq):
    if np is not None:
        return np.sin(2 * math.pi * freq * t)
    return [math.sin(2 * math.pi * freq * x) for x in t]


def _sine_sweep(t, f0, f1, dur):
    # fase = integral(2*pi*f(t)) com f(t) linear entre f0 e f1
    if np is not None:
        k = (f1 - f0) / max(dur, 1e-9)
        phase = 2 * math.pi * (f0 * t + 0.5 * k * t * t)
        return np.sin(phase)
    out = []
    k = (f1 - f0) / max(dur, 1e-9)
    for x in t:
        phase = 2 * math.pi * (f0 * x + 0.5 * k * x * x)
        out.append(math.sin(phase))
    return out


def _noise(n, seed):
    if np is not None:
        rng = np.random.default_rng(seed)
        return rng.uniform(-1.0, 1.0, n)
    rng_state = seed
    out = []
    for _ in range(n):
        rng_state = (1103515245 * rng_state + 12345) & 0x7FFFFFFF
        out.append((rng_state / 0x7FFFFFFF) * 2 - 1)
    return out


def _one_pole_lowpass(x, cutoff_hz):
    # filtro passa-baixa de 1 polo, simples e barato; alpha vem da constante de tempo
    alpha = 1 - math.exp(-2 * math.pi * cutoff_hz / RATE)
    if np is not None:
        y = np.zeros_like(x)
        acc = 0.0
        for i in range(len(x)):
            acc = acc + alpha * (x[i] - acc)
            y[i] = acc
        return y
    y = [0.0] * len(x)
    acc = 0.0
    for i in range(len(x)):
        acc = acc + alpha * (x[i] - acc)
        y[i] = acc
    return y


def _highpass(x, cutoff_hz):
    low = _one_pole_lowpass(x, cutoff_hz)
    if np is not None:
        return x - low
    return [x[i] - low[i] for i in range(len(x))]


def _bandpass(x, center_hz, width_hz):
    lo = _one_pole_lowpass(x, center_hz + width_hz / 2)
    return _highpass(lo, max(20.0, center_hz - width_hz / 2))


def _mix(*sigs):
    if np is not None:
        n = max(len(s) for s in sigs)
        out = np.zeros(n)
        for s in sigs:
            out[: len(s)] += s
        return out
    n = max(len(s) for s in sigs)
    out = [0.0] * n
    for s in sigs:
        for i, v in enumerate(s):
            out[i] += v
    return out


def _envelope(n, attack, decay, sustain_level=0.6, release=None, shape="exp"):
    """Envelope AD(S)R em amostras. attack/decay/release em segundos (fracao de n/RATE)."""
    release = release if release is not None else decay
    a = max(1, int(attack * RATE))
    d = max(1, int(decay * RATE))
    r = max(1, int(release * RATE))
    body = max(0, n - a - r)
    env = []
    for i in range(a):
        env.append(i / a)
    for i in range(body):
        # decaimento exponencial suave ate sustain_level ao longo do corpo
        frac = i / max(1, body)
        env.append(1.0 - (1.0 - sustain_level) * frac)
    for i in range(r):
        env.append(sustain_level * (1 - i / r))
    while len(env) < n:
        env.append(0.0)
    env = env[:n]
    return np.array(env) if np is not None else env


def _apply_env(x, env):
    if np is not None:
        return x[: len(env)] * np.array(env)
    return [x[i] * env[i] for i in range(min(len(x), len(env)))]


def _peak_normalize(x, peak=PEAK_LINEAR):
    if np is not None:
        m = float(np.max(np.abs(x))) if len(x) else 0.0
        if m < 1e-9:
            return x
        return x * (peak / m)
    m = max(abs(v) for v in x) if x else 0.0
    if m < 1e-9:
        return x
    scale = peak / m
    return [v * scale for v in x]


def _to_int16(x):
    if np is not None:
        xi = np.clip(x, -1.0, 1.0)
        return (xi * 32767.0).astype(np.int16)
    return [max(-32768, min(32767, int(v * 32767.0))) for v in x]


# --------------------------------------------------------------------------- fabricas de som por familia
def _thump(dur=0.12, freq=90, seed=1):
    t, n = _times(dur)
    tone = _sine_sweep(t, freq * 1.6, freq * 0.6, dur)
    body = _mix(tone, [v * 0.4 for v in _noise(n, seed)] if np is None else _noise(n, seed) * 0.4)
    env = _envelope(n, 0.002, dur * 0.3, sustain_level=0.15, release=dur * 0.6)
    return _apply_env(body, env)


def _punch(dur=0.14, seed=2, pitch=1.0):
    t, n = _times(dur)
    noise = _noise(n, seed)
    crack = _highpass(noise, 800 * pitch)
    low = _sine_sweep(t, 150 * pitch, 60 * pitch, dur)
    body = _mix([c * 0.6 for c in (crack if np is None else crack * 0.6)], low)
    env = _envelope(n, 0.001, dur * 0.35, sustain_level=0.1, release=dur * 0.5)
    return _apply_env(body, env)


def _hit_variation(seed):
    return _punch(dur=0.16, seed=seed, pitch=1.0 + (seed % 3) * 0.08)


def _whoosh(dur=0.5, seed=3, rising=True):
    t, n = _times(dur)
    noise = _noise(n, seed)
    cutoff = _linspace(400, 4000, n) if rising else _linspace(4000, 400, n)
    body = _variable_lowpass(noise, cutoff)
    env = _envelope(n, dur * 0.15, dur * 0.5, sustain_level=0.4, release=dur * 0.35)
    return _apply_env(body, env)


def _linspace(a, b, n):
    if np is not None:
        return np.linspace(a, b, n)
    return [a + (b - a) * i / max(1, n - 1) for i in range(n)]


def _variable_lowpass(x, cutoff_series):
    y = [0.0] * len(x)
    acc = 0.0
    for i in range(len(x)):
        c = cutoff_series[i]
        alpha = 1 - math.exp(-2 * math.pi * float(c) / RATE)
        acc = acc + alpha * (x[i] - acc)
        y[i] = acc
    return np.array(y) if np is not None else y


def _burst(dur=0.35, seed=4, center=1200, width=1500):
    t, n = _times(dur)
    noise = _noise(n, seed)
    body = _bandpass(noise, center, width)
    env = _envelope(n, 0.005, dur * 0.4, sustain_level=0.05, release=dur * 0.5)
    return _apply_env(body, env)


def _rumble(dur=0.9, seed=5, base=55):
    t, n = _times(dur)
    noise = _noise(n, seed)
    low = _one_pole_lowpass(noise, 180)
    tone = _sine(t, base) * 0.5 if np is not None else [v * 0.5 for v in _sine(t, base)]
    body = _mix(low, tone)
    env = _envelope(n, 0.02, dur * 0.5, sustain_level=0.5, release=dur * 0.4)
    return _apply_env(body, env)


def _crack(dur=0.25, seed=6):
    t, n = _times(dur)
    noise = _noise(n, seed)
    hi = _highpass(noise, 2500)
    low = _sine_sweep(t, 500, 90, dur)
    body = _mix(hi, low)
    env = _envelope(n, 0.001, dur * 0.25, sustain_level=0.08, release=dur * 0.6)
    return _apply_env(body, env)


def _zap(dur=0.3, seed=7, freq=900, loop=False):
    t, n = _times(dur)
    tone = _sine_sweep(t, freq * 1.8, freq * 0.6, dur)
    noise = _noise(n, seed)
    crackle = _highpass(noise, 3500)
    body = _mix([v * 0.85 for v in tone] if np is None else tone * 0.85,
                [v * 0.25 for v in crackle] if np is None else crackle * 0.25)
    sustain = 0.5 if loop else 0.1
    env = _envelope(n, 0.005, dur * 0.4, sustain_level=sustain, release=dur * 0.4)
    return _apply_env(body, env)


def _splash(dur=0.4, seed=8):
    t, n = _times(dur)
    noise = _noise(n, seed)
    body = _bandpass(noise, 1800, 2600)
    env = _envelope(n, 0.01, dur * 0.5, sustain_level=0.15, release=dur * 0.4)
    return _apply_env(body, env)


def _wave_gush(dur=0.6, seed=9):
    t, n = _times(dur)
    noise = _noise(n, seed)
    cutoff = _linspace(1500, 500, n)
    body = _variable_lowpass(noise, cutoff)
    tone = _sine_sweep(t, 220, 140, dur)
    mixed = _mix(body, [v * 0.3 for v in tone] if np is None else tone * 0.3)
    env = _envelope(n, 0.03, dur * 0.55, sustain_level=0.35, release=dur * 0.35)
    return _apply_env(mixed, env)


def _bubble(dur=0.3, seed=10):
    t, n = _times(dur)
    tone = _sine_sweep(t, 700, 1400, dur)
    env = _envelope(n, 0.01, dur * 0.4, sustain_level=0.1, release=dur * 0.4)
    return _apply_env(tone, env)


def _hiss(dur=0.5, seed=11):
    t, n = _times(dur)
    noise = _noise(n, seed)
    body = _highpass(noise, 3000)
    env = _envelope(n, 0.05, dur * 0.5, sustain_level=0.3, release=dur * 0.4)
    return _apply_env(body, env)


def _mist(dur=0.6, seed=12):
    t, n = _times(dur)
    noise = _noise(n, seed)
    body = _bandpass(noise, 2500, 3000)
    env = _envelope(n, 0.08, dur * 0.5, sustain_level=0.2, release=dur * 0.4)
    return _apply_env(body, env)


def _poof(dur=0.28, seed=13):
    t, n = _times(dur)
    noise = _noise(n, seed)
    body = _one_pole_lowpass(noise, 900)
    low = _sine_sweep(t, 220, 80, dur)
    mixed = _mix(body, [v * 0.4 for v in low] if np is None else low * 0.4)
    env = _envelope(n, 0.002, dur * 0.35, sustain_level=0.1, release=dur * 0.55)
    return _apply_env(mixed, env)


def _quake(dur=0.8, seed=14):
    return _rumble(dur=dur, seed=seed, base=45)


def _seal_focus(dur=0.35, seed=15, rising=True):
    t, n = _times(dur)
    f0, f1 = (500, 1100) if rising else (1100, 700)
    tone = _sine_sweep(t, f0, f1, dur)
    env = _envelope(n, 0.02, dur * 0.5, sustain_level=0.2, release=dur * 0.35)
    return _apply_env(tone, env)


def _shout(dur=0.4, seed=16):
    t, n = _times(dur)
    tone = _sine_sweep(t, 240, 180, dur)
    noise = _noise(n, seed)
    growl = _bandpass(noise, 400, 500)
    mixed = _mix([v * 0.6 for v in tone] if np is None else tone * 0.6,
                 [v * 0.5 for v in growl] if np is None else growl * 0.5)
    env = _envelope(n, 0.02, dur * 0.5, sustain_level=0.3, release=dur * 0.35)
    return _apply_env(mixed, env)


def _dragon_roar(dur=0.9, seed=17):
    t, n = _times(dur)
    tone = _sine_sweep(t, 160, 90, dur)
    noise = _noise(n, seed)
    growl = _bandpass(noise, 300, 400)
    mixed = _mix([v * 0.7 for v in tone] if np is None else tone * 0.7,
                 [v * 0.6 for v in growl] if np is None else growl * 0.6)
    env = _envelope(n, 0.05, dur * 0.55, sustain_level=0.4, release=dur * 0.35)
    return _apply_env(mixed, env)


def _explosion(dur=0.6, seed=18):
    t, n = _times(dur)
    noise = _noise(n, seed)
    body = _one_pole_lowpass(noise, 700)
    crack = _highpass(_noise(n, seed + 1), 2000)
    mixed = _mix(body, [v * 0.3 for v in crack] if np is None else crack * 0.3)
    env = _envelope(n, 0.002, dur * 0.3, sustain_level=0.2, release=dur * 0.65)
    return _apply_env(mixed, env)


def _slash(dur=0.2, seed=19):
    t, n = _times(dur)
    noise = _noise(n, seed)
    body = _highpass(noise, 2200)
    env = _envelope(n, 0.001, dur * 0.3, sustain_level=0.05, release=dur * 0.6)
    return _apply_env(body, env)


def _splat(dur=0.22, seed=20):
    t, n = _times(dur)
    noise = _noise(n, seed)
    body = _one_pole_lowpass(noise, 500)
    env = _envelope(n, 0.001, dur * 0.35, sustain_level=0.1, release=dur * 0.5)
    return _apply_env(body, env)


def _teleport(dur=0.35, seed=21, up=True):
    t, n = _times(dur)
    f0, f1 = (300, 1600) if up else (1600, 300)
    tone = _sine_sweep(t, f0, f1, dur)
    env = _envelope(n, 0.01, dur * 0.5, sustain_level=0.15, release=dur * 0.35)
    return _apply_env(tone, env)


def _thunder(dur=0.7, seed=22):
    t, n = _times(dur)
    crack = _highpass(_noise(n, seed), 2000)
    rumble = _one_pole_lowpass(_noise(n, seed + 1), 150)
    mixed = _mix([v * 0.5 for v in crack] if np is None else crack * 0.5, rumble)
    env = _envelope(n, 0.002, dur * 0.3, sustain_level=0.4, release=dur * 0.6)
    return _apply_env(mixed, env)


def _metal_throw(dur=0.3, seed=23):
    t, n = _times(dur)
    ring = _sine(t, 2600) if np is None else _sine(t, 2600)
    ring2 = _sine(t, 3300)
    noise = _noise(n, seed)
    hi = _highpass(noise, 3000)
    mixed = _mix([v * 0.3 for v in ring] if np is None else ring * 0.3,
                 [v * 0.2 for v in ring2] if np is None else ring2 * 0.2,
                 [v * 0.4 for v in hi] if np is None else hi * 0.4)
    env = _envelope(n, 0.001, dur * 0.3, sustain_level=0.15, release=dur * 0.6)
    return _apply_env(mixed, env)


def _wind_trap(dur=0.5, seed=24):
    t, n = _times(dur)
    noise = _noise(n, seed)
    cutoff = _linspace(600, 2200, n)
    body = _variable_lowpass(noise, cutoff)
    env = _envelope(n, 0.02, dur * 0.6, sustain_level=0.35, release=dur * 0.3)
    return _apply_env(body, env)


def _double_hit(seed=25):
    hit1 = _punch(dur=0.08, seed=seed, pitch=1.1)
    gap = _zeros(int(RATE * 0.03))
    hit2 = _punch(dur=0.1, seed=seed + 1, pitch=0.9)
    if np is not None:
        return np.concatenate([np.asarray(hit1), np.asarray(gap), np.asarray(hit2)])
    return list(hit1) + list(gap) + list(hit2)


def _chord(freqs, dur, seed=30, wave_fn=None):
    """Sequencia de notas curtas (level up, moeda, conquista): usado para melodias."""
    parts = []
    note_dur = dur / len(freqs)
    for i, f in enumerate(freqs):
        t, n = _times(note_dur)
        tone = _sine(t, f)
        env = _envelope(n, 0.005, note_dur * 0.5, sustain_level=0.3, release=note_dur * 0.45)
        parts.append(_apply_env(tone, env))
    if np is not None:
        return np.concatenate(parts)
    out = []
    for p in parts:
        out.extend(p)
    return out


def _click(dur=0.05, seed=31):
    t, n = _times(dur)
    noise = _noise(n, seed)
    body = _highpass(noise, 4000)
    env = _envelope(n, 0.0005, dur * 0.3, sustain_level=0.05, release=dur * 0.5)
    return _apply_env(body, env)


def _error_buzz(dur=0.3, seed=32):
    t, n = _times(dur)
    tone1 = _sine(t, 220)
    tone2 = _sine(t, 185)
    mixed = _mix([v * 0.5 for v in tone1] if np is None else tone1 * 0.5,
                 [v * 0.5 for v in tone2] if np is None else tone2 * 0.5)
    env = _envelope(n, 0.005, dur * 0.5, sustain_level=0.3, release=dur * 0.35)
    return _apply_env(mixed, env)


def _summon(dur=0.7, seed=33):
    t, n = _times(dur)
    noise = _noise(n, seed)
    low = _one_pole_lowpass(noise, 250)
    tone = _sine_sweep(t, 80, 130, dur)
    mixed = _mix(low, [v * 0.5 for v in tone] if np is None else tone * 0.5)
    env = _envelope(n, 0.08, dur * 0.5, sustain_level=0.4, release=dur * 0.35)
    return _apply_env(mixed, env)


# --------------------------------------------------------------------------- catalogo: id -> spec
# Cada spec: {"gen": callable-> sinal (lista/np.array em -1..1), "gain": 0..1, "channel": "effect",
#             "variations": [callable, ...]  (opcional, escolhido aleatoriamente na hora de tocar)}
def build_catalog():
    cat = {}

    def reg(name, gen, gain=0.85, channel="effect"):
        cat[name] = {"gen": gen, "gain": gain, "channel": channel}

    # ---- sfx referenciados por data/jutsus/*.json (33 nomes) ----
    reg("sfx_fire_whoosh", lambda: _whoosh(0.45, seed=101, rising=True))
    reg("sfx_fire_burst", lambda: _burst(0.35, seed=102, center=900, width=1600))
    reg("sfx_fire_puff", lambda: _poof(0.22, seed=103))
    reg("sfx_explosion", lambda: _explosion(0.6, seed=104))
    reg("sfx_wind_cut", lambda: _slash(0.18, seed=105))
    reg("sfx_wind_burst", lambda: _burst(0.4, seed=106, center=2200, width=2600))
    reg("sfx_wind_roar", lambda: _dragon_roar(0.7, seed=107))
    reg("sfx_wind_trap", lambda: _wind_trap(0.5, seed=108))
    reg("sfx_whirl", lambda: _wind_trap(0.6, seed=109))
    reg("sfx_splash", lambda: _splash(0.35, seed=110))
    reg("sfx_wave", lambda: _wave_gush(0.6, seed=111))
    reg("sfx_bubble", lambda: _bubble(0.3, seed=112))
    reg("sfx_mist", lambda: _mist(0.55, seed=113))
    reg("sfx_hiss", lambda: _hiss(0.45, seed=114))
    reg("sfx_zap", lambda: _zap(0.28, seed=115, freq=1100))
    reg("sfx_zap_loop", lambda: _zap(0.5, seed=116, freq=950, loop=True))
    reg("sfx_thunder", lambda: _thunder(0.7, seed=117))
    reg("sfx_thunder_hit", lambda: _thunder(0.4, seed=118))
    reg("sfx_quake", lambda: _quake(0.8, seed=119))
    reg("sfx_rock_crack", lambda: _crack(0.25, seed=120))
    reg("sfx_rock_rumble", lambda: _rumble(0.9, seed=121, base=48))
    reg("sfx_seal", lambda: _seal_focus(0.3, seed=122, rising=True))
    reg("sfx_focus", lambda: _seal_focus(0.35, seed=123, rising=True))
    reg("sfx_shout", lambda: _shout(0.4, seed=124))
    reg("sfx_dragon_roar", lambda: _dragon_roar(0.9, seed=125))
    reg("sfx_heal", lambda: _chord([523.25, 659.25, 783.99], 0.5, seed=126))
    reg("sfx_heavy_punch", lambda: _punch(0.2, seed=127, pitch=0.8))
    reg("sfx_punch", lambda: _punch(0.14, seed=128, pitch=1.0))
    reg("sfx_kick", lambda: _punch(0.16, seed=129, pitch=0.9))
    reg("sfx_double_hit", lambda: _double_hit(seed=130))
    reg("sfx_slash", lambda: _slash(0.2, seed=131))
    reg("sfx_splat", lambda: _splat(0.22, seed=132))
    reg("sfx_poof", lambda: _poof(0.28, seed=133))
    reg("sfx_teleport", lambda: _teleport(0.35, seed=134, up=True))
    reg("sfx_metal_throw", lambda: _metal_throw(0.3, seed=135))

    # ---- conjunto base do jogo ----
    cat["sfx_taijutsu_hit"] = {
        "variations": [lambda: _hit_variation(201), lambda: _hit_variation(202)],
        "gain": 0.9, "channel": "effect",
    }
    def _critical_hit():
        t, n = _times(0.16)
        ping = _sine_sweep(t, 1200, 1800, 0.16)
        ping = ping * 0.5 if np is not None else [v * 0.5 for v in ping]
        return _mix(_punch(0.16, seed=203, pitch=1.3), ping)
    reg("sfx_critical_hit", _critical_hit)
    reg("sfx_damage_taken", lambda: _thump(0.15, freq=110, seed=204))
    reg("sfx_monster_death", lambda: _mix(_poof(0.3, seed=205), _rumble(0.3, seed=206, base=70)))
    reg("sfx_level_up", lambda: _chord([392.00, 523.25, 659.25], 0.55, seed=207), gain=0.95)
    reg("sfx_item_pickup", lambda: _chord([880.0, 1174.66], 0.18, seed=208), gain=0.7)
    reg("sfx_item_drop", lambda: _chord([440.0, 330.0], 0.18, seed=209), gain=0.7)
    reg("sfx_coin", lambda: _chord([1046.5, 1318.5], 0.2, seed=210), gain=0.75)
    reg("sfx_door", lambda: _mix(_crack(0.3, seed=211), _rumble(0.3, seed=212, base=60)), gain=0.8)
    reg("sfx_menu_open", lambda: _seal_focus(0.25, seed=213, rising=True), gain=0.7)
    reg("sfx_menu_close", lambda: _seal_focus(0.22, seed=214, rising=False), gain=0.7)
    reg("sfx_click", lambda: _click(0.05, seed=215), gain=0.6)
    reg("sfx_achievement", lambda: _chord([523.25, 659.25, 783.99, 1046.5], 0.7, seed=216), gain=0.95)
    reg("sfx_chakra_empty", lambda: _error_buzz(0.3, seed=217), gain=0.8)
    reg("sfx_summon", lambda: _summon(0.7, seed=218), gain=0.85)

    return cat


def _seed_from_name(name):
    return sum(ord(c) for c in name) % 9973


# --------------------------------------------------------------------------- IO
def write_wav(path, samples_int16):
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        if np is not None:
            wf.writeframes(samples_int16.tobytes())
        else:
            wf.writeframes(struct.pack("<%dh" % len(samples_int16), *samples_int16))


def wav_to_ogg(wav_path, ogg_path):
    import soundfile as sf
    data, sr = sf.read(wav_path, dtype="float32")
    sf.write(ogg_path, data, sr, format="OGG", subtype="VORBIS")


def _lua_str(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def write_catalog_lua(catalog_json):
    """Espelha assets-src/audio/sfx_catalog.json como tabela Lua, para o modulo
    client-otc/modules/naruto_sounds ler sem depender do parser JSON em tempo de jogo."""
    lines = [
        "-- GERADO por tools/audio/gen_sfx.py a partir da sintese procedural (nao edite a mao).",
        "-- Fonte da verdade: assets-src/audio/sfx_catalog.json (mesmo conteudo).",
        "-- id -> {file='naruto/x.ogg', gain=0..1, channel='effect'|'ambient'|'music'}",
        "-- ou {variations={'naruto/x_1.ogg', 'naruto/x_2.ogg'}, gain=..., channel=...}",
        "NarutoSfxCatalog = {",
    ]
    for name in sorted(catalog_json.keys()):
        e = catalog_json[name]
        fields = [f"gain = {e['gain']}", f"channel = {_lua_str(e['channel'])}"]
        if "variations" in e:
            files = ", ".join(_lua_str(v) for v in e["variations"])
            fields.append(f"variations = {{{files}}}")
        else:
            fields.append(f"file = {_lua_str(e['file'])}")
        lines.append(f"\t[{_lua_str(name)}] = {{{', '.join(fields)}}},")
    lines.append("}")
    os.makedirs(os.path.dirname(OUT_CATALOG_LUA), exist_ok=True)
    with open(OUT_CATALOG_LUA, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    global RATE

    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", type=int, default=RATE)
    ap.add_argument("--keep-wav", action="store_true", help="mantem os WAV de staging (default: apaga)")
    ap.add_argument("--wav-dir", default=None, help="diretorio de staging para os WAV (default: scratch)")
    args = ap.parse_args()

    RATE = args.rate

    wav_dir = args.wav_dir or os.path.join("/tmp", "shinobi_sfx_wav_staging")
    os.makedirs(wav_dir, exist_ok=True)
    os.makedirs(OUT_OGG_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUT_CATALOG), exist_ok=True)

    jutsu_sfx = collect_jutsu_sfx()
    catalog = build_catalog()

    missing = jutsu_sfx - set(catalog.keys())
    if missing:
        raise SystemExit(f"sfx referenciados em data/jutsus/*.json sem sintese no catalogo: {sorted(missing)}")

    catalog_json = {}
    generated_files = []

    for name in sorted(catalog.keys()):
        spec = catalog[name]
        variations = spec.get("variations")
        entry = {"gain": round(spec.get("gain", 0.85), 3), "channel": spec.get("channel", "effect")}
        if variations:
            files = []
            for i, gen in enumerate(variations, start=1):
                fname = f"{name}_{i}.ogg"
                sig = gen()
                sig = _peak_normalize(sig)
                pcm = _to_int16(sig)
                wav_path = os.path.join(wav_dir, f"{name}_{i}.wav")
                write_wav(wav_path, pcm)
                ogg_path = os.path.join(OUT_OGG_DIR, fname)
                wav_to_ogg(wav_path, ogg_path)
                generated_files.append(ogg_path)
                files.append(f"naruto/{fname}")
                if not args.keep_wav:
                    os.remove(wav_path)
            entry["variations"] = files
        else:
            fname = f"{name}.ogg"
            sig = spec["gen"]()
            sig = _peak_normalize(sig)
            pcm = _to_int16(sig)
            wav_path = os.path.join(wav_dir, f"{name}.wav")
            write_wav(wav_path, pcm)
            ogg_path = os.path.join(OUT_OGG_DIR, fname)
            wav_to_ogg(wav_path, ogg_path)
            generated_files.append(ogg_path)
            entry["file"] = f"naruto/{fname}"
            if not args.keep_wav:
                os.remove(wav_path)
        catalog_json[name] = entry

    with open(OUT_CATALOG, "w", encoding="utf-8") as f:
        json.dump({"rate": RATE, "peak_dbfs": PEAK_DBFS, "sounds": catalog_json}, f, indent=2, ensure_ascii=False)
        f.write("\n")

    write_catalog_lua(catalog_json)

    total_bytes = sum(os.path.getsize(p) for p in generated_files)
    print(f"{len(generated_files)} arquivos .ogg gerados em {OUT_OGG_DIR} ({total_bytes/1024:.1f} KB total)")
    print(f"catalogo: {OUT_CATALOG} ({len(catalog_json)} entradas)")
    print(f"catalogo lua: {OUT_CATALOG_LUA}")
    if not args.keep_wav:
        try:
            os.rmdir(wav_dir)
        except OSError:
            pass


if __name__ == "__main__":
    main()
