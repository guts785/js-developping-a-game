"""gen_audio — 100% procedural WAV synthesis (no samples, no numpy).
Maqam-based music, oud/qanun/darbuka modelled additively, plus SFX + ambience.
"""
import math, os, random, struct, wave

SR = 22050
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audio")


# ---------------------------------------------------------------- helpers
def write_wav(name, samples, sr=SR):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    data = bytearray()
    for s in samples:
        v = int(max(-1.0, min(1.0, s)) * 32000)
        data += struct.pack("<h", v)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(bytes(data))
    print("wrote", name, f"{len(samples)/sr:.2f}s")
    return path


def env(i, n, a=0.01, d=0.2, s=0.7, r=0.3):
    """ADSR by normalised position."""
    t = i / max(1, n - 1)
    if t < a:
        return t / a
    if t < a + d:
        return 1.0 - (1.0 - s) * ((t - a) / d)
    if t < 1.0 - r:
        return s
    return s * max(0.0, (1.0 - t) / r)


def pluck(freq, dur, amp=0.5, bright=0.5, detune=0.004):
    """Oud-ish plucked string: harmonic stack with fast decay + slight detune."""
    n = int(dur * SR)
    out = [0.0] * n
    rnd = random.Random(int(freq * 1000))
    for i in range(n):
        t = i / SR
        e = math.exp(-t * (5.0 + 2.0 * (1 - bright)))
        v = 0.0
        for h in range(1, 9):
            ha = (bright ** (h - 1)) / h
            v += ha * math.sin(2 * math.pi * freq * h * t * (1 + detune * h * (rnd.random() - 0.5)))
        # body thump
        v += 0.25 * math.sin(2 * math.pi * freq * 0.5 * t) * math.exp(-t * 14)
        out[i] = v * e * amp
    return out


def qanun(freq, dur, amp=0.25):
    """Tremolo plucked — quick repeated plucks (qanun/kanoun)."""
    out = [0.0] * int(dur * SR)
    step = int(0.055 * SR)
    for k in range(0, len(out), step):
        p = pluck(freq * (1 + 0.0006 * k), step / SR * 1.6, amp * 0.5, 0.8)
        for j, v in enumerate(p):
            if k + j < len(out):
                out[k + j] += v
    return out


def ney(freq, dur, amp=0.3, vib=5.0):
    """Breathy reed flute — the sound of a Moroccan night."""
    n = int(dur * SR)
    out = [0.0] * n
    rnd = random.Random(7)
    for i in range(n):
        t = i / SR
        f = freq * (1 + 0.006 * math.sin(2 * math.pi * vib * t))
        v = math.sin(2 * math.pi * f * t)
        v += 0.4 * math.sin(2 * math.pi * f * 2 * t)
        v += 0.12 * math.sin(2 * math.pi * f * 3 * t)
        breath = (rnd.random() - 0.5) * 0.22
        e = env(i, n, 0.12, 0.15, 0.8, 0.35)
        out[i] = (v * 0.5 + breath) * e * amp
    return out


def darbuka(dur=0.22, low=True, amp=0.6):
    """Dumbek: pitched low hit + noisy slap."""
    n = int(dur * SR)
    out = [0.0] * n
    rnd = random.Random(3)
    base = 92.0 if low else 190.0
    for i in range(n):
        t = i / SR
        if low:
            v = math.sin(2 * math.pi * base * (1 - 2.2 * t) * t) * math.exp(-t * 22)
        else:
            v = 0.35 * (rnd.random() - 0.5) * math.exp(-t * 42)
            v += 0.5 * math.sin(2 * math.pi * base * t) * math.exp(-t * 26)
        out[i] = v * amp
    return out


def mix(*tracks):
    n = max(len(t) for t in tracks)
    out = [0.0] * n
    for t in tracks:
        for i, v in enumerate(t):
            out[i] += v
    return out


def at(track, pos_s, samples):
    """Overlay samples into a track at a time position."""
    start = int(pos_s * SR)
    need = start + len(samples)
    if need > len(track):
        track.extend([0.0] * (need - len(track)))
    for i, v in enumerate(samples):
        track[start + i] += v
    return track


