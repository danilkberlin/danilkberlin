"""Every card must render for rich, empty and sparse data, in both themes, and stay README-safe."""
from __future__ import annotations

import io
import re
from datetime import date, datetime, timedelta
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

import pytest
from PIL import Image

from generator import collect, config, stats
from generator.data import astro, github
from generator.gif import city
from generator.model import Day, Event
from generator.readme import Readme
from generator.svg.core import THEMES
from generator.svg.registry import CARDS

CFG = config.load()
NOW = datetime(2026, 11, 26, 2, 17, tzinfo=ZoneInfo(CFG.timezone))
MAX_SVG_BYTES = 400_000
MAX_GIF_BYTES = 3_000_000


def _sparse():
    """Mirrors a quiet public profile (one active day, tiny language shares) plus hostile strings."""
    data = collect.build(CFG, "empty", now=NOW)
    data.calendar[-24] = Day(data.calendar[-24].date, 2, 4)
    data.history = data.calendar
    data.totals.contributions_year = 2
    data.languages = [("C++", 90_000, "#f34b7d"), ("Shell", 23, "#89e051"), ("Jupyter <Notebook> & co", 5, "#DA5B0B")]
    demo = collect.build(CFG, "demo", now=NOW)
    data.repos = {name: repo for name, repo in demo.repos.items()}
    for repo in data.repos.values():
        repo.description = 'Tags like <script>alert("x")</script> & "quotes" must be escaped'
    data.events = [Event("PUSH", "weird&<repo>", NOW, "2 COMMITS")]
    return data


DATASETS = {
    "demo": lambda: collect.build(CFG, "demo", now=NOW),
    "empty": lambda: collect.build(CFG, "empty", now=NOW),
    "sparse": _sparse,
}


@pytest.fixture(scope="module", params=sorted(DATASETS))
def data(request):
    return DATASETS[request.param]()


@pytest.fixture(autouse=True)
def fast_gif(monkeypatch):
    monkeypatch.setattr(city, "FRAMES", 4)


@pytest.mark.parametrize("theme", sorted(THEMES))
@pytest.mark.parametrize("card", CARDS, ids=lambda c: c.name)
def test_card_renders_safely(card, theme, data):
    outputs = list(card.render(CFG, data, THEMES[theme], started=0.0))
    assert outputs, f"{card.name} produced nothing"
    for filename, content in outputs:
        assert filename.endswith(f"-{theme}.{'gif' if card.kind == 'gif' else 'svg'}")
        if card.kind == "gif":
            assert content[:6] == b"GIF89a"
            assert len(content) < MAX_GIF_BYTES
            assert Image.open(io.BytesIO(content)).n_frames == 4
            continue
        assert len(content.encode()) < MAX_SVG_BYTES, f"{filename} is too large"
        ElementTree.fromstring(content)  # well-formed
        lowered = content.lower()
        assert "<script" not in lowered and "foreignobject" not in lowered
        assert not re.search(r'href="(?!#)', content), f"{filename} references an external resource"
        assert not re.search(r"url\((?!#|data:)", content), f"{filename} loads something external"
        assert not re.search(r'="[^"]*\b(nan|inf)\b', lowered), f"{filename} has NaN/inf geometry"


def test_full_build_has_unique_filenames():
    data = collect.build(CFG, "demo", now=NOW)
    names = [name for card in CARDS for theme in THEMES.values() for name, _ in card.render(CFG, data, theme)]
    assert len(names) == len(set(names))


def test_readme_is_in_sync_with_profile():
    expected = Readme(CFG).render()
    actual = (config.ROOT / "README.md").read_text(encoding="utf-8")
    assert actual == expected, "README.md is stale: run `python -m generator.readme`"


def test_readme_references_every_rendered_image():
    data = collect.build(CFG, "demo", now=NOW)
    readme = Readme(CFG).render()
    for card in CARDS:
        for theme in THEMES.values():
            for name, _ in card.render(CFG, data, theme):
                assert f"/{name}" in readme, f"{name} is rendered but never shown"


def test_readme_has_no_visible_text():
    readme = Readme(CFG).render()
    without_comments = re.sub(r"<!--.*?-->", "", readme, flags=re.S)
    visible = re.sub(r"<[^>]+>", "", without_comments)
    assert visible.strip() == ""


def test_calendar_is_53_monday_first_weeks():
    data = collect.build(CFG, "demo", now=NOW)
    assert data.calendar[0].date.weekday() == 0
    assert data.calendar[-1].date == NOW.date()
    assert 52 * 7 < len(data.calendar) <= 53 * 7


def test_streaks():
    today = date(2026, 11, 26)
    history = [Day(today - timedelta(days=n), c) for n, c in reversed(list(enumerate([0, 3, 1, 2, 0, 5, 5, 5, 5])))]
    assert stats.current_streak(history) == 3  # today is still empty at build time
    assert stats.longest_streak(history) == 4
    assert stats.current_streak([]) == 0


def test_achievement_tiers():
    data = collect.build(CFG, "empty", now=NOW)
    for item in stats.achievements(data):
        assert 0 <= item.progress <= 1
        assert item.tier <= len(item.tiers)


@pytest.mark.parametrize("phase,name", [(0.0, "New Moon"), (0.25, "First Quarter"), (0.5, "Full Moon"), (0.75, "Last Quarter")])
def test_moon_names(phase, name):
    days = phase * astro.SYNODIC_MONTH
    moment = astro._REFERENCE + timedelta(days=days)
    assert astro.moon(moment).name == name


def test_moon_path_is_valid_for_all_phases():
    for i in range(30):
        path = astro.moon_path(10, 10, 5, i / 30)
        assert path.startswith("M") and "nan" not in path


def test_scrape_calendar_parses_github_markup(monkeypatch):
    page = (
        '<td tabindex="0" data-ix="44" style="width: 10px" data-date="2026-11-03" id="contribution-day-component-2-44" '
        'data-level="4" role="gridcell" class="ContributionCalendar-day"></td>'
        '<td data-date="2026-11-04" id="contribution-day-component-3-44" data-level="0" class="ContributionCalendar-day"></td>'
        '<tool-tip for="contribution-day-component-2-44" class="sr-only">1,204 contributions on November 3rd.</tool-tip>'
        '<tool-tip for="contribution-day-component-3-44" class="sr-only">No contributions on November 4th.</tool-tip>'
    )
    monkeypatch.setattr(github, "get", lambda *a, **k: page.encode())
    days = github.scrape_calendar("someone", 2026)
    assert days[date(2026, 11, 3)].count == 1204 and days[date(2026, 11, 3)].level == 4
    assert days[date(2026, 11, 4)].count == 0
