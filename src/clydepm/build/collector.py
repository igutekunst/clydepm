from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json
import time

from .hooks import BuildContext, BuildStage
from ..core.package import Package

@dataclass
class CompilationStep:
    """Records a single compilation step."""
    source_file: str
    object_file: str
    command: List[str]
    include_paths: List[str]
    start_time: float
    end_time: float = 0.0
    success: bool = False
    error: Optional[str] = None

@dataclass
class BuildData:
    """Collects data for a single build."""
    package_name: str
    package_version: str
    start_time: float
    compiler_info: Dict[str, str]
    compilation_steps: List[CompilationStep] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    end_time: float = 0.0
    success: bool = False
    error: Optional[str] = None

    def to_json(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "package": {
                "name": self.package_name,
                "version": self.package_version
            },
            "timing": {
                "start": datetime.fromtimestamp(self.start_time).isoformat(),
                "end": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
                "duration": self.end_time - self.start_time if self.end_time else None
            },
            "compiler": self.compiler_info,
            "compilation_steps": [
                {
                    "source": step.source_file,
                    "object": step.object_file,
                    "command": step.command,
                    "include_paths": step.include_paths,
                    "timing": {
                        "start": datetime.fromtimestamp(step.start_time).isoformat(),
                        "end": datetime.fromtimestamp(step.end_time).isoformat() if step.end_time else None,
                        "duration": step.end_time - step.start_time if step.end_time else None
                    },
                    "success": step.success,
                    "error": step.error
                }
                for step in self.compilation_steps
            ],
            "dependencies": self.dependencies,
            "success": self.success,
            "error": self.error
        }

class BuildDataCollector:
    """Collects build data using Builder hooks."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.current_build: Optional[BuildData] = None
        self.current_step: Optional[CompilationStep] = None
        
    def register_hooks(self, builder) -> None:
        """Register all hooks with the builder."""
        builder.add_hook(BuildStage.PRE_BUILD, self._on_build_start)
        builder.add_hook(BuildStage.PRE_COMPILE, self._on_compile_start)
        builder.add_hook(BuildStage.POST_COMPILE, self._on_compile_end)
        builder.add_hook(BuildStage.POST_DEPENDENCY_BUILD, self._on_dependencies_built)
        builder.add_hook(BuildStage.POST_BUILD, self._on_build_end)
        
    def _on_build_start(self, context: BuildContext) -> None:
        """Called when build starts."""
        self.current_build = BuildData(
            package_name=context.package.name,
            package_version=str(context.package.version),
            start_time=time.time(),
            compiler_info={
                "name": context.build_metadata.compiler_info.name,
                "version": context.build_metadata.compiler_info.version,
                "target": context.build_metadata.compiler_info.target
            }
        )
        
    def _on_compile_start(self, context: BuildContext) -> None:
        """Called before each compilation step."""
        if not context.source_file or not context.object_file:
            return
            
        self.current_step = CompilationStep(
            source_file=str(context.source_file),
            object_file=str(context.object_file),
            command=context.command,
            include_paths=[str(p) for p in context.build_metadata.includes],
            start_time=time.time()
        )
        
    def _on_compile_end(self, context: BuildContext) -> None:
        """Called after each compilation step."""
        if not self.current_step:
            return
            
        self.current_step.end_time = time.time()
        self.current_step.success = True
        if self.current_build:
            self.current_build.compilation_steps.append(self.current_step)
        self.current_step = None
        
    def _on_dependencies_built(self, context: BuildContext) -> None:
        """Called after dependencies are built."""
        if not self.current_build:
            return
            
        self.current_build.dependencies = {
            dep.name: str(dep.version)
            for dep in context.package.get_all_dependencies()
        }
        
    def _on_build_end(self, context: BuildContext) -> None:
        """Called when build ends."""
        if not self.current_build:
            return
            
        self.current_build.end_time = time.time()
        self.current_build.success = True
        
        # Save build data
        build_file = self.output_dir / f"build_{context.package.name}_{int(time.time())}.json"
        with open(build_file, 'w') as f:
            json.dump(self.current_build.to_json(), f, indent=2)
            
        self.current_build = None 