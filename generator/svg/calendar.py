"""Contribution calendar: cells rain down column by column, then a scanline sweeps."""
from __future__ import annotations

from .. import stats
from ..config import Config
from ..model import Data, Day
from .core import W, document, esc, label, odometer, panel, text_width

H = 230
COLS, ROWS = 53, 7
PITCH = 14.2
CELL = 11
GRID_X = 58
GRID_Y = 74
GRID_W = COLS * PITCH - (PITCH - CELL)
GRID_H = ROWS * PITCH - (PITCH - CELL)

CSS = f"""
.cell{{animation:drop .75s cubic-bezier(.3,1.45,.55,1) both}}
.scan{{opacity:0;animation:scan 7s linear 3.2s infinite}}
.ring{{transform-box:fill-box;transform-origin:center;animation:ring 2s ease-out 3s infinite}}
.today{{animation:today 1.6s ease-in-out 2.8s infinite}}
@keyframes drop{{from{{transform:translateY(-110px);opacity:0}}}}
@keyframes scan{{0%{{opacity:1;transform:translateX(0)}}55%{{opacity:1;transform:translateX({GRID_W + 60:.0f}px)}}56%,100%{{opacity:0;transform:translateX({GRID_W + 60:.0f}px)}}}}
@keyframes ring{{0%{{transform:scale(1);opacity:.95}}100%{{transform:scale(2.6);opacity:0}}}}
@keyframes today{{50%{{opacity:.15}}}}
"""


def _levels(days: list[Day]) -> list[int]:
    """GitHub's own levels when present; otherwise quartiles of the max count."""
    if any(d.level for d in days) or not any(d.count for d in days):
        return [d.level if d.count else 0 for d in days]
    peak = max(d.count for d in days)
    out = []
    for d in days:
        if not d.count:
            out.append(0)
        else:
            out.append(min(4, 1 + int(4 * (d.count - 1) / peak)))
    return out


def _months(days: list[Day], theme: dict) -> str:
    out = []
    last_col = -10
    for index, day in enumerate(days):
        if day.date.day != 1 and index != 0:
            continue
        col = index // ROWS
        if index == 0:
            # Only label the first partial month if it has room before the next one.
            nxt = next((i for i, d in enumerate(days) if d.date.day == 1), len(days)) // ROWS
            if nxt - col < 3:
                continue
        if col - last_col < 3:
            continue
        last_col = col
        out.append(
            f'<text x="{GRID_X + col * PITCH:.1f}" y="{GRID_Y - 9}" class="m" font-size="9.5" '
            f'letter-spacing=".6" fill="{theme["muted"]}">{day.date:%b}</text>'
        )
    return f'<g class="fade" style="animation-delay:.2s">{"".join(out)}</g>'


