from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Tuple
from app.routing import compute_route
import os

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
    """
    coords, gpx = compute_route(req.start, req.end, req.params.dict())
    return {"coords": coords, "gpx": gpx}


@app.get('/')
async def index():
    """Serve the web interface if it exists, otherwise return API info."""
    index_path = os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"msg": "Jadlo Route Planner PoC - use POST /route or visit the web interface"}
