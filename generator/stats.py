"""Derived numbers: streaks, rhythms and achievements."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from .model import Data, Day


def current_streak(history: list[Day]) -> int:
    """Consecutive active days ending today — or yesterday, since the build runs at night."""
    days = list(history)
    if days and days[-1].count == 0:
        days = days[:-1]
    streak = 0
    for day in reversed(days):
        if day.count == 0:
            break
        streak += 1
    return streak


def longest_streak(history: list[Day]) -> int:
    best = run = 0
    for day in history:
        run = run + 1 if day.count else 0
        best = max(best, run)
    return best


def best_day(days: list[Day]) -> Day | None:
    active = [d for d in days if d.count]
    return max(active, key=lambda d: (d.count, d.date)) if active else None


def last_year(data: Data) -> list[Day]:
    today = data.generated_at.date()
    return [d for d in data.calendar if (today - d.date).days < 365]


def weekly(days: list[Day], weeks: int) -> list[int]:
    """Totals of the last `weeks` 7-day windows, oldest first."""
    sums = []
    for w in range(weeks, 0, -1):
        window = days[max(0, len(days) - w * 7): len(days) - (w - 1) * 7]
        sums.append(sum(d.count for d in window))
    return sums


def hours(data: Data) -> list[int]:
    buckets = [0] * 24
    for stamp in data.commit_times:
        buckets[stamp.hour] += 1
    return buckets


def weekdays(data: Data) -> list[int]:
    """Mon..Sun. Commit timestamps if we have them, else calendar days."""
    buckets = [0] * 7
    if data.commit_times:
        for stamp in data.commit_times:
            buckets[stamp.weekday()] += 1
    else:
        for day in last_year(data):
            buckets[day.date.weekday()] += day.count
    return buckets


def chronotype(data: Data) -> tuple[str, int]:
    """('NIGHT OWL' | 'EARLY BIRD' | 'DAY WALKER' | 'NO DATA', peak hour)."""
    h = hours(data)
    total = sum(h)
    if not total:
        return "NO DATA YET", data.generated_at.hour
    peak = max(range(24), key=lambda i: h[i])
    night = sum(h[i] for i in (21, 22, 23, 0, 1, 2, 3)) / total
    morning = sum(h[i] for i in (5, 6, 7, 8)) / total
    if night >= 0.25:
        return "NIGHT OWL", peak
    if morning >= 0.2:
        return "EARLY BIRD", peak
    return "DAY WALKER", peak


def years_on_github(data: Data) -> float:
    return (data.generated_at - data.created_at).days / 365.25


@dataclass
class Achievement:
    key: str
    title: str
    icon: str
    value: int
    tiers: tuple[int, ...]
    unit: str

    @property
    def tier(self) -> int:
        return sum(1 for t in self.tiers if self.value >= t)

    @property
    def unlocked(self) -> bool:
        return self.tier > 0

    @property
    def next_goal(self) -> int | None:
        return next((t for t in self.tiers if self.value < t), None)

    @property
    def progress(self) -> float:
        goal = self.next_goal
        if goal is None:
            return 1.0
        floor = self.tiers[self.tier - 1] if self.tier else 0
        return max(0.0, min(1.0, (self.value - floor) / (goal - floor)))


def achievements(data: Data) -> list[Achievement]:
    year = last_year(data)
    h = hours(data)
    total_commits = sum(h) or 1
    night_pct = round(100 * sum(h[i] for i in (21, 22, 23, 0, 1, 2, 3)) / total_commits) if sum(h) else 0
    weekend_days = sum(1 for d in year if d.count and d.date.weekday() >= 5)
    return [
        Achievement("streak", "ON FIRE", "flame", longest_streak(data.history), (3, 7, 30, 100), "DAY STREAK"),
        Achievement("centurion", "CENTURION", "bolt", data.totals.contributions_year, (50, 100, 500, 1000), "CONTRIB / YR"),
        Achievement("marathon", "MARATHON", "calendar", sum(1 for d in year if d.count), (10, 50, 120, 250), "ACTIVE DAYS"),
        Achievement("polyglot", "POLYGLOT", "globe", len(data.languages), (2, 4, 6, 10), "LANGUAGES"),
        Achievement("pilot", "PR PILOT", "merge", data.totals.prs, (1, 10, 50, 200), "PULL REQUESTS"),
        Achievement("reviewer", "CODE CRITIC", "eye", data.totals.reviews, (1, 10, 50, 200), "REVIEWS"),
        Achievement("owl", "NIGHT OWL", "moon", night_pct, (10, 20, 30, 45), "% AFTER 21:00"),
        Achievement("weekend", "WEEKENDER", "coffee", weekend_days, (2, 10, 25, 50), "WEEKEND DAYS"),
        Achievement("builder", "ARCHITECT", "cube", data.public_repos, (1, 5, 15, 30), "PUBLIC REPOS"),
        Achievement("veteran", "VETERAN", "shield", int(years_on_github(data) * 12), (6, 12, 36, 60), "MONTHS HERE"),
    ]


def days_since(data: Data, start) -> int:
    return (data.generated_at.date() - start).days


def coding_uptime(data: Data, start) -> str:
    total = max(0, days_since(data, start))
    years, days = divmod(total, 365)
    parts = []
    if years:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    parts.append(f"{days} day{'s' if days != 1 else ''}")
    return ", ".join(parts)


def recent_window(data: Data, days: int) -> list[Day]:
    cutoff = data.generated_at.date() - timedelta(days=days - 1)
    return [d for d in data.calendar if d.date >= cutoff]
