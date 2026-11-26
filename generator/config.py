"""Loads and validates profile.yml."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

from . import palettes

ROOT = Path(__file__).resolve().parent.parent
ASSETS = Path(__file__).resolve().parent / "assets"


@dataclass
class Link:
    id: str
    label: str
    url: str


@dataclass
class StackItem:
    name: str
    icon: str | None = None


@dataclass
class Config:
    login: str
    name: str
    initials: str
    timezone: str
    roles: list[str]
    about: dict
    links: list[Link]
    stack: list[StackItem]
    featured: list[str]
    location: dict = field(default_factory=dict)
    palette: str = palettes.DEFAULT

    @property
    def coding_since(self) -> date:
        value = self.about.get("coding_since")
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value)) if value else date.today()


def load(path: Path | None = None) -> Config:
    raw = yaml.safe_load((path or ROOT / "profile.yml").read_text(encoding="utf-8"))
    missing = [k for k in ("login", "name") if not raw.get(k)]
    if missing:
        raise ValueError(f"profile.yml is missing: {', '.join(missing)}")
    stack = [StackItem(**item) for item in raw.get("stack", [])]
    for item in stack:
        if item.icon and not (ASSETS / "icons" / f"{item.icon}.svg").exists():
            raise ValueError(f"profile.yml: icon '{item.icon}' not found in generator/assets/icons")
    palette = raw.get("palette") or palettes.DEFAULT
    if palette not in palettes.PALETTES:
        raise ValueError(f"profile.yml: unknown palette '{palette}', choose one of: {', '.join(palettes.PALETTES)}")
    return Config(
        login=raw["login"],
        name=raw["name"],
        initials=raw.get("initials") or "".join(p[0] for p in raw["name"].split()[:2]).upper(),
        timezone=raw.get("timezone", "UTC"),
        roles=raw.get("roles") or [raw["name"]],
        about=raw.get("about") or {},
        links=[Link(**link) for link in raw.get("links", [])],
        stack=stack,
        featured=list(raw.get("featured") or [])[:3],
        location=raw.get("location") or {},
        palette=palette,
    )
