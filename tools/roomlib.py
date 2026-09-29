"""roomlib — reusable Moroccan interiors for «البلغة والجن», drawn at 640x360.

Every builder takes *world* coordinates (640x360). The room data in src/data/ is in
logical 320x180 space and gets doubled at load, so hotspot rects line up with the props
placed here — e.g. the office desk hotspot is logical [18,94,118,132] → world
[36,188,236,264], which is exactly where desk() draws.
"""
import math
import random
from pxlib import Cv, P, mix, rgb

W, H = 640, 360
FLOOR = 300          # default floor line (logical base_y 152 * 2)


# ====================================================================== walls
def plaster(cv, x0, y0, x1, y1, base="adobe", seed=1, damp=0.0):
    """Lime plaster wall: blotchy tone, hairline cracks, optional damp staining."""
    cv.rect(x0, y0, x1, y1, base)
    cv.noise(x0, y0, x1, y1, 0.10, seed=seed, scale=7, cols=("clay", "sand"))
    cv.noise(x0, y0, x1, y1, 0.07, seed=seed + 40, scale=17, cols=("terracotta", "cream"))
    rnd = random.Random(seed + 7)
    for _ in range(max(1, int((x1 - x0) / 90))):
        cv.cracks(rnd.randint(int(x0 + 6), int(x1 - 6)), rnd.randint(int(y0 + 4), int(y0 + 40)),
                  rnd.randint(14, 40), "clay", seed=rnd.randint(0, 999))
    if damp > 0.0:
        # rising damp at the bottom of the wall — a classic Casablanca interior
        cv.dither_grad_v(x0, y1 - 46, x1, y1, "teal_dark", 0.0, 0.34 * damp)
        cv.dither_grad_v(x0, y1 - 22, x1, y1, "umber", 0.0, 0.22 * damp)
    cv.ao(x0, y0, x1, y1, depth=5, amount=0.5)


def wainscot(cv, x0, y, x1, h=34, col="zellige", trim="brass_dark"):
    """Tiled dado along the bottom of a wall — very Moroccan, cheap detail."""
    cv.rect(x0, y, x1, y + h, col)
    for i in range(int(x0), int(x1), 16):
        cv.outline(i, y, i + 16, y + h, trim)
        cv.dither_rect(i + 2, y + 2, i + 14, y + h - 2, "cream", 0.16)
    cv.hline(x0, x1, y, "cream")
    cv.hline(x0, x1, y + h - 1, "ink")
    cv.ao(x0, y, x1, y + h, depth=3, amount=0.35)


def wood_panel(cv, x0, y0, x1, y1, col="brown", dark="umber", vertical=False, seed=2):
    """Planks with grain and a lit top edge."""
    cv.rect(x0, y0, x1, y1, col)
    step = 22
    if vertical:
        for x in range(int(x0), int(x1), step):
            cv.vline(x, y0, y1, dark)
            cv.vline(x + 1, y0, y1, mix(col, dark, 0.35))
    else:
        for y in range(int(y0), int(y1), step):
            cv.hline(x0, x1, y, dark)
            cv.hline(x0, x1, y + 1, mix(col, dark, 0.35))
    cv.noise(x0, y0, x1, y1, 0.10, seed=seed, scale=5, cols=(dark, "leather"))


def stone_block(cv, x0, y0, x1, y1, base="slate", seed=5):
    """Rough stone masonry for the cellar vault."""
    cv.rect(x0, y0, x1, y1, base)
    rnd = random.Random(seed)
    row_h = 26
    for ri, y in enumerate(range(int(y0), int(y1), row_h)):
        off = 0 if ri % 2 == 0 else 34
        for x in range(int(x0) - off, int(x1), 68):
            cv.outline(x, y, x + 68, y + row_h, "ink")
            cv.dither_rect(x + 1, y + 1, x + 67, y + 4, "slate_lit", 0.18)
            if rnd.random() < 0.5:
                cv.dither_rect(x + rnd.randint(2, 50), y + rnd.randint(4, 18),
                               x + rnd.randint(52, 66), y + rnd.randint(18, 24),
                               "teal_dark", 0.3)
    cv.noise(x0, y0, x1, y1, 0.10, seed=seed + 3, scale=6, cols=("ink", "slate_lit"))
    cv.ao(x0, y0, x1, y1, depth=8, amount=0.6)


