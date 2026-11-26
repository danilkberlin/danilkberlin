"""Hero banner: Berlin skyline at night (day in light mode), name, typed roles.

Live inputs: tonight's moon phase, current Berlin weather (rain/snow/fog/
clouds/storm particles), build number and timestamp.
"""
from __future__ import annotations

import random

from ..config import Config
from ..data.astro import moon_path
from ..model import Data
from .core import W, document, esc, fit_size, text_width

H = 380
HORIZON = 300


def _sky(theme: dict) -> str:
    if theme["name"] == "dark":
        stops = [(0, "#03051a"), (.5, "#0f0b38"), (.8, "#2c0d4d"), (1, "#5a1561")]
        ground = [(0, "#1a0833"), (1, "#05030f")]
    else:
        stops = [(0, "#7cc4ff"), (.45, "#bfe2ff"), (.8, "#ffd3ea"), (1, "#ffbfa6")]
        ground = [(0, "#f6d9f0"), (1, "#efe9ff")]
    sky = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    gnd = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in ground)
    return (
        f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">{sky}</linearGradient>'
        f'<linearGradient id="gnd" x1="0" y1="0" x2="0" y2="1">{gnd}</linearGradient>'
        f'<radialGradient id="haze" cx=".5" cy="1" r=".7"><stop offset="0" stop-color="{theme["pink"]}" stop-opacity=".45"/>'
        f'<stop offset="1" stop-color="{theme["pink"]}" stop-opacity="0"/></radialGradient></defs>'
        f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
        f'<ellipse cx="{W / 2}" cy="{HORIZON}" rx="520" ry="150" fill="url(#haze)"/>'
    )


def _stars(rng: random.Random, theme: dict) -> str:
    if theme["name"] != "dark":
        return ""
    out = []
    for _ in range(110):
        x, y = rng.uniform(0, W), rng.uniform(0, HORIZON - 70) ** 1.08 * 0.86
        r = rng.choice([.5, .6, .7, .8, 1, 1.2, 1.5])
        color = rng.choice(["#ffffff"] * 6 + [theme["cyan"], theme["pink"], theme["violet"]])
        out.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" class="twinkle" '
            f'style="animation-duration:{rng.uniform(2, 6):.1f}s;animation-delay:-{rng.uniform(0, 6):.1f}s"/>'
        )
    # shooting stars
    for i, (x, y, delay) in enumerate([(260, 40, 2.5), (620, 22, 9.0), (470, 70, 15.5)]):
        out.append(
            f'<g style="animation:shoot 18s linear {delay}s infinite" opacity="0">'
            f'<line x1="{x}" y1="{y}" x2="{x - 70}" y2="{y - 26}" stroke="url(#tail)" stroke-width="1.6" stroke-linecap="round"/>'
            f'<circle cx="{x}" cy="{y}" r="1.6" fill="#fff"/></g>'
        )
    return "".join(out)


def _moon(data: Data, theme: dict) -> str:
    cx, cy, r = 96, 82, 26
    if theme["name"] == "dark":
        lit = moon_path(cx, cy, r, data.moon.phase)
        glow = .25 + .55 * data.moon.illumination
        return (
            f'<defs><radialGradient id="mglow"><stop offset="0" stop-color="#fff3c4" stop-opacity="{glow:.2f}"/>'
            f'<stop offset="1" stop-color="#fff3c4" stop-opacity="0"/></radialGradient></defs>'
            f'<circle cx="{cx}" cy="{cy}" r="{r * 3.4}" fill="url(#mglow)" class="breathe"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#1c2152"/>'
            f'<path d="{lit}" fill="#fff6d6"/>'
            f'<g fill="#e8dcb0" opacity=".55"><circle cx="{cx - 8}" cy="{cy - 6}" r="4"/>'
            f'<circle cx="{cx + 9}" cy="{cy + 8}" r="3"/><circle cx="{cx + 4}" cy="{cy - 12}" r="2"/></g>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#fff6d6" stroke-opacity=".15"/>'
        )
    # Day: a striped synthwave sun.
    stripes = "".join(
        f'<rect x="{cx - r - 2}" y="{cy + 2 + i * 7}" width="{2 * r + 4}" height="{1.6 + i * .9:.1f}" fill="#bfe2ff"/>'
        for i in range(4)
    )
    return (
        f'<defs><linearGradient id="sun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd166"/>'
        f'<stop offset="1" stop-color="#ff5fa2"/></linearGradient>'
        f'<radialGradient id="sglow"><stop offset="0" stop-color="#ffd166" stop-opacity=".55"/>'
        f'<stop offset="1" stop-color="#ffd166" stop-opacity="0"/></radialGradient></defs>'
        f'<circle cx="{cx}" cy="{cy}" r="{r * 3}" fill="url(#sglow)" class="breathe"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#sun)"/>{stripes}'
    )


