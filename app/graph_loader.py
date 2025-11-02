"""
Graph loader module for prebuilt graphs.

This module provides utilities to load and manage prebuilt graphs for frequently
used regions, avoiding repeated downloads from Overpass API.
"""

import os
import pickle
import json
import logging
from typing import Optional, Dict, Tuple
import networkx as nx

logger = logging.getLogger(__name__)


class GraphRegistry:
    """Registry of available prebuilt graphs."""
    
    def __init__(self, graphs_dir: str = "prebuilt_graphs"):
        """
        Initialize graph registry.
        
        Args:
            graphs_dir: Directory containing prebuilt graphs
        """
        self.graphs_dir = graphs_dir
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict:
        """Load registry from disk."""
        registry_path = os.path.join(self.graphs_dir, "registry.json")
        
        if not os.path.exists(registry_path):
            logger.info(f"No registry found at {registry_path}")
            return {}
        
        try:
            with open(registry_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
            return {}
    
    def list_graphs(self) -> Dict:
        """List all available prebuilt graphs."""
        return self.registry
    
    def get_graph_info(self, name: str) -> Optional[Dict]:
        """Get information about a specific graph."""
        return self.registry.get(name)
    
    def covers_area(
        self,
        graph_name: str,
        point: Tuple[float, float],
        radius_km: float = 0
    ) -> bool:
        """
        Check if a prebuilt graph covers the requested area.
        
        Args:
            graph_name: Name of the prebuilt graph
            point: (lat, lon) tuple
            radius_km: Additional radius needed (0 for point queries)
            
        Returns:
            bool: True if the graph covers the area
        """
        info = self.get_graph_info(graph_name)
        if not info:
            return False
        
        # Calculate distance from graph center to point using haversine
        from math import radians, sin, cos, atan2, sqrt
        
        def haversine(a: Tuple[float, float], b: Tuple[float, float]) -> float:
            """Calculate great-circle distance in meters between two (lat, lon) points."""
            lat1, lon1 = a
            lat2, lon2 = b
            R = 6371000.0  # Earth radius in meters
            phi1 = radians(lat1)
            phi2 = radians(lat2)
            dphi = radians(lat2 - lat1)
            dlambda = radians(lon2 - lon1)
            a_val = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
            c = 2 * atan2(sqrt(a_val), sqrt(1 - a_val))
            return R * c
        
        center = (info['center']['lat'], info['center']['lon'])
        graph_radius_km = info['radius_km']
        
        dist_km = haversine(center, point) / 1000
        
        # Check if point + radius fits within graph (use 90% of graph radius to be safe)
        return (dist_km + radius_km) <= (graph_radius_km * 0.9)
    
    def find_suitable_graph(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        buffer_km: float = 5
    ) -> Optional[str]:
        """
        Find a prebuilt graph that covers both start and end points.
        
        Args:
            start: Start point (lat, lon)
            end: End point (lat, lon)
            buffer_km: Additional buffer around points
            
        Returns:
            Optional[str]: Name of suitable graph, or None
        """
        for name in self.registry:
            if self.covers_area(name, start, buffer_km) and \
               self.covers_area(name, end, buffer_km):
                logger.info(f"Found suitable prebuilt graph: {name}")
                return name
        
        return None


def load_prebuilt_graph(
    name: str,
    graphs_dir: str = "prebuilt_graphs"
) -> Optional[nx.MultiDiGraph]:
    """
    Load a prebuilt graph from disk.
    
    Args:
        name: Name of the graph (e.g., 'warsaw_city')
        graphs_dir: Directory containing prebuilt graphs
        
    Returns:
        Optional[nx.MultiDiGraph]: Loaded graph, or None if not found
    """
    graph_path = os.path.join(graphs_dir, f"{name}.pkl")
    
    if not os.path.exists(graph_path):
        logger.warning(f"Prebuilt graph not found: {graph_path}")
        return None
    
    try:
        logger.info(f"Loading prebuilt graph: {name}")
        with open(graph_path, 'rb') as f:
            G = pickle.load(f)
        logger.info(f"Loaded graph with {len(G.nodes)} nodes, {len(G.edges)} edges")
        return G
    except Exception as e:
        logger.error(f"Failed to load prebuilt graph {name}: {e}")
        return None


def get_or_download_graph(
    start: Tuple[float, float],
    end: Tuple[float, float],
    radius_meters: int,
    graphs_dir: str = "prebuilt_graphs"
) -> Tuple[nx.MultiDiGraph, bool]:
    """
    Get a graph for routing, preferring prebuilt graphs when available.
    
    This is a convenience function that tries to use a prebuilt graph and falls
    back to downloading from Overpass API if no suitable prebuilt graph exists.
    
    Args:
        start: Start point (lat, lon)
        end: End point (lat, lon)
        radius_meters: Radius for graph download if needed
        graphs_dir: Directory containing prebuilt graphs
        
    Returns:
        Tuple containing:
            - graph (nx.MultiDiGraph): The loaded or downloaded graph
            - used_prebuilt (bool): True if loaded from prebuilt, False if downloaded
    """
    import osmnx as ox
    
    # Try to find a suitable prebuilt graph
    registry = GraphRegistry(graphs_dir)
    graph_name = registry.find_suitable_graph(start, end, buffer_km=5)
    
    if graph_name:
        G = load_prebuilt_graph(graph_name, graphs_dir)
        if G is not None:
            logger.info(f"Using prebuilt graph: {graph_name}")
            return G, True
    
    # Fall back to downloading
    logger.info("No suitable prebuilt graph found, downloading from Overpass API")
    
    # Calculate center point between start and end
    center_lat = (start[0] + end[0]) / 2
    center_lon = (start[1] + end[1]) / 2
    center = (center_lat, center_lon)
    
    G = ox.graph_from_point(center, dist=radius_meters, network_type='bike')
    logger.info(f"Downloaded graph with {len(G.nodes)} nodes, {len(G.edges)} edges")
    
    return G, False


# Example usage
if __name__ == '__main__':
    # List available prebuilt graphs
    registry = GraphRegistry()
    graphs = registry.list_graphs()
    
    print("Available prebuilt graphs:")
    for name, info in graphs.items():
        print(f"  - {name}: {info['radius_km']:.1f} km radius around "
              f"({info['center']['lat']}, {info['center']['lon']})")
    
    # Check if a location is covered
    warsaw_center = (52.2297, 21.0122)
    for name in graphs:
        if registry.covers_area(name, warsaw_center):
            print(f"\n{name} covers Warsaw center")
            
            # Load the graph
            G = load_prebuilt_graph(name)
            if G:
                print(f"  Nodes: {len(G.nodes):,}")
                print(f"  Edges: {len(G.edges):,}")