# ====================================================================== floors
def tile_floor(cv, x0, y0, x1, y1, col="terracotta", grout="umber", cell=26, persp=True):
    """Square tile floor. Rows get taller toward the camera — cheap fake perspective."""
    cv.rect(x0, y0, x1, y1, col)
    y = float(y0)
    row = 0
    while y < y1:
        h = cell * (0.55 + 0.75 * ((y - y0) / max(1.0, y1 - y0))) if persp else cell
        step = cell * (0.7 + 0.6 * ((y - y0) / max(1.0, y1 - y0))) if persp else cell
        cv.hline(x0, x1, y, grout)
        off = (row % 2) * step * 0.5
        x = x0 - off
        while x < x1:
            cv.vline(x, y, y + h, grout)
            x += step
        # subtle sheen so the tiles read as fired clay, not flat blocks
        cv.dither_rect(x0, y + 1, x1, y + 3, "cream", 0.05)
        y += h
        row += 1
    cv.noise(x0, y0, x1, y1, 0.08, seed=11, scale=9, cols=("umber", "adobe"))
    cv.ao(x0, y0, x1, y0 + 10, depth=8, amount=0.5)


def zellige_floor(cv, x0, y0, x1, y1, seed=4):
    """Mosaic courtyard floor — the riad's signature."""
    cv.rect(x0, y0, x1, y1, "teal_dark")
    cols = ["zellige", "cream", "majorelle", "jade", "bone"]
    rnd = random.Random(seed)
    cell = 18
    for y in range(int(y0), int(y1), cell):
        for x in range(int(x0), int(x1), cell):
            c = cols[rnd.randrange(len(cols))]
            if rnd.random() < 0.55:
                cv.rect(x + 1, y + 1, x + cell - 1, y + cell - 1, c)
                cv.rect(x + 5, y + 5, x + cell - 5, y + cell - 5, "teal_dark")
            else:
                cv.rect(x + 1, y + 1, x + cell - 1, y + cell - 1, "cream")
                cv.rect(x + 4, y + 4, x + cell - 4, y + cell - 4, c)
    cv.noise(x0, y0, x1, y1, 0.10, seed=seed, scale=7, cols=("ink", "bone"))
    cv.ao(x0, y0, x1, y0 + 12, depth=9, amount=0.55)


def cobbles(cv, x0, y0, x1, y1, seed=6):
    """Worn street stones for the alley."""
    cv.rect(x0, y0, x1, y1, "slate")
    rnd = random.Random(seed)
    for _ in range(int((x1 - x0) * (y1 - y0) / 210)):
        cx = rnd.uniform(x0, x1)
        cy = rnd.uniform(y0, y1)
        r = rnd.uniform(4, 11)
        tone = rnd.choice(["slate", "slate_lit", "grey", "umber"])
        cv.ellipse(cx, cy, r, r * 0.6, tone)
        cv.dither_rect(cx - r, cy - r * 0.6, cx + r, cy - r * 0.3, "ink", 0.22)
    cv.noise(x0, y0, x1, y1, 0.10, seed=seed + 2, scale=5, cols=("ink", "slate_lit"))


def rug(cv, x0, y0, x1, y1, seed=8):
    """A zellige-patterned rug with a fringe — draws under the walk band."""
    cv.darken(x0 - 4, y0 - 3, x1 + 4, y1 + 4, 0.74)   # it lies ON the floor, so
    cv.rect(x0, y0, x1, y1, "red_dark")               # it needs an edge, not a lift
    cv.outline(x0, y0, x1, y1, "ink")
    cv.rect(x0 + 4, y0 + 4, x1 - 4, y1 - 4, "rust")
    cv.rect(x0 + 10, y0 + 10, x1 - 10, y1 - 10, "red_dark")
    cols = ["gold", "cream", "jade"]
    rnd = random.Random(seed)
    for y in range(int(y0 + 14), int(y1 - 14), 12):
        for x in range(int(x0 + 14), int(x1 - 14), 12):
            cv.rect(x, y, x + 7, y + 7, cols[rnd.randrange(3)])
    cv.outline(x0 + 10, y0 + 10, x1 - 10, y1 - 10, "gold")
    for x in range(int(x0) + 2, int(x1) - 2, 4):
        cv.vline(x, y1 - 3, y1, "bone")
        cv.vline(x, y0, y0 + 3, "bone")
    cv.noise(x0, y0, x1, y1, 0.10, seed=seed, scale=6, cols=("ink", "rust"))


# ====================================================================== structure
def contact_shadow(cv, cx, cy, rx, ry=None, amount=0.55):
    """A soft shadow where an object meets the floor. This is what stops props
    reading as stickers pasted onto a backdrop — without it nothing in the room
    is actually standing on anything."""
    cv.darken_ellipse(cx, cy, rx, ry if ry is not None else max(2.5, rx * 0.24), amount)


def _ground(cv, x0, x1, y, amount=0.5, spread=0.62, squash=0.22):
    """Contact shadow under a prop given its rect. Called at the top of the
    furniture builders so every piece grounds itself without the room having to
    remember to do it."""
    cx = (x0 + x1) / 2.0
    rx = max(6.0, (x1 - x0) * spread)
    contact_shadow(cv, cx, y, rx, max(2.5, rx * squash), amount)


