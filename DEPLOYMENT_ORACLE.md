# Oracle Cloud Deployment Guide

This guide explains how to deploy the Jadlo Route Planner on Oracle Cloud Infrastructure (OCI) using the **Always Free** tier, which includes up to 24GB RAM on ARM-based Ampere A1 instances.

## Oracle Cloud Free Tier Benefits

Oracle Cloud offers an Always Free tier that includes:
- **4 ARM-based Ampere A1 cores** and **24 GB of memory** (can be configured as 1-4 VMs)
- **200 GB of Block Storage**
- **10 GB of Object Storage**
- **Outbound Data Transfer**: 10 TB per month
- **No credit card expiration** - free tier resources never expire

This is ideal for hosting the Jadlo Route Planner, as the 24GB RAM provides ample resources for OSMnx operations and route generation.

## Prerequisites

1. **Oracle Cloud Account**: Sign up at https://www.oracle.com/cloud/free/
2. **SSH Key Pair**: Generate if you don't have one:
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/oci_key
   ```

## Step 1: Create a Compute Instance

1. **Log in to OCI Console**: https://cloud.oracle.com

2. **Navigate to Compute > Instances**

3. **Create Instance**:
   - **Name**: `jadlo-route-planner`
   - **Image**: Ubuntu 22.04 (Minimal is recommended)
   - **Shape**: Select "Ampere" (ARM-based)
     - Choose VM.Standard.A1.Flex
     - **OCPU count**: 2-4 (up to 4 for free tier)
     - **Memory**: 12-24 GB (up to 24 GB for free tier)
   - **Networking**: 
     - Create new VCN or use existing
     - Assign a public IP address
   - **SSH Keys**: Upload your public key (`~/.ssh/oci_key.pub`)

4. **Click "Create"** and wait for the instance to provision (1-2 minutes)

5. **Note the Public IP Address** displayed in the instance details

## Step 2: Configure Network Security

1. **Navigate to Networking > Virtual Cloud Networks**

2. **Select your VCN** > Security Lists > Default Security List

3. **Add Ingress Rule** for HTTP traffic:
   - **Source CIDR**: `0.0.0.0/0`
   - **IP Protocol**: TCP
   - **Destination Port Range**: `8000`
   - **Description**: Jadlo Route Planner Web Interface

4. **Optional - Add HTTPS**: If you plan to use HTTPS
   - **Destination Port Range**: `443`

## Step 3: Connect to Your Instance

```bash
# SSH into your instance
ssh -i ~/.ssh/oci_key ubuntu@<PUBLIC_IP_ADDRESS>
```

## Step 4: Install Docker and Docker Compose

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo apt-get install -y docker compose

# Log out and back in for group changes to take effect
exit
# SSH back in
ssh -i ~/.ssh/oci_key ubuntu@<PUBLIC_IP_ADDRESS>

# Verify Docker installation
docker --version
docker compose --version
```

## Step 5: Deploy Jadlo Route Planner

```bash
# Clone the repository
git clone https://github.com/mleszko/Jadlo.git
cd Jadlo

# Build and start the application using Docker Compose
docker compose up -d

# Check logs to ensure it's running
docker compose logs -f
```

The application should start within 30-60 seconds. Press `Ctrl+C` to stop following logs.

## Step 6: Configure Firewall (Ubuntu UFW)

```bash
# Allow SSH (important - don't lock yourself out!)
sudo ufw allow 22/tcp

# Allow the application port
sudo ufw allow 8000/tcp

# Enable firewall
sudo ufw --force enable

# Check status
sudo ufw status
```

## Step 7: Access Your Application

Open your browser and navigate to:
```
http://<PUBLIC_IP_ADDRESS>:8000
```

You should see the Jadlo Route Planner web interface!

## Step 8: Set Up Domain Name (Optional)

1. **Get a free domain** (e.g., from Freenom, DuckDNS, or use a domain you own)

2. **Create an A record** pointing to your instance's public IP

3. **Update CORS settings** in `app/main.py` if needed

## Step 9: Enable HTTPS with Let's Encrypt (Optional but Recommended)

