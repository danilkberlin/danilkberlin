"""Mission Control: rolling odometer counters, streak ring gauges, 30-day sparkline."""
from __future__ import annotations

from .. import stats
from ..config import Config
from ..model import Data
from .core import W, document, esc, label, odometer, panel, polar, smooth_path, text_width

H = 300

# Tile grid (left), ring column (right), sparkline strip (bottom-left).
TILE_X, TILE_Y = 28, 52
TILE_W, TILE_H, GAP = 122.5, 78, 10
RIGHT_X = 568
RIGHT_W = W - 28 - RIGHT_X

CSS = """
.spin{transform-box:fill-box;transform-origin:center;animation:spin 24s linear infinite}
.spinr{transform-box:fill-box;transform-origin:center;animation:spin 36s linear infinite reverse}
.ring{stroke-dasharray:1;animation:draw 1.8s cubic-bezier(.3,.7,.2,1) both}
.pulse{transform-box:fill-box;transform-origin:center;animation:pulse 2.2s ease-out infinite}
.area{animation:fade 1.2s ease both}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes pulse{0%{transform:scale(1);opacity:.9}100%{transform:scale(3.2);opacity:0}}
"""


def _fit(value: int, max_width: float, size: float) -> float:
    text = f"{value:,}"
    while size > 12 and text_width(text, "o", size) > max_width:
        size -= 1
    return size


def _tile(i: int, title: str, value: int, color: str, theme: dict) -> str:
    col, row = i % 4, i // 4
    x = TILE_X + col * (TILE_W + GAP)
    y = TILE_Y + row * (TILE_H + GAP)
    delay = 0.15 + i * 0.07
    size = _fit(value, TILE_W - 30, 27)
    return (
        f'<g class="up" style="animation-delay:{delay:.2f}s">'
        f'<rect x="{x:.1f}" y="{y}" width="{TILE_W}" height="{TILE_H}" rx="12" fill="{theme["bg"]}" '
        f'fill-opacity="{.55 if theme["name"] == "dark" else .7}" stroke="{theme["line"]}"/>'
        f'<rect x="{x:.1f}" y="{y + 16}" width="3" height="{TILE_H - 32}" rx="1.5" fill="{color}" filter="url(#glow)"/>'
        f'<text x="{x + 16:.1f}" y="{y + 24}" class="mb" font-size="9.5" letter-spacing="1.6" fill="{theme["muted"]}">'
        f"{esc(title)}</text>"
        f"{odometer(value, x + 15, y + 60, size, theme, color=color if theme['name'] == 'dark' else theme['text'], delay=delay + .25)}"
        f"</g>"
    )


def _ring(cx: float, cy: float, value: int, fraction: float, title: str, caption: str, color: str,
          theme: dict, delay: float) -> str:
    r = 40
    fraction = max(0.0, min(1.0, fraction))
    track = (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{theme["line"]}" stroke-width="7"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r + 11}" fill="none" stroke="{color}" stroke-opacity=".35" '
        f'stroke-width="1" stroke-dasharray="2 6" class="spin"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r - 9}" fill="none" stroke="{theme["faint"]}" stroke-opacity=".6" '
        f'stroke-width="1" stroke-dasharray="14 4 2 4" class="spinr"/>'
    )
    arc = ""
    if fraction > 0:
        end_x, end_y = polar(cx, cy, r, 360 * fraction)
        arc = (
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="7" stroke-linecap="round" '
            f'pathLength="1" transform="rotate(-90 {cx} {cy})" class="ring" filter="url(#glow)" '
            f'style="stroke-dashoffset:{1 - fraction:.4f};animation-delay:{delay:.2f}s"/>'
            f'<g class="pop" style="animation-delay:{delay + 1.6:.2f}s">'
            f'<circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="4.5" fill="{theme["panel"]}" stroke="{color}" stroke-width="2.5"/>'
            f'<circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="4.5" fill="none" stroke="{color}" class="pulse" '
            f'style="animation-delay:{delay + 2.2:.2f}s"/></g>'
        )
    size = 26 if value < 1000 else 20
    number = odometer(value, cx, cy + 6, size, theme, color=theme["text"], anchor="middle", delay=delay + .2)
    return (
        f"<g>{track}{arc}{number}"
        f'<text x="{cx}" y="{cy + 22}" text-anchor="middle" class="mb" font-size="8.5" letter-spacing="2" '
        f'fill="{theme["muted"]}">DAYS</text>'
        f'<text x="{cx}" y="{cy + r + 30}" text-anchor="middle" class="mb" font-size="9.5" letter-spacing="1.6" '
        f'fill="{theme["text"]}">{esc(title)}</text>'
        f'<text x="{cx}" y="{cy + r + 44}" text-anchor="middle" class="m" font-size="9" letter-spacing=".8" '
        f'fill="{theme["muted"]}">{esc(caption)}</text></g>'
    )


