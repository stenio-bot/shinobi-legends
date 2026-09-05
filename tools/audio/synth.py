#!/usr/bin/env python3
"""Motor de sintese reutilizavel (osciladores, ADSR, filtros, delay, mixer, escalas).

Compartilhado por tools/audio/gen_sfx.py (SFX curtos, ainda com suas proprias funcoes
internas - nao foi refeito para nao arriscar quebrar os 51 sons ja validados) e
tools/audio/gen_music.py (musica ambiente em loop, ver docs/sistemas/audio.md).

So numpy como dependencia (ja usado por gen_sfx.py). Nenhum material de terceiros
(ADR-002) - tudo e osciladores/ruido filtrado gerados aqui.
"""
import math

import numpy as np

RATE = 22050


# --------------------------------------------------------------------------- tempo/osciladores
def times(dur, rate=RATE):
    n = max(1, int(rate * dur))
    return np.arange(n) / rate, n


def sine(t, freq, phase=0.0):
    return np.sin(2 * math.pi * freq * t + phase)


def sine_vibrato(t, freq, vibrato_hz=5.0, vibrato_depth=0.01, phase=0.0):
    """Seno com vibrato (variacao de frequencia senoidal) - usado no shakuhachi."""
    inst_freq = freq * (1.0 + vibrato_depth * np.sin(2 * math.pi * vibrato_hz * t))
    # integra a frequencia instantanea para obter a fase (evita clique de fase)
    phase_arr = 2 * math.pi * np.cumsum(inst_freq) / RATE
    return np.sin(phase_arr + phase)


def sine_sweep(t, f0, f1, dur):
    k = (f1 - f0) / max(dur, 1e-9)
    phase = 2 * math.pi * (f0 * t + 0.5 * k * t * t)
    return np.sin(phase)


def triangle(t, freq):
    return 2.0 * np.abs(2.0 * ((t * freq) % 1.0) - 1.0) - 1.0


def sawtooth(t, freq):
    return 2.0 * ((t * freq) % 1.0) - 1.0


def square(t, freq, duty=0.5):
    return np.where((t * freq) % 1.0 < duty, 1.0, -1.0)


def noise(n, seed):
    rng = np.random.default_rng(seed)
    return rng.uniform(-1.0, 1.0, n)


def linspace(a, b, n):
    return np.linspace(a, b, n)


# --------------------------------------------------------------------------- filtros (1 polo, baratos)
def one_pole_lowpass(x, cutoff_hz, rate=RATE):
    alpha = 1 - math.exp(-2 * math.pi * cutoff_hz / rate)
    y = np.zeros_like(x, dtype=np.float64)
    acc = 0.0
    for i in range(len(x)):
        acc = acc + alpha * (x[i] - acc)
        y[i] = acc
    return y


def variable_lowpass(x, cutoff_series, rate=RATE):
    y = np.zeros_like(x, dtype=np.float64)
    acc = 0.0
    for i in range(len(x)):
        alpha = 1 - math.exp(-2 * math.pi * float(cutoff_series[i]) / rate)
        acc = acc + alpha * (x[i] - acc)
        y[i] = acc
    return y


def highpass(x, cutoff_hz, rate=RATE):
    return x - one_pole_lowpass(x, cutoff_hz, rate)


def bandpass(x, center_hz, width_hz, rate=RATE):
    lo = one_pole_lowpass(x, center_hz + width_hz / 2, rate)
    return highpass(lo, max(20.0, center_hz - width_hz / 2), rate)


def variable_bandpass(x, center_series, width_series, rate=RATE):
    lo = variable_lowpass(x, center_series + width_series / 2, rate)
    hi_cut = np.maximum(20.0, center_series - width_series / 2)
    return highpass(lo, float(np.mean(hi_cut)), rate)


