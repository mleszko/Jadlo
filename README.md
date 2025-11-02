# Jadlo — Route Planner PoC

This repository contains a proof-of-concept route planner for generating GPX routes with configurable user preferences (road priority, surface type, heatmap influence, street-view preference).

**🌐 Try it now!** The repository includes a beautiful web interface that lets users generate custom GPX routes without any installation.

**Quick Deploy Options:**

**⭐ Oracle Cloud (Best - 24GB RAM Free):**
```bash
# One command setup on Oracle Cloud (Ubuntu instance):
curl -fsSL https://raw.githubusercontent.com/mleszko/Jadlo/main/scripts/setup_oracle.sh | bash
```
See [DEPLOYMENT_ORACLE.md](DEPLOYMENT_ORACLE.md) for full guide.

**Render.com (Quick testing):**
1. Fork this repository
2. Sign up at [render.com](https://render.com)
3. Create new Web Service from your fork
4. Render auto-detects `render.yaml` and deploys!
5. Access your app at `https://your-app-name.onrender.com`

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions and more hosting options (Railway, Fly.io, GitHub Pages).

Note: This PoC uses `osmnx` for quick experimentation and validation of routing heuristics. For production, we recommend a dedicated routing engine (GraphHopper, Valhalla, OSRM, OpenRouteService) with prebuilt OSM extracts.

## Algorithm Choice: Dijkstra's Algorithm & A*

The routing implementation uses **Dijkstra's algorithm** (via NetworkX's `shortest_path`) for standard routing and **A*** for intersection-based routing. These algorithms are well-suited for finding optimal routes based on weighted edge values.

**Why Dijkstra/A*?**
- Both algorithms guarantee finding the optimal path based on edge weights
- Dijkstra's algorithm explores all possible paths efficiently
- A* adds a geographic heuristic for faster computation in intersection-based routing
- They naturally support custom edge weights that combine multiple factors (distance, surface, road type)

**Surface-Based Route Calculation:**
The route value calculation emphasizes **surface type** as a primary factor:
- Each surface type (asphalt, gravel, dirt, etc.) has a penalty multiplier
- The `surface_weight_factor` parameter controls how strongly surface influences route selection
- Higher values (e.g., 2.0) mean surface quality dominates route choice
- Lower values (e.g., 0.5) mean distance becomes relatively more important
- The algorithm finds the optimal balance between distance and surface preference

## What's in the repo

- `app/main.py` — FastAPI app with web interface and POST `/route` endpoint.
- `app/routing.py` — PoC logic for fetching a graph with `osmnx`, weighting edges, and generating GPX.
- `static/index.html` — **Web interface** for generating GPX routes with interactive map and parameter controls.
- `scripts/run_poc.py` — simple CLI to generate a single route and save GPX.
- `scripts/run_poc_segmented.py` — tool to split long routes into segments, generate each segment and stitch GPX together (useful in resource-constrained environments).
- `requirements.txt` — Python dependency list.
- `DEPLOYMENT.md` — **Complete guide for deploying to free hosting services** (Render, Railway, GitHub Pages).

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

3) **Access the web interface**:

Open your browser and go to `http://localhost:8000` to use the interactive web interface with map and parameter controls.

Alternatively, use the API directly with POST `/route` (JSON):

```json
{
	"start": [52.2297, 21.0122],
	"end": [53.1325, 23.1688],
	"params": { 
		"prefer_main_roads": 0.5, 
		"prefer_unpaved": 0.2, 
		"heatmap_influence": 0.0,
		"surface_weight_factor": 1.5
	}
}
```

**Parameter guide for surface-based routing:**
- `surface_weight_factor`: 1.0 = default balance, 2.0 = strongly prefer better surfaces, 0.5 = prioritize shorter distance
- `prefer_unpaved`: 1.0 = prefer gravel/dirt, 0.0 = avoid unpaved surfaces
- `prefer_main_roads`: 1.0 = prefer highways, 0.0 = prefer smaller roads

4) Quick CLI runs (single segment and segmented runner):

```bash
# single small segment
PYTHONPATH=. python scripts/run_poc.py --start 52.2297 21.0122 --end 52.3300 21.2518 --radius 3000 --out poc_route_3km.gpx

# or: split a long route into segments and stitch GPX (example run in Codespace):
PYTHONPATH=. python scripts/run_poc_segmented.py --start 52.2297 21.0122 --end 53.1325 23.1688 --segment-km 20 --radius 8000 --out poc_route_100km_segmented.gpx
```

## Web Interface

The repository includes a beautiful, user-friendly web interface for generating custom GPX routes:

**Features:**
- 🗺️ **Interactive Map**: Click to set start and end points, or enter coordinates manually
- 🎚️ **Parameter Controls**: Sliders for all routing parameters with real-time values
- 📍 **Preset Routes**: Quick load common route examples (Warsaw, Short, Long)
- 💾 **Download GPX**: Generate and download GPX files directly
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 📖 **Built-in Guide**: Parameter explanations and usage instructions

