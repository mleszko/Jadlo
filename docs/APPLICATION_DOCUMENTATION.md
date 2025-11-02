# Jadlo - Complete Application Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Routing Algorithm & Logic](#routing-algorithm--logic)
4. [Core Components](#core-components)
5. [API Reference](#api-reference)
6. [Configuration & Parameters](#configuration--parameters)
7. [Usage Examples](#usage-examples)
8. [Development & Testing](#development--testing)

---

## Overview

**Jadlo** is a route planning application that generates cycling routes with configurable preferences for road type, surface quality, and other factors. The application uses real OpenStreetMap (OSM) data to create routes that balance multiple criteria according to user preferences.

### Key Features

- **Surface-based routing**: Prioritize paved vs unpaved surfaces with configurable weight
- **Road type preferences**: Prefer or avoid main roads, cycleways, etc.
- **Intelligent algorithms**: Uses Dijkstra's algorithm and A* for optimal route finding
- **Real OSM data**: Routes follow actual roads from OpenStreetMap
- **Segmented routing**: Handles long distances (100km+) by breaking into manageable segments
- **GPX export**: Generates standard GPX files for GPS devices and mapping apps

### Technology Stack

- **Language**: Python 3.12+
- **Framework**: FastAPI (REST API)
- **Routing**: NetworkX (Dijkstra's algorithm, A*)
- **Map Data**: OSM via osmnx library
- **Testing**: pytest
- **Data Format**: GPX (GPS Exchange Format)

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                     Client/User                          │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI REST API (app/main.py)             │
│                                                          │
│  POST /route                                             │
│  - Receives: start, end, params                         │
│  - Returns: coordinates, GPX                            │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│            Routing Engine (app/routing.py)              │
│                                                          │
│  • compute_route()                                       │
│  • compute_route_intersections()                        │
│  • calculate_edge_weight()                              │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              OSM Data Layer (osmnx)                     │
│                                                          │
│  • Fetches map data from Overpass API                   │
│  • Builds graph from OSM data                           │
│  • Provides road network information                    │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Request**: Client sends route request with start/end points and preferences
2. **Graph Fetch**: System fetches OSM data for the relevant geographic area
3. **Weight Calculation**: Each road segment is assigned a weight based on user preferences
4. **Route Finding**: Dijkstra's or A* algorithm finds optimal path
5. **GPX Generation**: Route coordinates are converted to GPX format
6. **Response**: Client receives coordinates and GPX file

---

## Routing Algorithm & Logic

### Algorithm Choice: Dijkstra's Algorithm and A*

The application uses **two graph search algorithms** depending on the routing mode:

#### 1. Dijkstra's Algorithm (Standard Routing)

**Used in**: `compute_route()` function

**Why Dijkstra's?**
- Guarantees finding the optimal route based on edge weights
- Well-suited for weighted graphs where edges have costs
- No heuristic needed - explores systematically
- Works perfectly for our multi-criteria optimization

**How it works:**
```python
# Simplified conceptual flow
1. Build graph G from OSM data
2. For each edge (u, v):
   weight = length × highway_penalty × surface_penalty × other_factors
3. Find shortest path from origin to destination using weights
4. Path with minimum total weight is the optimal route
```

#### 2. A* Algorithm (Intersection-based Routing)

**Used in**: `compute_route_intersections()` function

**Why A*?**
- Faster than Dijkstra's for long distances
- Uses geographic distance as heuristic (haversine)
- Still guarantees optimal path when heuristic is admissible
- Works on simplified graph (intersections only) for lower memory usage

**How it works:**
```python
# Simplified conceptual flow
1. Build graph, then simplify to intersection nodes only
2. For each intersection edge:
   weight = base_weight + heading_bias_penalty
3. Use A* with haversine distance heuristic
4. Explores fewer nodes than Dijkstra's while remaining optimal
```

### Edge Weight Calculation

This is the **core logic** that determines route quality. Each road segment (edge) is assigned a weight, and the algorithm finds the path with minimum total weight.

#### Weight Formula

```python
weight = length × highway_penalty × (surface_penalty ^ surface_weight_factor) × heatmap_bonus
```

**Components:**

1. **length** - Distance in meters (base component)
2. **highway_penalty** - Road type penalty (motorway=5.0, cycleway=0.7)
3. **surface_penalty** - Surface quality penalty (asphalt=1.0, dirt=2.0)
4. **surface_weight_factor** - User control (0.1-3.0, default 1.0)
   - Higher = surface matters more in route selection
   - Lower = distance matters more than surface
5. **heatmap_bonus** - Popularity bonus (mocked in PoC)

#### Surface Penalty Scaling (Key Innovation)

The **exponential scaling** of surface penalties is the key feature added in this PR:

```python
surface_penalty = base_surface_penalty ^ surface_weight_factor
```

**Why exponential?**
- Creates strong differentiation at high factors
- Maintains reasonable behavior at low factors
- Example: dirt road with base penalty 2.0
  - Factor 0.5: penalty = 2.0^0.5 = 1.41 (mild preference)
  - Factor 1.0: penalty = 2.0^1.0 = 2.00 (base)
  - Factor 2.0: penalty = 2.0^2.0 = 4.00 (strong preference)

**Impact on routing:**
- With `surface_weight_factor=2.0`: 1000m paved route preferred over 800m dirt route by 68.8%
- With `surface_weight_factor=0.5`: 1000m paved route preferred over 800m dirt route by only 11.6%

### Surface Types and Penalties

```python
SURFACE_PENALTIES = {
    'paved': 1.0,      # Best - smooth paved roads
    'asphalt': 1.0,    # Best - asphalt
    'concrete': 1.0,   # Best - concrete
    'gravel': 1.6,     # Moderate - bumpy but passable
    'unpaved': 2.0,    # Poor - rough unpaved roads
    'dirt': 2.0,       # Poor - dirt tracks
}
```

### Highway Type Penalties

```python
HIGHWAY_PENALTIES = {
    'motorway': 5.0,      # Avoid - dangerous for bikes
    'trunk': 3.0,         # Avoid - fast traffic
    'primary': 2.0,       # Caution - busy roads
    'secondary': 1.5,     # Acceptable
    'tertiary': 1.2,      # Good
    'residential': 1.0,   # Good - quiet streets
    'service': 1.0,       # Good
    'cycleway': 0.7,      # Best - dedicated bike paths
    'path': 0.9,          # Good - multi-use paths
}
```

### User Preference Modulation

User preferences further modify the penalties:

#### 1. **prefer_main_roads** (0.0 - 1.0)
- 0.0 = avoid main roads (increase penalty)
- 1.0 = prefer main roads (decrease penalty)
- Affects: primary, secondary, trunk, motorway

#### 2. **prefer_unpaved** (0.0 - 1.0)
- 0.0 = avoid unpaved surfaces (increase penalty)
- 1.0 = prefer unpaved surfaces (decrease penalty)
- Affects: gravel, unpaved, dirt

#### 3. **surface_weight_factor** (0.1 - 3.0)
- Controls how strongly surface type influences routing
- Higher = surface quality dominates route selection
- Lower = distance becomes more important

#### 4. **heatmap_influence** (0.0 - 1.0)
- 0.0 = ignore popularity data
- 1.0 = strongly prefer popular routes
- Note: Currently mocked (looks for 'cycleway' tag)

### Route Finding Process

**Standard Mode** (`compute_route`):

```
1. Define geographic area (bbox around start/end)
2. Fetch OSM graph for area
3. Calculate weight for each edge using formula above
4. Find nearest nodes to start/end points
5. Run Dijkstra's shortest_path with weights
6. Convert node sequence to coordinates
7. Generate GPX from coordinates
```

**Intersection Mode** (`compute_route_intersections`):

```
1. Fetch OSM graph for area (with radius_meters)
2. Calculate edge weights
3. Simplify graph to intersection nodes only
   - Collapse degree-2 nodes into single edges
   - Preserve geometry and aggregate lengths
4. Add heading bias penalty
   - Penalize turns away from goal direction
5. Run A* with haversine heuristic
6. Reconstruct full geometry from original graph
7. Generate GPX
```

### Segmented Routing (for long distances)

For routes >50km, the system uses segmentation:

```
1. Calculate total distance
2. Divide route into ~20km segments
3. Interpolate intermediate waypoints
4. Route each segment independently
5. Stitch segments together
6. Bridge large gaps (>1km) with additional routing
7. Return complete route
```

**Benefits:**
- Lower memory usage
- Avoids Overpass API limits
- More resilient to failures (retry per segment)

---

## Core Components

### 1. FastAPI Application (`app/main.py`)

**Purpose**: REST API endpoint for route generation

**Endpoint**: `POST /route`

**Request Schema**:
```python
{
  "start": [lat, lon],      # Starting coordinates
  "end": [lat, lon],        # Destination coordinates
  "params": {               # Optional preferences
    "prefer_main_roads": 0.5,
    "prefer_unpaved": 0.5,
    "heatmap_influence": 0.0,
    "prefer_streetview": 0.0,
    "surface_weight_factor": 1.0
  }
}
```

**Response Schema**:
```python
{
  "coords": [[lat, lon], ...],  # List of route coordinates
  "gpx": "<?xml version=..."     # GPX file content
}
```

### 2. Routing Engine (`app/routing.py`)

**Core Functions**:

#### `compute_route(start, end, params, bbox_buffer, radius_meters)`
Standard routing using Dijkstra's algorithm on full graph.

**Parameters:**
- `start`: (lat, lon) tuple
- `end`: (lat, lon) tuple
- `params`: User preferences dict
- `bbox_buffer`: Degrees to expand bbox (default 0.12)
- `radius_meters`: Alternative to bbox, circular area

**Returns:** `(coords_list, gpx_string)`

#### `compute_route_intersections(start, end, params, radius_meters, heading_threshold_deg)`
Optimized routing using A* on simplified intersection graph.

**Parameters:**
- `start`: (lat, lon) tuple
- `end`: (lat, lon) tuple
- `params`: User preferences dict
- `radius_meters`: Fetch radius in meters
- `heading_threshold_deg`: Heading bias threshold (default 60°)

**Returns:** `(coords_list, gpx_string)`

#### `calculate_edge_weight(length, highway, surface, params)`
**Public API** for calculating edge weight.

**Parameters:**
- `length`: Road segment length in meters
- `highway`: Highway type string
- `surface`: Surface type string (or None)
- `params`: User preferences dict

**Returns:** `float` (edge weight)

**Example:**
```python
from app.routing import calculate_edge_weight

params = {'surface_weight_factor': 2.0, 'prefer_main_roads': 0.5}
weight = calculate_edge_weight(100.0, 'residential', 'asphalt', params)
# weight = 100.0 (100m × 1.0 highway × 1.0 surface)

weight = calculate_edge_weight(100.0, 'residential', 'dirt', params)
# weight = 400.0 (100m × 1.0 highway × 4.0 surface)
```

### 3. Helper Functions

#### `_get_surface_penalty(surface)`
Maps surface type string to penalty multiplier. Handles compound types (e.g., 'asphalt:lanes').

#### `_edge_penalty(u, v, key, data, params)`
Internal function that calculates edge weight with all factors.

#### `_haversine(a, b)`
Calculates great-circle distance in meters between two (lat, lon) points.

#### `_bearing(a, b)`
Calculates bearing in degrees from point a to b.

#### `simplify_graph_to_intersections(G)`
Simplifies graph by collapsing degree-2 nodes, creating intersection-level graph.

---

## API Reference

### REST API

#### POST /route

Generate a route between two points with configurable preferences.

**Request Body:**
```json
{
  "start": [52.2297, 21.0122],
  "end": [53.1325, 23.1688],
  "params": {
    "prefer_main_roads": 0.5,
    "prefer_unpaved": 0.2,
    "heatmap_influence": 0.0,
    "prefer_streetview": 0.0,
    "surface_weight_factor": 1.5
  }
}
```

**Response:**
```json
{
  "coords": [
    [52.2297, 21.0122],
    [52.2301, 21.0128],
    ...
  ],
  "gpx": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>..."
}
```

**Status Codes:**
- 200: Success
- 422: Validation error (invalid coordinates or parameters)
- 500: Server error (OSM data unavailable, routing failed)

### Python API

#### Function: `compute_route()`

```python
from app.routing import compute_route

start = (52.2297, 21.0122)
end = (52.3300, 21.2518)
params = {
    'prefer_main_roads': 0.5,
    'prefer_unpaved': 0.0,
    'surface_weight_factor': 2.0
}

coords, gpx = compute_route(start, end, params)
```

#### Function: `compute_route_intersections()`

```python
from app.routing import compute_route_intersections

start = (52.2297, 21.0122)
end = (52.3300, 21.2518)
params = {
    'prefer_main_roads': 0.5,
    'prefer_unpaved': 0.0,
    'surface_weight_factor': 2.0
}

coords, gpx = compute_route_intersections(
    start, end, params,
    radius_meters=8000,
    heading_threshold_deg=45
)
```

#### Function: `calculate_edge_weight()`

```python
from app.routing import calculate_edge_weight

# Calculate weight for a 100m asphalt residential road
params = {'surface_weight_factor': 2.0, 'prefer_main_roads': 0.5}
weight = calculate_edge_weight(100.0, 'residential', 'asphalt', params)
# Returns: 100.0

# Calculate weight for a 100m dirt residential road
weight = calculate_edge_weight(100.0, 'residential', 'dirt', params)
# Returns: 400.0 (penalty = 2.0^2.0 = 4.0)
```

---

## Configuration & Parameters

### RouteParams

All routing parameters with their ranges and defaults:

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `prefer_main_roads` | float | 0.0-1.0 | 0.5 | 0=avoid main roads, 1=prefer main roads |
| `prefer_unpaved` | float | 0.0-1.0 | 0.5 | 0=avoid unpaved, 1=prefer unpaved |
| `heatmap_influence` | float | 0.0-1.0 | 0.0 | 0=ignore popularity, 1=follow popular routes |
| `prefer_streetview` | float | 0.0-1.0 | 0.0 | 0=ignore streetview, 1=prefer covered routes |
| `surface_weight_factor` | float | 0.1-3.0 | 1.0 | Controls surface importance in routing |

### Surface Weight Factor Guide

This parameter has the strongest impact on route selection:

| Factor | Behavior | Use Case |
|--------|----------|----------|
| 0.1-0.5 | Distance priority | Shortest routes, surface less important |
| 0.5-0.8 | Balanced | Reasonable compromise |
| 0.8-1.2 | Default balance | Standard behavior |
| 1.2-2.0 | Surface preference | Avoid rough roads |
| 2.0-3.0 | Strong surface priority | Only smooth roads, accept longer routes |

### Example Configurations

#### Road Cyclist (fast, smooth roads)
```python
params = {
    'prefer_main_roads': 0.8,
    'prefer_unpaved': 0.0,
    'surface_weight_factor': 2.5,
    'heatmap_influence': 0.0
}
```

#### Mountain Biker (prefer trails)
```python
params = {
    'prefer_main_roads': 0.0,
    'prefer_unpaved': 1.0,
    'surface_weight_factor': 0.5,
    'heatmap_influence': 0.0
}
```

#### Casual Cyclist (balanced)
```python
params = {
    'prefer_main_roads': 0.5,
    'prefer_unpaved': 0.3,
    'surface_weight_factor': 1.0,
    'heatmap_influence': 0.5
}
```

#### Shortest Route (distance only)
```python
params = {
    'prefer_main_roads': 0.5,
    'prefer_unpaved': 0.5,
    'surface_weight_factor': 0.1,
    'heatmap_influence': 0.0
}
```

---

## Usage Examples

### Example 1: Basic Route via REST API

```bash
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{
    "start": [52.2297, 21.0122],
    "end": [52.3300, 21.2518],
    "params": {
      "surface_weight_factor": 1.5
    }
  }'
```

### Example 2: Python Script

```python
from app.routing import compute_route

# Define route
start = (52.2297, 21.0122)  # Warsaw
end = (52.3300, 21.2518)     # ~12km north

# Configure for smooth roads
params = {
    'prefer_main_roads': 0.5,
    'prefer_unpaved': 0.0,
    'surface_weight_factor': 2.0,
    'heatmap_influence': 0.0
}

# Generate route
coords, gpx = compute_route(start, end, params)

# Save GPX file
with open('route.gpx', 'w') as f:
    f.write(gpx)

print(f"Route generated with {len(coords)} points")
```

### Example 3: Long Distance Route

```python
from app.routing import compute_route_intersections
import math

def route_100km_segmented(start, end):
    """Generate 100km route using segmentation."""
    # Calculate segments
    dist_km = haversine_km(start, end)
    n_segments = math.ceil(dist_km / 20)
    
    # Generate intermediate points
    points = []
    for i in range(n_segments + 1):
        t = i / n_segments
        lat = start[0] + (end[0] - start[0]) * t
        lon = start[1] + (end[1] - start[1]) * t
        points.append((lat, lon))
    
    # Route each segment
    all_coords = []
    params = {'surface_weight_factor': 1.5}
    
    for i in range(n_segments):
        coords, _ = compute_route_intersections(
            points[i], points[i+1], params,
            radius_meters=8000
        )
        all_coords.extend(coords)
    
    return all_coords
```

### Example 4: Weight Calculation Demo

```python
from app.routing import calculate_edge_weight

# Define params for smooth road preference
params = {
    'surface_weight_factor': 2.0,
    'prefer_main_roads': 0.5,
    'prefer_unpaved': 0.5,
    'heatmap_influence': 0.0
}

# Compare different surfaces for same road type
surfaces = ['asphalt', 'concrete', 'gravel', 'unpaved', 'dirt']

print("100m residential road weight comparison:")
for surface in surfaces:
    weight = calculate_edge_weight(100.0, 'residential', surface, params)
    print(f"{surface:10s}: {weight:7.1f}")

# Output:
# asphalt   :   100.0
# concrete  :   100.0
# gravel    :   256.0
# unpaved   :   400.0
# dirt      :   400.0
```

---

## Development & Testing

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/mleszko/Jadlo.git
cd Jadlo

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
# Start FastAPI server
uvicorn app.main:app --reload

# Server runs on http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Running Tests

```bash
# All unit tests (fast, < 1 second)
PYTHONPATH=. python -m pytest tests/test_weight.py tests/test_routing.py tests/test_surface_routing.py -v

# Integration tests (slow, 3-5 minutes, requires network)
PYTHONPATH=. python -m pytest -m integration -v -s

# Specific test
PYTHONPATH=. python -m pytest tests/test_surface_routing.py::test_surface_weight_factor_high_emphasizes_surface -v

# With coverage
PYTHONPATH=. python -m pytest --cov=app tests/
```

### Test Structure

- **Unit Tests**: Fast tests validating logic without network calls
  - `tests/test_weight.py` - Edge weight calculations
  - `tests/test_routing.py` - Routing logic
  - `tests/test_surface_routing.py` - Surface weight factor behavior

- **Integration Tests**: Slow tests using real OSM data
  - `tests/test_integration_requirements.py` - PR merge requirements
  - `tests/test_generate_100km.py` - Long distance routing
  - `tests/test_generate_50km.py` - Medium distance routing

### Demo Scripts

```bash
# Surface routing demo
PYTHONPATH=. python scripts/demo_surface_routing.py

# Generate single route
PYTHONPATH=. python scripts/run_poc.py \
  --start 52.2297 21.0122 \
  --end 52.3300 21.2518 \
  --radius 3000 \
  --out route.gpx

# Generate segmented long route
PYTHONPATH=. python scripts/run_poc_segmented.py \
  --start 52.2297 21.0122 \
  --end 53.1325 23.1688 \
  --segment-km 20 \
  --radius 8000 \
  --out route_100km.gpx
```

### Project Structure

```
Jadlo/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   └── routing.py           # Core routing logic
├── scripts/
│   ├── demo_surface_routing.py    # Surface routing demo
│   ├── run_poc.py                 # Single route generator
│   └── run_poc_segmented.py       # Segmented route generator
├── tests/
│   ├── test_weight.py             # Weight calculation tests
│   ├── test_routing.py            # Routing logic tests
│   ├── test_surface_routing.py    # Surface feature tests
│   ├── test_integration_requirements.py  # Merge requirement tests
│   ├── test_generate_100km.py     # Long route test
│   └── test_generate_50km.py      # Medium route test
├── docs/
│   ├── APPLICATION_DOCUMENTATION.md  # This file
│   ├── ALGORITHM_CHOICE.md           # Algorithm rationale
│   └── INTEGRATION_TESTS.md          # Test documentation
├── README.md                # Quick start guide
├── TEST_RESULTS.md          # Test results summary
├── requirements.txt         # Python dependencies
└── pytest.ini              # Test configuration
```

### Key Files Modified in This PR

1. **app/routing.py**
   - Added `surface_weight_factor` parameter
   - Implemented exponential surface penalty scaling
   - Added `_get_surface_penalty()` helper
   - Created `calculate_edge_weight()` public API
   - Enhanced documentation

2. **app/main.py**
   - Added `surface_weight_factor` to RouteParams schema

3. **tests/test_surface_routing.py** (new)
   - 8 unit tests validating surface weight behavior

4. **tests/test_integration_requirements.py** (new)
   - 3 integration tests for PR merge requirements

5. **docs/** (new directory)
   - ALGORITHM_CHOICE.md - Algorithm rationale
   - INTEGRATION_TESTS.md - Test documentation
   - APPLICATION_DOCUMENTATION.md - This complete guide

6. **scripts/demo_surface_routing.py** (new)
   - Demonstration of surface weight impact

---

## Troubleshooting

### Common Issues

#### 1. osmnx Import Error
```
ImportError: osmnx requires GEOS/PROJ/GDAL
```
**Solution**: Install system dependencies or use Docker with preinstalled libraries.

#### 2. Overpass API Timeout
```
TimeoutError: Overpass API request timeout
```
**Solution**: Use segmented routing, reduce fetch radius, or retry later.

#### 3. NetworkXNoPath Error
```
networkx.exception.NetworkXNoPath: No path between nodes
```
**Solution**: Increase bbox_buffer or radius_meters to include more roads.

#### 4. Memory Error on Long Routes
```
MemoryError: Unable to allocate array
```
**Solution**: Use `compute_route_intersections()` or segmented routing.

### Performance Tips

1. **Use intersection-based routing** for routes >20km
2. **Use segmentation** for routes >50km
3. **Increase radius** if routing fails (more roads = more options)
4. **Cache OSM data** by enabling osmnx cache
5. **Reduce surface_weight_factor** if routes seem unrealistically long

---

## License & Attribution

- **Code**: See LICENSE file
- **OSM Data**: © OpenStreetMap contributors, ODbL license
- **Attribution Required**: When using OSM data, provide proper attribution

---

## Further Reading

- [README.md](../README.md) - Quick start guide
- [ALGORITHM_CHOICE.md](ALGORITHM_CHOICE.md) - Detailed algorithm explanation
- [INTEGRATION_TESTS.md](INTEGRATION_TESTS.md) - Test documentation
- [TEST_RESULTS.md](../TEST_RESULTS.md) - Test results summary
- [Assumptions.md](../Asumptions.md) - Project assumptions

---

**Document Version**: 1.0
**Last Updated**: 2025-11-01
**PR**: Add surface-based weighting with configurable factor for Dijkstra routing
