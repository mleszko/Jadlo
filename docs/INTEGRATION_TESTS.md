# Integration Tests for PR Merge Requirements

This document describes the integration tests created to validate the surface-based routing implementation before merging to main.

## Test Suite: `test_integration_requirements.py`

### Test 1: Performance - 100km Route Generation Time

**Test:** `test_100km_route_performance()`

**Requirement:** Generating a 100km route must take no longer than 3 minutes (180 seconds).

**Implementation:**
- Generates a ~130km route from Warsaw area using segmented routing
- Measures total execution time including all segments and retries
- Segments are 20km each with up to 3 retry attempts per segment
- Uses `compute_route_intersections()` with 8000m radius

**Success Criteria:**
- Total execution time < 180 seconds
- At least 10 route points generated
- All segments complete successfully or test is skipped

**Why This Matters:** Performance is critical for production use. Users expect responsive route generation, and 3 minutes is a reasonable upper bound for a 100km route.

---

### Test 2: Route Quality - No Large Gaps

**Test:** `test_100km_route_no_large_gaps()`

**Requirement:** Generated route must have no gaps or straight lines larger than 1km between consecutive points.

**Implementation:**
- Generates the same ~130km route with gap detection and bridging
- Calculates haversine distance between all consecutive coordinate pairs
- Attempts to bridge any gaps >1km using `compute_route_intersections()`
- Reports all gaps and identifies the largest one

**Success Criteria:**
- No gaps exceed 1000 meters between consecutive points
- Route follows actual road geometry rather than straight-line shortcuts
- Maximum gap and average gap are reported for transparency

**Why This Matters:** Large gaps indicate the routing algorithm is taking shortcuts through areas without road data, resulting in unrealistic routes. This validates that the algorithm follows actual road networks.

---

### Test 3: Surface Preference - Paved Road Coverage

**Test:** `test_100km_route_paved_surface_preference()`

**Requirement:** When configured to prefer paved surfaces (high `surface_weight_factor`), the generated route must have more than 80% paved roads.

**Implementation:**
- Generates a ~25km route with `surface_weight_factor=2.5` (strong paved preference)
- Fetches the OSM graph for the area with surface data
- Analyzes each edge in the route to determine surface type
- Categorizes surfaces as: paved (asphalt/concrete/paved), unpaved (gravel/dirt), or unknown
- Calculates percentage of paved roads from edges with known surface data

**Success Criteria:**
- >80% of route edges with known surface data are paved
- Route prioritizes paved surfaces even if they're slightly longer
- Surface statistics are reported (paved %, unpaved %, unknown %)

**Why This Matters:** This validates that the new `surface_weight_factor` parameter actually influences route selection. A high factor should strongly prefer paved surfaces, demonstrating the core feature of this PR.

---

## Running the Tests

### Run all integration tests:
```bash
PYTHONPATH=. python -m pytest tests/test_integration_requirements.py -v -s
```

### Run individual tests:
```bash
# Performance test only
PYTHONPATH=. python -m pytest tests/test_integration_requirements.py::test_100km_route_performance -v -s

# Gap test only
PYTHONPATH=. python -m pytest tests/test_integration_requirements.py::test_100km_route_no_large_gaps -v -s

# Surface preference test only
PYTHONPATH=. python -m pytest tests/test_integration_requirements.py::test_100km_route_paved_surface_preference -v -s
```

### Run with markers:
```bash
# Run all integration tests (these are marked with @pytest.mark.integration)
PYTHONPATH=. python -m pytest -m integration -v -s
```

---

## Test Dependencies

- **osmnx**: Required for fetching OSM data and graphs
- **networkx**: Used by routing algorithms (Dijkstra/A*)
- **gpxpy**: For GPX generation (optional, tests work without it)
- **pytest**: Test framework

These tests will automatically skip if `osmnx` is not available or if network issues prevent OSM data fetching.

---

## Test Output Examples

### Successful Performance Test:
```
✓ Performance test passed: 145.3s for 130.2km route (7 segments)
```

### Successful Gap Test:
```
✓ Gap test passed: No gaps >1km in route with 3847 points
  Max gap: 892m, Avg gap: 34m
```

### Successful Surface Test:
```
✓ Surface analysis:
  Total route length: 24.81km
  Paved: 87.3% (21.66km)
  Unpaved: 8.2% (2.04km)
  Unknown: 4.5% (1.11km)
```

---

## Notes

- **Network dependency**: These tests require internet access to fetch OSM data via Overpass API
- **Rate limiting**: Tests include retry logic and delays to handle Overpass rate limits
- **Data quality**: Surface coverage depends on OSM data completeness in the test area
- **Timing variation**: Performance can vary based on network speed and Overpass API load
- **Skip conditions**: Tests will skip (not fail) if network is unavailable or OSM data cannot be fetched

---

## Troubleshooting

**Test takes too long:**
- Reduce `segment_km` to use fewer segments
- Reduce `n_segments` for shorter test routes
- Check network connectivity to Overpass API

**Gap test fails:**
- Check if OSM data is complete for the test area
- Increase `radius_meters` in bridging attempts
- Review gap-filling logic in test

**Surface test fails:**
- Verify OSM data includes surface tags for the test area
- Adjust `surface_weight_factor` (try 3.0 for even stronger preference)
- Choose a different test area with better OSM surface data
- Check if the surface penalty calculation is working correctly

**Tests skip:**
- Install osmnx: `pip install osmnx`
- Check internet connectivity
- Try running tests individually to isolate issues
