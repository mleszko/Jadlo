# GraphHopper Quick Start Guide

This guide helps you set up GraphHopper with Jadlo in under 30 minutes.

## Why GraphHopper?

- ✅ **500-1000x faster** - Queries in 10-50ms vs minutes with OSMnx
- ✅ **30x less memory** - 200 MB vs 30-90 GB
- ✅ **100% free** - Apache 2.0 license, self-hosted
- ✅ **No API limits** - Unlimited requests when self-hosted
- ✅ **Production ready** - Used by major applications

## Quick Start (3 Options)

### Option 1: Docker Compose (Easiest - 5 minutes)

**Requirements:** Docker and Docker Compose

```bash
# 1. Download Poland OSM data (one-time, ~1.8 GB)
mkdir -p graphhopper-data
cd graphhopper-data
curl -O https://download.geofabrik.de/europe/poland-latest.osm.pbf
cd ..

# 2. Start GraphHopper + Jadlo
docker-compose -f docker-compose.graphhopper.yml up -d

# 3. Wait for graph building (5-10 minutes first time)
docker-compose -f docker-compose.graphhopper.yml logs -f graphhopper

# 4. Test it works
curl 'http://localhost:8989/health'
curl 'http://localhost:8000/health'
```

**Done!** GraphHopper is at http://localhost:8989, Jadlo at http://localhost:8000

### Option 2: Setup Script (Recommended - 10 minutes)

**Requirements:** Java 17+ and curl

```bash
# 1. Run setup script
./scripts/setup_graphhopper.sh

# 2. Start GraphHopper
cd graphhopper
./start.sh

# 3. In another terminal, configure Jadlo
export ROUTING_BACKEND=auto
export GRAPHHOPPER_URL=http://localhost:8989

# 4. Start Jadlo
uvicorn app.main:app --reload
```

### Option 3: Manual Setup (Advanced - 15 minutes)

```bash
# 1. Download GraphHopper
mkdir graphhopper && cd graphhopper
curl -L https://github.com/graphhopper/graphhopper/releases/download/9.1/graphhopper-web-9.1.jar \
  -o graphhopper-web-9.1.jar

# 2. Download OSM data
mkdir data
curl -L https://download.geofabrik.de/europe/poland-latest.osm.pbf \
  -o data/poland-latest.osm.pbf

# 3. Build graph
java -Xmx2g -jar graphhopper-web-9.1.jar import data/poland-latest.osm.pbf

# 4. Start server
java -Xmx512m -jar graphhopper-web-9.1.jar server data/poland-latest.osm.pbf
```

## Verify GraphHopper is Working

```bash
# Check health
curl 'http://localhost:8989/health'

# Get server info
curl 'http://localhost:8989/info'

# Test route (Warsaw center to airport)
curl 'http://localhost:8989/route?point=52.2297,21.0122&point=52.1672,20.9679&vehicle=bike'
```

## Configure Jadlo to Use GraphHopper

### Method 1: Environment Variables (Recommended)

```bash
export ROUTING_BACKEND=auto          # Try GraphHopper first, fall back to OSMnx
export GRAPHHOPPER_URL=http://localhost:8989
```

### Method 2: .env File

Create `.env` file in Jadlo root:

```env
ROUTING_BACKEND=auto
GRAPHHOPPER_URL=http://localhost:8989
```

### Method 3: Docker Compose

Already configured in `docker-compose.graphhopper.yml`

## Test Jadlo with GraphHopper

```bash
# Start Jadlo
uvicorn app.main:app --reload

# Test routing endpoint
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{
    "start": [52.2297, 21.0122],
    "end": [52.1672, 20.9679],
    "params": {
      "surface_weight_factor": 1.5,
      "prefer_main_roads": 0.5,
      "prefer_unpaved": 0.2
    }
  }'
```

Response should be almost instant (<50ms) vs minutes with OSMnx!

