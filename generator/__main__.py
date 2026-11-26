"""python -m generator --out dist [--demo|--empty] [--only hero,stats] [--no-gif]"""
from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import time
from datetime import date, datetime
from pathlib import Path

from . import collect, config
from .svg.core import THEMES
from .svg.registry import CARDS

log = logging.getLogger("generator")


def _json_default(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    raise TypeError(type(value))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="generator")
    parser.add_argument("--out", default="dist", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--demo", action="store_true", help="render deterministic demo data (offline)")
    mode.add_argument("--empty", action="store_true", help="render a brand-new, empty account (offline)")
    parser.add_argument("--only", default="", help="comma-separated card names")
    parser.add_argument("--no-gif", action="store_true", help="skip the (slow) 3D city GIF")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("fontTools").setLevel(logging.WARNING)

    started = time.monotonic()
    cfg = config.load()
    data = collect.build(cfg, "demo" if args.demo else "empty" if args.empty else "live")
    log.info("data source: %s · %d contributions in the last year", data.source, data.totals.contributions_year)
    args.out.mkdir(parents=True, exist_ok=True)

    only = {name.strip() for name in args.only.split(",") if name.strip()}
    written = 0
    for card in CARDS:
        if only and card.name not in only:
            continue
        if card.kind == "gif" and args.no_gif:
            continue
        for theme in THEMES.values():
            for filename, content in card.render(cfg, data, theme, started=started):
                path = args.out / filename
                if isinstance(content, bytes):
                    path.write_bytes(content)
                else:
                    path.write_text(content, encoding="utf-8")
                written += 1
                log.info("wrote %-32s %7.1f KB", filename, path.stat().st_size / 1024)

    snapshot = {k: v for k, v in dataclasses.asdict(data).items() if k not in ("history", "commit_times")}
    snapshot["elapsed_seconds"] = round(time.monotonic() - started, 2)
    (args.out / "data.json").write_text(json.dumps(snapshot, default=_json_default, indent=1), encoding="utf-8")
    log.info("done: %d files in %.1fs", written, time.monotonic() - started)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