def arch(cv, cx, y_top, y_bot, w, col="adobe", inner="ink", trim="brass_dark", horseshoe=True):
    """A Moorish arch. Interior stays dark so it reads as an opening."""
    hw = w / 2.0
    cv.rect(cx - hw, y_top + hw * 0.55, cx + hw, y_bot, col)
    cv.rect(cx - hw, y_top + hw * 0.55, cx + hw, y_bot, inner)
    # the arch itself
    for y in range(int(y_top), int(y_top + hw) + 1):
        t = (y - y_top) / max(1.0, hw)
        r = hw * math.sqrt(max(0.0, 1.0 - (1.0 - t) ** 2)) if t <= 1.0 else hw
        if horseshoe:
            r = hw * (1.0 + 0.12 * (1.0 - t))
        cv.rect(cx - r, y, cx + r, y + 1, inner)
    for y in range(int(y_top), int(y_bot)):
        t = (y - y_top) / max(1.0, hw)
        r = hw * math.sqrt(max(0.0, 1.0 - (1.0 - min(t, 1.0)) ** 2))
        if horseshoe:
            r = hw * (1.0 + 0.12 * (1.0 - min(t, 1.0)))
        cv.px(cx - r, y, trim)
        cv.px(cx - r - 1, y, col)
        cv.px(cx + r, y, trim)
        cv.px(cx + r + 1, y, col)
    # keystone + spandrel shading
    cv.rect(cx - 5, y_top - 3, cx + 5, y_top + 5, trim)
    cv.dither_rect(cx - hw - 6, y_top, cx + hw + 6, y_top + 8, "ink", 0.3)


def doorway(cv, x0, y0, x1, y1, col="brown", frame="brass_dark", open_dark=True):
    """A panelled door. If open_dark, the gap is black — an exit you can see."""
    cv.rect(x0, y0, x1, y1, "ink")
    if open_dark:
        cv.rect(x0 + 3, y0 + 3, x1 - 3, y1 - 3, "void")
        cv.dither_grad_v(x0 + 3, y0 + 3, x1 - 3, y1 - 3, "indigo", 0.35, 0.0)
    else:
        cv.rect(x0 + 3, y0 + 3, x1 - 3, y1 - 3, col)
        wood_panel(cv, x0 + 5, y0 + 6, x1 - 5, y1 - 6, col, "umber", vertical=True)
        cv.outline(x0 + 5, y0 + 6, x1 - 5, y1 - 6, "ink")
        cv.disc(x1 - 9, (y0 + y1) / 2, 2, "brass")
    cv.outline(x0, y0, x1, y1, frame)
    cv.rect(x0 - 2, y0 - 4, x1 + 2, y0, "clay")
    cv.ao(x0 - 3, y0, x1 + 3, y1, depth=6, amount=0.4)


def window_shaft(cv, x0, y0, x1, y1, drift=26.0, floor_y=FLOOR, amount=0.34, seed=1):
    """Mashrabiya window: lattice, sill, and the light it throws on the floor."""
    cv.rect(x0 - 3, y0 - 3, x1 + 3, y1 + 3, "clay")
    cv.rect(x0, y0, x1, y1, "indigo")
    cv.dither_grad_v(x0, y0, x1, y1, "sky_dust", 0.5, 0.12)
    # lattice
    for x in range(int(x0) + 4, int(x1) - 2, 9):
        cv.vline(x, y0 + 2, y1 - 2, "brass_dark")
    for y in range(int(y0) + 4, int(y1) - 2, 9):
        cv.hline(x0 + 2, x1 - 2, y, "brass_dark")
    cv.outline(x0, y0, x1, y1, "brass_dark")
    cv.rect(x0 - 6, y1, x1 + 6, y1 + 5, "clay")
    cv.dither_rect(x0 - 6, y1 + 5, x1 + 6, y1 + 8, "ink", 0.4)
    # the shaft lands on the floor
    cx = (x0 + x1) / 2.0
    cv.shaft(cx + drift * 0.4, y1, floor_y + 30, (x1 - x0) * 0.75, (x1 - x0) * 1.5,
             "lamp", amount=amount, drift=drift)


def hang_lamp(cv, cx, cy, r=11, chain=0):
    """Brass lantern on a chain with a warm pool under it."""
    if chain > 0:
        for y in range(int(cy - chain), int(cy)):
            cv.px(cx, y, "brass_dark")
    cv.poly([(cx, cy - r), (cx + r, cy + r * 0.2), (cx + r * 0.6, cy + r), (cx - r * 0.6, cy + r), (cx - r, cy + r * 0.2)], "brass")
    cv.poly([(cx, cy - r + 3), (cx + r * 0.6, cy + r * 0.2), (cx + r * 0.35, cy + r - 2), (cx - r * 0.35, cy + r - 2), (cx - r * 0.6, cy + r * 0.2)], "lamp")
    cv.disc(cx, cy + r * 0.35, max(2, r * 0.3), "flame")
    cv.vline(cx, cy - r, cy - r - 3, "brass_dark")
    cv.light_pool(cx, cy + r * 0.4, r * 3.4, "lamp", 0.5)


