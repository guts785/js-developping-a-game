"""gen_dlg — the dialogue band, authored at its real size: 640 x 92.

WHY IT MOVED TO THE TOP
The box used to sit at the bottom, 104px tall, from y=256 to y=360. The actors
stand with their feet at base_y (up to 306) and are 102px tall, so they occupy
y=204..306. A panel starting at 256 therefore buried the bottom 48px of every
character -- 47% of the sprite -- every single time dialogue showed. The floor
they stand on was hidden with them. That is the "body is not placed right".

Dentures and Demons solves this by letterboxing: the dialogue box lives in the
top bar, the UI in the bottom bar, and the scene in between, so the box never
covers a character. This does the same -- a band at the top of the frame, under
the objective line, clear of the play area.

The rail now runs along the BOTTOM edge, because that is the edge that meets the
scene and needs to read as a border rather than a lid.

Run from the tools/ directory:  python3 gen_dlg.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pxlib import Cv, mix

OUT = "../art/ui/"
W, H = 640, 92
RAIL = 10          # height of the brass rail along the bottom of the band


def build():
    cv = Cv(W, H, None)

    # Warm leather-to-umber rather than umber-to-void. A near-black field is what
    # made the box look like a hole in the room; this sits in the palette and still
    # carries COL_TEXT (184,171,148) at better than 3:1.
    field_top = mix("leather", "umber", 0.55)   # ~ (81, 54, 37)
    field_bot = mix("leather", "void", 0.62)    # ~ (48, 32, 26)

    # ------------------------------------------------------------------ field
    cv.rect(0, 0, W, H, field_top)
    cv.dither_grad_v(0, 0, W, H - RAIL, field_bot, 0.10, 0.92)
    # horizontal grain, one dithered row every six, so the field has a surface
    for y in range(3, H - RAIL - 2, 6):
        cv.dither_rect(0, y, W, y + 1, "umber", 0.16)
    # the rail casts a little shadow upward onto the field
    cv.dither_rect(0, H - RAIL - 5, W, H - RAIL, "void", 0.30)

    # ------------------------------------------------------------- brass rail
    ry = H - RAIL
    cv.rect(0, ry, W, H, "brass_dark")
    cv.hline(0, W, ry, "ink")
    cv.hline(0, W, ry + 1, mix("brass_dark", "brass", 0.5))
    cv.hline(0, W, ry + 2, "brass")
    cv.hline(0, W, ry + 3, "lamp")              # the lit edge of the rail
    cv.hline(0, W, H - 2, "brass_dark")
    cv.hline(0, W, H - 1, "ink")
    # rivets, with a glint so they read as metal rather than dots
    for x in range(18, W, 32):
        cv.rect(x - 1, ry + 4, x + 2, H - 3, "brass_dark")
        cv.px(x, ry + 5, "lamp")
        cv.px(x + 1, ry + 6, mix("brass", "lamp", 0.45))
        cv.px(x, H - 4, "ink")

    # ------------------------------------------------------------------ border
    # A full brass frame on all four sides. The old border was 1px ink at the very
    # edge of the screen against a dark brown field -- invisible. The band read as
    # a flat slab with no top, left or right edge at all, and the only thing that
    # registered was the gold line where the rail met the scene. Dentures and
    # Demons frames its box the same way: a hard outline, then a lit inner edge.
    cv.outline(0, 0, W, H, "ink")
    cv.outline(1, 1, W - 1, H - 1, "brass_dark")
    cv.outline(2, 2, W - 2, H - 2, "brass")
    cv.hline(3, W - 3, 3, "lamp")                       # lit top edge
    cv.vline(3, 3, H - 3, mix("brass", "lamp", 0.40))   # lit left edge
    cv.vline(W - 4, 3, H - 3, mix("brass", "ink", 0.35))  # shaded right edge

    # corner brackets, brass, so the band is framed rather than clipped
    for cx, sx in ((5, 1), (W - 6, -1)):
        cv.line(cx, 8, cx + 4 * sx, 4, "lamp")
        cv.line(cx, 9, cx + 4 * sx, 5, "brass")
        cv.px(cx + 2 * sx, 6, "lamp")
    return cv


def main():
    os.makedirs(OUT, exist_ok=True)
    cv = build()
    n = cv.save(OUT + "dlg_box.png")
    op = sum(1 for i in range(cv.w * cv.h) if cv.buf[i * 4 + 3] > 200)
    print("dlg_box.png %dx%d  %d bytes  opaque %d/%d" % (cv.w, cv.h, n, op, cv.w * cv.h))


if __name__ == "__main__":
    main()
