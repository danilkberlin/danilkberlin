"""Tech-stack marquee: two rows of brand tiles scrolling in opposite directions.

Icons are Simple Icons (CC0) paths, defined once in <defs> and placed with
<use>. Each row is drawn once and then cloned with <use>, so the seamless
loop costs almost no extra bytes.
"""
from __future__ import annotations

import math
import re

from ..config import ASSETS, Config, StackItem
from ..model import Data
from .core import W, document, esc, label, panel, text_width

H = 180
TILE_H = 44
GAP = 12
ICON = 22
SPEED = 34  # px per second

# Brand colours from simple-icons@13.21.0.
BRAND = {
    "php": "#777BB4", "laravel": "#FF2D20", "filament": "#FDAE4B", "openjdk": "#000000", "python": "#3776AB",
    "javascript": "#F7DF1E", "mysql": "#4479A1", "postgresql": "#4169E1", "sqlite": "#003B57", "redis": "#FF4438",
    "docker": "#2496ED", "kubernetes": "#326CE5", "amazonwebservices": "#232F3E", "jenkins": "#D24939",
    "rabbitmq": "#FF6600", "newrelic": "#1CE783", "git": "#F05032", "githubactions": "#2088FF",
    "phpstorm": "#000000", "github": "#181717", "linkedin": "#0A66C2", "telegram": "#26A5E4",
}

# Logos that are wordmarks become unreadable at 22px; they get a monogram tile instead.
WORDMARKS = {"filament"}

_PATH_D = re.compile(r'<path[^>]*\sd="([^"]+)"')


def icon_path(icon: str) -> str:
    """The `d` of a Simple Icons SVG (24×24 viewBox, a single path)."""
    svg = (ASSETS / "icons" / f"{icon}.svg").read_text(encoding="utf-8")
    match = _PATH_D.search(svg)
    if not match:
        raise ValueError(f"no path in icon {icon}")
    return match.group(1)


def _rgb(color: str) -> tuple[float, float, float]:
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def _luminance(rgb: tuple[float, float, float]) -> float:
    def channel(c: float) -> float:
        return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return .2126 * r + .7152 * g + .0722 * b


def _contrast(a: tuple, b: tuple) -> float:
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + .05) / (lb + .05)


def legible(color: str, background: str, minimum: float = 3.0) -> str:
    """Mix a brand colour toward white (dark bg) or black (light bg) until it reads."""
    rgb, bg = _rgb(color), _rgb(background)
    target = (1.0, 1.0, 1.0) if _luminance(bg) < .2 else (0.0, 0.0, 0.0)
    for step in range(0, 21):
        k = step / 20
        mixed = tuple(c * (1 - k) + t * k for c, t in zip(rgb, target))
        if _contrast(mixed, bg) >= minimum:
            return "#" + "".join(f"{round(c * 255):02x}" for c in mixed)
    return "#" + "".join(f"{round(c * 255):02x}" for c in target)


def _tile_width(item: StackItem) -> float:
    return 12 + ICON + 9 + text_width(item.name, "mb", 12) + 14


def _tile(item: StackItem, x: float, y: float, theme: dict, tile_fill: str) -> str:
    width = _tile_width(item)
    ix, iy = x + 12, y + (TILE_H - ICON) / 2
    if item.icon and item.icon not in WORDMARKS:
        color = legible(BRAND.get(item.icon, theme["cyan"]), tile_fill, 4.5 if theme["name"] == "dark" else 3.0)
        glyph = (
            f'<use href="#i-{item.icon}" transform="translate({ix:.1f} {iy:.1f}) scale({ICON / 24:.4f})" fill="{color}"/>'
        )
    else:
        initials = (item.name[:2] if len(item.name.split()) == 1 else "".join(w[0] for w in item.name.split()[:2]))
        brand = BRAND.get(item.icon or "")
        fill = brand or "url(#mono)"
        ink = "#ffffff" if not brand or _luminance(_rgb(brand)) < .45 else "#1b1e45"
        glyph = (
            f'<rect x="{ix:.1f}" y="{iy:.1f}" width="{ICON}" height="{ICON}" rx="6" fill="{fill}"/>'
            f'<text x="{ix + ICON / 2:.1f}" y="{iy + 15:.1f}" text-anchor="middle" class="o7" font-size="10" '
            f'fill="{ink}">{esc(initials)}</text>'
        )
    return (
        f'<rect x="{x:.1f}" y="{y}" width="{width:.1f}" height="{TILE_H}" rx="12" fill="{tile_fill}" '
        f'stroke="{theme["line"]}"/>'
        f"{glyph}"
        f'<text x="{ix + ICON + 9:.1f}" y="{y + TILE_H / 2 + 4.3:.1f}" class="mb" font-size="12" '
        f'fill="{theme["text"]}">{esc(item.name)}</text>'
    )


