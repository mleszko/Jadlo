# Quick Guide: Which Graph Approach and Repository Strategy?

## Your Question: Fork or Branch?

**Answer: Use branches, not a fork.**

Here's why:

```bash
# ✅ CORRECT: Create branches for different approaches
git checkout -b feature/optimize-large-graphs
git checkout -b feature/optimize-small-graphs

# ❌ AVOID: Forking creates an independent repository
# Only fork if you're creating a completely separate project
```

## The Two Approaches Explained Simply

### Approach 1: Larger Graphs (Full Detail)
- **What**: Uses all road nodes including curves and intermediate points
- **When**: Short routes (<50km), plenty of memory available
- **Function**: `compute_route()`
- **Think**: Like having a detailed street map with every curve marked

### Approach 2: Smaller Graphs (Intersections Only)
- **What**: Simplifies to just intersections, ignoring intermediate points
- **When**: Long routes (>50km), limited memory (Codespaces, free hosting)
- **Function**: `compute_route_intersections()`
- **Think**: Like having a simplified map showing only major junctions

## Quick Decision Guide

```
Route Length     Memory Available     Use This Approach
-----------     ----------------     -----------------
< 20km          Any                  compute_route()
20-50km         Plenty (>4GB*)       compute_route()
20-50km         Limited (<4GB*)      compute_route_intersections()
> 50km          Any                  compute_route_intersections()

* Memory threshold is approximate based on typical OSM graph sizes.
  Actual requirements depend on area density and road network complexity.
```

## How to Explore Both Approaches

### Option 1: Use Branches (Recommended)

```bash
# Work on large graph improvements
git checkout -b improve-large-graphs
# ... make changes ...
git commit -am "Improved memory handling for large graphs"

# Work on small graph improvements  
git checkout -b improve-small-graphs
# ... make changes ...
git commit -am "Better intersection detection"

# Compare results
git checkout improve-large-graphs
python test_route.py --approach large

git checkout improve-small-graphs  
python test_route.py --approach small

# Merge the winner (or keep both!)
git checkout main
git merge improve-large-graphs
```

### Option 2: Keep Both in Main (Current Status)

The codebase already has both approaches! You can:

```python
from app.routing import compute_route, compute_route_intersections

# Use large graphs
coords, gpx = compute_route(start, end, params, radius_meters=5000)

# Use small graphs
coords, gpx = compute_route_intersections(start, end, params, radius_meters=8000)
```

## Real-World Examples

### Example 1: Short City Route (10km)
```python
# Use full graph - better accuracy for short routes
from app.routing import compute_route

start = (52.2297, 21.0122)  # Warsaw
end = (52.2497, 21.0322)     # 10km away
params = {'prefer_main_roads': 0.5, 'surface_weight_factor': 1.5}

coords, gpx = compute_route(start, end, params, radius_meters=3000)
```

### Example 2: Long Inter-City Route (100km)
```python
# Use intersection graph - better memory efficiency
from app.routing import compute_route_intersections

start = (52.2297, 21.0122)  # Warsaw  
end = (53.1325, 23.1688)     # 100km away
params = {'prefer_main_roads': 0.5, 'surface_weight_factor': 1.5}

coords, gpx = compute_route_intersections(start, end, params, radius_meters=8000)
```

## Common Misconceptions

### ❌ "I need to fork to try both approaches"
✅ No! Both approaches already exist in the code. Just call different functions.

### ❌ "I need a new repository for each approach"  
✅ No! Use branches if you want to modify and compare approaches.

### ❌ "Forking is for experimentation"
✅ No! Forking is for creating independent projects. Branches are for experimentation.

## When You SHOULD Fork or Use Separate Repo

- You're creating a completely different route planner
- You want to take this code in a totally different direction
- You're not planning to merge changes back
- You don't have write access to the original repo
- **You're switching to a different routing engine** (e.g., osmnx → GraphHopper) and want both versions available

## Major Architecture Changes (e.g., Switching to GraphHopper)

If you're considering migrating from osmnx to GraphHopper or another routing engine, this is a **major architectural change**. You have three options:

1. **Separate Repository** (Recommended for production deployments)
   - Keep current osmnx version in "Jadlo" repo
   - Create new "Jadlo-GraphHopper" repo for GraphHopper version
   - Deploy both independently

2. **Long-Lived Branch** (For parallel development)
   - Create `engine/graphhopper` branch that lives alongside `main`
   - Both versions in same repo, deployed from different branches
   - Easier to share improvements between versions

3. **Adapter Pattern** (For runtime switching)
   - Both engines in same codebase with abstraction layer
   - Switch via configuration/environment variable
   - More complex but most flexible

See `docs/BRANCHING_STRATEGY.md` for detailed guidance on major architectural changes.

## Next Steps

1. **Try both approaches**: Run the examples above
2. **Measure performance**: See which works better for your routes
3. **Create branches**: If you want to improve either approach
4. **Read more details**: See `docs/BRANCHING_STRATEGY.md`

## TL;DR

| Goal | Action |
|------|--------|
| Try both osmnx approaches | Use the existing functions - no fork needed |
| Improve one osmnx approach | Create a branch (not a fork) |
| **Switch to GraphHopper (both versions live)** | **Separate repository or long-lived branch** |
| **Switch to GraphHopper (experiment only)** | **Long-lived branch: `engine/graphhopper`** |
| Create a new project | Fork the repository |
| Compare osmnx approaches | Create separate branches for each |
| Ship to production | Merge your branch to main |

**Bottom line for osmnx improvements**: Use branches, not forks.

**Bottom line for major engine changes** (osmnx → GraphHopper): Consider separate repository or long-lived branch depending on whether you need both in production.
