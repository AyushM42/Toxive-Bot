"""Purple pixel-art Toxive Jr (propeller beanie, lollipop) for the MHS-3.5 screen (480x320).

On the Pi it draws straight to the LCD framebuffer, no desktop needed:
    python display/squirrel.py
Preview anywhere (writes an animated GIF):
    python display/squirrel.py --preview squirrel.gif

It reads the bot's status file (settings.STATUS_FILE) to show when Toxive Jr is thinking or talking.
"""
import argparse
import math
import random
import sys
import time
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import settings  # noqa: E402

SCREEN = (480, 320)
SCALE = 4
W, H = SCREEN[0] // SCALE, SCREEN[1] // SCALE  # 120x80 low-res canvas
# Frames per second. Kept low so the model gets the CPU; lowest while it's thinking.
FPS = {"idle": 4, "thinking": 2, "talking": 6}

OUTLINE = (34, 10, 48)
FUR_DARK = (88, 30, 128)
FUR = (128, 52, 186)
FUR_LIGHT = (166, 96, 220)
FUR_MID = (146, 72, 204)
FUR_SHADE = (116, 54, 178)
CHEEK = (214, 176, 236)
EYE = (16, 6, 20)
WHITE = (255, 255, 255)
NOSE = (224, 150, 176)
HAT_RED = (222, 38, 52)
HAT_RED_DARK = (160, 20, 36)
HAT_CREAM = (250, 244, 206)
PROPELLER = (214, 222, 92)
STICK = (232, 210, 170)
CANDY = [(236, 64, 72), (248, 156, 48), (250, 222, 70), (84, 186, 92), (64, 140, 230), (160, 90, 210)]

SKY_TOP = (14, 10, 40)
SKY_BOTTOM = (48, 22, 84)
GROUND = (36, 74, 52)
GROUND_DARK = (24, 50, 36)
TEXT = (222, 190, 247)

SPRITE = (60, 58)
SPRITE_FULL = (84, 72)  # room for the tail plume above and behind
BODY_Y = 10  # body layers sit this far down in the full sprite
FEET_Y = BODY_Y + 57  # bottom row of the feet; nothing goes lower

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

STARS = [(6, 5), (21, 16), (44, 4), (60, 11), (76, 3), (98, 17), (110, 7), (88, 28), (11, 33), (114, 38), (33, 26)]


# --- sprite building -------------------------------------------------------------

def mask(draw_fn, size=SPRITE):
    m = Image.new("1", size, 0)
    draw_fn(ImageDraw.Draw(m))
    return m


def fur(m, light_from=(-1, -1)):
    """Fill a mask with purple fur: highlight on the lit edge, shadow on the far edge."""
    img = Image.new("RGBA", m.size, (0, 0, 0, 0))
    mp, px = m.load(), img.load()
    w, h = m.size
    inside = lambda x, y: 0 <= x < w and 0 <= y < h and mp[x, y]
    lx, ly = light_from
    for y in range(h):
        for x in range(w):
            if not mp[x, y]:
                continue
            if not inside(x + lx, y) or not inside(x, y + ly):
                px[x, y] = FUR_LIGHT
            elif not inside(x - lx, y) or not inside(x, y - ly) or not inside(x - lx, y - ly + 1):
                px[x, y] = FUR_DARK
            else:
                px[x, y] = FUR
    return img


def fur_texture(img, m, rng, count, direction):
    """Sprinkle short fur strands inside a mask, running along direction(x, y) -> (dx, dy).

    Strands near the lit top/left edge are light, near the far edge shaded, and mostly subtle
    elsewhere, so the fill looks soft rather than speckled. Edge pixels are left alone.
    """
    mp, px = m.load(), img.load()
    w, h = m.size
    inside = lambda x, y: 0 <= x < w and 0 <= y < h and mp[x, y]
    interior = {(x, y) for y in range(h) for x in range(w)
                if all(inside(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1))}
    starts = sorted(interior)
    for _ in range(count):
        x, y = rng.choice(starts)
        dx, dy = direction(x, y)
        if not inside(x - 3, y) or not inside(x, y - 3):
            color = FUR_LIGHT
        elif not inside(x + 3, y) or not inside(x, y + 3):
            color = FUR_SHADE
        else:
            color = FUR_MID if rng.random() < 0.6 else FUR_SHADE
        for k in range(rng.randint(2, 4)):
            q = (round(x + dx * k), round(y + dy * k))
            if q in interior:
                px[q] = color + (255,)


