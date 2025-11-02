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

1. **Performance**: Route generation must complete within time limits
   - 30km routes: <90 seconds
   - 60km routes: <150 seconds  
   - 100km routes: <240 seconds (4 minutes)
   - Each test displays generation time and timestamps for monitoring
   
2. **Route Quality**: No gaps or straight lines larger than 1km
   - Ensures routes follow actual road networks
   - Prevents unrealistic straight-line shortcuts

3. **Surface Preference**: Routes configured to prefer paved surfaces have >80% paved roads
   - Validates the surface_weight_factor parameter works correctly

**Test Suite:** `tests/test_integration_requirements.py`

The workflow runs each test as a separate step with descriptive names:
- "Performance test - 30km route generation"
- "Performance test - 60km route generation"
- "Performance test - 100km route generation"
- "Quality test - Check for gaps in 100km route"
- "Surface preference test - Paved surface routing"

**Running Locally:**
```bash
# Run all route quality tests
PYTHONPATH=. python -m pytest tests/test_integration_requirements.py -v -s

# Run individual performance tests
PYTHONPATH=. python -m pytest tests/test_integration_requirements.py::test_30km_route_performance -v -s
PYTHONPATH=. python -m pytest tests/test_integration_requirements.py::test_60km_route_performance -v -s
PYTHONPATH=. python -m pytest tests/test_integration_requirements.py::test_100km_route_performance -v -s

# Run quality tests
PYTHONPATH=. python -m pytest tests/test_integration_requirements.py::test_100km_route_no_large_gaps -v -s
PYTHONPATH=. python -m pytest tests/test_integration_requirements.py::test_100km_route_paved_surface_preference -v -s
```

**System Requirements:**
- Ubuntu latest (GitHub runner)
- Python 3.12
- System libraries: libgeos-dev, libproj-dev, libgdal-dev (required by osmnx)

**Timeout:** Each test step has its own timeout (5-8 minutes) appropriate for the route distance being tested.

**Blocking:** If any test fails, the workflow will fail and block the pull request from being merged.

## Notes

- These tests require network access to fetch OSM data from the Overpass API
- Tests will skip (not fail) if network is unavailable or OSM data cannot be fetched
- See `docs/INTEGRATION_TESTS.md` for detailed test documentation
