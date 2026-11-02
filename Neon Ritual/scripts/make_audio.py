"""
NEON_RITUAL - bespoke 15 s audio bed.
Two variants: ritual techno (main) and cinematic industrial.
Pure numpy synthesis, 48 kHz / 16-bit stereo WAV.
"""

import os
import wave
import numpy as np

SR = 48000
DUR = 15.0
N = int(SR * DUR)
BASE = r"D:\Tes Animasi-Motion-Blender\Neon Ritual"
OUT = os.path.join(BASE, "audio")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(20261102)
t = np.arange(N) / SR

D1 = 36.708
D2 = 73.416
F2 = 87.307
G2 = 97.999
A2 = 110.000
BB2 = 116.541
C3 = 130.813
D3 = 146.832
A3 = 220.000


def note(freq, dur, kind="sine"):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    if kind == "sine":
        return np.sin(2 * np.pi * freq * tt)
    if kind == "saw":
        return 2.0 * ((tt * freq) % 1.0) - 1.0
    if kind == "square":
        return np.sign(np.sin(2 * np.pi * freq * tt))
    raise ValueError(kind)


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def fft_filter(x, kind, cutoff, order=2, width=1.0):
    n = len(x)
    if n == 0:
        return x
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    ff = np.maximum(f, 1e-6)
    if kind == "low":
        H = 1.0 / np.sqrt(1.0 + (ff / cutoff) ** (2 * order))
    elif kind == "high":
        H = 1.0 / np.sqrt(1.0 + (cutoff / ff) ** (2 * order))
    elif kind == "band":
        H = np.exp(-0.5 * ((f - cutoff) / max(width, 1.0)) ** 2)
    else:
        raise ValueError(kind)
    return np.fft.irfft(X * H, n)


def add(buf, start, sig, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= N:
        return
    sig = sig[:N - i]
    j = i + len(sig)
    gl = np.sqrt((1.0 - pan) * 0.5)
    gr = np.sqrt((1.0 + pan) * 0.5)
    buf[0, i:j] += sig * gain * gl
    buf[1, i:j] += sig * gain * gr


def kick(dur=0.55, f0=115.0, f1=43.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-tt / 0.035)
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) * np.exp(-tt / 0.22)
    click = rng.standard_normal(n) * np.exp(-tt / 0.006) * 0.45
    return np.tanh((body + click) * 1.5)