def outline(img, color=OUTLINE):
    """Dark outline around every opaque pixel."""
    out = img.copy()
    src, px = img.load(), out.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            if src[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < w and 0 <= y + dy < h and src[x + dx, y + dy][3]:
                    px[x, y] = color + (255,)
                    break
    return out


def layer(fn):
    img = Image.new("RGBA", SPRITE, (0, 0, 0, 0))
    fn(ImageDraw.Draw(img), img.load())
    return img


# Tail spine like a real squirrel's: up behind the back, then a big plume that flops over
# backwards, away from the head. (x, y, thickness radius)
TAIL_SPINE = [
    (30, 60, 6.5), (38, 57, 9.5), (44, 52, 11), (46, 43, 10.5), (46, 35, 10.5), (46, 28, 11.5),
    (49, 22, 13), (56, 18, 13.5), (63, 20, 12), (67, 26, 9), (68, 32, 5.5),
]
TAIL_OUTLINE = (62, 22, 92)  # softer than the body outline so the fur edge looks fuzzy


def tail_points():
    """(x, y, radius, tangent x, tangent y) every half pixel along the spine."""
    points = []
    for (x0, y0, r0), (x1, y1, r1) in zip(TAIL_SPINE, TAIL_SPINE[1:]):
        length = math.dist((x0, y0), (x1, y1))
        tx, ty = (x1 - x0) / length, (y1 - y0) / length
        steps = int(length * 2)
        points += [(x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps, r0 + (r1 - r0) * i / steps, tx, ty) for i in range(steps)]
    return points


@lru_cache(maxsize=1)
def tail_layer():
    rng = random.Random(7)  # fixed seed: same fur every frame
    points = tail_points()

    def shape(d):
        for x, y, r, _, _ in points:
            d.ellipse([x - r, y - r, x + r, y + r], fill=1)
        # short uneven wisps all round the edge, swept towards the tip
        for x, y, r, tx, ty in points[::2]:
            for side in (1, -1):
                if rng.random() < 0.45:
                    continue
                nx, ny = -ty * side, tx * side
                length = rng.uniform(1, 3) * min(1, r / 8)
                bx, by = x + nx * (r - 1), y + ny * (r - 1)
                d.polygon([
                    (bx - tx * 1.3, by - ty * 1.3),
                    (bx + tx * 1.3, by + ty * 1.3),
                    (bx + nx * length + tx * length, by + ny * length + ty * length),
                ], fill=1)

    m = mask(shape, SPRITE_FULL)
    ImageDraw.Draw(m).rectangle([0, FEET_Y + 1, SPRITE_FULL[0], SPRITE_FULL[1]], fill=0)  # rest on the ground
    img = fur(m)

    def along_tail(x, y):
        _, _, _, tx, ty = min(points, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
        return tx, ty

    fur_texture(img, m, rng, 70, along_tail)
    return outline(img, TAIL_OUTLINE)


def body_layer(blink):
    def shape(d):
        d.ellipse([12, 26, 40, 56], fill=1)  # haunch
        d.ellipse([7, 20, 26, 46], fill=1)  # chest
        d.ellipse([2, 13, 21, 31], fill=1)  # head
        d.polygon([(4, 20), (0, 25), (2, 28), (8, 29)], fill=1)  # snout
        d.polygon([(16, 13), (20, 8), (22, 16)], fill=1)  # ear
        d.ellipse([5, 51, 21, 57], fill=1)  # foot
    m = mask(shape)
    img = fur(m)

    def body_fur(x, y):
        return (0.94, 0.33) if x < 22 and y < 30 else (0.37, 0.93)  # head fur runs back, body fur down

    fur_texture(img, m, random.Random(11), 40, body_fur)
    d = ImageDraw.Draw(img)
    d.ellipse([3, 24, 12, 33], fill=CHEEK)  # cheek / throat
    d.ellipse([7, 30, 14, 40], fill=CHEEK)
    d.arc([18, 32, 40, 58], 180, 270, fill=FUR_DARK)  # thigh
    d.point([(1, 25), (2, 25), (1, 26)], fill=NOSE)
    d.point([(5, 55), (7, 56), (9, 56)], fill=CHEEK)  # toes
    if blink:
        d.line([(7, 21), (10, 21)], fill=EYE)
    else:
        d.rectangle([7, 20, 9, 22], fill=EYE)
        d.point((7, 20), fill=WHITE)
    return outline(img)


def paw_layer():
    def draw(d, px):
        d.line([(9, 37), (17, 49)], fill=STICK)  # lollipop stick
        d.ellipse([9, 37, 14, 42], fill=FUR)  # paw
        d.point([(10, 38), (11, 38)], fill=FUR_LIGHT)
    return outline(layer(draw))


def lollipop_layer():
    def draw(d, px):
        cx, cy, r = 5.5, 35.5, 5.5
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                dist = math.hypot(dx, dy)
                if dist <= r:
                    swirl = (math.atan2(dy, dx) / (2 * math.pi) + dist / 3.2) * len(CANDY)
                    px[x, y] = CANDY[int(swirl) % len(CANDY)] + (255,)
        px[4, 33] = WHITE + (255,)
    return outline(layer(draw))


def hat_layer(phase):
    def draw(d, px):
        # dome: red / cream / red panels, cut off at the rim
        dome = mask(lambda m: m.ellipse([1, 7, 21, 27], fill=1))
        dm = dome.load()
        for y in range(7, 17):
            for x in range(1, 22):
                if dm[x, y]:
                    if x < 6:
                        color = HAT_RED
                    elif x < 15:
                        color = HAT_CREAM
                    else:
                        color = HAT_RED_DARK if y > 13 or x > 18 else HAT_RED
                    px[x, y] = color + (255,)
        d.line([(1, 16), (21, 16)], fill=HAT_RED_DARK)  # rim
        d.line([(5, 9), (4, 15)], fill=OUTLINE)  # panel seams
        d.line([(15, 9), (16, 15)], fill=OUTLINE)
        d.rectangle([10, 5, 12, 6], fill=HAT_RED)  # button + stem
        d.point((11, 4), fill=HAT_RED_DARK)
        # propeller blades, squashed sideways as they spin: full / half / edge-on / half
        span = (9, 5, 1, 5)[phase % 4]
        if span > 1:
            d.polygon([(11, 3), (11 - span, 1), (11 - span, 3)], fill=PROPELLER)
            d.polygon([(11, 3), (11 + span, 3), (11 + span, 5)], fill=PROPELLER)
        else:
            d.rectangle([10, 1, 12, 4], fill=PROPELLER)
    return outline(layer(draw))


@lru_cache(maxsize=None)
def sprite(tail_dx, tail_dy, blink, phase):
    img = Image.new("RGBA", SPRITE_FULL, (0, 0, 0, 0))
    img.alpha_composite(tail_layer(), (tail_dx, tail_dy))
    for part in (body_layer(blink), paw_layer(), lollipop_layer(), hat_layer(phase)):
        img.alpha_composite(part, (0, BODY_Y))
    return img


# --- scene -----------------------------------------------------------------------

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


@lru_cache(maxsize=1)
def sky():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        f = y / H
        draw.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * f) for a, b in zip(SKY_TOP, SKY_BOTTOM)))
    draw.rectangle([0, 65, W, H], fill=GROUND)
    draw.rectangle([0, 69, W, H], fill=GROUND_DARK)
    for x in range(0, W, 3):
        img.putpixel((x, 64), GROUND)
    return img


