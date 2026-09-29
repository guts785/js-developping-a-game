"""gen_sprites2 — parametric pixel characters at 2x for «البلغة والجن».

Old sheets were 18x34 frames scaled up 2x (chunky). These are authored at 36x68 with a
jointed rig: hip/knee/ankle and shoulder/elbow/hand chains, a cloth silhouette that sways
with the gait, a left-side rim light, and a contact shadow. 8 frames per sheet
(6 walk + 2 idle). Portraits are 88x88 natively — the dialogue box draws them 1:1.

Run:  python3 gen_sprites2.py
"""
import math
import os
import random

from pxlib import Cv, P, mix

FW, FH = 36, 68          # walk frame size
NFRAMES = 8              # 0..5 walk, 6..7 idle
PW, PH = 88, 88          # portrait

FOOT_Y = 70.0
HIP_Y = 44.0
SHOULDER_Y = 26.0
HEAD_CY = 15.0
THIGH, SHIN = 12.0, 12.0
UPARM, LOARM = 11.0, 11.0
OUT = "../art/chars/"

# classic 6-pose walk: (thighL, shinL, thighR, shinR, armL, armR, bob)
# degrees off vertical, positive swings toward +x (screen right). shin is relative to thigh.
WALK = [
    # Stride scaled to 0.82 of the original. At full reach the trailing leg put its
    # ankle at design x -15.4, and the foot ran off the left edge of the 54px frame --
    # measured: 5 pixels sitting flat on x0 at y90-94, in every contact pose, on 7 of
    # the 8 characters. The walk still reads; the foot stays inside the sprite now.
    (23, -5, -21, -26, -30, 25, 0.0),   # contact, left forward
    (14, -2, -11, -33, -18, 15, 1.0),   # down
    (2, -1, 2, -23, -5, 5, 0.0),        # passing
    (-21, -26, 23, -5, 25, -30, 0.0),   # contact, right forward
    (-11, -33, 14, -2, 15, -18, 1.0),   # down
    (2, -23, 2, -1, 5, -5, 0.0),        # passing
]
IDLE = [
    (5, -2, -4, -2, -4, 4, 0.0),
    (4, -2, -3, -2, -3, 3, 0.6),
]


def thick_line(cv, x0, y0, x1, y1, w, c):
    """Tapered capsule — the limb primitive."""
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        t = i / float(n)
        cv.disc(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, max(1.0, w * 0.5), c)


def limb(cv, x0, y0, x1, y1, w0, w1, c, dark):
    """Two-tone limb with an ink outline so it separates from the garment."""
    # outline pass first — this is what makes limbs read at this size
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        t = i / float(n)
        w = w0 + (w1 - w0) * t
        cv.disc(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, max(1.0, w * 0.5) + 1.0, "outline")
    thick_line(cv, x0, y0, x1, y1, w0, c)
    for i in range(n + 1):
        t = i / float(n)
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        w = w0 + (w1 - w0) * t
        cv.disc(x + w * 0.34, y, max(1.0, w * 0.26), dark)
        cv.disc(x - w * 0.30, y, max(1.0, w * 0.20), mix(c, "lamp", 0.26))


def foot(cv, ax, ay, col, facing=1):
    """A babouche: outline, body, lit toe, dark sole."""
    cv.ellipse(ax + 2.0 * facing, ay + 1.6, 4.6, 2.8, "outline")
    cv.ellipse(ax + 2.0 * facing, ay + 1.0, 3.9, 2.2, col)
    cv.ellipse(ax + 2.0 * facing, ay + 0.2, 3.4, 1.5, mix(col, "slate", 0.45))
    cv.px(ax + 5.0 * facing, ay + 0.4, "bone")
    cv.dither_rect(ax - 2.4 * facing, ay + 2.2, ax + 6.4 * facing, ay + 3.4, "outline", 0.4)


def joint(px, py, ang_deg, ln):
    a = math.radians(ang_deg)
    return px + math.sin(a) * ln, py + math.cos(a) * ln


