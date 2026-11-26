"""Night Owl Meter: 24h radial commit histogram, chronotype verdict, weekday bars."""
from __future__ import annotations

from .. import stats
from ..config import Config
from ..model import Data
from .core import HALF, arc_path, document, esc, fit_size, label, panel, polar

H = 300
CX, CY = 124, 168
R0 = 34  # inner radius where bars start
BAR = 58  # maximum bar length
TRACK_OUT = R0 + BAR
TICK = 98
LABEL_R = 109
RIGHT_X = 252
RIGHT_END = HALF - 20

NIGHT = {21, 22, 23, 0, 1, 2, 3}
MORNING = {4, 5, 6, 7, 8}


def _hour_color(hour: int, theme: dict) -> str:
    if hour in NIGHT:
        return theme["violet"]
    if hour in MORNING:
        return theme["amber"]
    return theme["cyan"]


def _icon(kind: str, cx: float, cy: float, color: str, theme: dict) -> str:
    """Small drawn emblem for the verdict (no emoji)."""
    if kind == "NIGHT OWL":
        return (
            f'<mask id="crescent"><rect x="{cx - 16}" y="{cy - 16}" width="32" height="32" fill="#fff"/>'
            f'<circle cx="{cx + 5.5}" cy="{cy - 4.5}" r="9.5" fill="#000"/></mask>'
            f'<g filter="url(#glow)"><circle cx="{cx}" cy="{cy}" r="11" fill="{color}" mask="url(#crescent)"/></g>'
            f'<path d="M{cx + 9},{cy - 12} l1,2.4 2.4,1 -2.4,1 -1,2.4 -1,-2.4 -2.4,-1 2.4,-1z" fill="{color}" class="twinkle"/>'
            f'<circle cx="{cx + 12}" cy="{cy + 4}" r="1" fill="{color}" class="twinkle" style="animation-delay:-1.4s"/>'
        )
    if kind == "EARLY BIRD":
        rays = "".join(
            f'<line x1="{polar(cx, cy + 4, 11, a)[0]:.1f}" y1="{polar(cx, cy + 4, 11, a)[1]:.1f}" '
            f'x2="{polar(cx, cy + 4, 15, a)[0]:.1f}" y2="{polar(cx, cy + 4, 15, a)[1]:.1f}"/>'
            for a in (-60, -30, 0, 30, 60)
        )
        return (
            f'<clipPath id="horizon"><rect x="{cx - 18}" y="{cy - 18}" width="36" height="{22}"/></clipPath>'
            f'<g filter="url(#glow)"><circle cx="{cx}" cy="{cy + 4}" r="8" fill="{color}" clip-path="url(#horizon)"/></g>'
            f'<g stroke="{color}" stroke-width="1.8" stroke-linecap="round" class="rise">{rays}</g>'
            f'<line x1="{cx - 15}" y1="{cy + 4.5}" x2="{cx + 15}" y2="{cy + 4.5}" stroke="{color}" stroke-width="1.8" stroke-linecap="round"/>'
            f'<line x1="{cx - 9}" y1="{cy + 9}" x2="{cx + 9}" y2="{cy + 9}" stroke="{color}" stroke-width="1.4" stroke-linecap="round" opacity=".6"/>'
        )
    if kind == "DAY WALKER":
        rays = "".join(
            f'<line x1="{polar(cx, cy, 10, a)[0]:.1f}" y1="{polar(cx, cy, 10, a)[1]:.1f}" '
            f'x2="{polar(cx, cy, 14, a)[0]:.1f}" y2="{polar(cx, cy, 14, a)[1]:.1f}"/>'
            for a in range(0, 360, 45)
        )
        return (
            f'<circle cx="{cx}" cy="{cy}" r="6.5" fill="{color}" filter="url(#glow)"/>'
            f'<g stroke="{color}" stroke-width="1.8" stroke-linecap="round">{rays}'
            f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" '
            f'dur="24s" repeatCount="indefinite"/></g>'
        )
    # No data: a dashed dial waiting to start
    return (
        f'<circle cx="{cx}" cy="{cy}" r="11" fill="none" stroke="{color}" stroke-width="1.6" stroke-dasharray="3 3"/>'
        f'<line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy - 7}" stroke="{color}" stroke-width="1.6" stroke-linecap="round"/>'
        f'<line x1="{cx}" y1="{cy}" x2="{cx + 5}" y2="{cy}" stroke="{color}" stroke-width="1.6" stroke-linecap="round"/>'
    )


