#!/bin/bash
# Setup script for Oracle Cloud Infrastructure (OCI)
# This script automates the deployment of Jadlo Route Planner on OCI

set -e  # Exit on error

echo "============================================"
echo "Jadlo Route Planner - Oracle Cloud Setup"
echo "============================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Error: Please do not run this script as root${NC}"
    echo "Run as regular user (ubuntu): ./scripts/setup_oracle.sh"
    exit 1
fi

echo -e "${BLUE}Step 1: Updating system packages...${NC}"
sudo apt-get update
sudo apt-get upgrade -y
echo -e "${GREEN}✓ System updated${NC}"
echo ""

echo -e "${BLUE}Step 2: Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✓ Docker installed${NC}"
else
    echo -e "${GREEN}✓ Docker already installed${NC}"
fi
echo ""

echo -e "${BLUE}Step 3: Installing Docker Compose...${NC}"
if ! docker compose version &> /dev/null; then
    # Try installing docker-compose-plugin for newer Docker versions
    sudo apt-get install -y docker-compose-plugin || sudo apt-get install -y docker-compose
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✓ Docker Compose already available${NC}"
fi
echo ""

echo -e "${BLUE}Step 4: Configuring firewall...${NC}"
# Allow SSH (port 22) - important!
sudo ufw allow 22/tcp
# Allow application port (8000)
sudo ufw allow 8000/tcp
# Enable firewall
echo "y" | sudo ufw enable
echo -e "${GREEN}✓ Firewall configured${NC}"
sudo ufw status
echo ""

echo -e "${BLUE}Step 5: Cloning Jadlo repository...${NC}"
if [ ! -d "$HOME/Jadlo" ]; then
    cd $HOME
    git clone https://github.com/mleszko/Jadlo.git
    echo -e "${GREEN}✓ Repository cloned${NC}"
else
    echo -e "${GREEN}✓ Repository already exists${NC}"
    echo "Pulling latest changes..."
    cd $HOME/Jadlo
    git pull
fi
echo ""

echo -e "${BLUE}Step 6: Creating cache directory...${NC}"
cd $HOME/Jadlo
mkdir -p cache
echo -e "${GREEN}✓ Cache directory created${NC}"
echo ""

echo -e "${BLUE}Step 7: Building Docker image...${NC}"
# Use the ARM64-optimized Dockerfile if available
if [ -f "Dockerfile.arm64" ]; then
    echo "Using ARM64-optimized Dockerfile..."
    docker build -f Dockerfile.arm64 -t jadlo-route-planner .
else
    echo "Using standard Dockerfile..."
    docker build -t jadlo-route-planner .
fi
echo -e "${GREEN}✓ Docker image built${NC}"
echo ""

echo -e "${BLUE}Step 8: Starting application with Docker Compose...${NC}"
docker compose up -d
echo -e "${GREEN}✓ Application started${NC}"
echo ""

echo -e "${BLUE}Step 9: Waiting for application to be ready...${NC}"
# Wait for application to start (max 60 seconds)
for i in {1..12}; do
    if docker compose ps | grep -q "running"; then
        if docker compose exec -T jadlo-app curl -f http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Application is ready!${NC}"
            break
        fi
    fi
    echo "Waiting... ($i/12)"
    sleep 5
done
echo ""

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null || echo "Check OCI Console for Public IP")

echo "============================================"
echo -e "${GREEN}Installation Complete!${NC}"
echo "============================================"
echo ""
echo -e "${BLUE}Access your application:${NC}"
echo "  → http://$PUBLIC_IP:8000"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "  → Check status:   docker compose ps"
echo "  → View logs:      docker compose logs -f"
echo "  → Restart:        docker compose restart"
echo "  → Stop:           docker compose down"
echo "  → Update:         git pull && docker compose up -d --build"
echo ""
echo -e "${BLUE}Important:${NC}"
echo "  → Ensure OCI Security List allows inbound traffic on port 8000"
echo "  → See DEPLOYMENT_ORACLE.md for detailed configuration"
echo ""
echo -e "${GREEN}Note:${NC} If Docker commands fail, you may need to log out and back in"
echo "for group permissions to take effect."
echo ""
