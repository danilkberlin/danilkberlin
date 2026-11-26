"""Shared SVG toolkit: embedded fonts, frames and animation helpers.

Colours come from the theme dict each card receives (see generator/palettes.py).

GitHub shows README images through its camo proxy inside <img>, so every SVG
must be fully self-contained: no scripts, no external fonts/images, no hover.
CSS @keyframes and SMIL both animate fine there. Conventions used throughout:

* An element's *base* style is its final, settled state; intro animations
  only define `from` keyframes and use `both` fill. That keeps the image
  correct under `prefers-reduced-motion` and in renderers without animation.
* Text uses two embedded font families, subset to exactly the glyphs used:
  `Orb` (Orbitron, display) and `JBM` (JetBrains Mono, data).
"""
from __future__ import annotations

import base64
import functools
import io
import html
import math
import re
from xml.etree import ElementTree
from dataclasses import dataclass

from fontTools import subset
from fontTools.ttLib import TTFont

from ..config import ASSETS

W = 840  # full-width card
HALF = 412  # two per row with a gap


# ─────────────────────────────────────────────────────────────── fonts ───

@dataclass(frozen=True)
class FontSpec:
    file: str
    family: str
    weight: int


FONTS = {
    "o": FontSpec("Orbitron-Black.ttf", "Orb", 900),
    "o7": FontSpec("Orbitron-Bold.ttf", "Orb", 700),
    "m": FontSpec("JetBrainsMono-Regular.ttf", "JBM", 400),
    "mb": FontSpec("JetBrainsMono-Bold.ttf", "JBM", 700),
}

FONT_CSS = """
.o{font-family:Orb,JBM,sans-serif;font-weight:900}
.o7{font-family:Orb,JBM,sans-serif;font-weight:700}
.m{font-family:JBM,ui-monospace,monospace;font-weight:400}
.mb{font-family:JBM,ui-monospace,monospace;font-weight:700}
"""


@functools.lru_cache(maxsize=None)
def _font(key: str) -> TTFont:
    return TTFont(ASSETS / "fonts" / FONTS[key].file)


@functools.lru_cache(maxsize=None)
def _advances(key: str) -> tuple[dict[int, int], int, int]:
    font = _font(key)
    cmap = font.getBestCmap()
    hmtx = font["hmtx"].metrics
    widths = {cp: hmtx[name][0] for cp, name in cmap.items()}
    return widths, font["head"].unitsPerEm, hmtx[".notdef"][0]


def text_width(text: str, key: str, size: float, spacing: float = 0.0) -> float:
    """Exact advance width of `text` in pixels (falls back to JBM for missing glyphs)."""
    widths, upm, fallback = _advances(key)
    mono_widths, mono_upm, _ = _advances("m")
    total = 0.0
    for char in text:
        cp = ord(char)
        if cp in widths:
            total += widths[cp] / upm
        else:
            total += mono_widths.get(cp, 600) / mono_upm
    return total * size + spacing * max(0, len(text) - 1)


def fit_size(text: str, key: str, max_width: float, size: float, spacing: float = 0.0, minimum: float = 8) -> float:
    while size > minimum and text_width(text, key, size, spacing) > max_width:
        size -= 0.5
    return size


@functools.lru_cache(maxsize=256)
def _subset_b64(key: str, chars: str) -> str | None:
    font = TTFont(ASSETS / "fonts" / FONTS[key].file)
    supported = set(font.getBestCmap())
    wanted = {ord(c) for c in chars} & supported
    if not wanted:
        return None
    unslash = FONTS[key].family == "Orb" and ord("0") in wanted
    if unslash:
        wanted.add(ord("O"))
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["kern", "liga", "calt"]
    options.name_IDs = []
    options.hinting = False
    options.desubroutinize = True
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=wanted)
    subsetter.subset(font)
    if unslash:
        # Orbitron's slashed zero reads as "Ø" at display sizes; its O is the same shape unslashed.
        for table in font["cmap"].tables:
            if ord("0") in table.cmap and ord("O") in table.cmap:
                table.cmap[ord("0")] = table.cmap[ord("O")]
    buffer = io.BytesIO()
    font.flavor = "woff2"
    font.save(buffer)
    return base64.b64encode(buffer.getvalue()).decode()


