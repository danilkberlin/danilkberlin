"""Nightly Build: a CI pipeline that lights up, plus "Tonight in Berlin"."""
from __future__ import annotations

import math
import time

from ..config import Config
from ..data.astro import moon_path
from ..model import Data
from .core import HALF, document, esc, label, panel, text_width

H = 260
STAGES = ["FETCH", "CRUNCH", "RENDER", "DEPLOY"]


def _weather_icon(kind: str, x: float, y: float, theme: dict, is_day: bool = False) -> str:
    """Small line icon centred at (x, y)."""
    def line_style(color: str) -> str:
        return f'fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"'

    stroke = line_style(theme["text"])
    cloud = (
        f'<path d="M{x - 13},{y + 5} a7,7 0 0 1 1,-13.8 a9,9 0 0 1 17,-2 a6.5,6.5 0 0 1 8,6.3 a5,5 0 0 1 -1,9.5z" {stroke}/>'
    )
    if kind == "clear" and is_day:
        rays = "".join(
            f'<line x1="{x + 10 * math.cos(a):.1f}" y1="{y + 10 * math.sin(a):.1f}" x2="{x + 14 * math.cos(a):.1f}" '
            f'y2="{y + 14 * math.sin(a):.1f}" stroke="{theme["amber"]}" stroke-width="1.8" stroke-linecap="round"/>'
            for a in (i * math.pi / 4 for i in range(8))
        )
        return f'<circle cx="{x}" cy="{y}" r="7" fill="{theme["amber"]}" filter="url(#glow)"/>{rays}'
    if kind == "clear":
        return (
            f'<path d="M{x + 6},{y - 10} a11,11 0 1 0 6,17 a9,9 0 0 1 -6,-17z" fill="{theme["amber"]}" '
            f'filter="url(#glow)"/>'
        )
    if kind == "cloudy":
        return cloud
    if kind == "fog":
        return cloud + "".join(
            f'<line x1="{x - 12 + i * 3}" y1="{y + 10 + i * 4}" x2="{x + 14 - i * 2}" y2="{y + 10 + i * 4}" {stroke}/>'
            for i in range(2)
        )
    if kind == "snow":
        return cloud + "".join(
            f'<circle cx="{x - 8 + i * 8}" cy="{y + 12}" r="1.6" fill="{theme["text"]}" '
            f'style="animation:fall 1.6s linear {i * .4:.1f}s infinite"/>' for i in range(3)
        )
    if kind == "storm":
        return cloud + f'<path d="M{x},{y + 6} l-4,7 h5 l-3,7" {line_style(theme["amber"])}/>'
    # rain / drizzle
    return cloud + "".join(
        f'<line x1="{x - 8 + i * 8}" y1="{y + 9}" x2="{x - 10 + i * 8}" y2="{y + 14}" {line_style(theme["cyan"])} '
        f'style="animation:fall 1s linear {i * .3:.1f}s infinite"/>' for i in range(3)
    )


