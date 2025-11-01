import pytest
from app.routing import compute_route


@pytest.mark.integration
def test_generate_50km(tmp_path):
    """Integration-style test: attempts to generate ~50 km route between Warsaw and Wyszków.
    Skips if osmnx (or network/deps) unavailable.
    """
    try:
        import osmnx as ox  # noqa: F401
    except Exception as e:
        pytest.skip(f"osmnx not available or failed to import: {e}")

    start = (52.2297, 21.0122)  # Warszawa
    end = (52.5920, 21.4610)    # okolice Wyszkowa (~50 km)

    params = {'prefer_main_roads': 0.5, 'prefer_unpaved': 0.2, 'heatmap_influence': 0.0, 'prefer_streetview': 0.0}

    # Use a graph around the start point with a 3km radius to limit data size in CI/container.
    # Very small radius for constrained environment testing.
    coords, gpx = compute_route(start, end, params, radius_meters=3000)

    # Basic sanity checks
    assert isinstance(coords, list)
    assert len(coords) >= 3
    assert isinstance(gpx, str) and gpx.strip().startswith('<?xml')

    out = tmp_path / 'poc_route_50km.gpx'
    out.write_text(gpx)
    print(f'Wrote GPX to {out}')
