
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

