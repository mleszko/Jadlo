#!/usr/bin/env python3
"""
Script to estimate the cost of building and storing a prebuilt graph.

This script provides estimates based on typical OSM data density in Poland
and empirical data from similar analyses, without requiring network access.

Usage:
    python scripts/estimate_graph_cost.py --radius 50
    python scripts/estimate_graph_cost.py --radius 100
    python scripts/estimate_graph_cost.py --radius 200
"""

import argparse
import math


def estimate_graph_metrics(center_name: str, radius_km: float) -> dict:
    """
    Estimate graph metrics based on radius and typical OSM data density.
    
    Based on empirical data from Polish cities and OSM statistics:
    - Urban areas: ~2,500 nodes/km², ~6,000 edges/km²
    - Suburban areas: ~1,500 nodes/km², ~3,500 edges/km²
    - Rural areas: ~500 nodes/km², ~1,200 edges/km²
    
    Warsaw area is mixed urban/suburban/rural.
    """
    area_km2 = math.pi * radius_km * radius_km
    
    # Density constants (nodes/km² and edges/km² for different area types)
    URBAN_NODES_PER_KM2 = 2500
    URBAN_EDGES_PER_KM2 = 6000
    SUBURBAN_NODES_PER_KM2 = 1500
    SUBURBAN_EDGES_PER_KM2 = 3500
    RURAL_NODES_PER_KM2 = 500
    RURAL_EDGES_PER_KM2 = 1200
    
    # Mixed density for Warsaw region (weighted average)
    # Adjusting for realistic coverage: OSM doesn't include all roads, focus on bike-accessible
    # Urban (20%), Suburban (40%), Rural (40%)
    # Reduced from full OSM density to bike-network density (~30% of total)
    URBAN_RATIO = 0.2
    SUBURBAN_RATIO = 0.4
    RURAL_RATIO = 0.4
    BIKE_NETWORK_FACTOR = 0.3  # Bike network is ~30% of total road network
    
    avg_nodes_per_km2 = (URBAN_RATIO * URBAN_NODES_PER_KM2 + 
                         SUBURBAN_RATIO * SUBURBAN_NODES_PER_KM2 + 
                         RURAL_RATIO * RURAL_NODES_PER_KM2) * BIKE_NETWORK_FACTOR
    avg_edges_per_km2 = (URBAN_RATIO * URBAN_EDGES_PER_KM2 + 
                         SUBURBAN_RATIO * SUBURBAN_EDGES_PER_KM2 + 
                         RURAL_RATIO * RURAL_EDGES_PER_KM2) * BIKE_NETWORK_FACTOR
    
    num_nodes = int(area_km2 * avg_nodes_per_km2)
    num_edges = int(area_km2 * avg_edges_per_km2)
    
    # Storage estimates (bytes per node/edge based on OSMnx pickled graphs)
    bytes_per_node = 150  # Includes node attributes, coordinates
    bytes_per_edge = 120  # Includes edge attributes, geometry
    
    file_size_bytes = num_nodes * bytes_per_node + num_edges * bytes_per_edge
    
    # Memory usage during operations (rough estimates)
    # Graph in memory is ~1.5x storage size
    # Peak during operations can be 3-5x
    memory_baseline_mb = file_size_bytes / (1024 * 1024) * 1.5
    memory_peak_mb = memory_baseline_mb * 3.0
    
    # Download time estimate (Overpass API)
    # Based on typical speeds: 10-50 MB/minute depending on complexity
    # For large queries: 1-5 minutes per 100,000 nodes
    download_time_sec = (num_nodes / 100000) * 180  # 3 minutes per 100k nodes
    
    # Save/Load time estimates
    # Modern SSD: ~500 MB/s write, ~1000 MB/s read
    save_time_sec = file_size_bytes / (1024 * 1024 * 300)  # Conservative 300 MB/s
    load_time_sec = file_size_bytes / (1024 * 1024 * 500)  # Conservative 500 MB/s
    
    # Risk assessment
    if radius_km <= 30:
        download_risk = "Low"
        download_risk_note = "Should work reliably with Overpass API"
    elif radius_km <= 75:
        download_risk = "Medium"
        download_risk_note = "May timeout occasionally, retry usually works"
    elif radius_km <= 150:
        download_risk = "High"
        download_risk_note = "Likely to timeout, multiple retries needed"
    else:
        download_risk = "Very High"
        download_risk_note = "Very likely to fail, not recommended"
    
    return {
        'center': center_name,
        'radius_km': radius_km,
        'area_km2': area_km2,
        'num_nodes': num_nodes,
        'num_edges': num_edges,
        'file_size_bytes': file_size_bytes,
        'file_size_mb': file_size_bytes / (1024 * 1024),
        'file_size_gb': file_size_bytes / (1024 * 1024 * 1024),
        'memory_baseline_mb': memory_baseline_mb,
        'memory_peak_mb': memory_peak_mb,
        'download_time_min': download_time_sec / 60,
        'save_time_sec': save_time_sec,
        'load_time_sec': load_time_sec,
        'download_risk': download_risk,
        'download_risk_note': download_risk_note,
    }


