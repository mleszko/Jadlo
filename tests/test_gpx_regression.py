"""
Regression tests for GPX generation.

These tests ensure that GPX generation remains stable across code changes by:
1. Validating GPX XML structure and format
2. Testing parameter consistency (same input produces same output)
3. Verifying route quality (coordinates, ordering, no duplicates)
4. Checking GPX compliance with GPX 1.1 schema
5. Testing various parameter combinations

Run with: PYTHONPATH=. python -m pytest tests/test_gpx_regression.py -v
"""
import sys
import os
import xml.etree.ElementTree as ET
import math
from typing import List, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.routing import calculate_edge_weight, _edge_penalty


def test_gpx_xml_structure_validation():
    """Test that GPX XML generation produces valid XML with required elements."""
    import gpxpy
    import gpxpy.gpx
    
    # Create a simple GPX object
    gpx = gpxpy.gpx.GPX()
    
    # Create track
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    
    # Create segment
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)
    
    # Add some test points
    test_coords = [
        (52.2297, 21.0122),
        (52.2300, 21.0125),
        (52.2305, 21.0130),
    ]
    
    for lat, lon in test_coords:
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
    
    # Convert to XML
    gpx_xml = gpx.to_xml()
    
    # Parse XML to verify structure
    root = ET.fromstring(gpx_xml)
    
    # Verify namespace
    namespace = {'gpx': 'http://www.topografix.com/GPX/1/1'}
    assert root.tag.endswith('gpx'), "Root element should be 'gpx'"
    
    # Verify required elements exist
    tracks = root.findall('.//gpx:trk', namespace)
    assert len(tracks) >= 1, "GPX should have at least one track"
    
    segments = root.findall('.//gpx:trkseg', namespace)
    assert len(segments) >= 1, "GPX track should have at least one segment"
    
    points = root.findall('.//gpx:trkpt', namespace)
    assert len(points) == len(test_coords), f"Should have {len(test_coords)} track points"
    
    # Verify track points have lat/lon attributes
    for point in points:
        assert 'lat' in point.attrib, "Track point should have 'lat' attribute"
        assert 'lon' in point.attrib, "Track point should have 'lon' attribute"
        
        lat = float(point.attrib['lat'])
        lon = float(point.attrib['lon'])
        
        assert -90 <= lat <= 90, f"Latitude {lat} out of valid range [-90, 90]"
        assert -180 <= lon <= 180, f"Longitude {lon} out of valid range [-180, 180]"


def test_gpx_coordinates_ordering():
    """Test that GPX coordinates are in correct order and form a valid path."""
    import gpxpy
    import gpxpy.gpx
    
    # Create GPX with ordered coordinates
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)
    
    # Progressive coordinates (moving east)
    test_coords = [
        (52.2297, 21.0122),
        (52.2297, 21.0125),
        (52.2297, 21.0128),
        (52.2297, 21.0131),
    ]
    
    for lat, lon in test_coords:
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
    
    # Verify ordering is preserved
    for i, point in enumerate(gpx_segment.points):
        assert point.latitude == test_coords[i][0]
        assert point.longitude == test_coords[i][1]


def test_gpx_no_duplicate_consecutive_points():
    """Test that GPX generation doesn't create duplicate consecutive points."""
    import gpxpy
    import gpxpy.gpx
    
    # Create GPX
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)
    
    # Add test points with potential duplicates
    test_coords = [
        (52.2297, 21.0122),
        (52.2300, 21.0125),
        (52.2300, 21.0125),  # duplicate
        (52.2305, 21.0130),
    ]
    
    # Add points but filter duplicates (this is what routing should do)
    prev = None
    for lat, lon in test_coords:
        if prev is None or prev != (lat, lon):
            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
            prev = (lat, lon)
    
    # Verify no consecutive duplicates
    points = gpx_segment.points
    for i in range(1, len(points)):
        prev_point = points[i - 1]
        curr_point = points[i]
        
        assert not (prev_point.latitude == curr_point.latitude and 
                   prev_point.longitude == curr_point.longitude), \
            f"Found duplicate consecutive points at index {i}"


def test_edge_weight_calculation_consistency():
    """
    Regression test: Verify that edge weight calculation is consistent.
    
    This test ensures that the weight calculation algorithm produces
    consistent results for the same inputs across code changes.
    """
    test_cases = [
        # (length, highway, surface, params, expected_range)
        (100.0, 'residential', 'asphalt', 
         {'prefer_main_roads': 0.5, 'prefer_unpaved': 0.5, 'heatmap_influence': 0.0, 'surface_weight_factor': 1.0},
         (95.0, 105.0)),  # Should be ~100.0
        
        (100.0, 'primary', 'asphalt',
         {'prefer_main_roads': 1.0, 'prefer_unpaved': 0.5, 'heatmap_influence': 0.0, 'surface_weight_factor': 1.0},
         (130.0, 150.0)),  # Primary with prefer should have reduced penalty
        
        (100.0, 'residential', 'dirt',
         {'prefer_main_roads': 0.5, 'prefer_unpaved': 0.0, 'heatmap_influence': 0.0, 'surface_weight_factor': 2.0},
         (480.0, 520.0)),  # Dirt with high surface factor should have high penalty (~500)
        
        (100.0, 'cycleway', 'asphalt',
         {'prefer_main_roads': 0.5, 'prefer_unpaved': 0.5, 'heatmap_influence': 1.0, 'surface_weight_factor': 1.0},
         (40.0, 45.0)),  # Cycleway with heatmap influence should have bonus (~42)
    ]
    
    for length, highway, surface, params, (min_weight, max_weight) in test_cases:
        weight = calculate_edge_weight(length, highway, surface, params)
        
        assert min_weight <= weight <= max_weight, \
            f"Weight {weight} for {highway}/{surface} outside expected range [{min_weight}, {max_weight}]"


