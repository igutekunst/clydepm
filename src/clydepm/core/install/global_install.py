"""
Module for handling global/system-wide installation of packages.
"""
from pathlib import Path
from typing import Optional, Dict, Any
import os
import shutil
import logging
import json
from datetime import datetime
from rich.prompt import Confirm

logger = logging.getLogger(__name__)

class GlobalInstaller:
    """Handles system-wide installation of packages."""
    
    def __init__(self, prefix: Optional[Path] = None):
        """Initialize global installer.
        
        Args:
            prefix: Optional custom prefix path. Defaults to ~/.clydepm/prefix
            prefix: Optional custom prefix path. Defaults to ~/.clyde/prefix
        """
        self.clyde_home = Path.home() / ".clyde"
        self.packages_dir = self.clyde_home / "packages"
        self.prefix = prefix or self.clyde_home / "prefix"
        self.bin_dir = self.prefix / "bin"
        self.lib_dir = self.prefix / "lib"
        self.include_dir = self.prefix / "include"
        
    def setup_directories(self) -> None:
        """Create installation directory structure if it doesn't exist."""
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        self.prefix.mkdir(parents=True, exist_ok=True)
        self.bin_dir.mkdir(exist_ok=True)
        self.lib_dir.mkdir(exist_ok=True)
        self.include_dir.mkdir(exist_ok=True)
        
    def get_package_dir(self, name: str) -> Path:
        """Get the installation directory for a package.
        
        Args:
            name: Package name
            
        Returns:
            Path to package directory
        """
        return self.packages_dir / name
        
    def create_symlink(self, source: Path, link: Path, overwrite: bool = False) -> bool:
        """Create a symlink, handling overwrites.
        
        Args:
            source: Source path
            link: Link path
            overwrite: Whether to overwrite existing link
            
        Returns:
            bool: True if successful
        """
        try:
            if link.exists() or link.is_symlink():
                if not overwrite:
                    logger.warning("Link already exists: %s", link)
                    return False
                link.unlink()
            
            # Create parent directories if needed
            link.parent.mkdir(parents=True, exist_ok=True)
            
            # Create relative symlink
            rel_source = os.path.relpath(source, link.parent)
            os.symlink(rel_source, link)
            return True
        except Exception as e:
            logger.error("Failed to create symlink: %s", e)
            return False
            
    def write_install_metadata(
        self,
        package_dir: Path,
        name: str,
        version: str,
        files: Dict[str, list],
        build_info: Dict[str, Any],
        dependencies: Dict[str, str]
    ) -> bool:
        """Write installation metadata file.
        
        Args:
            package_dir: Package installation directory
            name: Package name
            version: Package version
            files: Installed files by type
            build_info: Build information
            dependencies: Package dependencies
            
        Returns:
            bool: True if successful
        """
        try:
            metadata = {
                "name": name,
                "version": version,
                "installed_at": datetime.utcnow().isoformat(),
                "files": files,
                "dependencies": dependencies,
                "build_info": build_info
            }
            
            with open(package_dir / "install.json", "w") as f:
                json.dump(metadata, f, indent=2)
            return True
        except Exception as e:
            logger.error("Failed to write install metadata: %s", e)
            return False
            
    def install_binary(self, src: Path, name: str, package_name: str, overwrite: bool = False) -> bool:
        """Install a binary and create symlink in prefix.
        
        Args:
            src: Source binary path
            name: Binary name
            package_name: Name of package
            overwrite: Whether to overwrite existing files
            
        Returns:
            bool: True if installation succeeded
        """
        package_dir = self.get_package_dir(package_name)
        package_bin_dir = package_dir / "bin"
        package_bin_dir.mkdir(parents=True, exist_ok=True)
        
        # Install binary to package directory
        dest = package_bin_dir / name
        try:
            if dest.exists():
                if not overwrite:
                    logger.warning("Binary already exists: %s", dest)
                    return False
                dest.unlink()
            shutil.copy2(src, dest)
            os.chmod(dest, 0o755)  # Make executable
        except Exception as e:
            logger.error("Failed to install binary: %s", e)
            return False
            
        # Create symlink in prefix
        return self.create_symlink(dest, self.bin_dir / name, overwrite)
        
    def install_library(self, src: Path, name: str, package_name: str, overwrite: bool = False) -> bool:
        """Install a library and create symlink in prefix.
        
        Args:
            src: Source library path
            name: Library name
            package_name: Name of package
            overwrite: Whether to overwrite existing files
            
        Returns:
            bool: True if installation succeeded
        """
        package_dir = self.get_package_dir(package_name)
        package_lib_dir = package_dir / "lib"
        package_lib_dir.mkdir(parents=True, exist_ok=True)
        
        # Install library to package directory
        dest = package_lib_dir / name
        try:
            if dest.exists():
                if not overwrite:
                    logger.warning("Library already exists: %s", dest)
                    return False
                dest.unlink()
            shutil.copy2(src, dest)
        except Exception as e:
            logger.error("Failed to install library: %s", e)
            return False
            
        # Create symlink in prefix
        return self.create_symlink(dest, self.lib_dir / name, overwrite)
        
    def install_headers(self, src_dir: Path, package_name: str, overwrite: bool = False) -> bool:
        """Install headers and create symlink in prefix.
        
        Args:
            src_dir: Source directory containing headers
            package_name: Name of package
            overwrite: Whether to overwrite existing files
            
        Returns:
            bool: True if installation succeeded
        """
        package_dir = self.get_package_dir(package_name)
        package_include_dir = package_dir / "include"
        
        try:
            # Install headers to package directory
            if package_include_dir.exists():
                if not overwrite:
                    logger.warning("Headers already exist: %s", package_include_dir)
                    return False
                shutil.rmtree(package_include_dir)
            shutil.copytree(src_dir, package_include_dir)
        except Exception as e:
            logger.error("Failed to install headers: %s", e)
            return False
            
        # Create symlink in prefix
        return self.create_symlink(
            package_include_dir,
            self.include_dir / package_name,
            overwrite
        )
        
    def check_file_exists(self, path: Path) -> bool:
        """Check if a file exists and prompt for overwrite if it does.
        
        Args:
            path: Path to check
            
        Returns:
            bool: True if file can be written (doesn't exist or user approved overwrite)
        """
        if not path.exists():
            return True
            
        logger.warning(f"File already exists: {path}")
        return Confirm.ask("Do you want to overwrite?") 