# --------------------------------------------------------------------------- delay / pseudo-reverb
def delay(x, delay_s, feedback=0.35, mix=0.35, rate=RATE, taps=6):
    """Delay simples com feedback (eco). `taps` controla quantas repeticoes."""
    d = max(1, int(delay_s * rate))
    y = np.array(x, dtype=np.float64, copy=True)
    n = len(x)
    out = np.zeros(n, dtype=np.float64)
    gain = mix
    for k in range(1, taps + 1):
        shift = d * k
        if shift >= n:
            break
        out[shift:] += x[: n - shift] * gain
        gain *= feedback
    return y + out


def synthetic_reverb(x, decay_s=1.2, density=24, seed=99, rate=RATE, mix=0.4):
    """Reverb por convolucao com uma resposta ao impulso sintetica (ruido decaindo
    exponencialmente) - barato e sem precisar de IR de terceiros (ADR-002)."""
    ir_n = max(1, int(decay_s * rate))
    rng = np.random.default_rng(seed)
    ir = rng.uniform(-1.0, 1.0, ir_n)
    env = np.exp(-np.arange(ir_n) / (rate * decay_s / 5.0))
    ir = ir * env
    ir = ir / (np.sqrt(np.sum(ir ** 2)) + 1e-9)
    # convolucao via FFT (rapida o bastante para faixas de ~90s a 22050 Hz)
    wet = np.convolve(x, ir, mode="full")[: len(x)]
    peak_dry = np.max(np.abs(x)) + 1e-9
    peak_wet = np.max(np.abs(wet)) + 1e-9
    wet = wet * (peak_dry / peak_wet)
    return x * (1 - mix) + wet * mix


# --------------------------------------------------------------------------- envelope / mixer
def adsr(n, attack, decay, sustain_level=0.7, release=0.2, rate=RATE):
    a = max(1, int(attack * rate))
    d = max(1, int(decay * rate))
    r = max(1, int(release * rate))
    body = max(0, n - a - r)
    env = np.empty(n, dtype=np.float64)
    idx = 0
    if a > 0:
        seg = min(a, n)
        env[idx: idx + seg] = np.linspace(0, 1, seg, endpoint=False)
        idx += seg
    if idx < n and d > 0:
        seg = min(d, n - idx)
        env[idx: idx + seg] = np.linspace(1, sustain_level, seg, endpoint=False)
        idx += seg
    if idx < n and body > 0:
        seg = min(max(0, n - idx - r), n - idx)
        env[idx: idx + seg] = sustain_level
        idx += seg
    if idx < n:
        seg = n - idx
        env[idx:idx + seg] = np.linspace(sustain_level, 0, seg)
    return env[:n]


def apply_env(x, env):
    n = min(len(x), len(env))
    return x[:n] * env[:n]


def mix(*sigs_with_gain):
    """Cada item e (sinal, ganho) ou so o sinal (ganho=1). Preenche com zero ate o maior."""
    sigs = []
    for item in sigs_with_gain:
        if isinstance(item, tuple):
            s, g = item
        else:
            s, g = item, 1.0
        sigs.append(np.asarray(s, dtype=np.float64) * g)
    n = max(len(s) for s in sigs)
    out = np.zeros(n, dtype=np.float64)
    for s in sigs:
        out[: len(s)] += s
    return out


def pad_to(x, n):
    if len(x) >= n:
        return x[:n]
    out = np.zeros(n, dtype=np.float64)
    out[: len(x)] = x
    return out


def peak_normalize_db(x, target_dbfs=-12.0):
    target = 10 ** (target_dbfs / 20.0)
    m = float(np.max(np.abs(x))) if len(x) else 0.0
    if m < 1e-9:
        return x
    return x * (target / m)


def to_int16(x):
    xi = np.clip(x, -1.0, 1.0)
    return (xi * 32767.0).astype(np.int16)


# --------------------------------------------------------------------------- estereo
def to_stereo(mono, width=0.0, seed=1):
    """Duplica mono -> estereo. width>0 adiciona um leve descasamento (micro-delay +
    ruido de fase) entre L/R para dar largura sem precisar de IR verdadeira."""
    if width <= 0:
        return np.stack([mono, mono], axis=1)
    shift = max(1, int(width * RATE))
    right = np.empty_like(mono)
    right[:shift] = mono[:shift]
    right[shift:] = mono[:-shift]
    return np.stack([mono, right], axis=1)


