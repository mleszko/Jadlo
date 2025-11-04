# Branching Strategy for Exploring Graph Approaches

## Overview

This document provides guidance on repository management when exploring different routing approaches in Jadlo. Specifically, it addresses whether to fork the repository or create a new branch when working with different graph-based routing strategies.

## Quick Answer: Use Branches, Not Forks

**For exploring different approaches within the same project, create branches instead of forking.**

### Why Branches?

- **Easy comparison**: Switch between approaches using `git checkout`
- **Shared history**: All approaches share the same base, making it easy to merge improvements
- **Collaboration**: Team members can easily review and compare different approaches
- **Single repository**: Keeps all work in one place, avoiding synchronization issues
- **Easy merging**: Can cherry-pick or merge features between approaches

### When to Fork Instead

Forking is appropriate when:
- Creating a completely independent project based on this codebase
- You don't have write access to the original repository
- You want to maintain a permanent divergent version
- You're making changes you don't intend to merge back

## Special Case: Major Architectural Changes (e.g., Switching Routing Engines)

### The GraphHopper Migration Scenario

If you're considering a **major architectural change** like migrating from osmnx to GraphHopper, Valhalla, or another routing engine, you have three strategic options:

### Option 1: Separate Repository (Recommended for Major Rewrites)

**When to use**: When the new architecture is fundamentally different and you need both versions working simultaneously.

**Pros**:
- Complete independence between versions
- No risk of breaking the working osmnx version
- Can deploy both versions separately
- Clear separation of dependencies and configurations
- Easy to maintain different deployment pipelines

**Cons**:
- Duplicate code for shared components
- Harder to share improvements between versions
- Need to maintain two repositories

**How to do it**:
```bash
# Create a new repository
# Name it something like "Jadlo-GraphHopper" or "Jadlo-v2"
# Copy the codebase and start the migration

# Keep the original "Jadlo" repository with osmnx
```

### Option 2: Long-Lived Branches (For Parallel Development)

**When to use**: When you want to maintain both versions in the same repository but keep them separate.

**Pros**:
- Single repository with shared history
- Can cherry-pick improvements between branches
- Easier to share common code changes
- Single issue tracker and collaboration space

**Cons**:
- Need discipline to avoid merge conflicts
- Branch can diverge significantly over time
- Deployment requires specifying branch

**How to do it**:
```bash
# Create a long-lived branch for GraphHopper
git checkout -b engine/graphhopper

# This branch will live alongside main for extended period
# Deploy from main for osmnx version
# Deploy from engine/graphhopper for GraphHopper version

# Periodically merge common improvements
git checkout engine/graphhopper
git merge main  # or cherry-pick specific commits
```

### Option 3: Feature Flags / Adapter Pattern (For Gradual Migration)

**When to use**: When you want both engines available in the same codebase with runtime switching.

**Pros**:
- Single codebase with both engines
- Can switch at runtime via configuration
- Gradual migration path
- Can A/B test different engines

**Cons**:
- More complex codebase
- Need abstraction layer for routing engines
- Larger dependency footprint
- More complex deployment

**How to do it**:
```python
# Create an adapter interface
class RoutingEngine(ABC):
    @abstractmethod
    def compute_route(self, start, end, params):
        pass

class OSMnxEngine(RoutingEngine):
    def compute_route(self, start, end, params):
        # Current osmnx implementation
        pass

class GraphHopperEngine(RoutingEngine):
    def compute_route(self, start, end, params):
        # New GraphHopper implementation
        pass

# Select engine via configuration
ENGINE = os.getenv('ROUTING_ENGINE', 'osmnx')
engine = OSMnxEngine() if ENGINE == 'osmnx' else GraphHopperEngine()
```

### Recommendation for GraphHopper Migration

For a major architectural change like switching to GraphHopper:

1. **If prototyping/experimenting**: Use a **long-lived branch** (`engine/graphhopper`)
   - Easy to start, can decide later whether to merge or split

2. **If planning production deployment of both**: Create a **separate repository**
   - Better for maintaining two independent production systems
   - Cleaner separation of concerns

3. **If building a unified platform**: Use **adapter pattern**
   - Best long-term architecture
   - Requires more upfront design work

### Migration Checklist

When migrating to a different routing engine:

- [ ] Document the decision and rationale
- [ ] List incompatible features and breaking changes
- [ ] Plan for data migration (if applicable)
- [ ] Update deployment scripts and documentation
- [ ] Consider backwards compatibility requirements
- [ ] Plan for gradual rollout or A/B testing
- [ ] Update CI/CD pipelines
- [ ] Document differences in API and behavior

## The Two Graph Approaches in Jadlo (Current osmnx-based Implementation)

Jadlo currently implements two different graph-based routing approaches. Understanding these will help you choose the right approach for your use case.

### 1. Full Graph Approach (Larger Graphs)

**Function**: `compute_route()` in `app/routing.py`

**How it works**:
- Fetches the complete OSM graph for the area
- Includes all nodes: intersections, curves, and intermediate points along roads
- Uses Dijkstra's algorithm via NetworkX's `shortest_path`
- Computes weights for every edge in the graph