def impact(dur=1.4, freq=34.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    sub = np.sin(2 * np.pi * freq * tt) * np.exp(-tt / 0.5)
    noise = rng.standard_normal(n) * np.exp(-tt / 0.09)
    metal = (np.sin(2 * np.pi * 1730 * tt) +
             0.6 * np.sin(2 * np.pi * 2410 * tt)) * np.exp(-tt / 0.18)
    return np.tanh((sub * 1.3 + noise * 0.5 + metal * 0.25) * 1.2)


def metal_hit(dur=0.45, base=2150.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    noise = rng.standard_normal(n)
    noise = fft_filter(noise, "band", base, width=900)
    ring = (np.sin(2 * np.pi * base * tt) +
            0.5 * np.sin(2 * np.pi * base * 1.47 * tt) +
            0.3 * np.sin(2 * np.pi * base * 2.09 * tt))
    return (noise * 0.8 + ring * 0.35) * np.exp(-tt / 0.13)


def riser(dur=0.9, f0=220.0, f1=1600.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    noise = rng.standard_normal(n)
    noise = fft_filter(noise, "band", 1800, width=1400)
    sweep = np.sin(2 * np.pi * (f0 * (f1 / f0) ** (tt / dur)) * tt)
    env = (tt / dur) ** 2
    return (noise * 0.55 + sweep * 0.35) * env


def bell(dur=2.4, f=190.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    mod = 3.2 * np.exp(-tt / 0.75)
    car = np.sin(2 * np.pi * f * tt + mod * np.sin(2 * np.pi * f * 2.76 * tt))
    return car * np.exp(-tt / 1.15)


def chain_rattle(dur=0.18):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    noise = rng.standard_normal(n)
    noise = fft_filter(noise, "band", 2600, width=1500)
    clicks = np.zeros(n)
    for k in range(3):
        i = int(rng.uniform(0, n - 400))
        clicks[i:i + 300] += rng.standard_normal(300) * np.exp(-np.arange(300) / 70.0)
    return (noise * 0.6 + clicks * 0.9) * np.exp(-tt / 0.06)


def make_track(mode):
    buf = np.zeros((2, N), dtype=np.float64)

    # --- drone / room tone
    drone = (0.55 * np.sin(2 * np.pi * D1 * t + 0.22 * np.sin(2 * np.pi * 0.07 * t)) +
             0.28 * np.sin(2 * np.pi * D1 * 1.5 * t) +
             0.17 * np.sin(2 * np.pi * D2 * t + 0.1 * np.sin(2 * np.pi * 0.11 * t)))
    lfo = 0.65 + 0.35 * np.sin(2 * np.pi * 0.055 * t - 1.2)
    drone = fft_filter(drone * lfo, "low", 180, order=3)
    add(buf, 0, drone, 0.20, -0.15)
    add(buf, 0, np.roll(drone, 37), 0.20, 0.15)

    room = fft_filter(rng.standard_normal(N), "low", 160, order=2)
    add(buf, 0, room, 0.045, 0.0)

    # --- bell and chain intro
    add(buf, 0.05, bell(2.8, 182), 0.20, -0.2)
    add(buf, 13.6, bell(2.2, 196), 0.22, 0.1)
    for k in range(12):
        add(buf, 0.15 + k * 0.23 + rng.uniform(-0.03, 0.03),
            chain_rattle(0.16 + rng.uniform(0, 0.08)),
            0.10, rng.uniform(-0.6, 0.6))

    # --- impacts at the cut points
    for st, g in ((3.0, 0.55), (6.0, 0.75), (8.0, 0.85),
                  (10.0, 0.35), (12.0, 0.75), (13.0, 0.95),
                  (14.0, 1.0)):
        add(buf, st, impact(1.5, 33.0), g, 0.0)
        add(buf, st, metal_hit(0.5, 2100 + 180 * st), g * 0.35,
            rng.uniform(-0.25, 0.25))

    # --- risers into the reveal / impact
    for st, d in ((5.35, 0.65), (11.5, 0.5), (12.55, 0.45), (13.45, 0.55)):
        add(buf, st, riser(d, 240, 1800), 0.22, 0.0)

    if mode == "ritual":
        # four-on-the-floor from 3 s, break for the event-info shot
        for k in range(24):
            st = 3.0 + 0.5 * k
            if st >= 15.0:
                break
            if 10.0 <= st < 12.0:
                g = 0.15
            elif st in (3.0, 6.0, 8.0, 12.0, 13.0, 14.0):
                g = 0.85
            else:
                g = 0.52
            add(buf, st, kick(), g, 0.0)

        # rolling bass, sidechained
        pattern = [D2, D2, F2, D2, G2, D2, BB2, A2]
        bass = np.zeros(N)
        step = 0.25
        k = 0
        st = 3.0
        while st < 14.8:
            n = note(pattern[k % len(pattern)], step * 1.1, "saw")
            n = fft_filter(n, "low", 330, order=2)
            en = np.ones(len(n)) * (0.55 if 10.0 <= st < 12.0 else 1.0)
            i = int(st * SR)
            j = min(N, i + len(n))
            bass[i:j] += (n * en)[:j - i] * 0.45
            st += step
            k += 1
        sc = np.ones(N)
        for kk in range(24):
            st = 3.0 + 0.5 * kk
            if st >= N / SR:
                break
            i = int(st * SR)
            nn = int(0.38 * SR)
            j = min(N, i + nn)
            e = 1.0 - 0.9 * np.exp(-np.arange(j - i) / (0.11 * SR))
            sc[i:j] = np.minimum(sc[i:j], e)
        bass *= sc
        add(buf, 0, bass, 0.42, 0.0)

        # red-alert synth from 6 s
        alert = np.zeros(N)
        st = 6.0
        idx = 0
        while st < 14.5:
            dur = 0.22
            n = int(dur * SR)
            tt = np.arange(n) / SR
            a = note(D3, dur, "saw") + 0.7 * note(A3, dur, "saw")
            a = fft_filter(a, "low", 500 + 90 * idx, order=2)
            a *= np.exp(-tt / 0.12)
            i = int(st * SR)
            j = min(N, i + n)
            alert[i:j] += a[:j - i]
            st += 0.25
            idx += 1
        alert_env = np.ones(N)
        alert_env[int(10.0 * SR):int(12.0 * SR)] = 0.5
        add(buf, 0, alert * sc * alert_env, 0.16, 0.35)

    else:
        # cinematic variant: slow pulse, no four-on-floor
        for k in range(15):
            st = 3.0 + k * 0.75
            n = int(0.7 * SR)
            tt = np.arange(n) / SR
            pulse = np.sin(2 * np.pi * D1 * tt) * np.exp(-tt / 0.28)
            add(buf, st, pulse, 0.22, 0.0)
        add(buf, 0, fft_filter(note(D2, 15.0, "saw"), "low", 180, order=3),
            0.10, 0.0)

    # --- reverb send (metallic sources)
    send = np.zeros((2, N))
    # use the already-added percussion by extracting a high-passed copy
    send[0] = fft_filter(buf[0], "high", 700, order=2) * 0.30
    send[1] = fft_filter(buf[1], "high", 700, order=2) * 0.30
    ir_n = int(1.0 * SR)
    ir_t = np.arange(ir_n) / SR
    ir = rng.standard_normal((2, ir_n)) * np.exp(-ir_t / 0.55)
    ir = fft_filter(ir[0], "low", 6000, order=2), fft_filter(ir[1], "low", 6000, order=2)
    ir = np.array(ir)
    for ch in range(2):
        nfft = 1 << (N + ir_n - 1).bit_length()
        wet = np.fft.irfft(np.fft.rfft(send[ch], nfft) *
                           np.fft.rfft(ir[ch], nfft), nfft)[:N]
        buf[ch] += wet * 0.55

    # --- master
    mix = np.tanh(buf * 1.15)
    peak = float(np.max(np.abs(mix)))
    if peak > 1e-9:
        mix *= 0.80 / peak
    fade_in = int(2.5 * SR)
    mix[:, :fade_in] *= np.linspace(0, 1, fade_in) ** 1.4
    fade_out = int(0.35 * SR)
    mix[:, -fade_out:] *= np.linspace(1, 0, fade_out)
    return mix


def write_wav(path, mix):
    data = np.clip(mix.T, -1, 1)
    data = (data * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def stats(mix):
    peak = float(np.max(np.abs(mix)))
    rms = float(np.sqrt(np.mean(mix ** 2)))
    per_sec = [float(np.sqrt(np.mean(mix[:, i * SR:(i + 1) * SR] ** 2)))
               for i in range(int(DUR))]
    print("PEAK %.3f (%.1f dBFS)  RMS %.3f (%.1f dBFS)"
          % (peak, 20 * np.log10(max(peak, 1e-9)),
             rms, 20 * np.log10(max(rms, 1e-9))))
    print("PER_SEC", [round(v, 3) for v in per_sec])


if __name__ == "__main__":
    for mode, name in (("ritual", "NEON_RITUAL_AUDIO.wav"),
                       ("cinematic", "NEON_RITUAL_AUDIO_CINEMATIC.wav")):
        mix = make_track(mode)
        path = os.path.join(OUT, name)
        write_wav(path, mix)
        print("WROTE", path, os.path.getsize(path))
        stats(mix)