def stereo_mix(*stereo_sigs):
    n = max(s.shape[0] for s in stereo_sigs)
    out = np.zeros((n, 2), dtype=np.float64)
    for s in stereo_sigs:
        out[: s.shape[0]] += s
    return out


# --------------------------------------------------------------------------- corda dedilhada (Karplus-Strong)
def karplus_strong(freq, dur, rate=RATE, seed=0, damping=0.996, brightness=0.5, detune=1.0):
    """Sintese de corda dedilhada (koto/shamisen): preenche uma linha de atraso do
    tamanho do periodo com ruido e filtra por media movel a cada volta, decaindo
    naturalmente. `brightness` mistura media-movel (grave) com o sample cru (agudo);
    `detune` desafina levemente a frequencia (usado nas Ruinas)."""
    freq = max(20.0, freq * detune)
    period = max(2, int(round(rate / freq)))
    n = max(period + 1, int(rate * dur))
    rng = np.random.default_rng(seed)
    buf = rng.uniform(-1.0, 1.0, period)
    out = np.empty(n, dtype=np.float64)
    prev = buf[-1]
    for i in range(n):
        idx = i % period
        cur = buf[idx]
        avg = 0.5 * (cur + prev)
        newv = damping * (brightness * avg + (1 - brightness) * cur)
        buf[idx] = newv
        prev = newv
        out[i] = cur
    return out


# --------------------------------------------------------------------------- escalas / notas
A4 = 440.0


def note_freq(semitones_from_a4):
    return A4 * (2 ** (semitones_from_a4 / 12.0))


# Escalas japonesas pentatonicas classicas, como graus (semitons a partir da tonica).
SCALE_YO = [0, 2, 5, 7, 9]         # yo (major-like, "alegre")
SCALE_IN = [0, 1, 5, 7, 8]         # in (minor-like, melancolica - shakuhachi tradicional)
SCALE_DORIAN = [0, 2, 3, 5, 7, 9, 10]
SCALE_MINOR_PENTA = [0, 3, 5, 7, 10]


def scale_freq(root_semitone, scale, degree, octave=0):
    """degree pode ser negativo/maior que len(scale) - 1 (envolve oitavas)."""
    n = len(scale)
    oct_shift, idx = divmod(degree, n)
    semis = root_semitone + scale[idx] + 12 * (octave + oct_shift)
    return note_freq(semis)


# --------------------------------------------------------------------------- loop sem clique
def crossfade_loop(x, fade_s, rate=RATE):
    """Funde o final da faixa com o comeco (equal-power) para looping sem clique.
    Retorna uma faixa com o MESMO comprimento de entrada (o crossfade acontece dentro
    da regiao final, misturando com uma copia do inicio) - ao tocar em loop com o
    proprio SoundChannel:enqueue, o fim ja soa como o comeco."""
    n = len(x)
    f = max(1, min(int(fade_s * rate), n // 4))
    out = np.array(x, dtype=np.float64, copy=True)
    fade_in = np.sin(0.5 * math.pi * np.linspace(0, 1, f)) ** 2   # equal power
    fade_out = np.cos(0.5 * math.pi * np.linspace(0, 1, f)) ** 2
    head = x[:f]
    tail = x[n - f: n]
    blended = tail * fade_out + head * fade_in
    out[n - f: n] = blended
    return out


def crossfade_loop_stereo(x, fade_s, rate=RATE):
    n = x.shape[0]
    f = max(1, min(int(fade_s * rate), n // 4))
    out = np.array(x, dtype=np.float64, copy=True)
    fade_in = (np.sin(0.5 * math.pi * np.linspace(0, 1, f)) ** 2)[:, None]
    fade_out = (np.cos(0.5 * math.pi * np.linspace(0, 1, f)) ** 2)[:, None]
    head = x[:f]
    tail = x[n - f: n]
    out[n - f: n] = tail * fade_out + head * fade_in
    return out
