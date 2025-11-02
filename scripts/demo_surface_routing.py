#!/usr/bin/env python
"""
Demo script showing surface-based routing with different surface_weight_factor values.

This script demonstrates how the surface_weight_factor parameter influences route selection:
- Low factor (0.5): Prioritizes shorter distance over surface quality
- Medium factor (1.0): Balanced between distance and surface (default)
- High factor (2.0): Strongly prefers better surfaces even if longer

Run this script to see how Dijkstra's algorithm finds different optimal routes
based on the surface_weight_factor parameter.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.routing import calculate_edge_weight


def demo_surface_weight_impact():
    """Demonstrate how surface_weight_factor affects route selection."""
    
    print("=" * 80)
    print("SURFACE-BASED ROUTING DEMO")
    print("Dijkstra's Algorithm with Surface Type Weighting")
    print("=" * 80)
    print()
    
    # Example scenario: Two route options
    # Route A: 1000m on asphalt (good surface)
    # Route B: 800m on dirt road (poor surface, but shorter)
    
    route_a = {'length': 1000.0, 'highway': 'residential', 'surface': 'asphalt'}
    route_b = {'length': 800.0, 'highway': 'residential', 'surface': 'dirt'}
    
    print("SCENARIO: Choosing between two routes")
    print("-" * 80)
    print("Route A: 1000m on asphalt (good surface)")
    print("Route B:  800m on dirt road (poor surface, 20% shorter)")
    print()
    
    # Test different surface_weight_factor values
    factors = [
        (0.5, "Low - prioritize distance"),
        (1.0, "Medium - balanced (default)"),
        (2.0, "High - prioritize surface quality"),
    ]
    
    print("RESULTS: Which route does Dijkstra's algorithm choose?")
    print("-" * 80)
    
    for factor, description in factors:
        params = {
            'prefer_main_roads': 0.5,
            'prefer_unpaved': 0.5,
            'heatmap_influence': 0.0,
            'surface_weight_factor': factor
        }
        
        weight_a = calculate_edge_weight(1000.0, 'residential', 'asphalt', params)
        weight_b = calculate_edge_weight(800.0, 'residential', 'dirt', params)
        
        print(f"\nFactor = {factor} ({description})")
        print(f"  Route A weight: {weight_a:.2f}")
        print(f"  Route B weight: {weight_b:.2f}")
        
        if weight_a < weight_b:
            choice = "Route A (asphalt, longer)"
            saving = ((weight_b - weight_a) / weight_b) * 100
        else:
            choice = "Route B (dirt, shorter)"
            saving = ((weight_a - weight_b) / weight_a) * 100
        
        print(f"  → Algorithm chooses: {choice} ({saving:.1f}% better)")
    
    print()
    print("=" * 80)
    print("CONCLUSION:")
    print("-" * 80)
    print("• Low factor (0.5): Favors shorter distance - chooses dirt road")
    print("• Medium factor (1.0): Balanced - depends on the specific scenario")
    print("• High factor (2.0): Favors good surface - chooses paved route")
    print()
    print("The algorithm (Dijkstra/A*) finds the optimal route based on")
    print("your surface_weight_factor preference!")
    print("=" * 80)


def demo_surface_comparison():
    """Compare weights for different surface types."""
    
    print()
    print("=" * 80)
    print("SURFACE TYPE COMPARISON")
    print("=" * 80)
    print()
    
    surfaces = [
        ('asphalt', 'Smooth paved road'),
        ('concrete', 'Paved concrete road'),
        ('gravel', 'Gravel road'),
        ('unpaved', 'Unpaved road'),
        ('dirt', 'Dirt track'),
    ]
    
    params = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 1.5  # emphasize surface
    }
    
    print(f"Surface comparison (100m segments, factor={params['surface_weight_factor']}):")
    print("-" * 80)
    
    weights = []
    for surface, description in surfaces:
        weight = calculate_edge_weight(100.0, 'residential', surface, params)
        weights.append((surface, description, weight))
    
    # Sort by weight (best to worst)
    weights.sort(key=lambda x: x[2])
    
    for i, (surface, description, weight) in enumerate(weights, 1):
        print(f"{i}. {surface:12s} {description:25s} weight: {weight:7.2f}")
    
    print()
    print("Lower weight = preferred by the routing algorithm")
    print("=" * 80)


if __name__ == '__main__':
    demo_surface_weight_impact()
    demo_surface_comparison()
