# Jadlo — Route Planner PoC

This repository contains a proof-of-concept backend for planning routes (GPX) with configurable user preferences (road priority, surface type, heatmap influence, street-view preference).

Note: This PoC uses `osmnx` for quick experimentation and validation of routing heuristics. For production, we recommend a dedicated routing engine (GraphHopper, Valhalla, OSRM, OpenRouteService) with prebuilt OSM extracts.

## What's in the repo

- `app/main.py` — minimal FastAPI app exposing a POST `/route` endpoint.
- `app/routing.py` — PoC logic for fetching a graph with `osmnx`, weighting edges, and generating GPX.
- `scripts/run_poc.py` — simple CLI to generate a single route and save GPX.
- `scripts/run_poc_segmented.py` — tool to split long routes into segments, generate each segment and stitch GPX together (useful in resource-constrained environments).
- `requirements.txt` — Python dependency list.

## Example outputs

- `poc_route_3km.gpx` — example route generated with a small radius (3 km) — useful for testing in constrained environments.
- `poc_route_100km_segmented.gpx` — example stitched route produced by running the segmented runner (executed in Codespace using `scripts/run_poc_segmented.py`).

## Quick start (locally / in Codespace)

1) Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Note: `osmnx` requires native libraries (GEOS/PROJ/GDAL). In Codespace or CI use a container image with these libraries preinstalled.

2) Run the FastAPI server (locally):

```bash
uvicorn app.main:app --reload
```

3) Example POST `/route` (JSON):

```json
{
	"start": [52.2297, 21.0122],
	"end": [53.1325, 23.1688],
	"params": { "prefer_main_roads": 0.5, "prefer_unpaved": 0.2, "heatmap_influence": 0.0 }
}
```

4) Quick CLI runs (single segment and segmented runner):

```bash
# single small segment
PYTHONPATH=. python scripts/run_poc.py --start 52.2297 21.0122 --end 52.3300 21.2518 --radius 3000 --out poc_route_3km.gpx

# or: split a long route into segments and stitch GPX (example run in Codespace):
PYTHONPATH=. python scripts/run_poc_segmented.py --start 52.2297 21.0122 --end 53.1325 23.1688 --segment-km 20 --radius 8000 --out poc_route_100km_segmented.gpx
```

## Technical notes & limitations

- `osmnx` and the Overpass API: downloading a large OSM area can be memory-intensive and may hit Overpass limits (504/429). For long routes we use segmentation or a dedicated routing server.
- Caching and backoff: the segmented runner caches responses and does simple retries, but production systems should implement stronger caching and backoff strategies.
- Licensing: OSM data is licensed under ODbL — ensure proper attribution.

## Next steps

- Parameterize the API/UI (weight profiles, sliders) — add endpoints and a simple Leaflet demo.
- Integrate with Mapillary / Google Street View (check imagery coverage for route segments).
- Migrate to a dedicated routing engine (prebuilt graph and server) for production scalability.

---

File updated: added CLI usage instructions and notes about generated GPX files.

## Debugging in VS Code

If you want to run or debug the tests (or scripts) from VS Code and avoid "No module named 'app'" errors, make sure the workspace root is on Python's import path. This repo includes a sample VS Code launch configuration in `.vscode/launch.json` that sets `PYTHONPATH` and the working directory to the workspace root. Choose the "Python: Debug pytest single test (module)" configuration to run the integration test `tests/test_generate_100km.py::test_generate_100km_and_write_artifact`.

Alternatively, run tests from a terminal where the project root is on `PYTHONPATH`:

```bash
PYTHONPATH=. python -m pytest tests/test_generate_100km.py::test_generate_100km_and_write_artifact -q
```

The debugger or terminal must also use the Python interpreter that has `osmnx` and other dependencies installed.

## Running tests

- Fast unit/smoke tests (no network) run quickly. Integration tests in `tests/` may fetch OSM data and can take minutes or be skipped when `osmnx` is unavailable.
- To run all tests quickly (skip long integration ones), use pytest markers or run individual test files.

## Artifacts and cache

- Generated GPX artifacts are written to `artifacts/` by some integration scripts/tests. This repository already includes `.gitignore` entries to ignore `artifacts/` and `cache/`.
- If you accidentally committed large Overpass cache files (in `cache/`) you should remove them from the index and rewrite history or adopt Git LFS. To untrack the cached files without deleting them locally:

```bash
git rm --cached -r cache/
git commit -m "chore: untrack overpass cache files"
git push origin main
```

