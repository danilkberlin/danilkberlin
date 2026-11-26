"""Split-flap "Departures" board of recent public activity.

Every character sits on its own flap tile and rattles through a few random
glyphs before settling, staggered by row and column like a real station board.

Byte budget: tiles come from one <pattern>, and every glyph strip has the same
length, so a single shared keyframe drives all 300 cells. Each cell is a
nested overflow-hidden <svg> with one <text> whose per-glyph x/y lists stack
the strip vertically.
"""
from __future__ import annotations

import random
from datetime import datetime

from ..config import Config
from ..model import Data, Event
from .core import W, document, esc, label, panel, polar, text_width

ROWS = 6
CELL_W, CELL_H = 13.0, 22.0
PITCH_X, PITCH_Y = 14.5, 30.0
X0, Y0 = 24.0, 84.0
COLUMNS = [("TIME", 11), ("DESTINATION", 16), ("VIA", 14), ("STATUS", 9)]  # one blank cell between columns
STRIP = 7  # target + 5 random + blank
GLYPHS = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
BLANK = " "  # NBSP survives XML whitespace collapsing

H = Y0 + ROWS * PITCH_Y + 22

STATUS_FOR = {
    "PUSH": "DEPLOYED", "MERGE": "MERGED", "PR": "IN REVIEW", "RELEASE": "RELEASED", "NEW": "CREATED",
    "ISSUE": "REPORTED", "REVIEW": "REVIEWED", "STAR": "STARRED", "FORK": "FORKED",
}


def _palette(theme: dict) -> dict:
    dark = theme["name"] == "dark"
    if dark:
        return {
            "board": "#070a1f", "tile_top": "#181d45", "tile_bottom": "#11153a", "split": "#04051a",
            "glyph": theme["amber"], "time": "#ffe3a3",
        }
    return {
        "board": "#e4e7f7", "tile_top": "#ffffff", "tile_bottom": "#f1f3fc", "split": "#c3c8e6",
        "glyph": theme["text"], "time": theme["violet"],
    }


def _status_color(status: str, theme: dict) -> str:
    return {
        "BOARDING": theme["green"], "MERGED": theme["violet"], "DEPLOYED": theme["cyan"],
        "RELEASED": theme["pink"], "IN REVIEW": theme["amber"], "STANDBY": theme["muted"],
    }.get(status, theme["amber"] if theme["name"] == "dark" else theme["text"])


def _rows(cfg: Config, data: Data) -> list[tuple[str, str, str, str] | None]:
    """Up to ROWS rows of (time, destination, via, status); None marks a blank row."""
    events: list[Event] = sorted(data.events, key=lambda e: e.at, reverse=True)
    seen_pushes = {(e.repo, e.at.date()) for e in events if e.kind == "PUSH"}
    for name in cfg.featured:  # top up with the featured repos' last push
        repo = data.repos.get(name)
        if repo and repo.pushed_at:
            at = repo.pushed_at.astimezone(data.generated_at.tzinfo)
            if (name, at.date()) not in seen_pushes:
                events.append(Event("PUSH", name, at, ""))
    events = sorted(events, key=lambda e: e.at, reverse=True)[:ROWS]

    rows: list[tuple[str, str, str, str] | None] = []
    for index, event in enumerate(events):
        status = "BOARDING" if index == 0 else STATUS_FOR.get(event.kind, "ON TIME")
        via = f"{event.kind} {event.detail}".strip()
        rows.append((f"{event.at:%d.%m %H:%M}", event.repo, via, status))
    if not rows:
        now = data.generated_at
        rows.append((f"{now:%d.%m %H:%M}", "AWAITING COMMITS", "FIRST PUSH", "STANDBY"))
    rows += [None] * (ROWS - len(rows))
    return rows


def _fit(text: str, width: int) -> str:
    text = text.upper().replace(" ", BLANK)
    return text[:width].ljust(width, BLANK)


