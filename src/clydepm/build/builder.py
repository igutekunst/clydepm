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
from ..github.registry import GitHubRegistry
from ..core.version.version import Version
from .cache import BuildCache
from .hooks import BuildHookManager, BuildStage, BuildContext
from .collector import BuildDataCollector

# Set up build log file handler
logger = logging.getLogger("build")
logger.setLevel(logging.DEBUG)  # Always log everything to file
logger.propagate = False  # Don't propagate to root logger

# File handler for build.log
file_handler = logging.FileHandler("build.log", mode='w')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

@dataclass
class BuildResult:
    """Result of a build operation."""
    success: bool
    error: Optional[str] = None
    artifacts: Dict[str, Path] = None

class Builder:
    """Builds packages."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize builder.
        
        Args:
            cache_dir: Directory to store cache. Defaults to ~/.clydepm/cache
        """
        self.cache = BuildCache(cache_dir)
        self.hook_manager = BuildHookManager()
        self.error_handler = None
        self._built_packages = set()  # Track packages that have been built
        
        # Initialize and register build data collector
        build_data_dir = cache_dir / "build_data" if cache_dir else Path.home() / ".clydepm" / "build_data"
        self.collector = BuildDataCollector(build_data_dir)
        self.collector.register_hooks(self)
        
    def add_hook(self, stage: BuildStage, hook: Callable[[BuildContext], None]) -> None:
        """Add a build hook."""
        self.hook_manager.add_hook(stage, hook)
        
    def set_error_handler(self, handler: Callable[[BuildContext, str], None]) -> None:
        """Set the error handler for build failures."""
        self.error_handler = handler
        
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
                # Always add include paths - they should already be properly namespaced
                rel_include = os.path.relpath(include_path)
                cmd.extend(["-I", rel_include])
            except ValueError:
                # Path is on different drive/root, use absolute
                cmd.extend(["-I", str(include_path)])
        
        # Update context with command
        context.command = cmd
        
        # Log the compilation command
        logger.debug("[COMPILE] %s", " ".join(cmd))
        
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
                logger.debug("[COMPILER OUTPUT]\n%s", result.stdout)
            
            # Cache the successful compilation
            self.cache.cache_object(source_path, object_path, build_metadata)
            
            # Run post-compile hooks
            self.hook_manager.run_hooks(BuildStage.POST_COMPILE, context)
            
            return None
        except subprocess.CalledProcessError as e:
            error_msg = f"Compilation failed:\n{e.stderr}"
            logger.error("[COMPILE ERROR] %s", error_msg)
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
            logger.debug("[ARCHIVE] %s", " ".join(cmd))
            
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
                    logger.info("[ARCHIVER OUTPUT]\n%s", result.stdout)
                    
                # Run post-link hooks
                self.hook_manager.run_hooks(BuildStage.POST_LINK, context)
                    
                return None
            except subprocess.CalledProcessError as e:
                error_msg = f"Library creation failed:\n{e.stderr}"
                logger.error("[ARCHIVE ERROR] %s", error_msg)
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
            logger.debug("[LINK] %s", " ".join(cmd))
            
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
                    logger.debug("[LINKER OUTPUT]\n%s", result.stdout)
                    
                # Run post-link hooks
                self.hook_manager.run_hooks(BuildStage.POST_LINK, context)
                    
                return None
            except subprocess.CalledProcessError as e:
                error_msg = f"Linking failed:\n{e.stderr}"
                logger.error("[LINK ERROR] %s", error_msg)
                return error_msg

    def _ensure_dependencies(
        self,
        package: Package,
        context: BuildContext
    ) -> Optional[str]:
        """Ensure all dependencies are installed.
        
        Returns:
            Error message if failed, None if successful
        """
        try:
            deps = package.get_dependencies()
            if not deps:
                return None
                
            logger.info("Checking dependencies...")
            
            # First check if deps directory exists
            deps_dir = package.path / "deps"
            deps_dir.mkdir(exist_ok=True)
            
            # Get GitHub token and organization
            from ..github.config import get_github_token, load_config
            token = get_github_token()
            if not token:
                return "No GitHub token configured. Run 'clyde auth' to set up GitHub authentication"
                
            # Create registries dict to cache registries by username/org
            registries = {}
            
            # Check each dependency
            for name, version_spec in deps.items():
                if not version_spec.startswith("local:"):
                    # For @org/pkg format, extract org and package name
                    if name.startswith('@'):
                        org = name.split('/')[0][1:]  # Remove @ from org
                        pkg_name = name.split('/')[1]
                    else:
                        # Use package's organization as fallback
                        org = package.organization
                        if not org:
                            config = load_config()
                            org = config.get("organization")
                        pkg_name = name
                        
                    # Get or create registry for this org
                    if org not in registries:
                        registries[org] = GitHubRegistry(token, org)
                    registry = registries[org]
                    
                    dep_path = package.get_dependency_path(name)
                    if not dep_path.exists():
                        logger.info(f"Installing {name} {version_spec}")
                        
                        # Get all available versions
                        available_versions = registry.get_versions(pkg_name)
                        if not available_versions:
                            return f"No versions found for package {name}"
                            
                        # Find best matching version
                        if version_spec.startswith('^'):
                            # For ^x.y.z, find highest compatible version
                            base_version = Version.parse(version_spec[1:])
                            compatible_versions = [v for v in available_versions if v.is_compatible_with(base_version)]
                            if not compatible_versions:
                                return f"No compatible versions found for {name}@{version_spec}"
                            target_version = str(max(compatible_versions))
                        else:
                            # For exact version, find exact match
                            target_version = version_spec
                            
                        # Get package with resolved version
                        dep_pkg = registry.get_package(pkg_name, target_version)
                        
                        # Create parent directories if needed
                        dep_path.parent.mkdir(parents=True, exist_ok=True)
                        # Copy package files
                        import shutil
                        shutil.copytree(dep_pkg.path, dep_path)
                    else:
                        # Verify installed version matches
                        dep_pkg = Package(dep_path)
                        if not dep_pkg.is_compatible_with(version_spec):
                            logger.info(f"Updating {name} to match {version_spec}")
                            
                            # Get all available versions
                            available_versions = registry.get_versions(pkg_name)
                            if not available_versions:
                                return f"No versions found for package {name}"
                                
                            # Find best matching version
                            if version_spec.startswith('^'):
                                # For ^x.y.z, find highest compatible version
                                base_version = Version.parse(version_spec[1:])
                                compatible_versions = [v for v in available_versions if v.is_compatible_with(base_version)]
                                if not compatible_versions:
                                    return f"No compatible versions found for {name}@{version_spec}"
                                target_version = str(max(compatible_versions))
                            else:
                                # For exact version, find exact match
                                target_version = version_spec
                                
                            # Get package with resolved version
                            new_pkg = registry.get_package(pkg_name, target_version)
                            
                            # Remove old package
                            import shutil
                            shutil.rmtree(dep_path)
                            # Copy new package files
                            shutil.copytree(new_pkg.path, dep_path)
                            
            return None
        except Exception as e:
            error_msg = f"Failed to install dependencies: {str(e)}"
            logger.error(error_msg)
            return error_msg
            
    def _build_dependencies(
        self,
        package: Package,
        context: BuildContext,
        parent_package: Optional[Package] = None
    ) -> Optional[str]:
        """Build all dependencies in the correct order.
        
        Returns:
            Error message if failed, None if successful
        """
        try:
            # Create dependency resolver
            from ..core.dependency.resolver import DependencyResolver
            resolver = DependencyResolver(verbose=context.verbose)
            
            try:
                # Add package and its dependencies to the graph
                resolver.add_package(package)
            except ValueError as e:
                # This is likely a dependency not found error
                return str(e)  # Return the detailed error from resolver
                
            try:
                # Get build order (this will also check for cycles)
                build_order = resolver.get_build_order()
            except ValueError as e:
                return str(e)  # This will include cycle detection errors
                
            # Build each dependency in order
            for dep in build_order:
                # Skip the root package if it's not a dependency of another package
                if dep.name == package.name and not parent_package:
                    continue
                    
                logger.info(f"Building dependency: {dep.name}")
                
                # Create build context for dependency
                dep_context = BuildContext(
                    package=dep,
                    build_metadata=dep.create_build_metadata(context.build_metadata.compiler),
                    traits=context.traits,
                    verbose=context.verbose
                )
                
                # Build the dependency, passing the parent package
                result = self.build(dep, traits=context.traits, verbose=context.verbose, parent_package=package)
                if not result.success:
                    # Get the build directory for better error messages
                    build_dir = package.get_build_path(dep.name)
                    return result.error  # Just return the error, don't wrap it again
                    
            return None
        except Exception as e:
            error_msg = f"Failed to build dependencies: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _build_package(self, context: BuildContext, parent_package: Optional[Package] = None) -> BuildResult:
        """Build a package after dependencies are built.
        
        Args:
            context: Build context
            parent_package: If building a dependency, the package that depends on this one
            
        Returns:
            BuildResult indicating success/failure and artifacts
        """
        try:
            # Get source files and make paths relative to build dir
            sources = context.package.get_source_files()
            logger.debug(f"Found source files for {context.package.name}: {sources}")
            
            if not sources:
                error_msg = f"No source files found for {context.package.name} in {os.path.relpath(context.package.path/'src')}"
                logger.error(error_msg)
                return BuildResult(success=False, error=error_msg)
                
            # Compile each source file
            objects = []
            for source in sources:
                logger.debug(f"Compiling source file: {source}")
                # Use relative paths for object files
                object_path = Path(f"{source.stem}.o")
                error = self._compile_source(
                    source,
                    object_path,
                    context.package,
                    context.build_metadata,
                    context.verbose,
                    context.traits
                )
                if error:
                    logger.error(f"Failed to compile {source}: {error}")
                    return BuildResult(success=False, error=f"Failed to compile {source}:\n{error}")
                objects.append(object_path)
                
            # Link objects
            if context.package.package_type == PackageType.LIBRARY:
                output_name = f"lib{context.package.package_name}.a"
            else:
                output_name = context.package.name
            output_path = Path(output_name)
            
            logger.debug(f"Linking objects for {context.package.name}: {objects}")
            error = self._link_objects(
                objects,
                output_path,
                context.package,
                context.build_metadata,
                context.verbose,
                context.traits
            )
            if error:
                logger.error(f"Failed to link {context.package.name}: {error}")
                return BuildResult(success=False, error=f"Failed to link {context.package.name}:\n{error}")
                
            # Run post-build hooks
            try:
                self.hook_manager.run_hooks(BuildStage.POST_BUILD, context)
            except Exception as e:
                logger.error(f"Post-build hook failed for {context.package.name}: {e}")
                return BuildResult(success=False, error=f"Post-build hook failed: {str(e)}")
                
            # Return success with artifacts (convert back to absolute paths)
            output_path = context.package.get_output_path(parent_package)
            logger.debug(f"Build successful for {context.package.name}, output at: {output_path}")
            return BuildResult(
                success=True,
                artifacts={"output": output_path}
            )
        except Exception as e:
            error_msg = f"Build failed for {context.package.name}: {str(e)}"
            if hasattr(e, '__traceback__'):
                import traceback
                error_msg += f"\nTraceback:\n{''.join(traceback.format_tb(e.__traceback__))}"
            logger.error(error_msg)
            return BuildResult(success=False, error=error_msg)

    def build(
        self,
        package: Package,
        traits: Optional[Dict[str, str]] = None,
        verbose: bool = False,
        parent_package: Optional[Package] = None
    ) -> BuildResult:
        """Build a package."""
        logger.debug(f"Starting build of {package.name}")
        if parent_package:
            logger.debug(f"Building as dependency of {parent_package.name}")
        
        # Check if package has already been built
        package_key = (package.name, package.path)
        if package_key in self._built_packages:
            logger.debug(f"Package {package.name} has already been built, skipping")
            return BuildResult(success=True)
        
        try:
            # Create build metadata
            compiler_info = self._get_compiler_info()
            build_metadata = package.create_build_metadata(compiler_info)
            logger.debug(f"Created build metadata for {package.name}")
            
            # Add traits to build metadata
            if traits:
                build_metadata.traits.update(traits)
                logger.debug(f"Added traits to build metadata: {traits}")
                
            # Create build directory - use parent's build/deps directory if this is a dependency
            if parent_package:
                build_dir = parent_package.get_build_path(package._validated_config.name)
            else:
                build_dir = package.get_build_dir()
                
            logger.debug(f"Using build directory: {build_dir}")
                
            try:
                build_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                error_msg = f"Failed to create build directory {build_dir}: {str(e)}"
                logger.error(error_msg)
                return BuildResult(success=False, error=error_msg)
            
            # Change to build directory for all operations
            try:
                old_cwd = Path.cwd()
                os.chdir(build_dir)
                logger.debug(f"Changed working directory to: {build_dir}")
            except Exception as e:
                error_msg = f"Failed to change to build directory {build_dir}: {str(e)}"
                logger.error(error_msg)
                return BuildResult(success=False, error=error_msg)
                
            try:
                # Create build context
                context = BuildContext(
                    package=package,
                    build_metadata=build_metadata,
                    traits=traits or {},
                    verbose=verbose
                )
                
                try:
                    # Run pre-build hooks
                    logger.debug("Running pre-build hooks")
                    self.hook_manager.run_hooks(BuildStage.PRE_BUILD, context)
                except Exception as e:
                    error_msg = f"Pre-build hook failed for {package.name}: {str(e)}"
                    logger.error(error_msg)
                    return BuildResult(success=False, error=error_msg)
                
                # Step 1: Ensure all dependencies are installed
                logger.debug("Ensuring dependencies are installed")
                error = self._ensure_dependencies(package, context)
                if error:
                    logger.error(f"Dependency installation failed for {package.name}: {error}")
                    return BuildResult(success=False, error=error)
                
                # Step 2: Build all dependencies in topological order
                logger.debug("Building dependencies")
                error = self._build_dependencies(package, context, parent_package)
                if error:
                    logger.error(f"Dependency build failed for {package.name}: {error}")
                    return BuildResult(success=False, error=error)
                
                # Run post-dependency hooks
                try:
                    logger.debug("Running post-dependency hooks")
                    self.hook_manager.run_hooks(BuildStage.POST_DEPENDENCY_BUILD, context)
                except Exception as e:
                    error_msg = f"Post-dependency hook failed for {package.name}: {str(e)}"
                    logger.error(error_msg)
                    return BuildResult(success=False, error=error_msg)
                
                # Step 3: Build the package itself
                logger.debug(f"Building package {package.name}")
                result = self._build_package(context, parent_package)
                if not result.success:
                    logger.error(f"Package build failed for {package.name}: {result.error}")
                    return result
                
                # Mark package as built
                self._built_packages.add(package_key)
                
                logger.debug(f"Successfully built {package.name}")
                return result
                
            finally:
                # Change back to original directory
                logger.debug(f"Changing back to original directory: {old_cwd}")
                os.chdir(old_cwd)
                
        except Exception as e:
            error_msg = f"Build failed for {package.name}: {str(e)}"
            if hasattr(e, '__traceback__'):
                import traceback
                error_msg += f"\nTraceback:\n{''.join(traceback.format_tb(e.__traceback__))}"
            logger.error(error_msg)
            return BuildResult(success=False, error=error_msg) 