**Pros**:
- More accurate route representation with detailed geometry
- Captures all road curvature and details
- Better for short-to-medium routes
- Well-tested and stable

**Cons**:
- Higher memory usage for large areas
- Slower for long-distance routing
- May hit Overpass API rate limits on very large areas

**Best for**:
- Routes under 50km
- Areas with good connectivity
- When precise road geometry is important
- When memory and computation time are not constraints

### 2. Intersection-Based Approach (Smaller Graphs)

**Function**: `compute_route_intersections()` in `app/routing.py`

**How it works**:
- Simplifies the graph by collapsing degree-2 nodes (nodes along straight sections)
- Keeps only intersection nodes (junctions, endpoints)
- Uses A* algorithm with geographic heuristic
- Applies heading bias to prefer continuing straight
- Reconstructs full geometry from simplified paths

**Pros**:
- Significantly lower memory usage
- Faster for long-distance routing
- Better suited for resource-constrained environments (Codespaces, free hosting)
- Makes routing decisions only at meaningful junction points

**Cons**:
- More complex implementation
- Experimental status (may have edge cases)
- Requires additional geometry reconstruction step
- May need parameter tuning per region

**Best for**:
- Long routes (>50km)
- Resource-constrained environments
- When memory efficiency is critical
- Avoiding Overpass API timeouts

## Recommended Workflow for Exploring Both Approaches

### Step 1: Create Feature Branches

```bash
# For exploring full graph improvements
git checkout -b feature/optimize-full-graph

# For exploring intersection-based improvements
git checkout -b feature/optimize-intersection-routing
```

### Step 2: Document Your Changes

In each branch, clearly document:
- What you're testing/improving
- Performance characteristics
- Trade-offs observed
- Recommended use cases

### Step 3: Compare and Measure

Create benchmarks to compare approaches:

```python
# Example benchmark script
from app.routing import compute_route, compute_route_intersections
import time

start = (52.2297, 21.0122)
end = (53.1325, 23.1688)
params = {
    'prefer_main_roads': 0.5,
    'prefer_unpaved': 0.2,
    'heatmap_influence': 0.0,
    'surface_weight_factor': 1.5
}

# Test full graph approach
t0 = time.time()
coords1, gpx1 = compute_route(start, end, params, radius_meters=8000)
time1 = time.time() - t0

# Test intersection approach
t0 = time.time()
coords2, gpx2 = compute_route_intersections(start, end, params, radius_meters=8000)
time2 = time.time() - t0

print(f"Full graph: {time1:.2f}s, {len(coords1)} points")
print(f"Intersection: {time2:.2f}s, {len(coords2)} points")
```

### Step 4: Merge the Best Features

Once you've determined which approach works best for different scenarios:

```bash
# Merge improvements back to main
git checkout main
git merge feature/optimize-full-graph
# or
git merge feature/optimize-intersection-routing
```

Or keep both approaches and add routing logic to choose automatically based on distance:

```python
def smart_route(start, end, params, **kwargs):
    """Automatically choose the best routing approach based on distance."""
    distance = haversine_distance(start, end)
    
    if distance < 50000:  # Less than 50km
        return compute_route(start, end, params, **kwargs)
    else:
        return compute_route_intersections(start, end, params, **kwargs)
```

## Example: Setting Up to Explore Both Approaches

```bash
# Start from the main branch
git checkout main

# Create a branch for full-graph experimentation
git checkout -b experiment/full-graph-optimizations
# Make changes, test, commit
git add .
git commit -m "Optimize full graph memory usage"

# Return to main and create a branch for intersection-based work
git checkout main
git checkout -b experiment/intersection-routing-improvements
# Make changes, test, commit
git add .
git commit -m "Improve intersection detection algorithm"

# Compare results
git checkout experiment/full-graph-optimizations
python scripts/benchmark_approach.py --approach full

git checkout experiment/intersection-routing-improvements
python scripts/benchmark_approach.py --approach intersection

# Decide which to merge or keep both
```

## Best Practices

1. **Keep branches focused**: Each branch should explore one specific aspect
2. **Document everything**: Update README.md and docs/ with your findings
3. **Add tests**: Ensure both approaches maintain quality standards
4. **Benchmark regularly**: Track performance, memory, and quality metrics
5. **Regular commits**: Small, focused commits make comparison easier
6. **Meaningful names**: Use descriptive branch names like `feature/intersection-heading-bias` or `experiment/full-graph-caching`

## Current Status

As of this writing:
- Both approaches are implemented in `app/routing.py`
- Full graph approach is well-tested and stable
- Intersection-based approach is experimental but promising
- Choose based on your specific route length and memory constraints

## Questions?

- For general routing questions, see `docs/APPLICATION_DOCUMENTATION.md`
- For algorithm details, see `docs/ALGORITHM_CHOICE.md`
- For performance comparisons, see `docs/ROUTING_ALGORITHMS_COMPARISON.md`

## Summary

**Don't fork unless you're creating an independent project. Use branches to explore different approaches, and merge the best features back to main.**
