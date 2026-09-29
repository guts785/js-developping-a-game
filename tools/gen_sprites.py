"""gen_sprites — parametric pixel-art characters, walk cycles and portraits."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artlib import Canvas, P, c, ascii_sprite, quantize
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art", "chars")

SKINS = {
    "olive":  (196, 154, 108),
    "tan":    (170, 122, 82),
    "brown":  (128, 88, 58),
    "dark":   (92, 62, 42),
    "pale":   (222, 190, 152),
}
HAIR = {
    "black": (28, 22, 26),
    "grey":  (176, 168, 160),
    "white": (226, 220, 210),
    "brown": (74, 48, 34),
}


# ---------------------------------------------------------------- character
class Char:
    """A parametric side-view pixel character with a 4-frame walk cycle."""

    def __init__(self, name, skin="olive", robe="cream", robe2="sand", accent="blood",
                 hat=None, hat_col="blood", beard=None, hijab=None, scale_h=1.0,
                 hair="black", hunch=0.0, tall=False):
        self.name = name
        self.skin = SKINS.get(skin, skin) if isinstance(skin, str) else skin
        self.robe = robe
        self.robe2 = robe2
        self.accent = accent
        self.hat = hat                    # None | 'fez' | 'hood' | 'turban' | 'cap'
        self.hat_col = hat_col
        self.beard = beard                # None | 'full' | 'stubble' | 'goatee'
        self.hijab = hijab                # None | colour key
        self.hair = HAIR.get(hair, hair) if isinstance(hair, str) else hair
        self.hunch = hunch
        self.tall = tall

    # ---------------------------------------------------------- geometry
    def build(self, frame=0, walking=False):
        """frame 0..3 ; returns Canvas 18x34"""
        w, h = 18, 34
        cv = Canvas(w, h, (0, 0, 0, 0))
        cx = 9
        top = 3 if self.tall else 5
        head_h = 8
        head_w = 8
        body_top = top + head_h
        body_bot = body_top + 11
        leg_bot = 33

        bob = 0
        if walking:
            bob = [0, -1, 0, 1][frame % 4]
        body_top += bob
        body_bot += bob
        top += bob

        # ---- legs / babouches
        if walking:
            swings = [(1, -1), (0, 0), (-1, 1), (0, 0)]
            lx, rx = swings[frame % 4]
        else:
            lx = rx = 0
        leg_col = "clay"
        # left leg
        cv.rect(cx - 4, body_bot, cx - 2, leg_bot - 3 + max(0, -lx * 2), leg_col)
        cv.rect(cx - 5, leg_bot - 2 + max(0, -lx * 2), cx - 1, leg_bot, "ochre")   # babouche
        cv.px(cx - 5, leg_bot, "ink")
        # right leg
        cv.rect(cx + 2, body_bot, cx + 4, leg_bot - 3 + max(0, lx * 2), leg_col)
        cv.rect(cx + 1, leg_bot - 2 + max(0, lx * 2), cx + 5, leg_bot, "gold")
        cv.px(cx + 5, leg_bot, "ink")

        # ---- djellaba / robe (trapezoid)
        for y in range(body_top, body_bot + 1):
            f = (y - body_top) / max(1, body_bot - body_top)
            half = int(4 + f * 3.2)
            if self.hunch:
                half += int(self.hunch * 2)
            cv.rect(cx - half, y, cx + half, y, self.robe)
            cv.px(cx - half, y, self.robe2)
            cv.px(cx + half, y, self.robe2)
        # accent trim down the middle + hem
        cv.rect(cx - 1, body_top, cx, body_bot, self.accent)
        cv.rect(cx - 5, body_bot - 1, cx + 5, body_bot, self.accent)
        # hood collar
        cv.rect(cx - 4, body_top, cx + 4, body_top + 1, self.robe2)

        # ---- arms
        if walking:
            aswing = [-2, 0, 2, 0][frame % 4]
        else:
            aswing = 0
        cv.rect(cx - 5, body_top + 2, cx - 4, body_top + 7 + aswing, self.robe)
        cv.rect(cx + 4, body_top + 2, cx + 5, body_top + 7 - aswing, self.robe)
        cv.rect(cx - 5, body_top + 7 + aswing, cx - 4, body_top + 8 + aswing, self.skin)
        cv.rect(cx + 4, body_top + 7 - aswing, cx + 5, body_top + 8 - aswing, self.skin)

        # ---- head
        cv.rect(cx - head_w // 2, top, cx + head_w // 2 - 1, top + head_h - 1, self.skin)
        cv.px(cx - head_w // 2, top, (0, 0, 0, 0))
        cv.px(cx + head_w // 2 - 1, top + head_h - 1, (0, 0, 0, 0))
        # ear
        cv.px(cx + head_w // 2 - 1, top + 4, self.skin)
        # eye + brow
        cv.px(cx + 1, top + 3, "ink")
        cv.px(cx + 2, top + 3, "ink")
        cv.px(cx + 2, top + 2, self.hair)
        # mouth
        cv.px(cx + 2, top + 6, (120, 60, 50, 255))
        # nose
        cv.px(cx + 3, top + 4, (max(0, self.skin[0] - 30), max(0, self.skin[1] - 30), max(0, self.skin[2] - 30), 255))

        # ---- beard
        if self.beard == "full":
            cv.rect(cx - 3, top + 5, cx + 3, top + head_h + 2, self.hair)
            cv.rect(cx - 2, top + 5, cx + 2, top + 6, self.skin)
            cv.px(cx + 2, top + 6, (120, 60, 50, 255))
        elif self.beard == "stubble":
            cv.dither(cx - 3, top + 5, cx + 3, top + head_h, "ink", 0.35, 120, seed=3)
        elif self.beard == "goatee":
            cv.rect(cx, top + head_h, cx + 2, top + head_h + 2, self.hair)

        # ---- headwear
        if self.hijab:
            col = self.hijab
            cv.rect(cx - 4, top - 1, cx + 3, top + head_h + 1, col)
            cv.rect(cx - 3, top + 2, cx + 3, top + head_h, self.skin)
            cv.px(cx + 1, top + 3, "ink")
            cv.px(cx + 2, top + 3, "ink")
            cv.rect(cx - 4, top + head_h, cx + 4, body_top + 2, col)
            cv.px(cx + 3, top + 5, self.skin)
        elif self.hat == "fez":
            cv.rect(cx - 3, top - 5, cx + 2, top, self.hat_col)
            cv.rect(cx - 3, top - 1, cx + 2, top, (0, 0, 0, 0))
            cv.line(cx - 3, top - 5, cx + 2, top - 5, "ink")
            cv.px(cx - 1, top - 4, "ink")
            for t in range(0, 5, 2):
                cv.line(cx - 1 - t, top - 6, cx - 1 + t, top - 6, "ink")
        elif self.hat == "hood":
            cv.rect(cx - 4, top - 2, cx + 3, top + 6, self.hat_col)
            cv.rect(cx - 3, top + 1, cx + 3, top + 6, "void")
            cv.px(cx + 1, top + 3, "red")
            cv.px(cx + 2, top + 3, "red")
        elif self.hat == "turban":
            cv.rect(cx - 4, top - 4, cx + 3, top + 1, self.hat_col)
            cv.line(cx - 4, top - 2, cx + 3, top - 3, "cream")
            cv.line(cx - 4, top, cx + 3, top - 1, "cream")
        elif self.hat == "cap":
            cv.rect(cx - 3, top - 2, cx + 3, top, self.hat_col)
            cv.rect(cx - 3, top - 1, cx + 6, top, self.hat_col)
        else:
            # plain hair
            cv.rect(cx - 4, top - 1, cx + 3, top + 1, self.hair)
            cv.px(cx + 3, top + 1, self.hair)
        return cv

    def frames(self, walking=True):
        if walking:
            return [self.build(i, True) for i in range(4)]
        return [self.build(0, False), self.build(0, False)]

    # ---------------------------------------------------------- portrait
    def portrait(self, mood="neutral", size=44):
        cv = Canvas(size, size, "shadow")
        cv.grad_v(0, 0, size - 1, size - 1, "plum", "shadow")
        for i in range(30):
            rnd = random.Random(i * 7)
            cv.px(rnd.randint(0, size - 1), rnd.randint(0, size - 1), "mauve", 60)
        cx = size // 2
        # shoulders
        cv.rect(6, size - 12, size - 7, size - 1, self.robe)
        cv.rect(cx - 2, size - 12, cx + 1, size - 1, self.accent)
        cv.rect(6, size - 12, size - 7, size - 11, self.robe2)
        # neck
        cv.rect(cx - 3, size - 18, cx + 2, size - 11, self.skin)
        # head
        hw, hh = 15, 18
        top = 6
        cv.rect(cx - hw // 2, top, cx + hw // 2 - 1, top + hh - 1, self.skin)
        # cheek shading
        cv.dither(cx + 3, top + 6, cx + hw // 2 - 1, top + hh - 2, (max(0, self.skin[0] - 34), max(0, self.skin[1] - 34), max(0, self.skin[2] - 34), 255), 0.6, 150, seed=2)
        # brows + eyes
        eye_y = top + 7
        cv.rect(cx - 6, eye_y - 2, cx - 2, eye_y - 2, self.hair)
        cv.rect(cx + 2, eye_y - 2, cx + 6, eye_y - 2, self.hair)
        if mood == "angry":
            cv.line(cx - 6, eye_y - 3, cx - 2, eye_y - 1, self.hair)
            cv.line(cx + 6, eye_y - 3, cx + 2, eye_y - 1, self.hair)
        if mood == "dead":
            cv.rect(cx - 6, eye_y, cx - 2, eye_y + 1, "ink")
            cv.rect(cx + 2, eye_y, cx + 6, eye_y + 1, "ink")
            cv.px(cx - 4, eye_y, "red")
            cv.px(cx + 4, eye_y, "red")
        else:
            cv.rect(cx - 5, eye_y, cx - 3, eye_y + 2, "bone")
            cv.rect(cx + 3, eye_y, cx + 5, eye_y + 2, "bone")
            cv.rect(cx - 4, eye_y, cx - 3, eye_y + 1, "ink")
            cv.rect(cx + 3, eye_y, cx + 4, eye_y + 1, "ink")
        # nose
        cv.rect(cx - 1, eye_y + 3, cx + 1, eye_y + 7, (max(0, self.skin[0] - 40), max(0, self.skin[1] - 40), max(0, self.skin[2] - 40), 255))
        cv.px(cx - 2, eye_y + 7, (max(0, self.skin[0] - 55), max(0, self.skin[1] - 55), max(0, self.skin[2] - 55), 255))
        cv.px(cx + 2, eye_y + 7, (max(0, self.skin[0] - 55), max(0, self.skin[1] - 55), max(0, self.skin[2] - 55), 255))
        # mouth
        my = eye_y + 10
        if mood == "talk":
            cv.rect(cx - 3, my, cx + 3, my + 3, (110, 48, 44, 255))
            cv.rect(cx - 2, my + 1, cx + 2, my + 2, "ink")
        elif mood == "grin":
            cv.rect(cx - 4, my, cx + 4, my + 2, (110, 48, 44, 255))
            cv.rect(cx - 3, my, cx + 3, my, "bone")
        elif mood == "sad":
            cv.line(cx - 3, my + 2, cx, my, "ink")
            cv.line(cx, my, cx + 3, my + 2, "ink")
        else:
            cv.line(cx - 3, my + 1, cx + 3, my + 1, (110, 48, 44, 255))
        # beard / hair
        if self.beard == "full":
            cv.rect(cx - 8, eye_y + 8, cx + 8, top + hh + 4, self.hair)
            cv.rect(cx - 5, my - 1, cx + 5, my + 3, (110, 48, 44, 255))
            cv.rect(cx - 4, my, cx + 4, my, "bone")
            cv.dither(cx - 8, eye_y + 8, cx + 8, top + hh + 4, "ash", 0.3, 120, seed=5)
        elif self.beard == "stubble":
            cv.dither(cx - 7, eye_y + 8, cx + 7, top + hh + 2, "ink", 0.35, 110, seed=6)
        elif self.beard == "goatee":
            cv.rect(cx - 3, my + 2, cx + 3, top + hh + 3, self.hair)
        if self.hijab:
            cv.rect(cx - 11, top - 3, cx + 10, top + hh, self.hijab)
            cv.rect(cx - 9, top + 1, cx + 9, top + hh + 2, self.skin)
            cv.rect(cx - 11, top + hh, cx + 10, size - 12, self.hijab)
            cv.dither(cx - 11, top - 3, cx + 10, size - 12, "ash", 0.25, 90, seed=9)
            # redraw features over the cloth
            cv.rect(cx - 6, eye_y - 2, cx - 2, eye_y - 2, self.hair)
            cv.rect(cx + 2, eye_y - 2, cx + 6, eye_y - 2, self.hair)
            cv.rect(cx - 5, eye_y, cx - 3, eye_y + 2, "bone")
            cv.rect(cx + 3, eye_y, cx + 5, eye_y + 2, "bone")
            cv.rect(cx - 4, eye_y, cx - 3, eye_y + 1, "ink")
            cv.rect(cx + 3, eye_y, cx + 4, eye_y + 1, "ink")
            cv.rect(cx - 1, eye_y + 3, cx + 1, eye_y + 7, (max(0, self.skin[0] - 40), max(0, self.skin[1] - 40), max(0, self.skin[2] - 40), 255))
            cv.line(cx - 3, my + 1, cx + 3, my + 1, (110, 48, 44, 255))
        elif self.hat == "fez":
            cv.rect(cx - 9, top - 8, cx + 9, top + 1, self.hat_col)
            cv.rect(cx - 9, top, cx + 9, top + 1, "ink")
            cv.px(cx, top - 6, "ink")
            for t in range(0, 6, 2):
                cv.line(cx - t, top - 8, cx + t, top - 8, "ink")
        elif self.hat == "hood":
            cv.rect(cx - 12, top - 4, cx + 11, size - 6, self.hat_col)
            cv.rect(cx - 9, top + 1, cx + 8, top + hh, "void")
            cv.rect(cx - 5, eye_y, cx - 3, eye_y + 1, "red")
            cv.rect(cx + 3, eye_y, cx + 5, eye_y + 1, "red")
            cv.glow(cx - 4, eye_y, 7, "red", 0.7)
            cv.glow(cx + 4, eye_y, 7, "red", 0.7)
        elif self.hat == "turban":
            cv.rect(cx - 11, top - 7, cx + 10, top + 1, self.hat_col)
            cv.line(cx - 11, top - 4, cx + 10, top - 5, "cream")
            cv.line(cx - 11, top - 1, cx + 10, top - 2, "cream")
        else:
            cv.rect(cx - 9, top - 4, cx + 8, top + 2, self.hair)
            cv.rect(cx - 10, top - 1, cx - 8, top + 6, self.hair)
        cv.outline(0, 0, size - 1, size - 1, "ink")
        return quantize(cv, 22)


# ---------------------------------------------------------------- cast
CAST = {
    # protagonist — Inspector Rachid Belghawi
    "rachid": Char("rachid", skin="tan", robe="sand", robe2="cream", accent="blood",
                   hat="fez", hat_col="blood", beard="stubble", hair="black", tall=True),
    # the herb seller
    "zahra": Char("zahra", skin="olive", robe="teal", robe2="zellige", accent="gold",
                  hijab="plum", hair="grey"),
    # the blind fqih / sect defector
    "fqih": Char("fqih", skin="brown", robe="bone", robe2="cream", accent="azure",
                 hat="turban", hat_col="bone", beard="full", hair="white", hunch=0.2),
    # the constable sidekick
    "hmidou": Char("hmidou", skin="dark", robe="azure", robe2="majorelle", accent="cream",
                   hat="cap", hat_col="teal", beard="goatee", hair="black"),
    # the sect leader
    "mokhtar": Char("mokhtar", skin="pale", robe="void", robe2="shadow", accent="red",
                    hat="hood", hat_col="void", beard="goatee", hair="black", tall=True),
    # the jinn
    "jinn": Char("jinn", skin="dark", robe="shadow", robe2="plum", accent="blood",
                 hat="hood", hat_col="ink", hair="black", tall=True),
    # the boy who saw everything
    "sliman": Char("sliman", skin="tan", robe="ochre", robe2="gold", accent="terra",
                   hair="brown"),
    # Rachid's missing brother, seen in flashback
    "kamel": Char("kamel", skin="tan", robe="majorelle", robe2="azure", accent="gold",
                  hair="black"),
}

# stand-alone sprites (not humanoids)
EXTRA = {
    "babouche": """
