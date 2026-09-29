"""gen_rooms — backgrounds for «البلغة والجن». 320x180 pixel-art rooms."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artlib import (Canvas, P, c, tile_noise, zellige_band, arch, lamp_light,
                    lantern, scanline_vignette, grain, quantize)

W, H = 320, 180
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art", "rooms")

FLOOR_Y = 128          # where the walkable floor starts
CEIL_Y = 26


# ------------------------------------------------------------------ shared
def back_wall(cv, top="dusk", bot="plum", seed=3):
    cv.grad_v(0, 0, W - 1, FLOOR_Y, top, bot)
    tile_noise(cv, 0, 0, W - 1, FLOOR_Y, "dusk", "plum", seed=seed, scale=5, thresh=0.45)
    cv.noise(0, 0, W - 1, FLOOR_Y, "ash", 0.05, 70, seed + 40)


def floor_band(cv, a="clay", b="terra", seed=9, plank=False):
    cv.grad_v(0, FLOOR_Y, W - 1, H - 1, a, "ink")
    if plank:
        for x in range(0, W, 11):
            cv.line(x, FLOOR_Y, x - 8, H - 1, "ink")
        for y in range(FLOOR_Y, H, 5):
            cv.line(0, y, W - 1, y, "clay")
    tile_noise(cv, 0, FLOOR_Y, W - 1, H - 1, a, b, seed=seed, scale=4, thresh=0.5)
    cv.dither(0, FLOOR_Y, W - 1, FLOOR_Y + 3, "shadow", 0.5, 190, seed=seed)
    for x in range(0, W, 13):
        cv.line(x, FLOOR_Y + 4, x - 6, H - 1, "shadow")


def hanging_cloth(cv, x, y, w, h, col="blood", col2="terra"):
    cv.rect(x, y, x + w, y + h, col)
    for i in range(0, h, 3):
        cv.dither(x, y + i, x + w, y + i + 1, col2, 0.5, 200, seed=i)
    for i in range(0, w, 6):
        cv.line(x + i, y, x + i, y + h, "clay")
    for i in range(w + 1):
        cv.px(x + i, y + h + (1 if (i // 3) % 2 else 0), "clay")


def rug(cv, x, y, w, h, cols=("blood", "gold", "azure", "cream")):
    cv.rect(x, y, x + w, y + h, cols[0])
    cv.rect(x + 1, y + 1, x + w - 1, y + h - 1, cols[1])
    cv.rect(x + 3, y + 2, x + w - 3, y + h - 2, cols[0])
    for i in range(x + 5, x + w - 4, 5):
        cv.line(i, y + 3, i, y + h - 3, cols[2])
    cv.rect(x + w // 2 - 4, y + h // 2 - 2, x + w // 2 + 4, y + h // 2 + 2, cols[3])
    cv.line(x, y, x + w, y, "ink")
    cv.line(x, y + h, x + w, y + h, "ink")


def window_rain(cv, x, y, w, h, bars=True):
    cv.rect(x, y, x + w, y + h, "ink")
    cv.grad_v(x + 1, y + 1, x + w - 1, y + h - 1, "azure", "void")
    for i in range(40):
        rnd = random.Random(i * 7 + x)
        rx = rnd.randint(x + 1, x + w - 2)
        ry = rnd.randint(y + 1, y + h - 6)
        cv.line(rx, ry, rx, ry + rnd.randint(2, 5), "majorelle")
    for i in range(14):
        rnd = random.Random(i * 31 + x)
        cv.px(rnd.randint(x + 1, x + w - 2), rnd.randint(y + 1, y + h - 2), "lamp")
    if bars:
        for bx in range(x + 3, x + w - 2, 5):
            cv.line(bx, y + 1, bx, y + h - 1, "ash")
    cv.outline(x, y, x + w, y + h, "brass")


def shelf_books(cv, x, y, w, h, seed=5):
    rnd = random.Random(seed)
    cols = ["blood", "azure", "gold", "teal", "terra", "plum", "brass", "red"]
    cv.rect(x, y, x + w, y + h, "clay")
    cv.outline(x, y, x + w, y + h, "ink")
    for sy in range(y + 2, y + h - 2, 12):
        cv.rect(x + 1, sy + 10, x + w - 1, sy + 11, "ink")
        bx = x + 2
        while bx < x + w - 3:
            bw = rnd.randint(2, 4)
            bh = rnd.randint(7, 10)
            col = rnd.choice(cols)
            cv.rect(bx, sy + 10 - bh, min(bx + bw, x + w - 2), sy + 9, col)
            cv.px(bx, sy + 10 - bh, "cream")
            bx += bw + 1


def crate(cv, x, y, w, h, col="clay", top="terra"):
    cv.rect(x, y, x + w, y + h, col)
    cv.rect(x, y, x + w, y + 2, top)
    cv.outline(x, y, x + w, y + h, "ink")
    cv.line(x, y, x + w, y + h, "shadow")
    cv.line(x + w, y, x, y + h, "shadow")


def pot_plant(cv, x, y, scale=1.0):
    cv.rect(x - 3, y, x + 3, y + 6, "terra")
    cv.rect(x - 4, y, x + 4, y + 1, "clay")
    for i, dx in enumerate((-5, -2, 1, 3, 5)):
        hh = int((6 + i % 3 * 3) * scale)
        cv.line(x + dx, y, x + dx + (1 if dx > 0 else -1), y - hh, "zellige")
        cv.line(x + dx + 1, y - hh, x + dx + 3, y - hh - 3, "teal")


def table(cv, x, y, w, h=3):
    cv.rect(x, y, x + w, y + h, "clay")
    cv.rect(x, y, x + w, y, "sand_lit")
    cv.line(x + 2, y + h, x + 2, y + h + 8, "clay")
    cv.line(x + w - 2, y + h, x + w - 2, y + h + 8, "clay")
    cv.outline(x, y, x + w, y + h, "ink")


# ------------------------------------------------------------------ rooms
def room_office():
    """مكتب المفتش — rain-lashed Casablanca office, 1994."""
    cv = Canvas(W, H)
    back_wall(cv, "shadow", "plum", seed=2)
    # back bookshelf wall
    shelf_books(cv, 6, 34, 78, 74, seed=4)
    shelf_books(cv, 92, 44, 52, 64, seed=9)
    # window with rain
    window_rain(cv, 176, 34, 62, 46)
    lamp_light(cv, 207, 60, 40, "majorelle")
    # filing cabinet
    cv.rect(246, 62, 292, 128, "clay")
    cv.outline(246, 62, 292, 128, "ink")
    for i, yy in enumerate(range(68, 122, 20)):
        cv.rect(250, yy, 288, yy + 16, "terra")
        cv.outline(250, yy, 288, yy + 16, "ink")
        cv.rect(264, yy + 7, 276, yy + 9, "brass")
        cv.px(286, yy + 8, "ink")
    # wanted posters / evidence board
    cv.rect(140, 40, 172, 66, "cream")
    cv.outline(140, 40, 172, 66, "ash")
    for i in range(6):
        cv.line(143, 46 + i * 3, 168 - (i * 2), 46 + i * 3, "ash")
    cv.px(156, 43, "red")
    cv.rect(146, 58, 166, 64, "terra")
    # desk
    table(cv, 20, 112, 96, 4)
    cv.rect(30, 96, 52, 111, "bone")          # papers
    cv.line(31, 100, 50, 100, "ash")
    cv.line(31, 104, 47, 104, "ash")
    cv.rect(58, 100, 68, 111, "brass")        # typewriter
    cv.rect(60, 96, 66, 100, "ash")
    cv.rect(74, 100, 80, 111, "blood")        # mug
    cv.px(77, 98, "ash")
    # chair
    cv.rect(120, 104, 132, 130, "plum")
    cv.rect(122, 96, 130, 106, "mauve")
    cv.line(124, 130, 124, 136, "clay")
    cv.line(129, 130, 129, 136, "clay")
    # floor + rug
    floor_band(cv, "clay", "terra", seed=11, plank=True)
    rug(cv, 150, 140, 120, 30)
    # wall lamp
    lantern(cv, 118, 44, hanging=0)
    # babouches by the door
    cv.paste_ascii("""
