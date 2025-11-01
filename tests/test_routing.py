import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.routing import _edge_penalty


def test_edge_penalty_default():
    data = {'length': 100.0, 'highway': 'residential', 'surface': 'asphalt'}
    params = {'prefer_main_roads': 0.5, 'prefer_unpaved': 0.5, 'heatmap_influence': 0.0, 'prefer_streetview': 0.0}
    w = _edge_penalty(1, 2, 0, data, params)
    assert w > 0
    # residential/asphalt default should yield base length (no extra penalty)
    assert abs(w - 100.0) == 0


def test_prefer_unpaved_reduces_penalty():
    data = {'length': 100.0, 'highway': 'path', 'surface': 'gravel'}
    params_avoid = {'prefer_main_roads': 0.5, 'prefer_unpaved': 0.0, 'heatmap_influence': 0.0}
    params_prefer = {'prefer_main_roads': 0.5, 'prefer_unpaved': 1.0, 'heatmap_influence': 0.0}
    w_avoid = _edge_penalty(1, 2, 0, data, params_avoid)
    w_prefer = _edge_penalty(1, 2, 0, data, params_prefer)
    assert w_prefer <= w_avoid


def test_prefer_main_roads_effect():
    data_main = {'length': 100.0, 'highway': 'primary', 'surface': 'asphalt'}
    params_avoid = {'prefer_main_roads': 0.0, 'prefer_unpaved': 0.5, 'heatmap_influence': 0.0}
    params_prefer = {'prefer_main_roads': 1.0, 'prefer_unpaved': 0.5, 'heatmap_influence': 0.0}
    w_avoid = _edge_penalty(1, 2, 0, data_main, params_avoid)
    w_prefer = _edge_penalty(1, 2, 0, data_main, params_prefer)
    assert w_prefer < w_avoid
