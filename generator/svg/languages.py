"""Language Orbit: languages as planets circling a glowing monogram sun."""
from __future__ import annotations

import colorsys
import math
import random

from ..config import Config
from ..model import Data
from .core import HALF, document, esc, fit_size, label, panel, text_width

H = 300
CX, CY = 120, 174  # sun centre
TILT = -16  # orbit plane tilt in degrees
MAX_PLANETS = 6
LEGEND_X = 244
LEGEND_RIGHT = HALF - 22


# ───────────────────────────────────────────────────────── colour helpers ───

def _rgb(color: str) -> tuple[int, int, int]:
    value = color.lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in rgb)


def _luminance(color: str) -> float:
    def channel(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in _rgb(color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _mix(color: str, other: str, t: float) -> str:
    a, b = _rgb(color), _rgb(other)
    return _hex(tuple(x + (y - x) * t for x, y in zip(a, b)))


def visible(color: str, theme: dict) -> str:
    """Shift lightness (keeping hue and saturation) until the colour reads on the panel.

    Linguist colours can be nearly black (#555555, #384d54) on the dark theme or
    nearly white (#f1e05a) on the light one.
    """
    color = color or theme["muted"]
    r, g, b = (c / 255 for c in _rgb(color))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    dark = theme["name"] == "dark"
    for _ in range(30):
        candidate = _hex(tuple(c * 255 for c in colorsys.hls_to_rgb(h, l, s)))
        lum = _luminance(candidate)
        if (dark and lum >= 0.17) or (not dark and lum <= 0.5):
            return candidate
        l = min(0.92, l + 0.025) if dark else max(0.12, l - 0.025)
    return candidate


def outline(color: str, theme: dict) -> str:
    return _mix(color, "#ffffff", 0.45) if theme["name"] == "dark" else _mix(color, "#000000", 0.35)


# ───────────────────────────────────────────────────────────── geometry ───

def _orbit_path(rx: float, ry: float, start_deg: float) -> str:
    """Full ellipse around (CX, CY) as two arcs, beginning at `start_deg`.

    animateMotion starts at the first point of the path, so the start angle
    gives every planet its own phase without negative `begin` offsets.
    """
    a = math.radians(start_deg)
    x1, y1 = CX + rx * math.cos(a), CY + ry * math.sin(a)
    x2, y2 = CX - rx * math.cos(a), CY - ry * math.sin(a)
    return (
        f"M{x1:.2f},{y1:.2f} A{rx:.2f},{ry:.2f} 0 1 1 {x2:.2f},{y2:.2f} "
        f"A{rx:.2f},{ry:.2f} 0 1 1 {x1:.2f},{y1:.2f}Z"
    )


def _percent(share: float) -> str:
    pct = share * 100
    if pct < 1:
        return "<1%"
    return f"{pct:.1f}%" if pct < 10 else f"{pct:.0f}%"


def _size(total: int) -> str:
    if total >= 1_000_000:
        return f"{total / 1_000_000:.1f} MB"
    if total >= 1000:
        return f"{total / 1000:.0f} KB"
    return f"{total} B"


def _truncate(text: str, key: str, size: float, width: float) -> str:
    if text_width(text, key, size) <= width:
        return text
    while text and text_width(text + "…", key, size) > width:
        text = text[:-1]
    return text.rstrip() + "…"


# ─────────────────────────────────────────────────────────────── render ───

def _sun(cfg: Config, theme: dict) -> str:
    dark = theme["name"] == "dark"
    initials = cfg.initials[:3]
    size = fit_size(initials, "o", 26, 13)
    core_text = theme["bg"] if dark else "#ffffff"
    return (
        f'<defs><radialGradient id="corona"><stop offset="0" stop-color="{theme["amber"]}" stop-opacity=".55"/>'
        f'<stop offset=".45" stop-color="{theme["pink"]}" stop-opacity=".18"/>'
        f'<stop offset="1" stop-color="{theme["pink"]}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="suncore" cx=".38" cy=".32" r=".75"><stop offset="0" stop-color="{theme["sun_core"]}"/>'
        f'<stop offset=".45" stop-color="{theme["amber"]}"/><stop offset="1" stop-color="{theme["pink"]}"/></radialGradient></defs>'
        f'<circle cx="{CX}" cy="{CY}" r="46" fill="url(#corona)" class="corona"/>'
        f'<g class="pop" style="animation-delay:.15s">'
        f'<circle cx="{CX}" cy="{CY}" r="19" fill="url(#suncore)" filter="url(#glow)"/>'
        f'<text x="{CX}" y="{CY + size * .36:.1f}" text-anchor="middle" class="o" font-size="{size}" '
        f'fill="{core_text}" letter-spacing=".5">{esc(initials)}</text></g>'
    )


def _starfield(theme: dict) -> str:
    if theme["name"] != "dark":
        return ""
    rng = random.Random(7)
    dots = []
    for _ in range(26):
        x, y = rng.uniform(16, 228), rng.uniform(48, H - 16)
        if math.hypot(x - CX, (y - CY) * 2) < 70:
            continue
        dots.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.choice([.5, .7, .9])}" fill="{theme["text"]}" class="twinkle" '
            f'style="animation-duration:{rng.uniform(2.5, 5):.1f}s;animation-delay:-{rng.uniform(0, 5):.1f}s"/>'
        )
    return f'<g opacity=".55">{"".join(dots)}</g>'


