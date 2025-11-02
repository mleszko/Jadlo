#!/usr/bin/env python3
"""
Script to build and save a prebuilt graph for a specific region.

This is useful for frequently used areas to avoid repeated downloads from Overpass API.
Recommended for regions with 20-50km radius.

Usage:
    # Build Warsaw city graph (20km radius)
    PYTHONPATH=. python scripts/build_prebuilt_graph.py \
        --name warsaw_city \
        --center 52.2297 21.0122 \
        --radius 20000

    # Build Krakow city graph (25km radius)
    PYTHONPATH=. python scripts/build_prebuilt_graph.py \
        --name krakow_city \
        --center 50.0647 19.9450 \
        --radius 25000
"""

import argparse
import os
import pickle
import time
import json
from typing import Tuple

import osmnx as ox

# Enable caching
ox.config(use_cache=True, log_console=True)


def build_and_save_graph(
    name: str,
    center: Tuple[float, float],
    radius_meters: int,
    output_dir: str = "prebuilt_graphs"
) -> dict:
    """
    Build and save a graph for a region.
    
    Args:
        name: Name identifier for this graph (e.g., 'warsaw_city')
        center: (lat, lon) tuple
        radius_meters: Radius in meters
        output_dir: Directory to save graphs
        
    Returns:
        dict: Metadata about the saved graph
    """
    lat, lon = center
    print(f"\n{'=' * 80}")
    print(f"Building prebuilt graph: {name}")
    print(f"{'=' * 80}")
    print(f"Center:  {lat}, {lon}")
    print(f"Radius:  {radius_meters / 1000:.1f} km")
    print(f"{'=' * 80}\n")
    
    # Download graph
    print("Downloading graph from Overpass API...")
    start_time = time.time()
    
    try:
        G = ox.graph_from_point(center, dist=radius_meters, network_type='bike')
    except Exception as e:
        print(f"\n❌ ERROR: Failed to download graph: {e}")
        raise
    
    download_time = time.time() - start_time
    print(f"✓ Downloaded in {download_time:.1f} seconds")
    
    # Graph statistics
    num_nodes = len(G.nodes)
    num_edges = len(G.edges)
    print(f"\nGraph statistics:")
    print(f"  Nodes: {num_nodes:,}")
    print(f"  Edges: {num_edges:,}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Save graph
    graph_filename = f"{name}.pkl"
    graph_path = os.path.join(output_dir, graph_filename)
    
    print(f"\nSaving graph to: {graph_path}")
    save_start = time.time()
    
    with open(graph_path, 'wb') as f:
        pickle.dump(G, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    save_time = time.time() - save_start
    file_size = os.path.getsize(graph_path)
    
    print(f"✓ Saved in {save_time:.1f} seconds")
    print(f"File size: {file_size / (1024 * 1024):.1f} MB")
    
    # Create metadata
    metadata = {
        'name': name,
        'center': {'lat': lat, 'lon': lon},
        'radius_meters': radius_meters,
        'radius_km': radius_meters / 1000,
        'num_nodes': num_nodes,
        'num_edges': num_edges,
        'file_size_bytes': file_size,
        'download_time_sec': download_time,
        'save_time_sec': save_time,
        'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    # Save metadata
    metadata_path = os.path.join(output_dir, f"{name}_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✓ Metadata saved to: {metadata_path}")
    
    # Update registry
    registry_path = os.path.join(output_dir, "registry.json")
    registry = {}
    
    if os.path.exists(registry_path):
        with open(registry_path, 'r') as f:
            registry = json.load(f)
    
    registry[name] = {
        'graph_file': graph_filename,
        'metadata_file': f"{name}_metadata.json",
        'center': metadata['center'],
        'radius_km': metadata['radius_km'],
        'created_at': metadata['created_at'],
    }
    
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"✓ Registry updated: {registry_path}")
    
    print(f"\n{'=' * 80}")
    print(f"SUCCESS: Graph built and saved")
    print(f"{'=' * 80}\n")
    
    return metadata


def main():
    parser = argparse.ArgumentParser(
        description="Build and save a prebuilt graph for a specific region."
    )
    parser.add_argument(
        '--name',
        required=True,
        help='Name identifier for this graph (e.g., warsaw_city)'
    )
    parser.add_argument(
        '--center',
        nargs=2,
        type=float,
        required=True,
        help='Center point as lat lon'
    )
    parser.add_argument(
        '--radius',
        type=int,
        required=True,
        help='Radius in meters (recommended: 20000-50000)'
    )
    parser.add_argument(
        '--output-dir',
        default='prebuilt_graphs',
        help='Directory to save graphs (default: prebuilt_graphs)'
    )
    
    args = parser.parse_args()
    center = tuple(args.center)
    
    # Validate radius
    if args.radius > 100000:
        print(f"⚠️  WARNING: Radius {args.radius / 1000}km is very large!")
        print(f"Recommended: 20-50 km for prebuilt graphs.")
        print(f"For larger areas, consider using a proper routing engine instead.")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
    
    try:
        build_and_save_graph(args.name, center, args.radius, args.output_dir)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
