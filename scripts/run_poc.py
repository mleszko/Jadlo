#!/usr/bin/env python3
"""Simple CLI to run PoC route generation using app.routing.compute_route

Usage examples:
  python scripts/run_poc.py --start 52.2297 21.0122 --end 53.1325 23.1688 --radius 3000 --out poc.gpx
  # For long routes consider using bbox_buffer or run on a machine with enough RAM and use smaller corridor
"""
import argparse
from app.routing import compute_route


def parse_args():
    p = argparse.ArgumentParser(description='Run PoC route generation (OSMnx)')
    p.add_argument('--start', type=float, nargs=2, required=True, help='start lat lon')
    p.add_argument('--end', type=float, nargs=2, required=True, help='end lat lon')
    p.add_argument('--prefer_main_roads', type=float, default=0.5)
    p.add_argument('--prefer_unpaved', type=float, default=0.5)
    p.add_argument('--heatmap_influence', type=float, default=0.0)
    p.add_argument('--prefer_streetview', type=float, default=0.0)
    p.add_argument('--radius', type=float, default=None, help='radius (meters) around start point to limit graph')
    p.add_argument('--bbox-buffer', type=float, default=0.12, help='degree buffer for bbox if radius not set')
    p.add_argument('--out', type=str, default='poc_route.gpx')
    return p.parse_args()


def main():
    args = parse_args()
    params = {
        'prefer_main_roads': args.prefer_main_roads,
        'prefer_unpaved': args.prefer_unpaved,
        'heatmap_influence': args.heatmap_influence,
        'prefer_streetview': args.prefer_streetview,
    }

    coords, gpx = compute_route(tuple(args.start), tuple(args.end), params, bbox_buffer=args.bbox_buffer, radius_meters=args.radius)
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(gpx)
    print(f'Wrote {args.out}, points={len(coords)}')


if __name__ == '__main__':
    main()
