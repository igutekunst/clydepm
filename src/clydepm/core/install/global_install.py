"""
Module for handling global/system-wide installation of packages.
"""
from pathlib import Path
from typing import Optional
import os
import shutil
import logging
from rich.prompt import Confirm

logger = logging.getLogger(__name__)

class GlobalInstaller:
    """Handles system-wide installation of packages."""
    
    def __init__(self, prefix: Optional[Path] = None):
        """Initialize global installer.
        
        Args:
            prefix: Optional custom prefix path. Defaults to ~/.clyde/prefix
        """
        self.prefix = prefix or Path.home() / ".clyde" / "prefix"
        self.bin_dir = self.prefix / "bin"
        self.lib_dir = self.prefix / "lib"
        self.include_dir = self.prefix / "include"
        
    def setup_directories(self) -> None:
        """Create installation directory structure if it doesn't exist."""
        self.prefix.mkdir(parents=True, exist_ok=True)
        self.bin_dir.mkdir(exist_ok=True)
        self.lib_dir.mkdir(exist_ok=True)
        self.include_dir.mkdir(exist_ok=True)
        
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
        
    def install_binary(self, src: Path, name: str, overwrite: bool = False) -> bool:
        """Install a binary to prefix/bin.
        
        Args:
            src: Source binary path
            name: Name of binary
            overwrite: Whether to overwrite existing files
            
        Returns:
            bool: True if installation succeeded
        """
        dest = self.bin_dir / name
        if dest.exists() and not overwrite:
            logger.warning("File already exists: %s", dest)
            return False
            
        try:
            if dest.exists():
                dest.unlink()
            shutil.copy2(src, dest)
            os.chmod(dest, 0o755)  # Make executable
            return True
        except Exception as e:
            logger.error("Failed to install binary: %s", e)
            return False
        
    def install_library(self, src: Path, name: str, overwrite: bool = False) -> bool:
        """Install a library to prefix/lib.
        
        Args:
            src: Source library path
            name: Name of library file
            overwrite: Whether to overwrite existing files
            
        Returns:
            bool: True if installation succeeded
        """
        dest = self.lib_dir / name
        if dest.exists() and not overwrite:
            logger.warning("File already exists: %s", dest)
            return False
            
        try:
            if dest.exists():
                dest.unlink()
            shutil.copy2(src, dest)
            return True
        except Exception as e:
            logger.error("Failed to install library: %s", e)
            return False
        
    def install_headers(self, src_dir: Path, package_name: str, overwrite: bool = False) -> bool:
        """Install headers to prefix/include/package_name.
        
        Args:
            src_dir: Source directory containing headers
            package_name: Name of package (used for include subdirectory)
            overwrite: Whether to overwrite existing files
            
        Returns:
            bool: True if installation succeeded
        """
        dest_dir = self.include_dir / package_name
        
        if dest_dir.exists() and not overwrite:
            logger.warning("Directory already exists: %s", dest_dir)
            return False
            
        try:
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)
            return True
        except Exception as e:
            logger.error("Failed to install headers: %s", e)
            return False 