def _sparkline(data: Data, theme: dict) -> str:
    x0, y0 = TILE_X, TILE_Y + 2 * (TILE_H + GAP)
    width, height = 4 * TILE_W + 3 * GAP, 58
    days = stats.recent_window(data, 30)
    counts = [d.count for d in days] or [0]
    peak = max(counts)
    total = sum(counts)
    chart_x = x0 + 112
    chart_w = width - 112 - 14
    top, bottom = y0 + 12, y0 + height - 12
    scale = (bottom - top) / peak if peak else 0
    step = chart_w / max(1, len(counts) - 1)
    points = [(chart_x + i * step, bottom - c * scale) for i, c in enumerate(counts)]
    line = smooth_path(points)
    area = f"{line} L{points[-1][0]:.1f},{bottom} L{points[0][0]:.1f},{bottom}Z"
    end_x, end_y = points[-1]
    cyan, pink = theme["cyan"], theme["pink"]
    out = [
        f'<defs><linearGradient id="spk" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{cyan}"/>'
        f'<stop offset="1" stop-color="{pink}"/></linearGradient>'
        f'<linearGradient id="spka" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{cyan}" stop-opacity=".35"/>'
        f'<stop offset="1" stop-color="{cyan}" stop-opacity="0"/></linearGradient></defs>',
        f'<g class="up" style="animation-delay:.75s">'
        f'<rect x="{x0}" y="{y0}" width="{width}" height="{height}" rx="12" fill="{theme["bg"]}" '
        f'fill-opacity="{.55 if theme["name"] == "dark" else .7}" stroke="{theme["line"]}"/>'
        f'<text x="{x0 + 16}" y="{y0 + 24}" class="mb" font-size="9.5" letter-spacing="1.6" fill="{theme["muted"]}">LAST 30 DAYS</text>'
        f'<text x="{x0 + 16}" y="{y0 + 45}" class="o" font-size="17" fill="{theme["text"]}">{total:,}</text>'
        f'<text x="{x0 + 18 + text_width(f"{total:,}", "o", 17):.1f}" y="{y0 + 45}" class="m" font-size="9" '
        f'fill="{theme["muted"]}"> · PEAK {peak}</text>',
    ]
    # baseline grid
    for frac in (0, .5, 1):
        gy = bottom - frac * (bottom - top)
        out.append(
            f'<line x1="{chart_x}" y1="{gy:.1f}" x2="{chart_x + chart_w}" y2="{gy:.1f}" stroke="{theme["line"]}" '
            f'stroke-dasharray="{"0" if frac == 0 else "2 4"}"/>'
        )
    out.append(f'<path d="{area}" fill="url(#spka)" class="area" style="animation-delay:1.9s"/>')
    out.append(
        f'<path d="{line}" fill="none" stroke="url(#spk)" stroke-width="2.2" stroke-linecap="round" '
        f'stroke-linejoin="round" pathLength="1" class="draw" filter="url(#glow)" style="animation-delay:1s;animation-duration:1.8s"/>'
    )
    out.append(
        f'<g class="pop" style="animation-delay:2.7s"><circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="3.6" fill="{pink}" filter="url(#glow)"/>'
        f'<circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="3.6" fill="none" stroke="{pink}" class="pulse" style="animation-delay:3s"/></g>'
    )
    out.append("</g>")
    return "".join(out)


