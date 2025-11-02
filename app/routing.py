"""
Routing module for Jadlo route planner.

This module implements route calculation using Dijkstra's algorithm (via NetworkX's shortest_path)
and A* algorithm (for intersection-based routing). Routes are calculated based on customizable
edge weights that consider:
- Road surface type (primary factor for route quality)
- Highway classification
- User preferences (main roads, unpaved surfaces, heatmap data)

The algorithm choice:
- Dijkstra's algorithm is used for standard routing (compute_route function)
- A* with geographic heuristic is used for intersection-based routing (compute_route_intersections)
- Both algorithms find optimal routes based on weighted edge values

Surface-based routing:
The route value calculation emphasizes surface type as requested, allowing users to:
- Prefer specific surface types (paved vs unpaved)
- Control the weight/importance of surface in route selection via surface_weight_factor
- Balance between shortest distance and preferred surface quality
"""
import os
from typing import Tuple, List, Dict, Any
import gpxpy
import gpxpy.gpx
import osmnx as ox
import networkx as nx
import logging
import time

# Memory optimization configuration for 24GB RAM systems
# These settings optimize OSMnx and Overpass API queries for systems with ample memory
MEMORY_ALLOCATION_GB = 20  # Allocate 20GB for Overpass queries (leaving 4GB for system)
MEMORY_ALLOCATION_BYTES = MEMORY_ALLOCATION_GB * 1024 * 1024 * 1024

ox.settings.use_cache = True
ox.settings.log_console = True
ox.settings.timeout = 300  # Increased from default 180s to allow longer queries on 24GB systems
ox.settings.max_query_area_size = 5000000000  # Increased from 2.5B to 5B for larger route queries
ox.settings.memory = MEMORY_ALLOCATION_BYTES
# Note: {timeout} and {maxsize} are placeholders that OSMnx fills in at query time
ox.settings.overpass_settings = f'[out:json][timeout:{{timeout}}][maxsize:{MEMORY_ALLOCATION_BYTES}]'

logger = logging.getLogger(__name__)

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

# Surface penalties - these are multiplied by the surface_weight_factor parameter
# to control how strongly surface type influences route selection
SURFACE_PENALTIES = {
    'paved': 1.0,
    'asphalt': 1.0,
    'concrete': 1.0,
    'gravel': 1.6,
    'unpaved': 2.0,
    'dirt': 2.0,
}


def _get_surface_penalty(surface: str) -> float:
    """Get base surface penalty for a given surface type.
    
    Handles compound surface types (e.g., 'asphalt:lanes') by checking the prefix.
    Returns 1.0 (neutral) for unknown surface types.
    
    Args:
        surface: Surface type string from OSM data
        
    Returns:
        float: Base penalty multiplier for this surface type
    """
    # Try exact match first
    penalty = SURFACE_PENALTIES.get(surface)
    if penalty is not None:
        return penalty
    
    # Handle compound surface types (e.g., 'asphalt:lanes' -> check 'asphalt')
    if ':' in surface:
        base_type = surface.split(':')[0]
        penalty = SURFACE_PENALTIES.get(base_type)
        if penalty is not None:
            return penalty
    
    # Default to neutral penalty for unknown surfaces
    return 1.0