# ====================================================================== character spec
class Char:
    def __init__(self, cid, name, skin="skin", skin_lit="skin_lit", skin_dark="skin_dark",
                 robe="brown", robe_dark="umber", trim="brass_dark", accent="red",
                 outfit="djellaba", hat="fez", hat_col="red", hair="ink", beard=None,
                 shoes="void", girth=1.0, height=1.0, floats=False, hunch=0.0,
                 prop=None, eyes="ink", stare=False):
        self.cid = cid
        self.name = name
        self.skin = skin
        self.skin_lit = skin_lit
        self.skin_dark = skin_dark
        self.robe = robe
        self.robe_dark = robe_dark
        self.trim = trim
        self.accent = accent
        self.outfit = outfit
        self.hat = hat
        self.hat_col = hat_col
        self.hair = hair
        self.beard = beard
        self.shoes = shoes
        self.girth = girth
        self.height = height
        self.floats = floats
        self.hunch = hunch
        self.prop = prop
        self.eyes = eyes
        self.stare = stare

    # ---------------------------------------------------------------- head
    def draw_head(self, cv, cx, cy, facing=1, mood="neutral"):
        sk, sl, sd = self.skin, self.skin_lit, self.skin_dark
        rx, ry = 5.6, 6.4
        cv.ellipse(cx, cy, rx + 1.2, ry + 1.2, "outline")    # silhouette, not a box
        cv.ellipse(cx, cy, rx, ry, sk)                       # the face
        cv.ellipse(cx - 1.8, cy + 0.4, rx * 0.60, ry * 0.64, sl)
        cv.ellipse(cx + 2.6, cy + 1.2, rx * 0.42, ry * 0.52, sd)
        cv.ellipse(cx, cy + 3.2, rx * 0.84, ry * 0.46, sk)   # jaw
        if self.hair:
            cv.ellipse(cx, cy - 3.1, rx * 1.0, ry * 0.60, self.hair)
            cv.ellipse(cx - 1.6, cy - 3.7, rx * 0.5, ry * 0.28, mix(self.hair, "slate", 0.35))
        if self.beard:
            # A horseshoe, not a blob.
            #
            # The old beard was a single ellipse centred at cy+4.0 with ry*0.52 --
            # spanning cy+0.7 to cy+7.3, which swallowed the nose (cy+1.5) and the
            # mouth (cy+3.2) whole. The mouth was still being drawn, but in
            # skin_dark on top of a dark beard, so it vanished into it: that is
            # exactly why six of the eight heads read as having no mouth at all.
            # Two side lobes leave the mouth and chin open.
            cv.ellipse(cx - 3.8, cy + 5.0, rx * 0.34, ry * 0.42, self.beard)
            cv.ellipse(cx + 3.8, cy + 5.0, rx * 0.34, ry * 0.42, self.beard)
            cv.ellipse(cx, cy + 7.0, rx * 0.66, ry * 0.34, self.beard)
            cv.ellipse(cx, cy + 8.0, rx * 0.44, ry * 0.20, mix(self.beard, "ink", 0.4))
        # Brows, eyes, nose, mouth.
        #
        # Eye sizing here is driven by the 1.5x rasterisation, not by taste. The rig
        # is authored in design units and drawn through a 1.5x proxy, so an eye 1.0
        # design units wide lands on 1.5 native pixels -- which rounds to one pixel
        # on some frames and two on others. That is why the first attempt still
        # measured as a dead slit: at 1.9..2.9 design the eye was 1.5px wide. These
        # values are chosen to clear 2 native pixels on every frame.
        cv.line(cx - 4.1, cy - 3.4, cx - 1.1, cy - 3.0, "ink", 230)
        cv.line(cx + 1.1, cy - 3.0, cx + 4.1, cy - 3.4, "ink", 230)
        for sx in (-1.0, 1.0):
            cv.rect(cx + sx * 1.6, cy - 2.2, cx + sx * 3.2, cy - 1.0, "bone")     # sclera
            cv.rect(cx + sx * 1.6, cy - 1.0, cx + sx * 3.2, cy + 0.4, self.eyes)  # pupil
            cv.px(cx + sx * 2.6, cy - 0.7, "bone")                                # catchlight
        if self.stare:
            cv.px(cx - 3.4, cy - 0.2, "bone")
            cv.px(cx + 3.4, cy - 0.2, "bone")
        # Feature tone, chosen against this character's own skin.
        #
        # A single hard-coded tone cannot work across the cast. `skin_dark` on a
        # mid-brown face reads correctly as a nose shadow, but the jinn's skin is
        # near-black indigo -- a darker nose and mouth vanished into it completely,
        # and simply going LIGHTER still read as a smudge, because a face that dark
        # has no value structure to hang a pale feature on. The jinn gets ember-lit
        # features instead: the same information, and the right idiom for a smoke
        # being that has a fire inside it.
        sk_rgb = P.get(sk, (156, 106, 70))
        sk_lum = 0.2126 * sk_rgb[0] + 0.7152 * sk_rgb[1] + 0.0722 * sk_rgb[2]
        dark_skin = sk_lum < 95
        if dark_skin:
            nose_c = mix("crimson", "bone", 0.34)
            mouth_c = mix("crimson", "bone", 0.48)
            lip_c = mix("crimson", "bone", 0.20)
        else:
            nose_c = mix(sd, "ink", 0.42)
            # On a bearded head a skin-toned mouth line is invisible against the
            # beard, so the tone is taken from the beard instead.
            # The mouth now lands on open skin, because the beard lobes were moved
            # clear of it -- so it wants a DARK line. Taking the tone from the beard
            # instead produced a mid-grey at almost exactly the skin's own luminance
            # (114 against 114), which is the one value guaranteed to disappear. It
            # measured as invisible on rachid, sliman, mokhtar and kamel.
            mouth_c = "outline"
            lip_c = mix(sk, "bone", 0.42)
        # Nose: a bridge pixel over a contiguous base. Three separate px() calls at
        # -1.5 / +0.5 / +2.5 design land 1px each with gaps between them at 1.5x, so
        # the base never resolved into a shape -- it measured as scattered dots. A
        # line makes the base solid.
        cv.px(cx + 0.5, cy + 1.4, nose_c)
        cv.line(cx - 1.0, cy + 2.6, cx + 2.0, cy + 2.6, nose_c, 255)
        # Mouth: a 5px line with a lit lip beneath it. A single thin line kept reading
        # as a shadow rather than a mouth; the pair reads at any zoom.
        cv.line(cx - 2.4, cy + 3.5, cx + 2.4, cy + 3.5, mouth_c, 255)
        cv.line(cx - 1.6, cy + 4.6, cx + 1.6, cy + 4.6, lip_c, 255)
        return cy - ry

    def draw_hat(self, cv, cx, cy):
        if self.hat == "fez":
            cv.rect(cx - 5, cy - 10, cx + 5, cy - 5, self.hat_col)
            # Ink edges BEFORE the crown. The outline() call draws a flat line across
            # the top edge, and it used to run after the crown ellipse -- so the fez
            # read as a flat-topped box with a sliver of dome behind the ink, which
            # looks exactly like a hat cropped by the frame. Drawing the crown last
            # puts the dome back on top of the line.
            cv.outline(cx - 5, cy - 10, cx + 5, cy - 5, "ink")
            cv.dither_rect(cx - 5, cy - 10, cx + 1, cy - 5, "crimson", 0.25)
            cv.ellipse(cx, cy - 5, 5.6, 2.2, self.hat_col)
            # Crown raised from ry 1.8 to 2.6. At 1.8 the dome was 2px deep on a 16px
            # hat -- measured profile y4 w11 / y5 w13 / y6 w16 -- which is a flat top
            # however you draw it. 2.6 gives it a silhouette.
            cv.ellipse(cx, cy - 10, 5, 2.6, mix(self.hat_col, "crimson", 0.5))
            cv.line(cx + 4, cy - 9, cx + 8, cy - 3, "ink", 200)
            cv.disc(cx + 8, cy - 2, 1.6, "ink")
        elif self.hat == "turban":
            # Was hard-coded to bone/cream, so every turban was white -- which left
            # mokhtar sharing fqih's head. Taking the wrap from hat_col (cream when
            # unset) lets the sect leader wear a dark turban without touching fqih.
            base = self.hat_col if self.hat_col else "cream"
            # 0.48, not 0.35: a dark turban's wrap bands were the only thing holding
            # its silhouette against the night background, and at 0.35 the top edge
            # measured as low-contrast.
            lit = mix(base, "bone", 0.48)
            edge = mix(base, "ink", 0.45)
            for i in range(3):
                cv.ellipse(cx, cy - 5 - i * 1.6, 6.4 - i * 0.5, 2.6,
                           lit if i % 2 else base)
                cv.outline(cx - 6, cy - 7 - i * 2, cx + 6, cy - 4 - i * 2, edge)
            cv.ellipse(cx, cy - 9.5, 5.4, 2.4, lit)
            cv.line(cx - 6, cy - 4, cx - 9, cy + 4, base, 200)
        elif self.hat == "hood":
            cv.ellipse(cx, cy - 1, 8.2, 9.0, self.robe)
            cv.ellipse(cx, cy + 1.5, 5.6, 6.4, "void")
            cv.ellipse(cx, cy + 2, 5.2, 6.0, mix(self.skin_dark, "ink", 0.3))
            cv.ellipse(cx, cy + 3, 4.6, 5.2, self.skin)
            cv.dither_rect(cx - 8, cy - 8, cx + 8, cy + 2, self.robe_dark, 0.35)
        elif self.hat == "scarf":
            cv.ellipse(cx, cy - 1.5, 8.0, 8.4, self.hat_col)
            cv.ellipse(cx, cy + 2.5, 5.4, 5.6, mix(self.hat_col, "ink", 0.25))
            cv.ellipse(cx, cy + 3.2, 4.8, 5.0, self.skin)
            cv.dither_rect(cx - 8, cy - 8, cx + 8, cy, "crimson", 0.2)
            cv.line(cx - 7, cy + 4, cx - 9, cy + 13, self.hat_col, 230)
        elif self.hat == "cap":
            cv.ellipse(cx, cy - 5, 6.0, 3.0, "slate")
            cv.outline(cx - 6, cy - 8, cx + 6, cy - 2, "ink")

    # ---------------------------------------------------------------- body
    def draw_body(self, cv, cx, y_top, hem_y, sway=0.0, girth=1.0):
        """The garment silhouette: shoulders → hem, hem drifting with the gait."""
        sw = 6.2 * girth
        hem = 7.7 * girth
        pts = [
            (cx - sw, y_top),
            (cx + sw, y_top),
            (cx + hem + sway, hem_y),
            (cx - hem + sway, hem_y),
        ]
        cv.poly([(cx - sw - 1.2, y_top - 1.2), (cx + sw + 1.2, y_top - 1.2),
                 (cx + hem + sway + 1.2, hem_y + 1.2), (cx - hem + sway - 1.2, hem_y + 1.2)], "ink")
        cv.poly(pts, self.robe)
        # vertical cloth folds
        for i in range(-2, 3):
            fx = cx + i * (hem * 0.40)
            cv.line(fx + sway * 0.6, y_top + 3, fx * 0.9 + cx * 0.1 + sway, hem_y - 1,
                    self.robe_dark, 120)
        # lit left edge + shaded right side
        cv.line(cx - sw + 0.5, y_top, cx - hem + sway + 0.5, hem_y, mix(self.robe, "lamp", 0.32), 170)
        cv.dither_rect(cx + 2.5, y_top, cx + hem + sway, hem_y, self.robe_dark, 0.32)
        # collar + sash
        cv.line(cx - sw + 1, y_top + 1, cx, y_top + 4.5, self.trim, 210)
        cv.line(cx + sw - 1, y_top + 1, cx, y_top + 4.5, self.trim, 210)
        cv.rect(cx - sw * 0.85, y_top + 7, cx + sw * 0.85, y_top + 10, self.trim)
        cv.dither_rect(cx - sw * 0.85, y_top + 7, cx + sw * 0.85, y_top + 8, "bone", 0.22)
        return hem_y

    def draw_apron(self, cv, cx, y_top, hem_y, girth=1.0):
        cv.poly([(cx - 4.6, y_top + 4), (cx + 4.6, y_top + 4),
                 (cx + 6.4, hem_y - 4), (cx - 6.4, hem_y - 4)], "bone")
        cv.dither_rect(cx - 5, y_top + 5, cx + 6, hem_y - 5, "clay", 0.16)
        for i in range(7):
            rnd = random.Random(int(cx) + i * 31)
            sx = cx + rnd.randint(-6, 6)
            sy = y_top + rnd.randint(8, int(hem_y - y_top) - 6)
            cv.dither_rect(sx - 2, sy - 1, sx + 3, sy + 2, "red_dark", 0.5)
        cv.line(cx - 4.6, y_top + 4, cx + 4.6, y_top + 4, "ink", 220)

    def draw_prop(self, cv, cx, y, facing=1):
        if self.prop == "cane":
            cv.line(cx + 8 * facing, y - 30, cx + 9 * facing, y, "leather", 240)
            cv.disc(cx + 9 * facing, y - 31, 2, "brass")
        elif self.prop == "tray":
            cv.ellipse(cx - 9 * facing, y - 26, 8, 2.4, "brass")
            cv.disc(cx - 9 * facing, y - 28, 2, "clay")
        elif self.prop == "lantern":
            cv.line(cx - 9 * facing, y - 34, cx - 9 * facing, y - 26, "brass_dark")
            cv.poly([(cx - 9 * facing, y - 26), (cx - 4 * facing, y - 20),
                     (cx - 9 * facing, y - 14), (cx - 14 * facing, y - 20)], "brass")
            cv.disc(cx - 9 * facing, y - 20, 2, "flame")
            cv.light_pool(cx - 9 * facing, y - 20, 26, "lamp", 0.3)
        elif self.prop == "herbs":
            cv.poly([(cx - 8, y - 30), (cx - 2, y - 30), (cx - 3, y - 18), (cx - 9, y - 20)], "olive")

    # ---------------------------------------------------------------- one frame
    def frame(self, cv, ox, idx):
        pose = WALK[idx] if idx < 6 else IDLE[idx - 6]
        tL, sL, tR, sR, aL, aR, bob = pose
        bob *= 1.7                      # 1px of bob is invisible at 2x; make it read
        cx = ox + FW * 0.5
        g = self.girth
        ground = FOOT_Y
        hip = HIP_Y + bob - (1.0 - self.height) * 6
        sh = SHOULDER_Y + bob - (1.0 - self.height) * 6 + self.hunch
        head_cy = HEAD_CY + bob - (1.0 - self.height) * 6 + self.hunch * 1.4
        facing = 1

        # contact shadow
        cv.ellipse(cx, ground + 1, 9.5 * g, 2.6, "void", 90)
        cv.ellipse(cx, ground + 1, 6.5 * g, 1.6, "void", 120)

        if self.floats:
            self._frame_float(cv, cx, idx, bob)
            return

        # --- legs (back leg first so the front overlaps it)
        for (tt, ss, col) in ((tR, sR, self.robe_dark), (tL, sL, self.robe)):
            kx, ky = joint(cx, hip, tt, THIGH)
            ax, ay = joint(kx, ky, tt + ss, SHIN)
            limb(cv, cx, hip, kx, ky, 5.4 * g, 4.6 * g, col, self.robe_dark)
            limb(cv, kx, ky, ax, ay, 4.6 * g, 3.8 * g, col, self.robe_dark)
            foot(cv, ax, ay, mix(self.shoes, "slate", 0.3))
        # --- garment
        hem_y = ground - 16 + (1.0 - self.height) * 4
        sway = (tL - tR) * 0.12
        self.draw_body(cv, cx, sh - 1, hem_y, sway, g)
        if self.outfit == "apron":
            self.draw_apron(cv, cx, sh - 1, hem_y - 2, g)
        # --- arms (far arm behind, near arm in front) — tone-shifted so sleeves read
        #
        # Three faults fixed here, all measured rather than guessed.
        #
        # 1. Both arms used to originate at `cx`, the torso's centre line, so they
        #    emerged from the sternum and read as hanging off the neck. They now
        #    start at a real shoulder, offset laterally by 3.4g.
        # 2. The sleeves were 4.6g and 3.8g against a torso half-width of ~4.2g --
        #    as thick as the body, with no taper, which is why they read as
        #    bloated columns rather than sleeves. Now they taper 4.0g -> 3.2g ->
        #    2.0g.
        # 3. The forearm ended at 3.2g (4.8px at 1x) while the hand disc was only
        #    1.9g (2.85px). The sleeve's own end cap was wider than the hand, so
        #    it swallowed it whole -- which is why seven of the eight characters
        #    appeared to have no hands at all. The cuff is now narrower than the
        #    hand, and the hand is bigger and has a thumb.
        for (aa, col, side) in ((aR, mix(self.robe, "ink", 0.34), -1.0),
                                (aL, mix(self.robe, "lamp", 0.16), 1.0)):
            sx = cx + side * 3.4 * g
            ex, ey = joint(sx, sh + 3, aa, UPARM)
            hx, hy = joint(ex, ey, aa * 1.1, LOARM)
            limb(cv, sx, sh + 3, ex, ey, 4.0 * g, 3.2 * g, col, self.robe_dark)
            limb(cv, ex, ey, hx, hy, 3.0 * g, 2.0 * g, col, self.robe_dark)
            # Hand. Flagged as a stump three times now, and the reason is size: at
            # r2.1 the whole hand is 4x4 native pixels, so two finger notches plus a
            # thumb is more detail than the space can hold and it collapses straight
            # back into a blob. Silhouette beats interior detail at this scale -- a
            # bigger palm, a thumb that genuinely breaks the outline, and a dark rim
            # so the hand separates from the sleeve even when both are tan (rachid,
            # fqih and kamel were unreadable for exactly that reason).
            cv.disc(hx, hy - 0.4 * g, 3.4 * g, "outline")
            cv.disc(hx, hy - 0.4 * g, 2.9 * g, self.skin_dark)
            cv.disc(hx, hy - 0.4 * g, 2.5 * g, self.skin)
            cv.disc(hx - 0.6, hy - 1.1 * g, 1.2, self.skin_lit)
            cv.disc(hx - side * 3.1, hy + 0.3, 2.1, "outline")   # thumb breaks the silhouette
            cv.disc(hx - side * 3.1, hy + 0.3, 1.6, self.skin)
            cv.disc(hx - side * 3.1, hy - 0.3, 0.9, self.skin_lit)
        self.draw_prop(cv, cx, ground, facing)
        # --- head
        top = self.draw_head(cv, cx, head_cy, facing)
        self.draw_hat(cv, cx, head_cy)
        # neck
        cv.rect(cx - 2, head_cy + 5, cx + 2, sh + 1, self.skin_dark)
        cv.dither_rect(cx - 2, head_cy + 5, cx + 2, sh, "ink", 0.3)

    def _frame_float(self, cv, cx, idx, bob):
        """The jinn: no legs, a smoke column that thins to a wisp and drifts."""
        t = idx / float(NFRAMES)
        lift = 3.0 + math.sin(t * math.pi * 2) * 2.0
        hem = FOOT_Y - 12
        sh = SHOULDER_Y + lift
        # smoke tail
        for i in range(16):
            yy = hem + i * 1.6
            w = 5.0 * (1.0 - i / 16.0) + 1.0
            drift = math.sin(t * 6.28 + i * 0.5) * 2.4
            cv.disc(cx + drift, yy, w, mix(self.robe, "indigo", 0.3 + i * 0.03), 220)
        self.draw_body(cv, cx, sh - 2, hem, math.sin(t * 6.28) * 2.0, self.girth)
        # The body's embers, as a gradient rather than a flat speckle. A uniform
        # dither_rect at 0.12 scattered accent pixels evenly over the torso, which
        # read as static rather than as a glowing creature -- the dots have to thin
        # out as the smoke rises away from the head to read as light on a form.
        cv.dither_grad_v(cx - 10, sh - 4, cx + 10, hem, self.accent, 0.24, 0.03)
        # arms as tendrils. Reach trimmed from (5 + i*1.4) to (4 + i*0.9): at the old
        # spread the last tendril landed 18.2 design px from a centre that sits at
        # 18 design px, so the jinn's silhouette measured x0..x53 -- both frame edges,
        # flat-clipped -- on a 54px sprite. That is what made it read as a glitch.
        for sgn in (-1, 1):
            for i in range(9):
                yy = sh + 4 + i * 2.2
                xx = cx + sgn * (4 + i * 0.9) + math.sin(t * 6.28 + i * 0.6) * 1.6
                cv.disc(xx, yy, max(1.0, 2.6 - i * 0.22), self.robe, 230)
        top = self.draw_head(cv, cx, HEAD_CY + lift, 1)
        # glowing eyes
        cv.disc(cx - 2.2, HEAD_CY + lift - 0.5, 1.6, "crimson")
        cv.disc(cx + 1.2, HEAD_CY + lift - 0.5, 1.6, "crimson")
        # The aura. This was radius 18 in a 36-wide design frame, i.e. a 27px
        # dithered cloud centred on the head of a 54px sprite -- it clipped flat at
        # both side edges AND the top, so the jinn's measured silhouette spanned the
        # entire frame width and its top row carried 12 stray pixels. Read as glitch
        # noise, not as an aura. At radius 10 it hugs the head instead.
        # The aura used to be centred on the head at radius 10 -- but the head's own
        # radius is 10.2px at native scale, so the crimson pool landed exactly on the
        # silhouette and drew a CLOSED RED RING around the face. On screen it read as
        # a dotted outline competing with the eyes, and it was the single reason the
        # head judged as a glitch rather than a face. Centred on the chest it still
        # reads as the creature's inner fire, which is what it was always for.
        cv.light_pool(cx, sh + 9, 10, "crimson", 0.28)
        # Horns. 1px of `ink` on a night background is not a horn, it is a smudge --
        # measured as stray noise. A lighter core with a dark inner edge holds the
        # silhouette without losing the supernatural read.
        for sgn in (-1, 1):
            cv.line(cx + sgn * 5, HEAD_CY + lift - 4, cx + sgn * 8, HEAD_CY + lift - 12,
                    "ink", 255)
            cv.line(cx + sgn * 6, HEAD_CY + lift - 5, cx + sgn * 9, HEAD_CY + lift - 13,
                    mix(self.robe, "bone", 0.30), 235)

    # ---------------------------------------------------------------- sheet
    def walk_sheet(self):
        cv = Cv(FW * NFRAMES, FH, None)   # transparent, see gen_sprites3
        for i in range(NFRAMES):
            self.frame(cv, i * FW, i)
        return cv