def _used_glyphs(body: str) -> dict[str, str]:
    """Characters per font key, following class inheritance through the element tree."""
    used: dict[str, set[str]] = {key: set() for key in FONTS}
    root = ElementTree.fromstring(f'<svg xmlns="http://www.w3.org/2000/svg">{body}</svg>')

    def walk(element, inherited: str, in_text: bool) -> None:
        classes = (element.get("class") or "").split()
        key = next((c for c in classes if c in FONTS), inherited)
        tag = element.tag.rsplit("}", 1)[-1]
        is_text = in_text or tag in ("text", "tspan", "textPath")
        if is_text and element.text:
            _add(used, key, element.text)
        for child in element:
            walk(child, key, is_text)
            if is_text and child.tail:
                _add(used, key, child.tail)

    walk(root, "m", False)
    return {key: "".join(sorted(chars)) for key, chars in used.items() if "".join(chars).strip()}


def _add(used: dict[str, set[str]], key: str, text: str) -> None:
    used[key].update(text)
    # Glyphs the display font lacks (e.g. "°") fall back to JBM regular.
    used["m"].update(ch for ch in text if ord(ch) not in _advances(key)[0])


def font_faces(body: str) -> str:
    faces = []
    for key, chars in _used_glyphs(body).items():
        data = _subset_b64(key, chars)
        if data:
            spec = FONTS[key]
            faces.append(
                f"@font-face{{font-family:{spec.family};font-weight:{spec.weight};"
                f"src:url(data:font/woff2;base64,{data}) format('woff2')}}"
            )
    return "\n".join(faces)


# ─────────────────────────────────────────────────────────── documents ───

BASE_CSS = """
text{dominant-baseline:auto}
.fade{animation:fade .8s ease both}
.up{animation:up .8s cubic-bezier(.2,.8,.2,1) both}
.pop{animation:pop .6s cubic-bezier(.3,1.6,.5,1) both;transform-box:fill-box;transform-origin:center}
.draw{stroke-dasharray:1;stroke-dashoffset:0;animation:draw 2s ease-out both}
.roll{animation:roll 2.2s cubic-bezier(.15,.85,.25,1) both}
.growy{transform-box:fill-box;transform-origin:50% 100%;animation:growy 1s cubic-bezier(.2,.9,.3,1.2) both}
.growx{transform-box:fill-box;transform-origin:0 50%;animation:growx 1.1s cubic-bezier(.2,.9,.3,1) both}
.blink{animation:blink 1.05s steps(1) infinite}
.twinkle{animation:twinkle 3s ease-in-out infinite}
.cover{animation:cover 1s both}
@keyframes fade{from{opacity:0}}
@keyframes up{from{opacity:0;transform:translateY(12px)}}
@keyframes pop{from{opacity:0;transform:scale(.4)}}
@keyframes draw{from{stroke-dashoffset:1}}
@keyframes roll{from{transform:translateY(0)}}
@keyframes growy{from{transform:scaleY(0)}}
@keyframes growx{from{transform:scaleX(0)}}
@keyframes blink{50%{opacity:0}}
@keyframes twinkle{0%,100%{opacity:.25}50%{opacity:1}}
@keyframes cover{from{transform:translateX(0)}}
@media (prefers-reduced-motion: reduce){
  *{animation-duration:1ms!important;animation-delay:0s!important;animation-iteration-count:1!important}
}
"""


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def document(width: float, height: float, body: str, theme: dict, *, css: str = "", title: str = "",
             defs: str = "") -> str:
    style = f"{font_faces(body)}\n{FONT_CSS}{BASE_CSS}{css}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:g}" height="{height:g}" '
        f'viewBox="0 0 {width:g} {height:g}" role="img" aria-label="{esc(title)}">'
        f"<title>{esc(title)}</title>"
        f"<style>{_minify_css(style)}</style>"
        f"<defs>{glow_filter('glow', 3 * theme['glow'] + 0.5)}{glow_filter('glow2', 7 * theme['glow'] + 1)}{defs}</defs>"
        f"{body}</svg>"
    )


def _minify_css(css: str) -> str:
    css = re.sub(r"\s*\n\s*", "", css)
    return re.sub(r"\s*([{};:,])\s*", r"\1", css)


def glow_filter(fid: str, blur: float) -> str:
    return (
        f'<filter id="{fid}" x="-50%" y="-50%" width="200%" height="200%">'
        f'<feGaussianBlur stdDeviation="{blur:.2f}" result="b"/>'
        f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    )


