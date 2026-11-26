"""Trophy wall: ten tiered achievements computed from the profile data."""
from __future__ import annotations

import math

from .. import stats
from ..config import Config
from ..model import Data
from .core import W, document, esc, fit_size, label, panel

H = 272
COLS, ROWS = 5, 2
X0, Y0 = 20, 48
GAP_X, GAP_Y = 12, 10
BADGE_W = (W - 2 * X0 - (COLS - 1) * GAP_X) / COLS
BADGE_H = 100

# 24×24 line/solid icons, drawn by hand. ("fill" icons are solid shapes.)
ICONS: dict[str, tuple[str, str]] = {
    "flame": ("fill", '<path d="M12 2.5c.8 3.2 4.8 5.6 4.8 10.6a4.8 4.8 0 0 1-9.6 0c0-2.6 1.3-4.1 2.6-5.1.2 1.8.9 2.9 2.1 3.2-.6-3.2-.6-5.9.1-8.7z"/>'),
    "bolt": ("fill", '<path d="M13.5 2 4.5 13.5h6.5L9.8 22 19.5 10h-6.6z"/>'),
    "calendar": ("stroke", '<rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/>'
                 '<path d="M7.5 13.5h2v2h-2zM11 13.5h2v2h-2zM14.5 13.5h2v2h-2z" fill="currentColor" stroke="none"/>'),
    "globe": ("stroke", '<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/>'
              '<path d="M3 12h18M4.6 7.5h14.8M4.6 16.5h14.8"/>'),
    "merge": ("stroke", '<circle cx="6" cy="5.5" r="2.3"/><circle cx="6" cy="18.5" r="2.3"/><circle cx="18" cy="12" r="2.3"/>'
              '<path d="M6 7.8v8.4M6 7.8c0 3.6 3.4 4.2 9.7 4.2"/>'),
    "eye": ("stroke", '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/>'
            '<circle cx="12" cy="12" r="3" fill="currentColor" stroke="none"/>'),
    "moon": ("fill", '<path d="M19.5 14.6A8 8 0 1 1 9.4 4.5a6.3 6.3 0 0 0 10.1 10.1z"/>'
             '<path d="M17 3.5l.7 1.6 1.6.7-1.6.7-.7 1.6-.7-1.6-1.6-.7 1.6-.7z"/>'),
    "coffee": ("stroke", '<path d="M4.5 9.5h11v4.5a5 5 0 0 1-5 5h-1a5 5 0 0 1-5-5z"/><path d="M15.5 11h1.3a2.6 2.6 0 0 1 0 5.2h-1.6"/>'
               '<path d="M8 3.5c-.8 1 .8 1.8 0 3M11.5 3.5c-.8 1 .8 1.8 0 3M3.5 21.5h14"/>'),
    "cube": ("stroke", '<path d="M12 2.8 20.5 7.5v9L12 21.2 3.5 16.5v-9z"/><path d="M3.5 7.5 12 12.2l8.5-4.7M12 12.2v9"/>'),
    "shield": ("stroke", '<path d="M12 2.8 19.5 5.6v5.6c0 4.8-3.2 8.6-7.5 10.2-4.3-1.6-7.5-5.4-7.5-10.2V5.6z"/>'
               '<path d="M8.6 12.2l2.4 2.4 4.6-4.8"/>'),
}

LOCK = '<rect x="5" y="10.5" width="14" height="10" rx="2" fill="currentColor"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5" fill="none"/>'


def _accents(theme: dict) -> dict[str, tuple[str, str]]:
    t = theme
    return {
        "streak": (t["amber"], t["red"]),
        "centurion": (t["amber"], t["pink"]),
        "marathon": (t["cyan"], t["violet"]),
        "polyglot": (t["green"], t["cyan"]),
        "pilot": (t["violet"], t["pink"]),
        "reviewer": (t["cyan"], t["green"]),
        "owl": (t["violet"], t["cyan"]),
        "weekend": (t["pink"], t["amber"]),
        "builder": (t["cyan"], t["violet"]),
        "veteran": (t["amber"], t["green"]),
    }


def _hexagon(cx: float, cy: float, r: float) -> str:
    points = []
    for k in range(6):
        a = math.radians(60 * k - 90)
        points.append(f"{cx + r * math.cos(a):.2f},{cy + r * math.sin(a):.2f}")
    return " ".join(points)