def _edge_penalty(u, v, key, data, params: Dict[str, Any]) -> float:
    """Calculate edge weight/penalty based on route preferences.
    
    The weight calculation uses Dijkstra's algorithm (or A*) to find optimal routes.
    Surface type is a primary factor in route value calculation.
    
    Args:
        u, v, key: Edge identifiers
        data: Edge data containing length, highway, surface attributes
        params: User preferences including:
            - surface_weight_factor: Multiplier for surface penalty (default 1.0)
                Higher values = surface type has more influence on route choice
                Lower values = distance becomes relatively more important
            - prefer_main_roads: 0=avoid, 1=prefer main roads
            - prefer_unpaved: 0=avoid, 1=prefer unpaved surfaces
            - heatmap_influence: 0=ignore, 1=follow heatmap strongly
            
    Returns:
        float: Edge weight (lower is better, used by Dijkstra/A* algorithm)
    """
    # base: length in meters
    length = data.get('length', 1.0)

    # highway penalty
    highway = data.get('highway')
    if isinstance(highway, list):
        highway = highway[0]
    hp = HIGHWAY_PENALTIES.get(highway, 1.0)

    # Surface penalty - this is the primary factor for route value by surface
    # The surface_weight_factor parameter controls how strongly surface influences the route
    surface = data.get('surface')
    sp = 1.0
    if surface:
        base_sp = _get_surface_penalty(surface)
        # Apply surface_weight_factor: higher factor = surface matters more in route choice
        surface_weight_factor = params.get('surface_weight_factor', 1.0)
        # Convert penalty from base using exponential scaling for stronger effect
        # sp = base_sp ^ surface_weight_factor gives stronger differentiation
        sp = base_sp ** surface_weight_factor

    # prefer_main_roads: if user prefers main roads, we reduce penalty for main roads
    prefer_main = params.get('prefer_main_roads', 0.5)
    avoid_factor = 1.5
    prefer_factor = 0.7
    if highway in ('primary', 'secondary', 'trunk', 'motorway'):
        hp = hp * (avoid_factor + (prefer_factor - avoid_factor) * prefer_main)

    # prefer_unpaved: if user prefers unpaved, decrease penalty for gravel/unpaved
    prefer_unpaved = params.get('prefer_unpaved', 0.5)
    if surface in ('gravel', 'unpaved', 'dirt'):
        # Additional adjustment beyond base surface penalty for user who explicitly prefers unpaved
        sp = sp * (1.0 - 0.5 * (prefer_unpaved - 0.5))

    # heatmap influence: PoC - we don't have heatmap data, so we mock by looking for 'cycleway' tag
    heatmap_influence = params.get('heatmap_influence', 0.0)
    heatmap_bonus = 1.0
    if heatmap_influence > 0 and highway == 'cycleway':
        heatmap_bonus = 1.0 - 0.4 * heatmap_influence

    # streetview preference: PoC - not implemented, neutral
    streetview_pref = params.get('prefer_streetview', 0.0)

    # Final weight calculation: combines all factors
    # This weight is used by Dijkstra's algorithm to find the optimal route
    weight = length * hp * sp * heatmap_bonus
    return weight


def calculate_edge_weight(length: float, highway: str, surface: str | None, params: Dict[str, Any]) -> float:
    """Public API: Calculate edge weight for a road segment.
    
    This is a public wrapper around _edge_penalty for testing and external use.
    It calculates how the routing algorithm (Dijkstra/A*) will weight a road segment.
    
    Args:
        length: Length of road segment in meters
        highway: Highway type (e.g., 'residential', 'primary', 'cycleway')
        surface: Surface type (e.g., 'asphalt', 'gravel', 'dirt'), or None if unknown
        params: Routing parameters including:
            - surface_weight_factor: How strongly surface affects routing (default 1.0)
            - prefer_main_roads: 0=avoid, 1=prefer main roads
            - prefer_unpaved: 0=avoid, 1=prefer unpaved surfaces
            - heatmap_influence: 0=ignore, 1=follow heatmap
            
    Returns:
        float: Edge weight (lower is better, used by Dijkstra's algorithm)
        
    Example:
        >>> params = {'surface_weight_factor': 2.0, 'prefer_main_roads': 0.5, 
        ...           'prefer_unpaved': 0.5, 'heatmap_influence': 0.0}
        >>> weight_paved = calculate_edge_weight(100.0, 'residential', 'asphalt', params)
        >>> weight_dirt = calculate_edge_weight(100.0, 'residential', 'dirt', params)
        >>> # dirt road will have higher weight (less preferred)
        >>> assert weight_dirt > weight_paved
    """
    edge_data = {
        'length': length,
        'highway': highway,
        'surface': surface,
    }
    return _edge_penalty(None, None, None, edge_data, params)


