"""Featured repository cards (272×200, three per row), one image per repo.

A light segment travels around each card's border. The 26-week commit
sparkline draws itself on load.
"""
from __future__ import annotations

import math
from typing import Iterator

from ..config import Config
from ..model import Data, Repo
from .core import ago, document, esc, fit_size, panel, smooth_path, text_width, wrap

CW, CH = 272, 200
PAD = 20


def _round_rect(x: float, y: float, w: float, h: float, r: float) -> str:
    """Clockwise rounded-rect path starting just after the top-left corner."""
    return (
        f"M{x + r},{y} H{x + w - r} A{r},{r} 0 0 1 {x + w},{y + r} V{y + h - r} "
        f"A{r},{r} 0 0 1 {x + w - r},{y + h} H{x + r} A{r},{r} 0 0 1 {x},{y + h - r} "
        f"V{y + r} A{r},{r} 0 0 1 {x + r},{y}Z"
    )


def _star(cx: float, cy: float, r: float) -> str:
    points = []
    for i in range(10):
        radius = r if i % 2 == 0 else r * .45
        angle = math.radians(-90 + i * 36)
        points.append(f"{cx + radius * math.cos(angle):.2f},{cy + radius * math.sin(angle):.2f}")
    return "M" + " L".join(points) + "Z"


def _fork_icon(x: float, y: float, color: str) -> str:
    return (
        f'<g transform="translate({x} {y})" fill="none" stroke="{color}" stroke-width="1.3" stroke-linecap="round">'
        f'<circle cx="-3" cy="-4" r="1.6"/><circle cx="3" cy="-4" r="1.6"/><circle cx="0" cy="4.2" r="1.6"/>'
        f'<path d="M-3,-2.4 V-1.4 Q-3,.6 0,.6 Q3,.6 3,-1.4 V-2.4 M0,.6 V2.6"/></g>'
    )


def _repo_icon(x: float, y: float, color: str) -> str:
    """A small 'book' glyph in the spirit of a repository icon."""
    return (
        f'<g transform="translate({x} {y})" fill="none" stroke="{color}" stroke-width="1.5" stroke-linejoin="round">'
        f'<path d="M2,1 H12 V13 H4 Q2,13 2,11 Z"/><path d="M2,11 Q2,9.5 4,9.5 H12"/>'
        f'<path d="M5,13 V16 L6.5,14.8 L8,16 V13" fill="{color}" stroke="none"/></g>'
    )


def _sparkline(weekly: list[int], color: str, theme: dict, top: float, bottom: float) -> str:
    left, right = PAD, CW - PAD
    values = weekly[-26:] if weekly else []
    if not values or not any(values):
        return (
            f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="{theme["faint"]}" '
            f'stroke-dasharray="3 4" class="fade" style="animation-delay:.6s"/>'
        )
    peak = max(values)
    step = (right - left) / (len(values) - 1)
    points = [(left + i * step, bottom - (v / peak) * (bottom - top)) for i, v in enumerate(values)]
    line = smooth_path(points)
    area = f"{line} L{right},{bottom + 2} L{left},{bottom + 2}Z"
    lx, ly = points[-1]
    return (
        f'<defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{color}" stop-opacity=".35"/>'
        f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient></defs>'
        f'<path d="{area}" fill="url(#area)" class="fade" style="animation-delay:1.5s;animation-duration:1.2s"/>'
        f'<path d="{line}" pathLength="1" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round" class="draw" style="animation-delay:.6s" filter="url(#glow)"/>'
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="3" fill="{color}" class="pop" style="animation-delay:2.4s"/>'
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="3" fill="none" stroke="{color}" class="ping"/>'
    )


