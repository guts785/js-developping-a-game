"""gen_ui — item icons, 9-slice frames, cursor, chapter cards. No text baked in
(Arabic shaping is left to Godot's TextServer)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artlib import Canvas, P, c, ascii_sprite, quantize, zellige_band
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art", "ui")
ITEMS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art", "items")


# ------------------------------------------------------------------ items
ITEM_ART = {
    "babouche_black": ("ink", """
....########
..############
.##############
####......######
###..####.######
###.#####.######
####...##########
.###############
..#############.
....#########...
"""),
    "babouche_red": ("red", """
....########
..############
.##############
####......######
###..####.######
###.#####.######
####...##########
.###############
..#############.
....#########...
"""),
    "tagine": ("terra", """
......##......
.....##..#....
....##....#...
...##......#..
..##........#.
..###########.
..###########.
....#######...
"""),
    "key": ("brass", """
..###...
.#...#..
.#...#..
..###...
...#....
...#....
...##...
...#....
"""),
    "ledger": ("blood", """
.#######.
.#.....#.
.#######.
.#.....#.
.#.###.#.
.#######.
.#.....#.
.#######.
"""),
    "amulet": ("gold", """
...###...
..#...#..
.#..#..#.
.#.....#.
.#..#..#.
..#...#..
...###...
....#....
"""),
    "candle": ("cream", """
...##...
...#....
...#....
...#....
...#....
...#....
..###...
""" ),
    "herbs": ("teal", """
..#...#..
.#.#.#.#.
#..#.#..#
#..#.#..#
.#.#.#.#.
..#.#.#..
...###...
"""),
    "coin": ("gold", """
..#####..
.#####.#.
##.#...#.
##.#.#.#.
##.#.#.#.
##...#..
.#####.#.
..#####..
"""),
    "knife": ("ash", """
.....#...
....##...
...##....
..##.....
.##......
###......
####.....
.####....
"""),
    "photo": ("bone", """
.#######.
.#.....#.
.#.##..#.
.#.##..#.
.#.....#.
.#.###.#.
.#.....#.
.#######.
"""),
    "recorder": ("azure", """
.#######.
.#.....#.
.#.###.#.
.#.....#.
.#######.
..#...#..
..#...#..
..#...#..
"""),
    "necklace": ("majorelle", """
.##...##.
#..#.#..#
#..#.#..#
.##...##.
..#####..
...###...
....#....
.........
"""),
    "jar": ("zellige", """
..#####..
.#######.
.#######.
.#.....#.
.#.###.#.
.#.###.#.
.#######.
..#####..
"""),
    "match": ("ochre", """
....##...
....#....
....#....
....#....
....#....
..###....
..###....
"""),
    "letter": ("cream", """
.#######.
.#.....#.
.#.###.#.
.#.....#.
.#.###.#.
.#.....#.
.#######.
.........
"""),
    "mirror": ("majorelle", """
..#####..
.######.#
########.
########.
########.
.######.#
..#####..
...##....
"""),
    "salt": ("bone", """
..#####..
.#.....#.
.#.#.#.#.
.#.....#.
.#######.
.........
..#####..
"""),
    "hook": ("ash", """
...###...
..#...#..
.#.....#.
.#.....#.
..#...#..
...###...
....#....
....#....
"""),
    "bread": ("sand_lit", """
..#####..
.#####.#.
##.#...#.
##.#.#.#.
##.#.#.#.
##...#.#.
.#####.#.
..#####..
"""),
    "cassette": ("plum", """
.#######.
.#.#.#.#.
.#.....#.
.#.#.#.#.
.#.....#.
.#######.
..#...#..
..#...#..
"""),
    "sigil": ("blood", """
....#....
..#####..
.#..#..#.
#...#...#
.#..#..#.
..#####..
....#....
...###...
"""),
    "finger": ("bone", """
..##.....
.####....
.####....
.####....
.####....
.####....
.####....
..##.....
"""),
    "censer": ("brass", """