def background(t):
    img = sky().copy()
    for i, (x, y) in enumerate(STARS):
        s = math.sin(t * 1.3 + i * 2.1)
        if s > -0.6:
            img.putpixel((x, y), (255, 240, 200) if s > 0.5 else (150, 130, 190))
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
    x, y = 22, -2

    sway = round(math.sin(t * (6 if state == "talking" else 1.6)))
    bob = -1 if state == "talking" and int(t * 4) % 2 else 0
    blink = state != "thinking" and 2.0 < (t % 4.0) < 2.18
    spin = 3 if state == "thinking" else 1 if state == "talking" else 0.5  # propeller turns per second
    phase = int(t * spin * 4) % 4 if spin else 0

    squirrel = sprite(sway + 1, 0, blink, phase)
    img.paste(squirrel, (x, y + bob), squirrel)

    if state == "thinking":
        draw = ImageDraw.Draw(img)
        draw.ellipse([17, 18, 19, 20], fill=CHEEK)
        draw.ellipse([12, 12, 15, 15], fill=CHEEK)
        draw.rounded_rectangle([1, 1, 22, 10], radius=3, fill=CHEEK, outline=OUTLINE)
        for i in range(int(t * 3) % 4):
            draw.rectangle([6 + i * 4, 5, 7 + i * 4, 6], fill=OUTLINE)
        caption = "thinking..."
    elif state == "talking":
        caption = "ready to comply."
    else:
        caption = "toxive jr"
    text(img, caption, 72)
    return img  # low-res; scaled up when shown


