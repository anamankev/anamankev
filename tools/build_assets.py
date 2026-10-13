#!/usr/bin/env python3
"""Draws every picture used by README.md and saves it in assets/.

Run it from anywhere:

    python3 tools/build_assets.py

Each picture is drawn twice, once for GitHub's light theme and once for its
dark theme. The numbers in the charts are typed in below, each next to the
file it was copied from, so a chart only changes when its source does. The
graph in the header is read from tools/header_graph.json, which
tools/trace_search.py records from a real hnsw-engine index.

The pictures are SVG files: plain text that describes shapes, which the
browser draws at any size without blurring.

Most pictures are "tiles" 418 wide. Two tiles sit side by side on a desktop
screen and drop one under the other on a phone, so the text stays readable.
"""

import json
from html import escape
from math import dist
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ASSETS = TOOLS.parent / "assets"

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

# One set of colours per GitHub theme. The greys are GitHub's own, so the
# pictures sit on the page as if they were part of it.
THEMES = {
    "light": {
        "ink": "#1f2328",  # main text
        "ink2": "#59636e",  # secondary text
        "card": "#f6f8fa",  # tile background
        "border": "#d1d9e0",  # tile outline and thin rules
        "edge": "#afb8c1",  # links between graph nodes
        "context": "#818b98",  # bars and nodes that are background, not the point
        "accent": "#d9571e",  # the one thing each picture highlights
        "accent_text": "#bc4c00",  # accent dark enough to read as small text
        "spark": "#d9571e",  # the moving dot
        "glow": 0.09,
    },
    "dark": {
        "ink": "#f0f6fc",
        "ink2": "#9198a1",
        "card": "#161b22",
        "border": "#30363d",
        "edge": "#484f58",
        "context": "#7d8590",
        "accent": "#e3622b",
        "accent_text": "#f0883e",
        "spark": "#ffa657",
        "glow": 0.13,
    },
}

# ---------------------------------------------------------------------------
# The numbers. Change them here and nowhere else.
# ---------------------------------------------------------------------------

# hnsw-engine/docs/BENCHMARKS.md, table "sift1m_summary", column
# "QPS @ recall>=0.95" (full SIFT 1M, recall@10, one thread, Apple M5).
HNSW_QPS = [
    # name, what it is, queries per second, is this my engine?
    ("Exact search", "FAISS flat", 114, False),
    ("hnsw-engine", "Python + Numba", 4447, True),
    ("hnswlib", "C++", 6193, False),
    ("FAISS HNSW", "C++", 10301, False),
]

# two-stage-recsys/README.md, table "results_main", column "NDCG@10":
# point estimate, then the low and high ends of the 95% bootstrap interval.
RECSYS_NDCG = [
    ("Popularity", 0.0193, 0.0167, 0.0222, False),
    ("Item-item co-occurrence", 0.0276, 0.0244, 0.0311, False),
    ("Tuned implicit ALS", 0.0445, 0.0409, 0.0489, False),
    ("Two-tower, exact retrieval", 0.0615, 0.0570, 0.0664, False),
    ("Two-tower via hnsw-engine", 0.0619, 0.0573, 0.0668, False),
    ("Two-tower + LightGBM ranker", 0.0906, 0.0848, 0.0959, True),
]

