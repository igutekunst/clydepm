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
import uuid

from .models import (
    BuildData,
    BuildMetrics,
    BuildStatus,
    CompilationStep,
    DependencyGraphNode,
    DependencyGraphEdge,
    DependencyWarning,
    GraphLayout,
    IncludePath,
    IncludePathType,
    Package,
    PackageIdentifier,
    Position,
    ResolvedDependency,
    SourceFile,
    SourceTree,
    DependencyGraph,
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
        "http://127.0.0.1:5173",  # Alternative localhost
        "http://localhost:5174",  # Additional Vite port
        "http://127.0.0.1:5174"   # Alternative localhost for 5174
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build data directory
BUILD_DATA_DIR = Path.home() / ".clydepm" / "build_data"

def parse_package_identifier(name: str) -> PackageIdentifier:
    """Parse a package name into a PackageIdentifier."""
    if name.startswith("@"):
        org, pkg = name.split("/", 1)
        return PackageIdentifier(name=pkg, organization=org[1:])
    return PackageIdentifier(name=name)

def generate_source_tree(name: str, build_data: dict) -> SourceTree:
    """Generate a source tree from build data."""
    root = SourceTree(
        name=name,
        path=f"src/{name}",
        type="directory"
    )
    
    # Add source files from compilation steps
    source_files = set()
    for step in build_data.get("compilation_steps", []):
        source_files.add(step["source"])
        if "object" in step:
            source_files.add(step["object"])
            
    if source_files:
        src_dir = SourceTree(
            name="src",
            path=f"src/{name}/src",
            type="directory",
            children=[
                SourceTree(
                    name=path.split("/")[-1],
                    path=path,
                    type="header" if path.endswith((".h", ".hpp")) else "source"
                )
                for path in sorted(source_files)
            ]
        )
        root.children.append(src_dir)
        
    return root

def generate_build_metrics(build_data: dict) -> BuildMetrics:
    """Generate build metrics from build data."""
    steps = build_data.get("compilation_steps", [])
    total_time = 0
    cache_hits = 0
    cache_misses = 0
    
    for step in steps:
        if "timing" in step:
            start = datetime.fromisoformat(step["timing"]["start"])
            if "end" in step["timing"]:
                end = datetime.fromisoformat(step["timing"]["end"])
                total_time += (end - start).total_seconds()
        if step.get("cache_hit"):
            cache_hits += 1
        else:
            cache_misses += 1
            
    return BuildMetrics(
        total_time=total_time,
        cache_hits=cache_hits,
        cache_misses=cache_misses,
        artifact_sizes={},  # TODO: Calculate actual sizes
        memory_usage=0,     # TODO: Track memory usage
        cpu_usage=0,        # TODO: Track CPU usage
        timestamp=datetime.now(timezone.utc),
        files_compiled=len(steps),
        total_warnings=0,   # TODO: Count warnings
        total_errors=0      # TODO: Count errors
    )

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
            "initial": 0.6,
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

@app.get("/api/packages", response_model=List[Package])
async def get_all_packages() -> List[Package]:
    """Get all packages."""
    try:
        packages = {}  # Dict[str, Package]
        
        # Scan build files to find packages
        build_files = glob.glob(str(BUILD_DATA_DIR / "build_*.json"))
        for file in build_files:
            with open(file) as f:
                data = json.load(f)
                pkg_name = data["package"]["name"]
                pkg_version = data["package"]["version"]
                
                if pkg_name not in packages:
                    pkg_id = parse_package_identifier(pkg_name)
                    packages[pkg_name] = Package(
                        identifier=pkg_id,
                        current_version=pkg_version,
                        available_versions=[pkg_version]
                    )
                else:
                    if pkg_version not in packages[pkg_name].available_versions:
                        packages[pkg_name].available_versions.append(pkg_version)
                        # Update current version if newer
                        if pkg_version > packages[pkg_name].current_version:
                            packages[pkg_name].current_version = pkg_version
                            
        return list(packages.values())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/packages/{package_name}", response_model=Package)
async def get_package_details(package_name: str) -> Package:
    """Get package details."""
    try:
        # Find all builds for this package
        builds = await get_package_builds(package_name)
        if not builds:
            raise HTTPException(status_code=404, detail=f"Package {package_name} not found")
            
        # Get the latest build
        latest = builds[0]
        pkg_id = latest.package
        
        # Collect all versions
        versions = sorted(set(build.version for build in builds))
        
        return Package(
            identifier=pkg_id,
            current_version=latest.version,
            available_versions=versions
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dependencies", response_model=DependencyGraph)
async def get_dependency_graph(build_id: str) -> DependencyGraph:
    """Get the dependency graph data for a specific build."""
    try:
        # Find the build file
        build_file = BUILD_DATA_DIR / f"build_{build_id}.json"
        if not build_file.exists():
            raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
            
        with open(build_file) as f:
            build_data = json.load(f)
            
        nodes: List[DependencyGraphNode] = []
        edges: List[DependencyGraphEdge] = []
        warnings: List[DependencyWarning] = []
        
        # Add root package node
        root_pkg = parse_package_identifier(build_data["package"]["name"])
        root_version = build_data["package"]["version"]
        root_id = f"{root_pkg.full_name}@{root_version}"
        
        # Get metrics for the root package
        metrics = build_data.get("metrics")
        
        # Check if there was a build error
        error_message = build_data.get("error")
        has_error = bool(error_message)
        
        nodes.append(DependencyGraphNode(
            id=root_id,
            package=root_pkg,
            name=root_pkg.name,
            version=root_version,
            type="runtime",
            position=Position(x=0.0, y=0.0),
            metrics=metrics,
            has_warnings=has_error
        ))
        
        if has_error:
            warnings.append(DependencyWarning(
                id=f"error-{root_id}",
                package=root_pkg,
                message=error_message or "Unknown build error",
                level="error",
                context={
                    "package": root_pkg.full_name,
                    "version": root_version,
                    "type": "build_error"
                }
            ))
            
        # Add dependency nodes from dependency_graph if available
        y_level = 1
        processed = {root_id}
        
        # Get dependencies from the dependency graph
        dependency_graph = build_data.get("dependency_graph", {})
        for pkg_name, deps in dependency_graph.items():
            if pkg_name == root_pkg.name:
                for dep_name in deps:
                    pkg_id = parse_package_identifier(dep_name)
                    node_id = f"{pkg_id.full_name}@unknown"
                    
                    if node_id not in processed:
                        processed.add(node_id)
                        x_pos = (len(nodes) % 3 - 1) * 1.0
                        
                        # Add the dependency node
                        nodes.append(DependencyGraphNode(
                            id=node_id,
                            package=pkg_id,
                            name=pkg_id.name,
                            version="unknown",
                            type="runtime",
                            position=Position(x=x_pos, y=float(y_level)),
                            metrics=None,
                            has_warnings=True
                        ))
                        
                        # Add edge from root to dependency
                        edges.append(DependencyGraphEdge(
                            id=f"{root_id}->{node_id}",
                            source=root_id,
                            target=node_id,
                            type="runtime",
                            is_circular=False
                        ))
                        
                        # Add warning for missing dependency
                        warnings.append(DependencyWarning(
                            id=f"missing-{node_id}",
                            package=pkg_id,
                            message=f"Missing dependency: {pkg_id.full_name}",
                            level="warning",
                            context={
                                "package": pkg_id.full_name,
                                "type": "missing_dependency"
                            }
                        ))
                        
        return DependencyGraph(nodes=nodes, edges=edges, warnings=warnings)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/builds", response_model=List[BuildData])
async def get_all_builds() -> List[BuildData]:
    """Get all build data."""
    try:
        build_files = glob.glob(str(BUILD_DATA_DIR / "build_*.json"))
        builds = []
        
        for file in build_files:
            with open(file) as f:
                data = json.load(f)
                
                # Get build ID from filename (e.g., "build_1234567890.json" -> "1234567890")
                build_id = Path(file).stem.split('_', 1)[1]
                
                # Parse timestamps
                start_time = datetime.fromisoformat(data["timing"]["start"])
                end_time = (datetime.fromisoformat(data["timing"]["end"])
                           if "end" in data["timing"] else None)
                
                # Determine build status
                if "end" not in data["timing"]:
                    status = BuildStatus.IN_PROGRESS
                else:
                    status = (BuildStatus.SUCCESS 
                             if all(step["success"] for step in data["compilation_steps"])
                             else BuildStatus.FAILURE)
                
                # Create build data
                build = BuildData(
                    id=build_id,  # Use consistent ID from filename
                    package=parse_package_identifier(data["package"]["name"]),
                    version=data["package"]["version"],
                    timestamp=start_time,
                    status=status,
                    compiler_info=data["compiler"],
                    include_paths=data.get("include_paths", []),
                    library_paths=data.get("library_paths", []),
                    metrics=generate_build_metrics(data),
                    error=data.get("error")  # Get error from build data
                )
                
                # Add compilation steps
                for step in data["compilation_steps"]:
                    build.compilation_steps.append(CompilationStep(
                        source_file=step["source"],
                        object_file=step["object"],
                        command=step["command"].split() if step["command"] else [],
                        include_paths=step["include_paths"],
                        start_time=datetime.fromisoformat(step["timing"]["start"]),
                        end_time=(datetime.fromisoformat(step["timing"]["end"])
                                if "end" in step["timing"] else None),
                        success=step["success"],
                        error=step.get("error")
                    ))
                
                # Add resolved dependencies
                for dep_name, dep_version in data.get("dependencies", {}).items():
                    dep_id = parse_package_identifier(dep_name)
                    build.resolved_dependencies.append(ResolvedDependency(
                        package=dep_id,
                        version=dep_version,
                        type="runtime",  # TODO: Detect dev dependencies
                        source_tree=generate_source_tree(dep_name, data)
                    ))
                
                builds.append(build)
                
        return sorted(builds, key=lambda x: x.timestamp, reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/builds/{package_name}", response_model=List[BuildData])
async def get_package_builds(package_name: str) -> List[BuildData]:
    """Get all builds for a specific package."""
    try:
        all_builds = await get_all_builds()
        package_builds = [
            build for build in all_builds
            if build.package and build.package.name == package_name
        ]
        
        if not package_builds:
            raise HTTPException(
                status_code=404,
                detail=f"No builds found for package {package_name}"
            )
            
        # Convert each build to match the response model
        return [BuildData(
            id=build.id,
            package=build.package,
            version=build.version,
            timestamp=build.timestamp,
            status=build.status,
            compiler_info=build.compiler_info,
            resolved_dependencies=build.resolved_dependencies,
            compilation_steps=build.compilation_steps,
            include_paths=build.include_paths,
            library_paths=build.library_paths,
            metrics=build.metrics,
            error=build.error
        ) for build in package_builds]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting builds for package {package_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get builds for package {package_name}: {str(e)}"
        )

@app.get("/api/builds/{package_name}/latest", response_model=BuildData)
async def get_latest_package_build(package_name: str) -> BuildData:
    """Get the latest build for a specific package."""
    try:
        # Get all builds for the package
        builds = await get_package_builds(package_name)
        
        if not builds:
            raise HTTPException(
                status_code=404,
                detail=f"No builds found for package {package_name}"
            )
            
        # Sort by timestamp and get the latest
        latest_build = max(builds, key=lambda b: b.timestamp)
        
        # Convert to response model
        return latest_build
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting latest build for package {package_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get latest build for package {package_name}: {str(e)}"
        )

# Serve frontend in production
frontend_path = Path(__file__).parent / "frontend" / "dist"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True)) 