def _plane() -> str:
    return (
        '<g style="animation:fly 46s linear 4s infinite" opacity="0">'
        '<circle cx="0" cy="0" r="1.3" fill="#fff"/>'
        '<circle cx="-5" cy="0" r="1.2" fill="#ff4d6d" class="blink" style="animation-duration:.9s"/>'
        '<circle cx="5" cy="1" r="1.2" fill="#3ddc97" class="blink" style="animation-duration:1.3s"/></g>'
    )


def _clouds(rng: random.Random, theme: dict, count: int, opacity: float) -> str:
    color = "#2a2c62" if theme["name"] == "dark" else "#ffffff"
    rim = theme["pink"] if theme["name"] == "dark" else "#ffffff"
    out = []
    for i in range(count):
        y = rng.uniform(30, 150)
        scale = rng.uniform(.7, 1.3)
        duration = rng.uniform(70, 120)
        blobs = "".join(
            f'<ellipse cx="{dx * scale:.0f}" cy="{dy * scale:.0f}" rx="{rx * scale:.0f}" ry="{ry * scale:.0f}"/>'
            for dx, dy, rx, ry in [(0, 0, 46, 16), (-26, -6, 24, 15), (14, -14, 26, 18), (38, -2, 20, 11)]
        )
        out.append(
            f'<g style="animation:drift {duration:.0f}s linear -{rng.uniform(0, duration):.0f}s infinite">'
            f'<g transform="translate(0 {y:.0f})" fill="{color}" opacity="{opacity}" stroke="{rim}" stroke-opacity=".18">{blobs}</g></g>'
        )
    return "".join(out)


def _weather(data: Data, rng: random.Random, theme: dict) -> tuple[str, str]:
    """Returns (behind-skyline layer, in-front layer)."""
    kind = data.weather.kind if data.weather else "clear"
    dark = theme["name"] == "dark"
    behind, front = "", ""
    if kind in ("cloudy", "fog", "rain", "drizzle", "storm", "snow"):
        behind += _clouds(rng, theme, 5 if kind in ("cloudy", "storm") else 3, .55 if dark else .8)
    if kind in ("rain", "drizzle", "storm"):
        drops = {"drizzle": 45, "rain": 90, "storm": 130}[kind]
        color = "#9fb4ff" if dark else "#5b6fd6"
        for _ in range(drops):
            x = rng.uniform(0, W + 80)
            length = rng.uniform(8, 16)
            front += (
                f'<line x1="{x:.0f}" y1="-20" x2="{x - 3:.0f}" y2="{-20 + length:.0f}" stroke="{color}" '
                f'stroke-opacity="{rng.uniform(.25, .6):.2f}" stroke-width="1" '
                f'style="animation:rain {rng.uniform(.55, 1.0):.2f}s linear -{rng.uniform(0, 1):.2f}s infinite"/>'
            )
    if kind == "storm":
        front += f'<rect width="{W}" height="{HORIZON}" fill="#fff" opacity="0" style="animation:flash 9s 3s infinite"/>'
    if kind == "snow":
        for _ in range(80):
            x = rng.uniform(0, W)
            front += (
                f'<g style="animation:sway {rng.uniform(2.5, 4):.1f}s ease-in-out -{rng.uniform(0, 4):.1f}s infinite alternate">'
                f'<circle cx="{x:.0f}" cy="-10" r="{rng.uniform(.8, 2.4):.1f}" fill="#fff" opacity="{rng.uniform(.5, .95):.2f}" '
                f'style="animation:snow {rng.uniform(7, 14):.1f}s linear -{rng.uniform(0, 14):.1f}s infinite"/></g>'
            )
    if kind == "fog":
        color = "#8a8fc4" if dark else "#ffffff"
        for i in range(4):
            front += (
                f'<ellipse cx="{rng.uniform(100, 740):.0f}" cy="{HORIZON - 20 + i * 14}" rx="320" ry="16" fill="{color}" '
                f'opacity=".18" style="animation:fog {rng.uniform(16, 26):.0f}s ease-in-out -{rng.uniform(0, 10):.0f}s infinite alternate"/>'
            )
    return behind, front


