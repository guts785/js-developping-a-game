"""gen_fx — the small transparent overlays the actors and the scene need.

Everything here is RGBA with real alpha, unlike the room art (which is opaque and
baked). Written with PIL rather than pxlib on purpose: pxlib's canvas composites
with write-once-max alpha, which is right for sprite sheets but makes a soft
alpha ramp awkward to author.

Run:  python3 gen_fx.py     (from tools/)
"""
import math
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "art", "fx")
os.makedirs(OUT, exist_ok=True)


def contact_shadow(w=66, h=18, peak=205, tint=(10, 7, 11)):
    """The shadow under an actor's feet.

    Replaces art/ui/actor_halo.png, which was supposed to do this and never did:
    it is 72x32 with a peak alpha of 35 and not one fully-opaque pixel, so it
    rendered as nothing on every frame and the whole cast looked pasted onto the
    backdrop. The falloff here is deliberately long and shallow -- a steep ramp
    at this size reads as a hard black patch on the floor rather than a contact
    shadow, and the tint is a near-black warm rather than pure black so it sits
    inside the room's palette instead of cutting a hole in it.
    """
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            d = math.hypot((x - (w - 1) / 2.0) / (w / 2.0), (y - (h - 1) / 2.0) / (h / 2.0))
            if d > 1.0:
                continue
            a = int(peak * ((1.0 - d) ** 1.2))
            if a > 0:
                px[x, y] = (tint[0], tint[1], tint[2], a)
    return im


def mote(r=2, peak=150):
    """A single dust mote for the ambient float in lit rooms."""
    w = h = r * 2 + 1
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - r, y - r) / float(r)
            if d > 1.0:
                continue
            px[x, y] = (246, 214, 150, int(peak * (1.0 - d) ** 1.2))
    return im


if __name__ == "__main__":
    for name, img in (("shadow", contact_shadow()), ("mote", mote())):
        p = os.path.join(OUT, "%s.png" % name)
        img.save(p)
        # prove the alpha ramp is real, not another invisible overlay
        a = [img.getpixel((x, y))[3] for y in range(img.size[1]) for x in range(img.size[0])]
        print("  %-7s %sx%s  peak-alpha=%3d  opaque-px=%4d  %s"
              % (name, img.size[0], img.size[1], max(a), sum(1 for v in a if v == 255), p))
