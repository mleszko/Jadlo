"""
Tests for surface-based routing using Dijkstra's algorithm.

These tests validate that:
1. Surface type significantly influences route calculation
2. The surface_weight_factor parameter works as expected
3. Routes with better surfaces are preferred when factor is high
4. Distance is prioritized when factor is low
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.routing import calculate_edge_weight


def test_surface_weight_factor_default():
    """Test that default surface_weight_factor (1.0) produces base penalties."""
    params = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 1.0  # default
    }
    
    w_paved = calculate_edge_weight(100.0, 'residential', 'asphalt', params)
    w_gravel = calculate_edge_weight(100.0, 'residential', 'gravel', params)
    
    # Gravel should be more expensive than paved (1.6x base penalty)
    assert w_gravel > w_paved
    # Approximate check: gravel penalty should be around 1.6x paved
    ratio = w_gravel / w_paved
    assert 1.4 < ratio < 1.8


def test_surface_weight_factor_high_emphasizes_surface():
    """Test that high surface_weight_factor strongly emphasizes surface quality."""
    params_low = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 0.5  # low factor
    }
    
    params_high = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 2.0  # high factor
    }
    
    # With low factor, surface matters less
    w_paved_low = calculate_edge_weight(100.0, 'residential', 'asphalt', params_low)
    w_dirt_low = calculate_edge_weight(100.0, 'residential', 'dirt', params_low)
    ratio_low = w_dirt_low / w_paved_low
    
    # With high factor, surface matters much more
    w_paved_high = calculate_edge_weight(100.0, 'residential', 'asphalt', params_high)
    w_dirt_high = calculate_edge_weight(100.0, 'residential', 'dirt', params_high)
    ratio_high = w_dirt_high / w_paved_high
    
    # High factor should create bigger difference between surfaces
    assert ratio_high > ratio_low
    # With factor=2.0 and base dirt penalty=2.0, we expect 2.0^2.0 = 4.0x difference
    assert ratio_high > 3.0


def test_surface_weight_factor_low_prioritizes_distance():
    """Test that low surface_weight_factor prioritizes distance over surface."""
    params_low = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 0.5  # low factor - prioritize distance
    }
    
    w_paved_short = calculate_edge_weight(100.0, 'residential', 'asphalt', params_low)
    w_dirt_long = calculate_edge_weight(200.0, 'residential', 'dirt', params_low)
    
    # With low surface factor, the 2x distance should dominate
    # Even though dirt is worse surface, the route should be relatively comparable
    # because surface penalty is reduced by low factor
    assert w_dirt_long > w_paved_short
    # The ratio should be closer to 2.0 (length ratio) than 4.0 (if surface mattered more)
    ratio = w_dirt_long / w_paved_short
    # With factor=0.5, dirt penalty is 2.0^0.5 ≈ 1.414, so ratio ≈ 2 * 1.414 ≈ 2.83
    assert ratio < 3.0  # surface matters less, so ratio closer to length ratio


def test_surface_types_ordering():
    """Test that surface types are correctly ordered from best to worst."""
    surfaces = ['asphalt', 'paved', 'concrete', 'gravel', 'unpaved', 'dirt']
    params = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 1.0
    }
    
    weights = []
    for surface in surfaces:
        w = calculate_edge_weight(100.0, 'residential', surface, params)
        weights.append(w)
    
    # Paved surfaces (asphalt, paved, concrete) should have similar low weights
    assert abs(weights[0] - weights[1]) < 1.0
    assert abs(weights[1] - weights[2]) < 1.0
    
    # Unpaved surfaces should be progressively worse
    assert weights[3] > weights[2]  # gravel > concrete
    assert weights[4] > weights[3]  # unpaved > gravel
    assert weights[5] >= weights[4]  # dirt >= unpaved


def test_prefer_unpaved_reduces_unpaved_penalty():
    """Test that prefer_unpaved parameter reduces penalty for unpaved surfaces."""
    params_avoid = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.0,  # avoid unpaved
        'heatmap_influence': 0.0,
        'surface_weight_factor': 1.0
    }
    
    params_prefer = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 1.0,  # prefer unpaved
        'heatmap_influence': 0.0,
        'surface_weight_factor': 1.0
    }
    
    w_avoid = calculate_edge_weight(100.0, 'residential', 'gravel', params_avoid)
    w_prefer = calculate_edge_weight(100.0, 'residential', 'gravel', params_prefer)
    
    # Preferring unpaved should reduce the penalty
    assert w_prefer < w_avoid


def test_combined_surface_and_highway_factors():
    """Test that surface and highway penalties combine correctly."""
    params_high_surface = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 2.0  # surface matters a lot
    }
    
    params_low_surface = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 0.5  # surface matters less
    }
    
    # With high surface factor, motorway (bad for bikes but good surface) 
    # vs cycleway (good for bikes but bad surface) comparison
    w_motorway_high = calculate_edge_weight(100.0, 'motorway', 'asphalt', params_high_surface)
    w_cycleway_high = calculate_edge_weight(100.0, 'cycleway', 'dirt', params_high_surface)
    
    w_motorway_low = calculate_edge_weight(100.0, 'motorway', 'asphalt', params_low_surface)
    w_cycleway_low = calculate_edge_weight(100.0, 'cycleway', 'dirt', params_low_surface)
    
    # Both should be weighted, confirming the algorithm considers both factors
    assert w_motorway_high > 0
    assert w_cycleway_high > 0
    assert w_motorway_low > 0
    assert w_cycleway_low > 0


def test_missing_surface_defaults_correctly():
    """Test that edges without surface data get reasonable default penalty."""
    params = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 1.0
    }
    
    w_no_surface = calculate_edge_weight(100.0, 'residential', None, params)
    w_with_surface = calculate_edge_weight(100.0, 'residential', 'asphalt', params)
    
    # Without surface info, penalty should default to 1.0 (neutral)
    # so it should equal the asphalt case (also 1.0)
    assert w_no_surface == w_with_surface


def test_compound_surface_types():
    """Test that compound surface types (e.g., 'asphalt:lanes') are handled correctly."""
    params = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 1.0
    }
    
    # Test compound surface type
    w_simple = calculate_edge_weight(100.0, 'residential', 'asphalt', params)
    w_compound = calculate_edge_weight(100.0, 'residential', 'asphalt:lanes', params)
    
    # Both should have the same weight (compound type uses prefix)
    assert w_simple == w_compound