def _tv_tower(x: float, theme: dict, fill: str) -> str:
    base, top = HORIZON, 120
    sphere_y = 168
    lights = "".join(
        f'<rect x="{x - 11 + i * 3.2:.1f}" y="{sphere_y - 1.5}" width="1.6" height="3" fill="{theme["amber"] if theme["name"] == "dark" else "#ffffff"}" '
        f'opacity=".9"/>' for i in range(8)
    )
    return (
        f'<g fill="{fill}">'
        f'<path d="M{x - 7},{base} L{x - 3.2},{sphere_y + 10} L{x + 3.2},{sphere_y + 10} L{x + 7},{base}Z"/>'
        f'<path d="M{x - 12},{base} L{x - 4},{base - 24} L{x + 4},{base - 24} L{x + 12},{base}Z"/>'
        f'<circle cx="{x}" cy="{sphere_y}" r="14"/>'
        f'<rect x="{x - 2.6}" y="{top + 18}" width="5.2" height="{sphere_y - top - 30}"/>'
        f'<rect x="{x - 5}" y="{sphere_y - 20}" width="10" height="6" rx="2"/>'
        f'<rect x="{x - 1.2}" y="{top - 40}" width="2.4" height="60"/>'
        f'</g>{lights}'
        f'<g fill="#ff3355">' + "".join(
            f'<rect x="{x - 1.2}" y="{top - 40 + i * 12}" width="2.4" height="5" opacity=".85"/>' for i in range(5)
        ) + '</g>'
        f'<circle cx="{x}" cy="{top - 42}" r="2.6" fill="#ff2d55" filter="url(#glow)" class="beacon"/>'
    )


def _brandenburg(x: float, fill: str) -> str:
    base = HORIZON
    cols = "".join(f'<rect x="{x + 4 + i * 11.6:.1f}" y="{base - 38}" width="5" height="38"/>' for i in range(6))
    return (
        f'<g fill="{fill}">{cols}'
        f'<rect x="{x}" y="{base - 46}" width="72" height="9"/>'
        f'<rect x="{x + 16}" y="{base - 56}" width="40" height="11"/>'
        f'<path d="M{x + 26},{base - 56} l4,-9 h4 l3,4 h6 l2,-6 l3,11Z"/>'
        f'<rect x="{x - 6}" y="{base - 30}" width="8" height="30"/><rect x="{x + 70}" y="{base - 30}" width="8" height="30"/>'
        f"</g>"
    )


def _skyline(rng: random.Random, theme: dict) -> str:
    dark = theme["name"] == "dark"
    far_fill = "#1b1446" if dark else "#b6a9e6"
    near_top, near_bottom = ("#191541", "#07061a") if dark else ("#8c7fd0", "#6c61b5")
    window_colors = [theme["amber"], "#ffe8a3", theme["cyan"], theme["pink"]] if dark else ["#e9f6ff", "#ffffff", "#ffe1f0"]
    out = [
        f'<defs><linearGradient id="bld" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{near_top}"/>'
        f'<stop offset="1" stop-color="{near_bottom}"/></linearGradient></defs>'
    ]
    # Far layer
    x = -10
    far = []
    while x < W + 10:
        w = rng.uniform(22, 60)
        h = rng.uniform(40, 120)
        far.append(f'<rect x="{x:.0f}" y="{HORIZON - h:.0f}" width="{w:.0f}" height="{h:.0f}"/>')
        x += w - 2
    out.append(f'<g fill="{far_fill}" opacity=".85">{"".join(far)}</g>')

    out.append(_brandenburg(108, near_bottom if dark else near_bottom))
    out.append(_tv_tower(752, theme, near_top if dark else "#6c61b5"))

    # Near layer with windows (gaps left for the landmarks)
    x = -6
    windows = []
    near = []
    while x < W + 6:
        w = rng.uniform(18, 46)
        if 92 < x + w and x < 196:  # keep the Gate clear
            x = 196
            continue
        if 735 < x + w and x < 772:  # keep the tower base readable
            x = 772
            continue
        limit = 78 if 230 < x < 610 else 96
        h = rng.uniform(26, limit)
        top = HORIZON - h
        near.append(f'<rect x="{x:.0f}" y="{top:.0f}" width="{w:.0f}" height="{h + 1:.0f}"/>')
        if rng.random() < .35:
            near.append(f'<rect x="{x + w / 2 - 1:.0f}" y="{top - rng.uniform(6, 16):.0f}" width="2" height="16"/>')
        if rng.random() < .3:
            near.append(f'<rect x="{x + 4:.0f}" y="{top - 6:.0f}" width="{w - 8:.0f}" height="7"/>')
        for wx in range(int(x + 4), int(x + w - 4), 6):
            for wy in range(int(top + 6), HORIZON - 6, 8):
                if rng.random() < (.26 if dark else .18):
                    color = rng.choice(window_colors)
                    flicker = ""
                    if rng.random() < .12:
                        flicker = f' class="flick" style="animation-duration:{rng.uniform(3, 9):.1f}s;animation-delay:-{rng.uniform(0, 9):.1f}s"'
                    windows.append(f'<rect x="{wx}" y="{wy}" width="2.4" height="3.4" fill="{color}"{flicker}/>')
        x += w + rng.choice([0, 0, 2, 4])
    out.append(f'<g fill="url(#bld)">{"".join(near)}</g>')
    out.append(f'<g opacity="{.95 if dark else .8}">{"".join(windows)}</g>')
    # rim light on the horizon
    out.append(f'<rect y="{HORIZON - 1}" width="{W}" height="2" fill="{theme["pink"]}" opacity=".8" filter="url(#glow)"/>')
    return "".join(out)


