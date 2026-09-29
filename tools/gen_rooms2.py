"""gen_rooms2 — eight 640x360 rooms for «البلغة والجن».

Prop positions are pinned to the hotspot rects in src/data/rooms_*.gd (logical coords x2),
so what you click is what you see. Run:  python3 gen_rooms2.py
"""
import math
import random

from pxlib import Cv, P, mix
import roomlib as R
from roomlib import (W, H, plaster, wainscot, wood_panel, stone_block, tile_floor,
                     zellige_floor, cobbles, rug, arch, doorway, window_shaft, hang_lamp,
                     cobweb, desk, typewriter, cabinet, shelf, jar, table, chair, crate,
                     counter, stove, tagine, skull, chain, candle, plant, fountain,
                     skyline, satellite, laundry_line, cat, puddle, water_tank,
                     grade, lighting, contact_shadow, vignette, grain, dust)

OUT = "../art/rooms/"


def new(bg="ink"):
    cv = Cv(W, H)
    cv.rect(0, 0, W, H, bg)
    return cv


# ====================================================================== ch1 office
def office():
    """مكتب المفتش — a body in the ceiling, a desk, and too many files."""
    cv = new("void")
    FLOOR_Y = 304
    WALL_BOT = 236

    plaster(cv, 0, 0, W, WALL_BOT, "adobe", seed=3, damp=0.5)
    wainscot(cv, 0, WALL_BOT - 30, W, 30)
    # ceiling beam + the hole the body came through
    cv.rect(0, 0, W, 14, "umber")
    wood_panel(cv, 0, 0, W, 14, "umber", "ink")
    cv.ao(0, 0, W, 26, depth=10, amount=0.55)
    tile_floor(cv, 0, WALL_BOT, W, H, "terracotta", "umber", cell=30)

    # window (hotspot 344,60 → 484,168) — the only light in the room
    window_shaft(cv, 384, 62, 484, 166, drift=40, floor_y=FLOOR_Y, amount=0.30, seed=2)
    # dangling legs of the man in the ceiling (hotspot 280,36 → 400,140)
    cv.rect(298, 16, 366, 34, "void")
    cv.dither_rect(296, 14, 368, 38, "ink", 0.5)
    for lx in (312, 336):
        cv.rect(lx, 34, lx + 15, 96, "slate")
        cv.dither_grad_h(lx, 34, lx + 15, 96, "ink", 0.45, 0.05)
        cv.rect(lx, 34, lx + 15, 50, "bone")          # trouser cuff
        cv.outline(lx, 34, lx + 15, 96, "ink")
    cv.ellipse(319, 100, 9, 5, "leather")             # one shoe
    cv.ellipse(343, 100, 9, 5, "leather")
    cv.ellipse(319, 99, 9, 4, "brown")
    cv.ellipse(343, 99, 9, 4, "brown")

    # poster + the inspector's own diploma (hotspot 272,72 → 352,140)
    cv.rect(276, 76, 348, 138, "bone")
    cv.outline(276, 76, 348, 138, "brass_dark")
    cv.dither_rect(280, 80, 344, 96, "ink", 0.18)
    for i in range(4):
        cv.hline(284, 340, 100 + i * 6, "slate")
    cv.hline(284, 320, 126, "slate")
    cv.disc(312, 116, 12, "clay")
    cv.dither_rect(300, 104, 324, 128, "ink", 0.3)
    # lamp (hotspot 220,80 → 256,124)
    hang_lamp(cv, 238, 104, 13, chain=88)
    # desk (36,188 → 236,264) + typewriter (112,188 → 144,228)
    desk(cv, 36, 188, 236, 264)
    typewriter(cv, 116, 190)
    chair(cv, 250, 286, flip=True)
    # cabinet (488,120 → 588,256)
    cabinet(cv, 488, 120, 588, 256)
    # door out (592,148 → 638,304)
    doorway(cv, 592, 148, 638, 304, "brown", "brass_dark", open_dark=False)
    # rug (296,272 → 544,344)
    rug(cv, 296, 272, 544, 344)
    # the black babouche on the floor (176,236 → 236,268)
    for i, (bx, by) in enumerate(((188, 250), (212, 254))):
        cv.ellipse(bx, by, 12, 7, "void")
        cv.ellipse(bx, by - 2, 11, 5, "ink")
        cv.dither_rect(bx - 11, by - 5, bx + 11, by + 2, "slate", 0.18)
        cv.outline(bx - 12, by - 7, bx + 12, by + 7, "slate")
        cv.ellipse(bx + 8, by - 4, 5, 4, "void")
    cv.dither_rect(180, 244, 232, 264, "indigo", 0.22)
    cobweb(cv, 0, 0, 30)
    cobweb(cv, W, 0, 26, flip_x=True)
    dust(cv, 90, seed=4)
    lighting(cv, [
        (238, 108, 108, 0.92),               # the inspector's hanging lamp
        (434, 118, 150, 1.00),               # the window -- the room's key light.
                                             # Measured before this: the panes came
                                             # out at lum 115 against the wall's 116,
                                             # i.e. the window was exactly as bright
                                             # as the wall it was set into and read as
                                             # a dead rectangle. It has to out-bright
                                             # its own surround to read as a source.
        (462, 296, 168, 0.72, 0.30),         # and the shaft it throws on the tiles
        (600, 250, 96, 0.34),                # a little bounce off the door reveal
    ], ambient=0.56)
    grade(cv, "lamp", "indigo", 0.12, 0.16, top=0, bottom=WALL_BOT + 60)
    vignette(cv, 0.22)
    grain(cv, 0.015)
    return cv


