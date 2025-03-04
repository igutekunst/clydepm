"""
Build system for Clydepm.
"""
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
import subprocess
import logging
import sys
import os
from dataclasses import dataclass
from enum import Enum, auto

from ..core.package import Package, PackageType, CompilerInfo, BuildMetadata
from .cache import BuildCache

logger = logging.getLogger(__name__)

# Set up build log file handler - only log to file by default
build_logger = logging.getLogger("build")
build_logger.setLevel(logging.DEBUG)  # Always log everything to file
build_logger.propagate = False  # Prevent propagation to root logger
build_file_handler = logging.FileHandler("build.log", mode='w')
build_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
build_logger.addHandler(build_file_handler)

class BuildStage(Enum):
    """Build stages for hooks."""
    PRE_BUILD = auto()
    POST_DEPENDENCY_BUILD = auto()
    PRE_COMPILE = auto()
    POST_COMPILE = auto()
    PRE_LINK = auto()
    POST_LINK = auto()
    POST_BUILD = auto()

@dataclass
class BuildContext:
    """Context passed to build hooks."""
    package: Package
    build_metadata: BuildMetadata
    traits: Dict[str, str]
    verbose: bool
    source_file: Optional[Path] = None  # For compile hooks
    object_file: Optional[Path] = None  # For compile hooks
    output_file: Optional[Path] = None  # For link hooks
    command: Optional[List[str]] = None  # For command hooks

@dataclass
class BuildResult:
    """Result of a build operation."""
    success: bool
    error: Optional[str] = None
    artifacts: Dict[str, Path] = None

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
        """Run all hooks for a build stage."""
        for hook in self.hooks[stage]:
            try:
                hook(context)
            except Exception as e:
                logger.error("Hook failed at stage %s: %s", stage, e)