def _grid(theme: dict) -> str:
    dark = theme["name"] == "dark"
    color = theme["pink"] if dark else theme["violet"]
    vx = W / 2
    lines = [f'<rect y="{HORIZON}" width="{W}" height="{H - HORIZON}" fill="url(#gnd)"/>']
    for i in range(-16, 17):
        lines.append(
            f'<line x1="{vx + i * 9:.0f}" y1="{HORIZON}" x2="{vx + i * 120:.0f}" y2="{H}" stroke="{color}" stroke-opacity=".5" stroke-width="1"/>'
        )
    # Horizontal lines in perspective, each sliding to the next line's slot.
    rows = 9
    positions = [HORIZON + (H - HORIZON) * (i / rows) ** 2 for i in range(rows + 1)]
    css = []
    for i in range(rows):
        y, nxt = positions[i], positions[i + 1]
        css.append(f"@keyframes g{i}{{to{{transform:translateY({nxt - y:.2f}px)}}}}")
        lines.append(
            f'<line x1="0" y1="{y:.2f}" x2="{W}" y2="{y:.2f}" stroke="{color}" stroke-opacity="{.25 + .6 * i / rows:.2f}" '
            f'stroke-width="{.6 + i * .12:.2f}" style="animation:g{i} 1.6s linear infinite"/>'
        )
    lines.append(f'<rect y="{HORIZON}" width="{W}" height="16" fill="{theme["pink"]}" opacity=".12"/>')
    return f'<g>{"".join(lines)}</g>', "".join(css)