## Backend Selection

Jadlo now supports three routing modes:

### Auto Mode (Default - Recommended)

```bash
export ROUTING_BACKEND=auto
```

- Tries GraphHopper first
- Falls back to OSMnx if GraphHopper unavailable
- Best for development and production

### GraphHopper Only

```bash
export ROUTING_BACKEND=graphhopper
```

- Always uses GraphHopper
- Fails if GraphHopper is unavailable
- Best for production when GraphHopper is guaranteed

### OSMnx Only

```bash
export ROUTING_BACKEND=osmnx
```

- Always uses OSMnx (original behavior)
- Ignores GraphHopper even if available
- Best for testing or small areas

## Check Routing Status

```bash
# Via Python
python -m app.routing_hybrid

# Via API (coming soon)
curl http://localhost:8000/routing/info
```

## Troubleshooting

### GraphHopper not starting

**Error:** "Address already in use"
```bash
# Check if port 8989 is in use
lsof -i :8989

# Or change GraphHopper port
java -jar graphhopper-web-9.1.jar server --port 8990 data/poland-latest.osm.pbf
export GRAPHHOPPER_URL=http://localhost:8990
```

### Graph building fails

**Error:** "OutOfMemoryError"
```bash
# Increase Java heap size
java -Xmx4g -jar graphhopper-web-9.1.jar import data/poland-latest.osm.pbf
```

### Jadlo not finding GraphHopper

**Error:** "GraphHopper server not available"
```bash
# Check GraphHopper is running
curl http://localhost:8989/health

# Check environment variable
echo $GRAPHHOPPER_URL

# Verify connection from Jadlo
python -c "from app.routing_graphhopper import is_graphhopper_available; print(is_graphhopper_available())"
```

### Routes failing

**Check backend status:**
```python
from app.routing_hybrid import get_routing_info
import json
print(json.dumps(get_routing_info(), indent=2))
```

## Production Deployment

### Oracle Cloud Free Tier (Recommended - $0/month)

See [GRAPHHOPPER_MIGRATION.md](GRAPHHOPPER_MIGRATION.md#oracle-cloud-free-tier-recommended) for complete setup.

**Quick setup:**
```bash
# SSH into Oracle Cloud instance
ssh ubuntu@your-instance

# Install Java
sudo apt update
sudo apt install -y openjdk-17-jre-headless

# Run setup script
curl -fsSL https://raw.githubusercontent.com/mleszko/Jadlo/main/scripts/setup_graphhopper.sh | bash

# Install as system service
cd graphhopper
sudo cp graphhopper.service /etc/systemd/system/
sudo systemctl enable graphhopper
sudo systemctl start graphhopper
```

### Other Deployment Options

- **Railway.app:** See docker-compose.graphhopper.yml
- **Fly.io:** Use Dockerfile with GraphHopper
- **Your own VPS:** Any server with 512 MB RAM

## Performance Comparison

| Metric | OSMnx | GraphHopper | Improvement |
|--------|-------|-------------|-------------|
| Query time | 60-300 sec | 10-50 ms | 1000x faster |
| Memory | 30-90 GB | 200 MB | 150x less |
| Setup time | Instant | 30 min | One-time |
| Cost | $0 | $0 | Same |

## Next Steps

1. ✅ GraphHopper running
2. ✅ Jadlo connected
3. → Configure custom surface routing profiles
4. → Deploy to production
5. → Remove OSMnx dependency (optional)

See [GRAPHHOPPER_MIGRATION.md](GRAPHHOPPER_MIGRATION.md) for full migration guide.

## Resources

- [GraphHopper Documentation](https://docs.graphhopper.com/)
- [Custom Routing Profiles](https://docs.graphhopper.com/core/custom-profiles/)
- [GraphHopper GitHub](https://github.com/graphhopper/graphhopper)
- [Geofabrik OSM Extracts](https://download.geofabrik.de/)
