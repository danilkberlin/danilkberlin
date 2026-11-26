"""Every colour on the profile. Pick a palette with `palette:` in profile.yml.

Each palette has a `dark` and a `light` theme with the same keys (a test checks
that). The accent keys keep their original names but act as roles, so a new
palette only has to fill the roles, not match the hue in the name:

    cyan    primary accent: links, prompts, section diamonds, first stat
    pink    hot accent: cursors, horizon, peaks, the hottest heat level
    amber   highlight: medals, flip-board glyphs, the sun core
    violet  tertiary accent: gradients' middle stop, secondary series
    green   "ok" status          red   "error" status
    heat    5 steps, no activity -> most activity (calendar, 3D city)
    glow    neon glow strength (blur multiplier)

The keys after the core tokens colour the illustrated scenes (hero skyline,
terminal, departures board, 3D city), which have no generic role.
"""
from __future__ import annotations

DEFAULT = "nightshift"

PALETTES: dict[str, dict[str, dict]] = {
    # Neon synthwave navy: the original "Berlin Nightshift" look.
    "nightshift": {
        "dark": {
            "name": "dark",
            "bg": "#0b0f2a", "bg2": "#141a46", "panel": "#0e1334", "panel2": "#161d4d",
            "line": "#262e68", "text": "#e6e9ff", "muted": "#8d94c9", "faint": "#454c86",
            "cyan": "#22d3ee", "pink": "#f472b6", "amber": "#fbbf24", "violet": "#a78bfa",
            "green": "#34d399", "red": "#fb7185",
            "heat": ["#1a2050", "#2b3a8f", "#1590b8", "#22d3ee", "#f472b6"],
            "glow": 1.0,
            # hero scene
            "sky": [(0, "#03051a"), (.5, "#0f0b38"), (.8, "#2c0d4d"), (1, "#5a1561")],
            "ground": ["#1a0833", "#05030f"],
            "moon": "#fff6d6", "moon_shadow": "#1c2152", "moon_crater": "#e8dcb0", "moon_glow": "#fff3c4",
            "sun": ["#ffd166", "#ff5fa2"], "sun_stripe": "#bfe2ff",
            "cloud": "#2a2c62", "rain": "#9fb4ff", "fog": "#8a8fc4",
            "far": "#1b1446", "bld": ["#191541", "#07061a"], "tower": "#191541",
            "windows": ["#fbbf24", "#ffe8a3", "#22d3ee", "#f472b6"],
            "pill": "#0c1033",
            # cards
            "term": "#080b22", "term_bar": "#11163d",
            "board": "#070a1f", "board_tile": ["#181d45", "#11153a"], "board_split": "#04051a", "board_time": "#ffe3a3",
            "tile": "#141a44", "monitor": "#060920", "button": ["#161d4d", "#0e1334"], "sun_core": "#fff4c2",
            # 3D contribution city (GIF)
            "city_sky": ["#03051a", "#120c3d", "#3a1153"], "city_glow": "#f472b6",
            "city_plate": "#0a0822", "city_body": "#16143a", "city_empty": "#1a2050",
            "city_windows": ["#fbbf24", "#ffe8a3", "#22d3ee"], "city_label": "#e6e9ff", "city_chip": "#0c0a28",
        },
        "light": {
            "name": "light",
            "bg": "#f6f7fe", "bg2": "#e9ecfc", "panel": "#ffffff", "panel2": "#f1f3fd",
            "line": "#d9dcf2", "text": "#1b1e45", "muted": "#5d6394", "faint": "#b3b8da",
            "cyan": "#0891b2", "pink": "#db2777", "amber": "#d97706", "violet": "#7c3aed",
            "green": "#059669", "red": "#e11d48",
            "heat": ["#e6e9f7", "#b4ecf7", "#4fc3dc", "#0e8fb0", "#db2777"],
            "glow": 0.35,
            # hero scene
            "sky": [(0, "#7cc4ff"), (.45, "#bfe2ff"), (.8, "#ffd3ea"), (1, "#ffbfa6")],
            "ground": ["#f6d9f0", "#efe9ff"],
            "moon": "#d97706", "moon_shadow": "#1c2152", "moon_crater": "#e8dcb0", "moon_glow": "#fff3c4",
            "sun": ["#ffd166", "#ff5fa2"], "sun_stripe": "#bfe2ff",
            "cloud": "#ffffff", "rain": "#5b6fd6", "fog": "#ffffff",
            "far": "#b6a9e6", "bld": ["#8c7fd0", "#6c61b5"], "tower": "#6c61b5",
            "windows": ["#e9f6ff", "#ffffff", "#ffe1f0"],
            "pill": "#ffffff",
            # cards
            "term": "#fcfcff", "term_bar": "#eef0fb",
            "board": "#e4e7f7", "board_tile": ["#ffffff", "#f1f3fc"], "board_split": "#c3c8e6", "board_time": "#7c3aed",
            "tile": "#ffffff", "monitor": "#e9ecfc", "button": ["#ffffff", "#f3f4fd"], "sun_core": "#fff4c2",
            # 3D contribution city (GIF)
            "city_sky": ["#9fd4ff", "#d8ecff", "#ffd9ec"], "city_glow": "#ffc8e6",
            "city_plate": "#eee8ff", "city_body": "#968ad6", "city_empty": "#d6d0f0",
            "city_windows": ["#f0f8ff", "#ffffff", "#dcecff"], "city_label": "#3c3478", "city_chip": "#f6f3ff",
        },
    },
    # Sampled from the avatar: graphite tee and shorts, stone-grey hoodie, warm skin
    # (apricot, terracotta), sand sneakers. Neutral surfaces, warm neon accents,
    # and Berlin at night under sodium street lights.
    "graphite": {
        "dark": {
            "name": "dark",
            "bg": "#121113", "bg2": "#1c1b1d", "panel": "#161517", "panel2": "#201f21",
            "line": "#353336", "text": "#f2ede7", "muted": "#a9a59e", "faint": "#56534f",
            "cyan": "#ffb38a", "pink": "#f2735a", "amber": "#f5c46b", "violet": "#cf9fb8",
            "green": "#9ad4a0", "red": "#ff6b6b",
            "heat": ["#262325", "#4b362f", "#8a4f3a", "#e0704f", "#ffb38a"],
            "glow": 1.0,
            # hero scene
            "sky": [(0, "#0b0a0c"), (.5, "#1a1718"), (.8, "#3a2621"), (1, "#6b3a2c")],
            "ground": ["#2a1a16", "#0a0809"],
            "moon": "#fff1e0", "moon_shadow": "#2a2729", "moon_crater": "#e6d3bd", "moon_glow": "#ffe6cc",
            "sun": ["#f5c46b", "#f2735a"], "sun_stripe": "#3a2621",
            "cloud": "#3a3436", "rain": "#c9b8ab", "fog": "#8f857f",
            "far": "#221e20", "bld": ["#1f1b1d", "#0b090a"], "tower": "#1f1b1d",
            "windows": ["#f5c46b", "#ffe2b8", "#ffb38a", "#f2735a"],
            "pill": "#141315",
            # cards
            "term": "#0f0e10", "term_bar": "#1d1b1e",
            "board": "#0c0b0d", "board_tile": ["#232124", "#1a181b"], "board_split": "#070607", "board_time": "#ffe2b8",
            "tile": "#1d1c1e", "monitor": "#0b0a0c", "button": ["#201f21", "#161517"], "sun_core": "#fff1dc",
            # 3D contribution city (GIF)
            "city_sky": ["#0b0a0c", "#1d1819", "#4a2a22"], "city_glow": "#f2735a",
            "city_plate": "#121012", "city_body": "#1e1b1d", "city_empty": "#262325",
            "city_windows": ["#f5c46b", "#ffe2b8", "#ffb38a"], "city_label": "#f2ede7", "city_chip": "#141214",
        },
        "light": {
            "name": "light",
            "bg": "#f6f4f1", "bg2": "#ebe7e2", "panel": "#ffffff", "panel2": "#f7f5f2",
            "line": "#e0dbd4", "text": "#262528", "muted": "#6e6a66", "faint": "#c2bcb4",
            "cyan": "#c8703f", "pink": "#b83a4b", "amber": "#b7832b", "violet": "#9b5f84",
            "green": "#4f8a5b", "red": "#c8453a",
            "heat": ["#ece8e3", "#efc6a8", "#e8a27c", "#cf6d45", "#a8432a"],
            "glow": 0.35,
            # hero scene
            "sky": [(0, "#cfd2d4"), (.45, "#e6e2dc"), (.8, "#f6d6bf"), (1, "#f1b493")],
            "ground": ["#f3dccb", "#efe9e2"],
            "moon": "#b7832b", "moon_shadow": "#2a2729", "moon_crater": "#e6d3bd", "moon_glow": "#ffe6cc",
            "sun": ["#ffc46b", "#e8714f"], "sun_stripe": "#d9d9d8",
            "cloud": "#ffffff", "rain": "#8a7f78", "fog": "#ffffff",
            "far": "#c4c2bd", "bld": ["#9d9a94", "#7f7b76"], "tower": "#7f7b76",
            "windows": ["#fff4ea", "#ffffff", "#ffe1cf"],
            "pill": "#ffffff",
            # cards
            "term": "#fdfcfa", "term_bar": "#f0ede8",
            "board": "#ebe7e1", "board_tile": ["#ffffff", "#f6f3ef"], "board_split": "#d3ccc3", "board_time": "#9b5f84",
            "tile": "#ffffff", "monitor": "#ebe7e2", "button": ["#ffffff", "#f6f4f1"], "sun_core": "#fff1dc",
            # 3D contribution city (GIF)
            "city_sky": ["#d5d7d8", "#ece8e3", "#f8dcc8"], "city_glow": "#ffd2b8",
            "city_plate": "#f3efea", "city_body": "#a39d97", "city_empty": "#ddd7d0",
            "city_windows": ["#fff6ee", "#ffffff", "#ffe6d6"], "city_label": "#4a4440", "city_chip": "#faf8f5",
        },
    },
}


def themes(palette: str = DEFAULT) -> dict[str, dict]:
    """The {"dark": ..., "light": ...} pair of one palette."""
    try:
        return PALETTES[palette]
    except KeyError:
        raise ValueError(f"unknown palette '{palette}', choose one of: {', '.join(PALETTES)}") from None
