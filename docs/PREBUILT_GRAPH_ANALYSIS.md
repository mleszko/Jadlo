# Prebuilt Graph Analysis: Warsaw Area with 200km Radius

## Overview

This document analyzes the cost and feasibility of building and storing a prebuilt graph for the entire area around Warsaw with a 200km radius, as an alternative to fetching graphs on-demand from the Overpass API.

## Problem Statement

Currently, Jadlo fetches graph data from OpenStreetMap via the Overpass API on-demand for each route request. This approach:
- ✅ Works well for small areas and one-off requests
- ✅ Always has fresh data
- ❌ Slow for large areas (minutes to download)
- ❌ Memory intensive for large graphs
- ❌ Subject to Overpass API rate limits
- ❌ Unreliable for production use

**Question:** How costly would it be to build a graph from the entire area around Warsaw with a 200km radius and store it as a ready-to-use graph?

## Analysis Approach

We measure the following metrics for different radius sizes:
1. **Download time** - Time to fetch data from Overpass API
2. **Memory usage** - RAM required to build and hold the graph
3. **Storage size** - Disk space needed to store the graph
4. **Graph complexity** - Number of nodes and edges
5. **Load time** - Time to load the prebuilt graph from disk

### Test Tool

Use the analysis script to measure these metrics:

```bash
# Test 50km radius (moderate area)
PYTHONPATH=. python scripts/analyze_graph_cost.py --center 52.2297 21.0122 --radius 50000

# Test 100km radius (large area)
PYTHONPATH=. python scripts/analyze_graph_cost.py --center 52.2297 21.0122 --radius 100000

# Test 200km radius (very large area)
PYTHONPATH=. python scripts/analyze_graph_cost.py --center 52.2297 21.0122 --radius 200000
```

## Expected Results

Based on typical OSM data density in Poland and similar analyses:

### 50km Radius (Warsaw Metropolitan Area)

| Metric | Estimated Value |
|--------|----------------|
| Download time | 2-5 minutes |
| Memory usage | 500-800 MB |
| Storage size | 100-200 MB |
| Nodes | ~100,000-200,000 |
| Edges | ~250,000-500,000 |
| Load time | 1-3 seconds |

**Verdict:** ✅ **Practical and recommended**

### 100km Radius (Warsaw Region)

| Metric | Estimated Value |
|--------|----------------|
| Download time | 10-20 minutes |
| Memory usage | 2-4 GB |
| Storage size | 400-800 MB |
| Nodes | ~400,000-800,000 |
| Edges | ~1,000,000-2,000,000 |
| Load time | 3-10 seconds |

**Verdict:** ⚠️ **Feasible but challenging**
- May hit Overpass API timeout limits
- Requires significant server resources
- Loading time starts to become noticeable

### 200km Radius (Greater Poland Region)

| Metric | Estimated Value |
|--------|----------------|
| Download time | 24+ hours |
| Memory usage | 30-90 GB |
| Storage size | 15-25 GB |
| Nodes | ~49,000,000 |
| Edges | ~116,000,000 |
| Load time | 30-60 seconds |

**Verdict:** ❌ **Not recommended for on-demand download**
- Very likely to hit Overpass API limits (timeout/rate limit)
- Requires substantial server resources (90GB+ RAM peak)
- Long download times make on-demand impractical
- OSMnx NetworkX format is unoptimized (see comparison below)
- Better alternatives exist (see below)

**Note:** These sizes are for OSMnx's NetworkX graph format (Python pickle), which is much larger than optimized routing engines. See [GRAPH_SIZE_COMPARISON.md](GRAPH_SIZE_COMPARISON.md) for why OSMnx graphs are 10-60x larger than Google Maps or GraphHopper.

## Key Findings

### 1. Overpass API Limitations

The Overpass API has strict limits:
- **Timeout**: Queries taking >180 seconds are killed
- **Rate limits**: Frequent large queries get throttled
- **Resource limits**: Memory-intensive queries may be rejected

**A 200km radius query will likely hit these limits.**

### 2. Memory Requirements

Graph building requires:
- **In-memory graph**: 2-4x the stored size during processing
- **Peak memory**: Can spike to 5-10x during complex operations

**For 200km radius:** Expect 30-90 GB peak memory usage

### 2.5. Why So Large? OSMnx vs Google Maps

**Common question:** "Google Maps offline for Poland is ~1 GB, why is OSMnx graph 20 GB?"

**Answer:** OSMnx NetworkX graphs are **unoptimized development tools**, not production formats:

