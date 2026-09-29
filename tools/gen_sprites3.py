"""gen_sprites3 — native-resolution walk sheets for «البلغة والجن».

gen_sprites2 authored the rig at 36x68 and the game drew it at ART_SCALE 1.5.
Nearest-neighbour at 1.5x is the worst scale you can pick for pixel art: every
other source pixel lands on one screen pixel while its neighbour lands on two, so
the figure shimmers as it walks and never sits on the room's grid. That is what
made the actors read as pasted-on rather than part of the scene.

This keeps the proven rig — same joint chains, same cloth silhouette, same six
walk poses, same palette — but rasterises it directly at 54x102 through a scaling
proxy, so the rig maths stays in the units it was tuned in while the pixels it
lands on are real pixels of the final frame. Then a native detail pass spends the
extra pixels: a real eye (socket, sclera, iris, catchlight), a hand with a thumb,
an instep strap on each babouche.

Portraits are untouched: they were always drawn 1:1 at 88x88, so they never had
the scaling problem.

Run from this directory:  python3 gen_sprites3.py
"""
import math
import os

from pxlib import Cv, mix
import gen_sprites2 as g2
from gen_sprites2 import (
    Char as Char2, CHARS, MOODS, portrait, limb, foot, joint,
    FOOT_Y, HIP_Y, SHOULDER_Y, HEAD_CY, THIGH, SHIN, UPARM, LOARM,
    NFRAMES, OUT,
)

# design space is gen_sprites2's 36x72; native is exactly 1.5x of it
S = 1.5
DFW, DFH = 36, 72
FW, FH = int(round(DFW * S)), int(round(DFH * S))     # 54 x 108


class ScaledCv:
    """Design-space drawing onto a native canvas.

    Every coordinate, radius and width multiplies by S on the way in; palette names
    and alphas pass through untouched. Because it quacks like Cv, the whole Char rig
    in gen_sprites2 draws through it without a single change — which is the point.
    """

    def __init__(self, cv, s):
        self.cv = cv
        self.s = float(s)

    def px(self, x, y, c, a=255):
        self.cv.px(x * self.s, y * self.s, c, a)

    def get(self, x, y):
        return self.cv.get(int(x * self.s), int(y * self.s))

    def rect(self, x0, y0, x1, y1, c, a=255):
        self.cv.rect(x0 * self.s, y0 * self.s, x1 * self.s, y1 * self.s, c, a)

    def outline(self, x0, y0, x1, y1, c):
        self.cv.outline(x0 * self.s, y0 * self.s, x1 * self.s, y1 * self.s, c)

    def hline(self, x0, x1, y, c, a=255):
        self.cv.hline(x0 * self.s, x1 * self.s, y * self.s, c, a)

    def vline(self, x, y0, y1, c, a=255):
        self.cv.vline(x * self.s, y0 * self.s, y1 * self.s, c, a)

    def line(self, x0, y0, x1, y1, c, a=255):
        self.cv.line(x0 * self.s, y0 * self.s, x1 * self.s, y1 * self.s, c, a)

    def disc(self, cx, cy, r, c, a=255):
        self.cv.disc(cx * self.s, cy * self.s, r * self.s, c, a)

    def ring(self, cx, cy, r, c, thick=1, a=255):
        self.cv.ring(cx * self.s, cy * self.s, r * self.s, c, max(1, thick * self.s), a)

    def ellipse(self, cx, cy, rx, ry, c, a=255):
        self.cv.ellipse(cx * self.s, cy * self.s, rx * self.s, ry * self.s, c, a)

    def poly(self, pts, c, a=255):
        self.cv.poly([(x * self.s, y * self.s) for x, y in pts], c, a)

    def dither_rect(self, x0, y0, x1, y1, c, amount):
        self.cv.dither_rect(x0 * self.s, y0 * self.s, x1 * self.s, y1 * self.s, c, amount)

    def dither_grad_v(self, x0, y0, x1, y1, c, a_top, a_bot):
        self.cv.dither_grad_v(x0 * self.s, y0 * self.s, x1 * self.s, y1 * self.s,
                              c, a_top, a_bot)

    def noise(self, x0, y0, x1, y1, amount, seed=1, scale=3, cols=("ink", "slate")):
        self.cv.noise(x0 * self.s, y0 * self.s, x1 * self.s, y1 * self.s, amount,
                      seed, max(1, int(scale * self.s)), cols)

    def speckle(self, x0, y0, x1, y1, c, count, seed=1, amount=0.7):
        self.cv.speckle(x0 * self.s, y0 * self.s, x1 * self.s, y1 * self.s, c,
                        max(1, int(count * self.s * self.s)), seed, amount)

    def light_pool(self, cx, cy, r, c="lamp", strength=0.55, squash=1.0):
        self.cv.light_pool(cx * self.s, cy * self.s, r * self.s, c, strength, squash)