def cobweb(cv, x, y, size=26, flip_x=False, flip_y=False):
    sx = -1 if flip_x else 1
    sy = -1 if flip_y else 1
    for i in range(1, 5):
        r = size * i / 4.0
        for a in range(0, 91, 10):
            rad = math.radians(a)
            px = x + sx * math.cos(rad) * r
            py = y + sy * math.sin(rad) * r
            cv.dither(int(px), int(py), "bone", 0.4)
    for a in range(0, 91, 22):
        rad = math.radians(a)
        cv.line(x, y, x + sx * math.cos(rad) * size, y + sy * math.sin(rad) * size, "bone", 70)


# ====================================================================== furniture
def desk(cv, x0, y0, x1, y1):
    """Heavy administrative desk: top, apron, drawers, legs."""
    _ground(cv, x0, x1, y1, 0.52, 0.55)
    top = y0 + 6
    cv.rect(x0, top, x1, top + 8, "leather")
    cv.hline(x0, x1, top, "clay")
    cv.hline(x0, x1, top + 7, "umber")
    cv.rect(x0 + 6, top + 8, x1 - 6, y1 - 26, "brown")
    wood_panel(cv, x0 + 6, top + 8, x1 - 6, y1 - 26, "brown", "umber")
    # drawer stack
    cv.rect(x1 - 46, top + 12, x1 - 10, y1 - 30, "leather")
    for i in range(3):
        dy = top + 16 + i * 16
        cv.rect(x1 - 42, dy, x1 - 14, dy + 12, "brown")
        cv.disc(x1 - 28, dy + 6, 2, "brass")
    for lx in (x0 + 10, x1 - 14):
        cv.rect(lx, y1 - 26, lx + 5, y1, "umber")
    cv.ao(x0, top + 8, x1, y1, depth=4, amount=0.4)
    # papers + a lamp pool on the desk
    for i in range(5):
        px = x0 + 18 + i * 17
        cv.rect(px, top - 4, px + 14, top - 1, "cream")
        cv.dither_rect(px + 1, top - 4, px + 13, top - 3, "ink", 0.3)


def typewriter(cv, x, y):
    cv.rect(x, y + 6, x + 26, y + 20, "ink")
    cv.rect(x + 1, y + 7, x + 25, y + 14, "slate")
    cv.rect(x + 3, y - 2, x + 23, y + 6, "bone")
    for i in range(6):
        cv.vline(x + 5 + i * 3, y - 6, y - 2, "grey")
    cv.hline(x + 5, x + 21, y - 6, "brass_dark")
    for r in range(3):
        for c in range(8):
            cv.px(x + 3 + c * 2.6, y + 16 + r * 2, "grey")


def cabinet(cv, x0, y0, x1, y1):
    """Filing cabinet — the office's second silhouette."""
    _ground(cv, x0, x1, y1, 0.55, 0.58)
    cv.rect(x0, y0, x1, y1, "slate")
    cv.outline(x0, y0, x1, y1, "ink")
    for i in range(4):
        dy = y0 + 8 + i * 28
        cv.rect(x0 + 5, dy, x1 - 5, dy + 24, "slate_lit")
        cv.outline(x0 + 5, dy, x1 - 5, dy + 24, "ink")
        cv.dither_rect(x0 + 7, dy + 1, x1 - 7, dy + 4, "bone", 0.16)
        cv.rect((x0 + x1) / 2 - 8, dy + 11, (x0 + x1) / 2 + 8, dy + 14, "brass_dark")
    cv.dither_grad_h(x0, y0, x1, y1, "ink", 0.0, 0.3)
    cv.ao(x0, y0, x1, y0 + 8, depth=6, amount=0.5)


def shelf(cv, x0, y0, x1, y1, rows=3, items="jars"):
    """Shelf unit with rows of stuff. items: jars | herbs | books | skulls."""
    _ground(cv, x0, x1, y1, 0.5, 0.55)
    cv.rect(x0, y0, x1, y1, "brown")
    wood_panel(cv, x0, y0, x1, y1, "brown", "umber")
    cv.outline(x0, y0, x1, y1, "ink")
    rnd = random.Random(int(x0) + int(y0))
    row_h = (y1 - y0) / rows
    for r in range(rows):
        sy = y0 + r * row_h
        cv.rect(x0, sy + row_h - 5, x1, sy + row_h, "leather")
        cv.hline(x0, x1, sy + row_h - 5, "clay")
        cv.ao(x0, sy, x1, sy + row_h, depth=5, amount=0.5)
        x = x0 + 8
        while x < x1 - 14:
            if items == "jars":
                h = rnd.randint(14, 22)
                jar(cv, x, sy + row_h - 8 - h, 12, h, rnd.choice(["jade", "azure", "clay", "brass"]))
                x += 17
            elif items == "herbs":
                cv.poly([(x, sy + row_h - 8), (x + 7, sy + row_h - 8), (x + 10, sy + row_h - 8 - rnd.randint(10, 18)), (x - 3, sy + row_h - 8 - rnd.randint(8, 15))], "olive")
                cv.line(x + 3, sy + row_h - 8, x + 4, sy + row_h - 20, "moss")
                x += 16
            elif items == "books":
                w = rnd.randint(6, 12)
                cv.rect(x, sy + row_h - 8 - 18, x + w, sy + row_h - 8, rnd.choice(["rust", "teal_dark", "umber", "indigo"]))
                cv.vline(x + 1, sy + row_h - 24, sy + row_h - 9, "gold")
                x += w + 3
            else:
                skull(cv, x + 6, sy + row_h - 8, 8)
                x += 19


