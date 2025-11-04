# Prebuilt Graphs Directory

This directory stores prebuilt graphs for frequently used regions.

## Why Prebuilt Graphs?

Prebuilt graphs avoid repeated downloads from Overpass API for frequently used areas:
- ✅ Faster routing (no download wait)
- ✅ More reliable (no API timeouts)
- ✅ Offline capable (once downloaded)
- ⚠️ Only practical for 20-50km radius regions

## Building Prebuilt Graphs

Use the `build_prebuilt_graph.py` script:

```bash
# Build Warsaw city graph (20km radius)
PYTHONPATH=. python scripts/build_prebuilt_graph.py \
    --name warsaw_city \
    --center 52.2297 21.0122 \
    --radius 20000

# Build Krakow city graph (25km radius)
PYTHONPATH=. python scripts/build_prebuilt_graph.py \
    --name krakow_city \
    --center 50.0647 19.9450 \
    --radius 25000
```

## Registry

The `registry.json` file maintains a list of all available prebuilt graphs:

```json
{
  "warsaw_city": {
    "graph_file": "warsaw_city.pkl",
    "metadata_file": "warsaw_city_metadata.json",
    "center": {"lat": 52.2297, "lon": 21.0122},
    "radius_km": 20,
    "created_at": "2025-11-02 12:00:00"
  }
}
```

## Using Prebuilt Graphs

### In Python Code

```python
from app.graph_loader import get_or_download_graph

# Automatically uses prebuilt graph if available, otherwise downloads
start = (52.2297, 21.0122)
end = (52.3300, 21.2518)
G, is_prebuilt = get_or_download_graph(start, end, radius_meters=8000)

if is_prebuilt:
    print("Using prebuilt graph (fast!)")
else:
    print("Downloaded from Overpass API (slower)")
```

### Listing Available Graphs

```python
from app.graph_loader import GraphRegistry

registry = GraphRegistry()
graphs = registry.list_graphs()

for name, info in graphs.items():
    print(f"{name}: {info['radius_km']} km radius")
```

## File Structure

```
prebuilt_graphs/
├── README.md                    # This file
├── registry.json                # Index of all graphs
├── warsaw_city.pkl              # Graph data (binary)
├── warsaw_city_metadata.json    # Graph metadata
├── krakow_city.pkl
└── krakow_city_metadata.json
```

## Storage Estimates

| Radius | Storage | Memory | Notes |
|--------|---------|--------|-------|
| 20 km  | ~200 MB | ~1 GB  | ✅ Recommended for cities |
| 30 km  | ~450 MB | ~2 GB  | ✅ Good for metropolitan areas |
| 50 km  | ~1.2 GB | ~5 GB  | ⚠️ Feasible but large |
| 100 km | ~5 GB   | ~20 GB | ❌ Not recommended |

## Best Practices

1. **City centers** (20km): Perfect for single-city routing
2. **Metropolitan areas** (30-40km): Good for suburbs
3. **Update regularly**: Rebuild monthly to get OSM updates
4. **Use .gitignore**: Don't commit large .pkl files to git
5. **Fallback**: Always have on-demand download as backup

## Limitations

- Not suitable for >50km radius (too large)
- Requires disk space for storage
- Needs periodic updates for fresh OSM data
- For production, use proper routing engines instead

## See Also

- [PREBUILT_GRAPH_ANALYSIS.md](../docs/PREBUILT_GRAPH_ANALYSIS.md) - Detailed cost analysis
- [scripts/build_prebuilt_graph.py](../scripts/build_prebuilt_graph.py) - Build tool
- [scripts/estimate_graph_cost.py](../scripts/estimate_graph_cost.py) - Cost estimator
