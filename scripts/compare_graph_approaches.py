#!/usr/bin/env python3
"""
Compare the two graph approaches available in Jadlo.

This script demonstrates the difference between:
1. Full graph approach (compute_route) - detailed but memory-intensive
2. Intersection-based approach (compute_route_intersections) - efficient for long routes

Usage:
    PYTHONPATH=. python scripts/compare_graph_approaches.py
    PYTHONPATH=. python scripts/compare_graph_approaches.py --route short
    PYTHONPATH=. python scripts/compare_graph_approaches.py --route medium
    PYTHONPATH=. python scripts/compare_graph_approaches.py --route long
"""
import argparse
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.routing import compute_route, compute_route_intersections


# Predefined test routes
ROUTES = {
    'short': {
        'name': 'Short city route (~5km)',
        'start': (52.2297, 21.0122),  # Warsaw center
        'end': (52.2597, 21.0422),     # ~5km away
        'radius': 3000,
    },
    'medium': {
        'name': 'Medium route (~30km)',
        'start': (52.2297, 21.0122),  # Warsaw
        'end': (52.4297, 21.2122),     # ~30km away
        'radius': 5000,
    },
    'long': {
        'name': 'Long inter-city route (~100km)',
        'start': (52.2297, 21.0122),  # Warsaw
        'end': (53.1325, 23.1688),     # ~100km away
        'radius': 8000,
    },
}


def format_time(seconds):
    """Format time in a human-readable way."""
    if seconds < 60:
        return f"{seconds:.2f}s"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.1f}s"


def calculate_route_distance(coords):
    """Calculate approximate route distance in km using haversine."""
    from math import radians, sin, cos, sqrt, atan2
    
    total_distance = 0
    for i in range(len(coords) - 1):
        lat1, lon1 = coords[i]
        lat2, lon2 = coords[i + 1]
        
        R = 6371  # Earth radius in km
        phi1, phi2 = radians(lat1), radians(lat2)
        dphi = radians(lat2 - lat1)
        dlambda = radians(lon2 - lon1)
        
        a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        total_distance += R * c
    
    return total_distance


def compare_approaches(route_name='short'):
    """Compare both routing approaches on a given route."""
    
    if route_name not in ROUTES:
        print(f"Error: Unknown route '{route_name}'")
        print(f"Available routes: {', '.join(ROUTES.keys())}")
        return
    
    route_config = ROUTES[route_name]
    start = route_config['start']
    end = route_config['end']
    radius = route_config['radius']
    
    print(f"\n{'='*70}")
    print(f"Comparing Graph Approaches: {route_config['name']}")
    print(f"{'='*70}\n")
    print(f"Start:  {start}")
    print(f"End:    {end}")
    print(f"Radius: {radius}m\n")
    
    # Default routing parameters
    params = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.2,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 1.5,
    }
    
    print(f"Routing parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    print()
    
    # Test 1: Full graph approach
    print(f"{'─'*70}")
    print("Approach 1: FULL GRAPH (compute_route)")
    print(f"{'─'*70}")
    try:
        t0 = time.time()
        coords1, gpx1 = compute_route(start, end, params, radius_meters=radius)
        time1 = time.time() - t0
        distance1 = calculate_route_distance(coords1)
        
        print(f"✓ Success!")
        print(f"  Time:      {format_time(time1)}")
        print(f"  Points:    {len(coords1):,}")
        print(f"  Distance:  {distance1:.2f} km")
        print(f"  GPX size:  {len(gpx1):,} bytes")
        
        # Save GPX
        output_file1 = f"test_route_{route_name}_full.gpx"
        with open(output_file1, 'w', encoding='utf-8') as f:
            f.write(gpx1)
        print(f"  Saved:     {output_file1}")
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        time1 = None
        coords1 = None
    
    print()
    
    # Test 2: Intersection-based approach
    print(f"{'─'*70}")
    print("Approach 2: INTERSECTION-BASED (compute_route_intersections)")
    print(f"{'─'*70}")
    try:
        t0 = time.time()
        coords2, gpx2 = compute_route_intersections(start, end, params, radius_meters=radius)
        time2 = time.time() - t0
        distance2 = calculate_route_distance(coords2)
        
        print(f"✓ Success!")
        print(f"  Time:      {format_time(time2)}")
        print(f"  Points:    {len(coords2):,}")
        print(f"  Distance:  {distance2:.2f} km")
        print(f"  GPX size:  {len(gpx2):,} bytes")
        
        # Save GPX
        output_file2 = f"test_route_{route_name}_intersection.gpx"
        with open(output_file2, 'w', encoding='utf-8') as f:
            f.write(gpx2)
        print(f"  Saved:     {output_file2}")
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        time2 = None
        coords2 = None
    
    print()
    
    # Comparison summary
    if time1 and time2:
        print(f"{'─'*70}")
        print("COMPARISON SUMMARY")
        print(f"{'─'*70}")
        
        speedup = time1 / time2
        if speedup > 1:
            print(f"⚡ Intersection approach was {speedup:.1f}x faster")
        else:
            print(f"⚡ Full graph approach was {(1/speedup):.1f}x faster")
        
        point_ratio = len(coords1) / len(coords2)
        print(f"📍 Full graph has {point_ratio:.1f}x more detail points")
        
        if distance1 and distance2:
            dist_diff = abs(distance1 - distance2)
            dist_diff_pct = (dist_diff / distance1) * 100
            print(f"📏 Route distance differs by {dist_diff:.2f} km ({dist_diff_pct:.1f}%)")
        
        print(f"\nRecommendation for {route_config['name']}:")
        if route_name == 'short':
            print("  → Use FULL GRAPH for better accuracy and detail")
        elif route_name == 'medium':
            print("  → Either approach works; use INTERSECTION if memory-constrained")
        else:
            print("  → Use INTERSECTION APPROACH for better performance and memory efficiency")
    
    print(f"\n{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Compare the two graph routing approaches in Jadlo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  PYTHONPATH=. python scripts/compare_graph_approaches.py
  PYTHONPATH=. python scripts/compare_graph_approaches.py --route short
  PYTHONPATH=. python scripts/compare_graph_approaches.py --route medium
  PYTHONPATH=. python scripts/compare_graph_approaches.py --route long

Available routes:
  short   : ~5km city route (fast, good for testing)
  medium  : ~30km route (moderate length)
  long    : ~100km inter-city route (slow, tests scalability)
        """
    )
    
    parser.add_argument(
        '--route',
        choices=['short', 'medium', 'long'],
        default='short',
        help='Which test route to use (default: short)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("  Jadlo Graph Approaches Comparison Tool")
    print("="*70)
    print("\nThis script compares two routing approaches:")
    print("  1. Full Graph - All road details (memory intensive)")
    print("  2. Intersection-Based - Simplified graph (memory efficient)")
    print("\nNote: First run may be slower due to OSM data download and caching.")
    
    compare_approaches(args.route)
    
    print("For more information, see:")
    print("  - docs/GRAPH_APPROACHES_QUICK_GUIDE.md")
    print("  - docs/BRANCHING_STRATEGY.md")
    print()


if __name__ == '__main__':
    main()