def _card(cfg: Config, data: Data, theme: dict, name: str, index: int) -> str:
    repo: Repo | None = data.repos.get(name)
    accent = [theme["cyan"], theme["violet"], theme["pink"]][index % 3]
    second = [theme["pink"], theme["cyan"], theme["violet"]][index % 3]
    dash = "—"

    border_path = _round_rect(.75, .75, CW - 1.5, CH - 1.5, 15.25)
    border = (
        f'<path d="{border_path}" pathLength="1" fill="none" stroke="{accent}" stroke-width="1.8" '
        f'stroke-linecap="round" stroke-dasharray=".16 .84" class="run" filter="url(#glow)" '
        f'style="animation-delay:-{index * 2.3:.1f}s"/>'
        f'<path d="{border_path}" pathLength="1" fill="none" stroke="{second}" stroke-width="1.4" '
        f'stroke-linecap="round" stroke-dasharray=".06 .94" class="run" '
        f'style="animation-delay:-{index * 2.3 + 4.4:.1f}s"/>'
    )

    title_size = fit_size(name, "o7", CW - 44 - PAD, 15, spacing=.5, minimum=10)
    header = (
        _repo_icon(PAD - 1, 28, accent)
        + f'<text x="44" y="29" class="m" font-size="9.5" letter-spacing=".6" fill="{theme["muted"]}">{esc(cfg.login)} /</text>'
        + f'<text x="44" y="47" class="o7" font-size="{title_size}" letter-spacing=".5" fill="{theme["text"]}">{esc(name)}</text>'
        + f'<text x="{CW - PAD}" y="29" text-anchor="end" class="mb" font-size="10" letter-spacing="1" fill="{accent}">'
        f"#{index + 1:02d}</text>"
    )

    description = (repo.description or "No description yet.") if repo else "Details unavailable right now — check back after the next nightly build."
    lines = wrap(description, "m", 11, CW - 2 * PAD, 3)
    desc = "".join(
        f'<text x="{PAD}" y="{76 + i * 16}" class="m" font-size="11" fill="{theme["muted"]}">{esc(line)}</text>'
        for i, line in enumerate(lines)
    )

    weekly = repo.weekly_commits if repo else []
    total = sum(weekly)
    updated = ago((data.generated_at - repo.pushed_at).total_seconds()) if repo and repo.pushed_at else dash
    meta = (
        f'<text x="{PAD}" y="{128}" class="mb" font-size="8.5" letter-spacing="1.2" fill="{theme["muted"]}">'
        f'{total if repo else dash} COMMIT{"" if repo and total == 1 else "S"} · 26 WKS</text>'
        f'<text x="{CW - PAD}" y="{128}" text-anchor="end" class="mb" font-size="8.5" letter-spacing="1.2" fill="{accent}">'
        f"UPDATED {esc(updated.upper())}</text>"
    )
    spark = _sparkline(weekly, accent, theme, 136, 160)

    lang = (repo.language if repo else None) or dash
    lang_color = (repo.language_color if repo and repo.language else None) or theme["faint"]
    stars = str(repo.stars) if repo else dash
    forks = str(repo.forks) if repo else dash
    fork_w = text_width(forks, "mb", 10.5)
    star_w = text_width(stars, "mb", 10.5)
    fork_text_x = CW - PAD
    fork_icon_x = fork_text_x - fork_w - 9
    star_text_x = fork_icon_x - 13
    star_icon_x = star_text_x - star_w - 9
    footer = (
        f'<line x1="{PAD}" y1="171" x2="{CW - PAD}" y2="171" stroke="{theme["line"]}"/>'
        f'<circle cx="{PAD + 5}" cy="185" r="5" fill="{lang_color}"/>'
        f'<text x="{PAD + 15}" y="189" class="m" font-size="10.5" fill="{theme["text"]}">{esc(lang)}</text>'
        f'<path d="{_star(star_icon_x, 184.5, 5.6)}" fill="{theme["amber"]}"/>'
        f'<text x="{star_text_x}" y="189" text-anchor="end" class="mb" font-size="10.5" fill="{theme["text"]}">{esc(stars)}</text>'
        + _fork_icon(fork_icon_x, 185, theme["muted"])
        + f'<text x="{fork_text_x}" y="189" text-anchor="end" class="mb" font-size="10.5" fill="{theme["text"]}">{esc(forks)}</text>'
    )

    css = """
    .run{animation:run 7s linear infinite}
    @keyframes run{to{stroke-dashoffset:-1}}
    .ping{transform-box:fill-box;transform-origin:center;animation:ping 2.2s ease-out 2.8s infinite;opacity:0}
    @keyframes ping{0%{opacity:.9;transform:scale(1)}100%{opacity:0;transform:scale(3.2)}}
    """
    body = (
        panel(CW, CH, theme, accent=accent, radius=16)
        + border
        + f'<g class="up" style="animation-delay:.1s">{header}</g>'
        + f'<g class="fade" style="animation-delay:.35s">{desc}</g>'
        + f'<g class="fade" style="animation-delay:.5s">{meta}</g>'
        + spark
        + f'<g class="up" style="animation-delay:.7s">{footer}</g>'
    )
    title = f"{name}: {repo.description}" if repo and repo.description else name
    return document(CW, CH, body, theme, css=css, title=title)


def render(cfg: Config, data: Data, theme: dict) -> Iterator[tuple[str, str]]:
    for index, name in enumerate(cfg.featured):
        yield f"project-{name}", _card(cfg, data, theme, name, index)
