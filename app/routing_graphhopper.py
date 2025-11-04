"""
GraphHopper routing integration for Jadlo.

This module provides routing via GraphHopper as an alternative to OSMnx.
GraphHopper is significantly faster and more memory-efficient for production use.

Benefits over OSMnx:
- 500-1000x faster queries (10-50ms vs minutes)
- 30x less memory (200 MB vs 30-90 GB)
- No API limits when self-hosted
- Production-ready and battle-tested
"""

import os
import logging
from typing import Tuple, List, Dict, Any, Optional
import httpx
import gpxpy
import gpxpy.gpx

logger = logging.getLogger(__name__)

# GraphHopper server configuration
GRAPHHOPPER_URL = os.getenv('GRAPHHOPPER_URL', 'http://localhost:8989')
GRAPHHOPPER_TIMEOUT = int(os.getenv('GRAPHHOPPER_TIMEOUT', '30'))


def is_graphhopper_available() -> bool:
    """
    Check if GraphHopper server is available and responding.
    
    Returns:
        bool: True if GraphHopper is available, False otherwise
    """
    try:
        response = httpx.get(
            f"{GRAPHHOPPER_URL}/health",
            timeout=5.0
        )
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"GraphHopper not available: {e}")
        return False


def compute_route_graphhopper(
    start: Tuple[float, float],
    end: Tuple[float, float],
    params: Dict[str, Any]
) -> Tuple[List[Tuple[float, float]], str]:
    """
    Compute route using GraphHopper server.
    
    Args:
        start: (lat, lon) tuple for starting point
        end: (lat, lon) tuple for destination
        params: Routing parameters including:
            - surface_weight_factor: How strongly surface affects routing
            - prefer_main_roads: 0=avoid, 1=prefer main roads
            - prefer_unpaved: 0=avoid, 1=prefer unpaved surfaces
            - heatmap_influence: Not used in GraphHopper (yet)
            
    Returns:
        Tuple of (coordinates list, GPX string)
        
    Raises:
        Exception: If GraphHopper is unavailable or request fails
    """
    if not is_graphhopper_available():
        raise Exception(
            f"GraphHopper server not available at {GRAPHHOPPER_URL}. "
            "Please start GraphHopper or use OSMnx routing."
        )
    
    # Map Jadlo parameters to GraphHopper profile
    profile = _select_graphhopper_profile(params)
    
    # Build GraphHopper API request
    api_params = {
        'point': [f"{start[0]},{start[1]}", f"{end[0]},{end[1]}"],
        'vehicle': 'bike',
        'profile': profile,
        'points_encoded': False,
        'instructions': False,
        'elevation': False,
    }
    
    # Add custom weighting hints based on Jadlo parameters
    api_params.update(_get_weighting_hints(params))
    
    try:
        logger.info(f"Requesting route from GraphHopper: {start} -> {end}")
        response = httpx.get(
            f"{GRAPHHOPPER_URL}/route",
            params=api_params,
            timeout=GRAPHHOPPER_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        
        if 'paths' not in data or len(data['paths']) == 0:
            raise Exception("No route found by GraphHopper")
        
        path = data['paths'][0]
        
        # Extract coordinates (GraphHopper returns [lon, lat], we need [lat, lon])
        coords = [
            (point[1], point[0]) 
            for point in path['points']['coordinates']
        ]
        
        # Generate GPX from coordinates
        gpx = _coords_to_gpx(coords)
        
        logger.info(f"GraphHopper route computed: {len(coords)} points, "
                   f"{path.get('distance', 0)/1000:.1f} km, "
                   f"{path.get('time', 0)/1000:.0f} seconds")
        
        return coords, gpx
        
    except httpx.HTTPStatusError as e:
        error_msg = f"GraphHopper API error: {e.response.status_code}"
        try:
            error_data = e.response.json()
            if 'message' in error_data:
                error_msg += f" - {error_data['message']}"
        except:
            pass
        logger.error(error_msg)
        raise Exception(error_msg)
    except httpx.RequestError as e:
        error_msg = f"GraphHopper request failed: {e}"
        logger.error(error_msg)
        raise Exception(error_msg)


def _select_graphhopper_profile(params: Dict[str, Any]) -> str:
    """
    Select appropriate GraphHopper profile based on Jadlo parameters.
    
    Args:
        params: Jadlo routing parameters
        
    Returns:
        str: GraphHopper profile name
    """
    # For now, use standard bike profile
    # Future: map to custom profiles based on surface preferences
    prefer_unpaved = params.get('prefer_unpaved', 0.5)
    
    if prefer_unpaved > 0.7:
        # Prefer unpaved surfaces - use mountain bike profile if available
        return 'mtb'
    else:
        # Standard bike profile
        return 'bike'


def _get_weighting_hints(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Jadlo parameters to GraphHopper weighting hints.
    
    Args:
        params: Jadlo routing parameters
        
    Returns:
        dict: GraphHopper API parameters for custom weighting
    """
    hints = {}
    
    # Map surface_weight_factor to GraphHopper's priority weighting
    surface_weight = params.get('surface_weight_factor', 1.0)
    if surface_weight != 1.0:
        # Higher surface weight = higher priority on good surfaces
        # This is simplified - full custom profiles would be defined in GraphHopper config
        hints['weighting'] = 'fastest'
    
    # Map prefer_main_roads
    prefer_main = params.get('prefer_main_roads', 0.5)
    if prefer_main > 0.6:
        # Prefer main roads
        hints['avoid'] = 'unpaved'
    elif prefer_main < 0.4:
        # Avoid main roads
        hints['avoid'] = 'motorway'
    
    return hints


def _coords_to_gpx(coords: List[Tuple[float, float]]) -> str:
    """
    Convert list of coordinates to GPX format.
    
    Args:
        coords: List of (lat, lon) tuples
        
    Returns:
        str: GPX XML string
    """
    gpx = gpxpy.gpx.GPX()
    
    # Create track
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    
    # Create segment
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)
    
    # Add points
    for lat, lon in coords:
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
    
    return gpx.to_xml()


def get_graphhopper_info() -> Dict[str, Any]:
    """
    Get information about the connected GraphHopper server.
    
    Returns:
        dict: Server information including version, profiles, etc.
    """
    try:
        response = httpx.get(
            f"{GRAPHHOPPER_URL}/info",
            timeout=5.0
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to get GraphHopper info: {e}")
        return {
            'available': False,
            'error': str(e)
        }


# Example usage and testing
if __name__ == '__main__':
    # Test GraphHopper connection
    print(f"GraphHopper URL: {GRAPHHOPPER_URL}")
    print(f"Available: {is_graphhopper_available()}")
    
    if is_graphhopper_available():
        print("\nServer info:")
        info = get_graphhopper_info()
        print(info)
        
        # Test route
        print("\nTest route: Warsaw center to airport")
        start = (52.2297, 21.0122)  # Warsaw center
        end = (52.1672, 20.9679)     # Warsaw airport
        params = {
            'surface_weight_factor': 1.5,
            'prefer_main_roads': 0.5,
            'prefer_unpaved': 0.2,
        }
        
        try:
            coords, gpx = compute_route_graphhopper(start, end, params)
            print(f"Route computed: {len(coords)} points")
            print(f"GPX length: {len(gpx)} bytes")
        except Exception as e:
            print(f"Route failed: {e}")
