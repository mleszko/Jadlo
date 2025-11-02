#!/usr/bin/env python3
"""
Script to analyze the cost of building and storing a prebuilt graph for a large area.

This script measures:
- Download time from Overpass API
- Memory usage during graph building
- Storage size on disk
- Graph statistics (nodes, edges)

Usage:
    PYTHONPATH=. python scripts/analyze_graph_cost.py --center 52.2297 21.0122 --radius 50000
    PYTHONPATH=. python scripts/analyze_graph_cost.py --center 52.2297 21.0122 --radius 100000
    PYTHONPATH=. python scripts/analyze_graph_cost.py --center 52.2297 21.0122 --radius 200000
"""

import argparse
import time
import sys
import os
import pickle
import psutil
from typing import Tuple

import osmnx as ox
import networkx as nx

# Enable caching for OSMnx
ox.config(use_cache=True, log_console=True)


def get_memory_usage_mb() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def format_size(bytes_size: int) -> str:
    """Format bytes into human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def analyze_graph_cost(center: Tuple[float, float], radius_meters: int, output_dir: str = "artifacts") -> dict:
    """
    Analyze the cost of building and storing a graph for a given area.
    
    Args:
        center: (lat, lon) tuple for the center point
        radius_meters: Radius in meters
        output_dir: Directory to save the graph
        
    Returns:
        dict: Statistics about the graph building process
    """
    lat, lon = center
    print(f"\n{'=' * 80}")
    print(f"Analyzing graph cost for area:")
    print(f"  Center: {lat}, {lon}")
    print(f"  Radius: {radius_meters / 1000:.1f} km")
    print(f"{'=' * 80}\n")
    
    # Measure memory before
    mem_before = get_memory_usage_mb()
    print(f"Memory usage before: {mem_before:.2f} MB")
    
    # Download and build graph
    print(f"\nDownloading graph from Overpass API...")
    start_time = time.time()
    
    try:
        G = ox.graph_from_point(center, dist=radius_meters, network_type='bike')
    except Exception as e:
        print(f"\n❌ ERROR: Failed to download graph: {e}")
        print(f"This may be due to Overpass API limits or timeout.")
        print(f"Try a smaller radius or wait before retrying.")
        return None
    
    download_time = time.time() - start_time
    
    # Measure memory after
    mem_after = get_memory_usage_mb()
    mem_used = mem_after - mem_before
    
    print(f"✓ Download completed in {download_time:.1f} seconds")
    print(f"Memory usage after: {mem_after:.2f} MB (increase: {mem_used:.2f} MB)")
    
    # Graph statistics
    num_nodes = len(G.nodes)
    num_edges = len(G.edges)
    
    print(f"\nGraph statistics:")
    print(f"  Nodes: {num_nodes:,}")
    print(f"  Edges: {num_edges:,}")
    print(f"  Edges per node: {num_edges / num_nodes:.2f}")
    
    # Save graph to disk
    os.makedirs(output_dir, exist_ok=True)
    # Use a generic name based on center coordinates
    location_id = f"{lat:.2f}_{lon:.2f}".replace('.', '_').replace('-', 'n')
    graph_filename = f"graph_{location_id}_r{radius_meters // 1000}km.pkl"
    graph_path = os.path.join(output_dir, graph_filename)
    
    print(f"\nSaving graph to disk: {graph_path}")
    save_start = time.time()
    
    with open(graph_path, 'wb') as f:
        pickle.dump(G, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    save_time = time.time() - save_start
    file_size = os.path.getsize(graph_path)
    
    print(f"✓ Graph saved in {save_time:.1f} seconds")
    print(f"File size: {format_size(file_size)}")
    
    # Test loading the graph
    print(f"\nTesting graph loading...")
    load_start = time.time()
    
    with open(graph_path, 'rb') as f:
        G_loaded = pickle.load(f)
    
    load_time = time.time() - load_start
    print(f"✓ Graph loaded in {load_time:.1f} seconds")
    
    # Calculate efficiency metrics
    size_per_node = file_size / num_nodes
    size_per_edge = file_size / num_edges
    
    # Summary
    stats = {
        'radius_km': radius_meters / 1000,
        'download_time_sec': download_time,
        'memory_used_mb': mem_used,
        'num_nodes': num_nodes,
        'num_edges': num_edges,
        'file_size_bytes': file_size,
        'file_size_human': format_size(file_size),
        'save_time_sec': save_time,
        'load_time_sec': load_time,
        'size_per_node_bytes': size_per_node,
        'size_per_edge_bytes': size_per_edge,
    }
    
    print(f"\n{'=' * 80}")
    print(f"SUMMARY")
    print(f"{'=' * 80}")
    print(f"Radius:              {stats['radius_km']:.1f} km")
    print(f"Download time:       {stats['download_time_sec']:.1f} seconds")
    print(f"Memory increase:     {stats['memory_used_mb']:.2f} MB")
    print(f"Graph nodes:         {stats['num_nodes']:,}")
    print(f"Graph edges:         {stats['num_edges']:,}")
    print(f"File size:           {stats['file_size_human']}")
    print(f"Save time:           {stats['save_time_sec']:.1f} seconds")
    print(f"Load time:           {stats['load_time_sec']:.1f} seconds")
    print(f"Size per node:       {stats['size_per_node_bytes']:.1f} bytes")
    print(f"Size per edge:       {stats['size_per_edge_bytes']:.1f} bytes")
    print(f"{'=' * 80}\n")
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Analyze the cost of building and storing a prebuilt graph for a large area."
    )
    parser.add_argument(
        '--center',
        nargs=2,
        type=float,
        default=[52.2297, 21.0122],
        help='Center point as lat lon (default: Warsaw 52.2297 21.0122)'
    )
    parser.add_argument(
        '--radius',
        type=int,
        required=True,
        help='Radius in meters (e.g., 50000 for 50km, 200000 for 200km)'
    )
    parser.add_argument(
        '--output-dir',
        default='artifacts',
        help='Directory to save the graph (default: artifacts)'
    )
    
    args = parser.parse_args()
    center = tuple(args.center)
    
    # Validate radius
    if args.radius > 300000:
        print(f"⚠️  WARNING: Radius {args.radius / 1000}km is very large!")
        print(f"This may take a long time and could hit Overpass API limits.")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
    
    try:
        stats = analyze_graph_cost(center, args.radius, args.output_dir)
        
        if stats is None:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
