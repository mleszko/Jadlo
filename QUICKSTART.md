# Quick Start Guide

Get started with Jadlo Route Planner in minutes!

## Option 1: Use the Web Interface (No Installation Required)

If deployed to a free hosting service, simply visit the URL and start generating routes!

**Example deployed URL**: `https://your-app-name.onrender.com`

### How to use:
1. Click on the map to set your start point
2. Click again to set your end point
3. Adjust the routing parameters using the sliders
4. Click "Generate GPX Route"
5. Download your custom GPX file

## Option 2: Run Locally

### Prerequisites
- Python 3.12+
- System dependencies: libgeos-dev, libproj-dev, libgdal-dev

### Installation

```bash
# Clone the repository
git clone https://github.com/mleszko/Jadlo.git
cd Jadlo

# Install Python dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload
```

### Access the Web Interface

Open your browser and navigate to: `http://localhost:8000`

### Use the API Directly

```bash
curl -X POST "http://localhost:8000/route" \
  -H "Content-Type: application/json" \
  -d '{
    "start": [52.2297, 21.0122],
    "end": [52.4064, 21.5250],
    "params": {
      "prefer_main_roads": 0.5,
      "prefer_unpaved": 0.2,
      "heatmap_influence": 0.0,
      "prefer_streetview": 0.0,
      "surface_weight_factor": 1.5
    }
  }'
```

## Option 3: Use Docker

```bash
# Build the image
docker build -t jadlo-route-planner .

# Run the container
docker run -p 8000:8000 jadlo-route-planner
```

Then open `http://localhost:8000` in your browser.

## Understanding Parameters

### Surface Weight Factor (0.1 - 3.0)
- **1.0**: Default balance between distance and surface quality
- **2.0+**: Strongly prefer better road surfaces (asphalt over gravel)
- **0.5**: Prioritize shorter distance over surface quality

### Prefer Main Roads (0.0 - 1.0)
- **1.0**: Prefer highways and major roads (faster routes)
- **0.5**: Balanced approach
- **0.0**: Prefer smaller, scenic roads

### Prefer Unpaved (0.0 - 1.0)
- **1.0**: Prefer gravel and dirt roads (adventure/gravel bike routing)
- **0.0**: Avoid unpaved surfaces entirely

### Heatmap Influence (0.0 - 1.0)
- **0.0**: Ignore popularity (default)
- **1.0**: Follow popular routes (experimental feature)

### Prefer Street View Coverage (0.0 - 1.0)
- **0.0**: Ignore street view availability
- **1.0**: Prefer roads with street view imagery (requires external API)

## Example Routes

### Short Urban Route
- Start: 52.2297, 21.0122 (Warsaw city center)
- End: 52.2500, 21.0500
- Parameters: Default

### Long Scenic Route
- Start: 52.2297, 21.0122 (Warsaw)
- End: 53.1325, 23.1688 (Białystok)
- Parameters: prefer_unpaved = 0.8, surface_weight_factor = 0.5

### Fast Highway Route
- Start: 52.2297, 21.0122
- End: 52.4064, 21.5250
- Parameters: prefer_main_roads = 1.0, surface_weight_factor = 1.0

## Troubleshooting

### Route Generation Takes Too Long
- Long routes (>100km) may take several minutes
- Try using preset "Short Route" to test the system
- The first request is slower as it fetches OSM data

### Map Not Loading
- Check browser console for errors
- Ensure JavaScript is enabled
- Check if external CDN resources are accessible

### API Errors
- Verify coordinates are valid (latitude: -90 to 90, longitude: -180 to 180)
- Check that both start and end points are provided
- Ensure the route is within a reasonable distance (<200km recommended)

## Next Steps

- Deploy to free hosting: See [DEPLOYMENT.md](DEPLOYMENT.md)
- Explore the API: Check `app/main.py` for endpoint details
- Read technical docs: See the main [README.md](README.md)
- Customize the interface: Edit `static/index.html`

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Read the documentation in `docs/`

Happy routing! 🗺️
