"""
API models for the build inspector web interface.
"""
from datetime import datetime
from typing import List, Optional, Dict, Literal, Union
from enum import Enum
from pydantic import BaseModel, Field

class Position(BaseModel):
    """Node position in the graph."""
    x: float
    y: float

class IncludePathType(str, Enum):
    """Types of include paths"""
    SYSTEM = "system"
    USER = "user"
    DEPENDENCY = "dependency"

class IncludePath(BaseModel):
    """An include path used during compilation"""
    path: str
    type: Literal["system", "user", "dependency"]
    from_package: Optional[str] = None

class CompilerCommand(BaseModel):
    """Compilation command for a source file"""
    compiler: str
    source_file: str
    output_file: str
    command_line: str
    flags: List[str]
    include_paths: List[IncludePath]
    defines: Optional[Dict[str, Optional[str]]] = None
    timestamp: datetime
    duration_ms: float
    cache_hit: bool
    cache_key: str

class BuildWarning(BaseModel):
    """A compiler warning"""
    location: str
    message: str

class SourceFile(BaseModel):
    """A source or header file in the package"""
    path: str
    type: Literal["source", "header"]
    size: int
    last_modified: datetime
    compiler_command: Optional[CompilerCommand] = None
    warnings: Optional[List[BuildWarning]] = None
    included_by: Optional[List[str]] = None
    includes: Optional[List[str]] = None
    object_size: Optional[int] = None

class SourceTree(BaseModel):
    """Tree structure of source files"""
    name: str
    path: str
    type: Literal["directory", "source", "header"]
    children: List["SourceTree"] = Field(default_factory=list)
    file_info: Optional[SourceFile] = None

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

# New Package-related models
class PackageIdentifier(BaseModel):
    """Unique identifier for a package, including organization if present."""
    name: str
    organization: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Get the full package name including organization."""
        return f"@{self.organization}/{self.name}" if self.organization else self.name

class DependencyRequirement(BaseModel):
    """A dependency requirement with version constraint."""
    package: PackageIdentifier
    version_constraint: str  # e.g. "^1.0.0"
    type: Literal["runtime", "dev"] = "runtime"

class Package(BaseModel):
    """Package information."""
    identifier: PackageIdentifier
    current_version: str
    available_versions: List[str]
    description: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    dependencies: List[DependencyRequirement] = Field(default_factory=list)
    dev_dependencies: List[DependencyRequirement] = Field(default_factory=list)

class ResolvedDependency(BaseModel):
    """A resolved dependency with exact version."""
    package: PackageIdentifier
    version: str
    type: Literal["runtime", "dev"]
    source_tree: Optional[SourceTree] = None
    include_paths: List[IncludePath] = Field(default_factory=list)
    resolved_dependencies: List["ResolvedDependency"] = Field(default_factory=list)

# Updated Build-related models
class CompilationStep(BaseModel):
    """Records a single compilation step."""
    source_file: str
    object_file: str
    command: List[str]
    include_paths: List[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    error: Optional[str] = None
    metrics: Optional[BuildMetrics] = None

class BuildStatus(str, Enum):
    """Build status."""
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"

class BuildData(BaseModel):
    """Collects data for a single build."""
    id: str = Field(description="Unique build identifier")
    package: PackageIdentifier
    version: str
    timestamp: datetime
    status: BuildStatus
    compiler_info: Dict[str, str]
    resolved_dependencies: List[ResolvedDependency] = Field(default_factory=list)
    compilation_steps: List[CompilationStep] = Field(default_factory=list)
    include_paths: List[str] = Field(default_factory=list)
    library_paths: List[str] = Field(default_factory=list)
    metrics: Optional[BuildMetrics] = None
    error: Optional[str] = None

# Graph visualization models
class DependencyGraphNode(BaseModel):
    """A node in the dependency graph visualization."""
    id: str  # ${packageName}@${version}
    package: PackageIdentifier
    version: str
    type: Literal["runtime", "dev"]
    position: Position
    metrics: Optional[BuildMetrics] = None
    has_warnings: bool = False

class DependencyGraphEdge(BaseModel):
    """An edge in the dependency graph visualization."""
    id: str
    source: str  # Node ID
    target: str  # Node ID
    type: Literal["runtime", "dev"]
    is_circular: bool = False

class DependencyWarning(BaseModel):
    """A warning about a dependency."""
    id: str
    package: PackageIdentifier
    message: str
    level: Literal["info", "warning", "error"]
    context: Dict[str, str]

class GraphLayout(BaseModel):
    """Graph layout data."""
    nodes: List[DependencyGraphNode]
    edges: List[DependencyGraphEdge]
    warnings: List[DependencyWarning] 