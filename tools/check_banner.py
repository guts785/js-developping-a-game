#!/usr/bin/env python3
"""Check that the objective banner's glyphs carry a dark outline.

Walks the banner's pixel rows and, for every gold glyph pixel, looks for a
near-black pixel within 3px. With the outline applied most glyph pixels have
one; without it, the glyphs sit straight on the room art.
Usage: check_banner.py shot_play.png [y0 y1]
"""
import sys, zlib, struct

def load_png(path):
    d = open(path, "rb").read()
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
y0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
y1 = int(sys.argv[3]) if len(sys.argv) > 3 else 140
w, h, ch, px = load_png(path)

def rgb(x, y):
    o = (y*w + x)*ch
    return px[o], px[o+1], px[o+2]

def is_glyph(x, y):
    r, g, b = rgb(x, y)
    return r > 170 and g > 120 and b < 130 and (r - b) > 55

def is_dark(x, y):
    r, g, b = rgb(x, y)
    return r < 55 and g < 55 and b < 60

glyphs = outlined = 0
for y in range(max(0, y0), min(h, y1)):
    for x in range(w):
        if not is_glyph(x, y):
            continue
        glyphs += 1
        found = False
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                xx, yy = x+dx, y+dy
                if 0 <= xx < w and 0 <= yy < h and is_dark(xx, yy):
                    found = True; break
            if found: break
        if found: outlined += 1

# locate every row band that contains gold pixels, so the caller can see where
# the banner actually sits instead of guessing a crop
print("gold row bands across the whole frame:")
band, cur = [], None
for y in range(h):
    n = sum(1 for x in range(0, w, 2) if is_glyph(x, y))
    if n >= 2:
        if cur is None: cur = [y, y, n]
        else:
            cur[1] = y; cur[2] = max(cur[2], n)
    else:
        if cur is not None: band.append(tuple(cur)); cur = None
if cur: band.append(tuple(cur))
for a, b, n in band:
    print("  y %4d..%4d  peak=%d" % (a, b, n))
print()

print("banner rows y %d..%d" % (y0, y1))
print("gold glyph pixels: %d" % glyphs)
print("with a dark pixel within 3px: %d" % outlined)
if glyphs:
    print("outlined ratio: %.1f%%" % (100.0 * outlined / glyphs))