def _row(items: list[StackItem], y: float, theme: dict, tile_fill: str, rid: str, direction: int) -> tuple[str, str]:
    x = 0.0
    tiles = []
    for item in items:
        tiles.append(_tile(item, x, y, theme, tile_fill))
        x += _tile_width(item) + GAP
    row_w = x
    copies = max(2, math.ceil((W + row_w) / max(row_w, 1)) + 1)
    clones = "".join(f'<use href="#{rid}" x="{row_w * k:.1f}"/>' for k in range(1, copies))
    duration = row_w / SPEED
    if direction < 0:  # scroll left
        keyframes = f"@keyframes {rid}{{from{{transform:translateX(0)}}to{{transform:translateX(-{row_w:.1f}px)}}}}"
    else:  # scroll right
        keyframes = f"@keyframes {rid}{{from{{transform:translateX(-{row_w:.1f}px)}}to{{transform:translateX(0)}}}}"
    base = "" if direction < 0 else f"transform:translateX(-{row_w / 2:.1f}px);"
    markup = (
        f'<g style="{base}animation:{rid} {duration:.1f}s linear infinite">'
        f'<g id="{rid}">{"".join(tiles)}</g>{clones}</g>'
    )
    return markup, keyframes


def render(cfg: Config, data: Data, theme: dict) -> str:
    dark = theme["name"] == "dark"
    tile_fill = theme["tile"]
    items = cfg.stack
    top_row = items[0::2]
    bottom_row = items[1::2]

    icons = sorted({item.icon for item in items if item.icon and item.icon not in WORDMARKS})
    defs = "".join(f'<path id="i-{icon}" d="{icon_path(icon)}"/>' for icon in icons)
    defs += (
        f'<linearGradient id="mono" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{theme["cyan"]}"/>'
        f'<stop offset="1" stop-color="{theme["violet"]}"/></linearGradient>'
        f'<linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".09" stop-color="#fff" stop-opacity="1"/>'
        f'<stop offset=".91" stop-color="#fff" stop-opacity="1"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>'
        f'</linearGradient><mask id="fade" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
        f'<rect x="1" y="44" width="{W - 2}" height="{H - 56}" fill="url(#edge)"/></mask>'
    )

    row1, kf1 = _row(top_row, 52, theme, tile_fill, "r1", -1)
    row2, kf2 = _row(bottom_row, 108, theme, tile_fill, "r2", 1)
    count = len(items)
    body = (
        panel(W, H, theme, accent=theme["violet"])
        + label(24, 34, "Tech stack · daily drivers", theme, color=theme["violet"])
        + f'<text x="{W - 24}" y="34" text-anchor="end" class="m fade" font-size="10" letter-spacing="1.2" '
        f'fill="{theme["faint"] if dark else theme["muted"]}">{count} TOOLS · BACKEND FIRST</text>'
        + f'<g mask="url(#fade)"><g class="fade" style="animation-delay:.2s">{row1}</g>'
        f'<g class="fade" style="animation-delay:.45s">{row2}</g></g>'
    )
    return document(W, H, body, theme, css=kf1 + kf2, defs=defs,
                    title="Tech stack: " + ", ".join(item.name for item in items))
