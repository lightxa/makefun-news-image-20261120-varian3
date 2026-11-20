#!/usr/bin/env python3
"""news-image-20261120 varian 3: a chronological timeline of the day.

Draws one 1024x1024 PNG summing up the world news of Friday 20 November
2026 as a vertical timeline: seven moments from overnight to night, each
with its own drawn pictogram, a short factual caption and its field.
Pure standard library, deterministic, no network at runtime.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER   = (247, 243, 232)   # warm paper
INK     = (24, 30, 44)      # near-black ink
MUTED   = (90, 96, 110)     # grey-blue for small labels
SPINE   = (31, 58, 95)      # deep blue spine
ACCENTS = [
    (178, 58, 44),    # 1 Kyiv: brick red
    (14, 110, 110),   # 2 Hormuz tanker: teal
    (30, 90, 160),    # 3 Cyclone: storm blue
    (150, 92, 12),    # 4 Anthropic: amber
    (94, 60, 140),    # 5 Iran decision: purple
    (24, 110, 64),    # 6 Europe talks: green
    (120, 60, 30),    # 7 Genoa drones: rust
]
CARD    = (255, 255, 255)
CARDLN  = (214, 206, 188)

# ------------------------------------------------- the day's news (researched)
# Every story below happened or was first reported on 20 November 2026.
# Sources: Reuters (Kyiv, 00:41 UTC), Daily Baku (Hormuz tanker 01:27,
# Genoa drones 04:22), The Hindu (Cyclone Akvan, 01:43 IST), Nasdaq/AP
# via The Hindu/Unite.AI (Anthropic close, reported 20 Nov), Reuters/TOI
# (Trump Iran decision, reported 03:06 IST), BBC (Europe-Russia talks,
# reported 01:43 IST).
MOMENTS = [
    ("OVERNIGHT", "KYIV HIT BY MISSILES",
     "Fire in a Kyiv building after a",
     "missile strike in the early hours.",
     "WAR - UKRAINE"),
    ("OVERNIGHT", "TANKER HITS MINE",
     "A tanker catches fire after hitting",
     "a mine east of the Strait of Hormuz.",
     "SHIPPING - MIDDLE EAST"),
    ("MORNING", "CYCLONE AKVAN NEARS INDIA",
     "300,000 people evacuated in Odisha",
     "as the storm heads for the coast.",
     "WEATHER - INDIA"),
    ("MIDDAY", "ANTHROPIC SHARES JUMP 17%",
     "The AI firm closes its stock debut",
     "up 17% after a record $81bn IPO.",
     "TECH - MARKETS"),
    ("AFTERNOON", "TRUMP: NO RUSH ON IRAN",
     "The US president pushes any Iran",
     "war decision into 2027.",
     "POLITICS - USA"),
    ("EVENING", "EUROPE OPEN TO RUSSIA TALKS",
     "European leaders say they are ready",
     "for talks on ending the Ukraine war.",
     "DIPLOMACY - EUROPE"),
    ("NIGHT", "DRONES HALT GENOA AIRPORT",
     "Flights suspended after unidentified",
     "drones are spotted over the airport.",
     "SECURITY - ITALY"),
]

# ------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, most significant bit left.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ",": (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    ":": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    "-": (0x00, 0x00, 0x00, 0x0E, 0x00, 0x00, 0x00),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    "%": (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "+": (0x00, 0x04, 0x04, 0x0E, 0x04, 0x04, 0x00),
    "=": (0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
}

# ------------------------------------------------------- pixel canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def hline(self, x0, x1, y, c, t=1):
        for yy in range(y, y + t):
            for xx in range(min(x0, x1), max(x0, x1) + 1):
                self.set(xx, yy, c)

    def vline(self, x, y0, y1, c, t=1):
        for xx in range(x, x + t):
            for yy in range(min(y0, y1), max(y0, y1) + 1):
                self.set(xx, yy, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            for a in range(t):
                for b in range(t):
                    self.set(x0 + a, y0 + b, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, r, c, t=2):
        for yy in range(cy - r - t, cy + r + t + 1):
            for xx in range(cx - r - t, cx + r + t + 1):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if r - t < d <= r:
                    self.set(xx, yy, c)

    def triangle(self, pts, c):
        (x0, y0), (x1, y1), (x2, y2) = pts
        ymin, ymax = min(y0, y1, y2), max(y0, y1, y2)
        for yy in range(ymin, ymax + 1):
            xs = []
            for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)),
                                       ((x1, y1), (x2, y2)),
                                       ((x2, y2), (x0, y0))):
                if ay == by:
                    continue
                if min(ay, by) <= yy < max(ay, by):
                    xs.append(ax + (yy - ay) * (bx - ax) / (by - ay))
            if len(xs) >= 2:
                for xx in range(int(min(xs)), int(max(xs)) + 1):
                    self.set(xx, yy, c)

    def text(self, s, x, y, scale, c):
        cx = x
        for ch in s.upper():
            g = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, c)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def text_center(self, s, cx, y, scale, c):
        self.text(s, cx - self.text_w(s, scale) // 2, y, scale, c)

# ------------------------------------------------------------ PNG out
def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw.extend(cv.px[y * cv.w * 3:(y + 1) * cv.w * 3])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# --------------------------------------------------------- pictograms
# Each draws a small white emblem inside a node disc centred at (cx, cy).
def pic_burst(cv, cx, cy):
    # missile strike: radiating burst over a rooftop line
    cv.disc(cx, cy - 2, 7, PAPER)
    for k in range(8):
        import math
        a = k * 3.14159 / 4
        x1 = cx + int(10 * math.cos(a))
        y1 = cy - 2 + int(10 * math.sin(a))
        x2 = cx + int(23 * math.cos(a))
        y2 = cy - 2 + int(23 * math.sin(a))
        cv.line(x1, y1, x2, y2, PAPER, 3)
    cv.rect(cx - 22, cy + 16, 44, 8, PAPER)

def pic_tanker(cv, cx, cy):
    # ship hull, mast and waves
    cv.triangle([(cx - 24, cy - 2), (cx + 24, cy - 2),
                 (cx + 16, cy + 10)], PAPER)
    cv.rect(cx - 24, cy - 2, 40, 12, PAPER)
    cv.vline(cx - 6, cy - 18, cy - 2, PAPER, 3)
    cv.hline(cx - 12, cx + 0, cy - 18, PAPER, 3)
    cv.hline(cx - 24, cx - 10, cy + 18, PAPER, 3)
    cv.hline(cx + 2, cx + 16, cy + 18, PAPER, 3)
    cv.hline(cx - 16, cx + 8, cy + 23, PAPER, 3)

def pic_cyclone(cv, cx, cy):
    # spiral storm with rain below
    cv.ring(cx, cy - 4, 20, PAPER, 3)
    cv.ring(cx + 4, cy - 2, 13, PAPER, 3)
    cv.disc(cx + 2, cy - 4, 4, PAPER)
    for dx in (-18, -6, 6, 18):
        cv.vline(cx + dx, cy + 16, cy + 24, PAPER, 3)

def pic_chart(cv, cx, cy):
    # rising bars and arrow
    for i, h in enumerate((10, 16, 24)):
        cv.rect(cx - 22 + i * 13, cy + 12 - h, 9, h, PAPER)
    cv.line(cx - 24, cy + 14, cx + 22, cy - 18, PAPER, 3)
    cv.line(cx + 22, cy - 18, cx + 12, cy - 18, PAPER, 3)
    cv.line(cx + 22, cy - 18, cx + 22, cy - 8, PAPER, 3)

def pic_clock(cv, cx, cy):
    # a clock: the decision waits
    cv.ring(cx, cy, 21, PAPER, 3)
    cv.vline(cx, cy - 14, cy, PAPER, 3)
    cv.line(cx, cy, cx + 11, cy + 8, PAPER, 3)
    cv.disc(cx, cy, 3, PAPER)

def pic_talks(cv, cx, cy):
    # two speech bubbles in dialogue
    cv.rect(cx - 26, cy - 18, 24, 16, PAPER)
    cv.triangle([(cx - 20, cy - 2), (cx - 12, cy - 2),
                 (cx - 18, cy + 6)], PAPER)
    cv.rect(cx + 2, cy - 6, 24, 16, PAPER)
    cv.triangle([(cx + 20, cy + 10), (cx + 12, cy + 10),
                 (cx + 18, cy + 18)], PAPER)
    cv.disc(cx - 18, cy - 10, 2, ACCENTS[5])
    cv.disc(cx - 12, cy - 10, 2, ACCENTS[5])
    cv.disc(cx - 6, cy - 10, 2, ACCENTS[5])

def pic_drone(cv, cx, cy):
    # quadcopter over a runway strip
    cv.line(cx - 20, cy - 14, cx + 20, cy + 14, PAPER, 3)
    cv.line(cx + 20, cy - 14, cx - 20, cy + 14, PAPER, 3)
    for dx, dy in ((-20, -14), (20, -14), (-20, 14), (20, 14)):
        cv.disc(cx + dx, cy + dy, 5, PAPER)
    cv.disc(cx, cy, 7, PAPER)
    cv.hline(cx - 24, cx + 24, cy + 22, PAPER, 3)

PICS = [pic_burst, pic_tanker, pic_cyclone, pic_chart,
        pic_clock, pic_talks, pic_drone]

# -------------------------------------------------------------- layout
def draw():
    cv = Canvas(W, H, PAPER)

    # header band
    cv.rect(0, 0, W, 150, SPINE)
    cv.text_center("FRIDAY 20 NOVEMBER 2026", W // 2, 30, 5,
                   (247, 243, 232))
    cv.text_center("THE DAY IN SEVEN MOMENTS", W // 2, 88, 3,
                   (232, 196, 110))
    cv.rect(W // 2 - 200, 132, 400, 4, (232, 196, 110))

    # spine
    top0, rowh, n = 170, 114, len(MOMENTS)
    cv.vline(118, top0 + 57, top0 + (n - 1) * rowh + 57, SPINE, 6)

    for i, (when, head, cap1, cap2, field) in enumerate(MOMENTS):
        acc = ACCENTS[i]
        top = top0 + i * rowh
        cy = top + 57
        # node
        cv.disc(118, cy, 36, acc)
        cv.ring(118, cy, 36, (255, 255, 255), 3)
        PICS[i](cv, 118, cy)
        # card
        cv.rect(170, top + 4, 830, 106, CARD)
        cv.rect(170, top + 4, 830, 3, acc)
        cv.rect(170, top + 107, 830, 2, CARDLN)
        cv.rect(998, top + 4, 2, 106, CARDLN)
        # time + field
        cv.text(when, 190, top + 16, 2, acc)
        fw = cv.text_w(field, 2)
        cv.text(field, 980 - fw, top + 16, 2, MUTED)
        # headline + captions
        cv.text(head, 190, top + 40, 3, INK)
        cv.text(cap1, 190, top + 70, 2, MUTED)
        cv.text(cap2, 190, top + 88, 2, MUTED)

    # footer
    cv.text_center("SOURCES: REUTERS - BBC - THE HINDU - NASDAQ - DAILY BAKU",
                   W // 2, 978, 2, MUTED)
    cv.text_center("ALSO TODAY: WORLD CHILDREN'S DAY", W // 2, 1000, 2,
                   MUTED)
    return cv

def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(draw(), path)
    print(f"wrote {path} ({size} bytes, {W}x{H})")

if __name__ == "__main__":
    main()
