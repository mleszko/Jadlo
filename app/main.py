from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional, Tuple
from app.routing import compute_route

app = FastAPI(title="Jadlo Route Planner PoC")

class RouteParams(BaseModel):
    prefer_main_roads: float = Field(0.5, ge=0.0, le=1.0, description="0 = avoid main roads, 1 = prefer main roads")
    prefer_unpaved: float = Field(0.5, ge=0.0, le=1.0, description="0 = avoid unpaved, 1 = prefer unpaved")
    heatmap_influence: float = Field(0.0, ge=0.0, le=1.0, description="0 = ignore heatmaps, 1 = follow heatmap strongly (mocked)")
    prefer_streetview: float = Field(0.0, ge=0.0, le=1.0, description="0 = ignore streetview, 1 = prefer segments with streetview (requires external API)")

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
    return {"msg": "Jadlo Route Planner PoC - use POST /route"}
