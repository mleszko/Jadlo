# Deployment Guide - Free Hosting Options

This guide explains how to deploy the Jadlo Route Planner for free so users can test it without installation.

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

## Support

For issues or questions, please open an issue on the GitHub repository.
