"""
Tests for sample packages.
"""
import pytest
from pathlib import Path
from clydepm.core.package import Package
from clydepm.build.builder import Builder

def test_simple_package(copy_sample: callable, temp_build_dir: Path):
    """Test building a simple single-file package."""
    # Copy sample to temp directory
    package_dir = copy_sample("simple", temp_build_dir)
    
    # Create package and builder
    package = Package(package_dir)
    builder = Builder()
    
    # Build package
    result = builder.build(package)
    assert result.success
    assert result.artifacts
    
    # Check output exists
    assert any(path.exists() for path in result.artifacts.values())

def test_multi_file_package(copy_sample: callable, temp_build_dir: Path):
    """Test building a package with multiple source files."""
    # Copy sample to temp directory
    package_dir = copy_sample("multi_file", temp_build_dir)
    
    # Create package and builder
    package = Package(package_dir)
    builder = Builder()
    
    # Build package
    result = builder.build(package)
    assert result.success
    assert result.artifacts
    
    # Check output exists
    assert any(path.exists() for path in result.artifacts.values())

def test_package_with_deps(copy_sample: callable, temp_build_dir: Path):
    """Test building a package with dependencies."""
    # Copy sample to temp directory
    package_dir = copy_sample("with_deps", temp_build_dir)
    builder = Builder()
    
    # First build the formatter library
    formatter_dir = package_dir / "formatter"
    formatter_package = Package(formatter_dir)
    result = builder.build(formatter_package)
    assert result.success, "Failed to build formatter library"
    assert result.artifacts, "No artifacts produced for formatter library"
    
    # Then build the main application
    main_app_dir = package_dir / "main_app"
    main_package = Package(main_app_dir)
    result = builder.build(main_package)
    assert result.success, "Failed to build main application"
    assert result.artifacts, "No artifacts produced for main application"
    
    # Check both outputs exist
    assert any(path.exists() for path in result.artifacts.values()) 