....##########
..##############
.################
####........#####
###..####....####
###.######...####
####....#########
.###############
..#############.
....#########...
""",
    "babouche_red": """
....##########
..##############
.################
####........#####
###..####....####
###.######...####
####....#########
.###############
..#############.
....#########...
""",
    "cat": """
.##....##.
.####.####
..######..
..######..
.########.
.########.
..##..##..
.#..#..#..
""",
}


def dump():
    os.makedirs(OUT, exist_ok=True)
    written = []
    for name, ch in CAST.items():
        walk = ch.frames(walking=True)
        idle = ch.frames(walking=False)
        sheet = Image.new("RGBA", (18 * 6, 34), (0, 0, 0, 0))
        for i, fr in enumerate(walk):
            sheet.paste(fr.img, (i * 18, 0), fr.img)
        sheet.paste(idle[0].img, (4 * 18, 0), idle[0].img)
        sheet.paste(idle[1].img, (5 * 18, 0), idle[1].img)
        p = os.path.join(OUT, f"{name}_walk.png")
        sheet.save(p)
        written.append(p)
        for mood in ("neutral", "talk", "angry", "grin", "sad", "dead"):
            q = os.path.join(OUT, f"{name}_portrait_{mood}.png")
            ch.portrait(mood).img.save(q)
            written.append(q)
    # extras
    for name, art in EXTRA.items():
        cmap = {"#": "ink"}
        if name == "babouche_red":
            cmap = {"#": "red"}
        elif name == "cat":
            cmap = {"#": "ink"}
        img = ascii_sprite(art, cmap)
        p = os.path.join(OUT, f"{name}.png")
        img.save(p)
        written.append(p)
    for p in written:
        print("wrote", p)


if __name__ == "__main__":
    dump()