def _haversine(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Return great-circle distance in meters between two (lat, lon) points."""
    from math import radians, sin, cos, atan2, sqrt

    lat1, lon1 = a
    lat2, lon2 = b
    R = 6371000.0
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a_ = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    c = 2 * atan2(sqrt(a_), sqrt(1 - a_))
    return R * c


def _bearing(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Return bearing in degrees from point a to b (lat, lon)."""
    from math import radians, degrees, atan2, sin, cos

    lat1, lon1 = map(radians, a)
    lat2, lon2 = map(radians, b)
    dlon = lon2 - lon1
    x = sin(dlon) * cos(lat2)
    y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
    return (degrees(atan2(x, y)) + 360) % 360


def _ensure_edge_lengths(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """Ensure every edge in G has a 'length' attribute.

    Try several osmnx helper entrypoints across versions. If none are available
    compute an approximate haversine distance between edge endpoints as fallback.
    Returns the possibly-updated graph (some osmnx helpers return a new graph).
    """
    # Try ox.add_edge_lengths (older/newer versions may expose it at module level)
    try:
        if hasattr(ox, 'add_edge_lengths') and callable(getattr(ox, 'add_edge_lengths')):
            logger.debug('Using ox.add_edge_lengths')
            return ox.add_edge_lengths(G)
    except Exception as e:
        logger.warning('ox.add_edge_lengths raised: %s', e)

    # Try osmnx.utils_graph.add_edge_lengths
    try:
        from osmnx import utils_graph as _ug

        if hasattr(_ug, 'add_edge_lengths') and callable(getattr(_ug, 'add_edge_lengths')):
            logger.debug('Using osmnx.utils_graph.add_edge_lengths')
            return _ug.add_edge_lengths(G)
    except Exception as e:
        logger.warning('osmnx.utils_graph.add_edge_lengths raised: %s', e)

    # Last-resort: compute approximate lengths from node coordinates
    logger.warning('Falling back to approximate haversine-based edge lengths')
    coords = {n: (G.nodes[n].get('y'), G.nodes[n].get('x')) for n in G.nodes}
    for u, v, k, data in G.edges(keys=True, data=True):
        if data.get('length'):
            continue
        a = coords.get(u)
        b = coords.get(v)
        if a and b and None not in a and None not in b:
            try:
                data['length'] = _haversine(a, b)
            except Exception:
                data['length'] = 1.0
        else:
            data['length'] = 1.0
    return G


def _is_intersection_node(G: nx.MultiDiGraph, node: int) -> bool:
    """Decide whether a node is an intersection/endpoint. Use undirected degree.

    Intersection defined as node with undirected degree != 2 (i.e., junction or dead-end).
    """
    Gu = G.to_undirected(reciprocal=False)
    deg = Gu.degree(node)
    return deg != 2


def simplify_graph_to_intersections(G: nx.MultiDiGraph) -> nx.DiGraph:
    """Simplified, defensive implementation: collapse chains of degree-2 nodes.

    This version is intentionally conservative and robust: it only relies on basic
    undirected traversal and node coordinates, and bails out cleanly on unexpected data.
    """
    try:
        Gu = G.to_undirected(reciprocal=False)
        H = nx.DiGraph()

        # safe coordinate extractor with fallbacks
        def node_coord(n):
            nd = G.nodes.get(n, {})
            y = nd.get('y') or nd.get('lat')
            x = nd.get('x') or nd.get('lon') or nd.get('lon_deg')
            if y is None or x is None:
                return None
            return (y, x)

        coords = {n: node_coord(n) for n in G.nodes}

        # build set of intersections (undirected degree != 2)
        intersections = {n for n in G.nodes if Gu.degree(n) != 2}

        # ensure intersection nodes present in H with coords
        for n in intersections:
            c = coords.get(n)
            if c:
                H.add_node(n, y=c[0], x=c[1])
            else:
                H.add_node(n)

        # For each intersection, walk each neighbor chain until next intersection
        MAX_HOPS = 5000
        for n in intersections:
            for nbr in Gu[n]:
                # walk forward from n -> nbr until we hit another intersection or max hops
                path = [n]
                prev = n
                cur = nbr
                hops = 0
                while cur not in intersections and hops < MAX_HOPS:
                    path.append(cur)
                    # next nodes excluding the one we came from
                    nexts = [x for x in Gu[cur] if x != prev]
                    if not nexts:
                        break
                    prev, cur = cur, nexts[0]
                    # detect simple cycles
                    if cur in path:
                        break
                    hops += 1

                # if we ended at an intersection different than n, add aggregated edge
                if cur == n:
                    continue
                if cur not in intersections:
                    # didn't reach intersection; skip
                    continue

                # Prefer to build geometry by concatenating original edge geometries when present.
                geom_edges: List[Tuple[float, float]] = []
                total_len = 0.0
                seq = path + [cur]
                for i in range(len(seq) - 1):
                    u = seq[i]
                    v = seq[i + 1]
                    ed = G.get_edge_data(u, v) or G.get_edge_data(v, u)
                    if not ed:
                        continue
                    data = next(iter(ed.values()))
                    # sum lengths if available
                    total_len += data.get('length', 0.0)
                    # if this edge carries a shapely geometry, use its coordinates
                    geom_obj = data.get('geometry')
                    if geom_obj is not None:
                        try:
                            coords_seq = list(geom_obj.coords)
                            # geom_obj coords are (lon, lat) -> convert to (lat, lon)
                            conv = [(lat, lon) for (lon, lat) in coords_seq]
                            if geom_edges and geom_edges[-1] == conv[0]:
                                geom_edges.extend(conv[1:])
                            else:
                                geom_edges.extend(conv)
                        except Exception:
                            # fallback to node coords if geometry extraction fails
                            c_u = coords.get(u)
                            c_v = coords.get(v)
                            if c_u and (not geom_edges or geom_edges[-1] != c_u):
                                geom_edges.append(c_u)
                            if c_v:
                                geom_edges.append(c_v)
                    else:
                        # no geometry on edge: fallback to node coords
                        c_u = coords.get(u)
                        c_v = coords.get(v)
                        if c_u and (not geom_edges or geom_edges[-1] != c_u):
                            geom_edges.append(c_u)
                        if c_v:
                            geom_edges.append(c_v)

                # if we couldn't collect any edge geometries, fallback to simple node-based geom
                if geom_edges:
                    geom = geom_edges
                else:
                    geom = []
                    for p in seq:
                        c = coords.get(p)
                        if c:
                            if not geom or geom[-1] != c:
                                geom.append(c)

                # compute fallback length if not present
                if total_len == 0.0 and len(geom) >= 2:
                    total_len = _haversine(geom[0], geom[-1])

                # compute initial bearing (if possible)
                bearing = None
                if len(geom) >= 2:
                    bearing = _bearing(geom[0], geom[-1])

                # pick sample tags from first real edge if available
                highway = None
                surface = None
                if len(seq) >= 2:
                    ed0 = G.get_edge_data(seq[0], seq[1]) or G.get_edge_data(seq[1], seq[0])
                    if ed0:
                        fd = next(iter(ed0.values()))
                        highway = fd.get('highway')
                        surface = fd.get('surface')

                # add edge (n -> cur) if not already present or if shorter
                if H.has_edge(n, cur):
                    # prefer shorter aggregated segment
                    if H[n][cur].get('length', float('inf')) <= total_len:
                        continue
                H.add_edge(n, cur, length=total_len, geometry=geom, bearing=bearing, highway=highway, surface=surface)

        return H
    except Exception as e:
        logger.exception('simplify_graph_to_intersections failed: %s', e)
        # return empty graph so caller can fallback
        return nx.DiGraph()


def compute_route_intersections(start: Tuple[float, float], end: Tuple[float, float], params: Dict[str, Any], radius_meters: float | None = 12000, heading_threshold_deg: float = 60.0):
    """Compute a route on a simplified intersection graph using A*.

    This method reduces memory by collapsing degree-2 nodes and making decisions only at
    intersections. It also applies a heading bias: edges whose bearing deviates strongly
    from the direction to the final goal can receive an additional penalty unless they match
    user's preferences.
    
    Memory optimization note: With 24GB RAM, default radius_meters increased to 12000m (from 8000m)
    to provide better route coverage while utilizing available memory efficiently.
    """
    lat1, lon1 = start
    lat2, lon2 = end

    logger.info('start: fetch_graph')
    t0 = time.perf_counter()
    if radius_meters is not None:
        G = ox.graph_from_point((lat1, lon1), dist=radius_meters, network_type='bike')
    else:
        # build bbox around start/end with a small buffer
        buf = 0.12
        n = max(lat1, lat2) + buf
        s = min(lat1, lat2) - buf
        e = max(lon1, lon2) + buf
        w = min(lon1, lon2) - buf
        G = ox.graph_from_bbox(n, s, e, w, network_type='bike')
    logger.info('done: fetch_graph — took %.2f seconds', time.perf_counter() - t0)

    logger.info('start: ensure_edge_lengths')
    t0 = time.perf_counter()
    G = _ensure_edge_lengths(G)
    logger.info('done: ensure_edge_lengths — took %.2f seconds', time.perf_counter() - t0)

    # compute edge weights on the original graph so we can reconstruct detailed
    # segments between intersections using the full-resolution data
    logger.info('start: compute_edge_weights_on_original')
    t0 = time.perf_counter()
    for u, v, k, data in G.edges(keys=True, data=True):
        try:
            data['weight'] = _edge_penalty(u, v, k, data, params)
        except Exception:
            data['weight'] = data.get('length', 1.0)
    logger.info('done: compute_edge_weights_on_original — took %.2f seconds', time.perf_counter() - t0)

    logger.info('start: simplify_graph')
    t0 = time.perf_counter()
    H = simplify_graph_to_intersections(G)
    logger.info('done: simplify_graph — took %.2f seconds', time.perf_counter() - t0)

    if len(H) == 0:
        # fallback to original compute_route
        return compute_route(start, end, params, radius_meters=radius_meters)

    # find nearest intersection nodes to origin and destination
    orig_node = ox.distance.nearest_nodes(G, lon1, lat1)
    dest_node = ox.distance.nearest_nodes(G, lon2, lat2)

    # if nearest nodes are not intersection nodes, find nearest intersection by walking
    def nearest_intersection(node):
        if node in H.nodes:
            return node
        # BFS until intersection
        Gu = G.to_undirected(reciprocal=False)
        from collections import deque

        q = deque([node])
        seen = {node}
        while q:
            u = q.popleft()
            if u in H.nodes:
                return u
            for v in Gu[u]:
                if v in seen:
                    continue
                seen.add(v)
                q.append(v)
        return node

    s_node = nearest_intersection(orig_node)
    t_node = nearest_intersection(dest_node)

    # prepare heuristic for A*
    goal_coord = (lat2, lon2)

    def heuristic(u, v=None):
        cu = (H.nodes[u]['y'], H.nodes[u]['x'])
        return _haversine(cu, goal_coord)

    # compute edge weights with heading bias and user preferences
    for u, v, data in H.edges(data=True):
        # base weight = length * penalty
        fake_data = {'length': data.get('length', 1.0), 'highway': data.get('highway'), 'surface': data.get('surface')}
        base = _edge_penalty(u, v, 0, fake_data, params)
        # heading penalty: compare edge bearing to bearing from edge start to goal
        start_coord = (H.nodes[u]['y'], H.nodes[u]['x'])
        edge_bearing = data.get('bearing', 0.0)
        desired_bearing = _bearing(start_coord, goal_coord)
        diff = abs((edge_bearing - desired_bearing + 180) % 360 - 180)
        # if deviation is larger than threshold, add multiplicative penalty
        if diff > heading_threshold_deg:
            base *= 1.5 + (diff - heading_threshold_deg) / 180.0
        data['weight'] = base

    try:
        logger.info('start: astar_search')
        t0 = time.perf_counter()
        path = nx.astar_path(H, s_node, t_node, heuristic=heuristic, weight='weight')
        logger.info('done: astar_search — took %.2f seconds', time.perf_counter() - t0)
    except Exception:
        # fallback to original compute_route
        logger.exception('A* on intersection graph failed, falling back to compute_route')
        return compute_route(start, end, params, radius_meters=radius_meters)

    # Reconstruct full coordinates by routing on the original graph between
    # successive intersection nodes. This preserves the original edge geometries
    # (polylines) so the final GPX follows actual road shapes.
    coords: List[Tuple[float, float]] = []
    logger.info('start: reconstruct_coords_from_original_graph')
    t0 = time.perf_counter()

    # helper map of node coords for quick fallback
    coords_map = {n: (G.nodes[n].get('y'), G.nodes[n].get('x')) for n in G.nodes}

    for i in range(len(path) - 1):
        a = path[i]
        b = path[i + 1]
        try:
            seg_nodes = nx.shortest_path(G, a, b, weight='weight')
        except Exception:
            try:
                seg_nodes = nx.shortest_path(G, a, b, weight='length')
            except Exception:
                # unable to reconstruct this segment; skip
                logger.warning('unable to reconstruct segment %s -> %s on original graph', a, b)
                continue

        # convert the sequence of nodes into coordinates using original edge geometries
        for j in range(len(seg_nodes) - 1):
            u = seg_nodes[j]
            v = seg_nodes[j + 1]
            ed = G.get_edge_data(u, v) or G.get_edge_data(v, u)
            if not ed:
                # fallback to node coords
                cu = coords_map.get(u)
                cv = coords_map.get(v)
                if cu and (not coords or coords[-1] != cu):
                    coords.append(cu)
                if cv:
                    coords.append(cv)
                continue

            data = next(iter(ed.values()))
            geom_obj = data.get('geometry')
            if geom_obj is not None:
                try:
                    pts = [(lat, lon) for (lon, lat) in geom_obj.coords]
                    if coords and coords[-1] == pts[0]:
                        coords.extend(pts[1:])
                    else:
                        coords.extend(pts)
                except Exception:
                    cu = coords_map.get(u)
                    cv = coords_map.get(v)
                    if cu and (not coords or coords[-1] != cu):
                        coords.append(cu)
                    if cv:
                        coords.append(cv)
            else:
                cu = coords_map.get(u)
                cv = coords_map.get(v)
                if cu and (not coords or coords[-1] != cu):
                    coords.append(cu)
                if cv:
                    coords.append(cv)

    logger.info('done: reconstruct_coords_from_original_graph — took %.2f seconds', time.perf_counter() - t0)

    # ensure start and end points present
    if coords and coords[0] != (lat1, lon1):
        coords.insert(0, (lat1, lon1))
    if coords and coords[-1] != (lat2, lon2):
        coords.append((lat2, lon2))

    # generate GPX
    logger.info('start: generate_gpx')
    t0 = time.perf_counter()
    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(track)
    seg = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(seg)
    for lat, lon in coords:
        seg.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
    gpx_str = gpx.to_xml()
    logger.info('done: generate_gpx — took %.2f seconds', time.perf_counter() - t0)

    return coords, gpx_str


def compute_route(start: Tuple[float, float], end: Tuple[float, float], params: Dict[str, Any], bbox_buffer: float = 0.15, radius_meters: float | None = None):
    """PoC: fetch a fragment of the OSM graph between points (bbox with buffer) or around a point (radius_meters),
    compute the shortest route using custom weights.
    Returns list of (lat, lon) and GPX string.

    Note: fetching large graphs for long distances can be expensive; in production prefer a dedicated routing server.
    
    Memory optimization note: With 24GB RAM, bbox_buffer increased to 0.15 (from 0.12) to allow
    more comprehensive route options while staying within memory limits.
    """
    lat1, lon1 = start
    lat2, lon2 = end

    # Decide how to fetch the graph: either bbox between points (default) or circle around start point.
    logger.info('start: fetch_graph')
    t0 = time.perf_counter()
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
    logger.info('done: fetch_graph — took %.2f seconds', time.perf_counter() - t0)

    # Ensure the graph has 'length' attributes (robust across osmnx versions)
    logger.info('start: ensure_edge_lengths')
    t0 = time.perf_counter()
    G = _ensure_edge_lengths(G)
    logger.info('done: ensure_edge_lengths — took %.2f seconds', time.perf_counter() - t0)

    # Compute a weight for each edge and store it as the 'weight' attribute
    logger.info('start: compute_edge_weights')
    t0 = time.perf_counter()
    for u, v, k, data in G.edges(keys=True, data=True):
        try:
            wgt = _edge_penalty(u, v, k, data, params)
        except Exception:
            wgt = data.get('length', 1.0)
        data['weight'] = wgt
    logger.info('done: compute_edge_weights — took %.2f seconds', time.perf_counter() - t0)

    # find nearest nodes to the points
    orig_node = ox.distance.nearest_nodes(G, lon1, lat1)
    dest_node = ox.distance.nearest_nodes(G, lon2, lat2)

    # shortest path using the 'weight' attribute
    try:
        logger.info('start: shortest_path')
        t0 = time.perf_counter()
        route_nodes = nx.shortest_path(G, orig_node, dest_node, weight='weight')
        logger.info('done: shortest_path — took %.2f seconds', time.perf_counter() - t0)
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
