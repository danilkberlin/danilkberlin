"""Contribution City: the last 12 months as a 3D city, orbiting camera, rendered to GIF.

Each month is a district (6 week-columns × 7 weekday-rows); districts are laid
out 4×3 with glowing streets between them. Building height = sqrt-scaled daily
contributions. Rendered with a painter's algorithm in Pillow at 2× and
downsampled for anti-aliasing, then quantised to one shared palette.
"""
from __future__ import annotations

import io
import math
import random
from dataclasses import dataclass
from datetime import date

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from ..config import ASSETS, Config
from ..model import Data
from .. import stats

OUT_W, OUT_H = 840, 400
SS = 2  # supersampling
FRAMES = 60
FRAME_MS = 90
COLORS = 112
PITCH = math.radians(32)
GAP = 1.7  # street width between districts
FOOT = 0.74  # building footprint (cell = 1)


@dataclass
class Building:
    x: float  # world centre
    z: float
    h: float
    level: int
    count: int
    windows: list[tuple[int, float, float, int]]  # (face, u, v, color index)


def _hex(color: str) -> tuple[int, int, int]:
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def _shade(rgb, factor: float) -> tuple[int, int, int]:
    return tuple(max(0, min(255, int(c * factor))) for c in rgb)


def _mix(a, b, t: float) -> tuple[int, int, int]:
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


def _months(today: date) -> list[tuple[int, int]]:
    out = []
    y, m = today.year, today.month
    for _ in range(12):
        out.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return out[::-1]


def _layout(data: Data) -> tuple[list[Building], list[tuple[float, float, str]], float, float]:
    today = data.generated_at.date()
    months = _months(today)
    by_date = {d.date: d for d in data.calendar}
    counts = [d.count for d in data.calendar if (today - d.date).days < 400]
    top = max(counts) if counts and max(counts) else 1
    block_w, block_d = 6, 7
    width = 4 * block_w + 3 * GAP
    depth = 3 * block_d + 2 * GAP
    rng = random.Random(7)
    buildings, labels = [], []
    for index, (year, month) in enumerate(months):
        bx = (index % 4) * (block_w + GAP) - width / 2
        bz = (index // 4) * (block_d + GAP) - depth / 2
        labels.append((bx, bz, date(year, month, 1).strftime("%b").upper()))
        first = date(year, month, 1)
        day = first
        while day.month == month and day <= today:
            col = (day.day - 1 + first.weekday()) // 7
            row = day.weekday()
            entry = by_date.get(day)
            count = entry.count if entry else 0
            level = entry.level if entry and entry.level else (0 if not count else min(4, 1 + int(3.99 * count / top)))
            h = .12 if not count else .55 + 7.2 * math.sqrt(count / top)
            windows = []
            if h > 1.2:
                for face in range(4):
                    for v in [k * .55 + .45 for k in range(int((h - .5) / .55))]:
                        for u in (.3, .7):
                            if rng.random() < .55:
                                windows.append((face, u, v, rng.randrange(3)))
            buildings.append(Building(bx + col + .5, bz + row + .5, h, level, count, windows))
            day = date.fromordinal(day.toordinal() + 1)
    return buildings, labels, width, depth


class Camera:
    def __init__(self, yaw: float, scale: float, cx: float, cy: float):
        self.cos, self.sin = math.cos(yaw), math.sin(yaw)
        self.scale, self.cx, self.cy = scale, cx, cy
        self.cp, self.sp = math.cos(PITCH), math.sin(PITCH)

    def rotate(self, x: float, z: float) -> tuple[float, float]:
        return x * self.cos - z * self.sin, x * self.sin + z * self.cos

    def project(self, x: float, y: float, z: float) -> tuple[float, float]:
        xr, zr = self.rotate(x, z)
        return self.cx + xr * self.scale, self.cy + (zr * self.sp - y * self.cp) * self.scale


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(ASSETS / "fonts" / name), size)


