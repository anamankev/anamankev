#!/usr/bin/env python3
"""Draws every picture used by README.md and saves it in assets/.

Run it from anywhere:

    python3 tools/build_assets.py

Each picture is drawn twice, once for GitHub's light theme and once for its
dark theme. The numbers in the charts are typed in below, each next to the
file it was copied from, so a chart only changes when its source does.

The pictures are SVG files: plain text that describes shapes, which the
browser draws at any size without blurring.
"""

from html import escape
from math import dist
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

# One set of colours per GitHub theme. The greys are GitHub's own, so the
# pictures sit on the page as if they were part of it.
THEMES = {
    "light": {
        "ink": "#1f2328",  # main text
        "ink2": "#59636e",  # secondary text
        "card": "#f6f8fa",  # card background
        "border": "#d1d9e0",  # card outline and thin rules
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
    """A horizontal bar: square where it meets the baseline, rounded at the data end."""
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


# ---------------------------------------------------------------------------
# Header: my name beside an HNSW graph being searched
# ---------------------------------------------------------------------------

HEADER_W, HEADER_H = 880, 280

# The three layers are drawn as slanted sheets, top layer first.
SHEET_LEFT, SHEET_WIDTH, SHEET_SLANT, SHEET_HEIGHT = 552, 236, 78, 60
SHEET_TOP = {2: 22, 1: 110, 0: 198}

# Where each node sits on a sheet: across (0 = left, 1 = right), down (0 = top, 1 = bottom).
NODES = {
    0: (0.07, 0.30),
    1: (0.17, 0.74),
    2: (0.26, 0.24),
    3: (0.36, 0.60),
    4: (0.46, 0.16),
    5: (0.49, 0.84),
    6: (0.58, 0.42),
    7: (0.71, 0.66),
    8: (0.75, 0.18),
    9: (0.88, 0.46),
    10: (0.95, 0.82),
    11: (0.63, 0.90),
    12: (0.30, 0.88),
    13: (0.10, 0.56),
    14: (0.92, 0.16),
}
# As in HNSW, every node is on layer 0 and each higher layer keeps fewer of them.
LAYER_NODES = {0: list(NODES), 1: [1, 2, 3, 6, 7, 9], 2: [2, 6, 9]}
NEIGHBOURS = {0: 3, 1: 2, 2: 2}  # links drawn per node on each layer

# The search: enter at the top, hop to the node nearest the query, drop a layer, repeat.
SEARCH = [(2, 2), (2, 6), (1, 6), (1, 7), (0, 7), (0, 11)]  # (layer, node)


def node_xy(layer, node):
    across, down = NODES[node]
    x = SHEET_LEFT + SHEET_SLANT * (1 - down) + SHEET_WIDTH * across
    y = SHEET_TOP[layer] + SHEET_HEIGHT * down
    return round(x, 1), round(y, 1)


def layer_links(layer):
    """Join every node on a layer to its nearest few neighbours, plus the search hops."""
    nodes = LAYER_NODES[layer]
    links = set()
    for a in nodes:
        nearest = sorted((b for b in nodes if b != a), key=lambda b: dist(node_xy(layer, a), node_xy(layer, b)))
        links.update(tuple(sorted((a, b))) for b in nearest[: NEIGHBOURS[layer]])
    for (layer_a, a), (layer_b, b) in zip(SEARCH, SEARCH[1:]):
        if layer_a == layer_b == layer:
            links.add(tuple(sorted((a, b))))
    return sorted(links)


def header(theme):
    t = THEMES[theme]
    parts = []

    # Soft glow behind the graph.
    parts.append(
        '<defs><radialGradient id="glow" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0" stop-color="{t["accent"]}" stop-opacity="{t["glow"]}"/>'
        f'<stop offset="1" stop-color="{t["accent"]}" stop-opacity="0"/></radialGradient></defs>'
        '<ellipse cx="708" cy="140" rx="230" ry="150" fill="url(#glow)"/>'
    )

    # Left side: who I am.
    parts.append(text(1, 62, "CS + APPLIED MATH  ·  BRANDEIS ’30  ·  BOSTON", 12, t["accent_text"], 600, family=MONO, spacing=1.5))
    parts.append(text(-2, 128, "Kelvin Anaman", 60, t["ink"], 700, spacing=-1.6))
    parts.append(text(1, 170, "ML systems built from the paper up,", 19, t["ink2"]))
    parts.append(text(1, 196, "measured against the best libraries.", 19, t["ink2"]))
    x = 1
    for label, highlighted in [("Founder, Pulse Energies", True), ("Wien Scholar", False)]:
        width = round(len(label) * 7.1 + (38 if highlighted else 26))
        parts.append(
            f'<rect x="{x + 0.5}" y="222.5" width="{width}" height="28" rx="14" fill="none" stroke="{t["border"]}"/>'
        )
        if highlighted:
            parts.append(f'<circle cx="{x + 16}" cy="236.5" r="3.5" fill="{t["accent"]}"/>')
        text_x = x + (width + (12 if highlighted else 0)) / 2
        parts.append(text(text_x, 241, label, 12.5, t["ink2"], 500, anchor="middle"))
        x += width + 8

    # Right side: the three sheets, their names, and the links on each.
    for layer in (2, 1, 0):
        top, bottom = SHEET_TOP[layer], SHEET_TOP[layer] + SHEET_HEIGHT
        corners = [
            (SHEET_LEFT + SHEET_SLANT, top),
            (SHEET_LEFT + SHEET_SLANT + SHEET_WIDTH, top),
            (SHEET_LEFT + SHEET_WIDTH, bottom),
            (SHEET_LEFT, bottom),
        ]
        points = " ".join(f"{px},{py}" for px, py in corners)
        parts.append(
            f'<polygon points="{points}" fill="{t["card"]}" stroke="{t["border"]}" stroke-linejoin="round"/>'
        )
        parts.append(
            text(SHEET_LEFT + SHEET_SLANT / 2 - 14, top + SHEET_HEIGHT / 2 + 4, f"L{layer}", 11, t["ink2"], 500, "end", MONO)
        )
        for a, b in layer_links(layer):
            parts.append(line(*node_xy(layer, a), *node_xy(layer, b), t["edge"]))

    # Faint uprights: the same node seen on the layer below.
    for upper, lower in ((2, 1), (1, 0)):
        for node in LAYER_NODES[upper]:
            parts.append(line(*node_xy(upper, node), *node_xy(lower, node), t["edge"], 1, 0.45))

    # The search path, drawn under the nodes.
    route = [node_xy(layer, node) for layer, node in SEARCH]
    route_d = "M" + " L".join(f"{px:g} {py:g}" for px, py in route)
    route_length = sum(dist(a, b) for a, b in zip(route, route[1:]))
    parts.append(
        f'<path d="{route_d}" fill="none" stroke="{t["accent"]}" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" opacity="0.6"/>'
    )

    # Nodes. A ring in the sheet colour keeps each one clear of the lines under it.
    on_route = set(SEARCH)
    for layer in (2, 1, 0):
        radius = {2: 4.2, 1: 3.8, 0: 3.4}[layer]
        for node in LAYER_NODES[layer]:
            px, py = node_xy(layer, node)
            hit = (layer, node) in on_route
            parts.append(
                f'<circle cx="{px:g}" cy="{py:g}" r="{radius + (0.8 if hit else 0):g}" '
                f'fill="{t["accent"] if hit else t["context"]}" stroke="{t["card"]}" stroke-width="1.5"/>'
            )

    # The answer: the last node on the path, with a ring that breathes.
    end_x, end_y = route[-1]
    parts.append(
        f'<circle class="motion" cx="{end_x:g}" cy="{end_y:g}" r="6" fill="none" stroke="{t["spark"]}" stroke-width="1.5">'
        '<animate attributeName="r" values="6;15" dur="2.4s" repeatCount="indefinite"/>'
        '<animate attributeName="opacity" values="0.7;0" dur="2.4s" repeatCount="indefinite"/></circle>'
    )
    parts.append(text(end_x + 13, end_y + 4, "nearest", 10.5, t["ink2"], 500, family=MONO))

    # A bright streak and a dot that run along the path, rest at the answer, then repeat.
    loop = 'dur="7s" repeatCount="indefinite"'
    streak = 46
    parts.append(
        f'<path class="motion" d="{route_d}" fill="none" stroke="{t["spark"]}" stroke-width="2.6" '
        f'stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{streak} 4000" stroke-dashoffset="{streak}">'
        f'<animate attributeName="stroke-dashoffset" values="{streak};{streak - route_length:.1f};{streak - route_length:.1f}" '
        f'keyTimes="0;0.55;1" {loop}/>'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.55;0.66;1" {loop}/></path>'
    )
    # The dot is placed at the answer, and the animation moves it back along the
    # path, so it still sits in the right place wherever animation is switched off.
    back_d = "M" + " L".join(f"{px - end_x:g} {py - end_y:g}" for px, py in route)
    dot = f'<circle r="11" fill="{t["spark"]}" opacity="0.22"/><circle r="4.6" fill="{t["spark"]}"/>'
    parts.append(
        f'<g transform="translate({end_x:g} {end_y:g})"><g class="still">{dot}</g><g class="motion">{dot}'
        f'<animateMotion path="{back_d}" keyPoints="0;1;1" keyTimes="0;0.55;1" calcMode="linear" {loop}/>'
        "</g></g>"
    )

    description = (
        "Kelvin Anaman. ML systems built from the paper up, measured against the best libraries. "
        "Computer science and applied math, Brandeis class of 2030. Founder of Pulse Energies. "
        "Illustration: a search descending the three layers of an HNSW graph."
    )
    return svg(HEADER_W, HEADER_H, description, "".join(parts))


# ---------------------------------------------------------------------------
# Project cards: facts on the left, a picture of the result on the right
# ---------------------------------------------------------------------------

CARD_W, CARD_H = 880, 300
CHART_X = 404  # where the right-hand side starts


def card_start(theme, kicker, title, summary, facts):
    """The card outline and its left half. `facts` is three (value, meaning) pairs."""
    t = THEMES[theme]
    parts = [
        f'<rect x="0.5" y="0.5" width="{CARD_W - 1}" height="{CARD_H - 1}" rx="14" fill="{t["card"]}" stroke="{t["border"]}"/>',
        text(32, 46, kicker, 11, t["accent_text"], 600, family=MONO, spacing=1.4),
        text(31, 82, title, 27, t["ink"], 700, spacing=-0.5),
    ]
    for i, sentence in enumerate(summary):
        parts.append(text(32, 108 + 20 * i, sentence, 14, t["ink2"]))
    for i, (value, meaning) in enumerate(facts):
        y = 182 + 40 * i
        parts.append(line(32, y - 25, 352, y - 25, t["border"]))
        parts.append(text(32, y, value, 20, t["ink"], 700, spacing=-0.3))
        parts.append(text(128, y - 1, meaning, 12.5, t["ink2"]))
    parts.append(line(378, 32, 378, CARD_H - 32, t["border"]))
    return parts


def chart_heading(theme, title, subtitle):
    t = THEMES[theme]
    return [
        text(CHART_X, 46, title, 13.5, t["ink"], 600),
        text(CHART_X, 65, subtitle, 12, t["ink2"]),
    ]


def hnsw_card(theme):
    t = THEMES[theme]
    parts = card_start(
        theme,
        "VECTOR SEARCH",
        "hnsw-engine",
        ["HNSW built from the original paper, twice:", "a readable reference and a compiled engine."],
        [
            ("4,447", "queries/s at recall ≥ 0.95, 1M vectors"),
            ("39×", "faster than exact search"),
            ("336", "tests; two engines, one graph"),
        ],
    )
    parts += chart_heading(theme, "Queries per second at recall ≥ 0.95", "SIFT-1M  ·  recall@10  ·  one thread  ·  Apple M5")

    bar_x, full_length = 524, 250
    biggest = max(qps for _, _, qps, _ in HNSW_QPS)
    parts.append(line(bar_x, 86, bar_x, 262, t["border"]))
    for i, (name, kind, qps, mine) in enumerate(HNSW_QPS):
        y = 108 + 44 * i
        parts.append(text(CHART_X, y, name, 13, t["ink"], 600 if mine else 500))
        parts.append(text(CHART_X, y + 15, kind, 11, t["ink2"]))
        length = full_length * qps / biggest
        parts.append(bar(bar_x, y - 9, length, 16, t["accent"] if mine else t["context"]))
        parts.append(text(bar_x + max(length, 3) + 8, y + 4, f"{qps:,}", 13, t["ink"], 700 if mine else 500))

    listing = "; ".join(f"{name} ({kind}) {qps:,}" for name, kind, qps, _ in HNSW_QPS)
    description = (
        "hnsw-engine: HNSW vector search built from the original paper. "
        f"Queries per second at recall 0.95 or better on SIFT-1M, one thread: {listing}."
    )
    return svg(CARD_W, CARD_H, description, "".join(parts))


def recsys_card(theme):
    t = THEMES[theme]
    parts = card_start(
        theme,
        "RECOMMENDER SYSTEMS",
        "two-stage-recsys",
        ["Two-tower retrieval served by hnsw-engine,", "then a LightGBM ranker, behind an API."],
        [
            ("0.0906", "NDCG@10 vs 0.0445 for tuned ALS"),
            ("0.1047", "NDCG@10 at ten times the data"),
            ("0.56 ms", "per request, measured server-side"),
        ],
    )
    parts += chart_heading(theme, "NDCG@10 on MovieLens-1M", "full-catalog ranking  ·  lines show 95% bootstrap intervals")

    bar_x, per_unit = 606, 180 / 0.10  # 180 pixels for an NDCG of 0.10
    parts.append(line(bar_x, 84, bar_x, 268, t["border"]))
    for i, (name, value, low, high, mine) in enumerate(RECSYS_NDCG):
        y = 104 + 30 * i
        parts.append(text(CHART_X, y, name, 12.5, t["ink"] if mine else t["ink2"], 600 if mine else 400))
        parts.append(bar(bar_x, y - 11, per_unit * value, 14, t["accent"] if mine else t["context"]))
        low_x, high_x, mid_y = bar_x + per_unit * low, bar_x + per_unit * high, y - 4
        parts.append(line(low_x, mid_y, high_x, mid_y, t["ink"], 1.5))
        parts.append(line(low_x, mid_y - 3.5, low_x, mid_y + 3.5, t["ink"], 1.5))
        parts.append(line(high_x, mid_y - 3.5, high_x, mid_y + 3.5, t["ink"], 1.5))
        parts.append(text(high_x + 8, y, f"{value:.4f}", 12.5, t["ink"], 700 if mine else 500))

    listing = "; ".join(f"{name} {value:.4f}" for name, value, _, _, _ in RECSYS_NDCG)
    description = (
        "two-stage-recsys: two-tower retrieval served by hnsw-engine, then a LightGBM ranker. "
        f"NDCG@10 on MovieLens-1M with full-catalog ranking: {listing}."
    )
    return svg(CARD_W, CARD_H, description, "".join(parts))


# ---------------------------------------------------------------------------
# Footer: a thin line with a pulse in it
# ---------------------------------------------------------------------------


def footer(theme):
    t = THEMES[theme]
    blip = "l10 0 l7 -15 l10 28 l8 -21 l6 8 l10 0"
    whole = f"M0 24 H414 {blip} H880"
    parts = [
        f'<path d="{whole}" fill="none" stroke="{t["border"]}" stroke-width="1.2" stroke-linejoin="round"/>',
        f'<path d="M414 24 {blip}" fill="none" stroke="{t["accent"]}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>',
        f'<path class="motion" d="{whole}" fill="none" stroke="{t["spark"]}" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round" stroke-dasharray="70 4000" stroke-dashoffset="70">'
        '<animate attributeName="stroke-dashoffset" values="70;-900" dur="6s" repeatCount="indefinite"/></path>',
    ]
    return svg(880, 48, "A thin line with a pulse in it.", "".join(parts))


# ---------------------------------------------------------------------------

PICTURES = {
    "header": header,
    "card-hnsw-engine": hnsw_card,
    "card-two-stage-recsys": recsys_card,
    "footer": footer,
}

if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    for name, draw in PICTURES.items():
        for theme in THEMES:
            path = ASSETS / f"{name}-{theme}.svg"
            path.write_text(draw(theme), encoding="utf-8")
            print(f"wrote {path.relative_to(ASSETS.parent)}")
