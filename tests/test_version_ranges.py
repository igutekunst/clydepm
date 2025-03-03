"""
Tests for version range handling.
"""
import pytest
from clydepm.core.version import Version, VersionRange, Constraint, Operator

def test_constraint_parsing():
    """Test parsing version constraints."""
    # Test exact version
    c = Constraint.parse("1.2.3")
    assert c.operator == Operator.EQ
    assert c.version == Version.parse("1.2.3")
    
    # Test operators
    operators = {
        "=1.2.3": Operator.EQ,
        ">1.2.3": Operator.GT,
        "<1.2.3": Operator.LT,
        ">=1.2.3": Operator.GTE,
        "<=1.2.3": Operator.LTE,
        "^1.2.3": Operator.CARET,
        "~1.2.3": Operator.TILDE,
    }
    
    for constraint_str, expected_op in operators.items():
        c = Constraint.parse(constraint_str)
        assert c.operator == expected_op
        assert c.version == Version.parse("1.2.3")
    
    # Test with spaces
    c = Constraint.parse("  >=  1.2.3  ")
    assert c.operator == Operator.GTE
    assert c.version == Version.parse("1.2.3")

def test_invalid_constraints():
    """Test parsing invalid constraints."""
    invalid_constraints = [
        "",  # Empty string
        ">>1.2.3",  # Invalid operator
        ">=",  # Missing version
        ">=1",  # Invalid version
        ">=1.2",  # Invalid version
        ">=a.b.c",  # Invalid version
    ]
    
    for constraint in invalid_constraints:
        with pytest.raises(ValueError):
            Constraint.parse(constraint)

def test_constraint_matching():
    """Test version constraint matching."""
    version = Version.parse("1.2.3")
    
    # Test exact version
    assert Constraint.parse("1.2.3").matches(version)
    assert not Constraint.parse("1.2.4").matches(version)
    
    # Test greater than
    assert Constraint.parse(">1.2.2").matches(version)
    assert not Constraint.parse(">1.2.3").matches(version)
    
    # Test less than
    assert Constraint.parse("<1.2.4").matches(version)
    assert not Constraint.parse("<1.2.3").matches(version)
    
    # Test greater than or equal
    assert Constraint.parse(">=1.2.3").matches(version)
    assert Constraint.parse(">=1.2.2").matches(version)
    assert not Constraint.parse(">=1.2.4").matches(version)
    
    # Test less than or equal
    assert Constraint.parse("<=1.2.3").matches(version)
    assert Constraint.parse("<=1.2.4").matches(version)
    assert not Constraint.parse("<=1.2.2").matches(version)
    
    # Test caret (compatible with)
    assert Constraint.parse("^1.2.0").matches(version)
    assert Constraint.parse("^1.0.0").matches(version)
    assert not Constraint.parse("^2.0.0").matches(version)
    assert not Constraint.parse("^1.3.0").matches(version)
    
    # Test tilde (compatible with minor)
    assert Constraint.parse("~1.2.0").matches(version)
    assert not Constraint.parse("~1.3.0").matches(version)
    assert not Constraint.parse("~2.0.0").matches(version)

def test_version_range_parsing():
    """Test parsing version ranges."""
    # Single constraint
    vr = VersionRange.parse(">=1.2.3")
    assert len(vr.constraints) == 1
    assert vr.constraints[0].operator == Operator.GTE
    assert vr.constraints[0].version == Version.parse("1.2.3")
    
    # Multiple constraints
    vr = VersionRange.parse(">=1.2.3 <2.0.0")
    assert len(vr.constraints) == 2
    assert vr.constraints[0].operator == Operator.GTE
    assert vr.constraints[0].version == Version.parse("1.2.3")
    assert vr.constraints[1].operator == Operator.LT
    assert vr.constraints[1].version == Version.parse("2.0.0")
    
    # Extra whitespace
    vr = VersionRange.parse("  >=1.2.3   <2.0.0  ")
    assert len(vr.constraints) == 2

def test_invalid_version_ranges():
    """Test parsing invalid version ranges."""
    invalid_ranges = [
        "",  # Empty string
        "  ",  # Only whitespace
        "invalid",  # Invalid constraint
        ">= 1.2",  # Invalid version
    ]
    
    for range_str in invalid_ranges:
        with pytest.raises(ValueError):
            VersionRange.parse(range_str)

def test_version_range_matching():
    """Test version range matching."""
    version = Version.parse("1.2.3")
    
    # Single constraint
    assert VersionRange.parse(">=1.2.3").matches(version)
    assert not VersionRange.parse(">=1.2.4").matches(version)
    
    # Multiple constraints
    assert VersionRange.parse(">=1.2.0 <2.0.0").matches(version)
    assert not VersionRange.parse(">=1.2.0 <1.2.3").matches(version)
    
    # Complex ranges
    assert VersionRange.parse("^1.2.0 >=1.2.3").matches(version)
    assert not VersionRange.parse("^1.2.0 >1.2.3").matches(version)
    
    # Common patterns
    assert VersionRange.parse("~1.2.0").matches(version)  # Minor version compatible
    assert VersionRange.parse("^1.0.0").matches(version)  # Major version compatible
    assert VersionRange.parse(">=1.2.0 <2.0.0").matches(version)  # Version range 

def test_version_range_with_prerelease():
    """Test version range matching with prereleases according to SemVer spec.
    
    Key rules from SemVer spec:
    1. Prerelease versions are lower precedence than normal versions
    2. Range comparisons (>, >=, <, <=) exclude prereleases by default
    3. Prereleases only included when explicitly specified in range
    """
    version = Version.parse("1.2.3-beta")
    
    # Exact version matches
    assert VersionRange.parse("1.2.3-beta").matches(version)  # Exact prerelease match
    assert not VersionRange.parse("1.2.3").matches(version)   # Normal version doesn't match prerelease
    assert not VersionRange.parse("1.2.3-alpha").matches(version)  # Different prerelease
    
    # Range behavior - prereleases excluded by default
    assert not VersionRange.parse(">=1.2.3").matches(version)  # Prerelease excluded by default
    assert not VersionRange.parse(">=1.2.2").matches(version)  # Prerelease excluded by default
    assert not VersionRange.parse("<1.2.4").matches(version)   # Prerelease excluded by default
    
    # Ranges that explicitly include prereleases
    assert VersionRange.parse(">=1.2.3-0").matches(version)  # Explicitly includes prereleases
    assert VersionRange.parse(">=1.2.3-alpha").matches(version)  # Explicitly includes prereleases
    assert not VersionRange.parse(">=1.2.4-0").matches(version)  # Version too high
    
    # Multiple constraints
    assert VersionRange.parse(">=1.2.3-0 <1.2.4").matches(version)  # Explicitly includes prereleases
    assert not VersionRange.parse(">=1.2.3 <1.2.4").matches(version)  # Prereleases excluded by default
    
    # Tilde and caret ranges should also exclude prereleases by default
    assert not VersionRange.parse("~1.2.3").matches(version)  # Tilde excludes prereleases
    assert not VersionRange.parse("^1.2.0").matches(version)  # Caret excludes prereleases
    
    # But should include them when explicitly specified
    assert VersionRange.parse("~1.2.3-0").matches(version)  # Tilde with explicit prerelease
    assert VersionRange.parse("^1.2.0-0").matches(version)  # Caret with explicit prerelease

    