| Format | Poland Size | Optimization Level |
|--------|-------------|-------------------|
| Google Maps | ~1 GB | Maximum (proprietary) |
| GraphHopper | ~2 GB | High (production) |
| OSMnx NetworkX | ~60-80 GB | None (development) |

**Why 60x larger?**
- Python pickle format (not compressed)
- Full NetworkX graph with Python object overhead
- All OSM metadata preserved
- Shapely geometries (full precision)
- Designed for flexibility, not size

**See [GRAPH_SIZE_COMPARISON.md](GRAPH_SIZE_COMPARISON.md) for detailed explanation.**

This is why we recommend GraphHopper/Valhalla for production - they achieve Google Maps-like efficiency.

### 3. Storage Scaling

Storage scales roughly with area:
- 50km radius = π × 50² = 7,850 km²
- 100km radius = π × 100² = 31,400 km² (4x area)
- 200km radius = π × 200² = 125,600 km² (16x area)

**Storage grows quadratically with radius.**

### 4. Graph Loading Performance

Loading a prebuilt graph is **much faster** than downloading:
- 200 MB graph: ~2 seconds to load
- 2 GB graph: ~15 seconds to load

**Still slower than ideal for request-time loading.**

## Recommendations

### ❌ Do NOT: Single 200km Prebuilt Graph

**Reasons:**
1. Too large to download reliably from Overpass API
2. Excessive memory requirements (10-20 GB)
3. Slow to load (15-30 seconds per request)
4. Wastes resources - most routes use <5% of the graph
5. Inflexible - hard to update when roads change

### ✅ Do INSTEAD: Use a Proper Routing Engine

For production use, migrate to a dedicated routing engine:

**Option 1: GraphHopper (Recommended)**
- Pre-processes entire countries in minutes
- Serves queries in milliseconds
- ~200 MB RAM for Poland
- Open-source, self-hostable
- Supports custom profiles

```bash
# Download Poland extract (~2 GB)
wget https://download.geofabrik.de/europe/poland-latest.osm.pbf

# Build routing graph (one-time, ~5 minutes)
java -jar graphhopper.jar import poland-latest.osm.pbf

# Start server (uses ~200 MB RAM)
java -jar graphhopper.jar server
```

**Option 2: Valhalla**
- Highly optimized for bicycle routing
- Multi-modal support
- Open-source, production-ready
- Used by Mapbox

**Option 3: OSRM**
- Extremely fast (microsecond queries)
- Lightweight memory footprint
- Open-source
- Limited to single profile at a time

**Option 4: OpenRouteService**
- Flexible profiles
- Good documentation
- REST API compatible with Jadlo
- Can self-host

### ✅ Alternative: Regional Tile-Based Graphs

Instead of one huge graph, use multiple smaller regional graphs:

```
graphs/
  ├── warsaw_city_r20km.pkl      (100 MB)
  ├── warsaw_north_r30km.pkl     (200 MB)
  ├── warsaw_south_r30km.pkl     (200 MB)
  ├── lodz_r30km.pkl             (150 MB)
  └── ...
```

**Advantages:**
- Each graph small enough to download reliably
- Load only the graph(s) needed for a route
- Can update individual regions
- Parallel downloads possible

**Implementation:**
1. Divide Poland into overlapping ~50km tiles
2. Pre-build each tile graph
3. At routing time, determine which tiles are needed
4. Load and merge relevant tiles
5. Cache loaded tiles in memory

### ✅ Hybrid Approach (Best for Jadlo PoC)

Combine prebuilt graphs with on-demand fetching:

```python
def get_graph(center, radius):
    # Check if we have a prebuilt graph covering this area
    for prebuilt in PREBUILT_GRAPHS:
        if prebuilt.covers(center, radius):
            return load_graph(prebuilt.path)
    
    # Fall back to on-demand download for unusual areas
    return ox.graph_from_point(center, dist=radius, network_type='bike')
```

**Prebuilt graphs for common areas:**
- Warsaw city center (20km radius)
- Krakow city center (20km radius)
- Major cycling routes (50km corridors)

**On-demand for:**
- Unusual areas
- Long-distance routes (use segmentation)
- Testing/development

## Cost Analysis Summary

### One-Time Build Cost (200km radius)

| Resource | Cost | Notes |
|----------|------|-------|
| Overpass API | **Free but likely to fail** | Will hit timeout/rate limits |
| Computation | **30-60 minutes** | One-time build |
| Memory | **10-20 GB RAM** | During build only |
| Storage | **2-3 GB disk** | Permanent storage |

### Per-Request Cost (using prebuilt graph)

