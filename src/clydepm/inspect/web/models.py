"""
API models for the build inspector web interface.
"""
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel

class Position(BaseModel):
    """Node position in the graph."""
    x: float
    y: float

class IncludePathType(str, Enum):
    SYSTEM = "system"
    PUBLIC = "public"
    PRIVATE = "private"
    DEPENDENCY = "dependency"

class IncludePath(BaseModel):
    """An include path used during compilation"""
    path: str
    type: IncludePathType
    from_package: Optional[str]

class CompilerCommand(BaseModel):
    """Compilation command for a source file"""
    compiler: str
    source_file: str
    output_file: str
    command_line: str
    flags: List[str]
    include_paths: List[IncludePath]
    defines: Dict[str, Optional[str]]
    timestamp: datetime
    duration_ms: float
    cache_hit: bool
    cache_key: str

class BuildWarning(BaseModel):
    """A compiler warning"""
    file: str
    line: int
    column: int
    message: str
    level: str
    flag: Optional[str]

class SourceFile(BaseModel):
    """A source or header file in the package"""
    path: str
    type: str
    size: int
    last_modified: datetime
    compiler_command: Optional[CompilerCommand]
    included_by: List[str]
    includes: List[str]
    warnings: List[BuildWarning]
    object_size: Optional[int]

class SourceTree(BaseModel):
    """Tree structure of source files"""
    name: str
    path: str
    type: str
    children: Optional[List['SourceTree']]
    file_info: Optional[SourceFile]

class BuildMetrics(BaseModel):
    """Build metrics data."""
    total_time: float
    cache_hits: int
    cache_misses: int
    artifact_sizes: Dict[str, int]
    memory_usage: float
    cpu_usage: float
    timestamp: datetime
    files_compiled: int
    total_warnings: int
    total_errors: int

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
    source_tree: SourceTree
    include_paths: List[IncludePath]
    build_metrics: BuildMetrics
    compiler_config: Dict[str, str]

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

class GraphLayout(BaseModel):
    """Graph layout data."""
    nodes: List[DependencyNode]
    edges: List[DependencyEdge]
    warnings: List[DependencyWarning] 