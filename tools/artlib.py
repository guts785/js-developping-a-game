"""artlib — pixel-art generation library for «البلغة والجن».
Everything is drawn at native pixel scale (320x180 rooms) with a locked
24-colour Moroccan-noir palette, then saved as PNG for Godot.
"""
from PIL import Image, ImageDraw, ImageFilter
import random, math, os

# ---------------------------------------------------------------- palette
P = {
    "ink":        (13, 11, 16),
    "void":       (10, 9, 13),
    "shadow":     (26, 21, 32),
    "dusk":       (43, 34, 51),
    "plum":       (61, 48, 64),
    "mauve":      (87, 69, 90),
    "ash":        (110, 90, 99),
    "dust":       (138, 111, 106),
    "sand":       (168, 135, 111),
    "sand_lit":   (201, 163, 122),
    "cream":      (242, 226, 196),
    "bone":       (232, 224, 208),
    "clay":       (107, 59, 42),
    "terra":      (143, 74, 47),
    "ochre":      (181, 101, 47),
    "gold":       (217, 155, 60),
    "lamp":       (242, 193, 78),
    "teal":       (47, 74, 63),
    "zellige":    (63, 107, 90),
    "azure":      (31, 95, 107),
    "majorelle":  (43, 122, 140),
    "blood":      (140, 47, 47),
    "red":        (192, 57, 43),
    "brass":      (150, 118, 66),
}

def c(name, a=255):
    r, g, b = P[name]
    return (r, g, b, a)