class Char(Char2):
    # ------------------------------------------------------------------ face
    def _face(self, cv, hx, hy):
        """Native-resolution face. Replaces the proxy's version outright.

        Two design pixels per eye was all 36x68 could afford, and at 1.5x that
        becomes a grey smudge. Worse, the rig's hair cap and beard met in the middle
        of the head, so there was no skin between them at all -- at native size the
        face read as a dark void with two white dots in it.

        So this does not decorate the proxy's head, it re-lays it: a clean skin oval,
        then beard, fringe, brows, eyes, nose, mouth in that order, so features always
        land on top of facial hair instead of underneath it.
        """
        hx = int(round(hx))
        hy = int(round(hy))
        sk, sl, sd, ink = self.skin, self.skin_lit, self.skin_dark, "ink"

        # ink rim, then the face oval. The face has to separate from whatever is
        # behind it: against zahra's crimson scarf and the men's near-black hair the
        # skin was the same luminance as its surroundings, so the head closed up into
        # a single dark mass with two white dots in it.
        cv.ellipse(hx, hy, 7.6, 8.4, ink)
        cv.ellipse(hx, hy, 7.0, 7.8, sk)
        cv.ellipse(hx - 2.4, hy - 0.6, 4.4, 5.6, sl)
        cv.ellipse(hx + 3.2, hy + 1.4, 3.2, 4.4, sd)
        cv.ellipse(hx, hy + 4.6, 5.6, 3.0, sk)

        # beard first: a jaw ring, not a mask. The mouth stays clear of it.
        if self.beard:
            bc = self.beard
            cv.ellipse(hx - 5, hy + 4, 2.4, 4.0, bc)
            cv.ellipse(hx + 5, hy + 4, 2.4, 4.0, bc)
            cv.ellipse(hx, hy + 10, 4.8, 3.0, bc)
            cv.dither_rect(hx - 6, hy + 8, hx + 6, hy + 12, mix(bc, ink, 0.4), 0.26)

        # fringe only where a hat is not already covering the crown
        if self.hair and not self.hat:
            cv.ellipse(hx, hy - 6.5, 7.2, 2.6, self.hair)

        cv.line(hx - 6, hy - 3, hx - 2, hy - 3, ink, 210)
        cv.line(hx + 2, hy - 3, hx + 6, hy - 3, ink, 210)

        for ex in (hx - 4, hx + 4):
            cv.rect(ex - 1, hy - 2, ex + 1, hy + 1, ink)   # socket
            cv.rect(ex - 1, hy - 1, ex, hy, "bone")        # sclera
            cv.px(ex + 1, hy, self.eyes)                   # iris
            cv.px(ex, hy - 1, "bone")                      # catchlight

        cv.px(hx, hy + 3, sd)
        cv.px(hx + 1, hy + 3, mix(sd, ink, 0.45))
        cv.line(hx - 2, hy + 6, hx + 2, hy + 6, mix(sd, ink, 0.5), 215)
        cv.dither_rect(hx - 6, hy + 7, hx + 6, hy + 8, sd, 0.18)

    # ------------------------------------------------------------------ detail
    def _detail(self, cv, cx, head_cy, hands, ankles):
        """The pixels that only exist because the frame got 2.25x bigger."""
        s = S
        self._face(cv, cx * s, head_cy * s)
        for (hx, hy) in hands:
            cv.px(hx * s - 2, hy * s - 2, self.skin_lit)
            cv.px(hx * s + 2, hy * s + 1, self.skin_dark)
        for (ax, ay, col) in ankles:
            # instep strap — one design pixel of detail that survives at native res
            cv.line(ax * s - 3, ay * s - 1, ax * s + 2, ay * s - 2,
                    mix(col, "ink", 0.5), 200)

    # ------------------------------------------------------------------ frame
    def _frame_native(self, proxy, cv, ox, idx):
        pose = g2.WALK[idx] if idx < 6 else g2.IDLE[idx - 6]
        tL, sL, tR, sR, aL, aR, bob = pose
        bob *= 1.7
        # Arms: enforce a minimum outward swing. IDLE holds them at +-4 degrees,
        # which hangs both hands on the centre line of the garment where they read
        # as nothing at all -- the figure looks armless. Walk poses swing +-36, well
        # past this floor, so only the two idle frames change.
        aL = min(aL, -9.0)
        aR = max(aR, 9.0)
        # Ceilings as well as floors. The walk swings to +-36 degrees, and at -36 the
        # left hand lands at design x -0.2 -- off the left edge of a 54px frame. Every
        # contact pose was flat-clipped at x0. +-26 keeps the swing reading while the
        # hand stays inside the sprite.
        aL = max(aL, -26.0)
        aR = min(aR, 26.0)
        cx = ox + DFW * 0.5
        g = self.girth
        ground = FOOT_Y
        hip = HIP_Y + bob - (1.0 - self.height) * 6
        sh = SHOULDER_Y + bob - (1.0 - self.height) * 6 + self.hunch
        head_cy = HEAD_CY + bob - (1.0 - self.height) * 6 + self.hunch * 1.4

        # No baked shadow. The sheet used to draw its own "void" ellipse here at
        # ground+1, which was the only grounding the cast had -- but it is clipped
        # by the frame, hard-edged, and it now doubles up with the soft runtime
        # shadow sprite that art/fx/shadow.png provides. One shadow, drawn at
        # runtime, in the right shape. (Measured: this baked ellipse was the widest
        # thing in the sprite at 29-35px on the last row, wider than the shoulders,
        # which is why the silhouette read as a bell.)

        if self.floats:
            self._frame_float(proxy, cx, idx, bob)
            t = idx / float(NFRAMES)
            lift = 3.0 + math.sin(t * math.pi * 2) * 2.0
            self._face(cv, cx * S, (HEAD_CY + lift) * S)
            return

        ankles = []
        for (tt, ss, col) in ((tR, sR, self.robe_dark), (tL, sL, self.robe)):
            kx, ky = joint(cx, hip, tt, THIGH)
            ax, ay = joint(kx, ky, tt + ss, SHIN)
            limb(proxy, cx, hip, kx, ky, 5.4 * g, 4.6 * g, col, self.robe_dark)
            limb(proxy, kx, ky, ax, ay, 4.6 * g, 3.8 * g, col, self.robe_dark)
            foot(proxy, ax, ay, mix(self.shoes, "slate", 0.3))
            ankles.append((ax, ay, col))

        # Floor-length garments get a flared skirt and no visible legs. Four of the
        # cast were reading as the same silhouette -- a pair of legs under a tunic --
        # and a hat plus a colour swap does not fix that at 1x. A column does.
        floor_length = self.outfit in ("shawl", "hooded", "coat")
        # Hem raised from ground-16. The arm now ends at 44.9 and the knee sits at
        # HIP_Y+THIGH = 52, so ground-20 is as high as the robe can ride without the
        # hands poking out below it -- and it buys 4 more design px of visible leg.
        hem_y = ground - 2 if floor_length else ground - 20 + (1.0 - self.height) * 4
        sway = (tL - tR) * 0.12
        self.draw_body(proxy, cx, sh - 1, hem_y, sway, g)
        if floor_length:
            # Flare trimmed from 10.0g to 8.8g. At 10.0 the skirt finished 30px wide
            # against a 23-25px shoulder -- measured as the widest row in the sprite,
            # i.e. a bell. A robe should read as shoulders first, sweep second.
            proxy.poly([(cx - 6.6 * g, hem_y - 18), (cx + 6.6 * g, hem_y - 18),
                        (cx + 8.8 * g, hem_y), (cx - 8.8 * g, hem_y)], self.robe)
            proxy.dither_rect(cx - 8.8 * g, hem_y - 7, cx + 8.8 * g, hem_y,
                              self.robe_dark, 0.32)
            proxy.line(cx - 8.8 * g, hem_y, cx + 8.8 * g, hem_y, "ink", 230)
        if self.outfit == "apron":
            self.draw_apron(proxy, cx, sh - 1, hem_y - 2, g)

        hands = []
        # Shoulder joints sit at the garment's shoulder width, not on the spine.
        # Hanging the arms from the centre line buries them inside the robe -- same
        # value, no silhouette break -- so the figure reads as armless no matter how
        # the sleeve is shaded. From +-3.6 the sleeve straddles the garment edge and
        # its ink rim becomes a real outline. Both sleeves are pushed toward ink so
        # they separate from the robe; the lit-side arm only slightly less.
        for (aa, col, side) in ((aR, mix(self.robe, "ink", 0.42), 1.0),
                                (aL, mix(self.robe, "ink", 0.30), -1.0)):
            sx = cx + side * 3.0 * g
            ex, ey = joint(sx, sh + 3, aa, UPARM)
            hx, hy = joint(ex, ey, aa * 1.1, LOARM * 0.88)
            limb(proxy, sx, sh + 3, ex, ey, 4.6 * g, 3.8 * g, col, self.robe_dark)
            limb(proxy, ex, ey, hx, hy, 3.8 * g, 3.2 * g, col, self.robe_dark)
            # Inner seam. The sleeve is already pushed toward ink, but at 1x the robe
            # and the sleeve still read as one mass -- the limb only resolves as a
            # limb when there is a hard dark line where it meets the torso. This is
            # the single highest-value pixel on the whole sprite.
            for k in range(9):
                f = k / 8.0
                proxy.px(sx + (ex - sx) * f - side * 2.2 * g,
                         (sh + 3) + (ey - (sh + 3)) * f, "ink")
            for k in range(7):
                f = k / 6.0
                proxy.px(ex + (hx - ex) * f - side * 1.8 * g,
                         ey + (hy - ey) * f, "ink")
            proxy.disc(hx, hy, 2.4, self.skin_dark)
            proxy.disc(hx, hy, 1.9, self.skin)
            proxy.disc(hx - 0.6, hy - 0.6, 1.1, self.skin_lit)
            hands.append((hx, hy))

        self.draw_prop(proxy, cx, ground, 1)
        self.draw_head(proxy, cx, head_cy, 1)
        self.draw_hat(proxy, cx, head_cy)
        proxy.rect(cx - 2, head_cy + 5, cx + 2, sh + 1, self.skin_dark)
        proxy.dither_rect(cx - 2, head_cy + 5, cx + 2, sh, "ink", 0.3)

        self._detail(cv, cx, head_cy, hands, ankles)

    # ------------------------------------------------------------------ body
    def draw_body(self, cv, cx, y_top, hem_y, sway=0.0, girth=1.0):
        """Shoulders, chest, waist, hem -- a body, not a rectangle.

        The inherited version is a flat-topped trapezoid: half-width 6.2 at the
        shoulders to 7.7 at the hem, a 24% taper. At native size that is a
        monolithic block with no shoulders, no waist and no chest -- the figure
        reads as a walking curtain, and the flat top gives it no neck. A silhouette
        has to change direction on the way down: neck notch, shoulder shelf, chest,
        waist pinch, then the hem.
        """
        g = girth
        span = max(1.0, hem_y - y_top)

        def y_at(t: float) -> float:
            return y_top + span * t

        neck = 2.9 * g
        sho = 8.4 * g
        wst = 4.5 * g
        hem = 6.5 * g
        out = [
            (cx - neck, y_top),
            (cx - sho, y_at(0.09)),
            (cx - sho * 0.96, y_at(0.30)),
            (cx - wst, y_at(0.60)),
            (cx - hem + sway, hem_y),
            (cx + hem + sway, hem_y),
            (cx + wst, y_at(0.60)),
            (cx + sho * 0.96, y_at(0.30)),
            (cx + sho, y_at(0.09)),
            (cx + neck, y_top),
        ]
        yc = (y_top + hem_y) * 0.5

        def inflate(p, d):
            x, y = p
            dx, dy = x - cx, y - yc
            n = math.hypot(dx, dy) or 1.0
            return (x + dx / n * d, y + dy / n * d)

        cv.poly([inflate(p, 1.3) for p in out], "ink")
        cv.poly(out, self.robe)
        # vertical cloth folds
        for i in range(-2, 3):
            fx = cx + i * (hem * 0.40)
            cv.line(fx + sway * 0.6, y_top + 3, fx * 0.9 + cx * 0.1 + sway, hem_y - 1,
                    self.robe_dark, 120)
        # lit left edge, shaded right
        cv.line(cx - sho + 0.6, y_at(0.11), cx - hem + sway + 0.6, hem_y,
                mix(self.robe, "lamp", 0.32), 170)
        cv.dither_rect(cx + 2.0, y_at(0.14), cx + hem + sway, hem_y, self.robe_dark, 0.32)
        # waist pinch, stated on both edges so the taper is legible at 1x
        cv.line(cx - sho, y_at(0.11), cx - wst, y_at(0.58), mix(self.robe, "ink", 0.30), 150)
        cv.line(cx + sho, y_at(0.11), cx + wst, y_at(0.58), mix(self.robe, "ink", 0.30), 150)
        # collar V at the neck
        cv.line(cx - neck, y_top, cx, y_top + 3.6, self.trim, 210)
        cv.line(cx + neck, y_top, cx, y_top + 3.6, self.trim, 210)
        # sash at the waist. This is the single line that makes the garment read as
        # something worn by a body rather than a hanging block.
        sy0, sy1 = y_at(0.55), y_at(0.68)
        cv.rect(cx - wst - 0.4, sy0, cx + wst + 0.4, sy1, self.trim)
        cv.dither_rect(cx - wst - 0.4, sy0, cx + wst + 0.4, sy0 + 1, "bone", 0.22)
        cv.line(cx - wst - 0.4, sy1, cx + wst + 0.4, sy1, "ink", 170)
        return hem_y

    # ------------------------------------------------------------------ sheet
    def walk_sheet(self):
        cv = Cv(FW * NFRAMES, FH, None)   # native canvas: 432 x 102, TRANSPARENT
        # bg=None, not the default "void". An opaque sheet renders as a solid
        # 54x102 near-black rectangle with the figure painted on it -- the sprite
        # box the actors stood inside. Alpha is write-once-max here, so a
        # transparent sheet can only be had by never writing a background.
        proxy = ScaledCv(cv, S)
        for i in range(NFRAMES):
            self._frame_native(proxy, cv, i * DFW, i)
        return cv