# ====================================================================== ch2 alley
def alley():
    """زنقة الحبوس — laundry overhead, a cat, a puddle that is not water."""
    cv = new("void")
    FLOOR_Y = 304
    WALL_BOT = 252

    plaster(cv, 0, 0, 120, WALL_BOT, "clay", seed=11, damp=0.7)
    plaster(cv, 520, 0, W, WALL_BOT, "clay", seed=12, damp=0.7)
    # the far wall between the two buildings, deep in shadow
    plaster(cv, 120, 0, 520, 120, "umber", seed=13, damp=0.3)
    cv.dither_grad_v(120, 0, 520, 120, "void", 0.45, 0.15)
    # the old door the Brothers use (24,132 → 104,268)
    doorway(cv, 24, 132, 104, 268, "umber", "ink", open_dark=True)
    cv.rect(30, 140, 98, 260, "void")
    cv.dither_rect(30, 140, 98, 260, "indigo", 0.3)
    for i in range(4):
        cv.hline(34, 94, 150 + i * 28, "umber")
    cv.disc(88, 210, 3, "brass_dark")
    # arch over the alley mouth
    arch(cv, 320, 46, 252, 200, "clay", "void", "umber", horseshoe=True)
    cv.rect(220, 130, 420, 252, "void")
    cv.dither_grad_v(220, 130, 420, 252, "indigo", 0.42, 0.1)
    # hanging lanterns (236,64 → 400,124)
    for i, (lx, ly) in enumerate(((252, 92), (300, 78), (352, 96), (386, 86))):
        hang_lamp(cv, lx, ly, 9, chain=40 + (i % 2) * 26)
    # laundry across the alley (220,96 → 410,152)
    laundry_line(cv, 210, 420, 110, seed=9)
    # cobbled ground (120,320 → 600,356)
    cobbles(cv, 0, WALL_BOT, W, H, seed=6)
    cv.dither_grad_v(0, WALL_BOT, W, WALL_BOT + 40, "ink", 0.5, 0.0)
    # crates (420,256 → 492,316)
    crate(cv, 420, 258, 462, 300, seed=2)
    crate(cv, 452, 272, 492, 316, seed=3)
    crate(cv, 428, 232, 456, 262, seed=4)
    # puddle (272,296 → 372,344)
    puddle(cv, 322, 318, 48, 15)
    cv.dither_rect(274, 296, 370, 344, "teal", 0.12)
    # the cat (284,228 → 312,256)
    cat(cv, 292, 244, sitting=True)
    cv.dither_rect(278, 240, 314, 252, "ink", 0.2)
    # a drain, some weeds, wet walls
    cv.rect(500, 300, 540, 316, "void")
    for i in range(5):
        cv.vline(504 + i * 8, 300, 316, "slate")
    for i in range(9):
        wx = 150 + i * 26
        cv.line(wx, WALL_BOT, wx + 3, WALL_BOT - 14, "moss")
    cobweb(cv, 120, 0, 34)
    dust(cv, 60, seed=8)
    lighting(cv, [
        (252, 94, 88, 0.85), (300, 80, 88, 0.85),      # the four lanterns down
        (352, 98, 88, 0.85), (386, 88, 88, 0.85),      # the alley
        (320, 250, 220, 0.34, 0.5, "indigo"),          # cold light from the arch
    ], ambient=0.52)
    grade(cv, "lamp", "indigo", 0.14, 0.22, top=0, bottom=WALL_BOT + 80)
    vignette(cv, 0.24)
    grain(cv, 0.015)
    return cv


