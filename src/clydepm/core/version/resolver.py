"""
Version resolution for Clyde package manager.
Implements version constraint resolution algorithms.
"""
from typing import List, Optional, Set
from .version import Version
from .ranges import VersionRange

class VersionResolver:
    """Resolves version constraints to find compatible versions."""
    
    @staticmethod
    def find_latest_compatible(available_versions: List[Version],
                             constraints: VersionRange) -> Optional[Version]:
        """Find the latest version that satisfies all constraints.
        
        Args:
            available_versions: List of available versions
            constraints: Version range constraints
            
        Returns:
            Latest compatible version, or None if no compatible version found
        """
        compatible_versions = [
            v for v in available_versions
            if constraints.matches(v)
        ]
        
        return max(compatible_versions) if compatible_versions else None
        
    @staticmethod
    def find_all_compatible(available_versions: List[Version],
                          constraints: VersionRange) -> List[Version]:
        """Find all versions that satisfy the constraints.
        
        Args:
            available_versions: List of available versions
            constraints: Version range constraints
            
        Returns:
            List of compatible versions, sorted newest to oldest.
            According to SemVer:
            1. Sort by major.minor.patch numerically
            2. A prerelease version has lower precedence than its associated normal version
            3. Prerelease versions are sorted by their identifiers
        """
        # Filter compatible versions and sort in descending order
        compatible_versions = [
            v for v in available_versions
            if constraints.matches(v)
        ]
        print("available_versions", available_versions)
        print("constraints", constraints)
        print("compatible_versions", compatible_versions)
        print("sorted", sorted(compatible_versions, reverse=True))
        return sorted(compatible_versions, reverse=True)
        
    @staticmethod
    def find_minimal_compatible(version_a: Version,
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
    def find_maximal_compatible(version_a: Version,
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
    def find_compatible_range(version_a: Version,
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
        
        from .ranges import Constraint, Operator
        return VersionRange(constraints=[
            Constraint(operator=Operator.GTE, version=min_version),
            Constraint(operator=Operator.LTE, version=max_version)
        ]) 