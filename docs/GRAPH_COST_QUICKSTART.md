# Quick Start: Prebuilt Graph Cost Analysis

## TL;DR - Answer to the Question

**Question:** How costly would it be to build a graph from the entire area around Warsaw with a 200km radius and store it as a ready graph?

**Answer:** ❌ **NOT RECOMMENDED**

- **Storage:** ~20 GB (OSMnx NetworkX format)
- **Memory:** ~90 GB peak
- **Download:** ~24 hours (will likely fail)
- **Risk:** Very High

**Why so large?** OSMnx uses unoptimized Python pickle format. See [GRAPH_SIZE_COMPARISON.md](GRAPH_SIZE_COMPARISON.md) for comparison with Google Maps (~1 GB) and GraphHopper (~2 GB for all Poland).

**Better alternatives:**
1. ✅ Use GraphHopper/Valhalla (~2 GB for Poland, millisecond queries)
2. ✅ Keep current segmented approach (already works)
3. ⚠️ Prebuilt graphs for 20-50km city centers only

## Quick Analysis

Run the estimation tool to analyze any radius:

```bash
# Estimate 200km radius around Warsaw
python scripts/estimate_graph_cost.py --radius 200

# Compare different scenarios
python scripts/estimate_graph_cost.py --radius 50 --compare

# Estimate for different city
python scripts/estimate_graph_cost.py --radius 30 --center "Krakow"
```

### Example Output (200km):

```
GRAPH COST ESTIMATE
Location:            Warsaw
Radius:              200.0 km
Storage:             19.82 GB
Memory (peak):       89.2 GB
Download time:       1470.3 minutes (~24 hours)
Risk level:          Very High
Note:                Very likely to fail, not recommended
```

## Practical Alternative: City Centers (20-50km)

For **practical** prebuilt graphs, use 20-50km radius:

```bash
# Build Warsaw city graph (20km - RECOMMENDED)
PYTHONPATH=. python scripts/build_prebuilt_graph.py \
    --name warsaw_city \
    --center 52.2297 21.0122 \
    --radius 20000
```

### Warsaw City (20km) Estimates:
- Storage: ~200 MB ✅
- Memory: ~1 GB ✅
- Download: ~15 minutes ✅
- Load time: ~2 seconds ✅
- Risk: Low ✅

## Using Prebuilt Graphs

Once built, use them automatically in your code:

```python
from app.graph_loader import get_or_download_graph

# Automatically uses prebuilt if available, otherwise downloads
start = (52.2297, 21.0122)
end = (52.3300, 21.2518)
graph, used_prebuilt = get_or_download_graph(start, end, radius_meters=8000)

if used_prebuilt:
    print("✓ Fast! Using prebuilt graph")
else:
    print("⏳ Downloading from Overpass API...")
```

## Comparison Table

| Radius | Storage | Memory | Download | Risk | Use Case |
|--------|---------|--------|----------|------|----------|
| 20 km  | 200 MB  | 1 GB   | 15 min   | Low  | ✅ City centers |
| 50 km  | 1.2 GB  | 5.6 GB | 90 min   | Med  | ⚠️ Metro areas |
| 100 km | 5 GB    | 22 GB  | 6 hours  | High | ❌ Too large |
| 200 km | 20 GB   | 90 GB  | 24 hours | Very High | ❌ Not practical |

## Production Recommendation

For production systems, use a proper routing engine instead:

### GraphHopper (Recommended)

```bash
# Download Poland extract
wget https://download.geofabrik.de/europe/poland-latest.osm.pbf

# Build graph (one-time, ~5 minutes)
java -jar graphhopper.jar import poland-latest.osm.pbf

# Start server (uses ~200 MB RAM for entire Poland!)
java -jar graphhopper.jar server
```

**Benefits:**
- 500-1000x faster than prebuilt graph approach
- 10-20x less memory (200 MB vs 20+ GB)
- Entire country in one graph
- Millisecond query times
- Production-ready

### Other Options

- **Valhalla:** Bicycle-optimized, multi-modal
- **OSRM:** Ultra-fast (microsecond queries)
- **OpenRouteService:** Flexible profiles, REST API

## Files Reference

- **Documentation:** [PREBUILT_GRAPH_ANALYSIS.md](PREBUILT_GRAPH_ANALYSIS.md)
- **Estimation Tool:** `scripts/estimate_graph_cost.py`
- **Measurement Tool:** `scripts/analyze_graph_cost.py`
- **Build Tool:** `scripts/build_prebuilt_graph.py`
- **Usage Guide:** `prebuilt_graphs/README.md`

## Summary

| Approach | 200km Radius | 20km Radius | GraphHopper |
|----------|--------------|-------------|-------------|
| Storage  | 20 GB        | 200 MB      | 2 GB (Poland) |
| Memory   | 90 GB        | 1 GB        | 200 MB |
| Build    | 24 hours     | 15 min      | 5 min |
| Load     | 40 sec       | 2 sec       | Always ready |
| Query    | Minutes      | Seconds     | Milliseconds |
| Verdict  | ❌           | ✅          | ✅✅ Best |

**Final Recommendation:** Use GraphHopper/Valhalla for production. For PoC, keep the current segmented approach or use prebuilt graphs for specific 20km city centers only.
