#!/usr/bin/env python3
"""Analisa as faixas de musica geradas (RMS, clipping, espectro) e desenha um PNG por
faixa (forma de onda + espectrograma) em screenshots/music_<regiao>.png - "escutar com
os olhos" ja que o agente nao ouve audio (missao de musica ambiente, 2026-09-05).

Sem matplotlib/Pillow (nao instalados, evita puxar dependencia pesada so p/ isso):
escreve o PNG a mao (zlib da stdlib para o IDAT), grayscale/RGB simples.

Uso: .venv/bin/python tools/audio/analyze_music.py
"""
import json
import os
import struct
import zlib

import numpy as np
import soundfile as sf

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
MUSIC_DIR = os.path.join(ROOT, "client-otc", "data", "sounds", "naruto", "music")
CATALOG = os.path.join(ROOT, "assets-src", "audio", "music_catalog.json")
OUT_DIR = os.path.join(ROOT, "screenshots")


# --------------------------------------------------------------------------- PNG minimo (sem libs)
def write_png(path, rgb):
    h, w, _ = rgb.shape
    raw = bytearray()
    for y in range(h):
        raw.append(0)  # filtro "None"
        raw.extend(rgb[y].astype(np.uint8).tobytes())
    compressed = zlib.compress(bytes(raw), 6)

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)  # 8 bit, color type 2 = RGB
    with open(path, "wb") as f:
        f.write(sig)
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", compressed))
        f.write(chunk(b"IEND", b""))


def colormap(v):
    """v em [0,1] -> RGB (uint8), gradiente escuro->azul->ciano->amarelo (tipo 'magma' pobre)."""
    stops = np.array([
        [0.00, 8, 8, 20],
        [0.25, 40, 20, 90],
        [0.50, 40, 90, 160],
        [0.75, 80, 200, 200],
        [1.00, 255, 240, 140],
    ], dtype=np.float64)
    v = np.clip(v, 0.0, 1.0)
    out = np.zeros(v.shape + (3,), dtype=np.float64)
    for i in range(len(stops) - 1):
        p0, p1 = stops[i], stops[i + 1]
        mask = (v >= p0[0]) & (v <= p1[0])
        span = max(p1[0] - p0[0], 1e-9)
        frac = np.clip((v - p0[0]) / span, 0, 1)
        for c in range(3):
            out[..., c] = np.where(mask, p0[1 + c] + (p1[1 + c] - p0[1 + c]) * frac, out[..., c])
    return out


def spectrogram_db(sig_mono, rate, win=1024, hop=256):
    n = len(sig_mono)
    window = np.hanning(win)
    frames = []
    i = 0
    while i + win <= n:
        seg = sig_mono[i:i + win] * window
        spec = np.fft.rfft(seg)
        mag = np.abs(spec) + 1e-9
        frames.append(20 * np.log10(mag))
        i += hop
    mat = np.array(frames).T  # freq x time
    freqs = np.fft.rfftfreq(win, 1.0 / rate)
    return freqs, mat