def panel(width: float, height: float, theme: dict, *, x: float = 0, y: float = 0, radius: float = 18,
          accent: str | None = None, uid: str = "p") -> str:
    """Card background with a soft vertical gradient and a hairline border."""
    accent = accent or theme["cyan"]
    return (
        f'<defs><linearGradient id="{uid}bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{theme["panel2"]}"/><stop offset="1" stop-color="{theme["panel"]}"/>'
        f'</linearGradient><linearGradient id="{uid}edge" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{accent}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{accent}" stop-opacity=".9"/>'
        f'<stop offset="1" stop-color="{accent}" stop-opacity="0"/></linearGradient></defs>'
        f'<rect x="{x + .5}" y="{y + .5}" width="{width - 1}" height="{height - 1}" rx="{radius}" '
        f'fill="url(#{uid}bg)" stroke="{theme["line"]}"/>'
        f'<rect x="{x + radius}" y="{y}" width="{width - 2 * radius}" height="1.5" fill="url(#{uid}edge)"/>'
    )


def label(x: float, y: float, text: str, theme: dict, *, color: str | None = None, delay: float = 0) -> str:
    """Section label: neon diamond + spaced uppercase mono."""
    color = color or theme["cyan"]
    return (
        f'<g class="fade" style="animation-delay:{delay}s">'
        f'<rect x="{x}" y="{y - 8}" width="7" height="7" transform="rotate(45 {x + 3.5} {y - 4.5})" '
        f'fill="{color}" filter="url(#glow)"/>'
        f'<text x="{x + 16}" y="{y}" class="mb" font-size="11" letter-spacing="2.2" fill="{theme["muted"]}">'
        f"{esc(text.upper())}</text></g>"
    )


def _odometer_parts(value: int, cls: str, size: float, separators: bool) -> tuple[str, list[float]]:
    text = f"{value:,}" if separators else str(value)
    return text, [text_width(ch, cls, size) for ch in text]


def odometer_width(value: int, size: float, *, cls: str = "o7", separators: bool = True) -> float:
    return sum(_odometer_parts(value, cls, size, separators)[1])


def odometer(value: int, x: float, y: float, size: float, theme: dict, *, color: str, cls: str = "o7",
             delay: float = 0, anchor: str = "start", spins: int = 1, separators: bool = True) -> str:
    """Rolling digits. Each digit is a vertical strip that rolls up to its final value.

    `y` is the baseline. The rendered width is `odometer_width(value, size, cls=cls)`.
    """
    text, widths = _odometer_parts(value, cls, size, separators)
    # Slots advance proportionally (so "11" stays tight), but each clip window is as wide
    # as the widest digit, centred on its slot, so wide digits never clip mid-roll.
    window = max(text_width(str(n), cls, size) for n in range(10)) + 4
    line = size * 1.25
    total = sum(widths)
    left = x - total if anchor == "end" else x - total / 2 if anchor == "middle" else x
    parts = []
    cursor = left
    digits = [c for c in text if c.isdigit()]
    digit_index = 0
    for ch, width in zip(text, widths):
        if not ch.isdigit():
            parts.append(f'<text x="{cursor:.1f}" y="{y:.1f}" class="{cls}" font-size="{size}" fill="{color}">{esc(ch)}</text>')
            cursor += width
            continue
        target = int(ch)
        # Later digits spin more, like a real counter.
        laps = spins + (digit_index * 1) // max(1, len(digits) - 1) if len(digits) > 1 else spins
        strip = [str(n % 10) for n in range(laps * 10 + target + 1)]
        offset = (len(strip) - 1) * line
        mid = cursor + width / 2
        tspans = "".join(
            f'<tspan x="{mid:.1f}" y="{y + i * line:.1f}">{n}</tspan>' for i, n in enumerate(strip)
        )
        d = delay + 0.08 * digit_index
        parts.append(
            f'<svg x="{mid - window / 2:.1f}" y="{y - size * 1.02:.1f}" width="{window:.1f}" height="{size * 1.3:.1f}" overflow="hidden">'
            f'<g transform="translate({-(mid - window / 2):.1f} {-(y - size * 1.02):.1f})">'
            f'<g class="roll" style="transform:translateY(-{offset:.1f}px);animation-delay:{d:.2f}s">'
            f'<text class="{cls}" font-size="{size}" fill="{color}" text-anchor="middle">{tspans}</text></g></g></svg>'
        )
        cursor += width
        digit_index += 1
    return "".join(parts)