```bash
# Install Nginx
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/jadlo

# Add this configuration (replace YOUR_DOMAIN with your domain):
server {
    listen 80;
    server_name YOUR_DOMAIN;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Enable the site
sudo ln -s /etc/nginx/sites-available/jadlo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate (follow prompts)
sudo certbot --nginx -d YOUR_DOMAIN

# Add HTTPS ingress rule in OCI console (port 443)
```

## Step 10: Enable Auto-Start on Boot

The Docker Compose configuration already includes `restart: unless-stopped`, so the application will automatically start after instance reboots.

To verify:
```bash
# Check restart policy
docker inspect jadlo-route-planner | grep -A 5 RestartPolicy
```

## Monitoring and Maintenance

### View Application Logs
```bash
cd ~/Jadlo
docker compose logs -f
```

### Check Application Status
```bash
docker compose ps
```

### Restart Application
```bash
cd ~/Jadlo
docker compose restart
```

### Update Application
```bash
cd ~/Jadlo
git pull
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Check Resource Usage
```bash
# System resources
htop  # Install with: sudo apt-get install htop

# Docker stats
docker stats jadlo-route-planner
```

### Clean Up Docker Resources
```bash
# Remove unused images and containers
docker system prune -a

# View disk usage
docker system df
```

## Performance Optimization

### Cache Directory
The application caches OSM data in the `cache/` directory. This is mounted as a volume in docker compose.yml to persist between restarts.

To clear cache if it grows too large:
```bash
cd ~/Jadlo
sudo rm -rf cache/*
docker compose restart
```

### Memory Configuration
The docker compose.yml limits memory to 4GB by default. You can adjust this based on your instance size:

```yaml
deploy:
  resources:
    limits:
      memory: 8G  # Increase for larger routes
```

### Handle Long Routes
For routes longer than 100km, the application may take several minutes. Consider:
- Using the segmented runner
- Implementing a queue system for long-running requests
- Adding a background job processor (e.g., Celery with Redis)

## Troubleshooting

### Application Won't Start
```bash
# Check Docker logs
docker compose logs

# Check if port is already in use
sudo netstat -tulpn | grep 8000

# Verify Docker is running
sudo systemctl status docker
```

### Out of Memory Errors
```bash
# Check memory usage
free -h

# Check Docker container memory
docker stats jadlo-route-planner

# Increase swap if needed
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Connection Timeout
- Verify the OCI Security List includes ingress rule for port 8000
- Check Ubuntu firewall: `sudo ufw status`
- Ensure the instance has a public IP address

### OSM Data Download Fails
- This is usually due to Overpass API rate limits
- Wait a few minutes and retry
- Consider using smaller radius values for queries

## Cost Considerations

The Oracle Cloud Always Free tier provides:
- **Always Free** - No charges as long as you stay within free tier limits
- **No credit card expiration** - Resources remain free indefinitely
- **24GB RAM** on ARM instances is perfect for this application

Monitor your usage in the OCI console to ensure you stay within free tier limits.

## Security Best Practices

1. **Keep system updated**:
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

2. **Use SSH keys only** (disable password authentication):
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Set: PasswordAuthentication no
   sudo systemctl restart sshd
   ```

3. **Regular backups**: Use OCI Block Volume backups or snapshots

4. **Monitor logs** for suspicious activity:
   ```bash
   sudo tail -f /var/log/auth.log
   ```

5. **Implement rate limiting** if exposing to public internet

## Additional Resources

- **OCI Documentation**: https://docs.oracle.com/en-us/iaas/
- **OCI Free Tier**: https://www.oracle.com/cloud/free/
- **OCI Compute Shapes**: https://docs.oracle.com/en-us/iaas/Content/Compute/References/computeshapes.htm
- **Docker Documentation**: https://docs.docker.com/
- **Jadlo Repository**: https://github.com/mleszko/Jadlo

## Support

For issues specific to:
- **Jadlo application**: Open an issue on GitHub
- **Oracle Cloud**: Use OCI Support or Community Forums
- **Docker**: Check Docker documentation or Stack Overflow

---

**Congratulations!** Your Jadlo Route Planner is now running on Oracle Cloud with 24GB RAM, providing excellent performance for route generation. 🎉
