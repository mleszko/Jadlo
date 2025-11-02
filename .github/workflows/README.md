# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automated testing and quality checks.

## Route Quality Check

**File:** `route-quality-check.yml`

**Purpose:** Automatically validates that every commit meets route quality and performance requirements.

**Triggers:**
- Push to `main` branch
- Push to any `copilot/**` branch
- Pull requests targeting `main` branch

**Requirements Validated:**

1. **Performance**: Route generation for 100km routes must complete within 3 minutes (180 seconds)
   - Original requirement was <5 minutes; tests enforce the stricter 3-minute limit
   
2. **Route Quality**: No gaps or straight lines larger than 1km
   - Ensures routes follow actual road networks
   - Prevents unrealistic straight-line shortcuts

3. **Surface Preference**: Routes configured to prefer paved surfaces have >80% paved roads
   - Validates the surface_weight_factor parameter works correctly

**Test Suite:** `tests/test_integration_requirements.py`

**Running Locally:**
```bash
# Run all route quality tests
PYTHONPATH=. python -m pytest tests/test_integration_requirements.py -v -s

# Run individual tests
PYTHONPATH=. python -m pytest tests/test_integration_requirements.py::test_100km_route_performance -v -s
PYTHONPATH=. python -m pytest tests/test_integration_requirements.py::test_100km_route_no_large_gaps -v -s
```

**System Requirements:**
- Ubuntu latest (GitHub runner)
- Python 3.12
- System libraries: libgeos-dev, libproj-dev, libgdal-dev (required by osmnx)

**Timeout:** The workflow has a 15-minute timeout to ensure it doesn't run indefinitely.

**Blocking:** If any test fails, the workflow will fail and block the pull request from being merged.

## Notes

- These tests require network access to fetch OSM data from the Overpass API
- Tests will skip (not fail) if network is unavailable or OSM data cannot be fetched
- See `docs/INTEGRATION_TESTS.md` for detailed test documentation
