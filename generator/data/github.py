"""GitHub data: GraphQL when a token is available, public endpoints otherwise.

Only *public* repositories and events are ever named in the output. With a
personal access token, private activity still feeds the aggregate numbers
(contribution calendar, languages, commit hours) but never shows up by name.
"""
from __future__ import annotations

import html
import logging
import re
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote
from zoneinfo import ZoneInfo

from ..model import Day, Event, Repo, Totals
from .http import get, get_json, post_json

log = logging.getLogger(__name__)

API = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"
MAX_HISTORY_REPOS = 25

# Linguist colours for the public fallback path (GraphQL returns them itself).
LANGUAGE_COLORS = {
    "PHP": "#4F5D95", "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Python": "#3572A5",
    "Java": "#b07219", "Shell": "#89e051", "HTML": "#e34c26", "CSS": "#663399", "Blade": "#f7523f",
    "Twig": "#c1d026", "Go": "#00ADD8", "Rust": "#dea584", "Kotlin": "#A97BFF", "C#": "#178600",
    "C++": "#f34b7d", "C": "#555555", "Ruby": "#701516", "Vue": "#41b883", "Dockerfile": "#384d54",
    "Makefile": "#427819", "SCSS": "#c6538c", "Hack": "#878787", "Smarty": "#f0c040",
}


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


# ──────────────────────────────────────────────────────────────── GraphQL ───

_USER_QUERY = """
query($login: String!) {
  user(login: $login) {
    id name login createdAt
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name description url stargazerCount forkCount pushedAt isPrivate
        primaryLanguage { name color }
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}"""