def _clock(x: float, y: float, now: datetime, theme: dict, pal: dict) -> str:
    """Small station clock: hands at build time, a sweeping second hand, plus digits."""
    r = 15
    hour_angle = (now.hour % 12 + now.minute / 60) * 30
    minute_angle = now.minute * 6
    second_angle = now.second * 6
    ticks = "".join(
        f'<line x1="{polar(x, y, r - (3.5 if i % 3 == 0 else 2), i * 30)[0]:.1f}" '
        f'y1="{polar(x, y, r - (3.5 if i % 3 == 0 else 2), i * 30)[1]:.1f}" '
        f'x2="{polar(x, y, r - .6, i * 30)[0]:.1f}" y2="{polar(x, y, r - .6, i * 30)[1]:.1f}" '
        f'stroke="{theme["muted"]}" stroke-width="{1.4 if i % 3 == 0 else .8}"/>'
        for i in range(12)
    )
    hx, hy = polar(x, y, r * .5, hour_angle)
    mx, my = polar(x, y, r * .78, minute_angle)
    digits_x = x - r - 12
    return (
        f'<g class="fade" style="animation-delay:.4s">'
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="{pal["board"]}" stroke="{theme["line"]}"/>{ticks}'
        f'<line x1="{x}" y1="{y}" x2="{hx:.1f}" y2="{hy:.1f}" stroke="{theme["text"]}" stroke-width="2" stroke-linecap="round"/>'
        f'<line x1="{x}" y1="{y}" x2="{mx:.1f}" y2="{my:.1f}" stroke="{theme["text"]}" stroke-width="1.4" stroke-linecap="round"/>'
        f'<g><line x1="{x}" y1="{y + 3}" x2="{x}" y2="{y - r + 2.5}" stroke="{theme["cyan"]}" stroke-width=".9"/>'
        f'<circle cx="{x}" cy="{y - r + 4.5}" r="1.6" fill="{theme["cyan"]}"/>'
        f'<animateTransform attributeName="transform" type="rotate" from="{second_angle} {x} {y}" '
        f'to="{second_angle + 360} {x} {y}" dur="60s" repeatCount="indefinite"/></g>'
        f'<circle cx="{x}" cy="{y}" r="1.8" fill="{theme["cyan"]}"/>'
        f'<text x="{digits_x}" y="{y + 7}" text-anchor="end" class="mb" font-size="20" fill="{pal["glyph"]}">'
        f'{now:%H}<tspan class="blink">:</tspan>{now:%M}</text>'
        f'<text x="{digits_x - 74}" y="{y + 5}" text-anchor="end" class="m" font-size="10" letter-spacing="1.6" '
        f'fill="{theme["muted"]}">PLATFORM 1 · {esc((now.tzname() or "").upper())}</text>'
        f"</g>"
    )


