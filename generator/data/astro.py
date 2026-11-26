"""Moon phase without any API: mean synodic month from a known new moon."""
from __future__ import annotations

import math
from datetime import datetime, timezone

from ..model import Moon

SYNODIC_MONTH = 29.530588853
# New moon reference: 2000-01-06 18:14 UTC
_REFERENCE = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)

_NAMES = [
    (0.0339, "New Moon"),
    (0.2161, "Waxing Crescent"),
    (0.2839, "First Quarter"),
    (0.4661, "Waxing Gibbous"),
    (0.5339, "Full Moon"),
    (0.7161, "Waning Gibbous"),
    (0.7839, "Last Quarter"),
    (0.9661, "Waning Crescent"),
    (1.0001, "New Moon"),
]


def moon(at: datetime) -> Moon:
    days = (at.astimezone(timezone.utc) - _REFERENCE).total_seconds() / 86400
    phase = (days / SYNODIC_MONTH) % 1.0
    illumination = (1 - math.cos(2 * math.pi * phase)) / 2
    name = next(label for limit, label in _NAMES if phase < limit)
    return Moon(phase=phase, illumination=illumination, name=name, age_days=phase * SYNODIC_MONTH)


def moon_path(cx: float, cy: float, r: float, phase: float) -> str:
    """SVG path of the lit part of the moon (northern hemisphere view)."""
    # Terminator is a half-ellipse with rx = r*|cos(2πp)|.
    rx = abs(math.cos(2 * math.pi * phase)) * r
    waxing = phase < 0.5
    # Outer limb: right half when waxing, left half when waning.
    limb_sweep = 1 if waxing else 0
    # Terminator bulges toward the dark side for crescents, toward the lit side for gibbous.
    gibbous = 0.25 < phase < 0.75
    term_sweep = (1 if gibbous else 0) if waxing else (0 if gibbous else 1)
    top = f"{cx:.2f},{cy - r:.2f}"
    bottom = f"{cx:.2f},{cy + r:.2f}"
    return (
        f"M{top} A{r:.2f},{r:.2f} 0 0 {limb_sweep} {bottom} "
        f"A{rx:.2f},{r:.2f} 0 0 {term_sweep} {top}Z"
    )