_YEAR_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions totalPullRequestReviewContributions
      restrictedContributionsCount
      contributionCalendar {
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}"""

_HISTORY_QUERY = """
query($owner: String!, $name: String!, $uid: ID!, $since: GitTimestamp!) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef { target { ... on Commit {
      mine: history(first: 100, author: {id: $uid}) { nodes { authoredDate } }
      recent: history(first: 100, since: $since) { nodes { committedDate } }
    } } }
  }
}"""

_LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def _graphql(token: str, query: str, **variables):
    payload = post_json(GRAPHQL, {"query": query, "variables": variables}, token)
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    return payload["data"]


def fetch_graphql(login: str, token: str, featured: list[str], tz: str) -> dict:
    zone = ZoneInfo(tz)
    user = _graphql(token, _USER_QUERY, login=login)["user"]
    created = _parse_ts(user["createdAt"])
    now = datetime.now(timezone.utc)

    days: dict[date, Day] = {}
    totals = Totals(prs=user["pullRequests"]["totalCount"], issues=user["issues"]["totalCount"])
    for year in range(created.year, now.year + 1):
        start = max(datetime(year, 1, 1, tzinfo=timezone.utc), created)
        end = min(datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc), now)
        coll = _graphql(token, _YEAR_QUERY, login=login, **{"from": start.isoformat(), "to": end.isoformat()})
        coll = coll["user"]["contributionsCollection"]
        totals.commits += coll["totalCommitContributions"]
        totals.reviews += coll["totalPullRequestReviewContributions"]
        totals.private_contributions += coll["restrictedContributionsCount"]
        for week in coll["contributionCalendar"]["weeks"]:
            for d in week["contributionDays"]:
                day = date.fromisoformat(d["date"])
                days[day] = Day(day, d["contributionCount"], _LEVELS.get(d["contributionLevel"], 0))

    # The rolling-year calendar may straddle Jan 1st; fetch it as one window too so
    # the quartile levels match what GitHub shows on the profile. (The API rejects
    # windows longer than a year, so stay just inside it.)
    last_year = _graphql(
        token, _YEAR_QUERY, login=login,
        **{"from": (now - timedelta(days=364)).isoformat(), "to": now.isoformat()},
    )["user"]["contributionsCollection"]["contributionCalendar"]
    for week in last_year["weeks"]:
        for d in week["contributionDays"]:
            day = date.fromisoformat(d["date"])
            days[day] = Day(day, d["contributionCount"], _LEVELS.get(d["contributionLevel"], 0))

    nodes = user["repositories"]["nodes"]
    language_bytes: Counter[str] = Counter()
    colors: dict[str, str] = {}
    for node in nodes:
        for edge in node["languages"]["edges"]:
            language_bytes[edge["node"]["name"]] += edge["size"]
            colors[edge["node"]["name"]] = edge["node"]["color"] or "#8b93c7"

    since = (now - timedelta(weeks=26)).isoformat()
    commit_times: list[datetime] = []
    repos: dict[str, Repo] = {}
    for node in nodes[:MAX_HISTORY_REPOS]:
        try:
            repo_data = _graphql(token, _HISTORY_QUERY, owner=login, name=node["name"], uid=user["id"], since=since)
        except Exception as error:  # an empty repo has no default branch
            log.info("no history for %s: %s", node["name"], error)
            continue
        ref = (repo_data["repository"] or {}).get("defaultBranchRef")
        if not ref:
            continue
        commit_times += [_parse_ts(c["authoredDate"]).astimezone(zone) for c in ref["target"]["mine"]["nodes"]]
        if node["name"] in featured and not node["isPrivate"]:
            recent = [_parse_ts(c["committedDate"]) for c in ref["target"]["recent"]["nodes"]]
            repos[node["name"]] = _repo_from_node(node, _weekly(recent, now))
    for node in nodes:
        if node["name"] in featured and node["name"] not in repos and not node["isPrivate"]:
            repos[node["name"]] = _repo_from_node(node, [0] * 26)

    public = [n for n in nodes if not n["isPrivate"]]
    return {
        "name": user["name"] or login,
        "created_at": created,
        "followers": user["followers"]["totalCount"],
        "public_repos": len(public),
        "stars": sum(n["stargazerCount"] for n in public),
        "totals": totals,
        "days": days,
        "languages": [(n, b, colors[n]) for n, b in language_bytes.most_common()],
        "commit_times": commit_times,
        "repos": repos,
        "events": fetch_events(login, token, tz),
        "source": "graphql",
    }


def _repo_from_node(node: dict, weekly: list[int]) -> Repo:
    lang = node.get("primaryLanguage") or {}
    return Repo(
        name=node["name"],
        description=node.get("description") or "",
        url=node["url"],
        language=lang.get("name"),
        language_color=lang.get("color"),
        stars=node["stargazerCount"],
        forks=node["forkCount"],
        pushed_at=_parse_ts(node["pushedAt"]) if node.get("pushedAt") else None,
        weekly_commits=weekly,
    )


def _weekly(stamps: list[datetime], now: datetime, weeks: int = 26) -> list[int]:
    buckets = [0] * weeks
    for stamp in stamps:
        age = (now - stamp).days // 7
        if 0 <= age < weeks:
            buckets[weeks - 1 - age] += 1
    return buckets


# ─────────────────────────────────────────────────────────── public / REST ───

_TD = re.compile(r'<td\b[^>]*\bdata-date="[^"]+"[^>]*>')
_ATTR = re.compile(r'([\w-]+)="([^"]*)"')
_TIP = re.compile(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>')


def scrape_calendar(login: str, year: int | None = None) -> dict[date, Day]:
    """The profile contribution graph is public HTML; counts live in tooltips."""
    query = f"?from={year}-01-01&to={year}-12-31" if year else ""
    page = get(f"https://github.com/users/{login}/contributions{query}", accept="text/html").decode()
    tips = {}
    for target, text in _TIP.findall(page):
        match = re.match(r"([\d,]+) contribution", html.unescape(text))
        tips[target] = int(match.group(1).replace(",", "")) if match else 0
    days = {}
    for tag in _TD.findall(page):
        attrs = dict(_ATTR.findall(tag))
        day = date.fromisoformat(attrs["data-date"])
        days[day] = Day(day, tips.get(attrs.get("id", ""), 0), int(attrs.get("data-level", 0)))
    if not days:
        raise RuntimeError("contribution calendar markup changed: no days found")
    return days


def fetch_public(login: str, featured: list[str], tz: str, token: str | None = None) -> dict:
    zone = ZoneInfo(tz)
    user = get_json(f"{API}/users/{login}", token)
    created = _parse_ts(user["created_at"])
    now = datetime.now(timezone.utc)

    days: dict[date, Day] = {}
    for year in range(created.year, now.year + 1):
        days.update(scrape_calendar(login, year))
    days.update(scrape_calendar(login))  # rolling year, for GitHub's own levels

    repos_raw = [r for r in get_json(f"{API}/users/{login}/repos?per_page=100&type=owner&sort=pushed", token) if not r["fork"]]
    language_bytes: Counter[str] = Counter()
    commit_times: list[datetime] = []
    repos: dict[str, Repo] = {}
    for raw in repos_raw:
        for lang, size in get_json(raw["languages_url"], token).items():
            language_bytes[lang] += size
        try:
            commits = get_json(f"{API}/repos/{login}/{raw['name']}/commits?author={login}&per_page=100", token)
        except Exception:  # empty repositories answer 409
            commits = []
        commit_times += [_parse_ts(c["commit"]["author"]["date"]).astimezone(zone) for c in commits]
        if raw["name"] in featured:
            weekly = _weekly([_parse_ts(c["commit"]["committer"]["date"]) for c in commits], now)
            repos[raw["name"]] = Repo(
                name=raw["name"],
                description=raw.get("description") or "",
                url=raw["html_url"],
                language=raw.get("language"),
                language_color=LANGUAGE_COLORS.get(raw.get("language") or "", "#8b93c7"),
                stars=raw["stargazers_count"],
                forks=raw["forks_count"],
                pushed_at=_parse_ts(raw["pushed_at"]) if raw.get("pushed_at") else None,
                weekly_commits=weekly,
            )

    def search_total(query: str, kind: str = "issues") -> int:
        try:
            return get_json(f"{API}/search/{kind}?q={quote(query)}&per_page=1", token)["total_count"]
        except Exception as error:
            log.warning("search %r failed: %s", query, error)
            return 0

    totals = Totals(
        commits=search_total(f"author:{login}", "commits"),
        prs=search_total(f"author:{login} type:pr"),
        issues=search_total(f"author:{login} type:issue"),
        reviews=search_total(f"reviewed-by:{login} type:pr -author:{login}"),
    )
    return {
        "name": user.get("name") or login,
        "created_at": created,
        "followers": user["followers"],
        "public_repos": user["public_repos"],
        "stars": sum(r["stargazers_count"] for r in repos_raw),
        "totals": totals,
        "days": days,
        "languages": [(n, b, LANGUAGE_COLORS.get(n, "#8b93c7")) for n, b in language_bytes.most_common()],
        "commit_times": commit_times,
        "repos": repos,
        "events": fetch_events(login, token, tz),
        "source": "public",
    }


def fetch_events(login: str, token: str | None, tz: str) -> list[Event]:
    """Public events only (the last 90 days, newest first)."""
    zone = ZoneInfo(tz)
    events: list[Event] = []
    for raw in get_json(f"{API}/users/{login}/events/public?per_page=100", token):
        repo = raw["repo"]["name"].split("/", 1)[-1] if raw["repo"]["name"].startswith(f"{login}/") else raw["repo"]["name"]
        payload = raw.get("payload") or {}
        at = _parse_ts(raw["created_at"]).astimezone(zone)
        kind = raw["type"]
        if kind == "PushEvent":
            size = payload.get("size") or payload.get("distinct_size") or 1
            events.append(Event("PUSH", repo, at, f"{size} COMMIT{'S' if size != 1 else ''}"))
        elif kind == "PullRequestEvent":
            pr = payload.get("pull_request") or {}
            merged = payload.get("action") == "closed" and pr.get("merged")
            if payload.get("action") in ("opened", "reopened") or merged:
                events.append(Event("MERGE" if merged else "PR", repo, at, f"#{payload.get('number', '')}"))
        elif kind == "CreateEvent":
            ref_type = payload.get("ref_type", "")
            events.append(Event("NEW", repo, at, ref_type.upper()))
        elif kind == "ReleaseEvent":
            events.append(Event("RELEASE", repo, at, (payload.get("release") or {}).get("tag_name", "")))
        elif kind == "IssuesEvent" and payload.get("action") == "opened":
            events.append(Event("ISSUE", repo, at, f"#{(payload.get('issue') or {}).get('number', '')}"))
        elif kind == "PullRequestReviewEvent":
            events.append(Event("REVIEW", repo, at, ""))
        elif kind == "WatchEvent":
            events.append(Event("STAR", repo, at, ""))
        elif kind == "ForkEvent":
            events.append(Event("FORK", repo, at, ""))
    return events