def _dial(data: Data, theme: dict, hours: list[int], peak: int | None) -> str:
    dark = theme["name"] == "dark"
    top = max(hours) if any(hours) else 0
    out = []
    # Night zone (21:00 → 04:00) as a soft band behind the bars.
    out.append(
        f'<path d="{arc_path(CX, CY, R0 + BAR / 2, 21 * 15, 4 * 15 + 360)}" fill="none" stroke="{theme["violet"]}" '
        f'stroke-opacity="{.10 if dark else .08}" stroke-width="{BAR + 8}" class="fade"/>'
    )
    out.append(
        f'<circle cx="{CX}" cy="{CY}" r="{TRACK_OUT + 2}" fill="none" stroke="{theme["line"]}" stroke-dasharray="1 3"/>'
    )
    tracks, bars, ticks, labels = [], [], [], []
    for hour in range(24):
        angle = hour * 15
        x1, y1 = polar(CX, CY, R0, angle)
        x2, y2 = polar(CX, CY, TRACK_OUT, angle)
        tracks.append(f"M{x1:.1f},{y1:.1f}L{x2:.1f},{y2:.1f}")
        major = hour % 6 == 0
        t1 = polar(CX, CY, TICK - (2 if major else 0), angle)
        t2 = polar(CX, CY, TICK + (5 if major else 2.5), angle)
        ticks.append(
            f'<line x1="{t1[0]:.1f}" y1="{t1[1]:.1f}" x2="{t2[0]:.1f}" y2="{t2[1]:.1f}" '
            f'stroke="{theme["muted"] if major else theme["faint"]}" stroke-width="{1.4 if major else 1}"/>'
        )
        if major:
            lx, ly = polar(CX, CY, LABEL_R, angle)
            labels.append(
                f'<text x="{lx:.1f}" y="{ly + 3.6:.1f}" text-anchor="middle" class="mb" font-size="10" '
                f'fill="{theme["muted"]}">{hour:02d}</text>'
            )
        value = hours[hour]
        if not value:
            continue
        length = max(4.0, BAR * value / top)
        bx, by = polar(CX, CY, R0 + length, angle)
        is_peak = hour == peak
        color = theme["pink"] if is_peak else _hour_color(hour, theme)
        delay = .35 + hour * .045
        bars.append(
            f'<path d="M{x1:.1f},{y1:.1f}L{bx:.1f},{by:.1f}" pathLength="1" stroke="{color}" stroke-width="6" '
            f'stroke-linecap="round" class="bar" style="animation-delay:{delay:.2f}s"'
            + (' filter="url(#glow)"' if is_peak else "")
            + "/>"
        )
        if is_peak:
            bars.append(
                f'<g class="fade" style="animation-delay:{delay + .8:.2f}s">'
                f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="4" fill="none" stroke="{color}" stroke-width="1.5" '
                f'class="ping" style="animation-delay:{delay + 1:.2f}s"/></g>'
            )
    out.append(
        f'<path d="{"".join(tracks)}" stroke="{theme["line"]}" stroke-width="6" stroke-linecap="round" '
        f'opacity="{.8 if dark else 1}"/>'
    )
    out += bars + ticks + labels

    # Sweeping hand with a radar wedge, starting at the build time.
    now = data.generated_at
    start = (now.hour + now.minute / 60) * 15
    wedge = "".join(
        f'<path d="M{CX},{CY} L{polar(CX, CY, TRACK_OUT + 4, -a - 15)[0]:.1f},{polar(CX, CY, TRACK_OUT + 4, -a - 15)[1]:.1f} '
        f'A{TRACK_OUT + 4},{TRACK_OUT + 4} 0 0 1 {polar(CX, CY, TRACK_OUT + 4, -a)[0]:.1f},{polar(CX, CY, TRACK_OUT + 4, -a)[1]:.1f}Z" '
        f'fill="{theme["pink"]}" opacity="{op}"/>'
        for a, op in ((0, .16 if dark else .1), (15, .08 if dark else .05), (30, .035 if dark else .02))
    )
    hx, hy = polar(CX, CY, TRACK_OUT + 4, 0)
    sx, sy = polar(CX, CY, R0 - 4, 0)
    out.append(
        f'<g class="fade" style="animation-delay:1.6s"><g>{wedge}'
        f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{hx:.1f}" y2="{hy:.1f}" stroke="{theme["pink"]}" stroke-width="1.6" stroke-linecap="round"/>'
        f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="2.6" fill="{theme["pink"]}" filter="url(#glow)"/>'
        f'<animateTransform attributeName="transform" type="rotate" from="{start:.1f} {CX} {CY}" '
        f'to="{start + 360:.1f} {CX} {CY}" dur="30s" repeatCount="indefinite"/></g></g>'
    )

    # Hub with the peak hour.
    hub_text = f"{peak:02d}:00" if peak is not None else "--:--"
    size = fit_size(hub_text, "o", 42, 11)
    out.append(
        f'<circle cx="{CX}" cy="{CY}" r="{R0 - 7}" fill="{theme["panel2"]}" stroke="{theme["line"]}"/>'
        f'<text x="{CX}" y="{CY - 5}" text-anchor="middle" class="mb" font-size="7.5" letter-spacing="1.4" '
        f'fill="{theme["muted"]}">PEAK</text>'
        f'<text x="{CX}" y="{CY + 9}" text-anchor="middle" class="o" font-size="{size}" '
        f'fill="{theme["pink"] if peak is not None else theme["muted"]}">{hub_text}</text>'
    )
    return "".join(out)