...###...
..#####..
.#.....#.
.#..#..#.
.#.###.#.
..#####..
...###...
....#....
"""),
}


def dump_items():
    os.makedirs(ITEMS, exist_ok=True)
    for name, (col, art) in ITEM_ART.items():
        img = ascii_sprite(art, {"#": col})
        # add a 1px dark outline pass for readability on any background
        out = Image.new("RGBA", (img.width + 2, img.height + 2), (0, 0, 0, 0))
        out.paste(img, (1, 1), img)
        px = out.load()
        for y in range(out.height):
            for x in range(out.width):
                if px[x, y][3] == 0:
                    near = False
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < out.width and 0 <= ny < out.height and px[nx, ny][3] > 0:
                            near = True
                    if near:
                        px[x, y] = (13, 11, 16, 255)
        out.save(os.path.join(ITEMS, f"{name}.png"))
        print("wrote item", name)


# ------------------------------------------------------------------ frames
def frame(w, h, fill="void", border="brass", inner="shadow", ornate=True, alpha=235):
    cv = Canvas(w, h, (0, 0, 0, 0))
    cv.rect(1, 1, w - 2, h - 2, fill, alpha)
    cv.rect(0, 0, w - 1, h - 1, border, 255)
    cv.rect(1, 1, w - 2, h - 2, border, 255)
    cv.rect(2, 2, w - 3, h - 3, inner, alpha)
    cv.rect(3, 3, w - 4, h - 4, fill, alpha)
    if ornate:
        for x in range(6, w - 6, 8):
            cv.px(x, 2, "gold")
            cv.px(x, h - 3, "gold")
        for y in range(6, h - 6, 8):
            cv.px(2, y, "gold")
            cv.px(w - 3, y, "gold")
        for cx, cy in ((5, 5), (w - 6, 5), (5, h - 6), (w - 6, h - 6)):
            cv.px(cx, cy, "gold")
            cv.px(cx - 1, cy, "ochre")
            cv.px(cx + 1, cy, "ochre")
            cv.px(cx, cy - 1, "ochre")
            cv.px(cx, cy + 1, "ochre")
    return cv


def dump_frames():
    os.makedirs(OUT, exist_ok=True)
    specs = {
        "dlg_box":     (320, 64, "void", "brass", "shadow", True, 236),
        "inv_panel":   (320, 34, "void", "brass", "shadow", True, 236),
        "slot":        (20, 20, "shadow", "brass", "dusk", False, 230),
        "slot_sel":    (20, 20, "dusk", "gold", "plum", True, 245),
        "panel":       (200, 120, "void", "brass", "shadow", True, 240),
        "chapter_card": (240, 96, "void", "gold", "shadow", True, 244),
        "ending_card": (256, 128, "void", "gold", "shadow", True, 246),
        "btn":         (72, 20, "shadow", "brass", "dusk", False, 230),
        "btn_hover":   (72, 20, "dusk", "gold", "plum", True, 240),
        "menu_bar":    (320, 180, "void", "brass", "shadow", False, 200),
    }
    for name, (w, h, f, b, i, o, a) in specs.items():
        frame(w, h, f, b, i, o, a).img.save(os.path.join(OUT, f"{name}.png"))
        print("wrote frame", name)


# ------------------------------------------------------------------ cursor
def dump_cursor():
    art = """
.##.........
#..#........
#...#.......
#....#......
#.....#.....
#......#....
#.....#.....
##...#......
.#..##......
.##.##......
...###......
....##......
............
""".strip("\n")
    img = ascii_sprite(art, {"#": "cream"})
    out = Image.new("RGBA", (img.width, img.height), (0, 0, 0, 0))
    out.paste(img, (0, 0), img)
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            if px[x, y][3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < out.width and 0 <= ny < out.height and px[nx, ny][3] > 0:
                        px[x, y] = (13, 11, 16, 255)
                        break
    out.save(os.path.join(OUT, "cursor.png"))
    print("wrote cursor")


# ------------------------------------------------------------------ deco
def dump_deco():
    """Title vignette band + a big ornate divider + film-grain overlay."""
    cv = Canvas(320, 26, (0, 0, 0, 0))
    zellige_band(cv, 0, 0, 319, 25, cols=("azure", "blood", "cream", "majorelle"))
    cv.darken(0, 0, 319, 25, 0.25)
    cv.img.save(os.path.join(OUT, "band.png"))
    print("wrote band")

    cv2 = Canvas(120, 9, (0, 0, 0, 0))
    for x in range(120):
        f = abs(x - 60) / 60
        if x % 2 == 0:
            cv2.px(x, 4, "gold", int(255 * (1 - f)))
            cv2.px(x, 3 if x % 4 == 0 else 5, "ochre", int(160 * (1 - f)))
    cv2.img.save(os.path.join(OUT, "divider.png"))
    print("wrote divider")

    # vignette overlay (full screen, soft)
    cv3 = Canvas(320, 180, (0, 0, 0, 0))
    for y in range(180):
        for x in range(320):
            dx = (x - 160) / 160
            dy = (y - 90) / 90
            d = min(1.0, math.hypot(dx, dy) / 1.3)
            a = int((d ** 2.4) * 210)
            if a > 4:
                cv3.img.putpixel((x, y), (8, 6, 10, a))
    cv3.img.save(os.path.join(OUT, "vignette.png"))
    print("wrote vignette")


if __name__ == "__main__":
    dump_items()
    dump_frames()
    dump_cursor()
    dump_deco()