def jar(cv, x, y, w, h, col="jade"):
    cv.ellipse(x + w / 2, y + h * 0.62, w / 2, h * 0.38, col)
    cv.rect(x + w * 0.3, y, x + w * 0.7, y + h * 0.4, col)
    cv.rect(x + w * 0.24, y, x + w * 0.76, y + 3, mix(col, "ink", 0.3))
    cv.dither_rect(x + w * 0.2, y + h * 0.4, x + w * 0.4, y + h * 0.9, "cream", 0.2)
    cv.outline(x + w * 0.24, y, x + w * 0.76, y + h, "ink")


def table(cv, x0, y0, x1, y1, col="brown"):
    _ground(cv, x0, x1, y1, 0.46, 0.6)
    cv.rect(x0, y0, x1, y0 + 7, col)
    cv.hline(x0, x1, y0, "clay")
    cv.hline(x0, x1, y0 + 6, "umber")
    for lx in (x0 + 8, x1 - 12):
        cv.rect(lx, y0 + 7, lx + 5, y1, "umber")
    cv.rect(x0 + 8, y0 + 7, x1 - 12, y0 + 11, "umber")
    cv.ao(x0, y0, x1, y1, depth=3, amount=0.35)


def chair(cv, x, y, flip=False):
    s = -1 if flip else 1
    _ground(cv, x - 2, x + 26, y, 0.46, 0.6)
    cv.rect(x, y - 26, x + 4, y, "umber")
    cv.rect(x + 20, y - 30, x + 24, y, "umber")
    cv.rect(x, y - 30, x + 24, y - 26, "leather")
    cv.rect(x - 2, y - 14, x + 26, y - 10, "brown")
    cv.rect(x, y - 44, x + 24, y - 26, "brown")
    for i in range(3):
        cv.hline(x + 2, x + 22, y - 42 + i * 6, "umber")
    cv.ao(x - 2, y - 44, x + 26, y, depth=3, amount=0.3)


def crate(cv, x0, y0, x1, y1, seed=1):
    _ground(cv, x0, x1, y1, 0.5, 0.6)
    cv.rect(x0, y0, x1, y1, "leather")
    wood_panel(cv, x0, y0, x1, y1, "leather", "umber")
    cv.outline(x0, y0, x1, y1, "ink")
    cv.line(x0, y0, x1, y1, "umber", 90)
    cv.line(x1, y0, x0, y1, "umber", 90)
    cv.dither_rect(x0, y0, x1, y0 + 3, "sand", 0.25)
    cv.ao(x0, y0, x1, y1, depth=4, amount=0.4)


def counter(cv, x0, y0, x1, y1):
    """Shop counter — full width, wooden top, dark under."""
    _ground(cv, x0, x1, y1, 0.55, 0.6)
    cv.rect(x0, y0, x1, y0 + 10, "leather")
    cv.hline(x0, x1, y0, "clay")
    cv.hline(x0, x1, y0 + 9, "umber")
    cv.rect(x0, y0 + 10, x1, y1, "umber")
    wood_panel(cv, x0, y0 + 10, x1, y1, "umber", "ink", vertical=True)
    cv.ao(x0, y0 + 10, x1, y1, depth=6, amount=0.55)


def stove(cv, x0, y0, x1, y1):
    _ground(cv, x0, x1, y1, 0.6, 0.55)
    cv.rect(x0, y0, x1, y1, "ink")
    cv.outline(x0, y0, x1, y1, "slate")
    cv.rect(x0 + 6, y0 + 6, x1 - 6, y0 + 40, "void")
    cv.dither_grad_v(x0 + 6, y0 + 6, x1 - 6, y0 + 40, "ember", 0.55, 0.0)
    cv.dither_rect(x0 + 10, y0 + 26, x1 - 10, y0 + 38, "flame", 0.4)
    cv.rect(x0 + 10, y0 + 44, x1 - 10, y0 + 52, "slate")
    for i in range(4):
        cv.disc(x0 + 16 + i * 14, y0 + 48, 3, "brass_dark")
    cv.light_pool((x0 + x1) / 2, y0 + 30, 96, "ember", 0.42)
    cv.ao(x0, y0, x1, y1, depth=5, amount=0.5)