def _icon(key: str, cx: float, cy: float, size: float, color: str) -> str:
    kind, markup = ICONS[key]
    scale = size / 24
    paint = (
        f'fill="{color}" stroke="none"' if kind == "fill"
        else f'fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    )
    return (
        f'<g transform="translate({cx - size / 2:.2f} {cy - size / 2:.2f}) scale({scale:.3f})" '
        f'color="{color}" {paint}>{markup}</g>'
    )


def _value(a: stats.Achievement) -> str:
    return f"{a.value:,}"


def _badge(i: int, a: stats.Achievement, theme: dict) -> str:
    dark = theme["name"] == "dark"
    col, row = i % COLS, i // COLS
    bx = X0 + col * (BADGE_W + GAP_X)
    by = Y0 + row * (BADGE_H + GAP_Y)
    c1, c2 = _accents(theme)[a.key]
    unlocked = a.unlocked
    cx, cy = bx + 32, by + 40
    text_x = bx + 62
    text_w = bx + BADGE_W - 12 - text_x

    parts = [f'<clipPath id="c{i}"><rect x="{bx:.1f}" y="{by}" width="{BADGE_W:.1f}" height="{BADGE_H}" rx="12"/></clipPath>']
    if unlocked:
        parts.append(
            f'<defs><linearGradient id="g{i}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/>'
            f'<stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
            f'<rect x="{bx + .5:.1f}" y="{by + .5}" width="{BADGE_W - 1:.1f}" height="{BADGE_H - 1}" rx="12" '
            f'fill="{c1}" fill-opacity="{.07 if dark else .06}" stroke="{c1}" stroke-opacity="{.45 if dark else .5}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="27" fill="{c1}" opacity=".16" class="halo" style="animation-delay:-{i * .6:.1f}s"/>'
            f'<polygon points="{_hexagon(cx, cy, 22)}" fill="url(#g{i})"' + (' filter="url(#glow)"' if dark else "") + "/>"
            f'<polygon points="{_hexagon(cx, cy, 18.5)}" fill="none" stroke="#ffffff" stroke-opacity=".35"/>'
            + _icon(a.icon, cx, cy, 19, theme["bg"] if dark else "#ffffff")
        )
    else:
        parts.append(
            f'<rect x="{bx + .5:.1f}" y="{by + .5}" width="{BADGE_W - 1:.1f}" height="{BADGE_H - 1}" rx="12" '
            f'fill="{theme["line"]}" fill-opacity="{.18 if dark else .25}" stroke="{theme["line"]}" stroke-dasharray="4 3"/>'
            f'<polygon points="{_hexagon(cx, cy, 22)}" fill="{theme["line"] if dark else theme["panel2"]}" '
            f'stroke="{theme["faint"]}" stroke-dasharray="3 2"/>'
            + _icon(a.icon, cx, cy, 18, theme["faint"] if dark else theme["faint"])
            + f'<circle cx="{cx + 16}" cy="{cy + 15}" r="7.5" fill="{theme["panel"]}" stroke="{theme["faint"]}"/>'
            + _icon_raw(LOCK, cx + 16, cy + 15, 9.5, theme["muted"])
        )

    # tier pips under the emblem
    for k in range(len(a.tiers)):
        px = cx - 1.5 * 8 + k * 8
        filled = k < a.tier
        parts.append(
            f'<rect x="{px - 2.3:.1f}" y="{by + 79.2:.1f}" width="4.6" height="4.6" rx="1" '
            f'transform="rotate(45 {px:.1f} {by + 81.5:.1f})" '
            f'fill="{c1 if filled else theme["line"]}"' + (' filter="url(#glow)"' if filled and dark else "") + "/>"
        )

    title_size = fit_size(a.title, "o7", text_w, 10.5, spacing=.6, minimum=7)
    value = _value(a)
    value_size = fit_size(value, "o", text_w, 17, minimum=10)
    unit_size = fit_size(a.unit, "m", text_w, 8.5, spacing=.3, minimum=6.5)
    title_color = theme["text"] if unlocked else theme["muted"]
    value_color = c1 if unlocked else theme["muted"]
    parts.append(
        f'<text x="{text_x}" y="{by + 26}" class="o7" font-size="{title_size}" letter-spacing=".6" fill="{title_color}">{esc(a.title)}</text>'
        f'<text x="{text_x}" y="{by + 50}" class="o" font-size="{value_size}" fill="{value_color}">{esc(value)}</text>'
        f'<text x="{text_x}" y="{by + 64}" class="m" font-size="{unit_size}" letter-spacing=".3" fill="{theme["muted"]}">{esc(a.unit)}</text>'
    )

    # progress toward the next tier
    bar_w = text_w
    fill_w = max(2.0, bar_w * a.progress) if (a.progress or unlocked) else 0
    goal = a.next_goal
    left = f"NEXT {goal:,}" if goal is not None else "ALL TIERS"
    right = "MAX" if goal is None else f"{round(a.progress * 100)}%"
    parts.append(
        f'<rect x="{text_x}" y="{by + 72}" width="{bar_w:.1f}" height="4" rx="2" fill="{theme["line"]}"/>'
        + (
            f'<rect x="{text_x}" y="{by + 72}" width="{fill_w:.1f}" height="4" rx="2" '
            f'fill="{"url(#g%d)" % i if unlocked else theme["faint"]}" class="growx" style="animation-delay:{.7 + i * .09:.2f}s"/>'
            if fill_w else ""
        )
        + f'<text x="{text_x}" y="{by + 89}" class="m" font-size="8" letter-spacing=".4" fill="{theme["muted"]}">{esc(left)}</text>'
        f'<text x="{text_x + bar_w:.1f}" y="{by + 89}" text-anchor="end" class="mb" font-size="8" letter-spacing=".4" '
        f'fill="{c1 if goal is None else theme["muted"]}">{esc(right)}</text>'
    )

    if unlocked:
        sweep = BADGE_W + 120
        parts.append(
            f'<g clip-path="url(#c{i})"><path d="M{bx - 70:.1f},{by + BADGE_H} l30,-{BADGE_H} h26 l-30,{BADGE_H}z" '
            f'fill="url(#shine)" class="shine" style="transform:translateX({sweep:.0f}px);'
            f'animation:shine{i} 7s ease-in-out {2.4 + i * .45:.2f}s infinite both"/></g>'
        )
    return f'<g class="pop" style="animation-delay:{.15 + i * .09:.2f}s">{"".join(parts)}</g>'


def _icon_raw(markup: str, cx: float, cy: float, size: float, color: str) -> str:
    return (
        f'<g transform="translate({cx - size / 2:.2f} {cy - size / 2:.2f}) scale({size / 24:.3f})" color="{color}" '
        f'stroke="{color}" stroke-width="2.4" stroke-linecap="round">{markup}</g>'
    )


def render(cfg: Config, data: Data, theme: dict) -> str:
    items = stats.achievements(data)[: COLS * ROWS]
    unlocked = sum(1 for a in items if a.unlocked)
    tiers = sum(a.tier for a in items)
    max_tiers = sum(len(a.tiers) for a in items)
    summary = f"{unlocked}/{len(items)} UNLOCKED · {tiers}/{max_tiers} TIERS"
    sweep = BADGE_W + 120
    keyframes = "".join(
        f"@keyframes shine{i}{{0%{{transform:translateX(0)}}16%,100%{{transform:translateX({sweep:.0f}px)}}}}"
        for i in range(len(items))
    )
    css = f"""
    .halo{{transform-box:fill-box;transform-origin:center;animation:halo 3.6s ease-in-out infinite}}
    @keyframes halo{{50%{{transform:scale(1.14);opacity:.05}}}}
    {keyframes}
    """
    shine_alpha = .38 if theme["name"] == "dark" else .7
    defs = (
        f'<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffffff" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="#ffffff" stop-opacity="{shine_alpha}"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/>'
        f"</linearGradient>"
    )
    # XP meter in the header
    meter_w = 120
    meter_x = W - 24 - meter_w
    body = (
        panel(W, H, theme, accent=theme["amber"])
        + label(24, 32, "Achievements", theme, color=theme["amber"])
        + f'<g class="fade" style="animation-delay:.3s">'
        f'<text x="{meter_x - 14:.1f}" y="32" text-anchor="end" class="mb" font-size="10" letter-spacing="1.2" '
        f'fill="{theme["muted"]}">{esc(summary)}</text>'
        f'<rect x="{meter_x}" y="25" width="{meter_w}" height="6" rx="3" fill="{theme["line"]}"/>'
        + (
            f'<rect x="{meter_x}" y="25" width="{max(3, meter_w * tiers / max_tiers):.1f}" height="6" rx="3" '
            f'fill="url(#xp)" class="growx" style="animation-delay:.5s"/>' if tiers else ""
        )
        + "</g>"
        + "".join(_badge(i, a, theme) for i, a in enumerate(items))
    )
    defs += (
        f'<linearGradient id="xp" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{theme["amber"]}"/>'
        f'<stop offset="1" stop-color="{theme["pink"]}"/></linearGradient>'
    )
    title = f"Achievements: {summary.lower()} — " + ", ".join(
        f"{a.title.title()} {'tier ' + str(a.tier) if a.unlocked else 'locked'}" for a in items
    )
    return document(W, H, body, theme, css=css, title=title, defs=defs)
