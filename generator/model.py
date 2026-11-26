"""Plain data containers shared by fetchers, stats and renderers."""
from __future__ import annotations

from dataclasses import dataclass, field
import datetime as dt


@dataclass
class Day:
    date: dt.date
    count: int
    level: int = 0  # 0..4, GitHub's quartile bucket


@dataclass
class Repo:
    name: str
    description: str = ""
    url: str = ""
    language: str | None = None
    language_color: str | None = None
    stars: int = 0
    forks: int = 0
    pushed_at: dt.datetime | None = None
    private: bool = False
    languages: dict[str, int] = field(default_factory=dict)
    # commits per week for the last 26 weeks, oldest first
    weekly_commits: list[int] = field(default_factory=list)


@dataclass
class Event:
    kind: str  # PUSH, PR, MERGE, NEW, RELEASE, ISSUE, STAR, FORK, REVIEW
    repo: str
    at: dt.datetime
    detail: str = ""


@dataclass
class Weather:
    temp_c: float
    code: int
    kind: str  # clear, cloudy, fog, drizzle, rain, snow, storm
    wind_kmh: float = 0.0
    is_day: bool = False
    sunrise: dt.datetime | None = None
    sunset: dt.datetime | None = None


@dataclass
class Moon:
    phase: float  # 0 = new, 0.5 = full, 1 = new
    illumination: float  # 0..1
    name: str
    age_days: float


@dataclass
class Totals:
    commits: int = 0
    prs: int = 0
    issues: int = 0
    reviews: int = 0
    contributions_year: int = 0
    contributions_all: int = 0
    private_contributions: int = 0


@dataclass
class Data:
    login: str
    name: str
    created_at: dt.datetime
    followers: int
    public_repos: int
    stars: int
    totals: Totals
    calendar: list[Day]  # last 371 days (53 full weeks), oldest first, ending today
    history: list[Day]  # every day since the account was created
    languages: list[tuple[str, int, str]]  # (name, bytes, color), largest first
    commit_times: list[dt.datetime]  # local timezone
    events: list[Event]
    repos: dict[str, Repo]  # featured repos by name
    weather: Weather | None
    moon: Moon
    generated_at: dt.datetime  # local timezone
    run_number: int = 0
    source: str = "demo"  # graphql | public | demo