class Builder:
    """Builds packages."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize builder.
        
        Args:
            cache_dir: Directory to store cache. Defaults to ~/.clydepm/cache
        """
        self.cache = BuildCache(cache_dir)
        self.hook_manager = BuildHookManager()
        
    def add_hook(self, stage: BuildStage, hook: Callable[[BuildContext], None]) -> None:
        """Add a build hook."""
        self.hook_manager.add_hook(stage, hook)
        
    def _get_compiler_info(self) -> CompilerInfo:
        """Get information about the current compiler."""
        try:
            # Get compiler version - use g++ for C++
            result = subprocess.run(
                ["g++", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            version = result.stdout.split("\n")[0].split()[-1]
            
            # Get compiler target
            result = subprocess.run(
                ["g++", "-dumpmachine"],
                capture_output=True,
                text=True,
                check=True
            )
            target = result.stdout.strip()
            
            return CompilerInfo(
                name="g++",
                version=version,
                target=target
            )
        except subprocess.CalledProcessError as e:
            logger.error("Failed to get compiler info: %s", e)
            return CompilerInfo(
                name="g++",
                version="unknown",
                target="unknown"
            )
            
    def _compile_source(
        self,
        source_path: Path,
        object_path: Path,
        package: Package,
        build_metadata: BuildMetadata,
        verbose: bool = False,
        traits: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Compile a source file to an object file.
        
        Args:
            source_path: Path to source file (absolute)
            object_path: Path to output object file (relative to build dir)
            package: Package being built
            build_metadata: Build metadata
            verbose: Whether to show verbose output
            traits: Optional build traits
        
        Returns:
            Error message if compilation failed, None if successful
        """
        # Create context for hooks
        context = BuildContext(
            package=package,
            build_metadata=build_metadata,
            traits=traits or {},
            verbose=verbose,
            source_file=source_path,
            object_file=object_path
        )
        
        # Run pre-compile hooks
        self.hook_manager.run_hooks(BuildStage.PRE_COMPILE, context)
        
        # Check if we have a cached object file
        if self.cache.has_cached_object(source_path, build_metadata):
            if self.cache.get_cached_object(source_path, build_metadata, object_path):
                logger.debug("[CACHE] Using cached object for %s", source_path)
                return None
                
        # Build command - use g++ for .cpp files
        compiler = "g++" if source_path.suffix in [".cpp", ".cc", ".cxx"] else "gcc"
        
        # Get relative paths from build directory
        rel_source = os.path.relpath(source_path)
        
        cmd = [compiler, "-c", "-o", str(object_path), rel_source]
        cmd.extend(build_metadata.cflags)
        
        # Add include paths, making them relative when possible
        for include_path in build_metadata.includes:
            try:
                # Only add the base include directory, not package-specific subdirs
                if include_path.name == "include":
                    rel_include = os.path.relpath(include_path)
                    cmd.extend(["-I", rel_include])
            except ValueError:
                # Path is on different drive/root, use absolute
                if include_path.name == "include":
                    cmd.extend(["-I", str(include_path)])
        
        # Update context with command
        context.command = cmd
        
        # Log the compilation command
        build_logger.debug("[COMPILE] %s", " ".join(cmd))
        
        if verbose:
            logger.info("Compiling %s -> %s", rel_source, object_path)
            logger.info("Command: %s", " ".join(cmd))
            
        # Run compilation
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Log compiler output if any
            if result.stdout:
                build_logger.debug("[COMPILER OUTPUT]\n%s", result.stdout)
            
            # Cache the successful compilation
            self.cache.cache_object(source_path, object_path, build_metadata)
            
            # Run post-compile hooks
            self.hook_manager.run_hooks(BuildStage.POST_COMPILE, context)
            
            return None
        except subprocess.CalledProcessError as e:
            error_msg = f"Compilation failed:\n{e.stderr}"
            build_logger.error("[COMPILE ERROR] %s", error_msg)
            return error_msg
            
    def _link_objects(
        self,
        objects: List[Path],
        output_path: Path,
        package: Package,
        build_metadata: BuildMetadata,
        verbose: bool = False,
        traits: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Link object files into final artifact.
        
        Args:
            objects: List of object files (relative to build dir)
            output_path: Output path (relative to build dir)
            package: Package being built
            build_metadata: Build metadata
            verbose: Whether to show verbose output
            traits: Optional build traits
        
        Returns:
            Error message if linking failed, None if successful
        """
        # Create context for hooks
        context = BuildContext(
            package=package,
            build_metadata=build_metadata,
            traits=traits or {},
            verbose=verbose,
            output_file=output_path
        )
        
        # Run pre-link hooks
        self.hook_manager.run_hooks(BuildStage.PRE_LINK, context)
        
        if package.package_type == PackageType.LIBRARY:
            # Create static library with ar
            cmd = ["ar", "rcs", str(output_path)]
            cmd.extend(str(obj) for obj in objects)
            
            # Update context with command
            context.command = cmd
            
            # Log the library creation command
            build_logger.debug("[ARCHIVE] %s", " ".join(cmd))
            
            if verbose:
                logger.info("Creating library %s", output_path)
                logger.info("Command: %s", " ".join(cmd))
                
            # Run ar
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Log archiver output if any
                if result.stdout:
                    build_logger.info("[ARCHIVER OUTPUT]\n%s", result.stdout)
                    
                # Run post-link hooks
                self.hook_manager.run_hooks(BuildStage.POST_LINK, context)
                    
                return None
            except subprocess.CalledProcessError as e:
                error_msg = f"Library creation failed:\n{e.stderr}"
                build_logger.error("[ARCHIVE ERROR] %s", error_msg)
                return error_msg
        else:
            # Build command - use g++ for linking C++ code
            cmd = ["g++", "-o", str(output_path)]
            cmd.extend(str(obj) for obj in objects)
            
            # Add library paths from build metadata, making them relative when possible
            for lib_path in build_metadata.libs:
                if isinstance(lib_path, Path) and lib_path.exists():
                    try:
                        rel_lib = os.path.relpath(lib_path)
                        cmd.extend(["-L", rel_lib])
                    except ValueError:
                        # Path is on different drive/root, use absolute
                        cmd.extend(["-L", str(lib_path)])
            
            # Add ldflags from build metadata
            cmd.extend(build_metadata.ldflags)
            
            # Update context with command
            context.command = cmd
            
            # Log the linking command
            build_logger.debug("[LINK] %s", " ".join(cmd))
            
            if verbose:
                logger.info("Linking %s", output_path)
                logger.info("Command: %s", " ".join(cmd))
                
            # Run linker
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Log linker output if any
                if result.stdout:
                    build_logger.debug("[LINKER OUTPUT]\n%s", result.stdout)
                    
                # Run post-link hooks
                self.hook_manager.run_hooks(BuildStage.POST_LINK, context)
                    
                return None
            except subprocess.CalledProcessError as e:
                error_msg = f"Linking failed:\n{e.stderr}"
                build_logger.error("[LINK ERROR] %s", error_msg)
                return error_msg

    def _build_dependencies(
        self,
        package: Package,
        traits: Optional[Dict[str, str]] = None,
        verbose: bool = False
    ) -> Optional[str]:
        """Build all dependencies of a package.
        
        Returns:
            Error message if any dependency build failed, None if all successful
        """
        # Build all dependencies (both local and remote)
        for dep in package.get_all_dependencies():
            build_logger.debug("[DEPENDENCY] Building %s %s", dep.name, dep.version)
            result = self.build(dep, traits, verbose)
            if not result.success:
                error_msg = f"Failed to build dependency {dep.name}: {result.error}"
                build_logger.error("[DEPENDENCY ERROR] %s", error_msg)
                return error_msg
        return None

    def build(
        self,
        package: Package,
        traits: Optional[Dict[str, str]] = None,
        verbose: bool = False
    ) -> BuildResult:
        """Build a package.
        
        Args:
            package: Package to build
            traits: Optional build traits
            verbose: Whether to show verbose output
            
        Returns:
            BuildResult indicating success/failure and artifacts
        """
        try:
            # Create build metadata
            compiler_info = self._get_compiler_info()
            build_metadata = package.create_build_metadata(compiler_info)
            
            # Add traits to build metadata
            if traits:
                build_metadata.traits.update(traits)
                
            # Create build directory
            build_dir = package.get_build_dir()
            try:
                build_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return BuildResult(
                    success=False,
                    error=f"Failed to create build directory at {build_dir}: {str(e)}"
                )
            
            # Change to build directory for all operations
            try:
                old_cwd = Path.cwd()
                os.chdir(build_dir)
            except Exception as e:
                return BuildResult(
                    success=False,
                    error=f"Failed to change to build directory {build_dir} from {old_cwd}: {str(e)}"
                )
                
            try:
                # Create context for hooks with paths relative to build dir
                context = BuildContext(
                    package=package,
                    build_metadata=build_metadata,
                    traits=traits or {},
                    verbose=verbose
                )
                
                # Run pre-build hooks
                self.hook_manager.run_hooks(BuildStage.PRE_BUILD, context)
                
                # Build dependencies first
                error = self._build_dependencies(package, traits, verbose)
                if error:
                    return BuildResult(success=False, error=error)
                    
                # Run post-dependency hooks
                self.hook_manager.run_hooks(BuildStage.POST_DEPENDENCY_BUILD, context)
                
                # Get source files and make paths relative to build dir
                sources = package.get_source_files()
                if not sources:
                    return BuildResult(
                        success=False,
                        error=f"No source files found in {os.path.relpath(package.path/'src')}"
                    )
                    
                # Compile each source file
                objects = []
                for source in sources:
                    # Use relative paths for object files
                    object_path = Path(f"{source.stem}.o")
                    error = self._compile_source(
                        source,
                        object_path,
                        package,
                        build_metadata,
                        verbose,
                        traits
                    )
                    if error:
                        return BuildResult(success=False, error=error)
                    objects.append(object_path)
                    
                # Link objects
                if package.package_type == PackageType.LIBRARY:
                    output_name = f"lib{package.name}.a"
                else:
                    output_name = package.name
                output_path = Path(output_name)
                
                error = self._link_objects(
                    objects,
                    output_path,
                    package,
                    build_metadata,
                    verbose,
                    traits
                )
                if error:
                    return BuildResult(success=False, error=error)
                    
                # Run post-build hooks
                self.hook_manager.run_hooks(BuildStage.POST_BUILD, context)
                    
                # Return success with artifacts (convert back to absolute paths)
                return BuildResult(
                    success=True,
                    artifacts={"output": build_dir / output_path}
                )
            except Exception as e:
                logger.error("Build failed: %s", e)
                return BuildResult(
                    success=False,
                    error=f"Build failed in directory {build_dir}: {str(e)}"
                )
            finally:
                # Always try to restore the original working directory
                try:
                    os.chdir(old_cwd)
                except Exception as e:
                    logger.error("Failed to restore working directory to %s: %s", old_cwd, e)
                
        except Exception as e:
            logger.error("Build failed: %s", e)
            return BuildResult(
                success=False,
                error=str(e)
            ) 