def render(cfg: Config, data: Data, theme: dict) -> str:
    days = data.calendar[: COLS * ROWS]
    levels = _levels(days)
    heat = theme["heat"]
    today = data.generated_at.date()
    year = stats.last_year(data)
    best = stats.best_day(year)

    cells = []
    best_xy = today_xy = None
    for index, (day, level) in enumerate(zip(days, levels)):
        col, row = divmod(index, ROWS)
        x = GRID_X + col * PITCH
        y = GRID_Y + row * PITCH
        delay = 0.25 + col * 0.034 + row * 0.018
        glow = ' filter="url(#glow)"' if level == 4 and theme["name"] == "dark" else ""
        cells.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="2.6" fill="{heat[level]}" '
            f'class="cell" style="animation-delay:{delay:.2f}s"{glow}/>'
        )
        if best and day.date == best.date:
            best_xy = (x, y)
        if day.date == today:
            today_xy = (x, y)

    # Weekday labels (Monday-first)
    weekdays = "".join(
        f'<text x="{GRID_X - 10}" y="{GRID_Y + r * PITCH + 9:.1f}" text-anchor="end" class="m" font-size="9" '
        f'fill="{theme["muted"]}">{name}</text>'
        for r, name in ((0, "Mon"), (2, "Wed"), (4, "Fri"))
    )

    # Scanline sweeping across the grid
    scan = (
        f'<defs><linearGradient id="scan" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{theme["cyan"]}" stop-opacity="0"/>'
        f'<stop offset=".8" stop-color="{theme["cyan"]}" stop-opacity=".35"/>'
        f'<stop offset="1" stop-color="{theme["cyan"]}" stop-opacity=".9"/></linearGradient>'
        f'<clipPath id="gridclip"><rect x="{GRID_X - 4}" y="{GRID_Y - 4}" width="{GRID_W + 8:.1f}" height="{GRID_H + 8:.1f}"/></clipPath></defs>'
        f'<g clip-path="url(#gridclip)"><g class="scan">'
        f'<rect x="{GRID_X - 60}" y="{GRID_Y - 4}" width="56" height="{GRID_H + 8:.1f}" fill="url(#scan)"/>'
        f'<rect x="{GRID_X - 5}" y="{GRID_Y - 4}" width="1.5" height="{GRID_H + 8:.1f}" fill="{theme["cyan"]}" filter="url(#glow)"/>'
        f"</g></g>"
    )

    marks = ""
    if best_xy:
        bx, by = best_xy
        marks += (
            f'<g class="fade" style="animation-delay:2.9s">'
            f'<rect x="{bx - 2:.1f}" y="{by - 2:.1f}" width="{CELL + 4}" height="{CELL + 4}" rx="4" fill="none" '
            f'stroke="{theme["pink"]}" stroke-width="1.6" filter="url(#glow)"/>'
            f'<rect x="{bx - 2:.1f}" y="{by - 2:.1f}" width="{CELL + 4}" height="{CELL + 4}" rx="4" fill="none" '
            f'stroke="{theme["pink"]}" stroke-width="1.2" class="ring"/></g>'
        )
    if today_xy:
        tx, ty = today_xy
        marks += (
            f'<rect x="{tx - 1.5:.1f}" y="{ty - 1.5:.1f}" width="{CELL + 3}" height="{CELL + 3}" rx="3.6" fill="none" '
            f'stroke="{theme["cyan"]}" stroke-width="1.4" class="today"/>'
        )

    # Header: label left, total right
    total = data.totals.contributions_year
    suffix = "CONTRIBUTIONS IN THE LAST YEAR"
    suffix_w = text_width(suffix, "mb", 9.5, 1.4)
    total_size = 17
    header = (
        label(28, 34, "Contribution Grid", theme)
        + f'<text x="{W - 28}" y="34" text-anchor="end" class="mb fade" font-size="9.5" letter-spacing="1.4" '
        f'fill="{theme["muted"]}" style="animation-delay:.3s">{suffix}</text>'
        + odometer(total, W - 28 - suffix_w - 10, 35, total_size, theme, color=theme["cyan"], anchor="end", delay=.4)
    )

    # Footer: best day (left), legend (right)
    fy = H - 30
    if best:
        best_text = f"BEST DAY · {best.count} CONTRIBUTION{'S' if best.count != 1 else ''} · {best.date:%a %d %b %Y}".upper()
    else:
        best_text = "NO CONTRIBUTIONS YET · THE GRID IS WAITING"
    active = sum(1 for d in year if d.count)
    streak = stats.current_streak(data.history)
    footer_left = (
        f'<g class="fade" style="animation-delay:2.9s">'
        f'<rect x="28" y="{fy - 8.5}" width="9" height="9" rx="2" fill="none" stroke="{theme["pink"]}" stroke-width="1.5"/>'
        f'<text x="44" y="{fy}" class="mb" font-size="9.5" letter-spacing="1.2" fill="{theme["text"]}">{esc(best_text)}</text>'
        f'<text x="44" y="{fy + 14}" class="m" font-size="9" letter-spacing=".8" fill="{theme["muted"]}">'
        f"{active} ACTIVE DAYS · CURRENT STREAK {streak} · TODAY OUTLINED</text></g>"
    )
    legend_cells = "".join(
        f'<rect x="{W - 28 - 34 - (5 - i) * 14:.1f}" y="{fy - 9}" width="{CELL}" height="{CELL}" rx="2.6" fill="{heat[i]}" '
        f'class="pop" style="animation-delay:{2.6 + i * .08:.2f}s"/>'
        for i in range(5)
    )
    legend = (
        f'<g><text x="{W - 28 - 34 - 5 * 14 - 8:.1f}" y="{fy}" text-anchor="end" class="m fade" font-size="9" '
        f'fill="{theme["muted"]}" style="animation-delay:2.6s">LESS</text>{legend_cells}'
        f'<text x="{W - 28}" y="{fy}" text-anchor="end" class="m fade" font-size="9" fill="{theme["muted"]}" '
        f'style="animation-delay:3s">MORE</text></g>'
    )

    body = (
        panel(W, H, theme, accent=theme["pink"])
        + header + _months(days, theme) + f'<g class="fade" style="animation-delay:.2s">{weekdays}</g>'
        + f'<defs><clipPath id="rain"><rect x="0" y="48" width="{W}" height="{H - 48}"/></clipPath></defs>'
        + f'<g clip-path="url(#rain)">{"".join(cells)}</g>' + scan + marks + footer_left + legend
    )
    title = f"Contribution calendar: {total} contributions in the last year"
    if best:
        title += f", best day {best.date:%d %b %Y} with {best.count}"
    return document(W, H, body, theme, css=CSS, title=title)