# ====================================================================== ch3 souk
def souk():
    """دكان العطّار — a counter of jars, a skull, and a woman who knows your mother."""
    cv = new("void")
    WALL_BOT = 176
    FLOOR_Y = 304

    plaster(cv, 0, 0, W, WALL_BOT, "adobe", seed=21, damp=0.35)
    cv.rect(0, 0, W, 18, "umber")
    wood_panel(cv, 0, 0, W, 18, "umber", "ink")
    # back shelving (0,56 → 400,180)
    shelf(cv, 0, 56, 400, 178, rows=3, items="jars")
    shelf(cv, 404, 62, 500, 178, rows=2, items="herbs")
    # hanging censer (512,72 → 568,120)
    for y in range(0, 78):
        cv.px(540, y, "brass_dark")
    cv.poly([(540, 76), (554, 92), (548, 108), (532, 108), (526, 92)], "brass")
    cv.dither_rect(530, 84, 550, 106, "ember", 0.4)
    cv.disc(540, 96, 4, "flame")
    cv.light_pool(540, 96, 60, "ember", 0.35)
    cv.dither_rect(524, 108, 556, 124, "ink", 0.3)
    # hanging herb bundles over the counter
    for i, bx in enumerate((430, 456, 478, 500)):
        cv.line(bx, 0, bx, 40 + i * 6, "slate", 150)
        cv.poly([(bx - 7, 40 + i * 6), (bx + 7, 40 + i * 6), (bx + 4, 72 + i * 6), (bx - 4, 72 + i * 6)], "olive")
    # counter (0,180 → 640,260)
    counter(cv, 0, 180, W, 260)
    # jars on the counter (32,176 → 120,224)
    for i, jx in enumerate((30, 58, 86)):
        jar(cv, jx, 176, 22, 44, ("jade", "azure", "clay")[i])
    # herbs bundle on the counter (172,192 → 216,228)
    cv.poly([(170, 224), (214, 224), (206, 194), (178, 190)], "olive")
    cv.line(176, 222, 200, 196, "moss")
    cv.line(188, 224, 206, 200, "olive")
    cv.rect(168, 222, 216, 228, "leather")
    # the skull on the counter (304,184 → 396,224)
    skull(cv, 336, 204, 17)
    cv.dither_rect(304, 190, 380, 224, "ink", 0.25)
    cv.ellipse(336, 222, 20, 5, "ink")
    # scales + a brass tray
    cv.vline(420, 168, 200, "brass_dark")
    cv.hline(400, 440, 168, "brass")
    cv.disc(402, 176, 6, "brass")
    cv.disc(438, 176, 6, "brass")
    cv.ellipse(470, 176, 16, 5, "brass")
    # back door (584,200 → 638,304)
    doorway(cv, 584, 200, 638, 304, "umber", "brass_dark", open_dark=True)
    cv.dither_rect(586, 202, 636, 302, "indigo", 0.35)
    tile_floor(cv, 0, 260, W, H, "clay", "umber", cell=30)
    cv.dither_grad_v(0, 260, W, 300, "ink", 0.4, 0.0)
    cobweb(cv, W, 0, 30, flip_x=True)
    dust(cv, 70, seed=22)
    lighting(cv, [
        (540, 98, 136, 0.95, 1.0, "ember"),            # the brazier under the awning
        (300, 300, 210, 0.24, 0.4),                    # bounce off the street stones
    ], ambient=0.56)
    grade(cv, "lamp", "indigo", 0.16, 0.18, top=0, bottom=300)
    vignette(cv, 0.22)
    grain(cv, 0.015)
    return cv