def render(cfg: Config, data: Data, theme: dict) -> str:
    dark = theme["name"] == "dark"
    langs = data.languages[:MAX_PLANETS]
    total = sum(b for _, b, _ in data.languages)
    n = len(langs)

    orbits, planets, legend = [], [], []
    count = n or 3  # empty state still shows a little solar system
    for i in range(count):
        rx = 50 + (i + 0.5) / count * 56
        ry = rx * 0.5
        tint = visible(langs[i][2], theme) if i < n else theme["muted"]
        orbits.append(
            f'<ellipse cx="{CX}" cy="{CY}" rx="{rx:.1f}" ry="{ry:.1f}" fill="none" stroke="{tint}" '
            f'stroke-opacity="{.45 if dark else .55}" stroke-width=".9" stroke-dasharray="2 4" class="orbit" '
            f'style="animation-delay:{.1 + i * .08:.2f}s"/>'
        )
        if i >= n:
            continue
        name, size, color = langs[i]
        share = size / total if total else 0
        fill = visible(color, theme)
        r = 3.2 + 8.5 * math.sqrt(share)
        start = (i * 137.5 + 20) % 360  # golden-angle spread of starting phases
        duration = 9 + i * 4.5
        path = _orbit_path(rx, ry, start)
        planets.append(
            f'<g class="pop" style="animation-delay:{.5 + i * .12:.2f}s">'
            f'<g><circle r="{r + 3.5:.1f}" fill="{fill}" opacity=".22"/>'
            f'<circle r="{r:.1f}" fill="url(#pl{i})" stroke="{outline(fill, theme)}" stroke-width=".9"/>'
            f'<animateMotion dur="{duration:.1f}s" repeatCount="indefinite" path="{path}"/></g></g>'
        )
        planets.append(
            f'<defs><radialGradient id="pl{i}" cx=".35" cy=".3" r=".8">'
            f'<stop offset="0" stop-color="{_mix(fill, "#ffffff", .55)}"/><stop offset=".55" stop-color="{fill}"/>'
            f'<stop offset="1" stop-color="{_mix(fill, "#000000", .35)}"/></radialGradient></defs>'
        )

        # legend row
        y = 70 + i * 34
        bar_w = LEGEND_RIGHT - (LEGEND_X + 12)
        pct = _percent(share)
        pct_w = text_width(pct, "m", 10.5)
        name_fit = _truncate(name, "mb", 11, bar_w - pct_w - 8)
        delay = .6 + i * .12
        legend.append(
            f'<g class="up" style="animation-delay:{delay:.2f}s">'
            f'<circle cx="{LEGEND_X + 3}" cy="{y - 4}" r="4" fill="{fill}" stroke="{outline(fill, theme)}" stroke-width=".8"/>'
            f'<text x="{LEGEND_X + 12}" y="{y}" class="mb" font-size="11" fill="{theme["text"]}">{esc(name_fit)}</text>'
            f'<text x="{LEGEND_RIGHT}" y="{y}" text-anchor="end" class="m" font-size="10.5" fill="{theme["muted"]}">{esc(pct)}</text>'
            f'<rect x="{LEGEND_X + 12}" y="{y + 7}" width="{bar_w}" height="4" rx="2" fill="{theme["line"]}"/>'
            f'<rect x="{LEGEND_X + 12}" y="{y + 7}" width="{max(3, bar_w * share):.1f}" height="4" rx="2" fill="{fill}" '
            f'class="growx" style="animation-delay:{delay + .25:.2f}s"/></g>'
        )

    if n:
        more = len(data.languages) - n
        footer = f"{len(data.languages)} LANGUAGES · {_size(total)}" + (f" · +{more} MORE" if more > 0 else "")
    else:
        footer = "AWAITING FIRST LAUNCH"
        mid = (LEGEND_X + LEGEND_RIGHT) / 2
        legend.append(
            f'<g class="fade" style="animation-delay:.6s">'
            f'<rect x="{LEGEND_X}" y="104" width="{LEGEND_RIGHT - LEGEND_X}" height="92" rx="12" fill="none" '
            f'stroke="{theme["faint"]}" stroke-dasharray="3 4"/>'
            f'<text x="{mid}" y="146" text-anchor="middle" class="o7" font-size="13" letter-spacing="1.5" '
            f'fill="{theme["text"]}">NO CODE YET</text>'
            f'<text x="{mid}" y="166" text-anchor="middle" class="m" font-size="10" fill="{theme["muted"]}">'
            f"first commit pending</text></g>"
        )
    footer_size = fit_size(footer, "m", LEGEND_RIGHT - LEGEND_X, 9.5, spacing=1.2, minimum=7.5)

    css = """
    .orbit{animation:fade 1.2s ease both}
    .corona{transform-box:fill-box;transform-origin:center;animation:corona 5s ease-in-out infinite}
    @keyframes corona{50%{transform:scale(1.12);opacity:.75}}
    """
    body = (
        panel(HALF, H, theme, accent=theme["amber"])
        + label(22, 32, "Language Orbit", theme, color=theme["amber"])
        + _starfield(theme)
        + f'<g transform="rotate({TILT} {CX} {CY})">{"".join(orbits)}</g>'
        + _sun(cfg, theme)
        + f'<g transform="rotate({TILT} {CX} {CY})">{"".join(planets)}</g>'
        + "".join(legend)
        + f'<text x="{LEGEND_X}" y="{H - 22}" class="m fade" font-size="{footer_size}" letter-spacing="1.2" '
        f'fill="{theme["muted"]}" style="animation-delay:1.4s">{esc(footer)}</text>'
    )
    title = "Languages: " + ", ".join(f"{name} {_percent(b / total)}" for name, b, _ in langs) if n else "Languages: none yet"
    return document(HALF, H, body, theme, css=css, title=title)
