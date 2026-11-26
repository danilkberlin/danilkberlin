"""Footer: neon waves rolling under a sign-off and the last-build stamp."""
from __future__ import annotations

import math

from ..config import Config
from ..model import Data
from .core import W, document, esc, fit_size

H = 140


def _wave(amplitude: float, wavelength: float, y: float, phase: float) -> str:
    """A sine path two screens wide so translating by one wavelength loops seamlessly."""
    points = []
    x = -wavelength
    while x <= W + wavelength * 2:
        points.append(f"{x:.1f},{y + amplitude * math.sin(2 * math.pi * x / wavelength + phase):.1f}")
        x += 6
    return "M" + " L".join(points)


def render(cfg: Config, data: Data, theme: dict) -> str:
    out = [
        f'<defs><linearGradient id="fg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{theme["cyan"]}"/>'
        f'<stop offset=".5" stop-color="{theme["violet"]}"/><stop offset="1" stop-color="{theme["pink"]}"/></linearGradient>'
        f'<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".15" stop-color="#fff"/><stop offset=".85" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<mask id="edges"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask></defs>'
    ]
    waves = []
    specs = [(10, 210, 104, 0, theme["cyan"], 7, .55), (7, 160, 112, 1.3, theme["pink"], 5, .5), (5, 120, 120, 2.2, theme["violet"], 4, .45)]
    for amp, length, y, phase, color, speed, opacity in specs:
        waves.append(
            f'<g style="animation:wave{int(length)} {speed}s linear infinite">'
            f'<path d="{_wave(amp, length, y, phase)}" fill="none" stroke="{color}" stroke-width="1.6" stroke-opacity="{opacity}" '
            f'filter="url(#glow)"/></g>'
        )
    out.append(f'<g mask="url(#edges)">{"".join(waves)}</g>')

    message = "THANKS FOR STOPPING BY"
    size = fit_size(message, "o", 560, 22, spacing=6)
    out.append(
        f'<text x="{W / 2}" y="52" text-anchor="middle" class="o up" font-size="{size}" letter-spacing="6" fill="url(#fg)" '
        f'filter="url(#glow)">{esc(message)}</text>'
    )
    when = data.generated_at
    stamp = f"REBUILT NIGHTLY BY GITHUB ACTIONS · LAST BUILD {when:%d.%m.%Y %H:%M} {when.tzname() or ''}"
    out.append(
        f'<text x="{W / 2}" y="78" text-anchor="middle" class="mb fade" font-size="10.5" letter-spacing="2" '
        f'fill="{theme["muted"]}" style="animation-delay:.6s">{esc(stamp)}</text>'
    )
    css = "".join(
        f"@keyframes wave{int(length)}{{to{{transform:translateX(-{length}px)}}}}" for _, length, *_ in specs
    )
    return document(W, H, "".join(out), theme, css=css, title="Thanks for stopping by")