# ====================================================================== ch4 riad
def riad():
    """الدار الخالية — three arches, a dry fountain, and a wall that watches."""
    cv = new("void")
    WALL_BOT = 212
    FLOOR_Y = 304

    plaster(cv, 0, 0, W, WALL_BOT, "adobe", seed=31, damp=0.6)
    # vines along the top (0,0 → 640,80)
    for i in range(70):
        vx = random.Random(i * 7).randrange(0, W)
        vy = random.Random(i * 13).randrange(0, 76)
        cv.line(vx, 0, vx + random.Random(i).randint(-8, 8), vy, "olive")
        cv.disc(vx + 2, vy, random.Random(i * 3).randint(2, 4), "moss")
    cv.dither_rect(0, 0, W, 60, "ink", 0.3)
    # three horseshoe arches (56,80→144,208) (272,72→372,208) (496,80→584,208)
    for ax, aw in ((100, 88), (322, 100), (540, 88)):
        arch(cv, ax, 80, WALL_BOT, aw, "clay", "void", "brass_dark")
        cv.dither_rect(ax - aw / 2 + 4, 92, ax + aw / 2 - 4, WALL_BOT, "indigo", 0.4)
    # sigil wall — the plaster that answers (392,56 → 492,192)
    cv.dither_rect(392, 56, 492, 192, "umber", 0.3)
    cv.outline(392, 56, 492, 192, "clay")
    cv.dither_rect(392, 56, 492, 192, "crimson", 0.14)
    for i, r in enumerate((26, 44, 62)):
        cv.ring(442, 122, r, "red", 2, 190)
        cv.ellipse(442, 122, r, r * 0.34, "red", 150)
    cv.ring(442, 122, 8, "crimson", 3, 230)
    for a in range(0, 360, 30):
        rad = math.radians(a)
        cv.line(442 + math.cos(rad) * 10, 122 + math.sin(rad) * 4,
                442 + math.cos(rad) * 60, 122 + math.sin(rad) * 21, "crimson", 170)
    cv.line(442, 60, 442, 184, "red", 130)
    cv.line(396, 122, 488, 122, "red", 130)
    cv.dither_rect(408, 88, 476, 156, "crimson", 0.16)
    cv.ao(392, 56, 492, 192, depth=8, amount=0.45)
    # lantern (200,104 → 244,156)
    hang_lamp(cv, 222, 128, 13, chain=64)
    # fountain (260,192 → 380,336)
    zellige_floor(cv, 0, WALL_BOT, W, H, seed=4)
    cv.dither_grad_v(0, WALL_BOT, W, WALL_BOT + 30, "ink", 0.45, 0.0)
    fountain(cv, 320, 196, 336, r=48)
    # plants (60,260 → 140,340)
    plant(cv, 96, 336, 54, alive=True)
    plant(cv, 140, 320, 40, alive=False)
    plant(cv, 56, 312, 34, alive=False)
    # babouche left on the tiles (184,236 → 248,276)
    cv.ellipse(206, 256, 15, 9, "void")
    cv.ellipse(206, 253, 14, 7, "ink")
    cv.ellipse(224, 248, 12, 8, "void")
    cv.dither_rect(190, 246, 240, 268, "indigo", 0.2)
    cv.outline(191, 247, 221, 265, "slate")
    # scattered leaves + a dead fountain ring
    for i in range(26):
        rnd = random.Random(400 + i)
        cv.px(rnd.randrange(20, 620), rnd.randrange(WALL_BOT + 10, 350), "umber")
    cobweb(cv, 0, 0, 40)
    cobweb(cv, 320, 72, 30)
    dust(cv, 80, seed=32)
    lighting(cv, [
        (222, 132, 132, 0.92),                         # the courtyard lantern
        (320, 214, 196, 0.30, 0.55, "sky_dust"),       # daylight down the arches
    ], ambient=0.66)
    grade(cv, "lamp", "indigo", 0.12, 0.2, top=0, bottom=300)
    vignette(cv, 0.24)
    grain(cv, 0.015)
    return cv


