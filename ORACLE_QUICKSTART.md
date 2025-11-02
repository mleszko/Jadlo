# Oracle Cloud - Quick Start Guide

Deploy Jadlo Route Planner on Oracle Cloud's **Always Free** tier with 24GB RAM.

## Why Oracle Cloud?

- ✅ **24GB RAM** (vs 512MB on most free tiers)
- ✅ **Never expires** - Always Free tier
- ✅ **No spin-down** - Always available
- ✅ **ARM Ampere** processors (excellent performance)
- ✅ **Persistent storage** for cache

## Prerequisites

- Oracle Cloud account ([Sign up free](https://www.oracle.com/cloud/free/))
- SSH key pair

## 🚀 Quick Deploy (5 minutes)

### Step 1: Create Instance

1. Go to **OCI Console** → **Compute** → **Instances** → **Create Instance**
2. Configure:
   - **Image**: Ubuntu 22.04
   - **Shape**: VM.Standard.A1.Flex (ARM)
   - **OCPU**: 2-4 (up to 4 free)
   - **Memory**: 12-24 GB (up to 24 free)
   - **Network**: Assign public IP
   - **SSH Keys**: Upload your public key

### Step 2: Configure Security

1. Go to **Networking** → **Virtual Cloud Networks**
2. Select your VCN → **Security Lists** → **Default Security List**
3. Add **Ingress Rule**:
   - Source: `0.0.0.0/0`
   - Protocol: TCP
   - Port: `8000`

### Step 3: Install & Deploy

SSH into your instance:
```bash
ssh -i ~/.ssh/oci_key ubuntu@<PUBLIC_IP>
```

Run the automated setup:
```bash
curl -fsSL https://raw.githubusercontent.com/mleszko/Jadlo/main/scripts/setup_oracle.sh -o setup.sh
chmod +x setup.sh
./setup.sh
```

The script will:
- Install Docker & Docker Compose
- Clone the repository
- Build and start the application
- Configure the firewall

### Step 4: Access

Open your browser:
```
http://<PUBLIC_IP>:8000
```

## 📊 Monitoring

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Check resources
docker stats
```

## 🔄 Updates

```bash
cd ~/Jadlo
git pull
docker-compose up -d --build
```

## 🛑 Troubleshooting

### Application not accessible
- Verify OCI Security List includes port 8000
- Check firewall: `sudo ufw status`
- Check logs: `docker-compose logs`

### Docker permission denied
Log out and back in after setup, or run:
```bash
newgrp docker
```

### Out of memory
Increase instance RAM in OCI console (up to 24GB free).

## 📖 Full Documentation

See [DEPLOYMENT_ORACLE.md](DEPLOYMENT_ORACLE.md) for:
- HTTPS setup with Let's Encrypt
- Custom domain configuration
- Performance tuning
- Security best practices
- Systemd service setup

## 💡 Tips

1. **Cache Persistence**: The cache directory is mounted as a volume, making subsequent route generations much faster
2. **Memory**: 24GB is perfect for long routes (100km+)
3. **Performance**: ARM Ampere processors offer excellent performance
4. **Cost**: Stay within free tier limits - monitor in OCI console

## 🆘 Support

- **Application Issues**: [GitHub Issues](https://github.com/mleszko/Jadlo/issues)
- **Oracle Cloud**: [OCI Documentation](https://docs.oracle.com/en-us/iaas/)

---

**Total setup time**: ~5-10 minutes
**Result**: Production-ready route planner with 24GB RAM 🎉