def _badge(verdict: str, peak: int | None, hours: list[int], theme: dict) -> str:
    accent = {
        "NIGHT OWL": theme["violet"], "EARLY BIRD": theme["amber"], "DAY WALKER": theme["cyan"],
    }.get(verdict, theme["muted"])
    total = sum(hours)
    if verdict == "NIGHT OWL":
        share_label, share = "AFTER 21:00", sum(hours[h] for h in NIGHT)
    elif verdict == "EARLY BIRD":
        share_label, share = "BEFORE 09:00", sum(hours[h] for h in MORNING)
    else:
        share_label, share = "09:00–18:00", sum(hours[h] for h in range(9, 19))
    x, y, w, h = RIGHT_X, 50, RIGHT_END - RIGHT_X, 82
    title_x = x + 46
    size = fit_size(verdict, "o", RIGHT_END - title_x - 10, 13.5, spacing=.8)
    rows = (
        [("PEAK HOUR", f"{peak:02d}:00"), (share_label, f"{round(100 * share / total)}%")]
        if total
        else [("COMMITS", "0"), ("STATUS", "WARMING UP")]
    )
    lines = "".join(
        f'<text x="{x + 12}" y="{y + 56 + i * 15}" class="m" font-size="9.5" fill="{theme["muted"]}">{esc(k)}</text>'
        f'<text x="{RIGHT_END - 12}" y="{y + 56 + i * 15}" text-anchor="end" class="mb" font-size="9.5" '
        f'fill="{theme["text"]}">{esc(v)}</text>'
        for i, (k, v) in enumerate(rows)
    )
    return (
        f'<g class="pop" style="animation-delay:.5s">'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{accent}" fill-opacity=".08" '
        f'stroke="{accent}" stroke-opacity=".55"/>'
        f'{_icon(verdict, x + 24, y + 22, accent, theme)}'
        f'<text x="{title_x}" y="{y + 22 + size * .38:.1f}" class="o" font-size="{size}" letter-spacing=".8" '
        f'fill="{accent}">{esc(verdict)}</text>'
        f'<line x1="{x + 12}" y1="{y + 40}" x2="{RIGHT_END - 12}" y2="{y + 40}" stroke="{accent}" stroke-opacity=".25"/>'
        f"{lines}</g>"
    )


