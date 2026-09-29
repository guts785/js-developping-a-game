"""pxlib — pixel-art canvas + atmosphere toolkit for «البلغة والجن».

Stdlib only (zlib + struct). No PIL, no numpy.

The look this library aims at: hand-pixeled 2D with *painterly* light. The trick that
makes limited-palette pixel art feel atmospheric is ordered dithering — you fake a
gradient by checkerboarding two palette entries instead of blending them. Everything
here that would be "alpha" in a modern engine is a Bayer threshold instead, so the
result stays crisp pixel art at 1:1 and never turns into mush.
"""
import zlib
import struct
import math
import random

# ------------------------------------------------------------------ palette
# Moroccan noir: warm amber light against deep teal-indigo shadow, terracotta and
# brass in the middle. 40 entries, kept cohesive on purpose.
P = {
    # darks
    "void":      (10, 8, 14),
    "ink":       (18, 15, 24),
    # Warm outline ink, for the character rig only.
    #
    # `ink` is cold and blue-biased, which is right for room shadows but wrong for
    # a sprite outline: the rooms are built from warm darks (umber 58,40,30 / brown
    # 84,56,38), so a cast outlined in cold black reads as a sticker cut out and
    # laid on top -- "the characters' outlines are pure black; the background darks
    # are brown/gray, not pure black". Same value, warmed into the room's own dark
    # family, so the silhouette still reads but stops looking foreign.
    "outline":   (36, 23, 21),
    "night":     (24, 22, 36),
    "indigo":    (30, 32, 54),
    "teal_dark": (22, 42, 46),
    "teal":      (32, 58, 60),
    "slate":     (46, 52, 62),
    "slate_lit": (62, 70, 82),
    # earth
    "umber":     (58, 40, 30),
    "brown":     (84, 56, 38),
    "leather":   (110, 72, 46),
    "clay":      (138, 92, 60),
    "terracotta": (168, 106, 64),
    "adobe":     (196, 140, 92),
    "sand":      (214, 174, 122),
    "bone":      (232, 208, 166),
    "cream":     (244, 228, 196),
    # fire / brass
    "brass_dark": (122, 88, 34),
    "brass":     (176, 132, 48),
    "gold":      (214, 168, 68),
    "lamp":      (246, 206, 118),
    "flame":     (252, 228, 160),
    "ember":     (208, 108, 44),
    "rust":      (150, 62, 36),
    # cool accents
    "moss":      (72, 88, 52),
    "olive":     (104, 110, 62),
    "jade":      (74, 122, 96),
    "azure":     (58, 92, 132),
    "majorelle": (46, 62, 148),
    "zellige":   (72, 116, 148),
    "sky_night": (40, 48, 82),
    "sky_dust":  (72, 78, 108),
    # flesh / cloth
    "skin_dark": (104, 66, 44),
    "skin":      (156, 106, 70),
    "skin_lit":  (196, 148, 104),
    "red":       (152, 44, 40),
    "red_dark":  (104, 30, 32),
    "crimson":   (186, 58, 48),
    "white":     (250, 248, 240),
    "grey":      (128, 126, 122),
}

# 4x4 Bayer matrix, normalised to 0..15
BAYER = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
]


def bayer(x, y):
    return BAYER[y & 3][x & 3]


def rgb(name):
    if isinstance(name, tuple):
        return name
    return P[name]


def mix(a, b, t):
    """Linear colour mix — used for building palette ramps, not for shading pixels."""
    ca, cb = rgb(a), rgb(b)
    return tuple(int(round(ca[i] + (cb[i] - ca[i]) * t)) for i in range(3))