# A real index and one real search through it. See tools/trace_search.py.
GRAPH = json.loads((TOOLS / "header_graph.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------------------
# Small helpers for writing SVG
# ---------------------------------------------------------------------------


def text(x, y, content, size, fill, weight=400, anchor="start", family=SANS, spacing=None):
    """One line of text. `anchor` is start, middle or end."""
    extra = f' letter-spacing="{spacing}"' if spacing is not None else ""
    return (
        f'<text x="{x:g}" y="{y:g}" font-family="{family}" font-size="{size:g}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{extra}>{escape(content)}</text>'
    )


def line(x1, y1, x2, y2, stroke, width=1.0, opacity=1.0):
    return (
        f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{stroke}" '
        f'stroke-width="{width:g}" stroke-linecap="round" opacity="{opacity:g}"/>'
    )


def bar(x, y, length, thickness, fill):
    """A horizontal bar: square where it starts, rounded at the data end."""
    if length < 8:  # too short to round
        return f'<rect x="{x:g}" y="{y:g}" width="{max(length, 3):g}" height="{thickness:g}" fill="{fill}"/>'
    r = 4
    return (
        f'<path d="M{x:g} {y:g} h{length - r:g} a{r} {r} 0 0 1 {r} {r} v{thickness - 2 * r:g} '
        f'a{r} {r} 0 0 1 -{r} {r} h-{length - r:g} z" fill="{fill}"/>'
    )


def svg(width, height, description, body):
    """Wrap shapes in an SVG document. The description is read by screen readers."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(description)}">'
        f"<title>{escape(description)}</title>"
        # Visitors who ask their device for less motion get the still version.
        "<style>.still{display:none}"
        "@media (prefers-reduced-motion: reduce){.motion{display:none}.still{display:inline}}</style>"
        f"{body}</svg>\n"
    )


TILE_W = 418  # two of these plus the gap between them fill GitHub's 846-wide profile column
LEFT, RIGHT = 28, TILE_W - 28  # where a tile's content starts and ends


def tile_outline(theme, height):
    """The rounded panel behind a tile. It stops 3 short of each edge so neighbours don't touch."""
    t = THEMES[theme]
    return (
        f'<rect x="3.5" y="3.5" width="{TILE_W - 7}" height="{height - 7}" rx="12" '
        f'fill="{t["card"]}" stroke="{t["border"]}"/>'
    )


# ---------------------------------------------------------------------------
# Header, left half: who I am
# ---------------------------------------------------------------------------

HEADER_H = 300


def name_tile(theme):
    t = THEMES[theme]
    parts = [
        text(5, 78, "CS + APPLIED MATH  ·  BRANDEIS ’30  ·  BOSTON", 11.5, t["accent_text"], 600, family=MONO, spacing=1.4),
        text(2, 138, "Kelvin Anaman", 54, t["ink"], 700, spacing=-1.4),
        text(5, 178, "ML systems built from the paper up,", 18, t["ink2"]),
        text(5, 203, "measured against the best libraries.", 18, t["ink2"]),
    ]
    x = 5
    for label, highlighted in [("Founder, Pulse Energies", True), ("Wien Scholar", False)]:
        width = round(len(label) * 7.1 + (38 if highlighted else 26))
        parts.append(f'<rect x="{x + 0.5}" y="226.5" width="{width}" height="28" rx="14" fill="none" stroke="{t["border"]}"/>')
        if highlighted:
            parts.append(f'<circle cx="{x + 16}" cy="240.5" r="3.5" fill="{t["accent"]}"/>')
        parts.append(text(x + (width + (12 if highlighted else 0)) / 2, 245, label, 12.5, t["ink2"], 500, anchor="middle"))
        x += width + 8
    description = (
        "Kelvin Anaman. ML systems built from the paper up, measured against the best libraries. "
        "Computer science and applied math, Brandeis class of 2030, Boston. Founder of Pulse Energies. Wien Scholar."
    )
    return svg(TILE_W, HEADER_H, description, "".join(parts))


# ---------------------------------------------------------------------------
# Header, right half: a real HNSW index being searched
# ---------------------------------------------------------------------------

# The layers are drawn as slanted sheets, top layer first.
SHEET_LEFT, SHEET_WIDTH, SHEET_SLANT, SHEET_HEIGHT = 44, 286, 78, 76
SHEET_TOP = {2: 12, 1: 108, 0: 204}


def on_sheet(layer, across, down):
    """Turn a position in the unit square into a spot on a layer's sheet."""
    across, down = 0.06 + 0.88 * across, 0.10 + 0.80 * down  # keep clear of the sheet's edge
    x = SHEET_LEFT + SHEET_SLANT * (1 - down) + SHEET_WIDTH * across
    y = SHEET_TOP[layer] + SHEET_HEIGHT * down
    return round(x, 1), round(y, 1)


def node_xy(layer, node):
    return on_sheet(layer, *GRAPH["points"][node])


def graph_tile(theme):
    t = THEMES[theme]
    layers = GRAPH["layers"]
    route = [tuple(step) for step in GRAPH["route"]]  # (layer, node) for every node the search moved to
    parts = []

    # Soft glow behind the graph.
    parts.append(
        '<defs><radialGradient id="glow" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0" stop-color="{t["accent"]}" stop-opacity="{t["glow"]}"/>'
        f'<stop offset="1" stop-color="{t["accent"]}" stop-opacity="0"/></radialGradient></defs>'
        f'<ellipse cx="226" cy="{HEADER_H / 2:g}" rx="200" ry="150" fill="url(#glow)"/>'
    )

    # The sheets, their names, and every link the engine made on each layer.
    for layer in (2, 1, 0):
        top, bottom = SHEET_TOP[layer], SHEET_TOP[layer] + SHEET_HEIGHT
        corners = [
            (SHEET_LEFT + SHEET_SLANT, top),
            (SHEET_LEFT + SHEET_SLANT + SHEET_WIDTH, top),
            (SHEET_LEFT + SHEET_WIDTH, bottom),
            (SHEET_LEFT, bottom),
        ]
        points = " ".join(f"{px},{py}" for px, py in corners)
        parts.append(f'<polygon points="{points}" fill="{t["card"]}" stroke="{t["border"]}" stroke-linejoin="round"/>')
        parts.append(text(SHEET_LEFT + SHEET_SLANT / 2 - 12, top + SHEET_HEIGHT / 2 + 4, f"L{layer}", 11, t["ink2"], 500, "end", MONO))
        for a, b in layers[layer]["links"]:
            parts.append(line(*node_xy(layer, a), *node_xy(layer, b), t["edge"], 0.9))

    # Faint uprights: the same node seen on the layer below.
    for upper, lower in ((2, 1), (1, 0)):
        for node in layers[upper]["nodes"]:
            parts.append(line(*node_xy(upper, node), *node_xy(lower, node), t["edge"], 0.9, 0.4))

    # The search path, drawn under the nodes.
    path = [node_xy(layer, node) for layer, node in route]
    path_d = "M" + " L".join(f"{px:g} {py:g}" for px, py in path)
    path_length = sum(dist(a, b) for a, b in zip(path, path[1:]))
    parts.append(
        f'<path d="{path_d}" fill="none" stroke="{t["accent"]}" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" opacity="0.65"/>'
    )

    # Nodes. A ring in the sheet colour keeps each one clear of the lines under it.
    visited = set(route)
    for layer in (2, 1, 0):
        radius = {2: 3.8, 1: 3.3, 0: 2.6}[layer]
        for node in layers[layer]["nodes"]:
            px, py = node_xy(layer, node)
            hit = (layer, node) in visited
            parts.append(
                f'<circle cx="{px:g}" cy="{py:g}" r="{radius + (0.9 if hit else 0):g}" '
                f'fill="{t["accent"] if hit else t["context"]}" stroke="{t["card"]}" stroke-width="1.2"/>'
            )

    # The query: a small cross on the bottom layer, where the search is heading.
    qx, qy = on_sheet(0, *GRAPH["query"])
    parts.append(line(qx - 4, qy - 4, qx + 4, qy + 4, t["ink"], 1.6))
    parts.append(line(qx - 4, qy + 4, qx + 4, qy - 4, t["ink"], 1.6))
    # Its label goes under the sheet, joined by a thin line, so it covers nothing.
    sheet_bottom = SHEET_TOP[0] + SHEET_HEIGHT
    parts.append(line(qx, qy + 8, qx, sheet_bottom + 5, t["ink2"], 0.9))
    parts.append(text(qx, sheet_bottom + 17, "query", 10.5, t["ink"], 500, "middle", MONO))

    # The answer: the last node on the path, with a ring that breathes.
    end_x, end_y = path[-1]
    parts.append(
        f'<circle class="motion" cx="{end_x:g}" cy="{end_y:g}" r="5" fill="none" stroke="{t["spark"]}" stroke-width="1.4">'
        '<animate attributeName="r" values="5;14" dur="2.4s" repeatCount="indefinite"/>'
        '<animate attributeName="opacity" values="0.7;0" dur="2.4s" repeatCount="indefinite"/></circle>'
    )

    # A bright streak and a dot that run along the path, rest at the answer, then repeat.
    loop = 'dur="8s" repeatCount="indefinite"'
    streak = 40
    parts.append(
        f'<path class="motion" d="{path_d}" fill="none" stroke="{t["spark"]}" stroke-width="2.6" '
        f'stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{streak} 4000" stroke-dashoffset="{streak}">'
        f'<animate attributeName="stroke-dashoffset" values="{streak};{streak - path_length:.1f};{streak - path_length:.1f}" '
        f'keyTimes="0;0.6;1" {loop}/>'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.6;0.7;1" {loop}/></path>'
    )
    # The dot is placed at the answer, and the animation moves it back along the
    # path, so it still sits in the right place wherever animation is switched off.
    back_d = "M" + " L".join(f"{px - end_x:g} {py - end_y:g}" for px, py in path)
    dot = f'<circle r="10" fill="{t["spark"]}" opacity="0.22"/><circle r="4.2" fill="{t["spark"]}"/>'
    parts.append(
        f'<g transform="translate({end_x:g} {end_y:g})"><g class="still">{dot}</g><g class="motion">{dot}'
        f'<animateMotion path="{back_d}" keyPoints="0;1;1" keyTimes="0;0.6;1" calcMode="linear" {loop}/>'
        "</g></g>"
    )

    settings = GRAPH["settings"]
    description = (
        f"A real HNSW index of {settings['points']} points built by hnsw-engine, drawn as three layers. "
        "A highlighted path shows one search: it enters at the top layer, hops toward the query, "
        "drops a layer, and ends at the true nearest neighbour on the bottom layer."
    )
    return svg(TILE_W, HEADER_H, description, "".join(parts))


# ---------------------------------------------------------------------------
# Project tiles: one with the facts, one with a picture of the result
# ---------------------------------------------------------------------------

PROJECT_H = 330


def facts_tile(theme, kicker, title, summary, facts, description):
    """`summary` is two short lines; `facts` is three (value, meaning) pairs."""
    t = THEMES[theme]
    parts = [
        tile_outline(theme, PROJECT_H),
        text(LEFT, 50, kicker, 11, t["accent_text"], 600, family=MONO, spacing=1.4),
        text(LEFT - 1, 88, title, 28, t["ink"], 700, spacing=-0.5),
    ]
    for i, sentence in enumerate(summary):
        parts.append(text(LEFT, 116 + 21 * i, sentence, 14.5, t["ink2"]))
    for i, (value, meaning) in enumerate(facts):
        y = 200 + 44 * i
        parts.append(line(LEFT, y - 28, RIGHT, y - 28, t["border"]))
        parts.append(text(LEFT, y, value, 21, t["ink"], 700, spacing=-0.3))
        parts.append(text(LEFT + 100, y - 1, meaning, 13, t["ink2"]))
    return svg(TILE_W, PROJECT_H, description, "".join(parts))


def chart_start(theme, title, subtitle):
    t = THEMES[theme]
    return [
        tile_outline(theme, PROJECT_H),
        text(LEFT, 50, title, 14, t["ink"], 600),
        text(LEFT, 70, subtitle, 12, t["ink2"]),
    ]


def hnsw_facts(theme):
    return facts_tile(
        theme,
        "VECTOR SEARCH",
        "hnsw-engine",
        ["HNSW built from the original paper, twice:", "a readable reference and a compiled engine."],
        [
            ("4,447", "queries/s at recall ≥ 0.95, 1M vectors"),
            ("39×", "faster than exact search"),
            ("336", "tests; two engines, one graph"),
        ],
        "hnsw-engine: HNSW vector search built from the original paper, twice. 4,447 queries per second at recall "
        "0.95 or better on one million vectors, 39 times faster than exact search, 336 tests.",
    )


def hnsw_chart(theme):
    t = THEMES[theme]
    parts = chart_start(theme, "Queries per second at recall ≥ 0.95", "SIFT-1M  ·  recall@10  ·  one thread  ·  Apple M5")
    full_length = 300  # the longest bar
    biggest = max(qps for _, _, qps, _ in HNSW_QPS)
    for i, (name, kind, qps, mine) in enumerate(HNSW_QPS):
        y = 106 + 54 * i
        parts.append(
            f'<text x="{LEFT}" y="{y}" font-family="{SANS}" font-size="13">'
            f'<tspan font-weight="{700 if mine else 600}" fill="{t["ink"]}">{escape(name)}</tspan>'
            f'<tspan dx="7" font-size="12" fill="{t["ink2"]}">{escape(kind)}</tspan></text>'
        )
        length = full_length * qps / biggest
        parts.append(bar(LEFT, y + 9, length, 14, t["accent"] if mine else t["context"]))
        parts.append(text(LEFT + max(length, 3) + 8, y + 21, f"{qps:,}", 13, t["ink"], 700 if mine else 500))
    listing = "; ".join(f"{name} ({kind}) {qps:,}" for name, kind, qps, _ in HNSW_QPS)
    return svg(TILE_W, PROJECT_H, f"Queries per second at recall 0.95 or better on SIFT-1M, one thread: {listing}.", "".join(parts))


def recsys_facts(theme):
    return facts_tile(
        theme,
        "RECOMMENDER SYSTEMS",
        "two-stage-recsys",
        ["Two-tower retrieval served by hnsw-engine,", "then a LightGBM ranker, behind an API."],
        [
            ("0.0906", "NDCG@10 vs 0.0445 for tuned ALS"),
            ("0.1047", "NDCG@10 at ten times the data"),
            ("0.56 ms", "per request, measured server-side"),
        ],
        "two-stage-recsys: two-tower retrieval served by hnsw-engine, then a LightGBM ranker, behind an API. "
        "NDCG@10 of 0.0906 against 0.0445 for tuned ALS, 0.1047 at ten times the data, 0.56 ms per request.",
    )


def recsys_chart(theme):
    t = THEMES[theme]
    parts = chart_start(theme, "NDCG@10 on MovieLens-1M", "full-catalog ranking  ·  lines show 95% bootstrap intervals")
    per_unit = 290 / 0.10  # 290 wide for an NDCG of 0.10
    for i, (name, value, low, high, mine) in enumerate(RECSYS_NDCG):
        y = 100 + 37 * i
        parts.append(text(LEFT, y, name, 12.5, t["ink"] if mine else t["ink2"], 700 if mine else 400))
        parts.append(bar(LEFT, y + 7, per_unit * value, 12, t["accent"] if mine else t["context"]))
        low_x, high_x, mid_y = LEFT + per_unit * low, LEFT + per_unit * high, y + 13
        parts.append(line(low_x, mid_y, high_x, mid_y, t["ink"], 1.5))
        parts.append(line(low_x, mid_y - 3.5, low_x, mid_y + 3.5, t["ink"], 1.5))
        parts.append(line(high_x, mid_y - 3.5, high_x, mid_y + 3.5, t["ink"], 1.5))
        parts.append(text(high_x + 8, y + 17.5, f"{value:.4f}", 12.5, t["ink"], 700 if mine else 500))
    listing = "; ".join(f"{name} {value:.4f}" for name, value, _, _, _ in RECSYS_NDCG)
    return svg(TILE_W, PROJECT_H, f"NDCG@10 on MovieLens-1M with full-catalog ranking: {listing}.", "".join(parts))


# ---------------------------------------------------------------------------
# Footer: a thin line with a pulse in it
# ---------------------------------------------------------------------------


def footer(theme):
    t = THEMES[theme]
    blip = "l10 0 l7 -15 l10 28 l8 -21 l6 8 l10 0"
    whole = f"M0 24 H397 {blip} H846"
    parts = [
        f'<path d="{whole}" fill="none" stroke="{t["border"]}" stroke-width="1.2" stroke-linejoin="round"/>',
        f'<path d="M397 24 {blip}" fill="none" stroke="{t["accent"]}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>',
        f'<path class="motion" d="{whole}" fill="none" stroke="{t["spark"]}" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round" stroke-dasharray="70 4000" stroke-dashoffset="70">'
        '<animate attributeName="stroke-dashoffset" values="70;-870" dur="6s" repeatCount="indefinite"/></path>',
    ]
    return svg(846, 48, "A thin line with a pulse in it.", "".join(parts))


# ---------------------------------------------------------------------------

PICTURES = {
    "name": name_tile,
    "graph": graph_tile,
    "hnsw-engine-facts": hnsw_facts,
    "hnsw-engine-chart": hnsw_chart,
    "two-stage-recsys-facts": recsys_facts,
    "two-stage-recsys-chart": recsys_chart,
    "footer": footer,
}

if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    for old in ASSETS.glob("*.svg"):  # clear pictures left over from an earlier layout
        old.unlink()
    for name, draw in PICTURES.items():
        for theme in THEMES:
            path = ASSETS / f"{name}-{theme}.svg"
            path.write_text(draw(theme), encoding="utf-8")
            print(f"wrote {path.relative_to(ASSETS.parent)}")
