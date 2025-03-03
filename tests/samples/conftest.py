"""
Fixtures for sample package testing.
"""
import os
import shutil
from pathlib import Path
import pytest
from typing import Generator, Callable

@pytest.fixture
def samples_dir() -> Path:
    """Return the path to the samples directory."""
    return Path(__file__).parent / "packages"

@pytest.fixture
def copy_sample() -> Callable[[str, Path], Path]:
    """
    Fixture that provides a function to copy a sample package to a temporary directory.
    
    Args:
        package_name: Name of the sample package to copy
        target_dir: Directory to copy the package to
        
    Returns:
        Path to the copied package
    """
    def _copy_sample(package_name: str, target_dir: Path) -> Path:
        source_dir = Path(__file__).parent / "packages" / package_name
        if not source_dir.exists():
            raise ValueError(f"Sample package {package_name} not found")
            
        # Create target directory
        target_package_dir = target_dir / package_name
        target_package_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy package contents
        for item in source_dir.glob("*"):
            if item.is_dir():
                shutil.copytree(item, target_package_dir / item.name)
            else:
                shutil.copy2(item, target_package_dir / item.name)
                
        return target_package_dir
        
    return _copy_sample

@pytest.fixture
def temp_build_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create a temporary directory for building packages.
    Cleans up after the test.
    """
    build_dir = tmp_path / "build"
    build_dir.mkdir(parents=True)
    yield build_dir
    shutil.rmtree(build_dir) 