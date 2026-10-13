#!/usr/bin/env python3
"""Builds a small real HNSW index with hnsw-engine and records one search through it.

The header picture on the profile is drawn from this file's output, so the
graph beside my name is an actual index and an actual search, not a sketch.

It needs hnsw-engine installed, so run it with that project's Python:

    ../HNSW/.venv/bin/python tools/trace_search.py

It writes tools/header_graph.json. Then run tools/build_assets.py to redraw.
"""

import json
from pathlib import Path

import numpy as np
from hnsw_engine import HNSWIndex, __version__, exact_search

OUTPUT = Path(__file__).resolve().parent / "header_graph.json"

# Small on purpose: 40 points and at most 3 links per node (6 on layer 0) is
# about as much as a picture this size can show clearly.
COLUMNS, ROWS = 8, 5
M = 3
EF_CONSTRUCTION = 40
SEED = 122  # chosen so the index has three layers and the search hops on each one
QUERY = [0.687, 0.619]


def make_points(seed):
    """One point in each cell of an 8 x 5 grid, nudged at random inside its cell."""
    rng = np.random.default_rng(seed)
    count = COLUMNS * ROWS
    column, row = np.meshgrid(np.arange(COLUMNS), np.arange(ROWS))
    x = (column.ravel() + rng.uniform(0.15, 0.85, count)) / COLUMNS
    y = (row.ravel() + rng.uniform(0.15, 0.85, count)) / ROWS
    return np.stack([x, y], axis=1).astype("float32")


def squared_distance(a, b):
    return float(((a - b) ** 2).sum())


def replay_search(state, points, query):
    """Follow the search the engine runs for k=1, ef=1 and list every node it moves to.

    The engine returns only the answer, not the path. With a beam of one the
    path is fully determined by the graph: start at the entry point, move to
    the neighbour closest to the query while one is closer, then drop a layer.
    """
    here = state.entry_point
    route = []
    for layer in range(state.max_level, -1, -1):
        links = state.adjacency(layer)
        route.append([layer, here])
        while True:
            closest = min(links[here], key=lambda node: squared_distance(points[node], query), default=here)
            if squared_distance(points[closest], query) < squared_distance(points[here], query):
                here = closest
                route.append([layer, here])
            else:
                break
    return route


if __name__ == "__main__":
    points = make_points(SEED)
    query = np.array(QUERY, dtype="float32")

    index = HNSWIndex(dim=2, metric="l2", M=M, ef_construction=EF_CONSTRUCTION, seed=SEED, engine="reference")
    index.add(points)
    state = index.graph_state()

    route = replay_search(state, points, query)
    found = int(np.ravel(index.search(query, k=1, ef=1)[0])[0])
    truth = int(np.ravel(exact_search(points, query[None, :], 1, "l2")[0])[0])
    # The replayed path must end where the engine's own search ends, and that
    # must be the true nearest neighbour. Otherwise the picture would be wrong.
    assert route[-1][1] == found == truth, (route[-1][1], found, truth)

    layers = []
    for layer in range(state.max_level + 1):
        links = state.adjacency(layer)
        pairs = sorted({tuple(sorted((a, b))) for a, neighbours in links.items() for b in neighbours})
        layers.append({"nodes": sorted(links), "links": pairs})

    record = {
        "made_by": f"tools/trace_search.py with hnsw-engine {__version__} (reference engine)",
        "settings": {"points": len(points), "M": M, "ef_construction": EF_CONSTRUCTION, "seed": SEED},
        "points": [[round(float(x), 4), round(float(y), 4)] for x, y in points],
        "layers": layers,
        "entry_point": int(state.entry_point),
        "query": QUERY,
        "route": route,
        "nearest": found,
    }
    OUTPUT.write_text(json.dumps(record, separators=(",", ":")) + "\n", encoding="utf-8")
    sizes = ", ".join(f"layer {i}: {len(l['nodes'])} nodes, {len(l['links'])} links" for i, l in enumerate(layers))
    print(f"wrote {OUTPUT.name}  ({sizes}; route of {len(route)} nodes ends at the true nearest neighbour, node {found})")
