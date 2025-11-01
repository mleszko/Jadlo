#!/usr/bin/env python3
"""Generate a long route by splitting into smaller segments and stitching GPX.

This helps running long routes inside constrained environments (Codespace) by
requesting multiple smaller graphs instead of one huge bbox.

Usage:
  python scripts/run_poc_segmented.py --start 52.2297 21.0122 --end 53.1325 23.1688 \
      --segment-km 20 --radius 8000 --out poc_route_segmented.gpx

Notes:
- The script linearly interpolates lat/lon points between start and end to create
  segment endpoints. For long distances you may prefer great-circle interpolation.
- If a segment fails to find a path, the script will attempt to retry with a
  larger radius (up to 3x) before failing.
"""
import argparse
import math
import time
from typing import List, Tuple

from app.routing import compute_route


def haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    R = 6371.0
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(h))


def interp_points(a: Tuple[float, float], b: Tuple[float, float], n: int) -> List[Tuple[float, float]]:
    # simple linear interpolation in lat/lon
    points = []
    for i in range(n+1):
        t = i / n
        lat = a[0] + (b[0]-a[0])*t
        lon = a[1] + (b[1]-a[1])*t
        points.append((lat, lon))
    return points


def stitch_coords(all_coords: List[List[Tuple[float, float]]]) -> List[Tuple[float, float]]:
    if not all_coords:
        return []
    stitched = list(all_coords[0])
    for seg in all_coords[1:]:
        if not seg:
            continue
        # avoid duplicate near-boundary points: drop leading points from seg until different
        i = 0
        while i < len(seg) and seg[i] == stitched[-1]:
            i += 1
        stitched.extend(seg[i:])
    return stitched


def run_segmented(start, end, params, segment_km=20, radius_m=8000, out='poc_route_segmented.gpx'):
    dist_km = haversine_km(start, end)
    n_segments = max(1, math.ceil(dist_km / segment_km))
    print(f'distance ~{dist_km:.1f} km, splitting into {n_segments} segments')

    points = interp_points(start, end, n_segments)
    all_coords = []
    all_gpx_parts = []

    for i in range(n_segments):
        s = points[i]
        e = points[i+1]
        attempt = 0
        success = False
        cur_radius = radius_m
        while attempt < 3 and not success:
            try:
                print(f'Computing segment {i+1}/{n_segments}, start={s}, end={e}, radius={cur_radius}')
                coords, gpx = compute_route(s, e, params, radius_meters=cur_radius)
                all_coords.append(coords)
                all_gpx_parts.append(gpx)
                success = True
            except Exception as exc:
                attempt += 1
                cur_radius = int(cur_radius * 1.5)
                print(f'  segment failed (attempt {attempt}): {exc}. retrying with radius {cur_radius} in 2s')
                time.sleep(2)
        if not success:
            raise RuntimeError(f'Failed to compute segment {i+1} after retries')
        # small pause to be nice to Overpass
        time.sleep(1)

    stitched = stitch_coords(all_coords)

    # generate simple GPX from stitched coords
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
        gpx_str = gpx.to_xml()
    except Exception:
        # fallback: use concatenation of first segment GPX
        gpx_str = all_gpx_parts[0]

    with open(out, 'w', encoding='utf-8') as f:
        f.write(gpx_str)

    print(f'Wrote {out}, total points={len(stitched)}')
    return stitched, out


def parse_args():
    p = argparse.ArgumentParser(description='Run segmented PoC route generation')
    p.add_argument('--start', type=float, nargs=2, required=True)
    p.add_argument('--end', type=float, nargs=2, required=True)
    p.add_argument('--segment-km', type=float, default=20)
    p.add_argument('--radius', type=int, default=8000)
    p.add_argument('--out', type=str, default='poc_route_segmented.gpx')
    return p.parse_args()


def main():
    args = parse_args()
    params = {'prefer_main_roads': 0.5, 'prefer_unpaved': 0.2, 'heatmap_influence': 0.0, 'prefer_streetview': 0.0}
    run_segmented(tuple(args.start), tuple(args.end), params, segment_km=args.segment_km, radius_m=args.radius, out=args.out)


if __name__ == '__main__':
    main()