def _side_stats(data: Data, theme: dict) -> str:
    year = stats.last_year(data)
    active = sum(1 for d in year if d.count)
    best = stats.best_day(year)
    best_text = f"{best.count} · {best.date:%d %b}".upper() if best else "—"
    y0 = TILE_Y + 2 * (TILE_H + GAP)
    rows = [("ACTIVE DAYS", f"{active}/365", theme["cyan"]), ("BEST DAY", best_text, theme["pink"])]
    out = [
        f'<g class="up" style="animation-delay:.9s">'
        f'<rect x="{RIGHT_X}" y="{y0}" width="{RIGHT_W}" height="58" rx="12" fill="{theme["bg"]}" '
        f'fill-opacity="{.55 if theme["name"] == "dark" else .7}" stroke="{theme["line"]}"/>'
    ]
    for i, (title, value, color) in enumerate(rows):
        y = y0 + 24 + i * 19
        out.append(
            f'<circle cx="{RIGHT_X + 18}" cy="{y - 3.5}" r="2.6" fill="{color}" filter="url(#glow)"/>'
            f'<text x="{RIGHT_X + 28}" y="{y}" class="mb" font-size="9.5" letter-spacing="1.4" fill="{theme["muted"]}">{title}</text>'
            f'<text x="{RIGHT_X + RIGHT_W - 16}" y="{y}" text-anchor="end" class="mb" font-size="11" '
            f'fill="{theme["text"]}">{esc(value)}</text>'
        )
    out.append("</g>")
    return "".join(out)


def _milestone(longest: int) -> int:
    for goal in (7, 14, 30, 60, 100, 180, 365):
        if longest < goal:
            return goal
    return longest


def render(cfg: Config, data: Data, theme: dict) -> str:
    t = data.totals
    dark = theme["name"] == "dark"
    palette = [theme["cyan"], theme["violet"], theme["pink"], theme["amber"],
               theme["green"], theme["cyan"], theme["amber"], theme["pink"]]
    counters = [
        ("CONTRIB · 1Y", t.contributions_year),
        ("ALL-TIME", t.contributions_all),
        ("COMMITS", t.commits),
        ("PULL REQUESTS", t.prs),
        ("REVIEWS", t.reviews),
        ("ISSUES", t.issues),
        ("STARS EARNED", data.stars),
        ("FOLLOWERS", data.followers),
    ]
    tiles = "".join(_tile(i, title, value, palette[i], theme) for i, (title, value) in enumerate(counters))

    current = stats.current_streak(data.history)
    longest = stats.longest_streak(data.history)
    goal = _milestone(longest)
    ring_cy = TILE_Y + 58
    rings = (
        f'<rect x="{RIGHT_X}" y="{TILE_Y}" width="{RIGHT_W}" height="{2 * TILE_H + GAP}" rx="12" fill="{theme["bg"]}" '
        f'fill-opacity="{.55 if dark else .7}" stroke="{theme["line"]}" class="fade" style="animation-delay:.3s"/>'
        + _ring(RIGHT_X + RIGHT_W * .27, ring_cy, current, current / longest if longest else 0, "CURRENT STREAK",
                f"RECORD {longest}" if longest else "START TODAY", theme["cyan"], theme, .5)
        + _ring(RIGHT_X + RIGHT_W * .73, ring_cy, longest, longest / goal if goal else 0, "LONGEST STREAK",
                f"NEXT GOAL {goal}", theme["pink"], theme, .7)
    )

    since = data.created_at.astimezone(data.generated_at.tzinfo)
    meta = f"ON GITHUB SINCE {since:%b %Y} · UPDATED {data.generated_at:%d.%m.%Y}".upper()
    header = (
        label(28, 34, "Mission Control", theme)
        + f'<text x="{W - 28}" y="34" text-anchor="end" class="m fade" font-size="10" letter-spacing="1.2" '
        f'fill="{theme["muted"]}" style="animation-delay:.2s">{esc(meta)}</text>'
    )
    body = (
        panel(W, H, theme, accent=theme["cyan"])
        + header + tiles + rings + _sparkline(data, theme) + _side_stats(data, theme)
    )
    title = (
        f"GitHub stats: {t.contributions_year} contributions last year, {t.commits} commits, {t.prs} PRs, "
        f"{t.reviews} reviews, current streak {current} days, longest {longest} days"
    )
    return document(W, H, body, theme, css=CSS, title=title)
