"""Heartbeat monitor: each of the last 26 weeks is one ECG beat, spike = contributions."""
from __future__ import annotations

import math

from .. import stats
from ..config import Config
from ..model import Data
from .core import W, document, esc, label, odometer, panel

H = 170
WEEKS = 26
MX, MY, MW, MH = 28, 46, 612, 106  # monitor
RX = MX + MW + 16  # readout panel
RW = W - 28 - RX
TX0, TX1 = MX + 14, MX + MW - 14  # trace extent
BASE = MY + MH * 0.7
MAX_AMP = BASE - (MY + 26)
DRAW_START, DRAW_DUR = 0.4, 2.4
LOOP = 7.0

CSS = """
.beat{transform-box:fill-box;transform-origin:center}
.glowtrail{animation:fade 1s ease 2.4s both}
@keyframes heartbeat{0%{transform:scale(1)}14%{transform:scale(1.28)}28%{transform:scale(1)}42%{transform:scale(1.18)}70%{transform:scale(1)}}
"""


def _beat(x: float, width: float, amp: float) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = [(x, BASE), (x + .12 * width, BASE)]
    p_height = min(3.0, 1 + amp * .06)
    for i in range(1, 6):  # P wave
        t = i / 6
        pts.append((x + (.12 + .18 * t) * width, BASE - p_height * math.sin(math.pi * t)))
    pts += [
        (x + .34 * width, BASE),
        (x + .40 * width, BASE + .12 * amp),  # Q
        (x + .47 * width, BASE - amp),  # R
        (x + .54 * width, BASE + .24 * amp),  # S
        (x + .60 * width, BASE),
    ]
    t_height = 1 + .16 * amp
    for i in range(1, 8):  # T wave
        t = i / 8
        pts.append((x + (.64 + .24 * t) * width, BASE - t_height * math.sin(math.pi * t)))
    pts.append((x + .92 * width, BASE))
    return pts


def _trace(weeks: list[int]) -> tuple[list[tuple[float, float]], list[tuple[float, float, int]]]:
    peak = max(weeks) if weeks else 0
    width = (TX1 - TX0) / len(weeks)
    points: list[tuple[float, float]] = []
    tops = []
    for i, count in enumerate(weeks):
        amp = 6 + (MAX_AMP - 6) * math.sqrt(count / peak) if count and peak else 2.2
        beat = _beat(TX0 + i * width, width, amp)
        points += beat if not points else beat[1:]
        tops.append((TX0 + (i + .47) * width, BASE - amp, count))
    points.append((TX1, BASE))
    return points, tops


def _motion_keys(points: list[tuple[float, float]]) -> tuple[str, str]:
    """keyTimes/keyPoints so the dot moves at constant horizontal speed."""
    lengths = [0.0]
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        lengths.append(lengths[-1] + math.hypot(x2 - x1, y2 - y1))
    total = lengths[-1]
    span = points[-1][0] - points[0][0]
    times, keys = [], []
    for (x, _), length in zip(points, lengths):
        times.append((x - points[0][0]) / span)
        keys.append(length / total)
    times[0], times[-1], keys[0], keys[-1] = 0.0, 1.0, 0.0, 1.0
    return ";".join(f"{t:.5f}" for t in times), ";".join(f"{k:.5f}" for k in keys)


def _heart(cx: float, cy: float, s: float) -> str:
    return (
        f"M{cx:.1f},{cy + s * .9:.1f} "
        f"C{cx - s * 1.3:.1f},{cy + s * .05:.1f} {cx - s * .95:.1f},{cy - s * .95:.1f} {cx:.1f},{cy - s * .35:.1f} "
        f"C{cx + s * .95:.1f},{cy - s * .95:.1f} {cx + s * 1.3:.1f},{cy + s * .05:.1f} {cx:.1f},{cy + s * .9:.1f}Z"
    )


