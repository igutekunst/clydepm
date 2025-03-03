"""
Tests for the Version class.
"""
import pytest
from clydepm.core.version import Version

def test_version_parsing():
    """Test parsing version strings."""
    # Test basic versions
    v = Version.parse("1.2.3")
    assert v.major == 1
    assert v.minor == 2
    assert v.patch == 3
    assert v.prerelease is None
    assert v.build is None
    
    # Test with prerelease
    v = Version.parse("1.2.3-beta.1")
    assert v.major == 1
    assert v.minor == 2
    assert v.patch == 3
    assert v.prerelease == "beta.1"
    assert v.build is None
    
    # Test with build metadata
    v = Version.parse("1.2.3+build.123")
    assert v.major == 1
    assert v.minor == 2
    assert v.patch == 3
    assert v.prerelease is None
    assert v.build == "build.123"
    
    # Test with both prerelease and build
    v = Version.parse("1.2.3-beta.1+build.123")
    assert v.major == 1
    assert v.minor == 2
    assert v.patch == 3
    assert v.prerelease == "beta.1"
    assert v.build == "build.123"

def test_invalid_versions():
    """Test parsing invalid version strings."""
    invalid_versions = [
        "",  # Empty string
        "1",  # Missing minor and patch
        "1.2",  # Missing patch
        "1.2.3.4",  # Too many components
        "a.b.c",  # Non-numeric components
        "1.2.3-",  # Empty prerelease
        "1.2.3+",  # Empty build
        "-1.2.3",  # Negative numbers
        "1.2.3-@invalid",  # Invalid prerelease characters
        "01.2.3",  # Leading zeros
    ]
    
    for version in invalid_versions:
        with pytest.raises(ValueError):
            Version.parse(version)

def test_version_comparison():
    """Test version comparison operations."""
    # Basic ordering
    assert Version.parse("1.2.3") < Version.parse("2.0.0")
    assert Version.parse("1.2.3") < Version.parse("1.3.0")
    assert Version.parse("1.2.3") < Version.parse("1.2.4")
    
    # Prerelease versions are lower than release versions
    assert Version.parse("1.2.3-alpha") < Version.parse("1.2.3")
    assert Version.parse("1.2.3-alpha") < Version.parse("1.2.3-beta")
    
    # Build metadata is ignored in comparison
    assert Version.parse("1.2.3+build.1") == Version.parse("1.2.3+build.2")
    
    # Complex comparisons
    versions = [
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0-beta",
        "1.0.0-beta.2",
        "1.0.0-beta.11",
        "1.0.0-rc.1",
        "1.0.0",
        "1.0.1",
        "1.1.0",
        "2.0.0",
    ]
    
    # Check that each version is less than all following versions
    for i, v1 in enumerate(versions[:-1]):
        for v2 in versions[i+1:]:
            assert Version.parse(v1) < Version.parse(v2)

def test_version_equality():
    """Test version equality."""
    # Same versions should be equal
    assert Version.parse("1.2.3") == Version.parse("1.2.3")
    assert Version.parse("1.2.3-beta") == Version.parse("1.2.3-beta")
    
    # Build metadata doesn't affect equality
    assert Version.parse("1.2.3+build.1") == Version.parse("1.2.3+build.2")
    
    # Different versions should not be equal
    assert Version.parse("1.2.3") != Version.parse("1.2.4")
    assert Version.parse("1.2.3-alpha") != Version.parse("1.2.3-beta")

def test_version_string_representation():
    """Test converting versions to strings."""
    versions = [
        "1.2.3",
        "1.2.3-beta",
        "1.2.3+build.123",
        "1.2.3-beta+build.123",
    ]
    
    for version in versions:
        assert str(Version.parse(version)) == version

def test_version_compatibility():
    """Test version compatibility checks."""
    # Same major version should be compatible
    assert Version.parse("1.2.3").is_compatible_with(Version.parse("1.3.0"))
    assert Version.parse("2.0.0").is_compatible_with(Version.parse("2.1.0"))
    
    # Different major versions should not be compatible
    assert not Version.parse("1.2.3").is_compatible_with(Version.parse("2.0.0"))
    assert not Version.parse("2.0.0").is_compatible_with(Version.parse("3.0.0"))
    
    # Prerelease and build metadata don't affect compatibility
    assert Version.parse("1.2.3-beta").is_compatible_with(Version.parse("1.2.3"))
    assert Version.parse("1.2.3+build").is_compatible_with(Version.parse("1.2.3")) 