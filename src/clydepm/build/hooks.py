from enum import Enum, auto
from typing import Dict, List, Callable, Optional
from pathlib import Path
import logging

from ..core.package import Package, BuildMetadata

logger = logging.getLogger(__name__)

class BuildStage(Enum):
    """Build stages for hooks."""
    PRE_BUILD = auto()
    PRE_COMPILE = auto()
    POST_COMPILE = auto()
    PRE_LINK = auto()
    POST_LINK = auto()
    POST_DEPENDENCY_BUILD = auto()
    POST_BUILD = auto()
    
    def __str__(self) -> str:
        """Return a human-readable string."""
        return self.name.lower().replace('_', ' ')

class BuildContext:
    """Context passed to build hooks."""
    
    def __init__(
        self,
        package: Package,
        build_metadata: BuildMetadata,
        traits: Dict[str, str],
        verbose: bool,
        source_file: Optional[Path] = None,
        object_file: Optional[Path] = None,
        output_file: Optional[Path] = None,
        command: Optional[List[str]] = None
    ):
        self.package = package
        self.build_metadata = build_metadata
        self.traits = traits
        self.verbose = verbose
        self.source_file = source_file
        self.object_file = object_file
        self.output_file = output_file
        self.command = command

class BuildHookManager:
    """Manages build hooks."""
    
    def __init__(self):
        self.hooks: Dict[BuildStage, List[Callable[[BuildContext], None]]] = {
            stage: [] for stage in BuildStage
        }
        
    def add_hook(self, stage: BuildStage, hook: Callable[[BuildContext], None]) -> None:
        """Add a hook for a build stage."""
        self.hooks[stage].append(hook)
        
    def run_hooks(self, stage: BuildStage, context: BuildContext) -> None:
        """Run all hooks for a build stage.
        
        Args:
            stage: Build stage to run hooks for
            context: Build context to pass to hooks
            
        Raises:
            Exception: If any hook fails
        """
        for hook in self.hooks[stage]:
            try:
                hook(context)
            except Exception as e:
                # Log the full error for debugging
                logger.debug("Hook failed at %s stage: %s", stage, e)
                # Raise a cleaner error for user display
                raise Exception(f"Build failed during {str(stage)}") from e 