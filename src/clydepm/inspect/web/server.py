"""
FastAPI server for the build inspector web interface.
"""
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
import json
import glob
import os

from .models import (
    DependencyNode,
    DependencyEdge,
    DependencyWarning,
    BuildMetrics,
    GraphLayout,
    Position,
    SourceTree,
    IncludePath,
    IncludePathType,
    SourceFile,
    CompilerCommand,
    BuildData,
    CompilationStep
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

# Build data directory
BUILD_DATA_DIR = Path.home() / ".clydepm" / "build_data"

def generate_example_source_tree(name: str) -> SourceTree:
    return SourceTree(
        name=name,
        path=f"src/{name}",
        type="directory",
        file_info=None,
        children=[
            SourceTree(
                name="include",
                path=f"src/{name}/include",
                type="directory",
                file_info=None,
                children=[
                    SourceTree(
                        name=f"{name}.h",
                        path=f"src/{name}/include/{name}.h",
                        type="header",
                        file_info=None,
                        children=[]
                    )
                ]
            ),
            SourceTree(
                name="src",
                path=f"src/{name}/src",
                type="directory",
                file_info=None,
                children=[
                    SourceTree(
                        name=f"{name}.cpp",
                        path=f"src/{name}/src/{name}.cpp",
                        type="source",
                        file_info=None,
                        children=[]
                    )
                ]
            )
        ]
    )

def generate_example_build_metrics(name: str) -> BuildMetrics:
    return BuildMetrics(
        total_time=5.67,
        cache_hits=10,
        cache_misses=2,
        artifact_sizes={f"lib{name}.a": 1024*1024},
        memory_usage=256.0,
        cpu_usage=45.6,
        timestamp=datetime.now(timezone.utc),
        files_compiled=12,
        total_warnings=3,
        total_errors=0
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
        last_used=datetime.now(timezone.utc),
        source_tree=generate_example_source_tree("my-app"),
        include_paths=[
            IncludePath(path="/usr/include", type=IncludePathType.SYSTEM, from_package=None),
            IncludePath(path="include", type=IncludePathType.USER, from_package=None)
        ],
        build_metrics=generate_example_build_metrics("my-app"),
        compiler_config={"CXX": "g++", "CXXFLAGS": "-O2 -Wall"}
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
        last_used=datetime.now(timezone.utc),
        source_tree=generate_example_source_tree("fmt"),
        include_paths=[
            IncludePath(path="/usr/include", type=IncludePathType.SYSTEM, from_package=None),
            IncludePath(path="include/fmt", type=IncludePathType.USER, from_package="fmt")
        ],
        build_metrics=generate_example_build_metrics("fmt"),
        compiler_config={"CXX": "g++", "CXXFLAGS": "-O2"}
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
        last_used=datetime.now(timezone.utc),
        source_tree=generate_example_source_tree("spdlog"),
        include_paths=[
            IncludePath(path="/usr/include", type=IncludePathType.SYSTEM, from_package=None),
            IncludePath(path="include/spdlog", type=IncludePathType.USER, from_package="spdlog"),
            IncludePath(path="fmt/include", type=IncludePathType.DEPENDENCY, from_package="fmt")
        ],
        build_metrics=generate_example_build_metrics("spdlog"),
        compiler_config={"CXX": "g++", "CXXFLAGS": "-O2 -DSPDLOG_FMT_EXTERNAL"}
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
        last_used=datetime.now(timezone.utc),
        source_tree=generate_example_source_tree("catch2"),
        include_paths=[
            IncludePath(path="/usr/include", type=IncludePathType.SYSTEM, from_package=None),
            IncludePath(path="include", type=IncludePathType.USER, from_package=None)
        ],
        build_metrics=generate_example_build_metrics("catch2"),
        compiler_config={"CXX": "g++", "CXXFLAGS": "-O2"}
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
        # Get the latest build data
        build_files = glob.glob(str(BUILD_DATA_DIR / "build_*.json"))
        if not build_files:
            return GraphLayout(nodes=[], edges=[], warnings=[])
            
        # Sort by modification time to get latest
        latest_build = max(build_files, key=os.path.getmtime)
        with open(latest_build) as f:
            build_data = json.load(f)
            
        # Transform build data into graph nodes and edges
        nodes: List[DependencyNode] = []
        edges: List[DependencyEdge] = []
        warnings: List[DependencyWarning] = []
        
        # Add root package node
        root_pkg = build_data["package"]["name"]
        nodes.append(DependencyNode(
            id=root_pkg,
            name=root_pkg,
            version=build_data["package"]["version"],
            is_dev_dep=False,
            has_warnings=False,
            size=0,  # TODO: Calculate actual size
            direct_deps=list(build_data.get("dependencies", {}).keys()),
            all_deps=list(build_data.get("dependency_graph", {}).get(root_pkg, [])),
            position=Position(x=0.0, y=0.0),
            last_used=datetime.now(timezone.utc),
            source_tree=generate_example_source_tree(root_pkg),  # TODO: Generate real source tree
            include_paths=[
                IncludePath(path=path, type=IncludePathType.USER, from_package=None)
                for path in build_data.get("include_paths", [])
            ],
            build_metrics=generate_example_build_metrics(root_pkg),  # TODO: Generate real metrics
            compiler_config=build_data.get("compiler_info", {})
        ))
        
        # Add dependency nodes
        y_level = 1
        for pkg_name, deps in build_data.get("dependency_graph", {}).items():
            if pkg_name == root_pkg:
                continue
                
            # Add node
            x_pos = (len(nodes) % 3 - 1) * 1.0  # Spread nodes horizontally
            nodes.append(DependencyNode(
                id=pkg_name,
                name=pkg_name,
                version=build_data["dependencies"].get(pkg_name, "unknown"),
                is_dev_dep=False,  # TODO: Determine if dev dep
                has_warnings=False,
                size=0,  # TODO: Calculate actual size
                direct_deps=deps,
                all_deps=deps,
                position=Position(x=x_pos, y=float(y_level)),
                last_used=datetime.now(timezone.utc),
                source_tree=generate_example_source_tree(pkg_name),  # TODO: Generate real source tree
                include_paths=[],  # TODO: Get actual include paths
                build_metrics=generate_example_build_metrics(pkg_name),  # TODO: Generate real metrics
                compiler_config={}  # TODO: Get actual compiler config
            ))
            
            # Add edges for direct dependencies
            for dep in deps:
                edges.append(DependencyEdge(
                    id=f"{pkg_name}-{dep}",
                    source=pkg_name,
                    target=dep,
                    is_circular=False  # TODO: Detect circular deps
                ))
                
            # Move to next level if we've added 3 nodes at current level
            if len(nodes) % 3 == 0:
                y_level += 1
        
        return GraphLayout(
            nodes=nodes,
            edges=edges,
            warnings=warnings
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

@app.get("/api/file-info/{file_path:path}")
async def get_file_info(file_path: str) -> SourceFile:
    try:
        # This is where you'll eventually integrate with your build system
        # For now, return mock data based on file type
        is_header = file_path.endswith(('.h', '.hpp', '.hxx'))
        now = datetime.now(timezone.utc)
        
        return SourceFile(
            path=file_path,
            type="header" if is_header else "source",
            size=1024,  # Mock size
            last_modified=now,  # Required field
            included_by=[
                'src/main.cpp',
                'src/other_file.cpp'
            ] if is_header else [],
            includes=[
                '<vector>',
                '<string>',
                '<memory>',
                '"my-project/config.h"',
                '"my-project/utils.h"',
                '"../include/local.h"'
            ],
            compiler_command=CompilerCommand(
                compiler="clang++",  # Required field
                source_file=file_path,  # Required field
                output_file=f"{file_path}.o",  # Required field
                command_line=f"clang++ -c {file_path}",
                duration_ms=0,
                cache_hit=False,
                cache_key="mock-key",  # Required field
                timestamp=now,  # Required field
                flags=['-Wall', '-Wextra', '-std=c++17'],
                include_paths=[
                    IncludePath(path='/usr/include', type=IncludePathType.SYSTEM),
                    IncludePath(path='include', type=IncludePathType.USER),
                    IncludePath(
                        path='deps/fmt/include',
                        type=IncludePathType.DEPENDENCY,
                        from_package='fmt'
                    )
                ],
                defines={
                    'DEBUG': '1',
                    'VERSION': '"1.0.0"'
                }
            ),
            warnings=[],
            object_size=None
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/builds", response_model=List[BuildData])
async def get_all_builds() -> List[BuildData]:
    """Get all build data."""
    try:
        build_files = glob.glob(str(BUILD_DATA_DIR / "build_*.json"))
        builds = []
        for file in build_files:
            with open(file) as f:
                data = json.load(f)
                # Transform the data to match BuildData model
                build_data = {
                    "package_name": data["package"]["name"],
                    "package_version": data["package"]["version"],
                    "start_time": data["timing"]["start"],
                    "end_time": data["timing"]["end"] if "end" in data["timing"] else None,
                    "compiler_info": {
                        "name": data["compiler"]["name"],
                        "version": data["compiler"]["version"],
                        "target": data["compiler"]["target"]
                    },
                    "compilation_steps": [
                        {
                            "source_file": step["source"],
                            "object_file": step["object"],
                            "command": step["command"].split() if step["command"] else [],
                            "include_paths": step["include_paths"],
                            "start_time": step["timing"]["start"],
                            "end_time": step["timing"]["end"] if "end" in step["timing"] else None,
                            "success": step["success"],
                            "error": step["error"]
                        }
                        for step in data["compilation_steps"]
                    ],
                    "dependencies": data.get("dependencies", {}),
                    "dependency_graph": data.get("dependency_graph", {}),
                    "include_paths": data.get("include_paths", []),
                    "library_paths": data.get("library_paths", []),
                    "success": all(step["success"] for step in data["compilation_steps"]),
                    "error": None  # We'll add error handling later if needed
                }
                builds.append(BuildData(**build_data))
        return sorted(builds, key=lambda x: x.start_time, reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/builds/{package_name}", response_model=List[BuildData])
async def get_package_builds(package_name: str) -> List[BuildData]:
    """Get all builds for a specific package."""
    try:
        build_files = glob.glob(str(BUILD_DATA_DIR / f"build_{package_name}_*.json"))
        builds = []
        for file in build_files:
            with open(file) as f:
                data = json.load(f)
                # Transform the data to match BuildData model
                build_data = {
                    "package_name": data["package"]["name"],
                    "package_version": data["package"]["version"],
                    "start_time": data["timing"]["start"],
                    "end_time": data["timing"]["end"] if "end" in data["timing"] else None,
                    "compiler_info": {
                        "name": data["compiler"]["name"],
                        "version": data["compiler"]["version"],
                        "target": data["compiler"]["target"]
                    },
                    "compilation_steps": [
                        {
                            "source_file": step["source"],
                            "object_file": step["object"],
                            "command": step["command"].split() if step["command"] else [],
                            "include_paths": step["include_paths"],
                            "start_time": step["timing"]["start"],
                            "end_time": step["timing"]["end"] if "end" in step["timing"] else None,
                            "success": step["success"],
                            "error": step["error"]
                        }
                        for step in data["compilation_steps"]
                    ],
                    "dependencies": data.get("dependencies", {}),
                    "dependency_graph": data.get("dependency_graph", {}),
                    "include_paths": data.get("include_paths", []),
                    "library_paths": data.get("library_paths", []),
                    "success": all(step["success"] for step in data["compilation_steps"]),
                    "error": None  # We'll add error handling later if needed
                }
                builds.append(BuildData(**build_data))
        return sorted(builds, key=lambda x: x.start_time, reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/builds/{package_name}/latest", response_model=BuildData)
async def get_latest_package_build(package_name: str) -> BuildData:
    """Get the latest build for a specific package."""
    try:
        builds = await get_package_builds(package_name)
        if not builds:
            raise HTTPException(status_code=404, detail=f"No builds found for package {package_name}")
        return builds[0]  # Already sorted by start_time
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve frontend in production
frontend_path = Path(__file__).parent / "frontend" / "dist"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True)) 