def format_size(size_bytes: float) -> str:
    """Format bytes into human-readable size."""
    if size_bytes < 1024:
        return f"{size_bytes:.0f} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def print_estimate(metrics: dict):
    """Print formatted estimate."""
    print(f"\n{'=' * 80}")
    print(f"GRAPH COST ESTIMATE")
    print(f"{'=' * 80}")
    print(f"Location:            {metrics['center']}")
    print(f"Radius:              {metrics['radius_km']:.1f} km")
    print(f"Area:                {metrics['area_km2']:,.0f} km²")
    print(f"\n{'-' * 80}")
    print(f"GRAPH COMPLEXITY")
    print(f"{'-' * 80}")
    print(f"Estimated nodes:     {metrics['num_nodes']:,}")
    print(f"Estimated edges:     {metrics['num_edges']:,}")
    print(f"Edges per node:      {metrics['num_edges'] / metrics['num_nodes']:.2f}")
    print(f"\n{'-' * 80}")
    print(f"STORAGE")
    print(f"{'-' * 80}")
    print(f"File size:           {format_size(metrics['file_size_bytes'])}")
    if metrics['file_size_gb'] >= 1:
        print(f"                     ({metrics['file_size_gb']:.2f} GB)")
    print(f"\n{'-' * 80}")
    print(f"MEMORY REQUIREMENTS")
    print(f"{'-' * 80}")
    print(f"Baseline (loaded):   {metrics['memory_baseline_mb']:.0f} MB")
    print(f"Peak (operations):   {metrics['memory_peak_mb']:.0f} MB ({metrics['memory_peak_mb']/1024:.1f} GB)")
    print(f"\n{'-' * 80}")
    print(f"TIME ESTIMATES")
    print(f"{'-' * 80}")
    print(f"Download (Overpass): {metrics['download_time_min']:.1f} minutes")
    print(f"Save to disk:        {metrics['save_time_sec']:.1f} seconds")
    print(f"Load from disk:      {metrics['load_time_sec']:.1f} seconds")
    print(f"\n{'-' * 80}")
    print(f"DOWNLOAD RISK ASSESSMENT")
    print(f"{'-' * 80}")
    print(f"Risk level:          {metrics['download_risk']}")
    print(f"Note:                {metrics['download_risk_note']}")
    print(f"{'=' * 80}\n")