def render(cfg: Config, data: Data, theme: dict) -> str:
    pal = _palette(theme)
    rng = random.Random(data.generated_at.date().toordinal() * 7 + (theme["name"] == "dark"))
    rows = _rows(cfg, data)

    # Column geometry on the tile grid (whole pitches, so one pattern aligns everywhere).
    starts, cell = [], 0
    for _, width in COLUMNS:
        starts.append(cell)
        cell += width + 1
    total_cells = cell - 1
    board_right = X0 + total_cells * PITCH_X - (PITCH_X - CELL_W)
    lamp_x = board_right + 17

    xs = " ".join([f"{CELL_W / 2:g}"] * STRIP)
    ys = " ".join(f"{16 + i * CELL_H:g}" for i in range(STRIP))

    tiles = "".join(
        f'<rect x="{X0 + start * PITCH_X:g}" y="{Y0:g}" width="{width * PITCH_X - (PITCH_X - CELL_W):g}" '
        f'height="{ROWS * PITCH_Y - (PITCH_Y - CELL_H):g}" fill="url(#flap)"/>'
        for start, (_, width) in zip(starts, COLUMNS)
    )

    headers = "".join(
        f'<text x="{X0 + start * PITCH_X + 1:g}" y="{Y0 - 10:g}" class="mb" font-size="9.5" letter-spacing="2" '
        f'fill="{theme["muted"]}">{title}</text>'
        for start, (title, _) in zip(starts, COLUMNS)
    )

    cells, lamps = [], []
    for r, row in enumerate(rows):
        values = row if row else ("--.-- --:--", "", "", "")
        top = Y0 + r * PITCH_Y
        for c, (start, (_, width), value) in enumerate(zip(starts, COLUMNS, values)):
            if c == 0:
                color = pal["time"] if row else theme["faint"]
            elif c == 3:
                color = _status_color(value, theme)
            else:
                color = pal["glyph"]
            group_cls = ' class="mb boarding"' if row and c == 3 and value == "BOARDING" else ' class="mb"'
            parts = []
            for i, ch in enumerate(_fit(value, width)):
                strip = ch + "".join(rng.choice(GLYPHS) for _ in range(STRIP - 2)) + BLANK
                delay = .25 + r * .14 + (start + i) * .032 + rng.uniform(0, .12)
                parts.append(
                    f'<svg x="{X0 + (start + i) * PITCH_X:g}" y="{top:g}" width="{CELL_W:g}" height="{CELL_H:g}" overflow="hidden">'
                    f'<text class="f" x="{xs}" y="{ys}" style="animation-delay:{delay:.2f}s">{esc(strip)}</text></svg>'
                )
            cells.append(f'<g fill="{color}"{group_cls}>{"".join(parts)}</g>')
        cy = top + CELL_H / 2
        if row:
            lamp_color = _status_color(row[3], theme)
            blink = ' class="lamp"' if row[3] == "BOARDING" else ""
            lamps.append(
                f'<circle cx="{lamp_x:g}" cy="{cy:g}" r="4" fill="{lamp_color}" filter="url(#glow)"{blink} '
                f'style="animation-delay:{.4 + r * .14:.2f}s"/>'
            )
        else:
            lamps.append(f'<circle cx="{lamp_x:g}" cy="{cy:g}" r="4" fill="none" stroke="{theme["faint"]}"/>')

    sheen = (
        f'<defs><linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" '
        f'stop-opacity="{.07 if theme["name"] == "dark" else .5}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>'
        f'</linearGradient><clipPath id="boardclip"><rect x="16" y="{Y0 - 26:g}" width="{W - 32}" '
        f'height="{ROWS * PITCH_Y + 34:g}" rx="10"/></clipPath></defs>'
        f'<g clip-path="url(#boardclip)"><rect x="-140" y="{Y0 - 26:g}" width="120" height="{ROWS * PITCH_Y + 34:g}" '
        f'fill="url(#sheen)" transform="skewX(-18)" class="sheen"/></g>'
    )

    pattern = (
        f'<pattern id="flap" x="{X0:g}" y="{Y0:g}" width="{PITCH_X:g}" height="{PITCH_Y:g}" patternUnits="userSpaceOnUse">'
        f'<rect width="{CELL_W:g}" height="{CELL_H:g}" rx="2" fill="{pal["tile_bottom"]}"/>'
        f'<rect width="{CELL_W:g}" height="{CELL_H / 2:g}" rx="2" fill="{pal["tile_top"]}"/>'
        f'<rect y="{CELL_H / 2 - 3:g}" width="{CELL_W:g}" height="3" fill="{pal["tile_top"]}"/>'
        f'<rect y="{CELL_H / 2 - .5:g}" width="{CELL_W:g}" height="1" fill="{pal["split"]}"/>'
        f"</pattern>"
    )

    count = sum(1 for row in rows if row)
    css = f"""
    .f{{font-family:JBM,ui-monospace,monospace;font-weight:700;font-size:15px;text-anchor:middle;
        animation:flip .78s steps({STRIP - 1}) both}}
    @keyframes flip{{from{{transform:translateY(-{(STRIP - 1) * CELL_H:g}px)}}}}
    .boarding{{animation:board 1.8s ease-in-out 4.2s infinite}}
    @keyframes board{{50%{{opacity:.35}}}}
    .lamp{{animation:board 1.1s ease-in-out infinite}}
    .sheen{{animation:sheen 9s ease-in-out 3.6s infinite}}
    @keyframes sheen{{0%{{transform:skewX(-18deg) translateX(0)}}40%,100%{{transform:skewX(-18deg) translateX({W + 300}px)}}}}
    """
    title = "Departures · Abfahrt"
    sub_x = 40 + text_width(title.upper(), "mb", 11, 2.2) + 14
    body = (
        panel(W, H, theme, accent=theme["amber"])
        + label(24, 36, title, theme, color=theme["amber"])
        + f'<text x="{sub_x:.1f}" y="36" class="m fade" font-size="10" letter-spacing="1.2" fill="{theme["faint"]}" '
        f'style="animation-delay:.2s">— latest public activity</text>'
        + _clock(W - 38, 33, data.generated_at, theme, pal)
        + f'<rect x="16" y="{Y0 - 26:g}" width="{W - 32}" height="{ROWS * PITCH_Y + 34:g}" rx="10" fill="{pal["board"]}"/>'
        + headers
        + f'<line x1="{X0:g}" y1="{Y0 - 6:g}" x2="{lamp_x + 5:g}" y2="{Y0 - 6:g}" stroke="{theme["line"]}"/>'
        + tiles
        + "".join(cells)
        + "".join(lamps)
        + sheen
    )
    return document(W, H, body, theme, css=css, defs=pattern, title=f"Departures: {count} latest public activities")