def loop_fade(track, fade=0.35):
    """Crossfade the tail into the head so loops are seamless."""
    n = int(fade * SR)
    if n * 2 >= len(track):
        return track
    for i in range(n):
        f = i / n
        track[i] = track[i] * f + track[len(track) - n + i] * (1 - f)
    return track[:len(track) - n]


# ---------------------------------------------------------------- maqam
# Hijaz on D: D Eb F# G A Bb C  (the "Moroccan night" scale)
HIJAZ = [146.83, 155.56, 185.00, 196.00, 220.00, 233.08, 261.63, 293.66]
# Nahawand on A: darker, for the sect
NAHAWAND = [110.00, 123.47, 130.81, 146.83, 164.81, 174.61, 196.00, 220.00]


def music_menu(dur=30.0):
    n = int(dur * SR)
    tr = [0.0] * n
    # bass drone
    for i in range(n):
        t = i / SR
        tr[i] += 0.16 * math.sin(2 * math.pi * 73.42 * t) * (1 + 0.06 * math.sin(2 * math.pi * 0.11 * t))
    # oud melody
    melody = [0, 2, 1, 0, 3, 2, 4, 3, 2, 1, 0, 1, 2, 0, -1, 0]
    tpos = 0.0
    for k in range(int(dur / 1.5)):
        deg = melody[k % len(melody)]
        f = HIJAZ[deg % len(HIJAZ)] * (2 if deg >= len(HIJAZ) else 1)
        p = pluck(f, 1.9, 0.42, 0.55)
        at(tr, tpos, p)
        if k % 4 == 0:
            at(tr, tpos, qanun(f * 2, 1.4, 0.10))
        tpos += 1.5
    # ney answers
    for k in range(6):
        at(tr, 4.0 + k * 4.7, ney(HIJAZ[(k * 3) % len(HIJAZ)] * 2, 2.6, 0.16))
    # darbuka pattern — maqsoum-ish
    beat = 0.5
    k = 0
    while k * beat < dur - 0.5:
        tpos = k * beat
        if k % 8 in (0, 3, 6):
            at(tr, tpos, darbuka(0.3, True, 0.30))
        elif k % 8 in (2, 4, 7):
            at(tr, tpos, darbuka(0.16, False, 0.16))
        k += 1
    peak = max(abs(v) for v in tr) or 1
    tr = [v / peak * 0.72 for v in tr]
    return loop_fade(tr, 0.6)


def music_sect(dur=26.0):
    """The sect's theme — tritone, chant, chains."""
    n = int(dur * SR)
    tr = [0.0] * n
    for i in range(n):
        t = i / SR
        tr[i] += 0.20 * math.sin(2 * math.pi * 55.0 * t)
        tr[i] += 0.10 * math.sin(2 * math.pi * 77.78 * t) * (1 + 0.2 * math.sin(2 * math.pi * 0.07 * t))
    # low chant (male choir-ish formants)
    chant_notes = [NAHAWAND[0], NAHAWAND[1], NAHAWAND[0], NAHAWAND[3]]
    for k, f in enumerate(chant_notes):
        at(tr, k * 5.0, ney(f / 2, 4.2, 0.22, vib=3.4))
        at(tr, k * 5.0 + 0.1, ney(f / 2 * 1.005, 4.0, 0.16, vib=3.0))
    for k in range(int(dur / 2.0)):
        at(tr, k * 2.0, darbuka(0.4, True, 0.24))
        if k % 4 == 2:
            at(tr, k * 2.0 + 0.5, darbuka(0.2, False, 0.14))
    peak = max(abs(v) for v in tr) or 1
    return loop_fade([v / peak * 0.66 for v in tr], 0.5)


def amb_rain(dur=8.0):
    n = int(dur * SR)
    rnd = random.Random(11)
    tr = [0.0] * n
    lp = 0.0
    for i in range(n):
        w = rnd.random() * 2 - 1
        lp = lp * 0.86 + w * 0.14          # low-passed rumble
        tr[i] = lp * 0.5 + w * 0.10
    # droplets
    for _ in range(int(dur * 40)):
        p = int(rnd.random() * (n - 200))
        f = rnd.uniform(900, 2600)
        for j in range(200):
            tr[p + j] += 0.10 * math.sin(2 * math.pi * f * j / SR) * math.exp(-j / 40)
    # distant thunder
    for tpos in (1.5, 5.4):
        p = int(tpos * SR)
        for j in range(int(1.4 * SR)):
            if p + j < n:
                tr[p + j] += 0.35 * (rnd.random() * 2 - 1) * math.exp(-j / (0.35 * SR))
    peak = max(abs(v) for v in tr) or 1
    return loop_fade([v / peak * 0.55 for v in tr], 0.5)


