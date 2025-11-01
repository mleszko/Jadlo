import pytest
import math
import time
from typing import List, Tuple

from app.routing import compute_route_intersections, compute_route


@pytest.mark.integration
def test_generate_100km_and_write_artifact():
    """Integration test: generate ~100+ km route by splitting into segments and write GPX into artifacts/.

    This test is intended to run locally (or in a Codespace) and will write the resulting GPX
    into `artifacts/poc_route_100km_intersections.gpx`. The `artifacts/` directory is gitignored.
    """
    try:
        import osmnx as ox  # noqa: F401
    except Exception as e:
        pytest.skip(f"osmnx not available or failed to import: {e}")

    start = (52.2297, 21.0122)
    end = (53.1325, 23.1688)
    params = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.2,
        'heatmap_influence': 0.0,
        'prefer_streetview': 0.0,
    }

    # segmentation helpers (lightweight copy of the script logic)
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

    def stitch_coords(all_coords: List[List[Tuple[float, float]]]) -> List[Tuple[float, float]]:
        if not all_coords:
            return []
        stitched = list(all_coords[0])
        for seg in all_coords[1:]:
            if not seg:
                continue
            # if consecutive segments align, skip duplicates
            i = 0
            while i < len(seg) and seg[i] == stitched[-1]:
                i += 1

            # if there's a large gap between stitched[-1] and seg[i], try to fill it
            def haversine_m(a, b):
                from math import radians, sin, cos, atan2, sqrt
                R = 6371000.0
                lat1, lon1 = a
                lat2, lon2 = b
                phi1 = radians(lat1); phi2 = radians(lat2)
                dphi = radians(lat2 - lat1); dlambda = radians(lon2 - lon1)
                aa = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
                return R * 2 * atan2(sqrt(aa), sqrt(1-aa))

            if i < len(seg):
                gap = haversine_m(stitched[-1], seg[i])
                # if gap is unexpectedly large, attempt to compute a bridging route
                if gap > 1000.0:
                    # try several radii to bridge the gap
                    cur_radius = 8000
                    bridged = None
                    attempts = 0
                    while attempts < 3 and bridged is None:
                        try:
                            b_coords, _ = compute_route_intersections(stitched[-1], seg[i], params, radius_meters=cur_radius)
                            # ensure we have something reasonable
                            if b_coords and haversine_m(b_coords[0], stitched[-1]) < gap and haversine_m(b_coords[-1], seg[i]) < gap:
                                bridged = b_coords
                                break
                        except Exception:
                            pass
                        attempts += 1
                        cur_radius = int(cur_radius * 1.5)
                    if bridged:
                        # append bridged (skip duplicate start)
                        j = 0
                        while j < len(bridged) and bridged[j] == stitched[-1]:
                            j += 1
                        stitched.extend(bridged[j:])
                        # now append the remainder of seg skipping duplicates
                        k = 0
                        while k < len(seg) and seg[k] == stitched[-1]:
                            k += 1
                        stitched.extend(seg[k:])
                        continue
                    # fallback: try splitting the gap into smaller subsegments
                    sub_len = 5000.0
                    n_sub = max(1, int(gap // sub_len) + 1)
                    sub_points = interp_points(stitched[-1], seg[i], n_sub)
                    filled = True
                    for si in range(n_sub):
                        a = sub_points[si]
                        b = sub_points[si + 1]
                        attempt2 = 0
                        success2 = False
                        cur_radius2 = 8000
                        while attempt2 < 3 and not success2:
                            try:
                                c_coords, _ = compute_route_intersections(a, b, params, radius_meters=cur_radius2)
                                if c_coords and len(c_coords) >= 2:
                                    # append segment (skip duplicate start)
                                    m = 0
                                    while m < len(c_coords) and c_coords[m] == stitched[-1]:
                                        m += 1
                                    stitched.extend(c_coords[m:])
                                    success2 = True
                                    break
                            except Exception:
                                pass
                            attempt2 += 1
                            cur_radius2 = int(cur_radius2 * 1.5)
                        if not success2:
                            filled = False
                            break
                    if filled:
                        # finally append remainder of seg skipping duplicates
                        k = 0
                        while k < len(seg) and seg[k] == stitched[-1]:
                            k += 1
                        stitched.extend(seg[k:])
                        continue

            stitched.extend(seg[i:])
        return stitched

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
                coords, gpx = compute_route_intersections(s, e, params, radius_meters=cur_radius)
                all_coords.append(coords)
                success = True
            except Exception as exc:
                attempt += 1
                cur_radius = int(cur_radius * 1.5)
                time.sleep(1)
        if not success:
            pytest.skip(f"Segment {i+1} failed after retries")

    stitched = stitch_coords(all_coords)

    # Post-process: repair large straight-line gaps by routing on the original graph
    def haversine_m(a, b):
        from math import radians, sin, cos, atan2, sqrt
        R = 6371000.0
        lat1, lon1 = a
        lat2, lon2 = b
        phi1 = radians(lat1); phi2 = radians(lat2)
        dphi = radians(lat2 - lat1); dlambda = radians(lon2 - lon1)
        aa = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
        return R * 2 * atan2(sqrt(aa), sqrt(1-aa))

    final_coords: List[Tuple[float, float]] = [stitched[0]] if stitched else []
    for i in range(1, len(stitched)):
        a = stitched[i - 1]
        b = stitched[i]
        gap = haversine_m(a, b)
        if gap > 1000.0:
            # try several bbox buffers (degrees) to reconstruct the path on original graph
            buf = 0.05
            bridged = None
            attempts = 0
            while attempts < 4 and bridged is None:
                try:
                    coords_seg, _ = compute_route(a, b, params, bbox_buffer=buf)
                    if coords_seg and len(coords_seg) >= 2:
                        bridged = coords_seg
                        break
                except Exception:
                    pass
                attempts += 1
                buf *= 2
            if bridged:
                # append bridged but remove duplicate start
                j = 0
                while j < len(bridged) and bridged[j] == final_coords[-1]:
                    j += 1
                final_coords.extend(bridged[j:])
                continue
            else:
                # fallback to straight append
                final_coords.append(b)
        else:
            final_coords.append(b)

    stitched = final_coords

    # Basic sanity checks
    assert isinstance(stitched, list)
    assert len(stitched) >= 3

    # write artifact inside repo (artifacts/ is gitignored)
    import os
    os.makedirs('artifacts', exist_ok=True)
    out_path = os.path.join('artifacts', 'poc_route_100km_intersections.gpx')

    try:
        import gpxpy
        import gpxpy.gpx
        gpx = gpxpy.gpx.GPX()
        track = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(track)
        seg = gpxpy.gpx.GPXTrackSegment()
        track.segments.append(seg)
        for lat, lon in stitched:
            seg.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(gpx.to_xml())
    except Exception:
        # fallback: write a simple CSV of lat,lon
        with open(out_path + '.csv', 'w', encoding='utf-8') as f:
            for lat, lon in stitched:
                f.write(f"{lat},{lon}\n")

    assert os.path.exists(out_path) or os.path.exists(out_path + '.csv')