def _roles(cfg: Config, theme: dict, cy: float) -> tuple[str, str]:
    dark = theme["name"] == "dark"
    size = 17
    roles = cfg.roles
    widest = max(text_width(r, "m", size) for r in roles)
    pill_w = widest + 74
    pill_h = 38
    px = W / 2 - pill_w / 2
    pill_fill = "#0c1033" if dark else "#ffffff"
    tx = px + 40
    baseline = cy + 6
    timings = []
    t = 0.0
    for role in roles:
        n = len(role)
        typing = n / 18
        hold = 2.2
        erase = n / 40
        timings.append((t, typing, hold, erase, n))
        t += typing + hold + erase + .35
    cycle = t
    start = 2.0
    css = []
    groups = []
    for i, (role, (t0, typing, hold, erase, n)) in enumerate(zip(roles, timings)):
        width = text_width(role, "m", size)
        p = lambda s: f"{100 * s / cycle:.3f}%"  # noqa: E731
        a, b, c, d = t0, t0 + typing, t0 + typing + hold, t0 + typing + hold + erase
        css.append(
            f"@keyframes rc{i}{{0%{{transform:translateX(0)}}"
            f"{p(a)}{{transform:translateX(0);animation-timing-function:steps({n})}}"
            f"{p(b)}{{transform:translateX({width:.1f}px)}}"
            f"{p(c)}{{transform:translateX({width:.1f}px);animation-timing-function:steps({n})}}"
            f"{p(d)}{{transform:translateX(0)}}100%{{transform:translateX(0)}}}}"
            f"@keyframes rv{i}{{0%,{p(max(0, a - .01))}{{opacity:0}}{p(a)},{p(d + .3)}{{opacity:1}}"
            f"{p(min(cycle, d + .31))},100%{{opacity:0}}}}"
        )
        anim = f"{cycle:.2f}s linear {start}s infinite"
        groups.append(
            f'<g style="opacity:{1 if i == 0 else 0};animation:rv{i} {anim}">'
            f'<svg x="{tx - 2:.1f}" y="{baseline - 20}" width="{widest + 16:.0f}" height="28" overflow="hidden">'
            f'<text x="2" y="20" class="m" font-size="{size}" fill="{theme["text"]}">{esc(role)}</text>'
            f'<rect x="0" y="0" width="{widest + 16:.0f}" height="28" fill="{pill_fill}" '
            f'style="transform:translateX({width + 3:.1f}px);animation:rc{i} {anim}"/></svg>'
            f'<rect x="{tx + 2:.1f}" y="{baseline - 15}" width="9" height="18" fill="{theme["pink"]}" '
            f'style="transform:translateX({width + 2:.1f}px);animation:rc{i} {anim}"/></g>'
        )
    pill = (
        f'<g class="up" style="animation-delay:1.6s">'
        f'<rect x="{px:.1f}" y="{cy - pill_h / 2}" width="{pill_w:.1f}" height="{pill_h}" rx="{pill_h / 2}" fill="{pill_fill}" '
        f'stroke="{theme["cyan"]}" stroke-opacity=".75" filter="url(#glow)"/>'
        f'<text x="{px + 18:.1f}" y="{baseline}" class="mb" font-size="{size}" fill="{theme["cyan"]}">›</text>'
        f'{"".join(groups)}</g>'
    )
    return pill, "".join(css)


