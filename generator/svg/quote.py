"""Quote of the night: a different curated quote every day, typed out."""
from __future__ import annotations

import functools

import yaml

from ..config import ASSETS, Config
from ..model import Data
from .core import HALF, TYPED_CSS, document, esc, label, typed, wrap

H = 260


@functools.lru_cache(maxsize=1)
def quotes() -> list[dict]:
    return yaml.safe_load((ASSETS / "quotes.yml").read_text(encoding="utf-8"))


def pick(data: Data) -> dict:
    items = quotes()
    return items[data.generated_at.date().toordinal() % len(items)]


def render(cfg: Config, data: Data, theme: dict) -> str:
    quote = pick(data)
    bg = theme["panel"]
    out = [
        f'<rect x=".5" y=".5" width="{HALF - 1}" height="{H - 1}" rx="18" fill="{bg}" stroke="{theme["line"]}"/>',
        f'<rect x="18" y="0" width="{HALF - 36}" height="1.5" fill="{theme["violet"]}" opacity=".8"/>',
        label(22, 34, "Quote of the night", theme, color=theme["violet"]),
        f'<text x="{HALF - 26}" y="{H - 18}" text-anchor="end" class="o" font-size="120" fill="{theme["violet"]}" '
        f'opacity=".08">&#8221;</text>',
        f'<text x="20" y="96" class="o fade" font-size="64" fill="{theme["violet"]}" filter="url(#glow)" '
        f'style="animation-delay:.2s">&#8220;</text>',
    ]
    size = 14.5
    lines = wrap(quote["text"], "m", size, HALF - 96, 6)
    while len(lines) > 5 and size > 12:
        size -= .5
        lines = wrap(quote["text"], "m", size, HALF - 96, 6)
    lh = size * 1.55
    block = lh * len(lines)
    total = block + 22  # text + author line
    top = 62 + max(0, (H - 62 - 26 - total) / 2) + size * .9
    t = .5
    for i, line in enumerate(lines):
        last = i == len(lines) - 1
        markup, end = typed(62, top + i * lh, line, cls="m", size=size, fill=theme["text"], cover=bg, delay=t, cps=34,
                            cursor=theme["pink"], cursor_until=None if last else t + len(line) / 34 + .02)
        out.append(markup)
        t = end + .05
    author = f"— {quote['by']}"
    out.append(
        f'<text x="62" y="{top + block + 10:.0f}" class="mb up" font-size="11.5" letter-spacing="1" fill="{theme["violet"]}" '
        f'style="animation-delay:{t + .2:.2f}s">{esc(author)}</text>'
    )
    return document(HALF, H, "".join(out), theme, css=TYPED_CSS, title=f"“{quote['text']}” {author}")
