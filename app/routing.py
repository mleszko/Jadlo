import os
from typing import Tuple, List, Dict, Any
import gpxpy
import gpxpy.gpx
import osmnx as ox
import networkx as nx

ox.config(use_cache=True, log_console=True)

# Mapping examples for penalties/bonuses. These are simple and intended for PoC only.
HIGHWAY_PENALTIES = {
    'motorway': 5.0,
    'trunk': 3.0,
    'primary': 2.0,
    'secondary': 1.5,
    'tertiary': 1.2,
    'residential': 1.0,
    'service': 1.0,
    'cycleway': 0.7,
    'path': 0.9,
}

SURFACE_PENALTIES = {
    'paved': 1.0,
    'asphalt': 1.0,
    'concrete': 1.0,
    'gravel': 1.6,
    'unpaved': 2.0,
    'dirt': 2.0,
}


def _edge_penalty(u, v, key, data, params: Dict[str, Any]) -> float:
    # base: length in meters
    length = data.get('length', 1.0)

    # highway penalty
    highway = data.get('highway')
    if isinstance(highway, list):
        highway = highway[0]
    hp = HIGHWAY_PENALTIES.get(highway, 1.0)

    # surface penalty
    surface = data.get('surface')
    sp = 1.0
    if surface:
        sp = SURFACE_PENALTIES.get(surface, SURFACE_PENALTIES.get(surface.split(':')[0], 1.0))

    # prefer_main_roads: if user prefers main roads, we reduce penalty for main roads
    prefer_main = params.get('prefer_main_roads', 0.5)
    # interpret prefer_main: 0 -> strongly avoid main roads (increase hp), 1 -> prefer main roads (decrease hp)
    # For simplicity: hp_adj = lerp(avoid_factor, prefer_factor, prefer_main)
    # choose factors
    avoid_factor = 1.5
    prefer_factor = 0.7
    if highway in ('primary', 'secondary', 'trunk', 'motorway'):
        hp = hp * (avoid_factor + (prefer_factor - avoid_factor) * prefer_main)

    # prefer_unpaved: if user prefers unpaved, decrease penalty for gravel/unpaved
    prefer_unpaved = params.get('prefer_unpaved', 0.5)
    if surface in ('gravel', 'unpaved', 'dirt'):
        # if prefer_unpaved close to 1, reduce sp
        sp = sp * (1.0 - 0.5 * (prefer_unpaved - 0.5))

    # heatmap influence: PoC - we don't have heatmap data, so we mock by looking for 'cycleway' tag
    heatmap_influence = params.get('heatmap_influence', 0.0)
    heatmap_bonus = 1.0
    if heatmap_influence > 0 and highway == 'cycleway':
        heatmap_bonus = 1.0 - 0.4 * heatmap_influence

    # streetview preference: PoC - not implemented, neutral
    streetview_pref = params.get('prefer_streetview', 0.0)

    weight = length * hp * sp * heatmap_bonus
    return weight


def compute_route(start: Tuple[float, float], end: Tuple[float, float], params: Dict[str, Any], bbox_buffer: float = 0.12, radius_meters: float | None = None):
    """PoC: fetch a fragment of the OSM graph between points (bbox with buffer) or around a point (radius_meters),
    compute the shortest route using custom weights.
    Returns list of (lat, lon) and GPX string.

    Note: fetching large graphs for long distances can be expensive; in production prefer a dedicated routing server.
    """
    lat1, lon1 = start
    lat2, lon2 = end

    # Decide how to fetch the graph: either bbox between points (default) or circle around start point.
    if radius_meters is not None:
        # Use graph_from_point with radius in meters (smaller, more predictable area for tests)
        G = ox.graph_from_point((lat1, lon1), dist=radius_meters, network_type='bike')
    else:
        # Simple bbox with buffer (degrees). For long routes this can be very large — PoC only.
        # `bbox_buffer` allows tests to request a much smaller area (e.g., 0.02 degrees ~ a few km).
        buf = float(bbox_buffer)
        n = max(lat1, lat2) + buf
        s = min(lat1, lat2) - buf
        e = max(lon1, lon2) + buf
        w = min(lon1, lon2) - buf

        # Fetch the graph for the bicycle network
        G = ox.graph_from_bbox(n, s, e, w, network_type='bike')

    # Ensure the graph has 'length' attributes
    # different osmnx versions expose helpers differently; try to call helper if present
    try:
        if hasattr(ox, 'add_edge_lengths'):
            G = ox.add_edge_lengths(G)
        else:
            # newer osmnx might expose the helper in a submodule; attempt common fallback
            try:
                from osmnx import utils_graph

                G = utils_graph.add_edge_lengths(G)
            except Exception:
                # assume lengths already present
                pass
    except Exception:
        # best-effort: assume 'length' keys exist on edges
        pass

    # Compute a weight for each edge and store it as the 'weight' attribute
    for u, v, k, data in G.edges(keys=True, data=True):
        try:
            wgt = _edge_penalty(u, v, k, data, params)
        except Exception:
            wgt = data.get('length', 1.0)
        data['weight'] = wgt

    # find nearest nodes to the points
    orig_node = ox.distance.nearest_nodes(G, lon1, lat1)
    dest_node = ox.distance.nearest_nodes(G, lon2, lat2)

    # shortest path using the 'weight' attribute
    try:
        route_nodes = nx.shortest_path(G, orig_node, dest_node, weight='weight')
    except nx.NetworkXNoPath:
        raise

    # convert nodes to coordinates
    coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route_nodes]

    # generate GPX
    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(track)
    seg = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(seg)
    for lat, lon in coords:
        seg.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
    gpx_str = gpx.to_xml()

    return coords, gpx_str