| Resource | Cost | Notes |
|----------|------|-------|
| Load time | **15-30 seconds** | Every request |
| Memory | **2-4 GB RAM** | Held in memory |
| Storage I/O | **2-3 GB read** | Every request |

**Conclusion:** Very expensive per-request for a resource most routes don't need.

### Per-Request Cost (proper routing engine)

| Resource | Cost | Notes |
|----------|------|-------|
| Query time | **10-50 ms** | Lightning fast |
| Memory | **200 MB RAM** | Entire Poland |
| Storage I/O | **None** | Pre-loaded |

**Conclusion:** 500-1000x more efficient than prebuilt graph approach.

## Implementation Guide

If you still want to implement prebuilt graphs for specific regions:

### Step 1: Build the Graph

```bash
# Create artifacts directory
mkdir -p artifacts

# Build Warsaw region graph (50km is practical)
PYTHONPATH=. python scripts/analyze_graph_cost.py \
  --center 52.2297 21.0122 \
  --radius 50000 \
  --output-dir artifacts
```

### Step 2: Create Loading Utility

```python
# app/graph_loader.py
import pickle
import os
from typing import Optional
import networkx as nx

PREBUILT_GRAPHS = {
    'warsaw': {
        'path': 'artifacts/graph_warsaw_r50km.pkl',
        'center': (52.2297, 21.0122),
        'radius_km': 50,
    },
}

def load_prebuilt_graph(region: str) -> Optional[nx.MultiDiGraph]:
    """Load a prebuilt graph from disk."""
    if region not in PREBUILT_GRAPHS:
        return None
    
    config = PREBUILT_GRAPHS[region]
    path = config['path']
    
    if not os.path.exists(path):
        return None
    
    with open(path, 'rb') as f:
        return pickle.load(f)

def covers_area(graph_config: dict, point: tuple, radius_km: float) -> bool:
    """Check if a prebuilt graph covers the requested area."""
    from app.routing import _haversine
    
    center = graph_config['center']
    graph_radius = graph_config['radius_km']
    
    # Calculate distance from graph center to requested point
    dist_km = _haversine(center, point) / 1000
    
    # Check if point + radius fits within graph
    return (dist_km + radius_km) <= graph_radius * 0.9  # 90% to be safe
```

### Step 3: Integrate with Routing

```python
# Modify app/routing.py compute_route()
def compute_route(start, end, params, bbox_buffer=None, radius_meters=None):
    # Try loading prebuilt graph
    from app.graph_loader import load_prebuilt_graph, covers_area, PREBUILT_GRAPHS
    
    for region, config in PREBUILT_GRAPHS.items():
        if covers_area(config, start, radius_meters / 1000):
            G = load_prebuilt_graph(region)
            if G is not None:
                logger.info(f"Using prebuilt graph: {region}")
                # ... continue with routing
    
    # Fall back to on-demand download
    # ... existing code
```

## Conclusion

### Question: How costly would it be to build a 200km radius graph?

**Answer:**
- **Build cost:** 30-60 minutes, 10-20 GB RAM, likely to fail due to API limits
- **Storage cost:** 2-3 GB disk space
- **Usage cost:** 15-30 seconds load time, 2-4 GB RAM per request
- **Practical value:** ❌ Low - most routes don't need 200km of graph data

### Recommendations

1. **For PoC/small scale:** Use current on-demand approach with segmentation (already implemented)

2. **For medium scale:** Prebuilt graphs for city centers (20-50km radius)
   - Warsaw center: 20km radius (~100 MB, 2-3 sec load)
   - Common cycling areas
   - Hybrid with on-demand fallback

3. **For production:** Migrate to proper routing engine (GraphHopper, Valhalla, OSRM)
   - 500-1000x faster than prebuilt graph approach
   - Uses 10-20x less memory
   - Industry-standard solution
   - Poland country-wide in 200 MB RAM

### Next Steps

1. ✅ Use the analysis script to measure actual costs for your region
2. ⚠️ If building prebuilt graphs, start with 20-50km radius (practical)
3. ❌ Avoid 200km radius - not practical with Overpass API
4. ✅ For production, plan migration to GraphHopper or Valhalla

## Resources

- [GraphHopper Documentation](https://github.com/graphhopper/graphhopper)
- [Valhalla Documentation](https://github.com/valhalla/valhalla)
- [OSRM Documentation](http://project-osrm.org/)
- [OpenRouteService Documentation](https://openrouteservice.org/)
- [Overpass API Usage Policy](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html)
- [OSM Data Extracts (Geofabrik)](https://download.geofabrik.de/)