**How to use:**
1. Start the server: `uvicorn app.main:app --reload`
2. Open browser: `http://localhost:8000`
3. Click map or enter coordinates for start/end points
4. Adjust parameters using sliders
5. Click "Generate GPX Route"
6. Download the generated GPX file

**Deploy for free hosting:**
See [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step instructions to deploy on:
- Render.com (recommended - hosts both API and web interface)
- Railway.app
- GitHub Pages + separate backend
- Fly.io

## Testing in Codespaces

GitHub Codespaces provides a cloud-based development environment that's perfect for testing Jadlo. The Codespace comes with Python and system dependencies (GEOS/PROJ/GDAL) pre-installed.

### Quick Test (One Command)

To quickly test route generation in a Codespace, run:

```bash
PYTHONPATH=. python scripts/test_codespace.py
```

This will:
- Generate a short ~10km test route in the Warsaw area
- Save the result as `test_route_codespace.gpx`
- Complete in 30-60 seconds
- Print success message with route details

### Running Other Examples in Codespace

After testing with the quick script, you can try other examples:

```bash
# Small route (fast, ~1-2 minutes)
PYTHONPATH=. python scripts/run_poc.py --start 52.2297 21.0122 --end 52.3300 21.2518 --radius 3000 --out poc_route_3km.gpx

# Long segmented route (slower, ~5-10 minutes)
PYTHONPATH=. python scripts/run_poc_segmented.py --start 52.2297 21.0122 --end 53.1325 23.1688 --segment-km 20 --radius 8000 --out poc_route_100km_segmented.gpx
```

**Codespace Tips:**
- The first run may take longer as OSMnx downloads and caches OpenStreetMap data
- Cached data is stored in the `cache/` directory for faster subsequent runs
- For long routes, use the segmented runner to avoid memory issues
- Generated GPX files can be downloaded from the Codespace file explorer

## Technical notes & limitations

- `osmnx` and the Overpass API: downloading a large OSM area can be memory-intensive and may hit Overpass limits (504/429). For long routes we use segmentation or a dedicated routing server.
- Caching and backoff: the segmented runner caches responses and does simple retries, but production systems should implement stronger caching and backoff strategies.
- Licensing: OSM data is licensed under ODbL — ensure proper attribution.

## Documentation

For more detailed information:
- [ROUTING_ALGORITHMS_COMPARISON.md](docs/ROUTING_ALGORITHMS_COMPARISON.md) - Comprehensive comparison of Jadlo's approach with academic research, commercial applications (Strava, Komoot, Google Maps, Apple Maps, etc.), OSM routing engines, and LLM-based routing
- [ALGORITHM_CHOICE.md](docs/ALGORITHM_CHOICE.md) - Detailed explanation of why Dijkstra's algorithm is used
- [APPLICATION_DOCUMENTATION.md](docs/APPLICATION_DOCUMENTATION.md) - Complete technical documentation
- [INTEGRATION_TESTS.md](docs/INTEGRATION_TESTS.md) - Testing documentation

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

### Unit tests (fast)
Run unit tests that don't require network access:
```bash
PYTHONPATH=. python -m pytest tests/test_weight.py tests/test_routing.py tests/test_surface_routing.py -v
```

### Regression tests (fast)
Run regression tests to ensure GPX generation and parameter behavior remains stable:
```bash
# Using the convenience script
./scripts/run_regression_tests.sh

# Or directly with pytest
PYTHONPATH=. python -m pytest tests/test_gpx_regression.py -v
```

These tests validate:
- GPX XML structure and format compliance
- Parameter consistency (same input produces consistent output)
- Route quality (coordinates, ordering, no duplicates)
- Edge weight calculation stability across code changes
- All parameter combinations work correctly

**Use case:** Run regression tests before testing new settings or algorithms to ensure existing functionality still works correctly.

### Integration tests (require network)
Integration tests fetch OSM data and may take several minutes:

```bash
# Run all integration tests
PYTHONPATH=. python -m pytest -m integration -v -s

# Run specific integration test suites
PYTHONPATH=. python -m pytest tests/test_integration_requirements.py -v -s
PYTHONPATH=. python -m pytest tests/test_generate_100km.py -v -s
```

**Integration test requirements (see `docs/INTEGRATION_TESTS.md`):**
1. Performance: 100km route generation < 3 minutes
2. Quality: No gaps > 1km in routes
3. Surface preference: >80% paved roads with high surface_weight_factor

**Note:** These integration tests are automatically run by GitHub Actions on every commit to ensure code quality. See `.github/workflows/README.md` for details about the CI/CD pipeline.

### Skip integration tests
```bash
PYTHONPATH=. python -m pytest -m "not integration" -v
```

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


