import os
import math
import time
from pathlib import Path
from typing import List, Tuple

import pytest
import gpxpy

import osmnx as ox

from app import routing


SURFACE_UNPAVED = {'gravel', 'unpaved', 'dirt'}


def _haversine(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    from math import radians, sin, cos, atan2, sqrt

    lat1, lon1 = a
    lat2, lon2 = b
    R = 6371000.0
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    aa = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return R * 2 * atan2(math.sqrt(aa), math.sqrt(1 - aa))


def _read_gpx_points(path: Path) -> List[Tuple[float, float]]:
    gpx = gpxpy.parse(path.read_text())
    pts: List[Tuple[float, float]] = []
    for trk in gpx.tracks:
        for seg in trk.segments:
            for p in seg.points:
                pts.append((p.latitude, p.longitude))
    return pts


def _build_graph_for_points(pts: List[Tuple[float, float]], buffer_m: int = 2000):
    # build bbox around points with buffer in meters -> approx degrees
    lats = [p[0] for p in pts]
    lons = [p[1] for p in pts]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    # approx degrees per meter (latitude)
    deg_buf = buffer_m / 111320.0
    north = max_lat + deg_buf
    south = min_lat - deg_buf
    east = max_lon + deg_buf
    west = min_lon - deg_buf
    G = ox.graph_from_bbox(north, south, east, west, network_type='bike')
    return G


def _nearest_edge_surface(G, lat, lon):
    # try ox.distance.nearest_edges which may accept scalar or lists
    try:
        res = ox.distance.nearest_edges(G, lon, lat)
        if isinstance(res, tuple) and len(res) >= 2:
            u, v = res[0], res[1]
            key = res[2] if len(res) > 2 else 0
        else:
            u, v, key = res
    except Exception:
        # fallback: find nearest node and inspect incident edges
        try:
            node = ox.distance.nearest_nodes(G, lon, lat)
        except Exception:
            return None
        # inspect edges incident on node and pick first with surface
        for nbr in G[node]:
            ed = G.get_edge_data(node, nbr)
            if ed:
                data = next(iter(ed.values()))
                return data.get('surface')
        return None

    ed = G.get_edge_data(u, v)
    if not ed:
        return None
    data = next(iter(ed.values()))
    return data.get('surface')


@pytest.mark.skipif(not Path('artifacts/poc_route_100km_intersections.gpx').exists(), reason='artifact missing')
def test_count_unpaved_in_artifact():
    """Count how many GPX points lie on edges with unpaved surfaces.

    This test prints the counts and the fraction. It asserts that we have points.
    """
    p = Path('artifacts/poc_route_100km_intersections.gpx')
    pts = _read_gpx_points(p)
    assert len(pts) > 0

    # Build a single graph for the whole GPX bounding box (one-time cost).
    print('building single bbox graph for artifact...')
    t0 = time.perf_counter()
    # compute bbox with a modest buffer in degrees
    lats = [p[0] for p in pts]
    lons = [p[1] for p in pts]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    # buffer ~0.05 deg (~5 km) to capture nearby edges
    buf = 0.05
    G = ox.graph_from_bbox(max_lat + buf, min_lat - buf, max_lon + buf, min_lon - buf, network_type='bike')
    t1 = time.perf_counter()
    print(f'built graph: nodes={len(G.nodes)} edges={len(G.edges)} took {t1-t0:.2f}s')

    # Count unpaved by finding nearest edge for each point (fast now that graph is in memory)
    unpaved_count = 0
    looked = 0
    t_loop = time.perf_counter()
    for i, (lat, lon) in enumerate(pts):
        try:
            res = ox.distance.nearest_edges(G, lon, lat)
            # res may be tuple (u,v,key) or arrays; handle tuple
            if isinstance(res, tuple):
                u, v = res[0], res[1]
            else:
                u, v = res[0], res[1]
            ed = G.get_edge_data(u, v)
            surf = None
            if ed:
                data = next(iter(ed.values()))
                surf = data.get('surface')
            if isinstance(surf, list):
                surf = surf[0]
            if surf in SURFACE_UNPAVED:
                unpaved_count += 1
            looked += 1
        except Exception:
            # skip points that cannot be matched
            continue
        if i < 5 or i % 500 == 0:
            print(f'checked {i+1}/{len(pts)}')
    t_loop_end = time.perf_counter()

    frac = unpaved_count / max(1, looked)
    print(f'points={len(pts)} looked={looked} unpaved={unpaved_count} frac={frac:.3f} build_time={t1-t0:.2f}s loop_time={t_loop_end-t_loop:.2f}s')


def test_generate_100km_strict_avoid_unpaved():
    """Run a segmented generation where unpaved surfaces are heavily penalized.

    This will write a new artifact `artifacts/poc_route_100km_intersections_avoid_unpaved.gpx`.
    """
    try:
        import osmnx as _ox  # noqa: F401
    except Exception as e:
        pytest.skip(f"osmnx not available: {e}")

    # monkeypatch _edge_penalty to forbid unpaved surfaces by assigning huge weight
    orig_penalty = routing._edge_penalty

    def strict_penalty(u, v, key, data, params):
        surf = data.get('surface')
        if isinstance(surf, list):
            surf = surf[0]
        if surf in SURFACE_UNPAVED:
            # return very large cost
            return data.get('length', 1.0) * 1e6
        return orig_penalty(u, v, key, data, params)

    routing._edge_penalty = strict_penalty

    # run segmented generation (copy of test logic) and write artifact
    start = (52.2297, 21.0122)
    end = (53.1325, 23.1688)
    params = {
        'prefer_main_roads': 1.0,
        'prefer_unpaved': 0.0,
        'heatmap_influence': 0.0,
        'prefer_streetview': 0.0,
    }

    def haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
        lat1, lon1 = math.radians(a[0]), math.radians(a[1])
        lat2, lon2 = math.radians(b[0]), math.radians(b[1])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        R = 6371.0
        h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return 2 * R * math.asin(math.sqrt(h))

    def interp_points(a: Tuple[float, float], b: Tuple[float, float], n: int) -> List[Tuple[float, float]]:
        points = []
        for i in range(n + 1):
            t = i / n
            lat = a[0] + (b[0] - a[0]) * t
            lon = a[1] + (b[1] - a[1]) * t
            points.append((lat, lon))
        return points

    dist_km = haversine_km(start, end)
    segment_km = 20.0
    n_segments = max(1, math.ceil(dist_km / segment_km))
    points = interp_points(start, end, n_segments)
    all_coords = []

    for i in range(n_segments):
        s = points[i]
        e = points[i + 1]
        attempt = 0
        success = False
        cur_radius = 8000
        while attempt < 3 and not success:
            try:
                coords, gpx = routing.compute_route_intersections(s, e, params, radius_meters=cur_radius)
                all_coords.append(coords)
                success = True
            except Exception:
                attempt += 1
                cur_radius = int(cur_radius * 1.5)
                time.sleep(1)
        if not success:
            pytest.skip(f"Segment {i+1} failed after retries")

    # stitch
    stitched: List[Tuple[float, float]] = []
    for seg in all_coords:
        if not stitched:
            stitched.extend(seg)
            continue
        # avoid duplicates
        i = 0
        while i < len(seg) and seg[i] == stitched[-1]:
            i += 1
        stitched.extend(seg[i:])

    os.makedirs('artifacts', exist_ok=True)
    out_path = Path('artifacts/poc_route_100km_intersections_avoid_unpaved.gpx')
    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(track)
    segobj = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segobj)
    for lat, lon in stitched:
        segobj.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
    out_path.write_text(gpx.to_xml(), encoding='utf-8')

    # restore original penalty
    routing._edge_penalty = orig_penalty

    # quick check: ensure file exists
    assert out_path.exists()