def amb_drone(dur=10.0, base=58.0, tense=0.0):
    n = int(dur * SR)
    tr = [0.0] * n
    for i in range(n):
        t = i / SR
        v = 0.5 * math.sin(2 * math.pi * base * t)
        v += 0.28 * math.sin(2 * math.pi * base * 1.5 * t)
        if tense:
            v += tense * 0.22 * math.sin(2 * math.pi * base * 1.414 * t)
        v += 0.10 * math.sin(2 * math.pi * base * 2.02 * t)
        v *= 1 + 0.12 * math.sin(2 * math.pi * 0.09 * t)
        tr[i] = v
    # creaks and drips
    rnd = random.Random(int(base))
    for _ in range(9):
        p = int(rnd.random() * (n - 4000))
        f = rnd.uniform(120, 400)
        for j in range(4000):
            tr[p + j] += 0.12 * math.sin(2 * math.pi * f * j / SR) * math.exp(-j / 900) * (rnd.random() * 0.4 + 0.8)
    peak = max(abs(v) for v in tr) or 1
    return loop_fade([v / peak * 0.5 for v in tr], 0.5)


def amb_souk(dur=9.0):
    """Medina murmur: filtered crowd noise + a far-off radio."""
    n = int(dur * SR)
    rnd = random.Random(21)
    tr = [0.0] * n
    lp = 0.0
    for i in range(n):
        w = rnd.random() * 2 - 1
        lp = lp * 0.95 + w * 0.05
        tr[i] = lp * 0.9 + w * 0.03
    for k in range(int(dur)):
        at(tr, k + rnd.random(), pluck(HIJAZ[rnd.randint(0, 6)] * 2, 0.9, 0.07, 0.4))
    peak = max(abs(v) for v in tr) or 1
    return loop_fade([v / peak * 0.45 for v in tr], 0.5)


# ---------------------------------------------------------------- sfx
def sfx_step(seed=0, surface="stone"):
    rnd = random.Random(seed)
    n = int(0.10 * SR)
    out = [0.0] * n
    for i in range(n):
        t = i / SR
        v = (rnd.random() * 2 - 1) * math.exp(-t * 55)
        if surface == "stone":
            v += 0.4 * math.sin(2 * math.pi * 130 * t) * math.exp(-t * 40)
        else:
            v += 0.3 * math.sin(2 * math.pi * 90 * t) * math.exp(-t * 30)
        out[i] = v * 0.45
    return out


def sfx_click():
    n = int(0.05 * SR)
    return [0.35 * math.sin(2 * math.pi * 1500 * i / SR) * math.exp(-i / 250) for i in range(n)]


def sfx_hover():
    n = int(0.04 * SR)
    return [0.18 * math.sin(2 * math.pi * 900 * i / SR) * math.exp(-i / 400) for i in range(n)]


def sfx_pickup():
    tr = [0.0] * int(0.7 * SR)
    at(tr, 0.0, pluck(HIJAZ[4] * 2, 0.5, 0.5, 0.8))
    at(tr, 0.12, pluck(HIJAZ[6] * 2, 0.5, 0.45, 0.8))
    at(tr, 0.24, pluck(HIJAZ[7] * 2, 0.5, 0.4, 0.85))
    return tr


def sfx_door():
    rnd = random.Random(5)
    n = int(1.3 * SR)
    out = [0.0] * n
    for i in range(n):
        t = i / SR
        f = 200 - 120 * min(1.0, t / 1.1)
        v = math.sin(2 * math.pi * f * t) * 0.3
        v += (rnd.random() * 2 - 1) * 0.12 * (1 - t / 1.3)
        out[i] = v * math.exp(-t * 1.2)
    for k in range(6):
        at(out, 0.7 + k * 0.08, [0.3 * math.exp(-j / 300) * math.sin(2 * math.pi * 800 * j / SR) for j in range(600)])
    return out


