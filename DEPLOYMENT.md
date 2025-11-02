# Deployment Guide - Free Hosting Options

This guide explains how to deploy the Jadlo Route Planner for free so users can test it without installation.

**Note**: For research on free hosting with 32GB of RAM, see [FREE_HOSTING_32GB_RAM_RESEARCH.md](docs/FREE_HOSTING_32GB_RAM_RESEARCH.md). Summary: No cloud provider offers 32GB RAM for free; the best free option is Oracle Cloud with 24GB ARM VMs.

## Architecture

The application consists of:
- **Frontend**: Static HTML/CSS/JavaScript (in `/static` directory)
- **Backend**: FastAPI application (in `/app` directory)

## Option 1: All-in-One Deployment (Recommended for Testing)

### Render.com (Free Tier)

Render offers a free tier that can host both the API and serve static files.

1. **Create a Render account** at https://render.com

2. **Create a new Web Service**:
   - Connect your GitHub repository
   - Select "Python" as the environment
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables**:
   - Set `PYTHON_VERSION` to `3.12.3` (or your preferred version)
   - (Optional) Set `ALLOWED_ORIGINS` to restrict CORS (e.g., `https://your-domain.com,https://www.your-domain.com`)
   - If not set, all origins are allowed (suitable for testing, not recommended for production)

4. **System Dependencies**:
   Add a `render.yaml` file (see below) or install via Dockerfile:
   ```
   apt-get update && apt-get install -y libgeos-dev libproj-dev libgdal-dev
   ```

5. **Access your app**:
   - Your app will be available at `https://your-app-name.onrender.com`
   - The web interface will be served at the root URL

**Note**: The free tier spins down after inactivity, so the first request may take 30-60 seconds.

### Railway.app (Free Trial)

1. **Create a Railway account** at https://railway.app

2. **Deploy from GitHub**:
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your Jadlo repository
   - Railway will auto-detect it's a Python app

3. **Configure**:
   - Railway will automatically install dependencies from `requirements.txt`
   - Add environment variables if needed

4. **Generate Domain**:
   - Go to Settings → Generate Domain
   - Your app will be available at the generated URL

**Note**: Railway offers $5 free credit per month.

## Option 2: Separate Frontend and Backend

### Frontend: GitHub Pages (Free, Static Hosting)

1. **Modify the HTML** to point to your API:
   Update the `apiUrl` in `static/index.html`:
   ```javascript
   const apiUrl = 'https://your-backend-url.onrender.com/route';
   ```

2. **Enable GitHub Pages**:
   - Go to your repository Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main`, folder: `/static`
   - Your site will be at `https://username.github.io/Jadlo/`

3. **Update CORS** in `app/main.py`:
   ```python
   allow_origins=["https://username.github.io", "http://localhost:8000"]
   ```

### Backend Options:

#### A. Render.com (Free Tier)
See "Option 1" above for backend deployment.

#### B. Fly.io (Free Tier)

1. **Install flyctl**: Follow https://fly.io/docs/getting-started/installing-flyctl/

2. **Login**: `flyctl auth login`

3. **Launch app**: `flyctl launch`
   - Follow prompts to configure your app
   - Fly will generate a `fly.toml` file

4. **Deploy**: `flyctl deploy`

5. **Your API** will be at `https://your-app-name.fly.dev`

**Note**: Fly.io offers limited free tier with resource constraints.

#### C. Vercel (Serverless Functions - Limited)

Vercel can host the static site and API as serverless functions, but OSMnx may exceed size limits.

## Configuration Files

### `render.yaml` (for Render.com)

Create this file in the repository root:

```yaml
services:
  - type: web
    name: jadlo-route-planner
    runtime: python
    buildCommand: |
      apt-get update && apt-get install -y libgeos-dev libproj-dev libgdal-dev
      pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.3
    plan: free
```

### `Dockerfile` (Alternative for Render/Railway/Fly)

```dockerfile
FROM python:3.12-slim

# Install system dependencies for osmnx
RUN apt-get update && apt-get install -y \
    libgeos-dev \
    libproj-dev \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Testing Locally

Before deploying, test locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload

# Open browser
# Navigate to http://localhost:8000
```

The web interface will be served at the root URL.

## Important Notes

1. **Resource Limitations**: 
   - OSMnx queries can be memory-intensive
   - Free tiers have memory/CPU limits
   - Long routes may timeout or fail
   - Consider using the segmented runner for long routes

2. **Rate Limiting**:
   - Overpass API (used by OSMnx) has rate limits
   - Consider implementing request queuing for production

3. **Caching**:
   - The app uses OSMnx caching (stored in `cache/` directory)
   - Render/Railway have ephemeral filesystems, so cache won't persist
   - For better performance, consider using Redis or external cache

4. **Scaling**:
   - For production use, consider paid tiers or self-hosting
   - Implement proper error handling and monitoring
   - Add authentication if needed

## Recommended: Render.com Setup

For the easiest free deployment:

1. Fork or clone this repository
2. Sign up at https://render.com
3. Create a new Web Service from your repository
4. Add build command: 
   ```
   apt-get update && apt-get install -y libgeos-dev libproj-dev libgdal-dev && pip install -r requirements.txt
   ```
5. Add start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Deploy!

Your app will be available at `https://your-app-name.onrender.com` and users can use it directly without any installation.

## High-Memory Hosting (32GB+ RAM)

If you need high-memory hosting (32GB+ RAM) for production workloads or large-scale route generation:

### Reality Check
**No cloud provider offers 32GB RAM for free.** Free tiers typically provide 1-2GB RAM, designed for learning and prototyping. See [FREE_HOSTING_32GB_RAM_RESEARCH.md](docs/FREE_HOSTING_32GB_RAM_RESEARCH.md) for detailed research.

### Options for High-Memory Hosting

#### 1. Oracle Cloud (Best Free Option)
- **24GB RAM** on ARM-based VMs (Always Free)
- Closest to 32GB requirement among free tiers
- Limited to ARM architecture

#### 2. Academic/Research Cloud Credits
For academic institutions and research projects:
- **Google Cloud Research Credits**: Up to $5,000+ (up to 624GB RAM instances)
- **AWS Cloud Credit for Research**: Up to $5,000+ students, higher for faculty (up to 768GB RAM)
- **Azure Research Credits**: $5,000-$10,000+ (up to 448GB RAM)

Application required with research proposal.

#### 3. Trial Credits (Temporary)
For short-term high-memory needs:
- **AWS**: $200-$300 in trial credits
- **Google Cloud**: $300 credit (90 days)
- **Azure**: $200 credit (30 days)
- **Oracle**: $300 credit (30 days)

Requires credit card verification; expires after trial period.

#### 4. Paid Cloud Hosting
For sustained production use:
- **AWS EC2 m5.2xlarge** (32GB): ~$280/month
- **GCP n2-highmem-4** (32GB): ~$250/month  
- **Oracle Cloud ARM** (24GB): ~$22/month (best value)

#### 5. Memory Optimization (Recommended First Step)
Before pursuing expensive hosting:
- Use **segmented routing** (`scripts/run_poc_segmented.py`)
- Use **intersection-based routing** for lower memory usage
- Implement caching for OSMnx data
- Consider dedicated routing engines (GraphHopper, OSRM, Valhalla) that are more memory-efficient than OSMnx

### Recommendation
For Jadlo's demonstration and light usage, the current **Render.com free tier** with memory optimization is sufficient. For production-scale or academic research requiring 32GB+ RAM, apply for academic cloud credits or use paid tiers.

## Support

For issues or questions, please open an issue on the GitHub repository.
