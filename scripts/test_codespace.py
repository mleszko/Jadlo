#!/usr/bin/env python3
"""Simple script to test route generation in Codespaces with one command.

This script generates a small test route that is fast and suitable for testing
in resource-constrained environments like GitHub Codespaces.

Usage:
  python scripts/test_codespace.py

Or with PYTHONPATH:
  PYTHONPATH=. python scripts/test_codespace.py

The script will:
1. Generate a short ~10km route in Poland (Warsaw area)
2. Save the result as 'test_route_codespace.gpx'
3. Print success message with route details
"""
import sys
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.routing import compute_route


def main():
    print("=" * 60)
    print("Testing Route Generation in Codespace")
    print("=" * 60)
    print()
    
    # Short test route in Warsaw area (~10km)
    start = (52.2297, 21.0122)  # Warsaw center
    end = (52.3000, 21.0500)     # North Warsaw
    
    # Default parameters
    params = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.2,
        'heatmap_influence': 0.0,
        'prefer_streetview': 0.0,
    }
    
    output_file = 'test_route_codespace.gpx'
    
    print(f"Start point: {start}")
    print(f"End point: {end}")
    print(f"Parameters: {params}")
    print()
    print("Generating route... (this may take 30-60 seconds)")
    print()
    
    try:
        # Use a small radius for faster generation in Codespaces
        coords, gpx = compute_route(start, end, params, radius_meters=5000)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(gpx)
        
        print("✓ Success!")
        print(f"✓ Generated route with {len(coords)} points")
        print(f"✓ Saved to: {output_file}")
        print()
        print("=" * 60)
        print("Test completed successfully! 🎉")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print()
        print("If you see an error about missing system libraries (GEOS/PROJ/GDAL),")
        print("make sure you're running in a Codespace or environment with osmnx dependencies.")
        sys.exit(1)


if __name__ == '__main__':
    main()
