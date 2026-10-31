"""Purple pixel-art squirrel for the MHS-3.5 screen (480x320).

On the Pi it draws straight to the LCD framebuffer, no desktop needed:
    python display/squirrel.py
Preview anywhere (writes an animated GIF):
    python display/squirrel.py --preview squirrel.gif

It reads the bot's status file (settings.STATUS_FILE) to show when Toxive Jr is thinking or talking.
"""
import argparse
import math
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import settings  # noqa: E402

SCREEN = (480, 320)
SCALE = 5
W, H = SCREEN[0] // SCALE, SCREEN[1] // SCALE  # 96x64 low-res canvas
FPS = 8

COLORS = {
    "K": (30, 11, 51),  # outline
    "D": (91, 42, 142),  # shadow
    "P": (139, 69, 209),  # purple
    "M": (178, 120, 232),  # highlight
    "L": (222, 190, 247),  # belly
    "E": (18, 0, 24),  # eye
    "W": (255, 255, 255),
    "N": (255, 122, 184),  # nose
    "B": (232, 140, 214),  # blush
    "A": (150, 96, 45),  # acorn
    "a": (196, 140, 80),
    "C": (92, 58, 28),  # acorn cap
}
SKY_TOP = (14, 10, 40)
SKY_BOTTOM = (48, 22, 84)
GROUND = (36, 74, 52)
GROUND_DARK = (24, 50, 36)
TEXT = (222, 190, 247)

TAIL = """
........KKKKKK..........
......KKPPPPPPKK........
.....KPPMMMPPPPPK.......
....KPPMMPPPPPPPPK......
...KPPMPPPPKKKPPPPK.....
...KPPMPPPK...KPPPK.....
..KPPMPPPK.....KPPK.....
..KPPMPPPK......KK......
..KPPMPPPPK.............
..KPPMMPPPK.............
..KPPPMPPPPK............
...KPPMMPPPPK...........
...KPPPMMPPPPK..........
....KPPPMMPPPPK.........
....KDPPPMMPPPPK........
.....KDPPPPMPPPPK.......
.....KDDPPPPMPPPPK......
......KDDPPPPPPPPPK.....
......KDDDPPPPPPPPPK....
.......KDDDPPPPPPPPPK...
........KDDDPPPPPPPPK...
.........KDDDDPPPPPPK...
..........KKDDDDDPPPK...
............KKKDDDDK....
"""

BODY = """
..........................KK............
.........................KMPK...........
.........................KMLPK..........
........................KPMLPK..........
........................KPPPPKKK........
.......................KPPPPPPPPKK......
......................KPPPPPPPPPPPK.....
......................KPPPPPPPPPPPPK....
.....................KPPPPPPPPPEEPPPK...
.....................KPPPPPPPPEWEPPPK...
.....................KPPPPPPPPEEEPPPPK..
.....................KPPPPPBBPPPPPPPPNK.
.....................KDPPPPPPPPPPLLLKK..
......................KDPPPPPPPLLLLLK...
.......................KKDPPPPLLLLKK....
......................KPPPPPPLLLLLK.....
.....................KPPPPPPLLLLLLLK....
....................KPPPPPPLLLLKCCCK....
...................KPPPPPPLLLLKCCCCCK...
...................KPPPPPPLLLKMKAAAAK...
..................KPPPPPPPLLLKMKAaAAK...
..................KPPPPPPPLLLLKKAAAK....
..................KPPPPPPPLLLLLLKAK.....
..................KDPPPPPPLLLLLLLK......
..................KDPPPPPPPLLLLLLK......
..................KDDPPPPPPLLLLLLK......
..................KDDPPPPPPPLLLLLK......
...................KDDPPPPPPPLLLLK......
...................KDDDPPPPPPPPPPK......
....................KDDDPPPPPPPPK.......
....................KKDDDPPPPPPKK.......
...................KPPKKKKKKKKPPK.......
..................KPPPPPK..KPPPPPK......
..................KKKKKKK..KKKKKKK......
"""

# 3x5 pixel font
FONT = {
    "A": "010101111101101", "B": "110101110101110", "C": "011100100100011", "D": "110101101101110",
    "E": "111100110100111", "F": "111100110100100", "G": "011100101101011", "H": "101101111101101",
    "I": "111010010010111", "J": "001001001101010", "K": "101101110101101", "L": "100100100100111",
    "M": "101111111101101", "N": "110101101101101", "O": "010101101101010", "P": "110101110100100",
    "Q": "010101101110011", "R": "110101110101101", "S": "011100010001110", "T": "111010010010010",
    "U": "101101101101111", "V": "101101101101010", "W": "101101111111101", "X": "101101010101101",
    "Y": "101101010010010", "Z": "111001010100111", ".": "000000000000010", "!": "010010010000010",
    "?": "110001010000010", " ": "000000000000000", "'": "010010000000000",
}

STARS = [(5, 4), (17, 13), (40, 3), (55, 9), (63, 2), (79, 14), (88, 6), (70, 22), (9, 26), (92, 30)]


def parse(art):
    return [row for row in art.strip("\n").split("\n")]


TAIL_ROWS = parse(TAIL)
BODY_ROWS = parse(BODY)
BLINK_ROWS = [
    row.replace("W", "K").replace("E", "K") if "W" in row else row.replace("E", "P")
    for row in BODY_ROWS
]


def blit(img, rows, x0, y0):
    px = img.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in COLORS and 0 <= x0 + x < W and 0 <= y0 + y < H:
                px[x0 + x, y0 + y] = COLORS[ch]