def tagine(cv, cx, cy, r=26, col="clay", black=False):
    """A tagine — cone lid over a round base. The game's central object."""
    contact_shadow(cv, cx, cy + r * 0.8, r * 1.15, r * 0.3, 0.5)
    base = "ink" if black else col
    lid = "void" if black else mix(col, "ink", 0.25)
    cv.ellipse(cx, cy + r * 0.55, r * 1.15, r * 0.35, base)
    cv.ellipse(cx, cy + r * 0.42, r * 1.05, r * 0.3, mix(base, "ink", 0.2) if black else mix(base, "ink", 0.3))
    cv.poly([(cx - r, cy + r * 0.45), (cx + r, cy + r * 0.45), (cx + r * 0.18, cy - r * 1.15), (cx - r * 0.18, cy - r * 1.15)], lid)
    # Rim light. The black tagine is `void` on a `void` plinth under a dark vault,
    # so without this its silhouette has no edge and the game's central object
    # reads as a hole in the picture. The lit variant only needs the soft sheen.
    cv.line(cx - r * 0.85, cy + r * 0.35, cx - r * 0.1, cy - r * 1.05,
            mix(lid, "lamp", 0.62 if black else 0.28))
    if black:
        cv.line(cx - r * 0.66, cy + r * 0.26, cx - r * 0.07, cy - r * 0.92,
                mix("ember", "lamp", 0.5))
        cv.hline(cx - r * 0.92, cx + r * 0.24, cy + r * 0.44, mix("ember", "lamp", 0.34))
    cv.disc(cx, cy - r * 1.2, 3, mix(lid, "lamp", 0.4))
    if black:
        cv.dither_rect(cx - r, cy - r, cx + r, cy + r, "indigo", 0.25)
        cv.dither_rect(cx - r * 0.5, cy - r * 1.1, cx + r * 0.5, cy - r * 0.3, "ember", 0.18)
    cv.outline(cx - r, cy + r * 0.2, cx + r, cy + r * 0.8, "ink")


def skull(cv, cx, cy, r=7):
    cv.ellipse(cx, cy, r, r * 0.9, "bone")
    cv.ellipse(cx, cy + r * 0.55, r * 0.6, r * 0.45, "bone")
    cv.rect(cx - r * 0.6, cy - r * 0.25, cx - r * 0.2, cy + r * 0.15, "void")
    cv.rect(cx + r * 0.2, cy - r * 0.25, cx + r * 0.6, cy + r * 0.15, "void")
    cv.dither_rect(cx - r * 0.3, cy + r * 0.5, cx + r * 0.3, cy + r * 0.9, "ink", 0.5)


def chain(cv, x0, y0, x1, y1, links=14):
    for i in range(links + 1):
        t = i / float(links)
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + 6 * math.sin(t * 6.0)
        cv.ring(x, y, 3, "slate_lit", 1, 200)
        cv.px(x, y, "ink")


def candle(cv, x, y, h=10):
    cv.rect(x - 1, y - h, x + 1, y, "bone")
    cv.dither_rect(x - 1, y - h, x + 1, y - h + 2, "ink", 0.3)
    cv.px(x, y - h - 1, "flame")
    cv.disc(x, y - h - 2, 1, "lamp")
    cv.light_pool(x, y - h, 26, "lamp", 0.4)


def plant(cv, x, y, h=40, spread=16, alive=True):
    """Potted plant. Dead ones are the riad's whole mood."""
    contact_shadow(cv, x, y, 17, 5, 0.46)
    cv.poly([(x - 11, y - 16), (x + 11, y - 16), (x + 8, y), (x - 8, y)], "clay")
    cv.rect(x - 12, y - 18, x + 12, y - 15, "terracotta")
    col = "olive" if alive else "umber"
    rnd = random.Random(int(x) + int(y))
    for i in range(7 if alive else 5):
        a = -math.pi / 2 + (i - 3) * (0.42 if alive else 0.3)
        ln = h * (0.6 + rnd.random() * 0.4)
        cv.line(x, y - 16, x + math.cos(a) * ln, y - 16 + math.sin(a) * ln, col)
        cv.line(x + 1, y - 16, x + 1 + math.cos(a) * ln, y - 16 + math.sin(a) * ln, mix(col, "ink", 0.3))
    if not alive:
        cv.dither_rect(x - 14, y - 40, x + 14, y - 14, "ink", 0.25)