# --- output ----------------------------------------------------------------------

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
        # Work out once how the 120x80 canvas maps onto the screen
        self.rotate = (W > H) != (self.width > self.height)
        w, h = (H, W) if self.rotate else (W, H)
        sx, sy = self.width // w, self.height // h
        self.scale = sx if sx == sy and (w * sx, h * sy) == (self.width, self.height) else 0
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
        """Convert the low-res canvas to the screen's pixel format, then scale it up."""
        np = self.np
        if not self.scale:  # screen isn't an exact multiple of the canvas
            target = (self.height, self.width) if self.rotate else (self.width, self.height)
            img = img.resize(target, Image.NEAREST)
        a = np.asarray(img, dtype=np.uint16)
        if self.bpp == 16:
            data = (((a[..., 0] >> 3) << 11) | ((a[..., 1] >> 2) << 5) | (a[..., 2] >> 3)).astype("<u2")
        elif self.bpp == 24:
            data = a[..., ::-1].astype(np.uint8)  # BGR
        else:
            data = np.dstack([a[..., ::-1], np.full(a.shape[:2], 255, np.uint16)]).astype(np.uint8)  # BGRA
        if self.rotate:
            data = np.rot90(data)
        if self.scale > 1:
            data = data.repeat(self.scale, axis=0).repeat(self.scale, axis=1)
        rows = np.ascontiguousarray(data).reshape(self.height, -1).view(np.uint8)
        if rows.shape[1] < self.stride:
            rows = np.pad(rows, ((0, 0), (0, self.stride - rows.shape[1])))
        self.fb.seek(0)
        self.fb.write(rows.tobytes())
        self.fb.flush()


def preview(path):
    frames, durations = [], []
    for state, seconds in (("idle", 4.5), ("thinking", 2.5), ("talking", 2)):
        fps = FPS[state]
        for i in range(int(seconds * fps)):
            frames.append(frame(i / fps, state).resize(SCREEN, Image.NEAREST))
            durations.append(1000 // fps)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations, loop=0)
    print(f"Wrote {path}")


def run(device):
    fb = Framebuffer(device)
    last = None
    start = time.time()
    while True:
        state = read_state()
        img = frame(time.time() - start, state)
        data = img.tobytes()  # 120x80, cheap to compare
        if data != last:
            fb.show(img)
            last = data
        time.sleep(1 / FPS[state])


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--preview", help="write an animated GIF instead of drawing to the screen")
    p.add_argument("--device", help="framebuffer device, e.g. /dev/fb1 (default: auto-detect)")
    args = p.parse_args()
    if args.preview:
        preview(args.preview)
    else:
        run(args.device)
