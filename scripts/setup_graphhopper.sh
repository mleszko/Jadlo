#!/bin/bash
#
# GraphHopper Setup Script for Jadlo
#
# This script downloads and configures GraphHopper for use with Jadlo.
# It sets up GraphHopper with Poland OSM data and custom bike routing profiles.
#
# Usage:
#   ./scripts/setup_graphhopper.sh [install_dir]
#
# Environment variables:
#   GRAPHHOPPER_VERSION: Version to download (default: 9.1)
#   OSM_REGION: OSM region to download (default: poland)
#

set -e

# Configuration
GRAPHHOPPER_VERSION=${GRAPHHOPPER_VERSION:-"9.1"}
OSM_REGION=${OSM_REGION:-"poland"}
INSTALL_DIR=${1:-"./graphhopper"}

echo "=================================================="
echo "GraphHopper Setup for Jadlo"
echo "=================================================="
echo "Version: $GRAPHHOPPER_VERSION"
echo "OSM Region: $OSM_REGION"
echo "Install Directory: $INSTALL_DIR"
echo "=================================================="
echo

# Create install directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Download GraphHopper
echo "Step 1/5: Downloading GraphHopper..."
if [ ! -f "graphhopper-web-$GRAPHHOPPER_VERSION.jar" ]; then
    curl -L "https://github.com/graphhopper/graphhopper/releases/download/$GRAPHHOPPER_VERSION/graphhopper-web-$GRAPHHOPPER_VERSION.jar" \
        -o "graphhopper-web-$GRAPHHOPPER_VERSION.jar"
    echo "✓ GraphHopper downloaded"
else
    echo "✓ GraphHopper already downloaded"
fi

# Download OSM data
echo
echo "Step 2/5: Downloading OSM data for $OSM_REGION..."
mkdir -p data
if [ ! -f "data/$OSM_REGION-latest.osm.pbf" ]; then
    curl -L "https://download.geofabrik.de/europe/$OSM_REGION-latest.osm.pbf" \
        -o "data/$OSM_REGION-latest.osm.pbf"
    echo "✓ OSM data downloaded"
else
    echo "✓ OSM data already downloaded"
fi

# Create GraphHopper configuration
echo
echo "Step 3/5: Creating configuration..."
cat > config.yml << 'EOF'
# GraphHopper configuration for Jadlo
# Optimized for bicycle routing with surface preferences

graphhopper:
  datareader.file: data/poland-latest.osm.pbf
  graph.location: graph-cache
  graph.flag_encoders: bike,mtb
  
  # Profiles for different routing preferences
  profiles:
    - name: bike
      vehicle: bike
      weighting: fastest
      turn_costs: false
      
    - name: bike_paved
      vehicle: bike
      weighting: custom
      custom_model:
        speed:
          - if: surface == asphalt
            multiply_by: 1.0
          - if: surface == concrete
            multiply_by: 1.0
          - if: surface == paved
            multiply_by: 1.0
          - if: surface == gravel
            multiply_by: 0.7
          - if: surface == unpaved
            multiply_by: 0.5
          - if: surface == dirt
            multiply_by: 0.4
            
    - name: mtb
      vehicle: mtb
      weighting: fastest
      turn_costs: false
      
  # Memory and performance settings
  graph.dataaccess: RAM_STORE
  prepare.min_network_size: 200
  
  # API settings
  web.port: 8989

server:
  application_connectors:
    - type: http
      port: 8989
      bind_host: 0.0.0.0
  request_log:
    appenders: []
EOF

echo "✓ Configuration created"

# Build routing graph
echo
echo "Step 4/5: Building routing graph (this may take 5-10 minutes)..."
if [ ! -d "graph-cache" ]; then
    java -Xmx2g -jar "graphhopper-web-$GRAPHHOPPER_VERSION.jar" import config.yml
    echo "✓ Graph built successfully"
else
    echo "✓ Graph already built (delete graph-cache to rebuild)"
fi

# Create startup script
echo
echo "Step 5/5: Creating startup script..."
cat > start.sh << EOF
#!/bin/bash
# Start GraphHopper server for Jadlo

cd "\$(dirname "\$0")"

echo "Starting GraphHopper server..."
echo "API will be available at: http://localhost:8989"
echo "Press Ctrl+C to stop"
echo

java -Xmx512m -jar graphhopper-web-$GRAPHHOPPER_VERSION.jar server config.yml
EOF

chmod +x start.sh

# Create systemd service file (optional)
cat > graphhopper.service << EOF
[Unit]
Description=GraphHopper Routing Engine for Jadlo
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/java -Xmx512m -jar $(pwd)/graphhopper-web-$GRAPHHOPPER_VERSION.jar server $(pwd)/config.yml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Startup scripts created"

# Summary
echo
echo "=================================================="
echo "✓ GraphHopper Setup Complete!"
echo "=================================================="
echo
echo "To start GraphHopper:"
echo "  cd $INSTALL_DIR"
echo "  ./start.sh"
echo
echo "Or install as system service:"
echo "  sudo cp graphhopper.service /etc/systemd/system/"
echo "  sudo systemctl enable graphhopper"
echo "  sudo systemctl start graphhopper"
echo
echo "GraphHopper will be available at:"
echo "  http://localhost:8989"
echo
echo "Test the API:"
echo "  curl 'http://localhost:8989/health'"
echo
echo "Configure Jadlo to use GraphHopper:"
echo "  export ROUTING_BACKEND=auto"
echo "  export GRAPHHOPPER_URL=http://localhost:8989"
echo
echo "=================================================="