# ====================================================================== portraits
def portrait(ch, mood):
    """88x88 bust: panel, shoulders, head, expression. Drawn 1:1 for the dialogue box."""
    cv = Cv(PW, PH)
    cv.rect(0, 0, PW, PH, "void")
    # panel backdrop — grain, not an ordered-dither grid (that read as a starfield)
    cv.rect(0, 0, PW, PH, mix("void", "indigo", 0.5))
    cv.noise(0, 0, PW, PH, 0.4, seed=5, scale=13, cols=("indigo", "slate"))
    cv.rect(0, 0, PW, 4, "void")
    cv.rect(0, PH - 6, PW, PH, "void")
    cv.dither_rect(0, 4, PW, 14, "void", 0.35)
    cv.dither_rect(0, PH - 16, PW, PH - 6, "void", 0.4)
    cv.light_pool(PW * 0.5, PH * 0.44, 46, "lamp" if mood != "dead" else "sky_dust", 0.32)

    cx = PW * 0.5
    sk, sl, sd = ch.skin, ch.skin_lit, ch.skin_dark
    if mood == "dead":
        sk, sl, sd = "grey", "bone", "slate"

    # shoulders
    cv.poly([(cx - 34, PH), (cx - 22, PH - 26), (cx + 22, PH - 26), (cx + 34, PH)], ch.robe)
    cv.dither_rect(cx + 6, PH - 28, cx + 34, PH, ch.robe_dark, 0.3)
    cv.line(cx - 22, PH - 26, cx - 34, PH, mix(ch.robe, "lamp", 0.3), 170)
    cv.poly([(cx - 8, PH - 26), (cx + 8, PH - 26), (cx + 12, PH), (cx - 12, PH)], mix(ch.robe, "ink", 0.3))
    cv.line(cx - 22, PH - 26, cx - 8, PH - 26, ch.trim, 220)
    cv.line(cx + 8, PH - 26, cx + 22, PH - 26, ch.trim, 220)
    if ch.outfit == "apron":
        cv.poly([(cx - 14, PH - 24), (cx + 14, PH - 24), (cx + 20, PH), (cx - 20, PH)], "bone")
        for i in range(6):
            rnd = random.Random(i * 17 + 3)
            sx = cx + rnd.randint(-16, 16)
            sy = PH - 22 + rnd.randint(0, 20)
            cv.dither_rect(sx - 3, sy - 2, sx + 4, sy + 3, "red_dark", 0.45)

    # neck
    cv.rect(cx - 9, PH - 40, cx + 9, PH - 22, sd)
    cv.dither_rect(cx - 9, PH - 26, cx + 9, PH - 22, "ink", 0.3)
    cv.rect(cx - 9, PH - 40, cx - 3, PH - 22, sk)

    # head
    hy = PH - 54
    cv.ellipse(cx, hy, 20, 24, sk)
    cv.ellipse(cx - 7, hy - 4, 12, 15, sl)
    cv.ellipse(cx + 8, hy + 3, 10, 15, sd)
    cv.dither_rect(cx - 20, hy - 24, cx - 10, hy + 24, "lamp", 0.06)
    # cheekbones + jaw
    cv.dither_rect(cx - 16, hy + 10, cx - 6, hy + 20, sd, 0.3)
    cv.dither_rect(cx + 6, hy + 10, cx + 16, hy + 20, sd, 0.4)

    if ch.hair:
        hc = "grey" if mood == "dead" else ch.hair
        cv.ellipse(cx, hy - 14, 20, 12, hc)
        cv.dither_rect(cx - 20, hy - 24, cx + 20, hy - 8, mix(hc, "ink", 0.4), 0.3)

    # hat / headwear on top of everything
    if ch.hat == "fez":
        cv.rect(cx - 15, hy - 34, cx + 15, hy - 18, ch.hat_col)
        cv.ellipse(cx, hy - 18, 16, 5, mix(ch.hat_col, "crimson", 0.4))
        cv.ellipse(cx, hy - 34, 15, 5, mix(ch.hat_col, "crimson", 0.6))
        cv.dither_rect(cx - 15, hy - 34, cx - 4, hy - 18, "crimson", 0.3)
        cv.outline(cx - 15, hy - 34, cx + 15, hy - 18, "ink")
        cv.line(cx + 13, hy - 33, cx + 22, hy - 20, "ink", 200)
        cv.disc(cx + 22, hy - 19, 3, "ink")
    elif ch.hat == "turban":
        for i in range(3):
            cv.ellipse(cx, hy - 22 - i * 5, 19 - i * 2, 7, "bone" if i % 2 else "cream")
            cv.outline(cx - 19, hy - 26 - i * 5, cx + 19, hy - 18 - i * 5, "clay")
    elif ch.hat == "hood":
        cv.ellipse(cx, hy - 4, 26, 30, ch.robe)
        cv.ellipse(cx, hy, 19, 23, mix(ch.robe, "ink", 0.5))
        cv.ellipse(cx, hy + 1, 16, 19, sk)
        cv.ellipse(cx - 6, hy - 4, 7, 9, sl)
        cv.dither_rect(cx - 26, hy - 34, cx + 26, hy + 6, ch.robe_dark, 0.3)
        cv.outline(cx - 26, hy - 34, cx + 26, hy + 26, "ink")
    elif ch.hat == "scarf":
        cv.ellipse(cx, hy - 6, 25, 27, ch.hat_col)
        cv.ellipse(cx, hy, 19, 21, mix(ch.hat_col, "ink", 0.35))
        cv.ellipse(cx, hy + 1, 16, 18, sk)
        cv.ellipse(cx - 6, hy - 4, 7, 9, sl)
        cv.dither_rect(cx - 25, hy - 32, cx + 25, hy + 2, "crimson", 0.22)
        cv.line(cx - 22, hy + 16, cx - 28, PH - 20, ch.hat_col, 230)
        cv.line(cx + 22, hy + 16, cx + 28, PH - 20, ch.hat_col, 230)
    elif ch.hat == "cap":
        cv.ellipse(cx, hy - 14, 21, 9, "slate")
        cv.rect(cx - 21, hy - 18, cx + 21, hy - 12, "slate")

    # ---- beard first (now on top of any hood/scarf), then the face
    if ch.beard:
        bc = "grey" if mood == "dead" else ch.beard
        cv.ellipse(cx, hy + 17, 20, 14, bc)
        cv.ellipse(cx, hy + 20, 16, 10, mix(bc, "ink", 0.3))
        cv.dither_rect(cx - 19, hy + 13, cx + 19, hy + 30, mix(bc, "ink", 0.5), 0.28)
        cv.ellipse(cx - 15, hy - 4, 9, 11, bc)
        cv.ellipse(cx + 15, hy - 4, 9, 11, bc)
        cv.dither_rect(cx - 12, hy + 8, cx + 12, hy + 14, mix(bc, "bone", 0.3), 0.2)
    # ---- expression
    ey = hy - 2
    brow = hy - 11
    mouth_y = hy + 15
    for ex in (cx - 9, cx + 9):
        cv.ellipse(ex, ey, 6.0, 4.6, "ink")          # socket
        cv.ellipse(ex, ey, 5.2, 3.9, "bone")         # sclera
        cv.ellipse(ex + 1, ey, 3.0, 3.2, ch.eyes)    # iris
        cv.ellipse(ex + 1, ey, 1.6, 1.8, "void")     # pupil
        cv.px(ex - 0.5, ey - 1.5, "bone")            # catchlight
        cv.line(ex - 5, ey - 4, ex + 5, ey - 4, mix(sd, "ink", 0.4), 200)  # lid
    if mood == "dead":
        for ex in (cx - 9, cx + 9):
            cv.line(ex - 5, ey - 4, ex + 5, ey + 4, "ink", 220)
            cv.line(ex + 5, ey - 4, ex - 5, ey + 4, "ink", 220)
    if mood == "angry":
        cv.line(cx - 15, brow, cx - 3, brow + 4, "ink", 230)
        cv.line(cx + 15, brow, cx + 3, brow + 4, "ink", 230)
        cv.dither_rect(cx - 16, ey - 4, cx - 2, ey + 4, "crimson", 0.16)
        cv.dither_rect(cx + 2, ey - 4, cx + 16, ey + 4, "crimson", 0.16)
        cv.ellipse(cx, mouth_y, 8, 3, "ink")
        cv.rect(cx - 8, mouth_y - 1, cx + 8, mouth_y, sd)
    elif mood == "sad":
        cv.line(cx - 15, brow + 3, cx - 3, brow - 1, "ink", 220)
        cv.line(cx + 15, brow + 3, cx + 3, brow - 1, "ink", 220)
        cv.ellipse(cx, mouth_y + 1, 7, 2.4, "ink")
        cv.ellipse(cx - 10, ey + 5, 2, 1.6, "azure")
    elif mood == "grin":
        cv.line(cx - 15, brow - 1, cx - 3, brow + 2, "ink", 220)
        cv.line(cx + 15, brow - 1, cx + 3, brow + 2, "ink", 220)
        cv.ellipse(cx, mouth_y - 1, 11, 6, "ink")
        cv.rect(cx - 9, mouth_y - 4, cx + 9, mouth_y - 2, "bone")
        for i in range(-2, 3):
            cv.vline(cx + i * 4, mouth_y - 4, mouth_y - 2, "ink")
    elif mood == "talk":
        cv.line(cx - 15, brow - 1, cx - 3, brow, "ink", 220)
        cv.line(cx + 15, brow - 1, cx + 3, brow, "ink", 220)
        cv.ellipse(cx, mouth_y, 6.5, 5.0, "ink")
        cv.ellipse(cx, mouth_y + 1, 4.0, 2.6, "crimson")
        cv.rect(cx - 6, mouth_y - 5, cx + 6, mouth_y - 4, "bone")
    else:
        cv.line(cx - 15, brow, cx - 3, brow, "ink", 200)
        cv.line(cx + 15, brow, cx + 3, brow, "ink", 200)
        cv.line(cx - 7, mouth_y, cx + 7, mouth_y, "ink", 210)

    cv.dither_rect(cx - 3, hy + 2, cx + 4, hy + 10, sd, 0.28)   # nose bridge shadow
    cv.px(cx + 3, hy + 8, sd)
    cv.px(cx + 4, hy + 8, mix(sd, "ink", 0.5))
    cv.dither_rect(cx - 14, hy + 12, cx + 14, hy + 22, sd, 0.2)  # jaw shade
    cv.line(cx - 20, hy - 20, cx - 20, hy + 18, "lamp", 60)      # rim light, left
    cv.dither_rect(cx + 12, hy - 22, cx + 20, hy + 22, "ink", 0.28)

    if ch.cid == "jinn":
        cv.dither_rect(0, 0, PW, PH, "crimson", 0.1)
        cv.light_pool(cx, hy, 30, "crimson", 0.25)

    # frame
    cv.outline(0, 0, PW - 1, PH - 1, "brass_dark")
    cv.dither_rect(0, 0, PW - 1, 3, "ink", 0.4)
    cv.dither_rect(0, PH - 4, PW - 1, PH - 1, "ink", 0.4)
    return cv


