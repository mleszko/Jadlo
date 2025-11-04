from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Tuple
import os

# Import routing modules
from app.routing import compute_route  # Original OSMnx routing
try:
    from app.routing_hybrid import compute_route_hybrid, get_routing_info
    HYBRID_ROUTING_AVAILABLE = True
except ImportError:
    HYBRID_ROUTING_AVAILABLE = False

app = FastAPI(title="Jadlo Route Planner PoC")

# Add CORS middleware to allow web interface to call the API
# Configure allowed origins based on environment
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],  # In production, set ALLOWED_ORIGINS env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files if the static directory exists
static_path = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

class RouteParams(BaseModel):
    prefer_main_roads: float = Field(0.5, ge=0.0, le=1.0, description="0 = avoid main roads, 1 = prefer main roads")
    prefer_unpaved: float = Field(0.5, ge=0.0, le=1.0, description="0 = avoid unpaved, 1 = prefer unpaved")
    heatmap_influence: float = Field(0.0, ge=0.0, le=1.0, description="0 = ignore heatmaps, 1 = follow heatmap strongly (mocked)")
    prefer_streetview: float = Field(0.0, ge=0.0, le=1.0, description="0 = ignore streetview, 1 = prefer segments with streetview (requires external API)")
    surface_weight_factor: float = Field(1.0, ge=0.1, le=3.0, description="Multiplier for surface penalty (default 1.0). Higher values = surface type has stronger influence on route choice")

class RouteRequest(BaseModel):
    start: Tuple[float, float] = Field(..., description="(lat, lon)")
    end: Tuple[float, float] = Field(..., description="(lat, lon)")
    params: Optional[RouteParams] = RouteParams()


@app.post('/route')
async def route(req: RouteRequest):
    """Compute route between start and end using PoC weighting logic.
    Returns: geo coordinates and GPX string.
    
    This endpoint automatically uses the best available routing backend:
    - Tries GraphHopper first (if available) for fast routing
    - Falls back to OSMnx if GraphHopper is unavailable
    - Set ROUTING_BACKEND env var to control behavior
    """
    if HYBRID_ROUTING_AVAILABLE:
        coords, gpx, backend = compute_route_hybrid(req.start, req.end, req.params.dict())
        return {
            "coords": coords, 
            "gpx": gpx,
            "backend": backend,
            "backend_info": "GraphHopper (fast)" if backend == 'graphhopper' else "OSMnx (original)"
        }
    else:
        coords, gpx = compute_route(req.start, req.end, req.params.dict())
        return {
            "coords": coords, 
            "gpx": gpx,
            "backend": "osmnx",
            "backend_info": "OSMnx (original)"
        }


@app.get('/health')
async def health():
    """Health check endpoint for monitoring and load balancers."""
    return {"status": "healthy", "service": "Jadlo Route Planner"}


@app.get('/routing/info')
async def routing_info():
    """Get information about routing backends and configuration."""
    if HYBRID_ROUTING_AVAILABLE:
        return get_routing_info()
    else:
        return {
            "configured_backend": "osmnx",
            "available_backends": {"osmnx": True, "graphhopper": False},
            "recommendation": "osmnx",
            "note": "Hybrid routing not available. Using OSMnx only."
        }


@app.get('/')
async def index():
    """Serve the web interface if it exists, otherwise return API info."""
    index_path = os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"msg": "Jadlo Route Planner PoC - use POST /route or visit the web interface"}