def render(cfg: Config, data: Data, theme: dict) -> str:
    dark = theme["name"] == "dark"
    weeks = stats.weekly(data.calendar, WEEKS)
    bpm = weeks[-1]
    total = sum(weeks)
    points, tops = _trace(weeks)
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points)
    key_times, key_points = _motion_keys(points)
    monitor_fill = "#060920" if dark else theme["bg2"]
    grid_color = theme["cyan"] if dark else theme["violet"]

    # Monitor grid (minor + major lines), drawn above the eraser so it never disappears.
    grid = []
    for gx in range(MX + 10, MX + MW, 10):
        major = (gx - MX) % 50 == 0
        grid.append(f'<line x1="{gx}" y1="{MY}" x2="{gx}" y2="{MY + MH}" stroke-opacity="{.16 if major else .06}"/>')
    for gy in range(MY + 8, MY + MH, 10):
        major = (gy - MY - 8) % 50 == 0
        grid.append(f'<line x1="{MX}" y1="{gy}" x2="{MX + MW}" y2="{gy}" stroke-opacity="{.16 if major else .06}"/>')
    grid_markup = f'<g stroke="{grid_color}" stroke-width="1">{"".join(grid)}</g>'

    trace = (
        f'<defs><linearGradient id="ecg" gradientUnits="userSpaceOnUse" x1="{TX0}" y1="0" x2="{TX1}" y2="0">'
        f'<stop offset="0" stop-color="{theme["cyan"]}"/><stop offset=".55" stop-color="{theme["violet"]}"/>'
        f'<stop offset="1" stop-color="{theme["pink"]}"/></linearGradient>'
        f'<clipPath id="mon"><rect x="{MX}" y="{MY}" width="{MW}" height="{MH}" rx="10"/></clipPath>'
        f'<linearGradient id="erase" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{monitor_fill}" stop-opacity="0"/>'
        f'<stop offset=".35" stop-color="{monitor_fill}"/><stop offset="1" stop-color="{monitor_fill}"/></linearGradient></defs>'
        f'<path id="trace" d="{d}" fill="none" stroke="url(#ecg)" stroke-width="7" stroke-opacity=".12" '
        f'stroke-linejoin="round" class="glowtrail"/>'
        f'<path d="{d}" fill="none" stroke="url(#ecg)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" '
        f'pathLength="1" class="draw" filter="url(#glow)" style="animation-delay:{DRAW_START}s;animation-duration:{DRAW_DUR}s;'
        f'animation-timing-function:linear"/>'
    )
    begin = f"{DRAW_START + DRAW_DUR:.1f}s"
    sweep = (
        f'<rect x="{TX0 + 6}" y="{MY}" width="22" height="{MH}" fill="url(#erase)" opacity="0">'
        f'<set attributeName="opacity" to="1" begin="{begin}"/>'
        f'<animateTransform attributeName="transform" type="translate" from="0 0" to="{TX1 - TX0} 0" '
        f'dur="{LOOP}s" begin="{begin}" repeatCount="indefinite"/></rect>'
    )
    dot = (
        f'<g opacity="0"><set attributeName="opacity" to="1" begin="{begin}"/>'
        f'<animateMotion dur="{LOOP}s" begin="{begin}" repeatCount="indefinite" calcMode="linear" '
        f'keyTimes="{key_times}" keyPoints="{key_points}"><mpath href="#trace"/></animateMotion>'
        f'<circle r="7" fill="{theme["pink"]}" opacity=".25"/>'
        f'<circle r="3.2" fill="{"#ffffff" if dark else theme["pink"]}" filter="url(#glow)"/></g>'
    )

    peak_mark = ""
    if total:
        px, py, count = max(tops, key=lambda t: t[2])
        peak_mark = (
            f'<g class="fade" style="animation-delay:2.9s">'
            f'<text x="{px:.1f}" y="{py - 6:.1f}" text-anchor="middle" class="mb" font-size="9" fill="{theme["pink"]}">{count}</text></g>'
        )

    monitor = (
        f'<g class="fade" style="animation-delay:.1s">'
        f'<rect x="{MX}" y="{MY}" width="{MW}" height="{MH}" rx="10" fill="{monitor_fill}" stroke="{theme["line"]}"/></g>'
        f'<g clip-path="url(#mon)">{trace}{sweep}{grid_markup}{dot}</g>{peak_mark}'
        f'<g class="m fade" font-size="8.5" letter-spacing="1.2" fill="{theme["muted"]}" style="animation-delay:.3s">'
        f'<text x="{MX + 12}" y="{MY + 15}">LEAD II · 1 BEAT = 1 WEEK</text>'
        f'<text x="{MX + 12}" y="{MY + MH - 8}">{WEEKS}W AGO</text>'
        f'<text x="{MX + MW - 12}" y="{MY + MH - 8}" text-anchor="end">NOW</text></g>'
    )

    # Readout
    heart_color = theme["pink"] if bpm else theme["faint"]
    period = max(.45, min(1.6, 60 / bpm)) if bpm else 0
    heart_anim = f"animation:heartbeat {period:.2f}s ease-in-out 1s infinite" if bpm else ""
    status = "BEATING" if bpm else "RESTING"
    hx, hy = RX + 20, MY + 21
    readout = (
        f'<g class="fade" style="animation-delay:.2s">'
        f'<rect x="{RX}" y="{MY}" width="{RW}" height="{MH}" rx="10" fill="{theme["bg"]}" '
        f'fill-opacity="{.55 if dark else .7}" stroke="{theme["line"]}"/></g>'
        f'<path d="{_heart(hx, hy, 7)}" fill="{heart_color}" class="beat" style="{heart_anim}" filter="url(#glow)"/>'
        f'<text x="{hx + 14}" y="{hy + 4}" class="mb" font-size="10" letter-spacing="2" fill="{theme["text"]}">BPM</text>'
        f'<text x="{RX + RW - 12}" y="{hy + 4}" text-anchor="end" class="m" font-size="8.5" letter-spacing="1" '
        f'fill="{theme["muted"]}">{status}</text>'
        + odometer(bpm, RX + RW / 2, MY + 76, 34, theme, color=theme["text"], anchor="middle", delay=.6)
        + f'<text x="{RX + RW / 2}" y="{MY + MH - 10}" text-anchor="middle" class="m" font-size="8.5" letter-spacing=".8" '
        f'fill="{theme["muted"]}">{WEEKS} WEEKS · {total:,} TOTAL</text>'
    )

    header = (
        label(28, 34, "Heartbeat", theme, color=theme["pink"])
        + f'<text x="{W - 28}" y="34" text-anchor="end" class="m fade" font-size="10" letter-spacing="1.2" '
        f'fill="{theme["muted"]}" style="animation-delay:.2s">{esc("BPM = CONTRIBUTIONS IN THE LAST 7 DAYS")}</text>'
    )
    body = panel(W, H, theme, accent=theme["pink"]) + header + monitor + readout
    title = f"Weekly contribution heartbeat: {bpm} contributions in the last 7 days, {total} in 26 weeks"
    return document(W, H, body, theme, css=CSS, title=title)
