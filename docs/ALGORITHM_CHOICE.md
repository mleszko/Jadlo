# Algorithm Choice: Dijkstra's Algorithm for Surface-Based Routing

## Question: Should we use Dijkstra's algorithm or another?

**Answer: Yes, Dijkstra's algorithm is the right choice, and it's already implemented.**

## Current Implementation

The Jadlo route planner uses two graph search algorithms, both optimal for the task:

1. **Dijkstra's Algorithm** (via `networkx.shortest_path`)
   - Used in: `compute_route()` function
   - Finds the optimal path based on weighted edges
   - Guaranteed to find the best route according to edge weights

2. **A* Algorithm** (via `networkx.astar_path`)
   - Used in: `compute_route_intersections()` function
   - Enhanced Dijkstra's with geographic heuristic
   - Faster for long-distance routing, especially with intersection-based graphs
   - Still guarantees optimal path when heuristic is admissible

## Why Dijkstra's Algorithm?

Dijkstra's algorithm is **ideal** for calculating route values by surface because:

### 1. Supports Weighted Edges
- Each edge (road segment) can have a custom weight
- Weight combines: distance × highway_penalty × **surface_penalty** × other factors
- Surface type becomes a primary factor in route calculation

### 2. Finds Optimal Routes
- Guarantees finding the route with minimum total weight
- No heuristic bias (unlike greedy algorithms)
- Explores all promising paths systematically

### 3. Flexible Weighting Formula
Our implementation calculates edge weight as:
```python
weight = length × highway_penalty × (surface_penalty ^ surface_weight_factor) × heatmap_bonus
```

Where:
- `surface_penalty`: Base penalty per surface type (1.0 for asphalt, 2.0 for dirt)
- `surface_weight_factor`: User-configurable multiplier (0.1 to 3.0)
  - 0.5 = prioritize distance over surface
  - 1.0 = balanced (default)
  - 2.0 = strongly prefer better surfaces

### 4. Natural Multi-Criteria Optimization
The algorithm naturally balances:
- Distance (shorter is better)
- Surface quality (smoother is better)
- Road type (bike paths vs highways)
- User preferences (configurable weights)

## Surface-Based Route Value Calculation

The key insight for surface-based routing is in the **edge weight formula**:

```python
# Surface penalty uses exponential scaling for stronger effect
base_surface_penalty = SURFACE_PENALTIES[surface]  # 1.0 for paved, 2.0 for dirt
surface_penalty = base_surface_penalty ** surface_weight_factor

# Final edge weight
weight = length × highway_penalty × surface_penalty × heatmap_bonus
```

### Example: Impact of surface_weight_factor

Consider two routes:
- Route A: 1000m on asphalt (surface_penalty = 1.0)
- Route B: 800m on dirt (surface_penalty = 2.0)

| Factor | Route A Weight | Route B Weight | Algorithm Chooses |
|--------|----------------|----------------|-------------------|
| 0.5    | 1000           | 1131           | Route A (paved)   |
| 1.0    | 1000           | 1600           | Route A (paved)   |
| 2.0    | 1000           | 3200           | Route A (paved)   |

With high factor, the algorithm **strongly prefers better surfaces** even if they're longer.

## Comparison with Other Algorithms

### Dijkstra's vs. Greedy Algorithms
❌ **Greedy**: Always chooses locally best option, may miss globally optimal route  
✅ **Dijkstra's**: Explores all options, guarantees global optimum

### Dijkstra's vs. A*
✅ **Both find optimal paths** when heuristic is admissible  
🔹 **A***: Faster (uses geographic heuristic to guide search)  
🔹 **Dijkstra's**: Simpler (no heuristic needed)

We use **A*** for intersection-based routing (faster for long distances) and **Dijkstra's** for standard routing.

## Implementation Details

### Location in Code
- **File**: `app/routing.py`
- **Functions**:
  - `compute_route()`: Uses Dijkstra's via `nx.shortest_path(G, orig, dest, weight='weight')`
  - `compute_route_intersections()`: Uses A* via `nx.astar_path(H, s_node, t_node, heuristic=..., weight='weight')`
- **Edge weight calculation**: `_edge_penalty(u, v, key, data, params)`

### Surface Penalties (Base Values)
```python
SURFACE_PENALTIES = {
    'paved': 1.0,      # Best - smooth paved roads
    'asphalt': 1.0,    # Best - smooth asphalt
    'concrete': 1.0,   # Best - smooth concrete
    'gravel': 1.6,     # Moderate - bumpy but passable
    'unpaved': 2.0,    # Poor - rough unpaved roads
    'dirt': 2.0,       # Poor - dirt tracks
}
```

These base penalties are raised to the power of `surface_weight_factor` for exponential scaling.

## Conclusion

✅ **Dijkstra's algorithm is already implemented and is the right choice**  
✅ **Surface type is a primary factor in route calculation**  
✅ **The `surface_weight_factor` parameter gives users control over surface vs. distance tradeoff**  
✅ **A* is used as an optimization for long-distance routing**

The implementation correctly uses Dijkstra's algorithm to calculate route values by surface type, as requested in the issue.
