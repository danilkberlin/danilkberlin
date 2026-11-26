"""Social buttons: 200×52 neon pills, one image per link (each wrapped in <a>)."""
from __future__ import annotations

from typing import Iterator

from ..config import ASSETS, Config
from ..model import Data
from .core import document, esc, fit_size
from .stack import icon_path

BW, BH = 200, 52


def _globe(x: float, y: float, color: str) -> str:
    return (
        f'<g transform="translate({x} {y})" fill="none" stroke="{color}" stroke-width="1.6">'
        f'<circle cx="10" cy="10" r="9"/><ellipse cx="10" cy="10" rx="4" ry="9"/>'
        f'<path d="M1,10 H19 M2.6,5.2 H17.4 M2.6,14.8 H17.4"/></g>'
    )


def _icon(link_id: str, x: float, y: float, color: str) -> str:
    if (ASSETS / "icons" / f"{link_id}.svg").exists():
        return f'<path d="{icon_path(link_id)}" transform="translate({x} {y}) scale({20 / 24:.4f})" fill="{color}"/>'
    return _globe(x, y, color)


def _button(label_text: str, link_id: str, index: int, theme: dict) -> str:
    dark = theme["name"] == "dark"
    accent = [theme["cyan"], theme["violet"], theme["pink"], theme["amber"]][index % 4]
    top, bottom = theme["button"]
    text = label_text.upper()
    size = fit_size(text, "o7", BW - 54 - 36, 13, spacing=2.2, minimum=9)
    delay = index * 1.35
    defs = (
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/>'
        f'<stop offset="1" stop-color="{bottom}"/></linearGradient>'
        f'<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="#fff" stop-opacity="{.22 if dark else .85}"/>'
        f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="pill"><rect x="1" y="1" width="{BW - 2}" height="{BH - 2}" rx="{(BH - 2) / 2}"/></clipPath>'
    )
    body = (
        # soft halo that breathes
        f'<rect x="3" y="3" width="{BW - 6}" height="{BH - 6}" rx="{(BH - 6) / 2}" fill="none" stroke="{accent}" '
        f'stroke-width="2.5" filter="url(#glow2)" class="halo" style="animation-delay:{delay:.2f}s"/>'
        f'<rect x="1" y="1" width="{BW - 2}" height="{BH - 2}" rx="{(BH - 2) / 2}" fill="url(#bg)" '
        f'stroke="{accent}" stroke-opacity=".85" stroke-width="1.2"/>'
        f'<g clip-path="url(#pill)"><rect x="-90" y="-10" width="70" height="{BH + 20}" fill="url(#shine)" '
        f'transform="skewX(-20)" class="shine" style="animation-delay:{1.2 + delay:.2f}s"/></g>'
        f'<g class="pop" style="animation-delay:{.1 + index * .12:.2f}s">{_icon(link_id, 22, 16, accent)}</g>'
        f'<text x="54" y="{BH / 2 + size * .38:.1f}" class="o7 up" font-size="{size}" letter-spacing="2.2" '
        f'fill="{theme["text"]}" style="animation-delay:{.2 + index * .12:.2f}s">{esc(text)}</text>'
        f'<path d="M{BW - 32},{BH / 2 + 4} L{BW - 24},{BH / 2 - 4} M{BW - 30},{BH / 2 - 4} H{BW - 24} V{BH / 2 + 2}" '
        f'fill="none" stroke="{accent}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
        f'class="nudge" style="animation-delay:{1.2 + delay:.2f}s"/>'
    )
    css = """
    .halo{opacity:.25;animation:halo 5.4s ease-in-out infinite}
    @keyframes halo{0%,100%{opacity:.18}50%{opacity:.75}}
    .shine{animation:shine 5.4s ease-in-out infinite}
    @keyframes shine{0%{transform:skewX(-20deg) translateX(0)}35%,100%{transform:skewX(-20deg) translateX(330px)}}
    .nudge{animation:nudge 5.4s ease-in-out infinite}
    @keyframes nudge{0%,30%,100%{transform:translate(0,0)}15%{transform:translate(2px,-2px)}}
    """
    return document(BW, BH, body, theme, css=css, defs=defs, title=label_text)


def render(cfg: Config, data: Data, theme: dict) -> Iterator[tuple[str, str]]:
    for index, link in enumerate(cfg.links):
        yield f"btn-{link.id}", _button(link.label, link.id, index, theme)