def render(cfg: Config, data: Data, theme: dict) -> str:
    rng = random.Random(1989)  # skyline is stable; weather particles vary with seed below
    wrng = random.Random(data.generated_at.date().toordinal())
    dark = theme["name"] == "dark"

    name = cfg.name.upper()
    size = fit_size(name, "o", 640, 50, spacing=4)
    name_w = text_width(name, "o", size, 4)
    name_y = 146
    grad = (
        f'<defs><linearGradient id="nameg" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{theme["cyan"]}"/><stop offset=".55" stop-color="{theme["violet"]}"/>'
        f'<stop offset="1" stop-color="{theme["pink"]}"/></linearGradient>'
        f'<linearGradient id="tail" x1="1" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#fff"/>'
        f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>'
    )
    name_attrs = f'x="{W / 2}" y="{name_y}" text-anchor="middle" font-size="{size}" letter-spacing="4"'
    name_block = (
        f'<text {name_attrs} fill="none" stroke="url(#nameg)" stroke-width="1.2" class="o name-stroke">{esc(name)}</text>'
        f'<text {name_attrs} fill="url(#nameg)" class="o name-fill" filter="url(#glow)">{esc(name)}</text>'
        f'<text {name_attrs} fill="{theme["cyan"]}" class="o glitch g1">{esc(name)}</text>'
        f'<text {name_attrs} fill="{theme["pink"]}" class="o glitch g2">{esc(name)}</text>'
    )
    hello = (
        f'<text x="{W / 2}" y="{name_y - size - 14:.0f}" text-anchor="middle" class="mb fade" font-size="12" '
        f'letter-spacing="6" fill="{theme["muted"] if dark else theme["text"]}" style="animation-delay:.3s">'
        f"HI THERE, I&#8217;M</text>"
    )
    underline = (
        f'<rect x="{W / 2 - name_w / 2:.0f}" y="{name_y + 12}" width="{name_w:.0f}" height="2" fill="url(#nameg)" '
        f'class="growx" style="animation-delay:1.2s" filter="url(#glow)"/>'
    )
    pill, role_css = _roles(cfg, theme, name_y + 52)
    grid, grid_css = _grid(theme)
    behind, front = _weather(data, wrng, theme)

    when = data.generated_at
    temp = f"{data.weather.temp_c:+.0f}°C {data.weather.kind.upper()}" if data.weather else "NO WEATHER DATA"
    hud_color = theme["muted"] if dark else theme["text"]
    build = f"BUILD #{data.run_number}" if data.run_number else "LOCAL BUILD"
    hud = (
        f'<g class="mb fade" font-size="10" letter-spacing="1.5" fill="{hud_color}" style="animation-delay:2.4s">'
        f'<text x="{W - 20}" y="26" text-anchor="end">{esc(build)} · {when:%d.%m.%Y %H:%M} {esc(when.tzname() or "")}</text>'
        f'<circle cx="{W - 20 - text_width(f"{build} · {when:%d.%m.%Y %H:%M} {when.tzname() or ""}", "mb", 10, 1.5) - 10:.0f}" cy="22.5" r="3" '
        f'fill="{theme["green"]}" class="blink"/>'
        f'<text x="20" y="{H - 14}" fill="{theme["muted"] if dark else theme["violet"]}">52.52°N 13.40°E · BERLIN · {esc(temp)} · '
        f'{esc(data.moon.name.upper())} {data.moon.illumination * 100:.0f}%</text>'
        f'<text x="{W - 20}" y="{H - 14}" text-anchor="end" fill="{theme["muted"] if dark else theme["violet"]}">github.com/{esc(cfg.login)}</text>'
        f"</g>"
    )

    css = f"""
    .name-stroke{{stroke-dasharray:520;stroke-dashoffset:0;animation:trace 2.4s cubic-bezier(.6,0,.3,1) .2s both}}
    .name-fill{{animation:fillin 1s ease 1.6s both}}
    .glitch{{opacity:0;animation:glitch 7s steps(1) 4s infinite}}
    .g2{{animation-delay:4.06s}}
    .beacon{{animation:beacon 1.4s ease-in-out infinite}}
    .breathe{{animation:breathe 6s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}
    .flick{{animation:flick 6s steps(1) infinite}}
    @keyframes trace{{from{{stroke-dashoffset:520}}}}
    @keyframes fillin{{from{{opacity:0}}}}
    @keyframes glitch{{0%{{opacity:0}}93%{{opacity:.7;transform:translate(-3px,1px)}}94%{{opacity:.6;transform:translate(3px,-1px)}}
      95%{{opacity:.7;transform:translate(-1px,0)}}96%{{opacity:0;transform:none}}}}
    @keyframes beacon{{50%{{opacity:.15}}}}
    @keyframes breathe{{50%{{transform:scale(1.08);opacity:.8}}}}
    @keyframes flick{{0%{{opacity:1}}40%{{opacity:.1}}43%{{opacity:1}}70%{{opacity:.2}}72%{{opacity:1}}}}
    @keyframes shoot{{0%{{opacity:0;transform:translate(0,0)}}1%{{opacity:1}}5%{{opacity:0;transform:translate(-220px,-80px)}}100%{{opacity:0}}}}
    @keyframes fly{{0%{{opacity:1;transform:translate(-20px,64px)}}100%{{opacity:1;transform:translate(880px,36px)}}}}
    @keyframes drift{{from{{transform:translateX(-160px)}}to{{transform:translateX({W + 160}px)}}}}
    @keyframes rain{{from{{transform:translate(0,0)}}to{{transform:translate(-26px,{H + 40}px)}}}}
    @keyframes snow{{from{{transform:translateY(0)}}to{{transform:translateY({H + 20}px)}}}}
    @keyframes sway{{from{{transform:translateX(-8px)}}to{{transform:translateX(8px)}}}}
    @keyframes fog{{from{{transform:translateX(-60px)}}to{{transform:translateX(60px)}}}}
    @keyframes flash{{0%,100%{{opacity:0}}1%{{opacity:.5}}2%{{opacity:0}}3%{{opacity:.35}}5%{{opacity:0}}}}
    {grid_css}{role_css}
    """
    body = (
        f"{grad}{_sky(theme)}{_stars(wrng, theme)}{_moon(data, theme)}{_plane() if dark else ''}{behind}"
        f"{_skyline(rng, theme)}{grid}{front}"
        f'<g>{hello}{name_block}{underline}{pill}</g>{hud}'
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="{theme["line"]}"/>'
    )
    # Rounded corners for the whole scene.
    clip = f'<clipPath id="round"><rect width="{W}" height="{H}" rx="18"/></clipPath>'
    return document(W, H, f'<g clip-path="url(#round)">{body}</g>', theme, css=css, defs=clip,
                    title=f"{cfg.name} — {', '.join(cfg.roles)}")
