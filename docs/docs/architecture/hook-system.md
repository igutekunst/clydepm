# Hook System Architecture

This document describes both the current hook system and its planned evolution to support the build system refactor.

## Current Implementation

The current hook system is centered around build stages and provides a simple but effective way to extend the build process.

### Build Stages

```python
class BuildStage(Enum):
    """Build stages for hooks."""
    PRE_BUILD = auto()
    PRE_COMPILE = auto()
    POST_COMPILE = auto()
    PRE_LINK = auto()
    POST_LINK = auto()
    POST_DEPENDENCY_BUILD = auto()
    POST_BUILD = auto()
```

### Context Object

The `BuildContext` provides hook implementations with access to the current build state:

```python
class BuildContext:
    """Context passed to build hooks."""
    package: Package              # Current package being built
    build_metadata: BuildMetadata # Build configuration
    traits: Dict[str, str]       # Build traits
    verbose: bool                # Verbose output flag
    source_file: Optional[Path]  # Current source file (for compilation)
    object_file: Optional[Path]  # Output object file
    output_file: Optional[Path]  # Final output file
    command: Optional[List[str]] # Current build command
```

### Hook Management

Hooks are managed by the `BuildHookManager`:

```python
class BuildHookManager:
    """Manages build hooks."""
    hooks: Dict[BuildStage, List[Callable[[BuildContext], None]]]
    
    def add_hook(self, stage: BuildStage, 
                 hook: Callable[[BuildContext], None]) -> None:
        """Add a hook for a build stage."""
        
    def run_hooks(self, stage: BuildStage, 
                  context: BuildContext) -> None:
        """Run all hooks for a build stage."""
```

## Planned Evolution

The hook system will evolve to support the new phase-based architecture while maintaining backward compatibility.

### Phase-Based Hooks

Each phase will have its own context type and hooks:

```python
class ResolutionContext:
    """Context for dependency resolution phase."""
    requirement: PackageRequirement
    registry: Registry
    cache: PackageCache
    resolved_packages: Dict[str, Package]

class BuildPlanContext:
    """Context for build planning phase."""
    package: Package
    dependencies: List[Package]
    build_order: List[Package]
    artifact_mapping: Dict[Package, Path]

class BuildExecutionContext:
    """Context for build execution phase."""
    plan: BuildPlan
    current_package: Package
    artifacts: Dict[str, BuildArtifact]
    metrics: BuildMetrics
```

### Hook Points

1. **Resolution Phase**
   ```python
   class ResolutionHook(Enum):
       PRE_RESOLUTION = auto()
       PACKAGE_DISCOVERY = auto()
       VERSION_RESOLUTION = auto()
       PACKAGE_DOWNLOAD = auto()
       DEPENDENCY_RESOLUTION = auto()
       POST_RESOLUTION = auto()
   ```

2. **Build Planning Phase**
   ```python
   class PlanningHook(Enum):
       PRE_PLANNING = auto()
       DEPENDENCY_ANALYSIS = auto()
       BUILD_ORDER_COMPUTATION = auto()
       RESOURCE_ALLOCATION = auto()
       POST_PLANNING = auto()
   ```

3. **Build Execution Phase**
   ```python
   class ExecutionHook(Enum):
       PRE_BUILD = auto()
       PRE_COMPILE = auto()
       POST_COMPILE = auto()
       PRE_LINK = auto()
       POST_LINK = auto()
       POST_BUILD = auto()
   ```

### Enhanced Hook Manager

```python
class HookManager:
    """Manages hooks for all phases."""
    
    def add_resolution_hook(self, point: ResolutionHook,
                          hook: Callable[[ResolutionContext], None]):
        """Add a hook for the resolution phase."""
        
    def add_planning_hook(self, point: PlanningHook,
                         hook: Callable[[BuildPlanContext], None]):
        """Add a hook for the planning phase."""
        
    def add_execution_hook(self, point: ExecutionHook,
                          hook: Callable[[BuildExecutionContext], None]):
        """Add a hook for the execution phase."""
```

### Hook Registration

Hooks can be registered through a decorator syntax:

```python
@hooks.on(ResolutionHook.PACKAGE_DOWNLOAD)
def log_download(context: ResolutionContext):
    """Log package downloads."""
    logger.info(f"Downloading {context.requirement.name}")

@hooks.on(PlanningHook.BUILD_ORDER_COMPUTATION)
def validate_order(context: BuildPlanContext):
    """Validate build order."""
    check_circular_dependencies(context.build_order)

@hooks.on(ExecutionHook.POST_COMPILE)
def collect_metrics(context: BuildExecutionContext):
    """Collect compilation metrics."""
    update_metrics(context.metrics)
```

### Error Handling

Hooks include improved error handling and recovery:

```python
class HookError(Exception):
    """Base class for hook errors."""
    phase: str
    hook_point: str
    context: Any
    recoverable: bool

class HookManager:
    def handle_error(self, error: HookError) -> bool:
        """Handle a hook error.
        
        Returns:
            bool: Whether the error was handled and execution can continue
        """
```

### Instrumentation Support

The new hook system provides better support for build instrumentation:

1. **Metric Collection**
   ```python
   @hooks.metrics(ExecutionHook.PRE_COMPILE)
   def track_compilation(context: BuildExecutionContext):
       """Track compilation metrics."""
       start_timer(context.current_package)
   ```

