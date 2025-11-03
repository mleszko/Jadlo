# GraphHopper Migration Guide

## TL;DR

- **Setup time:** 30 minutes for basic routing, 1-2 days for full integration
- **Cost:** $0 (Apache 2.0 license, self-hosted)
- **Performance:** 500-1000x faster than OSMnx

## Is GraphHopper Free?

**Yes, GraphHopper is open-source and free to self-host.**

### Licensing Options

#### 1. Self-Hosted (Free & Recommended for Jadlo)

**GraphHopper Open Source**
- **License:** Apache 2.0 (very permissive)
- **Cost:** $0 - completely free
- **What you get:**
  - Full routing engine source code
  - Self-host on your own server
  - Unlimited requests
  - No API keys needed
  - Full control over data and privacy
  - Can customize routing profiles

**Perfect for Jadlo because:**
- ✅ Free forever
- ✅ No request limits
- ✅ No API keys to manage
- ✅ Full control
- ✅ Can run on Oracle Cloud Free Tier (24GB RAM)

#### 2. GraphHopper Cloud API (Paid Service)

If you don't want to self-host:
- **Free tier:** 5,000 requests/month
- **Paid plans:** Start at $99/month
- **Use case:** When you don't want to manage infrastructure

**Not necessary for Jadlo** - self-hosting is better for this use case.

## Why Switch from OSMnx to GraphHopper?

### Current (OSMnx) vs GraphHopper

| Feature | OSMnx (Current) | GraphHopper |
|---------|----------------|-------------|
| **Size** | 60-80 GB (Poland) | 2 GB (Poland) |
| **Memory** | 30-90 GB peak | 200 MB runtime |
| **Query Time** | Minutes (download + route) | 10-50 ms |
| **Scalability** | Limited to small areas | Entire countries |
| **Production Ready** | ❌ Development tool | ✅ Yes |
| **API Limits** | ❌ Overpass API limits | ✅ No limits (self-hosted) |
| **Cost** | $0 | $0 (self-hosted) |

### Benefits of Switching

1. **500-1000x Faster Queries**
   - OSMnx: Minutes to download graph + route
   - GraphHopper: 10-50 milliseconds to route

2. **30x Less Memory**
   - OSMnx: 30-90 GB peak for 200km
   - GraphHopper: 200 MB for entire Poland

3. **30x Smaller Storage**
   - OSMnx: 60-80 GB for Poland
   - GraphHopper: 2 GB for Poland

4. **No API Limits**
   - OSMnx: Limited by Overpass API
   - GraphHopper: Unlimited on your server

5. **Production Ready**
   - Used by major applications
   - Battle-tested at scale
   - Active development

## How to Switch to GraphHopper

### Step 1: Install GraphHopper

```bash
# Download GraphHopper
wget https://github.com/graphhopper/graphhopper/releases/download/9.1/graphhopper-web-9.1.jar

# Or use Docker (easier)
docker pull graphhopper/graphhopper:latest
```

### Step 2: Download OSM Data

```bash
# Poland extract from Geofabrik (updated daily)
wget https://download.geofabrik.de/europe/poland-latest.osm.pbf

# Size: ~1.8 GB download
```

### Step 3: Build Routing Graph

```bash
# Using JAR
java -Xmx2g -jar graphhopper-web-9.1.jar import poland-latest.osm.pbf

# Or using Docker
docker run -p 8989:8989 \
  -v $(pwd)/data:/data \
  graphhopper/graphhopper:latest \
  --input /data/poland-latest.osm.pbf
```

**Build time:** ~5 minutes on modern hardware
**Result:** ~2 GB routing graph

### Step 4: Start GraphHopper Server

```bash
# Using JAR
java -Xmx512m -jar graphhopper-web-9.1.jar server poland-latest.osm.pbf

# Or using Docker
docker run -p 8989:8989 \
  -v $(pwd)/data:/data \
  graphhopper/graphhopper:latest \
  --host 0.0.0.0
```

**Memory usage:** ~200 MB for Poland
**Startup time:** ~5 seconds

### Step 5: Query the API

```bash
# Test routing query (Warsaw to Krakow)
curl "http://localhost:8989/route?point=52.2297,21.0122&point=50.0647,19.9450&vehicle=bike"
```

**Response time:** 10-50 milliseconds

## Integration with Jadlo

### Option 1: Replace Backend (Recommended)

Replace `app/routing.py` OSMnx calls with GraphHopper API calls:

```python
# Before (OSMnx)
def compute_route(start, end, params):
    G = ox.graph_from_point(start, dist=radius_meters, network_type='bike')
    # ... routing on G
    
# After (GraphHopper)
def compute_route(start, end, params):
    import requests
    
    response = requests.get(
        'http://localhost:8989/route',
        params={
            'point': [f"{start[0]},{start[1]}", f"{end[0]},{end[1]}"],
            'vehicle': 'bike',
            'weighting': 'custom',  # Can implement surface preferences
            'points_encoded': False,
        }
    )
    
    data = response.json()
    coords = data['paths'][0]['points']['coordinates']
    # Convert to (lat, lon) format and generate GPX
```

### Option 2: Custom Profiles for Surface Routing

GraphHopper supports custom routing profiles with surface preferences:

```yaml
# config.yml
profiles:
  - name: bike_paved
    vehicle: bike
    weighting: custom
    custom_model:
      speed:
        - if: surface == asphalt
          multiply_by: 1.0
        - if: surface == gravel
          multiply_by: 0.6
        - if: surface == dirt
          multiply_by: 0.4
```