def draw_waveform(sig_mono, width, height):
    n = len(sig_mono)
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:, :] = (16, 18, 24)
    mid = height // 2
    step = max(1, n // width)
    for x in range(width):
        chunk = sig_mono[x * step:(x + 1) * step]
        if len(chunk) == 0:
            continue
        lo = float(np.min(chunk))
        hi = float(np.max(chunk))
        y0 = int(mid - hi * (height / 2 - 2))
        y1 = int(mid - lo * (height / 2 - 2))
        y0, y1 = sorted((max(0, min(height - 1, y0)), max(0, min(height - 1, y1))))
        img[y0:y1 + 1, x] = (110, 200, 255)
    img[mid, :] = (60, 70, 80)
    return img


def draw_spectrogram(mat_db, width, height, fmax_bins=None):
    freq_bins, time_bins = mat_db.shape
    if fmax_bins:
        freq_bins = min(freq_bins, fmax_bins)
        mat_db = mat_db[:freq_bins, :]
    # reamostra para width x height (nearest) sem scipy
    tx = (np.linspace(0, time_bins - 1, width)).astype(int)
    fy = (np.linspace(freq_bins - 1, 0, height)).astype(int)  # inverte (grave embaixo)
    resampled = mat_db[np.ix_(fy, tx)]
    vmax = float(np.max(resampled))
    vmin = vmax - 70.0
    norm = np.clip((resampled - vmin) / (vmax - vmin), 0, 1)
    return colormap(norm).astype(np.uint8)


def analyze_track(region_id, entry):
    path = os.path.join(MUSIC_DIR, os.path.basename(entry["file"]))
    data, rate = sf.read(path, dtype="float64", always_2d=True)
    mono = data.mean(axis=1)
    n = len(mono)
    dur = n / rate

    peak = float(np.max(np.abs(data)))
    clipping = peak >= 0.999

    win_s = 1.0
    win = int(win_s * rate)
    hop = win // 2
    rms_vals = []
    i = 0
    while i + win <= n:
        seg = mono[i:i + win]
        rms_vals.append(float(np.sqrt(np.mean(seg ** 2)) + 1e-12))
        i += hop
    rms_vals = np.array(rms_vals)
    rms_db = 20 * np.log10(rms_vals)
    rms_mean_db = float(np.mean(rms_db))
    rms_std_db = float(np.std(rms_db))

    spec = np.abs(np.fft.rfft(mono * np.hanning(n)))
    freqs = np.fft.rfftfreq(n, 1.0 / rate)
    bands = [
        ("sub 20-80Hz", 20, 80), ("grave 80-250Hz", 80, 250), ("medio-grave 250-800Hz", 250, 800),
        ("medio 800-2500Hz", 800, 2500), ("agudo 2500-6000Hz", 2500, 6000), ("brilho 6000+Hz", 6000, rate / 2),
    ]
    total_energy = float(np.sum(spec ** 2)) + 1e-12
    band_pct = {}
    for name, lo, hi in bands:
        mask = (freqs >= lo) & (freqs < hi)
        band_pct[name] = round(100.0 * float(np.sum(spec[mask] ** 2)) / total_energy, 1)

    freqs_sg, mat_db = spectrogram_db(mono, rate)
    max_freq_bin = int(np.searchsorted(freqs_sg, 6000))

    W, H_WAVE, H_SPEC = 1000, 220, 380
    wave_img = draw_waveform(mono, W, H_WAVE)
    spec_img = draw_spectrogram(mat_db, W, H_SPEC, fmax_bins=max_freq_bin)
    gap = np.full((4, W, 3), (200, 200, 200), dtype=np.uint8)
    full = np.concatenate([wave_img, gap, spec_img], axis=0)

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, f"music_{region_id}.png")
    write_png(out_path, full)

    return {
        "region": region_id,
        "duration_s": round(dur, 2),
        "peak_dbfs": round(20 * np.log10(peak + 1e-12), 2),
        "clipping": clipping,
        "rms_mean_dbfs": round(rms_mean_db, 2),
        "rms_std_db": round(rms_std_db, 2),
        "band_energy_pct": band_pct,
        "png": out_path,
    }


def main():
    with open(CATALOG, encoding="utf-8") as f:
        catalog = json.load(f)
    report = []
    for region_id, entry in catalog["tracks"].items():
        r = analyze_track(region_id, entry)
        report.append(r)
        print(f"== {region_id} ==")
        print(f"  duracao: {r['duration_s']}s  pico: {r['peak_dbfs']} dBFS  clipping: {r['clipping']}")
        print(f"  RMS medio: {r['rms_mean_dbfs']} dBFS  (desvio {r['rms_std_db']} dB)")
        print(f"  energia por banda: {r['band_energy_pct']}")
        print(f"  png: {r['png']}")
    with open(os.path.join(OUT_DIR, "music_analysis_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