def fountain(cv, cx, y_top, y_bot, r=40):
    """The riad's dry fountain — zellige rim, still water, brass spout."""
    contact_shadow(cv, cx, y_bot, r * 1.35, r * 0.36, 0.5)
    cv.ellipse(cx, y_bot, r * 1.25, r * 0.4, "clay")
    cv.ellipse(cx, y_bot - 6, r * 1.2, r * 0.36, "zellige")
    cv.ellipse(cx, y_bot - 10, r * 1.05, r * 0.3, "teal_dark")
    cv.ellipse(cx, y_bot - 10, r * 0.95, r * 0.26, "azure")
    cv.dither_rect(cx - r, y_bot - 14, cx + r, y_bot - 6, "sky_dust", 0.25)
    # basin wall + spout column
    cv.rect(cx - r * 0.5, y_top + 40, cx + r * 0.5, y_bot - 20, "clay")
    cv.dither_grad_h(cx - r * 0.5, y_top + 40, cx + r * 0.5, y_bot - 20, "ink", 0.35, 0.0)
    cv.rect(cx - r * 0.55, y_top + 34, cx + r * 0.55, y_top + 44, "zellige")
    cv.outline(cx - r * 0.5, y_top + 34, cx + r * 0.5, y_top + 44, "brass_dark")
    for i in range(3):
        cv.rect(cx - 3 + i * 3, y_top + 20, cx - 1 + i * 3, y_top + 36, "brass")
    cv.ao(cx - r, y_bot - 30, cx + r, y_bot, depth=6, amount=0.4)


def skyline(cv, x0, x1, y, seed=3):
    """Casablanca at night: rooftops, water tanks, dishes, lit windows."""
    rnd = random.Random(seed)
    cv.rect(x0, y - 90, x1, y + 20, "sky_night")
    cv.dither_grad_v(x0, y - 90, x1, y, "indigo", 0.5, 0.05)
    # moon
    cv.disc(x1 - 90, y - 74, 11, "bone")
    cv.dither_rect(x1 - 104, y - 88, x1 - 76, y - 60, "lamp", 0.14)
    x = x0
    while x < x1:
        bw = rnd.randint(34, 78)
        bh = rnd.randint(26, 72)
        top = y - bh
        cv.rect(x, top, x + bw, y + 10, "ink")
        cv.dither_grad_v(x, top, x + bw, y + 10, "indigo", 0.25, 0.0)
        cv.hline(x, x + bw, top, "slate")
        for wy in range(int(top) + 6, int(y), 13):
            for wx in range(int(x) + 5, int(x + bw) - 5, 12):
                if rnd.random() < 0.3:
                    cv.rect(wx, wy, wx + 5, wy + 7, rnd.choice(["lamp", "gold", "brass"]))
                else:
                    cv.rect(wx, wy, wx + 5, wy + 7, "void")
        if rnd.random() < 0.4:
            cv.rect(x + bw * 0.3, top - 9, x + bw * 0.3 + 12, top, "slate")
            cv.ellipse(x + bw * 0.3 + 6, top - 9, 6, 3, "grey")
        if rnd.random() < 0.3:
            cv.disc(x + bw * 0.7, top - 5, 5, "bone")
            cv.disc(x + bw * 0.7, top - 5, 2, "ink")
        x += bw + rnd.randint(3, 12)
    cv.hline(x0, x1, y + 10, "slate_lit")


def satellite(cv, x, y, r=7):
    cv.disc(x, y, r, "bone")
    cv.disc(x, y, r * 0.6, "grey")
    cv.line(x - r, y - r, x + r, y + r, "slate", 120)
    cv.vline(x, y + r, y + r + 6, "slate")


def laundry_line(cv, x0, x1, y, seed=5):
    """Clothes on a line — the alley's and the rooftop's signature."""
    rnd = random.Random(seed)
    cv.line(x0, y + 4, x1, y - 4, "slate", 170)
    x = x0 + 10
    cols = ["bone", "azure", "red", "jade", "cream", "zellige"]
    while x < x1 - 24:
        w = rnd.randint(18, 34)
        h = rnd.randint(24, 46)
        c = cols[rnd.randrange(len(cols))]
        cv.poly([(x, y + 2), (x + w, y + 2), (x + w - 2, y + h), (x + 2, y + h)], c)
        cv.dither_rect(x + 2, y + 2, x + w - 2, y + 8, "ink", 0.25)
        cv.dither_rect(x + 2, y + h - 8, x + w - 2, y + h, "ink", 0.2)
        x += w + rnd.randint(6, 18)


def cat(cv, x, y, sitting=True):
    cv.ellipse(x, y, 9, 6, "ink")
    if sitting:
        cv.ellipse(x + 6, y - 8, 5, 6, "ink")
        cv.poly([(x + 3, y - 13), (x + 5, y - 17), (x + 7, y - 13)], "ink")
        cv.poly([(x + 8, y - 13), (x + 10, y - 17), (x + 11, y - 12)], "ink")
    else:
        cv.ellipse(x + 10, y - 3, 5, 4, "ink")
        cv.poly([(x + 13, y - 7), (x + 15, y - 10), (x + 16, y - 6)], "ink")
    cv.px(x + 7, y - 9, "lamp")
    cv.px(x + 10, y - 9, "lamp")
    cv.line(x - 8, y - 2, x - 14, y - 8, "ink")