......####
.....######
.....##..##
.....##..##
""", 96, 120, {"#": "ochre"})
    cv.paste_ascii("""
.....####
....######
....##..##
....##..##
""", 104, 122, {"#": "gold"})
    # door on the right edge
    arch(cv, 300, 78, 24, 50, "clay", "void", "brass")
    scanline_vignette(cv, 0.12)
    grain(cv, 0.05, seed=21)
    return quantize(cv)


def room_alley():
    """زنقة المدينة القديمة — the old medina at 2am."""
    cv = Canvas(W, H)
    cv.grad_v(0, 0, W - 1, FLOOR_Y, "void", "dusk")
    # sky slot between buildings
    cv.rect(120, 0, 200, 34, "shadow")
    for i in range(26):
        rnd = random.Random(i * 13)
        cv.px(rnd.randint(121, 199), rnd.randint(1, 30), rnd.choice(("cream", "ash", "bone")))
    cv.blob(236, 20, 8, "bone")
    cv.glow(236, 20, 26, "cream", 0.4)
    # left building face
    cv.rect(0, 8, 108, FLOOR_Y + 30, "clay")
    tile_noise(cv, 0, 8, 108, FLOOR_Y + 30, "clay", "terra", seed=5, scale=6)
    # right building face
    cv.rect(212, 0, W - 1, FLOOR_Y + 30, "clay")
    tile_noise(cv, 212, 0, W - 1, FLOOR_Y + 30, "clay", "terra", seed=8, scale=6)
    # windows left
    for i, (wx, wy) in enumerate([(18, 30), (56, 30), (18, 62), (56, 62), (18, 94)]):
        cv.rect(wx, wy, wx + 22, wy + 20, "ink")
        cv.rect(wx + 2, wy + 2, wx + 20, wy + 18, "gold" if i % 2 else "azure")
        cv.outline(wx, wy, wx + 22, wy + 20, "brass")
        if i % 2 == 0:
            cv.rect(wx + 8, wy + 6, wx + 14, wy + 18, "shadow")
    # right windows
    for i, (wx, wy) in enumerate([(230, 26), (270, 26), (230, 60), (270, 60), (250, 96)]):
        cv.rect(wx, wy, wx + 24, wy + 22, "ink")
        cv.rect(wx + 2, wy + 2, wx + 22, wy + 20, "lamp" if i == 2 else "azure")
        cv.outline(wx, wy, wx + 24, wy + 22, "brass")
    # street floor — cobbles
    cv.grad_v(0, FLOOR_Y, W - 1, H - 1, "plum", "ink")
    for y in range(FLOOR_Y, H, 6):
        for x in range(0, W, 9):
            ox = (y // 6 % 2) * 4
            cv.rect(x + ox, y, x + ox + 7, y + 4, "dusk")
            cv.outline(x + ox, y, x + ox + 7, y + 4, "shadow")
    # puddle with lantern reflection
    cv.blob(160, 160, 22, "azure", 200, 0.35)
    cv.blob(160, 158, 14, "majorelle", 150, 0.35)
    # hanging lanterns across the alley
    for lx, ly in ((126, 42), (160, 36), (194, 42)):
        cv.line(0, 30, W - 1, 26, "ash")
        lantern(cv, lx, ly, hanging=6)
    # laundry lines
    cv.line(108, 60, 212, 54, "ash")
    hanging_cloth(cv, 116, 54, 12, 16, "blood", "terra")
    hanging_cloth(cv, 134, 52, 10, 14, "azure", "majorelle")
    hanging_cloth(cv, 150, 51, 13, 17, "cream", "sand")
    hanging_cloth(cv, 172, 50, 11, 15, "zellige", "teal")
    hanging_cloth(cv, 190, 50, 12, 16, "gold", "ochre")
    # doorway left
    arch(cv, 14, 70, 34, 60, "clay", "void", "brass")
    # a cat's eyes in the dark
    cv.px(146, 120, "lamp")
    cv.px(149, 120, "lamp")
    # crates + a dead plant
    crate(cv, 214, 138, 18, 16)
    crate(cv, 228, 132, 14, 22)
    pot_plant(cv, 250, 150, 1.1)
    # door to the souk (right edge)
    cv.rect(300, 74, W - 1, FLOOR_Y + 20, "ink")
    cv.line(302, 74, 302, FLOOR_Y + 20, "brass")
    scanline_vignette(cv, 0.14)
    grain(cv, 0.05, seed=33)
    return quantize(cv)


def room_souk():
    """دكان العطار — the herbalist's shop, jars and bones."""
    cv = Canvas(W, H)
    back_wall(cv, "shadow", "clay", seed=6)
    # shelving wall of jars
    for sy in (34, 62, 90):
        cv.rect(4, sy + 22, 200, sy + 24, "clay")
        cv.line(4, sy + 22, 200, sy + 22, "sand")
        jx = 10
        rnd = random.Random(sy)
        while jx < 194:
            jw = rnd.randint(7, 11)
            jh = rnd.randint(10, 16)
            col = rnd.choice(("zellige", "gold", "azure", "blood", "terra", "bone", "majorelle"))
            cv.rect(jx, sy + 22 - jh, jx + jw, sy + 21, col)
            cv.rect(jx + 1, sy + 22 - jh, jx + jw - 1, sy + 22 - jh + 2, "sand")
            cv.px(jx + jw // 2, sy + 26 - jh, "cream")
            cv.outline(jx, sy + 22 - jh, jx + jw, sy + 21, "ink")
            jx += jw + 3
    # hanging dried herbs from the ceiling
    for hx in range(20, 300, 22):
        rnd = random.Random(hx)
        hl = rnd.randint(10, 22)
        cv.line(hx, 0, hx, hl, "ash")
        for k in range(hl, hl + 8):
            cv.px(hx - 1, k, "teal")
            cv.px(hx + 1, k, "zellige")
            cv.px(hx, k, "teal")
        cv.blob(hx, hl + 10, 4, rnd.choice(("ochre", "blood", "gold", "teal")))
    # counter
    cv.rect(0, 108, 320, 128, "clay")
    cv.rect(0, 108, 320, 110, "sand_lit")
    cv.rect(0, 111, 320, 128, "terra")
    for x in range(0, 320, 16):
        cv.line(x, 111, x, 128, "clay")
    # apothecary props on the counter
    cv.rect(24, 96, 38, 108, "azure")       # big jar
    cv.rect(26, 92, 36, 97, "bone")
    cv.rect(48, 100, 58, 108, "gold")       # small jar
    cv.rect(70, 98, 78, 108, "blood")       # bottle
    cv.rect(72, 94, 76, 98, "bone")
    cv.rect(92, 102, 104, 108, "bone")      # mortar
    cv.rect(94, 100, 102, 103, "ash")
    cv.rect(120, 100, 134, 108, "plum")     # scale
    cv.line(127, 100, 127, 92, "brass")
    cv.line(120, 92, 134, 92, "brass")
    cv.rect(118, 90, 122, 93, "brass")
    cv.rect(132, 90, 136, 93, "brass")
    # skull + bones (the occult tell)
    cv.paste_ascii("""
..####..
.######.
##.##.##
##.##.##
.######.
..####..
""", 158, 96, {"#": "bone"})
    cv.px(160, 99, "void")
    cv.px(164, 99, "void")
    cv.line(176, 106, 190, 102, "bone")
    cv.line(180, 108, 194, 106, "bone")
    # floor
    floor_band(cv, "clay", "terra", seed=14)
    cv.rect(0, FLOOR_Y, W - 1, FLOOR_Y + 4, "shadow")
    # rug
    rug(cv, 60, 138, 190, 34, ("teal", "gold", "blood", "cream"))
    # a hanging censer smoking
    cv.line(268, 0, 268, 40, "ash")
    cv.rect(263, 40, 273, 50, "brass")
    cv.rect(264, 42, 272, 48, "lamp")
    lamp_light(cv, 268, 45, 34, "ochre")
    for i in range(30):
        rnd = random.Random(i * 5)
        cv.px(268 + rnd.randint(-6, 6), 30 + rnd.randint(0, 20), "ash", 60)
    scanline_vignette(cv, 0.13)
    grain(cv, 0.05, seed=44)
    return quantize(cv)


def room_riad():
    """الدار المهجورة — abandoned riad courtyard."""
    cv = Canvas(W, H)
    cv.grad_v(0, 0, W - 1, FLOOR_Y, "shadow", "dusk")
    # far courtyard wall with zellige band
    cv.rect(0, 20, W - 1, FLOOR_Y, "clay")
    tile_noise(cv, 0, 20, W - 1, FLOOR_Y, "clay", "terra", seed=17, scale=5)
    zellige_band(cv, 0, 96, W - 1, 110)
    # three horseshoe arches (arcade)
    arch(cv, 30, 44, 40, 56, "clay", "void", "brass")
    arch(cv, 140, 40, 44, 60, "clay", "void", "brass")
    arch(cv, 250, 44, 40, 56, "clay", "void", "brass")
    # broken frieze / calligraphy band
    cv.rect(0, 20, W - 1, 26, "azure")
    for x in range(2, W - 2, 6):
        cv.px(x, 23, "cream")
        cv.px(x + 2, 22, "gold")
        cv.px(x + 3, 24, "gold")
    # fountain in the middle
    cv.blob(160, 142, 30, "clay", 255, 0.42)
    cv.blob(160, 142, 26, "sand", 255, 0.42)
    cv.blob(160, 144, 20, "azure", 200, 0.42)
    cv.blob(160, 144, 12, "majorelle", 170, 0.42)
    cv.rect(156, 100, 164, 128, "sand")
    cv.blob(160, 100, 12, "sand_lit", 255, 0.5)
    cv.rect(158, 86, 162, 100, "sand")
    cv.blob(160, 88, 5, "bone")
    cv.glow(160, 120, 30, "azure", 0.35)
    # floor — courtyard tiles
    floor_band(cv, "plum", "dusk", seed=19)
    for y in range(FLOOR_Y, H, 8):
        for x in range(0, W, 16):
            cv.rect(x + (y // 8 % 2) * 8, y, x + 8 + (y // 8 % 2) * 8, y + 6, "dusk")
            cv.px(x + 4 + (y // 8 % 2) * 8, y + 3, "mauve")
    # overgrown plants
    pot_plant(cv, 40, 140, 1.6)
    pot_plant(cv, 58, 146, 1.2)
    pot_plant(cv, 262, 142, 1.5)
    pot_plant(cv, 282, 148, 1.1)
    # hanging vines
    for vx in (12, 76, 120, 208, 236, 300):
        rnd = random.Random(vx)
        for k in range(rnd.randint(14, 34)):
            cv.px(vx + int(math.sin(k * 0.4) * 2), k, "teal")
            if k % 3 == 0:
                cv.px(vx + int(math.sin(k * 0.4) * 2) + 1, k, "zellige")
    # lantern, half-dark
    lantern(cv, 110, 60, hanging=18)
    lantern(cv, 214, 56, hanging=14)
    cv.darken(0, 0, 30, FLOOR_Y, 0.35)
    cv.darken(W - 30, 0, W - 1, FLOOR_Y, 0.35)
    # open gate right (exit)
    cv.rect(302, 60, W - 1, FLOOR_Y + 26, "ink")
    cv.line(303, 60, 303, FLOOR_Y + 26, "brass")
    scanline_vignette(cv, 0.15)
    grain(cv, 0.06, seed=55)
    return quantize(cv)


def room_kitchen():
    """مطبخ الدار — the kitchen where the tagine is not for eating."""
    cv = Canvas(W, H)
    back_wall(cv, "shadow", "plum", seed=21)
    # tiled lower wall
    for y in range(74, FLOOR_Y, 10):
        for x in range(0, W, 12):
            cv.rect(x, y, x + 10, y + 8, "bone" if (x // 12 + y // 10) % 2 else "sand")
            cv.outline(x, y, x + 10, y + 8, "ash")
    cv.rect(0, 72, W - 1, 74, "clay")
    # hanging copper pots
    for px_, py_, r in ((40, 34, 8), (64, 30, 6), (86, 36, 9), (112, 32, 5)):
        cv.line(px_, 0, px_, py_ - r, "ash")
        cv.blob(px_, py_, r, "brass", 255, 0.85)
        cv.blob(px_ - 2, py_ - 2, r - 3, "ochre", 200, 0.85)
        cv.line(px_ + r, py_, px_ + r + 5, py_ - 3, "brass")
    # stove / kanoun with charcoal glow
    cv.rect(150, 92, 210, FLOOR_Y, "clay")
    cv.outline(150, 92, 210, FLOOR_Y, "ink")
    cv.rect(154, 100, 206, 118, "ink")
    for i in range(26):
        rnd = random.Random(i * 3)
        cv.blob(158 + rnd.randint(0, 44), 104 + rnd.randint(0, 10), rnd.randint(1, 3),
                rnd.choice(("red", "ochre", "lamp")))
    lamp_light(cv, 180, 108, 44, "red")
    # the tagine itself, centre stage
    cv.blob(180, 88, 22, "terra", 255, 0.42)
    cv.blob(180, 88, 19, "ochre", 255, 0.42)
    cv.blob(180, 84, 17, "clay", 255, 0.42)
    cv.blob(180, 82, 14, "sand_lit", 255, 0.42)
    cv.rect(179, 62, 181, 68, "clay")
    cv.blob(180, 61, 4, "gold")
    cv.glow(180, 80, 30, "red", 0.4)
    # hood above the tagine
    cv.rect(160, 44, 200, 62, "plum")
    cv.outline(160, 44, 200, 62, "ink")
    # table with knives and a jar of something dark
    table(cv, 20, 112, 108, 4)
    cv.rect(26, 98, 34, 112, "ash")          # blade
    cv.rect(26, 108, 40, 111, "clay")        # handle
    cv.rect(48, 100, 60, 112, "ink")         # dark jar
    cv.rect(50, 98, 58, 101, "bone")
    cv.px(54, 106, "red")
    cv.rect(70, 104, 84, 112, "blood")       # bowl
    cv.rect(72, 102, 82, 105, "red")
    cv.rect(96, 100, 116, 112, "bone")       # book
    cv.line(98, 104, 114, 104, "ash")
    cv.line(98, 108, 110, 108, "ash")
    # floor
    floor_band(cv, "clay", "terra", seed=23)
    cv.rect(0, FLOOR_Y, W - 1, FLOOR_Y + 3, "shadow")
    # door left (back to the courtyard)
    arch(cv, -6, 78, 34, 50, "clay", "void", "brass")
    # door right (to the stairs down)
    cv.rect(300, 74, W - 1, FLOOR_Y + 24, "ink")
    cv.line(302, 74, 302, FLOOR_Y + 24, "brass")
    scanline_vignette(cv, 0.14)
    grain(cv, 0.05, seed=66)
    return quantize(cv)


def room_cellar():
    """القبو — the cellar under the riad. The sect's kitchen."""
    cv = Canvas(W, H)
    cv.grad_v(0, 0, W - 1, FLOOR_Y, "void", "shadow")
    # rough stone blocks
    for y in range(0, FLOOR_Y, 12):
        for x in range(-6, W, 20):
            ox = (y // 12 % 2) * 10
            cv.rect(x + ox, y, x + ox + 18, y + 10, "plum")
            cv.outline(x + ox, y, x + ox + 18, y + 10, "ink")
            cv.dither(x + ox + 1, y + 1, x + ox + 17, y + 3, "mauve", 0.4, 150, seed=x + y)
    # zellige band, cracked
    zellige_band(cv, 0, 88, W - 1, 98, cols=("azure", "blood", "cream", "majorelle"))
    cv.rect(0, 88, W - 1, 90, "ink")
    # stone staircase down on the right
    for i in range(7):
        cv.rect(244 + i * 3, 118 - i * 9, 316, 126 - i * 9, "ash")
        cv.rect(244 + i * 3, 118 - i * 9, 316, 119 - i * 9, "bone")
        cv.outline(244 + i * 3, 118 - i * 9, 316, 126 - i * 9, "ink")
    # the big black tagine on a stone plinth
    cv.rect(120, 108, 196, FLOOR_Y, "ash")
    cv.outline(120, 108, 196, FLOOR_Y, "ink")
    cv.blob(158, 92, 30, "ink", 255, 0.45)
    cv.blob(158, 92, 26, "void", 255, 0.45)
    cv.blob(158, 84, 22, "shadow", 255, 0.45)
    cv.blob(158, 80, 16, "blood", 255, 0.42)
    cv.rect(157, 56, 159, 64, "shadow")
    cv.blob(158, 55, 5, "red")
    lamp_light(cv, 158, 76, 50, "red")
    # candles in a ring on the floor
    for ang in range(0, 360, 40):
        cx = 158 + int(math.cos(math.radians(ang)) * 66)
        cy = 148 + int(math.sin(math.radians(ang)) * 18)
        cv.rect(cx, cy - 6, cx + 1, cy, "bone")
        cv.px(cx, cy - 7, "lamp")
        cv.glow(cx, cy - 7, 12, "ochre", 0.6)
    # chalk sigil on the floor
    for ang in range(0, 360, 5):
        r = 40 + int(math.sin(math.radians(ang * 5)) * 6)
        cv.px(158 + int(math.cos(math.radians(ang)) * r), 156 + int(math.sin(math.radians(ang)) * r * 0.32), "blood")
    for ang in range(0, 360, 5):
        cv.px(158 + int(math.cos(math.radians(ang)) * 20), 156 + int(math.sin(math.radians(ang)) * 6), "bone")
    # shelves of skulls
    cv.rect(6, 40, 90, 44, "clay")
    for i, sx in enumerate(range(12, 84, 14)):
        cv.paste_ascii("""
.####.
######
##..##
######
.####.
""", sx, 30, {"#": "bone" if i % 2 else "cream"})
    # chains hanging
    for chx in (100, 210, 232):
        for k in range(0, 46, 4):
            cv.px(chx, 30 + k, "ash")
            cv.px(chx + 1, 32 + k, "ash")
    # floor
    floor_band(cv, "plum", "shadow", seed=27)
    cv.rect(0, FLOOR_Y, W - 1, FLOOR_Y + 4, "ink")
    scanline_vignette(cv, 0.22)
    grain(cv, 0.07, seed=77)
    return quantize(cv)


def room_rooftop():
    """السطح — Casablanca rooftops, the final confrontation."""
    cv = Canvas(W, H)
    # night sky
    cv.grad_v(0, 0, W - 1, 100, "void", "dusk")
    for i in range(70):
        rnd = random.Random(i * 17)
        cv.px(rnd.randint(0, W - 1), rnd.randint(0, 88), rnd.choice(("cream", "bone", "ash", "majorelle")))
    # moon
    cv.blob(58, 30, 13, "bone")
    cv.blob(52, 26, 13, (10, 9, 13, 255))
    cv.glow(60, 30, 34, "cream", 0.35)
    # distant skyline
    for i in range(30):
        rnd = random.Random(i * 29)
        bx = rnd.randint(0, W - 12)
        bw = rnd.randint(8, 20)
        bh = rnd.randint(14, 46)
        cv.rect(bx, 100 - bh, bx + bw, 100, "shadow")
        cv.outline(bx, 100 - bh, bx + bw, 100, "void")
        for wy in range(100 - bh + 4, 98, 7):
            for wx in range(bx + 3, bx + bw - 3, 5):
                if rnd.random() < 0.35:
                    cv.px(wx, wy, "lamp")
    # the roof deck
    cv.grad_v(0, 100, W - 1, H - 1, "plum", "ink")
    for y in range(100, H, 7):
        for x in range(0, W, 14):
            cv.rect(x + (y // 7 % 2) * 7, y, x + 7 + (y // 7 % 2) * 7, y + 5, "mauve")
            cv.outline(x + (y // 7 % 2) * 7, y, x + 7 + (y // 7 % 2) * 7, y + 5, "shadow")
    # parapet with zellige
    cv.rect(0, 96, W - 1, 106, "clay")
    zellige_band(cv, 0, 96, W - 1, 104, cols=("azure", "zellige", "cream", "majorelle"))
    # laundry lines and a water tank
    cv.line(0, 42, W - 1, 34, "ash")
    hanging_cloth(cv, 60, 34, 14, 20, "cream", "sand")
    hanging_cloth(cv, 84, 33, 12, 18, "azure", "majorelle")
    hanging_cloth(cv, 250, 32, 15, 22, "blood", "terra")
    cv.rect(196, 56, 226, 96, "plum")
    cv.rect(196, 56, 226, 58, "ash")
    cv.outline(196, 56, 226, 96, "ink")
    cv.line(200, 62, 222, 62, "shadow")
    # satellite dish
    for ang in range(0, 360, 6):
        cv.px(176 + int(math.cos(math.radians(ang)) * 12), 70 + int(math.sin(math.radians(ang)) * 12), "ash")
    cv.line(176, 70, 182, 78, "brass")
    # a single lantern on the parapet
    lantern(cv, 268, 88, hanging=0)
    # overturned chair + a spilled tagine (the sect left in a hurry)
    cv.rect(30, 130, 42, 140, "clay")
    cv.line(32, 140, 30, 152, "clay")
    cv.line(40, 140, 42, 152, "clay")
    cv.blob(104, 158, 16, "terra", 255, 0.42)
    cv.blob(104, 158, 12, "ochre", 255, 0.42)
    cv.blob(96, 164, 8, "blood", 190, 0.4)
    scanline_vignette(cv, 0.14)
    grain(cv, 0.05, seed=88)
    return quantize(cv)


def room_title():
    """Title card art — the black babouche, lit by one lamp."""
    cv = Canvas(W, H)
    cv.grad_v(0, 0, W - 1, H - 1, "void", "shadow")
    # radial lamp
    lamp_light(cv, 160, 96, 130, "ochre")
    cv.dither(0, 0, W - 1, H - 1, "plum", 0.35, 90, seed=5)
    # zellige floor band
    zellige_band(cv, 0, 150, W - 1, 178, cols=("azure", "blood", "cream", "majorelle"))
    cv.darken(0, 150, W - 1, H - 1, 0.45)
    # big centrepiece: a pair of black babouches on a brass tray
    cv.blob(160, 132, 60, "clay", 255, 0.22)
    cv.blob(160, 132, 54, "brass", 255, 0.22)
    cv.blob(160, 130, 48, "ochre", 255, 0.22)
    cv.paste_ascii("""
........###########.........
......###############.......
....###################.....
...#####################....
..#######################...
..########################..
..#########################.
..##########################
..##########################
..#########################.
..########################..
...#####################....
....###################.....
......###############.......
........###########.........
""", 96, 104, {"#": "ink"})
    # the pair
    cv.paste_ascii("""
....#########.........#########
...###########.......###########
..#############.....#############
..####.....####.....####.....####
..###..####..##.....###..####..##
..###.######.##.....###.######.##
..####....####......####....####.
...#########.........##########..
....#######...........########...
""", 118, 122, {"#": "void"})
    cv.paste_ascii("""
....#########.........#########
...###########.......###########
..#############.....#############
..####.....####.....####.....####
..###..####..##.....###..####..##
..###.######.##.....###.######.##
..####....####......####....####.
...#########.........##########..
....#######...........########...
""", 118, 122, {"#": "shadow"})
    # red glow in each toe (the eyes of the jinn)
    cv.blob(139, 130, 3, "red")
    cv.blob(178, 130, 3, "red")
    cv.glow(139, 130, 12, "red", 0.7)
    cv.glow(178, 130, 12, "red", 0.7)
    # smoke tendrils rising
    for i in range(160):
        rnd = random.Random(i * 13)
        sx = 120 + rnd.randint(0, 80)
        sy = 104 - rnd.randint(0, 60)
        cv.px(sx, sy, "plum", 70)
        cv.px(sx + 1, sy - 1, "mauve", 50)
    scanline_vignette(cv, 0.2)
    grain(cv, 0.06, seed=99)
    return quantize(cv)


ROOMS = {
    "office":   room_office,
    "alley":    room_alley,
    "souk":     room_souk,
    "riad":     room_riad,
    "kitchen":  room_kitchen,
    "cellar":   room_cellar,
    "rooftop":  room_rooftop,
    "title":    room_title,
}

if __name__ == "__main__":
    for name, fn in ROOMS.items():
        p = fn().save(os.path.join(OUT, f"{name}.png"))
        print("wrote", os.path.abspath(p))
