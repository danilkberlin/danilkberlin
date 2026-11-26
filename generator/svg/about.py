"""About: a neofetch-style terminal. ASCII Fernsehturm + live system info."""
from __future__ import annotations

from ..config import Config
from ..model import Data
from .. import stats
from .core import TYPED_CSS, W, document, esc, fit_size, text_width, typed

H = 372

ART = [
    "        .        ",
    "        |        ",
    "        |        ",
    "        |        ",
    "       _|_       ",
    "     .'   '.     ",
    "    | ::::: |    ",
    "     '.___.'     ",
    "       |#|       ",
    "       |#|       ",
    "       |#|       ",
    "       |#|       ",
    "      /###\\      ",
    "  ___/#####\\___  ",
]


def render(cfg: Config, data: Data, theme: dict) -> str:
    term_bg = theme["term"]
    bar_bg = theme["term_bar"]
    host = "berlin"
    prompt = f"{cfg.name.split()[0].lower()}@{host}"
    about = cfg.about
    size = 14

    streak = stats.current_streak(data.history)
    info: list[tuple[str, str]] = [
        ("role", f"{about.get('role', '')}" + (f" @ {about['company']}" if about.get("company") else "")),
        ("location", about.get("location", "")),
        ("uptime", f"{stats.coding_uptime(data, cfg.coding_since)} of shipping code"),
        ("focus", ", ".join(about.get("focus", []))),
        ("infra", ", ".join(about.get("infra", []))),
        ("speaks", " · ".join(about.get("speaks", []))),
        ("activity", f"{data.totals.contributions_year:,} contributions this year · {streak}-day streak"),
        ("motto", f'"{about.get("motto", "")}"'),
    ]
    info = [(k, v) for k, v in info if v.strip(' "')]

    out = []
    # window chrome
    out.append(
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{term_bg}" stroke="{theme["line"]}"/>'
        f'<path d="M.5,14.5 a14,14 0 0 1 14,-14 h{W - 29} a14,14 0 0 1 14,14 v19 h-{W - 1}z" fill="{bar_bg}"/>'
        f'<line x1="0" y1="34" x2="{W}" y2="34" stroke="{theme["line"]}"/>'
    )
    for i, color in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        out.append(f'<circle cx="{22 + i * 20}" cy="17" r="6" fill="{color}"/>')
    title = f"{prompt}: ~ — zsh — {W // 8}×{H // 16}"
    out.append(
        f'<text x="{W / 2}" y="21.5" text-anchor="middle" class="m" font-size="11.5" fill="{theme["muted"]}">{esc(title)}</text>'
    )

    # line 1: prompt + typed command
    x0, y = 26, 64
    prompt_text = f"{prompt}:~$"
    pw = text_width(prompt_text + " ", "mb", size)
    out.append(
        f'<text x="{x0}" y="{y}" class="mb fade" font-size="{size}" style="animation-delay:.2s">'
        f'<tspan fill="{theme["green"]}">{esc(prompt)}</tspan><tspan fill="{theme["muted"]}">:</tspan>'
        f'<tspan fill="{theme["cyan"]}">~</tspan><tspan fill="{theme["muted"]}">$</tspan></text>'
    )
    command = "neofetch --city berlin"
    cmd, t = typed(x0 + pw, y, command, cls="m", size=size, fill=theme["text"], cover=term_bg, delay=.6, cps=22,
                   cursor=theme["pink"], cursor_until=.6 + len(command) / 22 + .25)
    out.append(cmd)
    t += .35

    # ASCII art, gradient top→bottom, revealed line by line
    art_size = 12.5
    art_lh = 17
    art_top = 104
    for i, line in enumerate(ART):
        ratio = i / (len(ART) - 1)
        color = _mix(theme["pink"], theme["cyan"], ratio)
        out.append(
            f'<text x="{x0 + 8}" y="{art_top + i * art_lh}" class="mb fade" font-size="{art_size}" fill="{color}" '
            f'xml:space="preserve" style="animation-delay:{t + i * .05:.2f}s;animation-duration:.25s">{esc(line)}</text>'
        )
    beacon_x = x0 + 8 + text_width("        ", "mb", art_size) + text_width(".", "mb", art_size) / 2
    out.append(
        f'<circle cx="{beacon_x:.1f}" cy="{art_top - 8}" r="3" fill="#ff2d55" filter="url(#glow)" '
        f'style="animation:pre {t:.2f}s linear backwards,beacon 1.4s ease-in-out {t:.2f}s infinite"/>'
    )

    # info panel
    ix = 300
    iy = 98
    lh = 22
    header = f"{prompt}"
    out.append(
        f'<text x="{ix}" y="{iy}" class="mb fade" font-size="{size + 1}" style="animation-delay:{t:.2f}s">'
        f'<tspan fill="{theme["pink"]}">{esc(prompt.split("@")[0])}</tspan><tspan fill="{theme["muted"]}">@</tspan>'
        f'<tspan fill="{theme["cyan"]}">{host}</tspan></text>'
        f'<rect x="{ix}" y="{iy + 8}" width="{text_width(header, "mb", size + 1):.0f}" height="1.5" fill="{theme["muted"]}" '
        f'class="growx" style="animation-delay:{t + .1:.2f}s;animation-duration:.4s"/>'
    )
    key_w = max(text_width(k + ":", "mb", size) for k, _ in info) + 12
    for i, (key, value) in enumerate(info):
        ly = iy + 34 + i * lh
        delay = t + .25 + i * .12
        max_w = W - ix - key_w - 26
        value_size = fit_size(value, "m", max_w, size, minimum=12)
        shown = value
        while text_width(shown, "m", value_size) > max_w and len(shown) > 4:
            shown = shown[:-2].rstrip(" ,·") + "…"
        out.append(
            f'<g class="fade" style="animation-delay:{delay:.2f}s;animation-duration:.3s">'
            f'<text x="{ix}" y="{ly}" class="mb" font-size="{size}" fill="{theme["cyan"]}">{esc(key)}'
            f'<tspan fill="{theme["muted"]}">:</tspan></text>'
            f'<text x="{ix + key_w:.0f}" y="{ly}" class="m" font-size="{value_size}" fill="{theme["text"]}">{esc(shown)}</text></g>'
        )
    # colour blocks
    by = iy + 34 + len(info) * lh - 6
    palette = [theme["heat"][1], theme["red"], theme["green"], theme["amber"], theme["violet"], theme["pink"], theme["cyan"], theme["text"]]
    for i, color in enumerate(palette):
        out.append(
            f'<rect x="{ix + i * 26}" y="{by}" width="24" height="12" rx="2" fill="{color}" class="pop" '
            f'style="animation-delay:{t + .3 + len(info) * .12 + i * .05:.2f}s"/>'
        )

    # final prompt with idle caret
    fy = H - 22
    end = t + .6 + len(info) * .12 + .5
    out.append(
        f'<text x="{x0}" y="{fy}" class="mb fade" font-size="{size}" style="animation-delay:{end:.2f}s">'
        f'<tspan fill="{theme["green"]}">{esc(prompt)}</tspan><tspan fill="{theme["muted"]}">:</tspan>'
        f'<tspan fill="{theme["cyan"]}">~</tspan><tspan fill="{theme["muted"]}">$</tspan></text>'
        f'<rect x="{x0 + pw:.1f}" y="{fy - size + 1}" width="{size * .6:.1f}" height="{size + 3}" fill="{theme["pink"]}" '
        f'style="animation:pre {end:.2f}s linear backwards,blink 1.05s steps(1) {end:.2f}s infinite"/>'
    )

    css = TYPED_CSS + "@keyframes beacon{50%{opacity:.15}}"
    return document(W, H, "".join(out), theme, css=css, title=f"About {cfg.name}")


def _mix(a: str, b: str, t: float) -> str:
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))