def _background(theme: dict) -> Image.Image:
    w, h = OUT_W * SS, OUT_H * SS
    dark = theme["name"] == "dark"
    top, mid, bottom = (("#03051a", "#120c3d", "#3a1153") if dark else ("#9fd4ff", "#d8ecff", "#ffd9ec"))
    img = Image.new("RGB", (w, h))
    px = ImageDraw.Draw(img)
    a, b, c = _hex(top), _hex(mid), _hex(bottom)
    for y in range(h):
        t = y / h
        color = _mix(a, b, t / .6) if t < .6 else _mix(b, c, (t - .6) / .4)
        px.line([(0, y), (w, y)], fill=color)
    if dark:
        rng = random.Random(3)
        for _ in range(140):
            x, y = rng.uniform(0, w), rng.uniform(0, h * .55)
            if y < 84 * SS and (x < 330 * SS or x > 560 * SS):
                continue  # keep the title and "tallest tower" text clean
            r = rng.choice([1, 1, 1.5, 2, 2.5])
            px.ellipse([x - r, y - r, x + r, y + r], fill=rng.choice([(255, 255, 255), (200, 210, 255), _hex(theme["cyan"])]))
    # horizon glow
    glow = Image.new("RGB", (w, h), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([w * .1, h * .45, w * .9, h * 1.15], fill=_hex(theme["pink"]) if dark else (255, 200, 230))
    glow = glow.filter(ImageFilter.GaussianBlur(80 * SS))
    return Image.blend(img, Image.composite(glow, img, glow.convert("L")), .35 if dark else .25)


def _frame(base: Image.Image, buildings, labels, width, depth, yaw: float, theme: dict, fonts) -> Image.Image:
    dark = theme["name"] == "dark"
    img = base.copy()
    draw = ImageDraw.Draw(img)
    w, h = img.size
    extent = math.hypot(width, depth)
    scale = min(w * .86 / extent, h * .9 / (extent * math.sin(PITCH) + 9 * math.cos(PITCH)))
    cam = Camera(yaw, scale, w / 2, h * .5 + scale * 3.4)

    # ground plate
    pad = 1.4
    corners = [(-width / 2 - pad, -depth / 2 - pad), (width / 2 + pad, -depth / 2 - pad),
               (width / 2 + pad, depth / 2 + pad), (-width / 2 - pad, depth / 2 + pad)]
    plate = [cam.project(x, 0, z) for x, z in corners]
    draw.polygon(plate, fill=(10, 8, 34) if dark else (238, 232, 255), outline=_hex(theme["pink"]))
    # streets: glowing lines between districts
    street = _hex(theme["pink"]) if dark else _hex(theme["violet"])
    block_w, block_d = 6, 7
    for i in range(1, 4):
        x = -width / 2 + i * (block_w + GAP) - GAP / 2
        draw.line([cam.project(x, 0, -depth / 2 - pad), cam.project(x, 0, depth / 2 + pad)], fill=street, width=SS)
    for j in range(1, 3):
        z = -depth / 2 + j * (block_d + GAP) - GAP / 2
        draw.line([cam.project(-width / 2 - pad, 0, z), cam.project(width / 2 + pad, 0, z)], fill=street, width=SS)

    heat = [_hex(c) for c in theme["heat"]]
    body = (22, 20, 58) if dark else (150, 138, 214)
    lit = [_hex(theme["amber"]), (255, 232, 163), _hex(theme["cyan"])] if dark else [(240, 248, 255), (255, 255, 255), (220, 236, 255)]
    show_x = 1 if cam.sin > 0 else -1  # which ±x face points at the viewer
    show_z = 1 if cam.cos > 0 else -1
    order = sorted(buildings, key=lambda b: cam.rotate(b.x, b.z)[1])
    half = FOOT / 2
    for b in order:
        x0, x1, z0, z1 = b.x - half, b.x + half, b.z - half, b.z + half
        top_color = heat[b.level] if b.count else (heat[0] if dark else (214, 208, 240))
        if not b.count:
            quad = [cam.project(x0, b.h, z0), cam.project(x1, b.h, z0), cam.project(x1, b.h, z1), cam.project(x0, b.h, z1)]
            draw.polygon(quad, fill=top_color)
            continue
        side_base = _mix(body, top_color, .35)
        # x-facing side
        fx = x1 if show_x > 0 else x0
        face_x = [cam.project(fx, 0, z0), cam.project(fx, 0, z1), cam.project(fx, b.h, z1), cam.project(fx, b.h, z0)]
        draw.polygon(face_x, fill=_shade(side_base, .85 if dark else .92))
        fz = z1 if show_z > 0 else z0
        face_z = [cam.project(x0, 0, fz), cam.project(x1, 0, fz), cam.project(x1, b.h, fz), cam.project(x0, b.h, fz)]
        draw.polygon(face_z, fill=_shade(side_base, .62 if dark else .78))
        # windows on the two visible faces
        for face, u, v, ci in b.windows:
            if face == 0 and show_x > 0 or face == 1 and show_x < 0:
                zc = z0 + u * FOOT
                pts = [cam.project(fx, v, zc - .09), cam.project(fx, v, zc + .09),
                       cam.project(fx, v + .22, zc + .09), cam.project(fx, v + .22, zc - .09)]
            elif face == 2 and show_z > 0 or face == 3 and show_z < 0:
                xc = x0 + u * FOOT
                pts = [cam.project(xc - .09, v, fz), cam.project(xc + .09, v, fz),
                       cam.project(xc + .09, v + .22, fz), cam.project(xc - .09, v + .22, fz)]
            else:
                continue
            draw.polygon(pts, fill=lit[ci])
        roof = [cam.project(x0, b.h, z0), cam.project(x1, b.h, z0), cam.project(x1, b.h, z1), cam.project(x0, b.h, z1)]
        draw.polygon(roof, fill=top_color, outline=_shade(top_color, 1.25) if dark else _shade(top_color, .85))
        if b.level >= 4:  # rooftop beacon on the hottest days
            bx, by = cam.project(b.x, b.h + .35, b.z)
            r = 2.2 * SS
            draw.ellipse([bx - r, by - r, bx + r, by + r], fill=(255, 45, 85))
    # month labels at each district's corner nearest the viewer, drawn on top
    label_fill = _hex(theme["text"]) if dark else (60, 52, 120)
    chip = (12, 10, 40) if dark else (246, 243, 255)
    for x0, z0, text in labels:
        corners = [(x0, z0), (x0 + block_w, z0), (x0 + block_w, z0 + block_d), (x0, z0 + block_d)]
        cx, cz = max(corners, key=lambda c: cam.rotate(*c)[1])
        # nudge out into the street, away from the district centre
        mx, mz = x0 + block_w / 2, z0 + block_d / 2
        nx, nz = cx + (cx - mx) * .12, cz + (cz - mz) * .12
        sx, sy = cam.project(nx, 0, nz)
        box = draw.textbbox((sx, sy), text, font=fonts["label"], anchor="mm")
        draw.rounded_rectangle([box[0] - 5 * SS, box[1] - 3 * SS, box[2] + 5 * SS, box[3] + 3 * SS], radius=4 * SS,
                               fill=chip, outline=street)
        draw.text((sx, sy), text, font=fonts["label"], fill=label_fill, anchor="mm")
    return img


def _overlay(img: Image.Image, data: Data, theme: dict, fonts) -> Image.Image:
    draw = ImageDraw.Draw(img)
    s = SS
    text = _hex(theme["text"]) if theme["name"] == "dark" else (27, 30, 69)
    muted = _hex(theme["muted"])
    accent = _hex(theme["cyan"])
    year = stats.last_year(data)
    best = stats.best_day(year)
    total = data.totals.contributions_year
    draw.text((26 * s, 24 * s), "CONTRIBUTION CITY", font=fonts["title"], fill=text)
    draw.rectangle([26 * s, 52 * s, 66 * s, 54 * s], fill=accent)
    sub = f"LAST 12 MONTHS · {total:,} CONTRIBUTIONS"
    draw.text((26 * s, 62 * s), sub, font=fonts["small"], fill=muted)
    right = (OUT_W - 26) * s
    if best:
        draw.text((right, 26 * s), "TALLEST TOWER", font=fonts["small"], fill=muted, anchor="ra")
        draw.text((right, 42 * s), f"{best.count} / {best.date:%d %b %Y}".upper().replace("0", "O"), font=fonts["stat"], fill=text, anchor="ra")
    else:
        draw.text((right, 26 * s), "NO TOWERS YET", font=fonts["small"], fill=muted, anchor="ra")
        draw.text((right, 42 * s), "FIRST COMMIT BUILDS ONE", font=fonts["small"], fill=text, anchor="ra")
    # legend
    lx, ly = 26 * s, (OUT_H - 30) * s
    draw.text((lx, ly), "LESS", font=fonts["small"], fill=muted, anchor="lm")
    for i, color in enumerate(theme["heat"]):
        x = lx + 42 * s + i * 16 * s
        draw.rectangle([x, ly - 5 * s, x + 11 * s, ly + 6 * s], fill=_hex(color))
    draw.text((lx + 42 * s + 5 * 16 * s + 4 * s, ly), "MORE", font=fonts["small"], fill=muted, anchor="lm")
    draw.text((right, ly), f"GITHUB.COM/{data.login.upper()}", font=fonts["small"], fill=muted, anchor="rm")
    return img


def render(cfg: Config, data: Data, theme: dict) -> bytes:
    fonts = {
        "title": _font("Orbitron-Black.ttf", 22 * SS),
        "stat": _font("Orbitron-Bold.ttf", 15 * SS),
        "small": _font("JetBrainsMono-Bold.ttf", 10 * SS),
        "label": _font("JetBrainsMono-Bold.ttf", 11 * SS),
    }
    buildings, labels, width, depth = _layout(data)
    base = _background(theme)
    frames = []
    for i in range(FRAMES):
        yaw = math.radians(30) + 2 * math.pi * i / FRAMES
        big = _frame(base, buildings, labels, width, depth, yaw, theme, fonts)
        big = _overlay(big, data, theme, fonts)
        frames.append(big.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS))
    # One shared palette from a sample of frames keeps colours stable (no flicker).
    sample = Image.new("RGB", (OUT_W, OUT_H * 4))
    for k, idx in enumerate(range(0, FRAMES, FRAMES // 4)):
        if k < 4:
            sample.paste(frames[idx], (0, OUT_H * k))
    # Small-but-important colours (legend swatches, text) get exact slots so median-cut can't merge them away.
    reserved = [_hex(c) for c in theme["heat"]] + [_hex(theme[k]) for k in ("text", "muted", "cyan", "pink")]
    reserved += [(27, 30, 69), (255, 45, 85)]
    learned = sample.quantize(colors=COLORS - len(reserved), method=Image.Quantize.MEDIANCUT)
    entries = learned.getpalette()[: 3 * (COLORS - len(reserved))]
    for rgb in reserved:
        entries += list(rgb)
    palette = Image.new("P", (1, 1))
    # Unused slots get a colour nothing in the scene is near, so no pixel lands on the transparent index.
    palette.putpalette(entries + [0, 255, 0] * (256 - COLORS))
    quantized = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    return _encode(quantized)


def _encode(frames: list[Image.Image]) -> bytes:
    """Pixels unchanged since the previous frame become transparent, which LZW compresses well."""
    transparent = COLORS  # first unused palette slot
    out = [frames[0]]
    previous = frames[0].tobytes()
    for frame in frames[1:]:
        current = frame.tobytes()
        delta = bytes(transparent if a == b else a for a, b in zip(current, previous))
        image = Image.frombytes("P", frame.size, delta)
        image.putpalette(frame.getpalette())
        image.info["transparency"] = transparent
        out.append(image)
        previous = current
    buffer = io.BytesIO()
    out[0].save(buffer, format="GIF", save_all=True, append_images=out[1:], duration=FRAME_MS, loop=0,
                optimize=False, disposal=1, transparency=transparent)
    return buffer.getvalue()
