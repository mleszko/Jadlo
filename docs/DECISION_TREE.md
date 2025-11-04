# Decision Trees for Jadlo

## Decision Tree 1: Fork or Branch?

```
┌─────────────────────────────────────────┐
│  Do you want to explore different       │
│  approaches within Jadlo?               │
└─────────────────────────────────────────┘
                    │
                    ├── YES ──────────────────────────────┐
                    │                                      │
                    └── NO ───────────────────────────┐   │
                                                       │   │
        ┌──────────────────────────────────────────┐ │   │
        │  Do you want to create an independent    │ │   │
        │  project based on this codebase?         │ │   │
        └──────────────────────────────────────────┘ │   │
                    │                                 │   │
                    ├── YES ──┐                       │   │
                    │         │                       │   │
                    └── NO ───┼───────────────────────┤   │
                              │                       │   │
                     ┌────────▼──────────┐            │   │
                     │                   │            │   │
                     │  FORK THE REPO    │            │   │
                     │                   │            │   │
                     └───────────────────┘            │   │
                                                      │   │
                                         ┌────────────▼───▼────────────┐
                                         │                             │
                                         │  CREATE A BRANCH            │
                                         │  (git checkout -b ...)      │
                                         │                             │
                                         └─────────────────────────────┘
```

## Decision Tree 2: Which Graph Approach?

```
┌─────────────────────────────────────────┐
│  What is your route length?             │
└─────────────────────────────────────────┘
                    │
      ┌─────────────┼─────────────┐
      │             │             │
  < 20km        20-50km        > 50km
      │             │             │
      ▼             ▼             ▼
┌─────────┐   ┌──────────┐   ┌──────────────────┐
│         │   │ Memory   │   │                  │
│  FULL   │   │Available?│   │  INTERSECTION    │
│  GRAPH  │   └──────────┘   │  APPROACH        │
│         │         │         │                  │
└─────────┘    ┌────┴────┐   └──────────────────┘
               │         │
           > 4GB     < 4GB
               │         │
               ▼         ▼
         ┌─────────┐   ┌──────────────────┐
         │  FULL   │   │  INTERSECTION    │
         │  GRAPH  │   │  APPROACH        │
         └─────────┘   └──────────────────┘
```

## Decision Tree 3: Repository Strategy for Teams

```
┌─────────────────────────────────────────┐
│  Do you have write access to the repo?  │
└─────────────────────────────────────────┘
                    │
                    ├── YES ──────────────────────┐
                    │                              │
                    └── NO ───────────┐            │
                                      │            │
                            ┌─────────▼────────┐   │
                            │                  │   │
                            │  FORK FIRST,     │   │
                            │  then create PR  │   │
                            │                  │   │
                            └──────────────────┘   │
                                                   │
                                   ┌───────────────▼──────────────┐
                                   │  Working on a feature?       │
                                   └───────────────┬──────────────┘
                                                   │
                                        ┌──────────┴──────────┐
                                        │                     │
                                      YES                    NO
                                        │                     │
                                        ▼                     ▼
                              ┌────────────────────┐  ┌─────────────┐
                              │ CREATE BRANCH:     │  │             │
                              │ feature/xyz        │  │ USE main    │
                              └────────────────────┘  │             │
                                                      └─────────────┘
```

## Summary Table

| Scenario | Solution | Command |
|----------|----------|---------|
| Want to explore full-graph improvements | Create feature branch | `git checkout -b feature/optimize-full-graph` |
| Want to explore intersection-based improvements | Create feature branch | `git checkout -b feature/optimize-intersection` |
| Want to test both approaches | Use comparison script | `PYTHONPATH=. python scripts/compare_graph_approaches.py` |
| Creating completely new project | Fork repository | Click "Fork" on GitHub |
| Contributing without write access | Fork then PR | Fork → commit → create PR |
| Want to merge improvements | Merge branch to main | `git checkout main && git merge feature/xyz` |

## Quick Commands Reference

### Branch Workflow
```bash
# Create and switch to new branch
git checkout -b experiment/my-improvement

# Make changes and commit
git add .
git commit -m "Add my improvement"

# Push branch
git push origin experiment/my-improvement

# Switch back to main
git checkout main

# Merge when ready
git merge experiment/my-improvement
```

### Fork Workflow (External Contributors)
```bash
# 1. Fork on GitHub (use UI)

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/Jadlo.git

# 3. Add upstream remote
git remote add upstream https://github.com/mleszko/Jadlo.git

# 4. Create branch
git checkout -b my-contribution

# 5. Make changes and commit
git add .
git commit -m "My contribution"

# 6. Push to your fork
git push origin my-contribution

# 7. Create Pull Request on GitHub (use UI)
```

### Comparing Approaches
```bash
# Try both on a short route
PYTHONPATH=. python scripts/compare_graph_approaches.py --route short

# Try both on a long route
PYTHONPATH=. python scripts/compare_graph_approaches.py --route long

# Use in your code
from app.routing import compute_route, compute_route_intersections

# Full graph
coords, gpx = compute_route(start, end, params)

# Intersection-based
coords, gpx = compute_route_intersections(start, end, params)
```

## Related Documentation

- **[GRAPH_APPROACHES_QUICK_GUIDE.md](GRAPH_APPROACHES_QUICK_GUIDE.md)** - Detailed guide on which approach to use
- **[BRANCHING_STRATEGY.md](BRANCHING_STRATEGY.md)** - Complete branching strategy documentation
- **[APPLICATION_DOCUMENTATION.md](APPLICATION_DOCUMENTATION.md)** - Full technical documentation

## Visual Comparison

```
┌───────────────────────────────────────────────────────────┐
│                  FULL GRAPH APPROACH                      │
├───────────────────────────────────────────────────────────┤
│  • • • • • • • • •                                        │
│ • ─────────────── •  ← Every point along the road        │
│ •  •  •  •  •  •  •     is a node in the graph           │
│ • ───────────────  •                                      │
│  • • • • • • • • •                                        │
│                                                           │
│  Pros: Very detailed, accurate geometry                   │
│  Cons: High memory usage, many nodes to process           │
└───────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────┐
│              INTERSECTION-BASED APPROACH                  │
├───────────────────────────────────────────────────────────┤
│  •                                                        │
│  ●─────────────────●  ← Only intersection nodes          │
│  ●  ────────────────●     are kept in the graph          │
│  ●─────────────────●                                      │
│  •                                                        │
│                                                           │
│  Pros: Low memory, fast for long routes                   │
│  Cons: Must reconstruct detailed geometry                 │
└───────────────────────────────────────────────────────────┘
```

## Key Takeaway

**For exploring different approaches within Jadlo:**
- ✅ Use branches
- ❌ Don't fork

**For choosing a routing approach:**
- Short routes (<50km) → Full graph
- Long routes (>50km) → Intersection-based
- Limited memory → Intersection-based
- Need detailed geometry → Full graph