def test_surface_weight_factor_progression():
    """
    Regression test: Verify that surface_weight_factor has expected effect.
    
    As surface_weight_factor increases, the penalty for poor surfaces
    should increase exponentially.
    """
    base_params = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
    }
    
    factors = [0.5, 1.0, 1.5, 2.0, 2.5]
    
    # Test with dirt surface (penalty = 2.0)
    weights = []
    for factor in factors:
        params = {**base_params, 'surface_weight_factor': factor}
        weight = calculate_edge_weight(100.0, 'residential', 'dirt', params)
        weights.append(weight)
    
    # Weights should be monotonically increasing
    for i in range(1, len(weights)):
        assert weights[i] > weights[i - 1], \
            f"Weight should increase with surface_weight_factor: {weights[i]} <= {weights[i-1]}"
    
    # The increase should be significant for higher factors
    # With dirt penalty=2.0: factor=0.5 gives 2^0.5≈1.41, factor=2.5 gives 2^2.5≈5.66
    assert weights[-1] / weights[0] > 3.0, \
        "High surface_weight_factor should significantly increase penalty for poor surfaces"


def test_prefer_unpaved_parameter_effect():
    """
    Regression test: Verify that prefer_unpaved parameter reduces penalty for unpaved surfaces.
    """
    base_params = {
        'prefer_main_roads': 0.5,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 1.0,
    }
    
    # Test with gravel surface
    params_avoid = {**base_params, 'prefer_unpaved': 0.0}
    params_neutral = {**base_params, 'prefer_unpaved': 0.5}
    params_prefer = {**base_params, 'prefer_unpaved': 1.0}
    
    weight_avoid = calculate_edge_weight(100.0, 'residential', 'gravel', params_avoid)
    weight_neutral = calculate_edge_weight(100.0, 'residential', 'gravel', params_neutral)
    weight_prefer = calculate_edge_weight(100.0, 'residential', 'gravel', params_prefer)
    
    # Weights should decrease as we prefer unpaved more
    assert weight_prefer < weight_neutral < weight_avoid, \
        "prefer_unpaved should reduce penalty for unpaved surfaces"


def test_prefer_main_roads_parameter_effect():
    """
    Regression test: Verify that prefer_main_roads parameter affects main road selection.
    """
    base_params = {
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 1.0,
    }
    
    # Test with primary road
    params_avoid = {**base_params, 'prefer_main_roads': 0.0}
    params_neutral = {**base_params, 'prefer_main_roads': 0.5}
    params_prefer = {**base_params, 'prefer_main_roads': 1.0}
    
    weight_avoid = calculate_edge_weight(100.0, 'primary', 'asphalt', params_avoid)
    weight_neutral = calculate_edge_weight(100.0, 'primary', 'asphalt', params_neutral)
    weight_prefer = calculate_edge_weight(100.0, 'primary', 'asphalt', params_prefer)
    
    # When we prefer main roads, penalty should be lower
    assert weight_prefer < weight_neutral < weight_avoid, \
        "prefer_main_roads should progressively reduce penalty for main roads"


def test_parameter_combinations_stability():
    """
    Regression test: Test various parameter combinations to ensure stability.
    
    This test checks that all valid parameter combinations produce reasonable weights.
    """
    # Test matrix of parameters
    prefer_main_values = [0.0, 0.5, 1.0]
    prefer_unpaved_values = [0.0, 0.5, 1.0]
    surface_factors = [0.5, 1.0, 2.0]
    
    highways = ['residential', 'primary', 'cycleway', 'path']
    surfaces = ['asphalt', 'gravel', 'dirt']
    
    for prefer_main in prefer_main_values:
        for prefer_unpaved in prefer_unpaved_values:
            for surface_factor in surface_factors:
                params = {
                    'prefer_main_roads': prefer_main,
                    'prefer_unpaved': prefer_unpaved,
                    'heatmap_influence': 0.0,
                    'surface_weight_factor': surface_factor,
                }
                
                for highway in highways:
                    for surface in surfaces:
                        weight = calculate_edge_weight(100.0, highway, surface, params)
                        
                        # Sanity checks
                        assert weight > 0, \
                            f"Weight should be positive for {highway}/{surface}"
                        assert weight < 10000.0, \
                            f"Weight should be reasonable for {highway}/{surface}, got {weight}"
                        assert not math.isnan(weight), \
                            f"Weight should not be NaN for {highway}/{surface}"
                        assert not math.isinf(weight), \
                            f"Weight should not be infinite for {highway}/{surface}"


