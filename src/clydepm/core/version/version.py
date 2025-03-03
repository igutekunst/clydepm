"""
Version handling for Clyde package manager.
Implements semantic versioning (SemVer) specification.
"""
from dataclasses import dataclass
from typing import Optional, Tuple, List
import re

@dataclass(frozen=True)
class Version:
    """Represents a semantic version number."""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None

    _version_re = re.compile(
        r"^(?P<major>0|[1-9]\d*)"
        r"\.(?P<minor>0|[1-9]\d*)"
        r"\.(?P<patch>0|[1-9]\d*)"
        r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
        r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
    )

    @classmethod
    def parse(cls, version_str: str) -> "Version":
        """Parse a version string into a Version object.
        
        Args:
            version_str: Version string to parse (e.g. "1.2.3-beta+build.123")
            
        Returns:
            Version object
            
        Raises:
            ValueError: If version string is invalid
        """
        match = cls._version_re.match(version_str)
        if not match:
            raise ValueError(f"Invalid version string: {version_str}")
            
        parts = match.groupdict()
        return cls(
            major=int(parts["major"]),
            minor=int(parts["minor"]),
            patch=int(parts["patch"]),
            prerelease=parts["prerelease"],
            build=parts["build"]
        )
        
    def __str__(self) -> str:
        """Convert version to string."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version

    def _compare_prerelease(self, other: "Version") -> int:
        """Compare prerelease identifiers.
        
        According to SemVer spec:
        1. A pre-release version has lower precedence than a normal version
        2. Identifiers consisting of only digits are compared numerically
        3. Identifiers with letters or hyphens are compared lexically
        4. Numeric identifiers always have lower precedence than non-numeric identifiers
        
        Returns:
            -1 if self < other
            0 if self == other
            1 if self > other
        """
        if not self.prerelease and not other.prerelease:
            return 0
        if not self.prerelease:
            return 1
        if not other.prerelease:
            return -1
            
        self_parts = self.prerelease.split('.')
        other_parts = other.prerelease.split('.')
        
        for self_part, other_part in zip(self_parts, other_parts):
            # If both parts are numeric, compare numerically
            self_is_num = self_part.isdigit()
            other_is_num = other_part.isdigit()
            
            if self_is_num and other_is_num:
                self_num = int(self_part)
                other_num = int(other_part)
                if self_num != other_num:
                    return -1 if self_num < other_num else 1
            else:
                # Non-numeric parts are compared lexically
                if self_part != other_part:
                    return -1 if self_part < other_part else 1
                
        # If we get here, all parts were equal up to the shortest length
        # The shorter one has lower precedence
        if len(self_parts) != len(other_parts):
            return -1 if len(self_parts) < len(other_parts) else 1
        return 0
        
    def _compare_key(self) -> Tuple[int, int, int]:
        """Get comparison key for version sorting.
        
        Note: Build metadata is ignored in comparisons as per SemVer spec.
        """
        return (self.major, self.minor, self.patch)
        
    def __lt__(self, other: "Version") -> bool:
        """Compare versions."""
        if not isinstance(other, Version):
            return NotImplemented
            
        # Compare version numbers first
        self_key = (self.major, self.minor, self.patch)
        other_key = (other.major, other.minor, other.patch)
        
        if self_key != other_key:
            return self_key < other_key
            
        # If version numbers are equal, compare prerelease
        return self._compare_prerelease(other) < 0
        
    def __le__(self, other: "Version") -> bool:
        """Compare versions."""
        if not isinstance(other, Version):
            return NotImplemented
            
        # Compare version numbers first
        self_key = (self.major, self.minor, self.patch)
        other_key = (other.major, other.minor, other.patch)
        
        if self_key != other_key:
            return self_key < other_key
            
        # If version numbers are equal, compare prerelease
        return self._compare_prerelease(other) <= 0
        
    def __gt__(self, other: "Version") -> bool:
        """Compare versions."""
        if not isinstance(other, Version):
            return NotImplemented
            
        # Compare version numbers first
        self_key = (self.major, self.minor, self.patch)
        other_key = (other.major, other.minor, other.patch)
        
        if self_key != other_key:
            return self_key > other_key
            
        # If version numbers are equal, compare prerelease
        return self._compare_prerelease(other) > 0
        
    def __ge__(self, other: "Version") -> bool:
        """Compare versions."""
        if not isinstance(other, Version):
            return NotImplemented
            
        # Compare version numbers first
        self_key = (self.major, self.minor, self.patch)
        other_key = (other.major, other.minor, other.patch)
        
        if self_key != other_key:
            return self_key > other_key
            
        # If version numbers are equal, compare prerelease
        return self._compare_prerelease(other) >= 0
        
    def __eq__(self, other: object) -> bool:
        """Check version equality.
        
        Note: Build metadata is ignored in equality checks as per SemVer spec.
        """
        if not isinstance(other, Version):
            return NotImplemented
            
        # Compare version numbers first
        self_key = (self.major, self.minor, self.patch)
        other_key = (other.major, other.minor, other.patch)
        
        if self_key != other_key:
            return False
            
        # If version numbers are equal, compare prerelease
        return self._compare_prerelease(other) == 0
        
    def is_compatible_with(self, other: "Version") -> bool:
        """Check if this version is compatible with another version.
        
        In semantic versioning, versions with the same major version
        are considered compatible.
        
        Args:
            other: Version to check compatibility with
            
        Returns:
            True if versions are compatible
        """
        return self.major == other.major 