# ====================================================================== ch5 kitchen
def kitchen():
    """مطبخ الإخوان — a range, a pot rack, and something still cooking."""
    cv = new("void")
    WALL_BOT = 170
    FLOOR_Y = 304

    plaster(cv, 0, 0, W, WALL_BOT, "clay", seed=41, damp=0.5)
    # tiled splashback
    for ty in range(0, WALL_BOT, 22):
        for tx in range(0, W, 22):
            cv.rect(tx + 1, ty + 1, tx + 20, ty + 20, "bone" if (tx // 22 + ty // 22) % 2 else "cream")
            cv.dither_rect(tx + 3, ty + 3, tx + 18, ty + 8, "ink", 0.1)
    cv.dither_rect(0, 0, W, WALL_BOT, "umber", 0.22)
    cv.noise(0, 0, W, WALL_BOT, 0.3, seed=42, scale=9, cols=("umber", "clay"))
    # pot rack (60,48 → 260,104)
    cv.rect(52, 44, 268, 50, "slate")
    cv.hline(52, 268, 44, "slate_lit")
    for i in range(6):
        px = 70 + i * 34
        cv.vline(px, 50, 58, "slate_lit")
        w = 14 + (i % 3) * 4
        cv.ellipse(px, 78 + (i % 2) * 6, w, w * 0.6, "slate")
        cv.ellipse(px, 76 + (i % 2) * 6, w * 0.8, w * 0.45, "grey")
        cv.dither_rect(px - w, 70 + (i % 2) * 6, px + w, 84 + (i % 2) * 6, "ink", 0.25)
    cv.ao(52, 44, 268, 100, depth=5, amount=0.4)
    # the floor goes down BEFORE any furniture, or it buries the room
    tile_floor(cv, 0, WALL_BOT, W, H, "slate_lit", "ink", cell=30)
    cv.dither_grad_v(0, WALL_BOT, W, WALL_BOT + 40, "ink", 0.22, 0.0)
    # the range (296,180 → 428,304)
    stove(cv, 296, 178, 428, 304)
    # the tagine on it (300,112 → 428,236)
    tagine(cv, 362, 154, 40, "clay", black=False)
    cv.light_pool(362, 164, 90, "flame", 0.28)
    # steam
    for i in range(30):
        rnd = random.Random(500 + i)
        sx = 340 + rnd.randrange(0, 46)
        sy = 120 - rnd.randrange(0, 70)
        cv.dither(sx, sy, "bone", 0.28)
    # table (36,188 → 256,264) + dark jar (92,192 → 124,228)
    table(cv, 36, 188, 256, 264, "brown")
    jar(cv, 92, 190, 32, 40, "slate")
    cv.dither_rect(96, 196, 120, 226, "ink", 0.3)
    for i in range(4):
        cv.rect(150 + i * 18, 182, 162 + i * 18, 190, "cream")
    # a second small table with a knife and onion
    table(cv, 250, 210, 330, 258, "umber")
    cv.rect(268, 202, 296, 208, "bone")
    cv.ellipse(308, 206, 7, 6, "cream")
    # stairs down (596,140 → 638,304)
    cv.rect(596, 140, 638, 304, "void")
    for i in range(9):
        sy = 152 + i * 18
        cv.rect(600, sy, 634, sy + 12, "slate" if i % 2 else "grey")
        cv.hline(600, 634, sy, "ink")
    cv.dither_grad_v(596, 140, 638, 304, "indigo", 0.3, 0.5)
    cv.ao(590, 140, 640, 304, depth=8, amount=0.5)
    # a blood smear by the range — small, deniable
    cv.dither_rect(420, 250, 470, 268, "red_dark", 0.3)
    dust(cv, 34, seed=43)
    lighting(cv, [
        (362, 196, 172, 0.95, 1.0, "flame"),           # the stove mouth
        (362, 300, 156, 0.36, 0.36, "ember"),          # spill across the floor
    ], ambient=0.60)
    grade(cv, "ember", "indigo", 0.16, 0.2, top=0, bottom=300)
    vignette(cv, 0.22)
    grain(cv, 0.015)
    return cv


# ====================================================================== ch6 cellar
def cellar():
    """القبو — the black tagine, a ring of candles, and what the Brothers keep."""
    cv = new("void")
    WALL_BOT = 240
    FLOOR_Y = 304

    stone_block(cv, 0, 0, W, WALL_BOT, "slate", seed=51)
    cv.dither_grad_v(0, 0, W, WALL_BOT, "void", 0.5, 0.2)
    # vault ribs
    for rx in (110, 320, 530):
        for i in range(28):
            t = i / 27.0
            ang = math.pi * t
            x = rx + math.cos(ang) * 96
            y = 40 + math.sin(ang) * 40
            cv.disc(x, y, 5, "ink")
            cv.disc(x, y - 2, 4, "slate")
    # shelf of skulls (0,52 → 192,100)
    cv.rect(0, 96, 192, 104, "umber")
    cv.hline(0, 192, 96, "clay")
    cv.ao(0, 52, 192, 100, depth=6, amount=0.5)
    for i in range(7):
        skull(cv, 16 + i * 27, 88, 10)
    # chains (192,48 → 480,156)
    chain(cv, 210, 30, 250, 150, links=16)
    chain(cv, 300, 24, 322, 158, links=18)
    chain(cv, 400, 30, 384, 146, links=16)
    for hx, hy in ((250, 150), (322, 158), (384, 146)):
        cv.ring(hx, hy + 6, 6, "slate_lit", 2, 210)
    # inner door (592,120 → 638,304)
    doorway(cv, 592, 120, 638, 304, "umber", "ink", open_dark=True)
    cv.dither_rect(594, 122, 636, 302, "void", 0.5)
    # stairs up (488,156 → 584,252)
    cv.rect(488, 156, 584, 252, "void")
    for i in range(6):
        sy = 162 + i * 16
        cv.rect(492 + i * 2, sy, 580 - i * 2, sy + 11, "slate" if i % 2 else "grey")
        cv.hline(492 + i * 2, 580 - i * 2, sy, "ink")
    cv.dither_grad_v(488, 156, 584, 252, "indigo", 0.2, 0.45)
    cv.ao(482, 150, 590, 258, depth=8, amount=0.55)
    tile_floor(cv, 0, WALL_BOT, W, H, "slate_lit", "ink", cell=34)
    cv.dither_grad_v(0, WALL_BOT, W, H, "void", 0.10, 0.28)
    # floor sigil (200,280 → 440,356)
    cv.ellipse(320, 320, 122, 38, "void")
    cv.dither_rect(200, 284, 440, 356, "indigo", 0.2)
    cv.ellipse(320, 320, 116, 34, "ink")
    for i in range(3):
        cv.ring(320, 320, 34 + i * 30, "crimson", 1, 120)
        cv.ellipse(320, 320, 34 + i * 30, (34 + i * 30) * 0.3, "crimson", 100)
    for a in range(0, 360, 45):
        rad = math.radians(a)
        cv.line(320 + math.cos(rad) * 30, 320 + math.sin(rad) * 10,
                320 + math.cos(rad) * 116, 320 + math.sin(rad) * 36, "red", 110)
    cv.disc(320, 320, 8, "crimson")
    # ring of candles (160,260 → 480,344)
    for i in range(11):
        a = math.pi * (0.08 + 0.84 * i / 10.0)
        cx = 320 + math.cos(a) * 140
        cy = 330 - math.sin(a) * 26
        candle(cv, cx, cy, 12 + (i % 3) * 3)
    # plinth + the black tagine (240,104 → 400,260)
    # The plinth used to stop at y=246 with the cellar floor at FLOOR_Y=304 -- it was
    # standing on nothing, 58px of air under it, which is why it read as floating no
    # matter how it was shaded. A plinth is a column: run it to the floor.
    contact_shadow(cv, 322, 300, 78, 12, 0.62)
    cv.rect(258, 214, 386, 298, "ink")
    cv.ellipse(322, 214, 64, 12, "slate")
    cv.dither_grad_h(258, 214, 386, 298, "void", 0.3, 0.6)
    cv.vline(258, 214, 298, "slate_lit")          # lit left edge of the column
    tagine(cv, 322, 178, 52, "ink", black=True)
    cv.light_pool(322, 190, 130, "ember", 0.3)
    # water dripping from the vault
    for i in range(14):
        rnd = random.Random(600 + i)
        cv.dither(rnd.randrange(60, 580), rnd.randrange(0, 240), "sky_dust", 0.35)
    cobweb(cv, 0, 0, 46)
    cobweb(cv, W, 0, 40, flip_x=True)
    dust(cv, 100, seed=52)
    lighting(cv, [
        (322, 190, 184, 0.80, 1.0, "ember"),           # the black tagine on its plinth
        (320, 320, 196, 0.74, 0.34, "lamp"),           # the ring of candles
    ], ambient=0.42)                                   # the darkest room in the game
    grade(cv, "ember", "indigo", 0.14, 0.26, top=0, bottom=H)
    vignette(cv, 0.26)
    grain(cv, 0.018)
    return cv


# ====================================================================== ch6 rooftop
def rooftop():
    """سطح الدار — Casablanca at night and an overturned tagine."""
    cv = new("void")
    SKY_BOT = 126
    PARAPET = 216
    DECK = 250
    FLOOR_Y = 312

    # sky
    cv.rect(0, 0, W, SKY_BOT + 20, "sky_night")
    cv.dither_grad_v(0, 0, W, SKY_BOT + 20, "indigo", 0.45, 0.1)
    for i in range(70):
        rnd = random.Random(700 + i)
        sx = rnd.randrange(0, W)
        sy = rnd.randrange(0, SKY_BOT)
        cv.px(sx, sy, "bone", rnd.randint(40, 140))
    # skyline (0,168 → 640,216)
    skyline(cv, 0, W, 216, seed=3)
    # moon glow over the city
    cv.light_pool(552, 140, 150, "bone", 0.12)
    # laundry above the roof (110,60 → 550,116)
    cv.vline(108, 40, 250, "slate")
    cv.vline(552, 30, 250, "slate")
    laundry_line(cv, 104, 556, 74, seed=5)
    # water tank (384,104 → 460,200)
    water_tank(cv, 384, 104, 460, 200)
    cv.dither_rect(378, 100, 466, 206, "ink", 0.2)
    satellite(cv, 366, 116, 8)
    # parapet wall in front of the city
    plaster(cv, 0, PARAPET, W, DECK, "clay", seed=61, damp=0.4)
    cv.rect(0, PARAPET, W, PARAPET + 8, "adobe")
    cv.dither_grad_v(0, PARAPET, W, DECK, "ink", 0.15, 0.5)
    cv.ao(0, PARAPET, W, DECK, depth=6, amount=0.4)
    # lantern on the parapet (516,160 → 560,208)
    cv.vline(538, 158, 216, "brass_dark")
    hang_lamp(cv, 538, 186, 11)
    # the roof deck
    tile_floor(cv, 0, DECK, W, H, "clay", "umber", cell=30)
    cv.dither_grad_v(0, DECK, W, DECK + 30, "ink", 0.45, 0.0)
    # overturned tagine (160,292 → 264,352)
    cv.ellipse(212, 322, 54, 16, "ink")
    cv.dither_rect(160, 296, 264, 348, "indigo", 0.22)
    cv.ellipse(206, 318, 34, 22, "clay")
    cv.ellipse(206, 314, 30, 18, "clay")
    cv.dither_rect(176, 300, 236, 318, "lamp", 0.18)
    cv.poly([(240, 316), (268, 306), (272, 318), (244, 328)], "clay")
    cv.ellipse(258, 314, 14, 8, "terracotta")
    # what spilled
    cv.dither_rect(180, 330, 300, 352, "red_dark", 0.3)
    cv.dither_rect(200, 336, 280, 348, "crimson", 0.16)
    # a bucket, a rope, a satellite dish
    cv.ellipse(120, 300, 14, 10, "slate")
    cv.ellipse(120, 296, 12, 6, "grey")
    cv.ellipse(120, 294, 11, 4, "void")
    cv.dither_rect(96, 288, 146, 310, "ink", 0.2)
    cv.line(320, 250, 560, 260, "leather", 120)
    satellite(cv, 470, 268, 10)
    cobweb(cv, W, PARAPET, 34, flip_x=True)
    dust(cv, 50, seed=62)
    lighting(cv, [
        (552, 140, 216, 0.55, 1.0, "sky_dust"),        # the moon over the medina
        (538, 190, 108, 0.85),                         # the lantern by the stair
    ], ambient=0.50)
    grade(cv, "lamp", "indigo", 0.1, 0.2, top=0, bottom=H)
    vignette(cv, 0.24)
    grain(cv, 0.015)
    return cv


# ====================================================================== title art
def title_art():
    """Key art: the inspector's doorway, one lantern, and two eyes in the dark."""
    cv = new("void")
    # night street
    cv.rect(0, 0, W, H, "sky_night")
    cv.dither_grad_v(0, 0, W, H, "indigo", 0.5, 0.2)
    plaster(cv, 0, 0, 180, H, "clay", seed=71, damp=0.6)
    plaster(cv, 460, 0, W, H, "clay", seed=72, damp=0.6)
    # a lit doorway in the middle
    cv.rect(250, 60, 390, 360, "void")
    arch(cv, 320, 60, 360, 150, "adobe", "void", "brass_dark")
    cv.rect(258, 90, 382, 360, "void")
    cv.dither_grad_v(258, 90, 382, 360, "ember", 0.45, 0.0)
    cv.light_pool(320, 300, 210, "ember", 0.3)
    # the inspector, back to us, in the doorway
    cv.rect(300, 176, 344, 320, "umber")
    cv.poly([(298, 178), (346, 178), (356, 320), (288, 320)], "brown")
    cv.dither_grad_h(288, 178, 356, 320, "ink", 0.3, 0.0)
    cv.ellipse(322, 162, 17, 19, "clay")
    cv.dither_rect(306, 146, 338, 178, "ink", 0.25)
    cv.poly([(304, 148), (340, 148), (336, 130), (308, 130)], "red")
    cv.dither_rect(308, 130, 336, 138, "crimson", 0.35)
    cv.rect(322, 130, 326, 118, "red_dark")
    cv.ellipse(322, 120, 6, 4, "red")
    # lantern in the left hand
    hang_lamp(cv, 292, 236, 13)
    # a black babouche on the step
    cv.ellipse(370, 336, 20, 11, "void")
    cv.ellipse(370, 332, 19, 9, "ink")
    cv.outline(351, 325, 389, 345, "slate")
    cv.dither_rect(352, 328, 388, 342, "indigo", 0.2)
    # the jnoun's eyes in the dark of the right alley
    for ex in (508, 540):
        cv.ellipse(ex, 210, 13, 7, "void")
        cv.ellipse(ex, 210, 9, 5, "crimson")
        cv.ellipse(ex, 210, 3, 4, "void")
        cv.dither_rect(ex - 16, 196, ex + 16, 226, "crimson", 0.14)
    cv.dither_rect(480, 180, 570, 250, "void", 0.4)
    cobbles(cv, 0, 300, W, H, seed=73)
    dust(cv, 90, seed=74)
    lighting(cv, [
        (292, 240, 122, 0.85),                         # the lantern over the title
        (320, 300, 236, 0.55, 1.0, "ember"),           # and the glow off the tagine
    ], ambient=0.60)
    grade(cv, "ember", "indigo", 0.16, 0.24, top=0, bottom=H)
    vignette(cv, 0.26)
    grain(cv, 0.018)
    return cv


# ====================================================================== main
ROOMS = [
    ("office", office),
    ("alley", alley),
    ("souk", souk),
    ("riad", riad),
    ("kitchen", kitchen),
    ("cellar", cellar),
    ("rooftop", rooftop),
    ("title", title_art),
]

if __name__ == "__main__":
    import os
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for name, fn in ROOMS:
        cv = fn()
        path = OUT + name + ".png"
        cv.save(path)
        total += 1
        print("  %-9s %s" % (name, path))
    print("\n%d rooms @ %dx%d" % (total, W, H))