class Cv:
    """An RGBA pixel canvas. All drawing clips silently."""

    def __init__(self, w, h, bg: "str | None" = "void"):
        """bg="void" fills opaque (the common case). Pass bg=None for a canvas
        that starts fully transparent -- alpha here is write-once-max, so a
        transparent background can only be had by never writing one."""
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 4)
        if bg is not None:
            self.rect(0, 0, w, h, bg)

    # -------------------------------------------------------------- raw
    def px(self, x, y, c, a=255):
        x = int(x)
        y = int(y)
        if x < 0 or y < 0 or x >= self.w or y >= self.h:
            return
        i = (y * self.w + x) * 4
        r, g, b = rgb(c)
        if a >= 255:
            self.buf[i] = r
            self.buf[i + 1] = g
            self.buf[i + 2] = b
            self.buf[i + 3] = 255
        else:
            br, bg_, bb, ba = self.buf[i], self.buf[i + 1], self.buf[i + 2], self.buf[i + 3]
            f = a / 255.0
            self.buf[i] = int(br + (r - br) * f)
            self.buf[i + 1] = int(bg_ + (g - bg_) * f)
            self.buf[i + 2] = int(bb + (b - bb) * f)
            self.buf[i + 3] = max(ba, a)

    def get(self, x, y):
        if x < 0 or y < 0 or x >= self.w or y >= self.h:
            return (0, 0, 0, 0)
        i = (y * self.w + x) * 4
        return (self.buf[i], self.buf[i + 1], self.buf[i + 2], self.buf[i + 3])

    # -------------------------------------------------------------- dither
    def dither(self, x, y, c, amount):
        """Ordered-dither a colour in: amount 0..1. 1 = solid, 0 = nothing."""
        if amount <= 0.0:
            return
        if amount >= 1.0:
            self.px(x, y, c)
            return
        if bayer(x, y) / 16.0 < amount:
            self.px(x, y, c)

    def dither_rect(self, x0, y0, x1, y1, c, amount):
        x0, y0, x1, y1 = self._norm(x0, y0, x1, y1)
        for y in range(int(y0), int(y1)):
            for x in range(int(x0), int(x1)):
                self.dither(x, y, c, amount)

    def dither_grad_v(self, x0, y0, x1, y1, c, a0, a1):
        """Vertical dithered gradient of one colour — the workhorse for light falloff."""
        x0, y0, x1, y1 = self._norm(x0, y0, x1, y1)
        span = max(1.0, y1 - y0 - 1)
        for y in range(int(y0), int(y1)):
            t = (y - y0) / span
            self.dither_rect(x0, y, x1, y + 1, c, a0 + (a1 - a0) * t)

    def dither_grad_h(self, x0, y0, x1, y1, c, a0, a1):
        x0, y0, x1, y1 = self._norm(x0, y0, x1, y1)
        span = max(1.0, x1 - x0 - 1)
        for x in range(int(x0), int(x1)):
            t = (x - x0) / span
            for y in range(int(y0), int(y1)):
                self.dither(x, y, c, a0 + (a1 - a0) * t)

    def ramp_v(self, x0, y0, x1, y1, stops):
        """Vertical ramp through a list of (t, colour) stops, dithered between them."""
        x0, y0, x1, y1 = self._norm(x0, y0, x1, y1)
        span = max(1.0, y1 - y0 - 1)
        for y in range(int(y0), int(y1)):
            t = (y - y0) / span
            self._dither_band(x0, x1, y, stops, t)

    def _dither_band(self, x0, x1, y, stops, t):
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
                # draw the lower colour solid, then dither the upper one over it
                for x in range(int(x0), int(x1)):
                    self.px(x, y, c0)
                if f > 0.0:
                    for x in range(int(x0), int(x1)):
                        self.dither(x, y, c1, f)
                return
        for x in range(int(x0), int(x1)):
            self.px(x, y, stops[-1][1] if t > stops[-1][0] else stops[0][1])

    # -------------------------------------------------------------- shapes
    def rect(self, x0, y0, x1, y1, c, a=255):
        x0, y0, x1, y1 = self._norm(x0, y0, x1, y1)
        for y in range(int(y0), int(y1)):
            for x in range(int(x0), int(x1)):
                self.px(x, y, c, a)

    def outline(self, x0, y0, x1, y1, c):
        x0, y0, x1, y1 = self._norm(x0, y0, x1, y1)
        for x in range(int(x0), int(x1)):
            self.px(x, int(y0), c)
            self.px(x, int(y1) - 1, c)
        for y in range(int(y0), int(y1)):
            self.px(int(x0), y, c)
            self.px(int(x1) - 1, y, c)

    def hline(self, x0, x1, y, c, a=255):
        if x1 < x0:
            x0, x1 = x1, x0
        for x in range(int(x0), int(x1)):
            self.px(x, y, c, a)

    def vline(self, x, y0, y1, c, a=255):
        if y1 < y0:
            y0, y1 = y1, y0
        for y in range(int(y0), int(y1)):
            self.px(x, y, c, a)

    def line(self, x0, y0, x1, y1, c, a=255):
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.px(x0, y0, c, a)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c, a=255):
        rr = r * r
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= rr:
                    self.px(x, y, c, a)

    def ring(self, cx, cy, r, c, thick=1, a=255):
        ro = r * r
        ri = max(0.0, r - thick) ** 2
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                d = (x - cx) ** 2 + (y - cy) ** 2
                if ri <= d <= ro:
                    self.px(x, y, c, a)

    def ellipse(self, cx, cy, rx, ry, c, a=255):
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                if rx <= 0 or ry <= 0:
                    continue
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    self.px(x, y, c, a)

    def poly(self, pts, c, a=255):
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if y0 == y1:
                    continue
                if (y >= min(y0, y1)) and (y < max(y0, y1)):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + (x1 - x0) * t)
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(math.ceil(xs[i])), int(math.floor(xs[i + 1])) + 1):
                    self.px(x, y, c, a)

    # -------------------------------------------------------------- texture
    def noise(self, x0, y0, x1, y1, amount, seed=1, scale=3, cols=("ink", "slate")):
        """Blotchy value noise: two palette entries, smooth-ish clusters.

        Clamped. Callers used to pass 0.3-0.55, which speckled ~8.5% of every
        surface and read as a uniform noise filter over the whole room rather
        than as material. Dentures and Demons' rooms are flat fills with dither
        only where light changes; anything above ~0.035 stops reading as plaster
        or stone and starts reading as sandpaper.
        """
        amount = min(amount, 0.035)
        x0, y0, x1, y1 = self._norm(x0, y0, x1, y1)
        rnd = random.Random(seed)
        gw = int((x1 - x0) / scale) + 2
        gh = int((y1 - y0) / scale) + 2
        grid = [[rnd.random() for _ in range(gh)] for _ in range(gw)]

        def sample(gx, gy):
            x = gx / scale
            y = gy / scale
            ix, iy = int(x), int(y)
            fx, fy = x - ix, y - iy
            # smoothstep
            fx = fx * fx * (3 - 2 * fx)
            fy = fy * fy * (3 - 2 * fy)
            a = grid[min(ix, gw - 1)][min(iy, gh - 1)]
            b = grid[min(ix + 1, gw - 1)][min(iy, gh - 1)]
            c = grid[min(ix, gw - 1)][min(iy + 1, gh - 1)]
            d = grid[min(ix + 1, gw - 1)][min(iy + 1, gh - 1)]
            return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

        for y in range(int(y0), int(y1)):
            for x in range(int(x0), int(x1)):
                v = sample(x - x0, y - y0)
                if v > 1.0 - amount * 0.5:
                    self.dither(x, y, cols[1], 0.6)
                elif v < amount * 0.35:
                    self.dither(x, y, cols[0], 0.5)

    def speckle(self, x0, y0, x1, y1, c, count, seed=1, amount=0.7):
        x0, y0, x1, y1 = self._norm(x0, y0, x1, y1)
        rnd = random.Random(seed)
        for _ in range(count):
            self.dither(int(rnd.uniform(x0, x1)), int(rnd.uniform(y0, y1)), c, amount)

    def cracks(self, x, y, length, c, seed=1, spread=3):
        rnd = random.Random(seed)
        cx, cy = x, y
        for _ in range(length):
            self.px(cx, cy, c, 150)
            cx += rnd.choice([-1, 0, 1])
            cy += rnd.choice([0, 1, 1, 1])
            if rnd.random() < 0.12:
                cx += rnd.choice([-spread, spread])

    # -------------------------------------------------------------- light
    def light_pool(self, cx, cy, r, c="lamp", strength=0.55, squash=1.0):
        """Warm radial light with a dithered falloff — no hard edge anywhere."""
        r = float(r)
        for y in range(int(cy - r * squash), int(cy + r * squash) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                d = math.hypot(x - cx, (y - cy) / max(0.001, squash))
                if d > r:
                    continue
                t = 1.0 - d / r
                self.dither(x, y, c, (t * t) * strength)

    def darken(self, x0, y0, x1, y1, factor):
        """Multiply RGB by `factor`. The region falls into shadow.

        This is the primitive the whole lighting model was missing. Every other
        call in this library composites a colour *in*, which can only ever raise a
        surface toward the paint -- so a room built at full brightness and then
        dithered with warm light barely changes, and reads as flat. Light only
        reads against dark. Multiplicative falloff also preserves the hue ratios
        inside the region, so a shadowed blue tile stays blue-dark instead of
        turning into the same near-black as a shadowed red one.
        """
        x0, y0, x1, y1 = self._norm(x0, y0, x1, y1)
        f = max(0.0, min(1.0, float(factor)))
        for y in range(max(0, int(y0)), min(self.h, int(y1))):
            base = y * self.w * 4
            for x in range(max(0, int(x0)), min(self.w, int(x1))):
                i = base + x * 4
                self.buf[i] = int(self.buf[i] * f)
                self.buf[i + 1] = int(self.buf[i + 1] * f)
                self.buf[i + 2] = int(self.buf[i + 2] * f)

    def darken_ellipse(self, cx, cy, rx, ry, amount=0.55, falloff=1.6):
        """A soft elliptical shadow, multiplied down.

        `darken()` is rectangular, which is useless for grounding furniture. This
        is the contact-shadow primitive: because it multiplies rather than
        compositing black in, the shadow keeps the hue of whatever it lands on —
        a shadow over the terracotta tiles stays warm-dark instead of turning into
        the same flat void as a shadow over the blue wainscot.
        """
        rx = max(0.001, float(rx))
        ry = max(0.001, float(ry))
        for y in range(max(0, int(cy - ry)), min(self.h, int(cy + ry) + 1)):
            for x in range(max(0, int(cx - rx)), min(self.w, int(cx + rx) + 1)):
                d = math.hypot((x - cx) / rx, (y - cy) / ry)
                if d > 1.0:
                    continue
                f = 1.0 - amount * ((1.0 - d) ** falloff)
                i = (y * self.w + x) * 4
                self.buf[i] = int(self.buf[i] * f)
                self.buf[i + 1] = int(self.buf[i + 1] * f)
                self.buf[i + 2] = int(self.buf[i + 2] * f)

    def glow(self, cx, cy, r, c="lamp", strength=0.9, squash=1.0, ring=0.0):
        """Add light. Raises luminance toward `c` with a squared falloff.

        Deliberately *not* a dither: dithering a warm colour over a dark surface
        leaves half the pixels untouched, so the pool reads as speckle at 1x. A
        continuous lerp toward the light colour, then quantised by the caller's
        palette on save, is what makes it read as illumination. `squash` < 1
        gives a floor ellipse; `ring` skips the very centre so a lamp's own glass
        is not washed out by its own glow.
        """
        r = float(r)
        if r <= 0:
            return
        cr, cg, cb = rgb(c)
        for y in range(int(cy - r * squash), int(cy + r * squash) + 1):
            if y < 0 or y >= self.h:
                continue
            for x in range(int(cx - r), int(cx + r) + 1):
                if x < 0 or x >= self.w:
                    continue
                d = math.hypot(x - cx, (y - cy) / max(0.001, squash))
                if d > r or d < r * ring:
                    continue
                t = 1.0 - d / r
                a = (t * t) * strength
                i = (y * self.w + x) * 4
                self.buf[i] = min(255, int(self.buf[i] + (cr - self.buf[i]) * a))
                self.buf[i + 1] = min(255, int(self.buf[i + 1] + (cg - self.buf[i + 1]) * a))
                self.buf[i + 2] = min(255, int(self.buf[i + 2] + (cb - self.buf[i + 2]) * a))


    def shade(self, x0, y0, x1, y1, c="ink", amount=0.5, falloff="none"):
        """Darken a region. falloff: none | down | up | radial-free."""
        x0, y0, x1, y1 = self._norm(x0, y0, x1, y1)
        for y in range(int(y0), int(y1)):
            for x in range(int(x0), int(x1)):
                a = amount
                if falloff == "down":
                    a = amount * (1.0 - (y - y0) / max(1.0, y1 - y0))
                elif falloff == "up":
                    a = amount * ((y - y0) / max(1.0, y1 - y0))
                self.dither(x, y, c, a)

    def ao(self, x0, y0, x1, y1, depth=6, amount=0.55):
        """Ambient occlusion: a dithered dark band hugging the top edge of a region."""
        for i in range(depth):
            self.dither_rect(x0, y0 + i, x1, y0 + i + 1, "ink", amount * (1.0 - i / depth) ** 1.6)

    def ao_bottom(self, x0, y0, x1, y1, depth=6, amount=0.55):
        for i in range(depth):
            self.dither_rect(x0, y1 - i - 1, x1, y1 - i, "ink", amount * (1.0 - i / depth) ** 1.6)

    def shaft(self, x, y_top, y_bot, width_top, width_bot, c="lamp", amount=0.30, drift=0.0):
        """A light shaft through a window — a dithered parallelogram."""
        for y in range(int(y_top), int(y_bot)):
            t = (y - y_top) / max(1.0, y_bot - y_top)
            w = width_top + (width_bot - width_top) * t
            x0 = x + drift * t
            for xx in range(int(x0 - w / 2), int(x0 + w / 2)):
                self.dither(xx, y, c, amount * (1.0 - t * 0.55))

    def fog_band(self, x0, y0, x1, y1, c="sky_dust", amount=0.22, seed=3):
        """Ground haze: dithered, thinning toward the top of the band."""
        x0, y0, x1, y1 = self._norm(x0, y0, x1, y1)
        for y in range(int(y0), int(y1)):
            t = 1.0 - (y - y0) / max(1.0, y1 - y0)
            for x in range(int(x0), int(x1)):
                self.dither(x, y, c, amount * t)

    def motes(self, x0, y0, x1, y1, count=40, c="lamp", seed=9):
        x0, y0, x1, y1 = self._norm(x0, y0, x1, y1)
        rnd = random.Random(seed)
        for _ in range(count):
            self.dither(int(rnd.uniform(x0, x1)), int(rnd.uniform(y0, y1)), c, 0.75)

    # -------------------------------------------------------------- io
    def _norm(self, x0, y0, x1, y1):
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        return x0, y0, x1, y1

    def save(self, path):
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)  # filter type 0
            raw += self.buf[y * self.w * 4:(y + 1) * self.w * 4]
        comp = zlib.compress(bytes(raw), 9)

        def chunk(tag, data):
            c = struct.pack(">I", len(data)) + tag + data
            return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 6, 0, 0, 0))
        png += chunk(b"IDAT", comp)
        png += chunk(b"IEND", b"")
        with open(path, "wb") as f:
            f.write(png)
        return len(png)
