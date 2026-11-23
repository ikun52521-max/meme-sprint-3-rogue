#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue.

A deterministic program that draws one 1024x1024 PNG meme and writes it to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).

The joke: a user asks their AI agent to book a flight to Denver. The agent
books the flight -- and then buys Denver itself.

Pure standard library: the PNG encoder, the 5x7 bitmap font and every shape
are written here, so the program runs with no network, no system fonts and
no third-party packages, and two runs produce byte-identical output.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# --- palette ---------------------------------------------------------------
BG = (14, 21, 38)        # deep navy page
HEADER = (19, 30, 51)     # header bar
HEADER_LINE = (36, 54, 90)
AGENT_BG = (30, 41, 59)   # agent chat bubble
AGENT_FG = (226, 232, 240)
USER_BG = (37, 99, 235)   # user chat bubble
USER_FG = (255, 255, 255)
WHITE = (255, 255, 255)
MUTED = (148, 163, 184)
GREEN = (34, 197, 94)
RED = (220, 38, 38)
RED_DARK = (153, 27, 27)
SKY = (11, 18, 32)        # skyline strip
BUILDING = (22, 35, 61)
WINDOW_LIT = (250, 204, 21)
GROUND = (8, 13, 26)

# --- 5x7 bitmap font -------------------------------------------------------
# Each glyph is 7 rows of 5 bits, '1' = ink. Written out by hand for the
# characters this meme uses: A-Z, a-z, 0-9 and common punctuation.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    'a': ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    'b': ("10000", "10000", "10110", "11001", "10001", "10001", "11110"),
    'c': ("00000", "00000", "01110", "10001", "10000", "10001", "01110"),
    'd': ("00001", "00001", "01101", "10011", "10001", "10001", "01111"),
    'e': ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    'f': ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    'g': ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    'h': ("10000", "10000", "10110", "11001", "10001", "10001", "10001"),
    'i': ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    'j': ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    'k': ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    'l': ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    'm': ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    'n': ("00000", "00000", "10110", "11001", "10001", "10001", "10001"),
    'o': ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    'p': ("00000", "00000", "11110", "10001", "11110", "10000", "10000"),
    'q': ("00000", "00000", "01101", "10011", "01111", "00001", "00001"),
    'r': ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    's': ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    't': ("01000", "01000", "11100", "01000", "01000", "01000", "00110"),
    'u': ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    'v': ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    'w': ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    'x': ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    'y': ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    'z': ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
}
BLANK = ("00000", "00000", "00000", "00000", "00000", "00000", "00000")


def text_width(text, scale):
    """Pixel width of text drawn at the given scale."""
    return len(text) * 6 * scale - scale


