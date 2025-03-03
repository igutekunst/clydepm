"""
Version resolution for Clyde package manager.
Implements version constraint resolution algorithms.
"""
from typing import List, Optional, Set, Tuple
from .version import Version
from .ranges import VersionRange, Constraint, Operator

class VersionResolver:
    """Resolves version constraints to find compatible versions."""
    
    def __init__(self, available_versions: List[Version]):
        """Initialize with list of available versions."""
        self.available_versions = sorted(available_versions)

    def _find_compatible_versions(self, constraints: VersionRange) -> List[Version]:
        """Find all versions that satisfy the given constraints.
        
        Args:
            constraints: Version range constraints
            
        Returns:
            List of compatible versions, sorted according to SemVer rules
        """
        compatible = []
        for version in self.available_versions:
            if constraints.matches(version):
                compatible.append(version)
        return sorted(compatible)

    def find_latest_compatible(self, constraints: VersionRange) -> Optional[Version]:
        """Find the latest version that satisfies the given constraints.
        
        Args:
            constraints: Version range constraints
            
        Returns:
            Latest compatible version, or None if no compatible version found
        """
        compatible = self._find_compatible_versions(constraints)
        return compatible[-1] if compatible else None

    def find_all_compatible(self, constraints: VersionRange) -> List[Version]:
        """Find all versions that satisfy the given constraints.
        
        Args:
            constraints: Version range constraints
            
        Returns:
            List of compatible versions, sorted according to SemVer rules
        """
        return self._find_compatible_versions(constraints)

    def find_minimal_compatible(self, constraints: VersionRange) -> Optional[Version]:
        """Find the minimal version that satisfies the given constraints.
        
        Args:
            constraints: Version range constraints
            
        Returns:
            Minimal compatible version, or None if no compatible version found
        """
        compatible = self._find_compatible_versions(constraints)
        return compatible[0] if compatible else None

    def find_maximal_compatible(self, constraints: VersionRange) -> Optional[Version]:
        """Find the maximal version that satisfies the given constraints.
        
        Args:
            constraints: Version range constraints
            
        Returns:
            Maximal compatible version, or None if no compatible version found
        """
        compatible = self._find_compatible_versions(constraints)
        return compatible[-1] if compatible else None

    def find_compatible_range(self, constraints: VersionRange) -> Optional[Tuple[Version, Version]]:
        """Find the range of compatible versions.
        
        Args:
            constraints: Version range constraints
            
        Returns:
            Tuple of (min_version, max_version), or None if no compatible versions found
        """
        compatible = self._find_compatible_versions(constraints)
        if not compatible:
            return None
        return (compatible[0], compatible[-1])
        
    @staticmethod
    def find_minimal_compatible_between(version_a: Version,
                                      version_b: Version) -> Optional[Version]:
        """Find the minimal version compatible with both versions.
        
        In semantic versioning, versions are compatible if they have
        the same major version number.
        
        Args:
            version_a: First version
            version_b: Second version
            
        Returns:
            Minimal compatible version, or None if versions are incompatible
        """
        if version_a.major != version_b.major:
            return None
            
        return min(version_a, version_b)
        
    @staticmethod
    def find_maximal_compatible_between(version_a: Version,
                                      version_b: Version) -> Optional[Version]:
        """Find the maximal version compatible with both versions.
        
        Args:
            version_a: First version
            version_b: Second version
            
        Returns:
            Maximal compatible version, or None if versions are incompatible
        """
        if version_a.major != version_b.major:
            return None
            
        return max(version_a, version_b)
        
    @staticmethod
    def find_compatible_range_between(version_a: Version,
                                    version_b: Version) -> Optional[VersionRange]:
        """Find a version range compatible with both versions.
        
        Args:
            version_a: First version
            version_b: Second version
            
        Returns:
            Compatible version range, or None if versions are incompatible
        """
        if version_a.major != version_b.major:
            return None
            
        min_version = min(version_a, version_b)
        max_version = max(version_a, version_b)
        
        return VersionRange(constraints=[
            Constraint(operator=Operator.GTE, version=min_version),
            Constraint(operator=Operator.LTE, version=max_version)
        ]) 