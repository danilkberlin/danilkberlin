"""Deterministic datasets for tests and offline previews."""
from __future__ import annotations

import math
import random
from datetime import date, datetime, timedelta

from ..config import Config
from ..model import Day, Event, Repo, Totals, Weather


def _level(count: int, top: int) -> int:
    if count == 0:
        return 0
    return min(4, 1 + int(3 * count / max(top, 1)))


def demo(cfg: Config, now: datetime) -> dict:
    rng = random.Random(42)
    created = datetime(2023, 11, 13, 10, 24, tzinfo=now.tzinfo)
    today = now.date()
    counts: dict[date, int] = {}
    day = created.date()
    while day <= today:
        ramp = 0.35 + 0.65 * min(1.0, (day - created.date()).days / 700)
        weekday_boost = 1.0 if day.weekday() < 5 else 0.45
        season = 0.75 + 0.25 * math.sin(day.toordinal() / 58)
        p_active = 0.62 * ramp * weekday_boost * season
        counts[day] = int(rng.expovariate(1 / (4.5 * ramp)) + 1) if rng.random() < p_active else 0
        day += timedelta(days=1)
    for offset in range(9):  # an ongoing streak
        counts[today - timedelta(days=offset)] = max(counts.get(today - timedelta(days=offset), 0), 2 + offset % 4)
    top = max(counts.values())
    days = {d: Day(d, c, _level(c, top)) for d, c in counts.items()}

    commit_times = []
    for _ in range(640):
        hour = rng.choices(range(24), weights=[3, 2, 1, .4, .2, .2, .4, 1, 3, 6, 7, 7, 5, 6, 7, 7, 6, 5, 4, 5, 7, 8, 7, 5])[0]
        stamp = now - timedelta(days=rng.randrange(0, 365))
        commit_times.append(stamp.replace(hour=hour, minute=rng.randrange(60)))

    descriptions = {
        "danylo-kravets": "Personal portfolio — vanilla HTML/CSS/JS SPA with hash router, i18n and dark mode.",
        "monopoly": "The classic property-trading board game, implemented in PHP with a clean domain model.",
        "dolphin": "Shell tooling to bootstrap and tame local dev environments.",
    }
    langs = {"danylo-kravets": ("JavaScript", "#f1e05a"), "monopoly": ("PHP", "#4F5D95"), "dolphin": ("Shell", "#89e051")}
    repos = {}
    for index, name in enumerate(cfg.featured):
        lang, color = langs.get(name, ("PHP", "#4F5D95"))
        repos[name] = Repo(
            name=name,
            description=descriptions.get(name, "A project worth a look."),
            url=f"https://github.com/{cfg.login}/{name}",
            language=lang,
            language_color=color,
            stars=[12, 5, 3][index % 3],
            forks=[2, 1, 0][index % 3],
            pushed_at=now - timedelta(days=[1, 9, 40][index % 3], hours=3),
            weekly_commits=[max(0, int(rng.gauss(4, 3) * (0.3 + w / 26))) for w in range(26)],
        )

    kinds = [("PUSH", "3 COMMITS"), ("MERGE", "#42"), ("PUSH", "1 COMMIT"), ("PR", "#41"), ("RELEASE", "v1.2.0"),
             ("NEW", "BRANCH"), ("STAR", ""), ("PUSH", "7 COMMITS"), ("ISSUE", "#17")]
    names = cfg.featured or ["profile"]
    events = [
        Event(kind, names[i % len(names)], now - timedelta(hours=5 + i * 19), detail)
        for i, (kind, detail) in enumerate(kinds)
    ]
    languages = [("PHP", 512_000, "#4F5D95"), ("JavaScript", 188_000, "#f1e05a"), ("Python", 96_000, "#3572A5"),
                 ("Java", 61_000, "#b07219"), ("Twig", 34_000, "#c1d026"), ("Shell", 18_000, "#89e051")]
    return {
        "name": cfg.name,
        "created_at": created,
        "followers": 48,
        "public_repos": 17,
        "stars": 64,
        "totals": Totals(commits=1742, prs=128, issues=37, reviews=212),
        "days": days,
        "languages": languages,
        "commit_times": commit_times,
        "repos": repos,
        "events": events,
        "source": "demo",
        "weather": Weather(temp_c=3.4, code=63, kind="rain", wind_kmh=14,
                           sunrise=now.replace(hour=7, minute=48) + timedelta(days=1),
                           sunset=now.replace(hour=15, minute=56)),
    }


def empty(cfg: Config, now: datetime) -> dict:
    """A brand-new account: every card must still render nicely."""
    created = now - timedelta(days=3)
    return {
        "name": cfg.name,
        "created_at": created,
        "followers": 0,
        "public_repos": 0,
        "stars": 0,
        "totals": Totals(),
        "days": {},
        "languages": [],
        "commit_times": [],
        "repos": {},
        "events": [],
        "source": "demo",
        "weather": None,
    }