# ====================================================================== cast
CHARS = {
    "rachid": Char("rachid", "المفتش رشيد", skin="skin", skin_lit="skin_lit", skin_dark="skin_dark",
                   robe="bone", robe_dark="clay", trim="brass_dark", accent="red",
                   outfit="djellaba", hat="fez", hat_col="red", hair="ink", beard="ink",
                   shoes="leather", girth=1.0, height=1.0, prop=None),
    "hmidou": Char("hmidou", "حميدو", skin="skin_lit", skin_lit="bone", skin_dark="skin",
                   robe="azure", robe_dark="majorelle", trim="bone", accent="bone",
                   outfit="tunic", hat=None, hat_col=None, hair="ink", beard=None,
                   shoes="leather", girth=0.9, height=0.92, stare=True),
    "sliman": Char("sliman", "سليمان", skin="skin_dark", skin_lit="skin", skin_dark="umber",
                   robe="grey", robe_dark="slate", trim="bone", accent="red_dark",
                   outfit="apron", hat=None, hat_col=None, hair=None, beard="ink",
                   shoes="leather", girth=1.22, height=1.0),
    "zahra": Char("zahra", "الزهرة", skin="skin", skin_lit="skin_lit", skin_dark="skin_dark",
                  robe="jade", robe_dark="olive", trim="gold", accent="crimson",
                  outfit="shawl", hat="scarf", hat_col="crimson", hair=None, beard=None,
                  shoes="umber", girth=1.02, height=0.96, hunch=1.5, prop="herbs"),
    "fqih": Char("fqih", "الفقيه", skin="skin_dark", skin_lit="skin", skin_dark="umber",
                 robe="bone", robe_dark="clay", trim="brass_dark", accent="jade",
                 outfit="hooded", hat="hood", hat_col=None, hair=None, beard="grey",
                 shoes="umber", girth=1.05, height=1.06, prop="cane"),
    "mokhtar": Char("mokhtar", "الأخ المختار", skin="skin_lit", skin_lit="bone", skin_dark="skin",
                    # Coat lifted off `ink` to `indigo`. Robe, hair, beard and shoes
                    # were all ink/void -- within 8 levels of each other -- so the whole
                    # figure collapsed into one black mass and measured only 26 distinct
                    # colours against rachid's 42. Indigo/ink now separates the coat from
                    # the beard and the hair the way the other seven read.
                    robe="indigo", robe_dark="ink", trim="crimson", accent="crimson",
                    # Headwear is the silhouette, not the colour. A fez in a different
                    # colour still measured as "a recoloured rachid" -- same face, same
                    # beard, same hat shape. A turban separates the two on outline; it
                    # is drawn dark so he does not become fqih's twin. (`scarf` was
                    # tried first and read as a woman's headscarf on a robed figure.)
                    outfit="coat", hat="turban", hat_col="indigo", hair="ink", beard="ink",
                    shoes="void", girth=0.98, height=1.05, stare=True),
    "kamel": Char("kamel", "كمال", skin="skin", skin_lit="skin_lit", skin_dark="skin_dark",
                  robe="bone", robe_dark="clay", trim="jade", accent="azure",
                  outfit="djellaba", hat="cap", hat_col=None, hair="ink", beard=None,
                  shoes="umber", girth=0.95, height=0.98),
    "jinn": Char("jinn", "الجن", skin="grey", skin_lit="slate_lit", skin_dark="void",
                 robe="indigo", robe_dark="void", trim="crimson", accent="crimson",
                 outfit="smoke", hat=None, hat_col=None, hair=None, beard=None,
                 shoes=None, girth=1.1, height=1.0, floats=True, eyes="crimson"),
}
# The jinn is the one head that needs its own value structure. At indigo (lum 33)
# over void (lum 10) the entire head lived inside a 23-level luminance range --
# there was no ramp to hang a nose or mouth on, which is why it kept judging as a
# blob no matter how the features were coloured. Lifting the base to sky_night and
# the highlight to azure gives it a real 23..88 ramp while staying night-dark.
CHARS["jinn"].skin = "sky_night"
CHARS["jinn"].skin_lit = "azure"
CHARS["jinn"].skin_dark = "night"

MOODS = ["neutral", "talk", "angry", "sad", "grin", "dead"]


def main():
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for cid, ch in CHARS.items():
        ch.walk_sheet().save("%s%s_walk.png" % (OUT, cid))
        n += 1
        for m in MOODS:
            portrait(ch, m).save("%s%s_portrait_%s.png" % (OUT, cid, m))
            n += 1
    print("%d sprite images (frame %dx%d x%d, portrait %dx%d)" % (n, FW, FH, NFRAMES, PW, PH))


if __name__ == "__main__":
    main()
