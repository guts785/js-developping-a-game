"""gen_ui3 — the inventory ledge.

The HUD bar was a flat near-black rectangle: 640x46 game pixels of it, 19 distinct
colours across the whole band. Against a dithered room it read as a letterbox -- the
eye files it as "the picture ends here", not as furniture. Worse, the actors walk in
front of it, so the flatness was sitting right under the busiest part of the frame.

This draws it as what it actually is: a wooden ledge with a brass rail along the top
lip, the shadow it throws back onto the room, and enough grain that it reads as part
of the set. The brass line is the important part -- it gives the bottom of the frame
an edge, which is what stops a dark bar from looking like missing image data.

Run from this directory:  python3 gen_ui3.py
"""
import os

from pxlib import Cv, mix

OUT = "../art/ui/"
W, H = 640, 46


def hud_bar():
    cv = Cv(W, H)
    # body: worn wood, lit from the left like every other surface in the game
    cv.rect(0, 0, W, H, "brown")
    cv.dither_grad_h(0, 0, W, H, "umber", 0.34, 0.0)
    for i in range(0, W, 7):
        cv.vline(i, 5, H, "umber", 90 if i % 14 == 0 else 55)
    cv.dither_rect(0, 6, W, 16, "clay", 0.16)
    cv.dither_rect(0, H - 12, W, H, "ink", 0.30)

    # brass rail along the top lip. One bright line, one dark line under it.
    cv.rect(0, 0, W, 2, "brass_dark")
    cv.hline(0, W, 2, "brass")
    cv.dither_rect(0, 3, W, 4, "bone", 0.35)
    cv.hline(0, W, 4, "ink")

    # shadow the rail throws down the face of the ledge
    cv.dither_grad_v(0, 5, W, 15, "ink", 0.42, 0.0)

    # end grain, so the bar has caps instead of running off both edges
    for x in (0, W - 3):
        cv.rect(x, 0, x + 2, H, "umber")
        cv.vline(x + 2 if x == 0 else x - 1, 0, H, "ink")

    cv.hline(0, W, H - 1, "ink")
    return cv


def main():
    os.makedirs(OUT, exist_ok=True)
    hud_bar().save(OUT + "hud_bar.png")
    print("hud_bar.png %dx%d" % (W, H))


if __name__ == "__main__":
    main()
