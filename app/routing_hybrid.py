"""
Hybrid routing module that supports both OSMnx and GraphHopper backends.

This module provides intelligent routing that can:
1. Try GraphHopper first (if available) for fast routing
2. Fall back to OSMnx if GraphHopper is unavailable
3. Allow manual backend selection via environment variables

Environment Variables:
    ROUTING_BACKEND: 'auto' (default), 'graphhopper', 'osmnx'
    GRAPHHOPPER_URL: GraphHopper server URL (default: http://localhost:8989)
"""

import os
import logging
from typing import Tuple, List, Dict, Any

logger = logging.getLogger(__name__)

# Routing backend configuration
ROUTING_BACKEND = os.getenv('ROUTING_BACKEND', 'auto').lower()


def compute_route_hybrid(
    start: Tuple[float, float],
    end: Tuple[float, float],
    params: Dict[str, Any],
    backend: str = None
) -> Tuple[List[Tuple[float, float]], str, str]:
    """
    Compute route using hybrid backend selection.
    
    Backend selection priority:
    1. If backend parameter is specified, use that
    2. If ROUTING_BACKEND env var is set, use that
    3. Otherwise, try GraphHopper first, fall back to OSMnx
    
    Args:
        start: (lat, lon) tuple for starting point
        end: (lat, lon) tuple for destination  
        params: Routing parameters dict
        backend: Optional backend override ('graphhopper', 'osmnx', or None)
        
    Returns:
        Tuple of (coordinates list, GPX string, backend_used)
        
    Raises:
        Exception: If routing fails on all available backends
    """
    # Determine which backend to use
    selected_backend = backend or ROUTING_BACKEND
    
    if selected_backend == 'graphhopper':
        return _try_graphhopper(start, end, params, fallback=False)
    elif selected_backend == 'osmnx':
        return _try_osmnx(start, end, params)
    else:  # 'auto'
        return _try_graphhopper(start, end, params, fallback=True)


def _try_graphhopper(
    start: Tuple[float, float],
    end: Tuple[float, float],
    params: Dict[str, Any],
    fallback: bool = True
) -> Tuple[List[Tuple[float, float]], str, str]:
    """
    Try routing with GraphHopper, optionally falling back to OSMnx.
    
    Args:
        start: Starting coordinates
        end: Destination coordinates
        params: Routing parameters
        fallback: If True, fall back to OSMnx on failure
        
    Returns:
        Tuple of (coordinates, GPX, backend_used)
    """
    try:
        from app.routing_graphhopper import compute_route_graphhopper, is_graphhopper_available
        
        if not is_graphhopper_available():
            if fallback:
                logger.info("GraphHopper not available, falling back to OSMnx")
                return _try_osmnx(start, end, params)
            else:
                raise Exception("GraphHopper server not available")
        
        coords, gpx = compute_route_graphhopper(start, end, params)
        return coords, gpx, 'graphhopper'
        
    except Exception as e:
        logger.warning(f"GraphHopper routing failed: {e}")
        if fallback:
            logger.info("Falling back to OSMnx")
            return _try_osmnx(start, end, params)
        else:
            raise


def _try_osmnx(
    start: Tuple[float, float],
    end: Tuple[float, float],
    params: Dict[str, Any]
) -> Tuple[List[Tuple[float, float]], str, str]:
    """
    Route using OSMnx (original implementation).
    
    Args:
        start: Starting coordinates
        end: Destination coordinates
        params: Routing parameters
        
    Returns:
        Tuple of (coordinates, GPX, backend_used)
    """
    try:
        from app.routing import compute_route
        
        coords, gpx = compute_route(start, end, params)
        return coords, gpx, 'osmnx'
        
    except Exception as e:
        logger.error(f"OSMnx routing failed: {e}")
        raise Exception(f"All routing backends failed. Last error: {e}")


def get_available_backends() -> Dict[str, bool]:
    """
    Check which routing backends are available.
    
    Returns:
        dict: Backend availability status
    """
    backends = {
        'osmnx': False,
        'graphhopper': False,
    }
    
    # Check OSMnx
    try:
        import osmnx
        backends['osmnx'] = True
    except ImportError:
        pass
    
    # Check GraphHopper
    try:
        from app.routing_graphhopper import is_graphhopper_available
        backends['graphhopper'] = is_graphhopper_available()
    except Exception:
        pass
    
    return backends


def get_routing_info() -> Dict[str, Any]:
    """
    Get information about routing configuration and available backends.
    
    Returns:
        dict: Routing configuration and status
    """
    backends = get_available_backends()
    
    return {
        'configured_backend': ROUTING_BACKEND,
        'available_backends': backends,
        'recommendation': 'graphhopper' if backends['graphhopper'] else 'osmnx',
        'graphhopper_url': os.getenv('GRAPHHOPPER_URL', 'http://localhost:8989'),
    }


# Example usage
if __name__ == '__main__':
    import json
    
    print("Routing Configuration")
    print("=" * 50)
    info = get_routing_info()
    print(json.dumps(info, indent=2))
    
    print("\nTest route:")
    start = (52.2297, 21.0122)  # Warsaw center
    end = (52.1672, 20.9679)     # Warsaw airport
    params = {
        'surface_weight_factor': 1.5,
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.2,
    }
    
    try:
        coords, gpx, backend = compute_route_hybrid(start, end, params)
        print(f"✓ Route computed using {backend}")
        print(f"  Points: {len(coords)}")
        print(f"  GPX size: {len(gpx)} bytes")
    except Exception as e:
        print(f"✗ Route failed: {e}")