def render(cfg: Config, data: Data, theme: dict, started: float | None = None) -> str:
    elapsed = time.monotonic() - started if started else 0.0
    out = [panel(HALF, H, theme, accent=theme["green"]), label(22, 34, "Nightly build", theme, color=theme["green"])]
    build = f"#{data.run_number}" if data.run_number else "LOCAL"
    out.append(
        f'<text x="{HALF - 22}" y="34" text-anchor="end" class="mb fade" font-size="11" fill="{theme["faint"] if theme["name"] == "dark" else theme["muted"]}" '
        f'letter-spacing="1.5">{esc(build)}</text>'
    )

    # pipeline
    left, right, py = 46, HALF - 46, 82
    step = (right - left) / (len(STAGES) - 1)
    per = .55
    out.append(f'<line x1="{left}" y1="{py}" x2="{right}" y2="{py}" stroke="{theme["line"]}" stroke-width="3" stroke-linecap="round"/>')
    out.append(
        f'<line x1="{left}" y1="{py}" x2="{right}" y2="{py}" stroke="{theme["green"]}" stroke-width="3" stroke-linecap="round" '
        f'pathLength="1" class="draw" style="animation-duration:{per * (len(STAGES) - 1):.2f}s;animation-delay:.5s;animation-timing-function:linear" '
        f'filter="url(#glow)"/>'
    )
    for i, stage in enumerate(STAGES):
        cx = left + i * step
        at = .5 + i * per
        out.append(
            f'<circle cx="{cx:.1f}" cy="{py}" r="14" fill="{theme["panel"]}" stroke="{theme["line"]}" stroke-width="2"/>'
            # spinner while "running"
            f'<circle cx="{cx:.1f}" cy="{py}" r="14" fill="none" stroke="{theme["amber"]}" stroke-width="2" '
            f'stroke-dasharray="22 66" style="transform-box:fill-box;transform-origin:center;opacity:0;'
            f'animation:spin .5s linear {max(0, at - per):.2f}s {max(1, round(per / .5))},show {per:.2f}s steps(1) {max(0, at - per):.2f}s"/>'
            f'<g class="pop" style="animation-delay:{at:.2f}s">'
            f'<circle cx="{cx:.1f}" cy="{py}" r="14" fill="{theme["green"]}" filter="url(#glow)"/>'
            f'<path d="M{cx - 5.5:.1f},{py + .5} l3.8,3.8 l7,-7.6" fill="none" stroke="{theme["panel"]}" stroke-width="2.6" '
            f'stroke-linecap="round" stroke-linejoin="round"/></g>'
            f'<text x="{cx:.1f}" y="{py + 32}" text-anchor="middle" class="mb fade" font-size="10" letter-spacing="1.4" '
            f'fill="{theme["muted"]}" style="animation-delay:{at:.2f}s">{stage}</text>'
        )
    done = .5 + (len(STAGES) - 1) * per + .3
    when = data.generated_at
    status = f"PASSED · {elapsed:.1f}s · {when:%d.%m.%Y %H:%M} {when.tzname() or ''}"
    out.append(
        f'<g class="up" style="animation-delay:{done:.2f}s">'
        f'<rect x="22" y="{py + 46}" width="{HALF - 44}" height="26" rx="13" fill="{theme["green"]}" fill-opacity=".12" '
        f'stroke="{theme["green"]}" stroke-opacity=".5"/>'
        f'<circle cx="38" cy="{py + 59}" r="4" fill="{theme["green"]}" class="blink" style="animation-duration:2s"/>'
        f'<text x="52" y="{py + 63}" class="mb" font-size="11" fill="{theme["green"]}" letter-spacing=".6">{esc(status)}</text></g>'
    )

    # tonight in Berlin
    ty = 192
    place = (cfg.location.get("name") or "Berlin").upper()
    is_night = not (data.weather and data.weather.is_day)
    out.append(
        f'<line x1="22" y1="{ty - 18}" x2="{HALF - 22}" y2="{ty - 18}" stroke="{theme["line"]}" stroke-dasharray="2 4"/>'
        f'<text x="22" y="{ty - 2}" class="mb fade" font-size="10" letter-spacing="2" fill="{theme["muted"]}" '
        f'style="animation-delay:{done + .2:.2f}s">{"TONIGHT" if is_night else "TODAY"} IN {esc(place)}</text>'
    )
    cols = [22, 150, 292]
    wy = ty + 34
    delay = done + .35
    # weather
    if data.weather:
        temp = f"{data.weather.temp_c:+.0f}°"
        cond = data.weather.kind.upper()
    else:
        temp, cond = "—", "NO DATA"
    out.append(
        f'<g class="up" style="animation-delay:{delay:.2f}s">{_weather_icon(data.weather.kind if data.weather else "cloudy", cols[0] + 16, wy - 6, theme, not is_night)}'
        f'<text x="{cols[0] + 40}" y="{wy}" class="o7" font-size="20" fill="{theme["text"]}">{esc(temp)}</text>'
        f'<text x="{cols[0] + 40}" y="{wy + 16}" class="mb" font-size="9.5" letter-spacing="1.2" fill="{theme["muted"]}">{esc(cond)}</text></g>'
    )
    # moon
    mx, my, mr = cols[1] + 12, wy - 7, 11
    name = data.moon.name.upper()
    out.append(
        f'<g class="up" style="animation-delay:{delay + .12:.2f}s">'
        f'<circle cx="{mx}" cy="{my}" r="{mr}" fill="{theme["line"]}"/>'
        f'<path d="{moon_path(mx, my, mr, data.moon.phase)}" fill="{theme["moon"]}"/>'
        f'<text x="{mx + 20}" y="{wy}" class="o7" font-size="20" fill="{theme["text"]}">{data.moon.illumination * 100:.0f}%</text>'
        f'<text x="{mx + 20}" y="{wy + 16}" class="mb" font-size="9.5" letter-spacing="1.2" fill="{theme["muted"]}">'
        f'{esc(_shorten(name, 118))}</text></g>'
    )
    # sunrise
    sx, sy = cols[2] + 12, wy - 4
    sunrise = f"{data.weather.sunrise:%H:%M}" if data.weather and data.weather.sunrise else "—"
    rays = "".join(
        f'<line x1="{sx + 9 * c:.1f}" y1="{sy - 9 * s:.1f}" x2="{sx + 13 * c:.1f}" y2="{sy - 13 * s:.1f}" '
        f'stroke="{theme["amber"]}" stroke-width="1.8" stroke-linecap="round"/>'
        for c, s in [(1, 0), (.7, .7), (0, 1), (-.7, .7), (-1, 0)]
    )
    out.append(
        f'<g class="up" style="animation-delay:{delay + .24:.2f}s">'
        f'<path d="M{sx - 7},{sy} a7,7 0 0 1 14,0z" fill="{theme["amber"]}"/>{rays}'
        f'<line x1="{sx - 15}" y1="{sy + 3}" x2="{sx + 15}" y2="{sy + 3}" stroke="{theme["text"]}" stroke-width="1.8" stroke-linecap="round"/>'
        f'<text x="{sx + 22}" y="{wy}" class="o7" font-size="20" fill="{theme["text"]}">{esc(sunrise)}</text>'
        f'<text x="{sx + 22}" y="{wy + 16}" class="mb" font-size="9.5" letter-spacing="1.2" fill="{theme["muted"]}">SUNRISE</text></g>'
    )
    css = (
        "@keyframes spin{to{transform:rotate(360deg)}}"
        "@keyframes show{from,to{opacity:1}}"
        "@keyframes fall{from{transform:translateY(-3px);opacity:1}to{transform:translateY(5px);opacity:0}}"
    )
    return document(HALF, H, "".join(out), theme, css=css, title=f"Nightly build {build}: passed")


def _shorten(text: str, width: float) -> str:
    while text_width(text, "mb", 9.5, 1.2) > width and " " in text:
        text = text.rsplit(" ", 1)[0]
    return text