2. **Build Graphs**
   ```python
   @hooks.graph(PlanningHook.DEPENDENCY_ANALYSIS)
   def update_graph(context: BuildPlanContext):
       """Update dependency graph."""
       add_dependencies_to_graph(context.dependencies)
   ```

3. **Resource Monitoring**
   ```python
   @hooks.monitor(ExecutionHook.PRE_BUILD)
   def monitor_resources(context: BuildExecutionContext):
       """Monitor system resources."""
       track_memory_usage(context.metrics)
   ```

### Using Hooks with Classes

Hooks can be integrated with classes in several ways:

1. **Class-Based Hook Implementation**
```python
class BuildMetricsCollector:
    """Collects build metrics using hooks."""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    @hooks.on(ExecutionHook.PRE_COMPILE)
    def on_compile_start(self, context: BuildExecutionContext):
        """Record compilation start time."""
        package = context.current_package
        self.start_times[package.name] = time.time()
        
    @hooks.on(ExecutionHook.POST_COMPILE)
    def on_compile_end(self, context: BuildExecutionContext):
        """Calculate compilation duration."""
        package = context.current_package
        start_time = self.start_times.pop(package.name)
        duration = time.time() - start_time
        self.metrics[package.name] = {
            'duration': duration,
            'success': context.artifacts.get(package.name) is not None
        }
```

2. **Hook Factory Methods**
```python
class BuildLogger:
    """Logging utility that creates hook functions."""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        
    def create_hooks(self) -> List[Tuple[Any, Callable]]:
        """Create and return all hooks for this logger."""
        return [
            (ResolutionHook.PACKAGE_DOWNLOAD, self.log_download),
            (ExecutionHook.PRE_BUILD, self.log_build_start),
            (ExecutionHook.POST_BUILD, self.log_build_end)
        ]
        
    def log_download(self, context: ResolutionContext):
        """Log package download events."""
        self._log(f"Downloading {context.requirement.name}")
        
    def log_build_start(self, context: BuildExecutionContext):
        """Log build start events."""
        self._log(f"Starting build of {context.current_package.name}")
        
    def log_build_end(self, context: BuildExecutionContext):
        """Log build completion events."""
        self._log(f"Completed build of {context.current_package.name}")
        
    def _log(self, message: str):
        """Write a log message."""
        with open(self.log_file, 'a') as f:
            f.write(f"{time.time()}: {message}\n")
```

3. **Hook Manager Integration**
```python
class CustomBuildSystem:
    """Example of a custom build system using hooks."""
    
    def __init__(self):
        self.hook_manager = HookManager()
        self.metrics = BuildMetricsCollector()
        self.logger = BuildLogger(Path("build.log"))
        
    def setup_hooks(self):
        """Register all hooks."""
        # Register metrics collector hooks
        self.hook_manager.add_execution_hook(
            ExecutionHook.PRE_COMPILE,
            self.metrics.on_compile_start
        )
        self.hook_manager.add_execution_hook(
            ExecutionHook.POST_COMPILE,
            self.metrics.on_compile_end
        )
        
        # Register logger hooks
        for hook_point, handler in self.logger.create_hooks():
            if isinstance(hook_point, ResolutionHook):
                self.hook_manager.add_resolution_hook(hook_point, handler)
            elif isinstance(hook_point, ExecutionHook):
                self.hook_manager.add_execution_hook(hook_point, handler)
    
    def build(self, package: Package):
        """Execute build with hooks."""
        self.setup_hooks()
        # Build implementation...
```

4. **Inheritance-Based Hooks**
```python
class BaseBuilder:
    """Base class with hook support."""
    
    def __init__(self):
        self.hook_manager = HookManager()
        self._register_hooks()
    
    def _register_hooks(self):
        """Register hooks from method names."""
        for name in dir(self):
            if name.startswith('on_'):
                attr = getattr(self, name)
                if hasattr(attr, '_hook_point'):
                    self.hook_manager.add_execution_hook(
                        attr._hook_point, attr
                    )

class CustomBuilder(BaseBuilder):
    """Custom builder implementation."""
    
    @hooks.on(ExecutionHook.PRE_BUILD)
    def on_build_start(self, context: BuildExecutionContext):
        """Handle build start."""
        self.prepare_build_directory(context)
    
    @hooks.on(ExecutionHook.POST_BUILD)
    def on_build_complete(self, context: BuildExecutionContext):
        """Handle build completion."""
        self.cleanup_build_directory(context)
```

These patterns demonstrate different ways to organize hooks within classes:

- **Class-Based Hook Implementation**: Encapsulates related hooks and their shared state
- **Hook Factory Methods**: Creates hooks dynamically based on configuration
- **Hook Manager Integration**: Coordinates multiple hook providers
- **Inheritance-Based** for reusable hook infrastructure

Choose the pattern that best fits your use case:

- Use **Class-Based** when hooks share state or resources
- Use **Factory Methods** when hooks need runtime configuration
- Use **Hook Manager Integration** for complex systems with multiple hook sources
- Use **Inheritance-Based** for reusable hook infrastructure

## Migration Strategy

1. **Phase 1: Add New Context Types**
   - Introduce new context classes
   - Keep backward compatibility with BuildContext

2. **Phase 2: Add Phase-Specific Hooks**
   - Implement new hook points
   - Map old hooks to new system

3. **Phase 3: Enhanced Features**
   - Add instrumentation support
   - Improve error handling
   - Add resource monitoring

4. **Phase 4: Documentation and Examples**
   - Update hook documentation
   - Provide migration examples
   - Create hook templates 