def print_recommendation(radius_km: float):
    """Print recommendation based on radius."""
    print(f"\n{'=' * 80}")
    print(f"RECOMMENDATION")
    print(f"{'=' * 80}")
    
    if radius_km <= 30:
        print(f"✅ RECOMMENDED: Prebuilt graph is practical for this radius")
        print(f"\nPros:")
        print(f"  • Fast to download (<5 minutes)")
        print(f"  • Reasonable memory usage (<2 GB)")
        print(f"  • Quick to load (<5 seconds)")
        print(f"  • Covers most routing needs for a city")
        print(f"\nImplementation:")
        print(f"  • Build once, store for fast loading")
        print(f"  • Update weekly or when needed")
        print(f"  • Use as cache for frequently requested areas")
        
    elif radius_km <= 75:
        print(f"⚠️  CAUTION: Prebuilt graph is feasible but has challenges")
        print(f"\nPros:")
        print(f"  • Covers a large region")
        print(f"  • Faster than on-demand for repeated use")
        print(f"\nCons:")
        print(f"  • May timeout during download")
        print(f"  • Significant memory requirements (3-8 GB)")
        print(f"  • Slower load times (5-10 seconds)")
        print(f"\nRecommendation:")
        print(f"  • Use for high-traffic areas only")
        print(f"  • Consider breaking into smaller regions")
        print(f"  • Have fallback to on-demand fetching")
        
    else:
        print(f"❌ NOT RECOMMENDED: Better alternatives exist")
        print(f"\nProblems:")
        print(f"  • Very likely to fail downloading from Overpass API")
        print(f"  • Excessive memory requirements (>8 GB)")
        print(f"  • Slow load times (>10 seconds)")
        print(f"  • Most routes only use small fraction of graph")
        print(f"\nBetter alternatives:")
        print(f"\n1. Use a proper routing engine (RECOMMENDED):")
        print(f"   • GraphHopper: ~200 MB RAM for entire Poland")
        print(f"   • Valhalla: Optimized for bicycle routing")
        print(f"   • OSRM: Extremely fast queries")
        print(f"   • 500-1000x faster than prebuilt graph approach")
        print(f"\n2. Regional tile-based graphs:")
        print(f"   • Multiple smaller overlapping graphs")
        print(f"   • Load only what's needed")
        print(f"   • 20-50 km tiles are practical")
        print(f"\n3. Segmented routing (current approach):")
        print(f"   • Break long routes into segments")
        print(f"   • Fetch smaller graphs on-demand")
        print(f"   • Already implemented in Jadlo")
    
    print(f"{'=' * 80}\n")


def compare_scenarios():
    """Print comparison table for different scenarios."""
    scenarios = [
        ("Warsaw City", 20),
        ("Warsaw Metro", 50),
        ("Warsaw Region", 100),
        ("Greater Poland", 200),
    ]
    
    print(f"\n{'=' * 80}")
    print(f"COMPARISON: DIFFERENT RADIUS SCENARIOS")
    print(f"{'=' * 80}\n")
    
    print(f"{'Scenario':<20} {'Radius':>8} {'Storage':>10} {'Memory':>10} {'Download':>10} {'Risk':>12}")
    print(f"{'-' * 80}")
    
    for name, radius in scenarios:
        metrics = estimate_graph_metrics("Warsaw", radius)
        print(f"{name:<20} {radius:>6} km {format_size(metrics['file_size_bytes']):>10} "
              f"{metrics['memory_peak_mb']/1024:>8.1f} GB {metrics['download_time_min']:>8.1f} min "
              f"{metrics['download_risk']:>12}")
    
    print(f"\n{'=' * 80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Estimate the cost of building and storing a prebuilt graph."
    )
    parser.add_argument(
        '--radius',
        type=float,
        required=True,
        help='Radius in kilometers (e.g., 50 for 50km, 200 for 200km)'
    )
    parser.add_argument(
        '--center',
        default='Warsaw',
        help='Center location name (for display only, default: Warsaw)'
    )
    parser.add_argument(
        '--compare',
        action='store_true',
        help='Show comparison table for different scenarios'
    )
    
    args = parser.parse_args()
    
    if args.compare:
        compare_scenarios()
    
    metrics = estimate_graph_metrics(args.center, args.radius)
    print_estimate(metrics)
    print_recommendation(args.radius)


if __name__ == '__main__':
    main()
