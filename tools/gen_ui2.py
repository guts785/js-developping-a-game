#!/usr/bin/env python3
"""gen_ui2.py -- UI chrome at native 640x360 density.

The v1 UI PNGs were authored in the old 320x180 logical space and the runtime
stretches them (320x64 -> 640x64), which squashes the ornament horizontally.
These are drawn natively at final size with real detail instead of an upscale.

Only five assets are actually referenced by the runtime: vignette, dlg_box,
cursor, chapter_card, ending_card. Stdlib only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pxlib import Cv, P, mix  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art", "ui")

BAYER4 = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
]


def transparent(w, h):
    """A genuinely transparent RGBA canvas.

    Cv's per-pixel alpha is write-once-max (px() does max(ba, a)), so alpha can
    never be cleared back to 0 by drawing -- it has to start empty. bg=None
    leaves the buffer zeroed, which is alpha 0 everywhere.
    """
    return Cv(w, h, None)


def rosette(c, cx, cy, r=8):
    """Moorish rosette: concentric diamonds with diagonal studs.

    Deliberately not a cross or an L-bracket -- those read as editor alignment
    handles rather than ornament when they sit at a frame corner.
    """
    c.poly([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], "brass_dark")
    r2 = max(2, r - 3)
    c.poly([(cx, cy - r2), (cx + r2, cy), (cx, cy + r2), (cx - r2, cy)], "gold")
    r3 = max(1, r2 - 3)
    c.poly([(cx, cy - r3), (cx + r3, cy), (cx, cy + r3), (cx - r3, cy)], "void")
    for (dx, dy) in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        c.px(cx + dx * (r + 2), cy + dy * (r + 2), "brass")


def zellige_rail(c, x0, y0, x1, y1, seed_shift=0):
    """A repeating Moorish diamond strip -- the house ornament."""
    y = y0
    h = y1 - y0
    step = 20
    x = x0 + step // 2
    while x < x1:
        half = max(2, h // 2)
        c.poly([(x, y - half + h), (x + half, y + h // 2), (x, y + half + 1), (x - half, y + h // 2)],
               "brass_dark")
        c.px(x, y + h // 2, "gold")
        x += step
    _ = seed_shift


def brass_frame(c, x0, y0, x1, y1, thick=3):
    """Riveted brass border with a lit top-left and a shadowed bottom-right."""
    c.rect(x0, y0, x1, y1, "brass")
    c.rect(x0, y0, x1, y0 + 1, "gold")            # lit rail
    c.rect(x0, y0, x0 + 1, y1, "gold")
    c.rect(x0, y1 - 1, x1, y1, "brass_dark")      # shadowed rail
    c.rect(x1 - 1, y0, x1, y1, "brass_dark")
    c.rect(x0 + thick, y0 + thick, x1 - thick, y1 - thick, "void")
    c.rect(x0 + thick, y0 + thick, x1 - thick, y0 + thick + 1, "ink")
    # corner rosettes
    for (cx, cy) in [(x0 + 4, y0 + 4), (x1 - 5, y0 + 4), (x0 + 4, y1 - 5), (x1 - 5, y1 - 5)]:
        rosette(c, cx, cy, 7)


def gen_vignette(w=640, h=360):
    """Radial darkening, alpha-dithered so the falloff still reads as pixels.

    Falloff starts at 0.62 of the half-diagonal instead of 0.40 and tops out near
    half alpha instead of 78%. At the old values the bottom-centre of the frame got
    44% darkening, and every room bakes its own corner falloff underneath -- the two
    stacked turned the bottom third into a letterbox on top of an already dark floor.
    """
    c = transparent(w, h)
    cx, cy = w / 2.0, h / 2.0
    levels = 9
    for y in range(h):
        dy = (y - cy) / cy
        row = BAYER4[y & 3]
        for x in range(w):
            dx = (x - cx) / cx
            d = (dx * dx + dy * dy) ** 0.5          # 0 centre, ~1.41 corner
            t = (d - 0.62) / 0.86
            if t <= 0.0:
                continue
            if t > 1.0:
                t = 1.0
            q = t * t * levels * 0.55               # quadratic, capped
            base = int(q)
            frac = q - base
            thr = (row[x & 3] + 0.5) / 16.0
            if frac > thr:
                base += 1
            if base > levels:
                base = levels
            a = int(base / float(levels) * 255)
            if a > 0:
                c.px(x, y, "void", a)
    # bottom edge sinks harder -- the frame of the CRT
    for y in range(h - 26, h):
        k = (y - (h - 26)) / 26.0
        for x in range(0, w, 2):
            a = int(k * 26)
            if a > 0:
                c.px(x, y, "void", min(255, a))
    c.save(os.path.join(OUT, "vignette.png"))


def gen_dlg_box(w=640, h=64):
    """Strip that caps the dialogue box. The panel below supplies the fill.

    Kept deliberately plain: an earlier version had corner caps and a dashed
    zellige band, and at 1:1 on a CRT filter that reads as a selection marquee
    with drag handles rather than as ornament.
    """
    c = Cv(w, h, "void")
    c.rect(0, 0, w, h, "void")
    c.ramp_v(0, 0, w, h, [(0.0, mix("void", "ink", 0.75)), (0.4, "void"), (1.0, mix("void", "night", 0.5))])
    # one clean brass rail
    c.rect(0, 0, w, 3, "brass")
    c.rect(0, 0, w, 1, "gold")
    c.rect(0, 3, w, 4, "ink")
    c.rect(0, h - 2, w, h, "ink")
    c.ao(0, 4, w, h, depth=8, amount=0.35)
    c.noise(0, 5, w, h - 3, 0.06, seed=17, scale=6, cols=("ink", "night"))
    c.save(os.path.join(OUT, "dlg_box.png"))


def gen_cursor(w=24, h=26):
    """Pointing hand, ink-outlined, brass cuff -- legible on any room."""
    c = transparent(w, h)
    body = "bone"
    # index finger
    c.rect(9, 2, 14, 13, "ink")
    c.rect(10, 3, 13, 13, body)
    c.rect(11, 2, 12, 4, "cream")
    # knuckle mass
    c.rect(5, 11, 19, 21, "ink")
    c.rect(6, 12, 18, 20, body)
    # folded fingers
    for i, x in enumerate((7, 10, 13)):
        c.rect(x, 13, x + 3, 17, mix(body, "slate", 0.35 + i * 0.08))
    # thumb
    c.rect(3, 13, 8, 19, "ink")
    c.rect(4, 14, 7, 18, body)
    # cuff
    c.rect(6, 20, 18, 24, "ink")
    c.rect(7, 21, 17, 23, "brass")
    c.rect(7, 21, 17, 22, "gold")
    # highlight
    c.rect(11, 5, 12, 11, "white")
    c.px(6, 13, "cream")
    c.save(os.path.join(OUT, "cursor.png"))


def gen_chapter_card(w=480, h=192):
    """Dark card with a brass frame; the chapter title is drawn over it by Godot."""
    c = Cv(w, h, "void")
    c.rect(0, 0, w, h, "void")
    c.ramp_v(0, 0, w, h, [(0.0, mix("void", "indigo", 0.45)), (0.5, "void"), (1.0, "night")])
    c.fog_band(0, 0, w, h, "majorelle", 0.10, seed=5)
    brass_frame(c, 0, 0, w, h, thick=4)
    # inner hairline
    c.outline(7, 7, w - 8, h - 8, "brass_dark")
    # zellige strips top and bottom
    zellige_rail(c, 20, 12, w - 20, 13)
    zellige_rail(c, 20, h - 14, w - 20, h - 15)
    # corner rosettes
    for (ox, oy) in [(14, 14), (w - 15, 14), (14, h - 15), (w - 15, h - 15)]:
        rosette(c, ox, oy, 9)
    c.ao(4, 4, w - 4, h - 4, depth=10, amount=0.45)
    c.noise(8, 8, w - 8, h - 8, 0.08, seed=31, scale=5, cols=("indigo", "void"))
    c.save(os.path.join(OUT, "chapter_card.png"))


def gen_ending_card(w=512, h=256):
    """Same family, larger, with a heavier frame for the payoff screen."""
    c = Cv(w, h, "void")
    c.rect(0, 0, w, h, "void")
    c.ramp_v(0, 0, w, h, [(0.0, "night"), (0.45, mix("void", "indigo", 0.35)), (1.0, "void")])
    c.light_pool(w * 0.5, h * 0.30, 150, "lamp", 0.16)
    c.fog_band(0, h * 0.5, w, h, "crimson", 0.07, seed=11)
    brass_frame(c, 0, 0, w, h, thick=5)
    c.outline(9, 9, w - 10, h - 10, "brass_dark")
    c.outline(11, 11, w - 12, h - 12, "brass_dark")
    zellige_rail(c, 26, 15, w - 26, 16)
    zellige_rail(c, 26, h - 17, w - 26, h - 18)
    # a small tagine silhouette, the game's mark
    cx, cy = w * 0.5, h - 40
    c.ellipse(cx, cy, 34, 8, "brass_dark")
    c.poly([(cx - 30, cy - 1), (cx, cy - 30), (cx + 30, cy - 1)], "brass_dark")
    c.poly([(cx - 22, cy - 3), (cx, cy - 24), (cx + 22, cy - 3)], "brass")
    c.ring(cx, cy - 31, 3, "gold", 1)
    c.ao(6, 6, w - 6, h - 6, depth=12, amount=0.4)
    c.noise(10, 10, w - 10, h - 10, 0.07, seed=47, scale=6, cols=("indigo", "void"))
    c.save(os.path.join(OUT, "ending_card.png"))


def gen_actor_halo(w=72, h=32):
    """Warm contact pool drawn at the actor's feet.

    The inspector wears a dark djellaba in dark rooms, so he kept dissolving into
    the floor. This is the lamp catching the ground under him -- it separates the
    silhouette without touching the sprite itself.
    """
    c = transparent(w, h)
    cx, cy = w / 2.0, h / 2.0
    for y in range(h):
        dy = (y - cy) / cy
        for x in range(w):
            dx = (x - cx) / cx
            d = (dx * dx + dy * dy) ** 0.5
            if d >= 1.0:
                continue
            fall = (1.0 - d)
            q = fall * fall * 0.80
            base = int(q)
            frac = q - base
            if frac > (BAYER4[y & 3][x & 3] + 0.5) / 16.0:
                base += 1
            a = int(min(base, 6) / 6.0 * 210)
            if a > 0:
                c.px(x, y, "lamp", a)
    c.save(os.path.join(OUT, "actor_halo.png"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    gen_vignette()
    gen_dlg_box()
    gen_cursor()
    gen_chapter_card()
    gen_ending_card()
    gen_actor_halo()
    print("6 UI assets written at native size (vignette 640x360, dlg_box 640x64,")
    print("cursor 24x26, chapter_card 480x192, ending_card 512x256, actor_halo 72x32)")
