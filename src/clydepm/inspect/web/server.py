"""
FastAPI server for the build inspector web interface.
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timezone

from .models import (
    DependencyNode,
    DependencyEdge,
    DependencyWarning,
    BuildMetrics,
    GraphLayout,
    Position
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

# Example data
EXAMPLE_NODES = [
    DependencyNode(
        id="app",
        name="my-app",
        version="1.0.0",
        is_dev_dep=False,
        has_warnings=False,
        size=1024,
        direct_deps=["fmt", "spdlog"],
        all_deps=["fmt", "spdlog", "catch2"],
        position=Position(x=0.0, y=0.0),
        last_used=datetime.now(timezone.utc)
    ),
    DependencyNode(
        id="fmt",
        name="fmt",
        version="9.1.0",
        is_dev_dep=False,
        has_warnings=False,
        size=512,
        direct_deps=[],
        all_deps=[],
        position=Position(x=-1.0, y=1.0),
        last_used=datetime.now(timezone.utc)
    ),
    DependencyNode(
        id="spdlog",
        name="spdlog",
        version="1.11.0",
        is_dev_dep=False,
        has_warnings=True,
        size=768,
        direct_deps=["fmt"],
        all_deps=["fmt"],
        position=Position(x=1.0, y=1.0),
        last_used=datetime.now(timezone.utc)
    ),
    DependencyNode(
        id="catch2",
        name="catch2",
        version="3.4.0",
        is_dev_dep=True,
        has_warnings=False,
        size=256,
        direct_deps=[],
        all_deps=[],
        position=Position(x=0.0, y=2.0),
        last_used=datetime.now(timezone.utc)
    )
]

EXAMPLE_EDGES = [
    DependencyEdge(
        id="app-fmt",
        source="app",
        target="fmt",
        is_circular=False
    ),
    DependencyEdge(
        id="app-spdlog",
        source="app",
        target="spdlog",
        is_circular=False
    ),
    DependencyEdge(
        id="spdlog-fmt",
        source="spdlog",
        target="fmt",
        is_circular=False
    )
]

EXAMPLE_WARNINGS = [
    DependencyWarning(
        id="w1",
        package="spdlog",
        message="Using older version of fmt than recommended",
        level="warning",
        context={"recommended_version": "10.0.0", "current_version": "9.1.0"}
    )
]

# API routes
@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/api/graph-settings")
async def get_graph_settings() -> Dict:
    """Get graph visualization settings."""
    return {
        "zoom": {
            "initial": 0.6,  # Start more zoomed out
            "min": 0.2,
            "max": 2.0
        },
        "layout": {
            "width": 1000,
            "height": 800,
            "nodeSpacing": 100,
            "rankSpacing": 150
        },
        "physics": {
            "enabled": True,
            "stabilization": True,
            "repulsion": {
                "nodeDistance": 200
            }
        }
    }

@app.get("/api/dependencies", response_model=GraphLayout)
async def get_dependency_graph() -> GraphLayout:
    """Get the full dependency graph data."""
    try:
        return GraphLayout(
            nodes=EXAMPLE_NODES,
            edges=EXAMPLE_EDGES,
            warnings=EXAMPLE_WARNINGS
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dependencies/{package}", response_model=DependencyNode)
async def get_package_details(package: str) -> DependencyNode:
    """Get detailed information about a specific package."""
    try:
        for node in EXAMPLE_NODES:
            if node.id == package:
                return node
        raise HTTPException(status_code=404, detail=f"Package {package} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics", response_model=BuildMetrics)
async def get_build_metrics() -> BuildMetrics:
    """Get current build metrics."""
    try:
        return BuildMetrics(
            total_time=15.3,
            cache_hits=42,
            cache_misses=3,
            artifact_sizes={
                "my-app": 1024 * 1024,  # 1MB
                "fmt": 512 * 1024,      # 512KB
                "spdlog": 768 * 1024,   # 768KB
                "catch2": 256 * 1024    # 256KB
            },
            memory_usage=256.5,  # MB
            cpu_usage=45.2,      # Percentage
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve frontend in production
frontend_path = Path(__file__).parent / "frontend" / "dist"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True)) 