def sfx_fail():
    n = int(0.6 * SR)
    return [0.4 * math.sin(2 * math.pi * (300 - 180 * i / n) * i / SR) * math.exp(-i / (0.25 * SR)) for i in range(n)]


def sfx_sting():
    n = int(1.6 * SR)
    out = [0.0] * n
    rnd = random.Random(9)
    for i in range(n):
        t = i / SR
        v = math.sin(2 * math.pi * 880 * t) * math.exp(-t * 3)
        v += math.sin(2 * math.pi * 1245 * t) * math.exp(-t * 4) * 0.8   # tritone
        v += (rnd.random() * 2 - 1) * 0.25 * math.exp(-t * 8)
        out[i] = v * 0.4
    return out


def sfx_page():
    rnd = random.Random(13)
    n = int(0.4 * SR)
    return [(rnd.random() * 2 - 1) * math.exp(-i / (0.06 * SR)) * 0.28 for i in range(n)]


def sfx_chant_hit(ok=True):
    tr = [0.0] * int(0.5 * SR)
    if ok:
        at(tr, 0, pluck(HIJAZ[0], 0.4, 0.5, 0.9))
        at(tr, 0, darbuka(0.2, True, 0.4))
    else:
        at(tr, 0, sfx_fail())
    return tr


def sfx_heartbeat():
    n = int(1.2 * SR)
    out = [0.0] * n
    for pos, amp in ((0.0, 1.0), (0.28, 0.7)):
        p = int(pos * SR)
        for j in range(int(0.25 * SR)):
            if p + j < n:
                t = j / SR
                out[p + j] += amp * math.sin(2 * math.pi * 48 * t) * math.exp(-t * 22) * 0.6
    return out


def sfx_babouche():
    """The cursed slipper whispers."""
    tr = [0.0] * int(1.1 * SR)
    rnd = random.Random(31)
    for k in range(3):
        at(tr, k * 0.3, ney(220 * (1 + 0.1 * k), 0.5, 0.20, vib=8))
    for i in range(len(tr)):
        tr[i] += (rnd.random() - 0.5) * 0.05
    return tr


def sfx_win():
    tr = [0.0] * int(2.2 * SR)
    for k, d in enumerate((0, 2, 4, 6, 7)):
        at(tr, k * 0.18, pluck(HIJAZ[d] * 2, 1.4, 0.42, 0.75))
    at(tr, 0.9, qanun(HIJAZ[7] * 2, 1.2, 0.14))
    return tr


def sfx_lose():
    tr = [0.0] * int(2.6 * SR)
    for k, d in enumerate((4, 2, 1, 0)):
        at(tr, k * 0.35, pluck(NAHAWAND[d], 1.6, 0.4, 0.4))
    at(tr, 1.5, ney(NAHAWAND[0] / 2, 1.2, 0.2, vib=3))
    return tr


SFX = {
    "step_stone": lambda: sfx_step(1, "stone"),
    "step_wood":  lambda: sfx_step(2, "wood"),
    "step_sand":  lambda: sfx_step(3, "sand"),
    "click":      sfx_click,
    "hover":      sfx_hover,
    "pickup":     sfx_pickup,
    "door":       sfx_door,
    "fail":       sfx_fail,
    "sting":      sfx_sting,
    "page":       sfx_page,
    "chant_ok":   lambda: sfx_chant_hit(True),
    "chant_bad":  lambda: sfx_chant_hit(False),
    "heartbeat":  sfx_heartbeat,
    "babouche":   sfx_babouche,
    "win":        sfx_win,
    "lose":       sfx_lose,
}

AMBIENCE = {
    "amb_rain":  lambda: amb_rain(8.0),
    "amb_drone": lambda: amb_drone(10.0, 58.0, 0.0),
    "amb_tense": lambda: amb_drone(10.0, 46.0, 0.6),
    "amb_souk":  lambda: amb_souk(9.0),
}

MUSIC = {
    "music_menu": lambda: music_menu(30.0),
    "music_sect": lambda: music_sect(26.0),
}

if __name__ == "__main__":
    for name, fn in SFX.items():
        write_wav(f"sfx_{name}.wav", fn())
    for name, fn in AMBIENCE.items():
        write_wav(f"{name}.wav", fn())
    for name, fn in MUSIC.items():
        write_wav(f"{name}.wav", fn())
    print("done")