This gives you the same surface-based routing that Jadlo currently does with OSMnx!

### Option 3: Hybrid Approach

Keep current implementation for PoC, add GraphHopper as optional backend:

```python
# app/routing.py
def compute_route(start, end, params, use_graphhopper=False):
    if use_graphhopper and graphhopper_available():
        return compute_route_graphhopper(start, end, params)
    else:
        return compute_route_osmnx(start, end, params)
```

## Deployment Options

### Oracle Cloud Free Tier (Recommended)

GraphHopper works perfectly on Oracle Cloud Free Tier:
- **CPU:** 2 cores (enough)
- **RAM:** 24 GB (way more than needed - only needs 200 MB)
- **Storage:** 200 GB (plenty for multiple countries)
- **Cost:** $0 forever

**Setup script for Oracle Cloud:**

```bash
#!/bin/bash
# Install Java
sudo apt update
sudo apt install -y openjdk-17-jre-headless

# Download GraphHopper
cd /opt
sudo wget https://github.com/graphhopper/graphhopper/releases/download/9.1/graphhopper-web-9.1.jar

# Download Poland OSM data
sudo mkdir -p /opt/graphhopper/data
cd /opt/graphhopper/data
sudo wget https://download.geofabrik.de/europe/poland-latest.osm.pbf

# Build graph
cd /opt
sudo java -Xmx2g -jar graphhopper-web-9.1.jar import data/poland-latest.osm.pbf

# Create systemd service
sudo tee /etc/systemd/system/graphhopper.service > /dev/null <<EOF
[Unit]
Description=GraphHopper Routing Engine
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt
ExecStart=/usr/bin/java -Xmx512m -jar /opt/graphhopper-web-9.1.jar server data/poland-latest.osm.pbf
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable graphhopper
sudo systemctl start graphhopper
```

### Other Free Options

1. **Railway.app Free Tier**
   - 512 MB RAM (tight but works)
   - $5/month after free hours
   - Easy Docker deployment

2. **Fly.io Free Tier**
   - 3 shared CPUs
   - 256 MB RAM (need to optimize)
   - Good for testing

3. **Your Own Server**
   - Any VPS with 512 MB RAM
   - $5/month typical cost

## Cost Comparison

| Solution | Setup Cost | Monthly Cost | Maintenance |
|----------|-----------|--------------|-------------|
| **OSMnx (Current)** | $0 | $0 | High (API limits) |
| **GraphHopper Self-Hosted** | $0 | $0 (Oracle Free) | Low |
| **GraphHopper Cloud API** | $0 | $99+ | None |
| **Commercial APIs** | $0 | $100-1000+ | None |

**Recommendation:** Self-hosted GraphHopper on Oracle Cloud = $0/month forever

## Migration Timeline

### Quick Start (1 hour)

**Just want basic routing?** GraphHopper setup is **very fast**:

1. Download GraphHopper JAR (5 min)
2. Download Poland OSM data (10 min)
3. Build graph (5 min)
4. Start server (instant)
5. Test API (5 min)

**Total: ~30 minutes** for basic working routing!

### Full Integration (1-2 days)

**To integrate with Jadlo's custom features** (surface routing, parameter controls):

1. **Day 1 Morning:** Setup GraphHopper server
   - Install and configure (1 hour)
   - Download data and build graph (30 minutes)
   - Test API (30 minutes)

2. **Day 1 Afternoon:** Integrate with Jadlo
   - Create GraphHopper routing function (2 hours)
   - Test with example routes (1 hour)

3. **Day 2 Morning:** Custom profiles for surface routing
   - Configure custom weighting (2 hours)
   - Test surface preferences (1 hour)

4. **Day 2 Afternoon:** Deploy and test
   - Deploy to Oracle Cloud (1 hour)
   - End-to-end testing (2 hours)

**Note:** The 1-2 days is for **complete integration** with Jadlo's surface-based routing features, not just basic setup. GraphHopper itself installs in under 1 hour.

## Should You Switch?

### Switch to GraphHopper if:

✅ You want to go to production
✅ You need fast, reliable routing
✅ You want to avoid API limits
✅ You need to route across entire Poland
✅ You want minimal server costs

### Stick with OSMnx if:

⚠️ This is just a quick PoC/demo
⚠️ You only route in small areas (<20km)
⚠️ You don't mind slow responses
⚠️ Development/research project only

## Conclusion

**For Jadlo, switching to GraphHopper is highly recommended:**

1. **Still 100% free** (self-hosted, Apache 2.0 license)
2. **500-1000x faster** than current OSMnx approach
3. **30x less memory** (200 MB vs 6-90 GB)
4. **No API limits** (self-hosted = unlimited)
5. **Production ready** (used by major apps)
6. **Supports surface routing** (via custom profiles)
7. **Easy to deploy** (Oracle Cloud Free Tier)

**Next steps:**
1. Try the setup script above on a test server
2. Test basic routing
3. Configure custom profile for surface preferences
4. Integrate into Jadlo
5. Deploy to Oracle Cloud Free Tier

**Total cost:** $0 forever (using Oracle Cloud Free Tier)

## Resources

- [GraphHopper GitHub](https://github.com/graphhopper/graphhopper)
- [GraphHopper Documentation](https://docs.graphhopper.com/)
- [Custom Profiles Guide](https://docs.graphhopper.com/core/custom-profiles/)
- [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)
- [Geofabrik OSM Extracts](https://download.geofabrik.de/)