def _recast():
    """Re-home every cast entry onto the native Char without re-typing the table."""
    # sliman and fqih were authored a full step down the skin ramp. At native size
    # that put their faces at the same luminance as the ink outline, so the head read
    # as a dark blob with two white dots. One step up each, which also lifts their
    # portraits.
    skin_fix = {
        "sliman": ("skin", "skin_lit", "skin_dark"),
        "fqih": ("skin", "skin_lit", "skin_dark"),
    }
    out = {}
    for cid, ch in CHARS.items():
        n = Char.__new__(Char)
        n.__dict__.update(ch.__dict__)
        if cid in skin_fix:
            n.skin, n.skin_lit, n.skin_dark = skin_fix[cid]
        out[cid] = n
    return out


def mute_cast(cv, ceiling=185.0, desat=0.26):
    """Pull the cast into the room's value and saturation range.

    Measured, not guessed. The rooms are muted by construction: their brightest
    common tone is lum 86, and their most saturated common tone sits at 0.53-0.63.
    The cast was carrying highlights at lum 210 -- 2.4x brighter than anything in
    the room -- and a fez red at saturation 0.74. Drawn side by side the cast
    therefore reads as cut out and laid on top, however clean its silhouette is.
    That is the whole of the "weird design": one layer finished to a different
    palette than the other.

    This caps the sprite's value range at `ceiling` (still above the room's own
    brightest tone, so the cast reads as lit rather than flat) and pulls its
    saturation into the room's band.

    Applied to the finished sheet rather than to the palette entries, because the
    palette is shared with the rooms: muting `bone`, `cream` or `red` in pxlib
    would have flattened the room art along with the cast.
    """
    buf = cv.buf
    f = 1.0 - desat
    for i in range(0, len(buf), 4):
        if buf[i + 3] == 0:
            continue
        r, g, b = buf[i], buf[i + 1], buf[i + 2]
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        if lum > ceiling:
            k = ceiling / lum
            r, g, b = r * k, g * k, b * k
        grey = 0.2126 * r + 0.7152 * g + 0.0722 * b
        buf[i] = int(grey + (r - grey) * f + 0.5)
        buf[i + 1] = int(grey + (g - grey) * f + 0.5)
        buf[i + 2] = int(grey + (b - grey) * f + 0.5)
    return cv


def main():
    os.makedirs(OUT, exist_ok=True)
    cast = _recast()
    n = 0
    for cid, ch in cast.items():
        mute_cast(ch.walk_sheet()).save("%s%s_walk.png" % (OUT, cid))
        n += 1
        for m in MOODS:
            mute_cast(portrait(ch, m)).save("%s%s_portrait_%s.png" % (OUT, cid, m))
            n += 1
    print("%d sprite images (frame %dx%d x%d, portrait 88x88)" % (n, FW, FH, NFRAMES))


if __name__ == "__main__":
    main()
