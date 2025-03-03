"""
FastAPI server for the build inspector web interface.
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Dict, List

from .models import (
    DependencyNode,
    DependencyEdge,
    DependencyWarning,
    BuildMetrics,
    GraphLayout
)

app = FastAPI(
    title="Clyde Build Inspector",
    description="Web interface for inspecting build dependencies and metrics",
    version="0.1.0"
)

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173"   # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/api/dependencies", response_model=GraphLayout)
async def get_dependency_graph() -> GraphLayout:
    """Get the full dependency graph data."""
    try:
        # TODO: Implement actual dependency collection
        # This is a placeholder that should be replaced with real implementation
        return GraphLayout(
            nodes=[],
            edges=[],
            warnings=[]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dependencies/{package}", response_model=DependencyNode)
async def get_package_details(package: str) -> DependencyNode:
    """Get detailed information about a specific package."""
    try:
        # TODO: Implement actual package detail collection
        raise HTTPException(status_code=404, detail=f"Package {package} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics", response_model=BuildMetrics)
async def get_build_metrics() -> BuildMetrics:
    """Get current build metrics."""
    try:
        # TODO: Implement actual metrics collection
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve frontend in production
frontend_path = Path(__file__).parent / "frontend" / "dist"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True)) 