def text(img, s, y, color=TEXT):
    s = s.upper()
    x0 = (W - (len(s) * 4 - 1)) // 2
    px = img.load()
    for i, ch in enumerate(s):
        glyph = FONT.get(ch, FONT["?"])
        for j, bit in enumerate(glyph):
            if bit == "1":
                x, yy = x0 + i * 4 + j % 3, y + j // 3
                if 0 <= x < W and 0 <= yy < H:
                    px[x, yy] = color


def background(t):
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        f = y / H
        draw.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * f) for a, b in zip(SKY_TOP, SKY_BOTTOM)))
    for i, (x, y) in enumerate(STARS):
        if math.sin(t * 1.3 + i * 2.1) > -0.6:
            img.putpixel((x, y), (255, 240, 200) if math.sin(t * 1.3 + i * 2.1) > 0.5 else (150, 130, 190))
    draw.rectangle([0, 46, W, H], fill=GROUND)
    draw.rectangle([0, 50, W, H], fill=GROUND_DARK)
    for x in range(0, W, 3):
        img.putpixel((x, 45), GROUND)
    return img


def read_state():
    try:
        with open(settings.STATUS_FILE) as f:
            state, stamp = f.read().split()
        age = time.time() - float(stamp)
    except (OSError, ValueError):
        return "idle"
    if state == "thinking" and age < 120:
        return "thinking"
    if state == "talking" and age < 4:
        return "talking"
    return "idle"


def frame(t, state):
    img = background(t)
    x, y = 26, 12

    sway = round(math.sin(t * (6 if state == "talking" else 1.6)))
    bob = -1 if state == "talking" and int(t * 4) % 2 else 0
    blink = state != "thinking" and 2.0 < (t % 4.0) < 2.18

    blit(img, TAIL_ROWS, x + 1 + sway, y - 1 + bob + (1 if sway < 0 else 0))
    blit(img, BLINK_ROWS if blink else BODY_ROWS, x, y + bob)

    if state == "thinking":
        draw = ImageDraw.Draw(img)
        draw.ellipse([60, 14, 62, 16], fill=COLORS["L"])
        draw.ellipse([63, 9, 66, 12], fill=COLORS["L"])
        draw.rounded_rectangle([67, 1, 91, 10], radius=3, fill=COLORS["L"], outline=COLORS["K"])
        dots = int(t * 3) % 4
        for i in range(dots):
            img.putpixel((74 + i * 4, 6), COLORS["K"])
            img.putpixel((75 + i * 4, 6), COLORS["K"])
        caption = "thinking..."
    elif state == "talking":
        caption = "ready to comply."
    else:
        caption = "toxive jr"
    text(img, caption, 55)
    return img.resize(SCREEN, Image.NEAREST)


class Framebuffer:
    def __init__(self, device=None):
        import numpy as np

        self.np = np
        self.device = device or self.find()
        name = Path(self.device).name
        sysfs = Path("/sys/class/graphics") / name
        self.width, self.height = map(int, (sysfs / "virtual_size").read_text().split(","))
        self.bpp = int((sysfs / "bits_per_pixel").read_text())
        stride = sysfs / "stride"
        self.stride = int(stride.read_text()) if stride.exists() else self.width * self.bpp // 8
        print(f"Using {self.device}: {self.width}x{self.height} {self.bpp}bpp")
        self.fb = open(self.device, "wb")

    @staticmethod
    def find():
        # Prefer the SPI LCD driver over HDMI
        devices = sorted(Path("/sys/class/graphics").glob("fb[0-9]*"))
        for d in devices:
            if "ili" in (d / "name").read_text().lower():
                return f"/dev/{d.name}"
        return f"/dev/{devices[-1].name}" if devices else "/dev/fb1"

    def show(self, img):
        np = self.np
        if (img.width > img.height) != (self.width > self.height):
            img = img.rotate(90, expand=True)
        if img.size != (self.width, self.height):
            img = img.resize((self.width, self.height), Image.NEAREST)
        a = np.asarray(img, dtype=np.uint16)
        if self.bpp == 16:
            pixels = ((a[..., 0] >> 3) << 11) | ((a[..., 1] >> 2) << 5) | (a[..., 2] >> 3)
            data = pixels.astype("<u2")
        else:
            data = np.dstack([a[..., 2], a[..., 1], a[..., 0], np.full(a.shape[:2], 255, np.uint16)]).astype(np.uint8)
        rows = data.reshape(self.height, -1).view(np.uint8)
        if rows.shape[1] < self.stride:
            rows = np.pad(rows, ((0, 0), (0, self.stride - rows.shape[1])))
        self.fb.seek(0)
        self.fb.write(rows.tobytes())
        self.fb.flush()


def preview(path):
    frames = []
    for state, seconds in (("idle", 4.5), ("thinking", 2.5), ("talking", 2)):
        for i in range(int(seconds * FPS)):
            frames.append(frame(i / FPS, state))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=1000 // FPS, loop=0)
    frames[0].save(Path(path).with_suffix(".png"))
    print(f"Wrote {path}")


def run(device):
    fb = Framebuffer(device)
    try:
        Path("/sys/class/graphics/fbcon/cursor_blink").write_text("0")
    except OSError:
        pass
    last = None
    start = time.time()
    while True:
        img = frame(time.time() - start, read_state())
        data = img.tobytes()
        if data != last:
            fb.show(img)
            last = data
        time.sleep(1 / FPS)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--preview", help="write an animated GIF instead of drawing to the screen")
    p.add_argument("--device", help="framebuffer device, e.g. /dev/fb1 (default: auto-detect)")
    args = p.parse_args()
    if args.preview:
        preview(args.preview)
    else:
        run(args.device)