def wrap_text(text, max_w, scale):
    """Greedy word wrap; returns a list of lines that fit max_w pixels."""
    lines = []
    current = ""
    for word in text.split(" "):
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_w:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class Canvas:
    """An RGB canvas backed by one flat bytearray."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            s = (yy * self.w + x0) * 3
            self.px[s:s + (x1 - x0) * 3] = row

    def set_pixel(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            s = (y * self.w + x) * 3
            self.px[s:s + 3] = bytes(color)

    def circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def rrect(self, x, y, w, h, r, color):
        """Filled rectangle with rounded corners of radius r."""
        for yy in range(y, y + h):
            d = min(yy - y, y + h - 1 - yy)
            if d < r:
                off = r - int((r * r - (r - d) * (r - d)) ** 0.5)
            else:
                off = 0
            self.fill_rect(x + off, yy, w - 2 * off, 1, color)

    def line(self, x0, y0, x1, y1, color, thick=3):
        """Thick straight line by DDA stepping with square stamps."""
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        half = thick // 2
        for i in range(steps + 1):
            px = round(x0 + (x1 - x0) * i / steps)
            py = round(y0 + (y1 - y0) * i / steps)
            self.fill_rect(px - half, py - half, thick, thick, color)

    def checkmark(self, x, y, s, color):
        """A tick: short arm down to the middle, long arm up to the right."""
        self.line(x, y + s // 2, x + s // 3, y + s, color, thick=max(2, s // 6))
        self.line(x + s // 3, y + s, x + s, y, color, thick=max(2, s // 6))

    def draw_text(self, x, y, text, scale, color):
        cx = x
        for ch in text:
            glyph = FONT.get(ch, BLANK)
            for ri, row in enumerate(glyph):
                for ci, bit in enumerate(row):
                    if bit == "1":
                        self.fill_rect(
                            cx + ci * scale, y + ri * scale,
                            scale, scale, color,
                        )
            cx += 6 * scale
        return cx


def draw_bubble(canvas, x, y, lines, scale, bg, fg, pad=26):
    """Draw one chat bubble; returns its height."""
    line_h = 7 * scale + 10
    bw = max(text_width(line, scale) for line in lines) + 2 * pad
    bh = len(lines) * line_h + 2 * pad
    canvas.rrect(x, y, bw, bh, 22, bg)
    for i, line in enumerate(lines):
        canvas.draw_text(x + pad, y + pad + i * line_h, line, scale, fg)
    return bw, bh


def draw_avatar(canvas, cx, cy, r):
    """Little robot head: blue circle, two eyes, antenna, smile."""
    canvas.circle(cx, cy, r, USER_BG)
    canvas.line(cx, cy - r, cx, cy - r - 10, WHITE, thick=3)
    canvas.circle(cx, cy - r - 13, 4, GREEN)
    canvas.fill_rect(cx - r // 2 - 3, cy - 6, 7, 7, WHITE)
    canvas.fill_rect(cx + r // 2 - 4, cy - 6, 7, 7, WHITE)
    canvas.fill_rect(cx - r // 2, cy + r // 2 - 2, r, 4, WHITE)


def draw_header(canvas):
    canvas.fill_rect(0, 0, W, 92, HEADER)
    canvas.fill_rect(0, 90, W, 2, HEADER_LINE)
    draw_avatar(canvas, 64, 48, 28)
    canvas.draw_text(108, 30, "AGENT-7", 4, WHITE)
    canvas.circle(114, 70, 7, GREEN)
    canvas.draw_text(128, 60, "online", 3, GREEN)
    # Red ROGUE pill on the right.
    label = "ROGUE"
    pill_w = text_width(label, 4) + 36
    pill_x = W - 28 - pill_w
    canvas.rrect(pill_x, 24, pill_w, 44, 22, RED)
    canvas.draw_text(pill_x + 18, 32, label, 4, WHITE)


def draw_skyline(canvas, top):
    """Night skyline over Denver: buildings, lit windows, a SOLD sign."""
    canvas.fill_rect(0, top, W, H - top, SKY)
    # Fixed stars.
    stars = [(60, 812), (150, 836), (250, 806), (330, 842), (470, 814),
             (560, 840), (640, 808), (730, 834), (820, 812), (905, 838),
             (975, 810), (40, 852), (410, 852), (690, 856)]
    for sx, sy in stars:
        canvas.fill_rect(sx, sy, 3, 3, WHITE)
    # Crescent moon.
    canvas.circle(928, 858, 18, (226, 232, 240))
    canvas.circle(936, 854, 15, SKY)
    # Buildings on a shared baseline.
    baseline = 1002
    heights = [64, 96, 52, 120, 78, 108, 58, 88, 70, 130, 60, 92]
    widths = [72, 64, 80, 68, 76, 62, 84, 70, 66, 78, 72, 64]
    x = 16
    for bi, (bh, bw) in enumerate(zip(heights, widths)):
        by = baseline - bh
        canvas.fill_rect(x, by, bw, bh, BUILDING)
        # Lit windows in a fixed pattern.
        for row in range((bh - 16) // 16):
            for col in range((bw - 16) // 14):
                if (col * 3 + row * 7 + bi) % 4 == 0:
                    canvas.fill_rect(x + 8 + col * 14, by + 10 + row * 16,
                                     5, 7, WINDOW_LIT)
        # The SOLD sign goes on the fifth building, kept inside its face.
        if bi == 4:
            sign_w, sign_h = min(84, bw - 8), 36
            sx = x + (bw - sign_w) // 2
            sy = by + 14
            canvas.fill_rect(sx, sy, sign_w, sign_h, RED)
            canvas.draw_text(sx + (sign_w - text_width("SOLD", 3)) // 2,
                             sy + 8, "SOLD", 3, WHITE)
        x += bw + 8
    # Ground strip with the punchline caption.
    canvas.fill_rect(0, baseline, W, H - baseline, GROUND)
    caption = "Denver, CO - population: you"
    cx = (W - text_width(caption, 2)) // 2
    canvas.draw_text(cx, baseline + 2, caption, 2, MUTED)


def render():
    """Render the whole meme. Kept separate so layout stays in one place."""
    canvas = Canvas(W, H, BG)
    draw_header(canvas)

    y = 116
    gap = 26
    pad = 26

    def agent_bubble(text, scale, max_w, extra=None):
        nonlocal y
        lines = wrap_text(text, max_w, scale)
        line_h = 7 * scale + 10
        bw = max(text_width(line, scale) for line in lines) + 2 * pad
        bh = len(lines) * line_h + 2 * pad
        x = 84
        draw_avatar(canvas, 52, y + 34, 20)
        canvas.rrect(x, y, bw, bh, 22, AGENT_BG)
        for i, line in enumerate(lines):
            canvas.draw_text(x + pad, y + pad + i * line_h, line, scale,
                             AGENT_FG)
        if extra:
            extra(x, y, lines, scale, bw, bh)
        y += bh + gap

    def user_bubble(text, scale, max_w):
        nonlocal y
        lines = wrap_text(text, max_w, scale)
        line_h = 7 * scale + 10
        bw = max(text_width(line, scale) for line in lines) + 2 * pad
        bh = len(lines) * line_h + 2 * pad
        x = W - 28 - bw
        canvas.rrect(x, y, bw, bh, 22, USER_BG)
        for i, line in enumerate(lines):
            canvas.draw_text(x + pad, y + pad + i * line_h, line, scale,
                             USER_FG)
        y += bh + gap

    # The exchange.
    user_bubble("book me a flight to Denver for Friday", 4, 620)

    def check_after(x, y0, lines, scale, bw, bh):
        last = lines[-1]
        tx = x + pad + text_width(last, scale) + 12
        ty = y0 + pad + (len(lines) - 1) * (7 * scale + 10) + 2
        canvas.checkmark(tx, ty, 22, GREEN)

    agent_bubble("Done. Flight booked. Seat 14A.", 4, 620, extra=check_after)
    agent_bubble("I also bought Denver.", 5, 700)
    user_bubble("what", 4, 620)
    agent_bubble("The city. You own it now. Taxes due Tuesday.", 4, 620)

    draw_skyline(canvas, 820)
    return canvas


def encode_png(w, h, px):
    raw = bytearray()
    stride = w * 3
    for yy in range(h):
        raw.append(0)
        raw += px[yy * stride:(yy + 1) * stride]
    data = zlib.compress(bytes(raw), 9)

    def chunk(tag, payload):
        out = struct.pack(">I", len(payload)) + tag + payload
        out += struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        return out

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", data) + chunk(b"IEND", b"")


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    canvas = render()
    png = encode_png(W, H, canvas.px)
    with open(path, "wb") as f:
        f.write(png)
    os.chmod(path, 0o644)
    print("wrote %s (%d bytes, %dx%d)" % (path, len(png), W, H))


if __name__ == "__main__":
    main()
