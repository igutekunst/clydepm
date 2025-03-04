"""
Build artifact caching system.
"""
from pathlib import Path
from typing import Dict, List, Optional, Set
import hashlib
import json
import shutil
import logging
import os
import tarfile
from dataclasses import asdict

from ..core.package import Package, BuildMetadata

logger = logging.getLogger(__name__)

class TarFilter:
    """Filter for tar file extraction that preserves file permissions."""
    
    def __call__(self, member: tarfile.TarInfo, path: Optional[str] = None) -> Optional[tarfile.TarInfo]:
        """Filter tar file members during extraction.
        
        Args:
            member: The tar file member being processed
            path: Optional extraction path
            
        Returns:
            The processed member or None to skip it
        """
        # Skip unsafe files
        if not member.name or member.name.startswith(('/', '..')):
            return None
            
        # Ensure reasonable permissions
        member.mode = 0o644  # Regular files
        if member.isdir():
            member.mode = 0o755  # Directories
        if member.islnk() or member.issym():
            return None  # Skip links for safety
            
        return member

class BuildCache:
    """Manages caching of build artifacts."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize build cache.
        
        Args:
            cache_dir: Directory to store cache. Defaults to ~/.clydepm/cache
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".clydepm" / "cache"
            
        self.cache_dir = cache_dir
        self.objects_dir = cache_dir / "objects"
        self.deps_dir = cache_dir / "deps"
        self.artifacts_dir = cache_dir / "artifacts"
        
        # Create cache directories
        for dir in [self.cache_dir, self.objects_dir, self.deps_dir, self.artifacts_dir]:
            dir.mkdir(parents=True, exist_ok=True)
            
        logger.debug("Using build cache at %s", self.cache_dir)
        
    def _hash_file(self, path: Path) -> str:
        """Generate hash for a file based on its contents."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
        
    def _hash_source(self, source_path: Path, build_metadata: BuildMetadata) -> str:
        """Generate hash for a source file and its build configuration."""
        # Hash the source file
        file_hash = self._hash_file(source_path)
        
        # Hash the build configuration
        config = {
            "compiler": asdict(build_metadata.compiler),
            "cflags": sorted(build_metadata.cflags),
            "includes": [str(p) for p in build_metadata.includes],
            "traits": build_metadata.traits
        }
        config_hash = hashlib.sha256(
            json.dumps(config, sort_keys=True).encode()
        ).hexdigest()
        
        # Combine hashes
        return hashlib.sha256(
            f"{file_hash}:{config_hash}".encode()
        ).hexdigest()
        
    def get_object_path(self, source_path: Path, build_metadata: BuildMetadata) -> Path:
        """Get path where cached object file should be stored."""
        obj_hash = self._hash_source(source_path, build_metadata)
        return self.objects_dir / f"{obj_hash}.o"
        
    def has_cached_object(self, source_path: Path, build_metadata: BuildMetadata) -> bool:
        """Check if object file is cached for source file."""
        cached = self.get_object_path(source_path, build_metadata).exists()
        if cached:
            logger.info("[Cache Hit] Found cached object for %s", source_path.name)
        else:
            logger.info("[Cache Miss] No cached object for %s", source_path.name)
        return cached
        
    def cache_object(self, source_path: Path, object_path: Path, build_metadata: BuildMetadata) -> None:
        """Cache compiled object file."""
        cached_path = self.get_object_path(source_path, build_metadata)
        logger.debug("Caching object %s -> %s", object_path, cached_path)
        shutil.copy2(object_path, cached_path)
        
    def get_cached_object(
        self,
        source_path: Path,
        build_metadata: BuildMetadata,
        dest_path: Path
    ) -> bool:
        """Get cached object file if it exists.
        
        Returns:
            True if cached object was found and copied, False otherwise
        """
        cached_path = self.get_object_path(source_path, build_metadata)
        if cached_path.exists():
            logger.debug("Using cached object %s -> %s", cached_path, dest_path)
            # Create destination directory
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cached_path, dest_path)
            return True
        return False
        
    def _hash_artifact(self, package: Package, build_metadata: BuildMetadata) -> str:
        """Generate hash for final artifact based on all source files and build config."""
        hasher = hashlib.sha256()
        
        # Hash all source files
        for source in sorted(package.get_source_files()):
            source_path = package.path / source
            hasher.update(self._hash_file(source_path).encode())
            
        # Hash build configuration
        config = {
            "name": package.name,
            "version": str(package.version),
            "type": package.package_type.value,
            "compiler": asdict(build_metadata.compiler),
            "cflags": sorted(build_metadata.cflags),
            "includes": [str(p) for p in build_metadata.includes],
            "traits": build_metadata.traits
        }
        hasher.update(
            json.dumps(config, sort_keys=True).encode()
        )
        
        return hasher.hexdigest()
        
    def get_artifact_path(self, package: Package, build_metadata: BuildMetadata) -> Path:
        """Get path where cached final artifact should be stored."""
        artifact_hash = self._hash_artifact(package, build_metadata)
        return self.artifacts_dir / f"{package.name}-{artifact_hash}"
        
    def has_cached_artifact(self, package: Package, build_metadata: BuildMetadata) -> bool:
        """Check if final artifact is cached."""
        cached = self.get_artifact_path(package, build_metadata).exists()
        if cached:
            logger.info("[Cache Hit] Found cached artifact for %s %s", package.name, package.version)
        else:
            logger.info("[Cache Miss] No cached artifact for %s %s", package.name, package.version)
        return cached
        
    def cache_artifact(self, package: Package, build_metadata: BuildMetadata) -> None:
        """Cache final build artifact."""
        cached_path = self.get_artifact_path(package, build_metadata)
        output_path = package.get_output_path()
        
        logger.debug("Caching artifact %s -> %s", output_path, cached_path)
        
        # Create tarball of the artifact and its dependencies
        with tarfile.open(cached_path, "w:gz") as tar:
            # Add the main artifact
            tar.add(output_path, arcname=output_path.name)
            
            # Add any dependency artifacts needed for runtime
            for dep in package.get_runtime_dependencies():
                dep_output = dep.get_output_path()
                if dep_output.exists():
                    tar.add(dep_output, arcname=dep_output.name)
                    
    def get_cached_artifact(self, package: Package, build_metadata: BuildMetadata) -> bool:
        """Get cached final artifact if it exists.
        
        Returns:
            True if cached artifact was found and extracted, False otherwise
        """
        cached_path = self.get_artifact_path(package, build_metadata)
        if cached_path.exists():
            logger.debug("Using cached artifact %s", cached_path)
            
            # Extract the cached artifact
            with tarfile.open(cached_path, "r:gz") as tar:
                def is_within_directory(directory, target):
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted path traversal in tar file")
                    
                    tar.extractall(
                        path,
                        members,
                        numeric_owner=numeric_owner,
                        filter=TarFilter()
                    )
                
                # Safely extract to the package's output directory
                output_dir = package.get_output_path().parent
                output_dir.mkdir(parents=True, exist_ok=True)
                safe_extract(tar, str(output_dir))
                
            return True
        return False
        
    def clean_package(self, package: Package) -> None:
        """Clean cached artifacts for a specific package.
        
        Args:
            package: Package to clean artifacts for
        """
        logger.info("Cleaning cache for package %s", package.name)
        
        # Clean artifacts directory
        for artifact in self.artifacts_dir.glob(f"{package.name}-*"):
            logger.debug("Removing artifact %s", artifact)
            artifact.unlink()
            
        # Clean object files
        build_dir = package.get_build_dir()
        if build_dir.exists():
            logger.debug("Removing build directory %s", build_dir)
            shutil.rmtree(build_dir)
            
        # Clean dependency artifacts recursively
        for dep in package.get_all_dependencies():
            self.clean_package(dep)
            
    def clean(self) -> None:
        """Clean the entire cache."""
        logger.info("Cleaning build cache at %s", self.cache_dir)
        shutil.rmtree(self.cache_dir)
        self.cache_dir.mkdir(parents=True)
        self.objects_dir.mkdir()
        self.deps_dir.mkdir()
        self.artifacts_dir.mkdir() 