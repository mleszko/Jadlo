from app.routing import _edge_penalty


def test_edge_penalty_basic():
    params = {
        'prefer_main_roads': 0.5,
        'prefer_unpaved': 0.5,
        'heatmap_influence': 0.0,
        'prefer_streetview': 0.0,
    }

    # Synthetic edge data: 100 m residential paved
    data = {'length': 100.0, 'highway': 'residential', 'surface': 'asphalt'}
    w1 = _edge_penalty(1, 2, 0, data, params)
    assert w1 > 0

    # If surface is unpaved, weight should be larger
    data_unpaved = {'length': 100.0, 'highway': 'residential', 'surface': 'unpaved'}
    w2 = _edge_penalty(1, 2, 0, data_unpaved, params)
    assert w2 > w1

    # If highway is primary and prefer_main_roads=1.0, penalty should be lower than when avoid
    params_pref = params.copy()
    params_pref['prefer_main_roads'] = 1.0
    data_primary = {'length': 100.0, 'highway': 'primary', 'surface': 'asphalt'}
    w_pref = _edge_penalty(1, 2, 0, data_primary, params_pref)

    params_avoid = params.copy()
    params_avoid['prefer_main_roads'] = 0.0
    w_avoid = _edge_penalty(1, 2, 0, data_primary, params_avoid)

    assert w_pref < w_avoid
