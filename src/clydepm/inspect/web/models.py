"""
API models for the build inspector web interface.
"""
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel

class Position(BaseModel):
    """Node position in the graph."""
    x: float
    y: float

class DependencyNode(BaseModel):
    """A node in the dependency graph."""
    id: str
    name: str
    version: str
    is_dev_dep: bool
    has_warnings: bool
    size: int
    direct_deps: List[str]
    all_deps: List[str]
    position: Position
    last_used: datetime

class DependencyEdge(BaseModel):
    """An edge in the dependency graph."""
    id: str
    source: str
    target: str
    is_circular: bool

class DependencyWarning(BaseModel):
    """A warning about a dependency."""
    id: str
    package: str
    message: str
    level: str
    context: Dict[str, str]

class BuildMetrics(BaseModel):
    """Build metrics data."""
    total_time: float
    cache_hits: int
    cache_misses: int
    artifact_sizes: Dict[str, int]
    memory_usage: float
    cpu_usage: float
    timestamp: datetime

class GraphLayout(BaseModel):
    """Graph layout data."""
    nodes: List[DependencyNode]
    edges: List[DependencyEdge]
    warnings: List[DependencyWarning] 