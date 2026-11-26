"""Every image the README uses, in README order."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterator

from ..config import Config
from ..model import Data


@dataclass
class Card:
    name: str
    func: Callable
    kind: str = "svg"  # svg | gif | multi
    wants_timer: bool = False  # receives `started` (monotonic start of the build)

    def render(self, cfg: Config, data: Data, theme: dict, started: float = 0.0) -> Iterator[tuple[str, str | bytes]]:
        suffix = theme["name"]
        if self.kind == "multi":
            # func yields (stem, svg) for several images (buttons, project cards)
            for stem, svg in self.func(cfg, data, theme):
                yield f"{stem}-{suffix}.svg", svg
        elif self.kind == "gif":
            yield f"{self.name}-{suffix}.gif", self.func(cfg, data, theme)
        elif self.wants_timer:
            yield f"{self.name}-{suffix}.svg", self.func(cfg, data, theme, started=started)
        else:
            yield f"{self.name}-{suffix}.svg", self.func(cfg, data, theme)


def _cards() -> list[Card]:
    from ..gif import city
    from . import (about, achievements, buttons, calendar, clock, departures, footer, hero, languages, nightly,
                   projects, pulse, quote, stack, stats_card)

    return [
        Card("hero", hero.render),
        Card("buttons", buttons.render, kind="multi"),
        Card("about", about.render),
        Card("stats", stats_card.render),
        Card("city", city.render, kind="gif"),
        Card("calendar", calendar.render),
        Card("pulse", pulse.render),
        Card("languages", languages.render),
        Card("clock", clock.render),
        Card("departures", departures.render),
        Card("projects", projects.render, kind="multi"),
        Card("stack", stack.render),
        Card("achievements", achievements.render),
        Card("quote", quote.render),
        Card("footer", footer.render),
        # Last, so its "rendered in Xs" covers the whole build.
        Card("nightly", nightly.render, wants_timer=True),
    ]


CARDS = _cards()
