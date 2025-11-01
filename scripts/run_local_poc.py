"""Prosty skrypt uruchamiający PoC na krótkim fragmencie (centrum Warszawy).
Uwaga: wymaga zainstalowanego osmnx i zależności systemowych. Użyj bbox_buffer małego (np. 0.02).
"""
from app.routing import compute_route

# przykładowe bliskie punkty w Warszawie
start = (52.2296756, 21.0122287)  # Rynek/centrum
end = (52.235, 21.01)  # kilka kilometrów na północ
params = {"prefer_main_roads": 0.3, "prefer_unpaved": 0.2, "heatmap_influence": 0.0, "prefer_streetview": 0.0}

if __name__ == '__main__':
    try:
        coords, gpx = compute_route(start, end, params, bbox_buffer=0.02)
        print(f"Got {len(coords)} points in route")
        # zapisz GPX do pliku
        with open('poc_route.gpx', 'w', encoding='utf-8') as f:
            f.write(gpx)
        print('Saved GPX to poc_route.gpx')
    except Exception as e:
        print('Failed to compute route:', e)
        raise