def puddle(cv, cx, cy, rx=28, ry=9):
    cv.ellipse(cx, cy, rx, ry, "teal_dark")
    cv.ellipse(cx, cy - 1, rx * 0.8, ry * 0.7, "teal")
    cv.dither_rect(cx - rx * 0.5, cy - ry, cx + rx * 0.5, cy, "sky_dust", 0.3)
    cv.dither_rect(cx - rx, cy + ry - 2, cx + rx, cy + ry + 1, "ink", 0.3)


def water_tank(cv, x0, y0, x1, y1):
    cv.rect(x0, y0 + 8, x1, y1, "slate")
    cv.ellipse((x0 + x1) / 2, y0 + 8, (x1 - x0) / 2, 6, "slate_lit")
    cv.rect(x0 + 4, y0, x1 - 4, y0 + 10, "grey")
    for i in range(3):
        cv.hline(x0, x1, y0 + 20 + i * 16, "ink")
    cv.dither_grad_h(x0, y0 + 8, x1, y1, "ink", 0.0, 0.35)
    cv.ao(x0, y0, x1, y1, depth=5, amount=0.45)


# ====================================================================== grading
def lighting(cv, lights, ambient=0.42):
    """The room's light model: fall into shadow, then be relit by its own sources.

    `lights` is a list of `(cx, cy, r, strength[, squash[, colour]])`. Called after
    the room is built and before `grade()`/`vignette()`, so the baked AO, every prop
    and the floor all take the same falloff.

    Why this exists: without it a room is authored at full brightness and then
    "lit" by dithering a warm colour on top, which can only raise an already-bright
    surface. The light was always in the file — it just had nothing to read
    against, so every room came out evenly lit and flat. Darkening first is what
    turns a colour into a light source.

    `ambient` is deliberately kept off the floor (~0.5-0.65) rather than pitched
    down like a night scene: the actor sprites are baked at full brightness and
    drawn over the room, so a room much darker than this makes the cast look
    pasted on.
    """
    cv.darken(0, 0, W, H, ambient)
    for L in lights:
        cx, cy, r, s = L[0], L[1], L[2], L[3]
        squash = L[4] if len(L) > 4 else 1.0
        col = L[5] if len(L) > 5 else "lamp"
        cv.glow(cx, cy, r, col, s, squash=squash)


def grade(cv, warm="lamp", cool="indigo", warm_amt=0.10, cool_amt=0.14, top=0.0, bottom=0.0):
    """Disabled: was the source of the room-wide speckle.

    It dithered a flat warm/cool tint across the whole canvas, twice, ignoring
    material and light entirely -- a uniform dot field over plaster, wood, glass
    and stone alike. That is what read as "a noise filter laid over everything"
    and made the rooms look like sandpaper while the flat-shaded characters read
    as stickers pasted onto it.

    `lighting()` now does this properly: it darkens the room first and then
    relights it from each room's own sources, so warmth and shadow come from
    geometry rather than from a tint applied over the top. Kept as a no-op so the
    existing call sites stay valid.
    """
    return


def vignette(cv, strength=0.5):
    """Corner falloff, dithered so it never bands.

    Falloff starts at 0.80 of the half-diagonal rather than 0.62, and callers pass
    ~0.22 rather than ~0.6. At the old values the bottom third of every room went to
    near-black: office.png measured 10/255 at y=300 where the tiles underneath are
    168. art/ui/vignette.png then stacks a second tube vignette on top at runtime, so
    the two together were turning the bottom of the frame into a letterbox -- which
    is exactly what it looked like.
    """
    cx, cy = W / 2.0, H / 2.0
    for y in range(H):
        for x in range(0, W, 2):
            d = math.hypot((x - cx) / cx, (y - cy) / cy)
            a = max(0.0, (d - 0.80)) * strength * 1.6
            if a > 0.02:
                cv.dither(x, y, "void", min(0.55, a))
                cv.dither(x + 1, y, "void", min(0.55, a))


def grain(cv, amount=0.05, seed=17):
    rnd = random.Random(seed)
    for _ in range(int(W * H * amount * 0.12)):
        x = rnd.randrange(W)
        y = rnd.randrange(H)
        cv.px(x, y, "bone" if rnd.random() < 0.5 else "ink", 26)


def dust(cv, count=70, seed=21):
    rnd = random.Random(seed)
    for _ in range(count):
        x = rnd.randrange(W)
        y = rnd.randrange(0, int(H * 0.8))
        cv.dither(x, y, "lamp", 0.6)
