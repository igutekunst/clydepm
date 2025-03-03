"""
Tests for version resolution.
"""
import pytest
from clydepm.core.version import Version, VersionRange, VersionResolver

def test_find_latest_compatible():
    """Test finding latest compatible version."""
    available_versions = [
        Version.parse(v) for v in [
            "1.0.0",
            "1.1.0",
            "1.2.0",
            "1.2.1",
            "1.2.2",
            "2.0.0",
            "2.0.1",
        ]
    ]
    
    # Test exact version
    constraints = VersionRange.parse("1.2.0")
    result = VersionResolver.find_latest_compatible(available_versions, constraints)
    assert result == Version.parse("1.2.0")
    
    # Test version range
    constraints = VersionRange.parse(">=1.2.0 <2.0.0")
    result = VersionResolver.find_latest_compatible(available_versions, constraints)
    assert result == Version.parse("1.2.2")
    
    # Test caret range
    constraints = VersionRange.parse("^1.0.0")
    result = VersionResolver.find_latest_compatible(available_versions, constraints)
    assert result == Version.parse("1.2.2")
    
    # Test no compatible versions
    constraints = VersionRange.parse(">=3.0.0")
    result = VersionResolver.find_latest_compatible(available_versions, constraints)
    assert result is None

def test_find_all_compatible():
    """Test finding all compatible versions."""
    available_versions = [
        Version.parse(v) for v in [
            "1.0.0",
            "1.1.0",
            "1.2.0-beta",
            "1.2.0",
            "1.2.1",
            "2.0.0-alpha",
            "2.0.0",
        ]
    ]
    
    # Test exact version
    constraints = VersionRange.parse("1.2.0")
    result = VersionResolver.find_all_compatible(available_versions, constraints)
    assert result == [Version.parse("1.2.0")]
    
    # Test version range - prereleases excluded by default
    constraints = VersionRange.parse(">=1.2.0 <2.0.0")
    result = VersionResolver.find_all_compatible(available_versions, constraints)
    assert result == [
        Version.parse("1.2.1"),
        Version.parse("1.2.0"),
    ]
    
    # Test version range with explicit prerelease
    constraints = VersionRange.parse(">=1.2.0-0 <2.0.0")
    result = VersionResolver.find_all_compatible(available_versions, constraints)
    assert result == [
        Version.parse("1.2.1"),
        Version.parse("1.2.0"),
        Version.parse("1.2.0-beta"),
    ]
    
    # Test no compatible versions
    constraints = VersionRange.parse(">=3.0.0")
    result = VersionResolver.find_all_compatible(available_versions, constraints)
    assert result == []

def test_find_minimal_compatible():
    """Test finding minimal compatible version."""
    # Compatible versions
    v1 = Version.parse("1.2.0")
    v2 = Version.parse("1.3.0")
    result = VersionResolver.find_minimal_compatible(v1, v2)
    assert result == v1
    
    # Different order
    result = VersionResolver.find_minimal_compatible(v2, v1)
    assert result == v1
    
    # Incompatible versions
    v1 = Version.parse("1.0.0")
    v2 = Version.parse("2.0.0")
    result = VersionResolver.find_minimal_compatible(v1, v2)
    assert result is None
    
    # Same version
    v1 = Version.parse("1.0.0")
    result = VersionResolver.find_minimal_compatible(v1, v1)
    assert result == v1

def test_find_maximal_compatible():
    """Test finding maximal compatible version."""
    # Compatible versions
    v1 = Version.parse("1.2.0")
    v2 = Version.parse("1.3.0")
    result = VersionResolver.find_maximal_compatible(v1, v2)
    assert result == v2
    
    # Different order
    result = VersionResolver.find_maximal_compatible(v2, v1)
    assert result == v2
    
    # Incompatible versions
    v1 = Version.parse("1.0.0")
    v2 = Version.parse("2.0.0")
    result = VersionResolver.find_maximal_compatible(v1, v2)
    assert result is None
    
    # Same version
    v1 = Version.parse("1.0.0")
    result = VersionResolver.find_maximal_compatible(v1, v1)
    assert result == v1

def test_find_compatible_range():
    """Test finding compatible version range."""
    # Compatible versions
    v1 = Version.parse("1.2.0")
    v2 = Version.parse("1.3.0")
    result = VersionResolver.find_compatible_range(v1, v2)
    assert result is not None
    assert result.matches(v1)
    assert result.matches(v2)
    assert not result.matches(Version.parse("1.1.0"))
    assert not result.matches(Version.parse("1.4.0"))
    
    # Incompatible versions
    v1 = Version.parse("1.0.0")
    v2 = Version.parse("2.0.0")
    result = VersionResolver.find_compatible_range(v1, v2)
    assert result is None
    
    # Same version
    v1 = Version.parse("1.0.0")
    result = VersionResolver.find_compatible_range(v1, v1)
    assert result is not None
    assert result.matches(v1) 