# ---------------------------------------------------------------- canvas
class Canvas:
    """Thin wrapper over an RGBA image with pixel-art helpers."""
    def __init__(self, w, h, bg="ink"):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w, h), c(bg) if isinstance(bg, str) else bg)
        self.d = ImageDraw.Draw(self.img)

    def px(self, x, y, col, a=255):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.img.putpixel((int(x), int(y)), c(col, a) if isinstance(col, str) else col)

    def rect(self, x0, y0, x1, y1, col, a=255):
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        self.d.rectangle([x0, y0, x1, y1], fill=c(col, a) if isinstance(col, str) else col)

    def line(self, x0, y0, x1, y1, col, a=255):
        self.d.line([x0, y0, x1, y1], fill=c(col, a) if isinstance(col, str) else col)

    def grad_v(self, x0, y0, x1, y1, top, bot):
        """Vertical gradient between two palette colours."""
        t, b = (P[top], P[bot]) if isinstance(top, str) else (top, bot)
        h = max(1, y1 - y0)
        for i, y in enumerate(range(y0, y1 + 1)):
            f = i / h
            col = (int(t[0] + (b[0] - t[0]) * f),
                   int(t[1] + (b[1] - t[1]) * f),
                   int(t[2] + (b[2] - t[2]) * f), 255)
            self.d.line([x0, y, x1, y], fill=col)

    def grad_h(self, x0, y0, x1, y1, left, right):
        l, r = (P[left], P[right]) if isinstance(left, str) else (left, right)
        w = max(1, x1 - x0)
        for i, x in enumerate(range(x0, x1 + 1)):
            f = i / w
            col = (int(l[0] + (r[0] - l[0]) * f),
                   int(l[1] + (r[1] - l[1]) * f),
                   int(l[2] + (r[2] - l[2]) * f), 255)
            self.d.line([x, y0, x, y1], fill=col)

    def dither(self, x0, y0, x1, y1, col, density=0.5, a=255, checker=True, seed=0):
        """Ordered/random dither fill — the shading workhorse."""
        rnd = random.Random(seed)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if checker:
                    on = ((x + y) % 2 == 0)
                else:
                    on = rnd.random() < density
                if on and rnd.random() < density + 0.35:
                    self.px(x, y, col, a)

    def noise(self, x0, y0, x1, y1, col, density=0.06, a=90, seed=1):
        rnd = random.Random(seed)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if rnd.random() < density:
                    self.px(x, y, col, a)

    def speck(self, x0, y0, x1, y1, cols, density=0.10, seed=1):
        rnd = random.Random(seed)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if rnd.random() < density:
                    self.px(x, y, rnd.choice(cols))

    def blob(self, cx, cy, r, col, a=255, squash=1.0):
        for y in range(int(cy - r * squash), int(cy + r * squash) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                if ((x - cx) ** 2 + ((y - cy) / squash) ** 2) <= r * r:
                    self.px(x, y, col, a)

    def glow(self, cx, cy, r, col, strength=0.75):
        """Radial additive-ish glow baked into the pixels, soft-dithered edge."""
        rnd = random.Random(int(cx) * 31 + int(cy))
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                d = math.hypot(x - cx, y - cy)
                if d > r or not (0 <= x < self.w and 0 <= y < self.h):
                    continue
                f = max(0.0, 1.0 - d / r) ** 2.4 * strength
                # soft dithered falloff so the halo doesn't read as a hard disc
                if d > r * 0.55 and rnd.random() > 1.0 - (d / r) * 0.85:
                    continue
                if f <= 0.02:
                    continue
                base = self.img.getpixel((int(x), int(y)))
                g = P[col] if isinstance(col, str) else col[:3]
                self.img.putpixel((int(x), int(y)), (
                    min(255, int(base[0] + g[0] * f)),
                    min(255, int(base[1] + g[1] * f)),
                    min(255, int(base[2] + g[2] * f)), 255))

    def darken(self, x0, y0, x1, y1, amount=0.35):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if 0 <= x < self.w and 0 <= y < self.h:
                    r, g, b, a = self.img.getpixel((x, y))
                    self.img.putpixel((x, y), (int(r * (1 - amount)), int(g * (1 - amount)),
                                               int(b * (1 - amount)), a))

    def outline(self, x0, y0, x1, y1, col="ink"):
        self.d.rectangle([x0, y0, x1, y1], outline=c(col))

    def paste_ascii(self, art, ox, oy, cmap, flip=False):
        """Stamp an ASCII-art sprite. cmap maps char -> palette key or RGBA."""
        rows = [r for r in art.strip("\n").split("\n")]
        for j, row in enumerate(rows):
            src = row[::-1] if flip else row
            for i, ch in enumerate(src):
                if ch == " " or ch == ".":
                    continue
                col = cmap.get(ch)
                if col is None:
                    continue
                self.px(ox + i, oy + j, col)

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.img.save(path)
        return path


def ascii_sprite(art, cmap):
    """Convert ASCII art to a standalone RGBA image."""
    rows = [r for r in art.strip("\n").split("\n")]
    w = max(len(r) for r in rows)
    h = len(rows)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in (" ", "."):
                continue
            col = cmap.get(ch)
            if col is None:
                continue
            img.putpixel((i, j), c(col) if isinstance(col, str) else col)
    return img


def tile_noise(cv, x0, y0, x1, y1, base_a, base_b, seed=3, scale=4, thresh=0.5):
    """Cheap value-noise mottling between two palette colours."""
    rnd = random.Random(seed)
    gw = (x1 - x0) // scale + 2
    gh = (y1 - y0) // scale + 2
    grid = [[rnd.random() for _ in range(gw)] for _ in range(gh)]
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            gx = (x - x0) // scale
            gy = (y - y0) // scale
            v = (grid[gy][gx] + grid[gy + 1][gx] + grid[gy][gx + 1] + grid[gy + 1][gx + 1]) / 4
            cv.px(x, y, base_a if v < thresh else base_b)


def zellige_band(cv, x0, y0, x1, y1, seed=7, cols=("azure", "zellige", "cream", "majorelle")):
    """Moroccan tile band — a real signature of the look."""
    w = x1 - x0
    step = 8
    for i, x in enumerate(range(x0, x1 + 1, step)):
        for j, y in enumerate(range(y0, y1 + 1, step)):
            col = cols[(i + j) % len(cols)]
            cv.rect(x, y, min(x + step - 2, x1), min(y + step - 2, y1), col)
            cv.rect(x + 1, y + 1, min(x + step - 3, x1), min(y + step - 3, y1), cols[(i + j + 2) % len(cols)])
            cv.px(x + step // 2, y + step // 2, "cream")
            cv.px(x + step // 2 - 1, y + step // 2, "cream")
            cv.px(x + step // 2 + 1, y + step // 2, "cream")
            cv.px(x + step // 2, y + step // 2 - 1, "cream")
            cv.px(x + step // 2, y + step // 2 + 1, "cream")


def arch(cv, x, y, w, h, col="clay", inner="void", trim="brass"):
    """Moroccan horseshoe arch — used on every doorway."""
    cv.rect(x, y + h // 3, x + w, y + h, col)
    r = w // 2
    cx = x + r
    cy = y + h // 3
    for yy in range(y, y + h // 3 + 1):
        for xx in range(x, x + w + 1):
            if math.hypot(xx - cx, yy - cy) <= r:
                cv.px(xx, yy, col)
    # inner void
    ir = r - 3
    for yy in range(y + 3, y + h // 3 + 1):
        for xx in range(x + 3, x + w - 2):
            if math.hypot(xx - cx, yy - cy) <= ir:
                cv.px(xx, yy, inner)
    cv.rect(x + 3, cy, x + w - 3, y + h, inner)
    # trim
    for t in range(2):
        for xx in range(x + 3, x + w - 2):
            if math.hypot(xx - cx, y + 3 + t - cy) <= ir + 1:
                cv.px(xx, y + 3 + t, trim)
    cv.line(x + 2, cy, x + 2, y + h, trim)
    cv.line(x + w - 2, cy, x + w - 2, y + h, trim)


def lamp_light(cv, cx, cy, r, col="lamp"):
    cv.glow(cx, cy, r, col, 0.85)
    cv.glow(cx, cy, int(r * 0.45), "cream", 0.7)


def lantern(cv, x, y, hanging=0, col="brass"):
    """Hanging brass lantern with a lit core."""
    if hanging:
        cv.line(x, y - hanging, x, y, "ash")
    cv.rect(x - 3, y, x + 3, y + 9, col)
    cv.rect(x - 2, y + 1, x + 2, y + 8, "lamp")
    cv.rect(x - 4, y - 1, x + 4, y, col)
    cv.rect(x - 4, y + 9, x + 4, y + 10, col)
    cv.px(x, y + 4, "cream")
    cv.px(x, y + 5, "cream")
    lamp_light(cv, x, y + 5, 26)


def scanline_vignette(cv, strength=0.16):
    """Bake a subtle CRT vignette so the pixel art reads retro."""
    w, h = cv.w, cv.h
    for y in range(h):
        for x in range(w):
            dx = (x - w / 2) / (w / 2)
            dy = (y - h / 2) / (h / 2)
            d = min(1.0, math.hypot(dx, dy) / 1.25)
            f = 1.0 - (d ** 2.2) * strength * 3.2
            if f < 1.0:
                r, g, b, a = cv.img.getpixel((x, y))
                cv.img.putpixel((x, y), (max(0, int(r * f)), max(0, int(g * f)),
                                         max(0, int(b * f)), a))


def grain(cv, amount=0.05, seed=11):
    rnd = random.Random(seed)
    for y in range(cv.h):
        for x in range(cv.w):
            if rnd.random() < amount:
                r, g, b, a = cv.img.getpixel((x, y))
                d = rnd.choice((-18, -10, 10, 16))
                cv.img.putpixel((x, y), (max(0, min(255, r + d)), max(0, min(255, g + d)),
                                         max(0, min(255, b + d)), a))


def quantize(cv, n=28):
    """Snap the whole frame to a tight indexed palette — the pixel-art tell."""
    img = cv.img.convert("RGB")
    q = img.quantize(colors=n, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
    out = q.convert("RGBA")
    cv.img = out
    return cv