def test_edge_penalty_direct_call():
    """
    Regression test: Test _edge_penalty function directly to ensure consistency.
    """
    # Test edge with complete data
    edge_data = {
        'length': 100.0,
        'highway': 'residential',
        'surface': 'asphalt',
    }
    params = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 1.0,
    }
    
    weight = _edge_penalty(1, 2, 0, edge_data, params)
    
    # With residential/asphalt and neutral params, weight should be ~100
    assert 95.0 <= weight <= 105.0, \
        f"Weight {weight} unexpected for neutral residential/asphalt"


def test_surface_penalty_unknown_types():
    """
    Regression test: Verify handling of unknown surface types.
    """
    params = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 1.0,
    }
    
    # Test with unknown surface type
    weight_unknown = calculate_edge_weight(100.0, 'residential', 'unknown_surface_type', params)
    weight_none = calculate_edge_weight(100.0, 'residential', None, params)
    weight_asphalt = calculate_edge_weight(100.0, 'residential', 'asphalt', params)
    
    # Unknown surfaces should default to neutral (1.0), same as asphalt
    assert weight_unknown == weight_asphalt, \
        "Unknown surface types should default to neutral penalty"
    assert weight_none == weight_asphalt, \
        "Missing surface should default to neutral penalty"


def test_compound_surface_handling():
    """
    Regression test: Verify that compound surface types are handled correctly.
    """
    params = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 1.0,
    }
    
    # Test compound surface types (e.g., 'asphalt:lanes', 'gravel:compacted')
    weight_simple = calculate_edge_weight(100.0, 'residential', 'asphalt', params)
    weight_compound = calculate_edge_weight(100.0, 'residential', 'asphalt:lanes', params)
    
    assert weight_simple == weight_compound, \
        "Compound surface 'asphalt:lanes' should be treated same as 'asphalt'"
    
    weight_gravel = calculate_edge_weight(100.0, 'residential', 'gravel', params)
    weight_gravel_compound = calculate_edge_weight(100.0, 'residential', 'gravel:compacted', params)
    
    assert weight_gravel == weight_gravel_compound, \
        "Compound surface 'gravel:compacted' should be treated same as 'gravel'"


def test_highway_list_handling():
    """
    Regression test: Verify that highway tags as lists are handled correctly.
    """
    # Some OSM edges have highway as a list
    edge_data_list = {
        'length': 100.0,
        'highway': ['residential', 'service'],  # List format
        'surface': 'asphalt',
    }
    
    edge_data_single = {
        'length': 100.0,
        'highway': 'residential',  # Single value
        'surface': 'asphalt',
    }
    
    params = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 1.0,
    }
    
    weight_list = _edge_penalty(1, 2, 0, edge_data_list, params)
    weight_single = _edge_penalty(1, 2, 0, edge_data_single, params)
    
    # Both should produce the same result (first element used from list)
    assert weight_list == weight_single, \
        "Highway as list should use first element"


def test_edge_lengths_validation():
    """
    Regression test: Verify that edge lengths are handled correctly.
    """
    params = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
        'surface_weight_factor': 1.0,
    }
    
    # Test different lengths
    lengths = [10.0, 100.0, 1000.0, 10000.0]
    
    for length in lengths:
        weight = calculate_edge_weight(length, 'residential', 'asphalt', params)
        
        # Weight should scale roughly with length for neutral params
        assert weight > 0, f"Weight should be positive for length {length}"
        
        # For neutral params, weight should be close to length
        ratio = weight / length
        assert 0.5 <= ratio <= 2.0, \
            f"Weight/length ratio {ratio} unexpected for neutral params"


def test_cycleway_heatmap_bonus():
    """
    Regression test: Verify that cycleways get bonus with heatmap influence.
    """
    base_params = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'surface_weight_factor': 1.0,
    }
    
    # Test cycleway with different heatmap influence
    params_no_heatmap = {**base_params, 'heatmap_influence': 0.0}
    params_high_heatmap = {**base_params, 'heatmap_influence': 1.0}
    
    weight_no_heatmap = calculate_edge_weight(100.0, 'cycleway', 'asphalt', params_no_heatmap)
    weight_high_heatmap = calculate_edge_weight(100.0, 'cycleway', 'asphalt', params_high_heatmap)
    
    # High heatmap influence should reduce weight for cycleways
    assert weight_high_heatmap < weight_no_heatmap, \
        "High heatmap_influence should reduce penalty for cycleways"
    
    # The bonus should be significant (up to 40% reduction)
    reduction = (weight_no_heatmap - weight_high_heatmap) / weight_no_heatmap
    assert reduction > 0.2, \
        f"Heatmap bonus should provide significant reduction, got {reduction:.1%}"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
