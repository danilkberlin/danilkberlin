"""Turns raw fetcher output into the normalised `Data` every renderer consumes."""
from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .config import Config
from .data import fixtures, github, weather
from .data.astro import moon
from .model import Data, Day

log = logging.getLogger(__name__)

CALENDAR_WEEKS = 53


def calendar_start(today: date) -> date:
    """Monday of the week 52 weeks before the current one (53 columns, Monday-first)."""
    return today - timedelta(days=today.weekday()) - timedelta(weeks=CALENDAR_WEEKS - 1)


def build(cfg: Config, mode: str = "live", now: datetime | None = None) -> Data:
    zone = ZoneInfo(cfg.timezone)
    now = (now or datetime.now(zone)).astimezone(zone)

    if mode == "demo":
        raw = fixtures.demo(cfg, now)
    elif mode == "empty":
        raw = fixtures.empty(cfg, now)
    else:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if token:
            log.info("fetching via GraphQL")
            raw = github.fetch_graphql(cfg.login, token, cfg.featured, cfg.timezone)
        else:
            log.info("no token: using public endpoints")
            raw = github.fetch_public(cfg.login, cfg.featured, cfg.timezone)
        loc = cfg.location
        raw["weather"] = (
            weather.fetch(loc["latitude"], loc["longitude"], cfg.timezone) if "latitude" in loc else None
        )

    today = now.date()
    days: dict[date, Day] = raw["days"]
    start = calendar_start(today)
    calendar = [days.get(start + timedelta(n)) or Day(start + timedelta(n), 0) for n in range((today - start).days + 1)]
    first = raw["created_at"].astimezone(zone).date()
    history = [days.get(first + timedelta(n)) or Day(first + timedelta(n), 0) for n in range((today - first).days + 1)]

    totals = raw["totals"]
    totals.contributions_year = sum(d.count for d in calendar if (today - d.date).days < 365)
    totals.contributions_all = sum(d.count for d in history)
    if not totals.commits:
        totals.commits = len(raw["commit_times"])

    return Data(
        login=cfg.login,
        name=cfg.name,
        created_at=raw["created_at"],
        followers=raw["followers"],
        public_repos=raw["public_repos"],
        stars=raw["stars"],
        totals=totals,
        calendar=calendar,
        history=history,
        languages=raw["languages"],
        commit_times=raw["commit_times"],
        events=raw["events"],
        repos=raw["repos"],
        weather=raw.get("weather"),
        moon=moon(now),
        generated_at=now,
        run_number=int(os.environ.get("GITHUB_RUN_NUMBER", "0") or 0),
        source=raw["source"],
    )