## Notes about long runs

- Long routes may hit Overpass rate limits or be memory-heavy. Prefer the segmented runner (`scripts/run_poc_segmented.py`) or the intersection-based routing (`compute_route_intersections`) implemented in `app/routing.py` for lower memory use.
- For reproducible development, consider using a container image with GEOS/PROJ/GDAL preinstalled (required by `osmnx`).

## Experimental routing: intersection-based A* (experimental / not yet merged)

An experimental routing mode has been developed to reduce memory usage and make routing decisions only at intersections. Instead of running shortest-path on the full OSMnx node graph (which includes many degree-2 nodes along road polylines), this approach:

- Collapses degree-2 chain nodes and simplifies the graph to intersection-level nodes.
- Aggregates geometry and length for the collapsed chains so each simplified edge represents a road segment between two intersections.
- Runs an A* search on the simplified intersection graph. The heuristic is geographic (haversine). An optional heading bias penalizes turns that diverge strongly from the incoming bearing so the algorithm prefers to "stay on" the same road when it roughly points toward the destination.

Why this helps
- Much lower memory and CPU when fetching and routing on large areas — good for Codespace / constrained environments.
- Fewer decision points: decisions are made at intersections instead of every vertex along a polyline, reducing noisy off-road detours.

Key parameters and tuning
- `radius_meters` — OSM fetch radius used to build a local graph for a segment. Larger values cover more road context but use more memory.
- `heading_threshold_deg` — how strict the heading bias is (smaller = stronger preference to continue straight). Typical values: 30–60 degrees.
- `prefer_main_roads`, `prefer_unpaved`, `heatmap_influence`, `prefer_streetview` — same user-weight parameters used by the PoC edge-weight function; they influence the edge penalty multiplier.

Typical usage (Python API example)

```python
from app.routing import compute_route_intersections

start = (52.2297, 21.0122)
end = (53.1325, 23.1688)
params = {
	'prefer_main_roads': 0.5,
	'prefer_unpaved': 0.2,
	'heatmap_influence': 0.0,
	'prefer_streetview': 0.0,
}

# returns (coords_list, gpx_xml_string)
coords, gpx_xml = compute_route_intersections(start, end, params, radius_meters=8000, heading_threshold_deg=45)

# write GPX if desired
with open('artifacts/poc_route_intersections.gpx', 'w', encoding='utf-8') as f:
	f.write(gpx_xml)
```

Caveats
- Experimental: this mode may produce gaps if the Overpass fetch for a segment fails or returns incomplete data — use the segmented runner as a fallback.
- May need parameter tuning per region (urban vs rural) — e.g., increase `radius_meters` in rural areas where intersections are sparse.
- The heading bias is a heuristic; it can reduce undesirable short detours but may sometimes prefer a longer straight segment improperly. Tweak `heading_threshold_deg` and user weights to adjust behavior.

If you'd like, I can add a short example script that runs `compute_route_intersections` for a multi-segment 100 km flow (similar to `scripts/run_poc_segmented.py`) and writes the artifact to `artifacts/`.



## Release notes (recent)

Version: experimental / PoC

- Improved segment stitching and GPX reconstruction
	- The segmented runner and test harness now attempt to bridge large gaps between adjacent route segments by:
		- first trying to bridge using the intersection-simplified graph (fast, low-memory),
		- falling back to routing on the original OSMnx graph for that subsegment when needed,
		- dividing very large gaps into smaller subsegments and routing each piece if a single bridge fails.
	- As part of this work, the intersection-graph simplifier now prefers original edge geometries (LineString) when aggregating degree-2 chains, preserving road curvature instead of straight-line shortcuts.
	- The result: the generated GPX artifacts no longer contain long straight-line jumps between segments — routes follow available road geometries more closely.

- Tests & artifacts
	- The integration test `tests/test_generate_100km.py::test_generate_100km_and_write_artifact` was updated to include improved stitching and post-processing repair of large gaps. Running the test produces `artifacts/poc_route_100km_intersections.gpx`.

- Caveats
	- This is still a PoC: the approach relies on Overpass/OSMnx responses and may be sensitive to missing data or Overpass limits. The segmented runner and retries mitigate many issues but do not eliminate them.

Suggested commit message used for this change:

```
chore(release): improve segment stitching and GPX reconstruction

- bridge large gaps between segments using intersection or original-graph routing
- prefer original edge geometries when reconstructing GPX to avoid straight-line jumps
- update integration test to write repaired artifact
```