def _weekdays(data: Data, theme: dict) -> str:
    values = stats.weekdays(data)
    top = max(values) if any(values) else 0
    base = 262
    max_h = 76
    col_w = 13
    span = RIGHT_END - RIGHT_X
    gap = (span - 7 * col_w) / 6
    out = [
        f'<text x="{RIGHT_X}" y="158" class="mb fade" font-size="9.5" letter-spacing="1.8" fill="{theme["muted"]}" '
        f'style="animation-delay:.9s">BY WEEKDAY</text>',
        f'<line x1="{RIGHT_X}" y1="{base + .5}" x2="{RIGHT_END}" y2="{base + .5}" stroke="{theme["line"]}"/>',
    ]
    best = values.index(top) if top else None
    for i, (letter, value) in enumerate(zip("MTWTFSS", values)):
        x = RIGHT_X + i * (col_w + gap)
        h = max(2.0, max_h * value / top) if top else 2.0
        color = theme["pink"] if i == best else (theme["violet"] if i >= 5 else theme["cyan"])
        out.append(
            f'<rect x="{x:.1f}" y="{base - max_h}" width="{col_w}" height="{max_h}" rx="3" fill="{theme["line"]}" opacity=".45"/>'
            f'<rect x="{x:.1f}" y="{base - h:.1f}" width="{col_w}" height="{h:.1f}" rx="3" fill="{color}" class="growy" '
            f'style="animation-delay:{1 + i * .08:.2f}s"' + (' filter="url(#glow)"' if i == best else "") + "/>"
            f'<text x="{x + col_w / 2:.1f}" y="{base + 14}" text-anchor="middle" class="mb" font-size="9.5" '
            f'fill="{theme["text"] if i == best else theme["muted"]}">{letter}</text>'
        )
    if best is not None:
        x = RIGHT_X + best * (col_w + gap) + col_w / 2
        h = max_h
        out.append(
            f'<text x="{x:.1f}" y="{base - h - 5}" text-anchor="middle" class="mb fade" font-size="8.5" '
            f'fill="{theme["pink"]}" style="animation-delay:1.8s">{values[best]}</text>'
        )
    return "".join(out)


def render(cfg: Config, data: Data, theme: dict) -> str:
    hours = stats.hours(data)
    verdict, peak_hour = stats.chronotype(data)
    peak = peak_hour if any(hours) else None
    css = """
    .bar{stroke-dasharray:1;stroke-dashoffset:0;animation:draw .9s cubic-bezier(.2,.9,.3,1) both}
    .ping{transform-box:fill-box;transform-origin:center;animation:ping 2.4s ease-out infinite}
    .rise{animation:rise 3s ease-in-out infinite}
    @keyframes ping{0%{transform:scale(.6);opacity:1}80%,100%{transform:scale(2.6);opacity:0}}
    @keyframes rise{50%{opacity:.35}}
    """
    body = (
        panel(HALF, H, theme, accent=theme["violet"])
        + label(22, 32, "Night Owl Meter", theme, color=theme["violet"])
        + _dial(data, theme, hours, peak)
        + _badge(verdict, peak, hours, theme)
        + _weekdays(data, theme)
    )
    title = f"Commit clock: {verdict.lower()}" + (f", peak at {peak:02d}:00" if peak is not None else "")
    return document(HALF, H, body, theme, css=css, title=title)