def typed(x: float, y: float, text: str, *, cls: str, size: float, fill: str, cover: str, delay: float,
          cps: float = 28, spacing: float = 0, extra: str = "", cursor: str | None = None,
          cursor_until: float | None = None) -> tuple[str, float]:
    """Typewriter reveal: a cover rect (solid `cover` colour) slides right in steps.

    Returns (markup, end_time). Needs a solid background colour behind the text.
    """
    width = text_width(text, cls, size, spacing)
    n = max(1, len(text))
    duration = n / cps
    h = size * 1.5
    top = y - size * 1.15
    caret = ""
    if cursor:
        # pre: hidden until typing starts · cover: rides along with the text ·
        # blink: idles at the end · hide: disappears when the next line takes over.
        animations = [
            f"pre {max(delay, .01):.2f}s linear backwards",
            f"cover {duration:.2f}s steps({n}) {delay:.2f}s both",
            f"blink 1.05s steps(1) {delay + duration:.2f}s infinite",
        ]
        if cursor_until is not None:
            animations.append(f"hide .01s linear {cursor_until:.2f}s forwards")
        caret = (
            f'<rect x="{x + 1:.1f}" y="{top + size * .25:.1f}" width="{size * .58:.1f}" height="{size * 1.15:.1f}" '
            f'fill="{cursor}" style="transform:translateX({width + 2:.1f}px);animation:{",".join(animations)}"/>'
        )
    markup = (
        f'<svg x="{x - 2:.1f}" y="{top:.1f}" width="{width + size + 6:.1f}" height="{h:.1f}" overflow="hidden">'
        f'<text x="2" y="{y - top:.1f}" class="{cls}" font-size="{size}" fill="{fill}" '
        f'letter-spacing="{spacing}" {extra}>{esc(text)}</text>'
        f'<rect x="0" y="0" width="{width + size + 6:.1f}" height="{h:.1f}" fill="{cover}" '
        f'style="transform:translateX({width + 4:.1f}px);animation:cover {duration:.2f}s steps({n}) {delay:.2f}s both"/>'
        f"</svg>{caret}"
    )
    return markup, delay + duration


TYPED_CSS = """
@keyframes pre{from,to{opacity:0}}
@keyframes hide{from,to{opacity:0}}
"""


def polar(cx: float, cy: float, r: float, angle_deg: float) -> tuple[float, float]:
    a = math.radians(angle_deg - 90)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def arc_path(cx: float, cy: float, r: float, start: float, end: float) -> str:
    x1, y1 = polar(cx, cy, r, start)
    x2, y2 = polar(cx, cy, r, end)
    large = 1 if (end - start) % 360 > 180 else 0
    return f"M{x1:.2f},{y1:.2f} A{r},{r} 0 {large} 1 {x2:.2f},{y2:.2f}"


def smooth_path(points: list[tuple[float, float]]) -> str:
    """Catmull-Rom → cubic Bézier, for friendly sparklines."""
    if len(points) < 2:
        return ""
    d = f"M{points[0][0]:.1f},{points[0][1]:.1f}"
    for i in range(len(points) - 1):
        p0 = points[i - 1] if i else points[i]
        p1, p2 = points[i], points[i + 1]
        p3 = points[i + 2] if i + 2 < len(points) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


def compact(n: int) -> str:
    if n >= 10_000:
        return f"{n / 1000:.0f}K"
    if n >= 1000:
        return f"{n / 1000:.1f}K"
    return str(n)


def ago(delta_seconds: float) -> str:
    minutes = delta_seconds / 60
    if minutes < 60:
        return f"{max(1, int(minutes))}m ago"
    hours = minutes / 60
    if hours < 24:
        return f"{int(hours)}h ago"
    days = hours / 24
    if days < 30:
        return f"{int(days)}d ago"
    if days < 365:
        return f"{int(days / 30)}mo ago"
    return f"{int(days / 365)}y ago"


def wrap(text: str, key: str, size: float, max_width: float, max_lines: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if text_width(candidate, key, size) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and " ".join(lines) != " ".join(words):
        last = lines[-1]
        while last and text_width(last + "…", key, size) > max_width:
            last = last[:-1].rstrip()
        lines[-1] = last + "…"
    return lines
