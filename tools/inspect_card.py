#!/usr/bin/env python3
"""Decode a PNG with stdlib only and report every text band in the chapter card.

No PIL/numpy here -- zlib + struct, same as the art generators. The card panel
now sizes itself from the wrapped text, so this scans a region rather than
assuming fixed geometry.
"""
import sys, zlib, struct

def load_png(path):
    d = open(path, "rb").read()
    assert d[:8] == b"\x89PNG\r\n\x1a\n", "not a png"
    pos, idat, w, h, ct = 8, b"", 0, 0, 0
    while pos < len(d):
        ln = struct.unpack(">I", d[pos:pos+4])[0]
        typ = d[pos+4:pos+8]
        data = d[pos+8:pos+8+ln]
        if typ == b"IHDR":
            w, h, _, ct = struct.unpack(">IIBB", data[:10])
        elif typ == b"IDAT":
            idat += data
        elif typ == b"IEND":
            break
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = {0:1, 2:3, 3:1, 4:2, 6:4}[ct]
    stride = w * ch
    out = bytearray(w * h * ch)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]; p += 1
        line = bytearray(raw[p:p+stride]); p += stride
        if f == 1:
            for i in range(ch, stride): line[i] = (line[i] + line[i-ch]) & 255
        elif f == 2:
            for i in range(stride): line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i-ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i-ch] if i >= ch else 0
                b = prev[i]
                c = prev[i-ch] if i >= ch else 0
                pp = a + b - c
                pa, pb, pc = abs(pp-a), abs(pp-b), abs(pp-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        out[y*stride:(y+1)*stride] = line
        prev = line
    return w, h, ch, out

path = sys.argv[1]
w, h, ch, px = load_png(path)
print("image %dx%d ch=%d" % (w, h, ch))

def rgb(x, y):
    o = (y*w + x)*ch
    return px[o], px[o+1], px[o+2]

def lum(x, y):
    r, g, b = rgb(x, y)
    return (r*299 + g*587 + b*114) // 1000

# Text is near-white; the button border is gold (high R, mid G, low B).
def is_text(x, y):
    r, g, b = rgb(x, y)
    return r > 165 and g > 165 and b > 165

def is_gold(x, y):
    r, g, b = rgb(x, y)
    return r > 140 and g > 95 and b < 110 and (r - b) > 60

X0, X1 = 240, 1040          # central column, 2x of the 640-space card
text_rows, gold_rows = [], []
for y in range(80, 720):
    tn = gn = 0
    for x in range(X0, X1, 2):
        if is_text(x, y): tn += 1
        elif is_gold(x, y): gn += 1
    text_rows.append((y, tn))
    gold_rows.append((y, gn))

def bands(rows, need):
    out, cur = [], None
    for y, n in rows:
        if n >= need:
            if cur is None: cur = [y, y]
            else: cur[1] = y
        else:
            if cur is not None: out.append(tuple(cur)); cur = None
    if cur: out.append(tuple(cur))
    return out

tb = bands(text_rows, 3)
print("\ntext bands (x %d..%d):" % (X0, X1))
for a, b in tb:
    print("  y %4d..%4d  (h=%3d)" % (a, b, b-a+1))

# The button is the widest gold horizontal run -- its top and bottom border.
gb = bands(gold_rows, 40)
print("\nwide gold bands (button frame):")
for a, b in gb:
    print("  y %4d..%4d  (h=%3d)" % (a, b, b-a+1))

if tb and gb:
    # button interior = between the first two wide gold bands
    btn_top = gb[0][0]
    btn_bot = gb[1][1] if len(gb) > 1 else gb[0][1]
    print("\nbutton frame y %d..%d" % (btn_top, btn_bot))
    inside = [(a, b) for a, b in tb if a >= btn_top - 2 and b <= btn_bot + 2]
    over = [(a, b) for a, b in tb if b > btn_top - 2 and a < btn_bot]
    if over:
        print("TEXT OVERLAPPING BUTTON: %s" % (over,))
    else:
        print("clean: no text row reaches the button frame")
    last_text = max(b for _, b in tb)
    print("lowest text row %d, button top %d" % (last_text, btn_top))
