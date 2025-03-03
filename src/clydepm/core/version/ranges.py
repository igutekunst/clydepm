"""
Version range handling for Clyde package manager.
Implements version constraint parsing and matching.
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple
import re

from .version import Version

class Operator(Enum):
    """Version comparison operators."""
    EQ = "="  # Exactly equal
    GT = ">"  # Greater than
    LT = "<"  # Less than
    GTE = ">="  # Greater than or equal
    LTE = "<="  # Less than or equal
    CARET = "^"  # Compatible with (same major version)
    TILDE = "~"  # Compatible with (same minor version)

@dataclass(frozen=True)
class Constraint:
    """A single version constraint."""
    operator: Operator
    version: Version

    _constraint_re = re.compile(
        r"^(?P<operator>[=<>~^]|>=|<=)?\s*(?P<version>\d+\.\d+\.\d+(?:-[0-9A-Za-z-.]+)?(?:\+[0-9A-Za-z-.]+)?)$"
    )

    @classmethod
    def parse(cls, constraint_str: str) -> "Constraint":
        """Parse a constraint string into a Constraint object.
        
        Args:
            constraint_str: Constraint string (e.g. ">=1.2.3", "^2.0.0")
            
        Returns:
            Constraint object
            
        Raises:
            ValueError: If constraint string is invalid
        """
        match = cls._constraint_re.match(constraint_str.strip())
        if not match:
            raise ValueError(f"Invalid constraint string: {constraint_str}")
            
        parts = match.groupdict()
        operator = parts["operator"] or "="  # Default to exact version if no operator
        
        return cls(
            operator=Operator(operator),
            version=Version.parse(parts["version"])
        )
        
    def _get_base_version(self, version: Version) -> Tuple[int, int, int]:
        """Get the base version without prerelease or build metadata."""
        return (version.major, version.minor, version.patch)
        
    def _compare_prerelease_identifiers(self, ver_a: Version, ver_b: Version) -> bool:
        """Compare prerelease identifiers according to SemVer rules.
        
        Returns True if ver_a has precedence over ver_b.
        """
        if not ver_a.prerelease and not ver_b.prerelease:
            return True
        if not ver_a.prerelease and ver_b.prerelease:
            return True
        if ver_a.prerelease and not ver_b.prerelease:
            return False
            
        # Both have prereleases - compare each identifier
        a_ids = ver_a.prerelease.split('.')
        b_ids = ver_b.prerelease.split('.')
        
        for a_id, b_id in zip(a_ids, b_ids):
            a_is_num = a_id.isdigit()
            b_is_num = b_id.isdigit()
            
            # If both numeric, compare numerically
            if a_is_num and b_is_num:
                if int(a_id) != int(b_id):
                    return int(a_id) >= int(b_id)
            # If both non-numeric, compare lexically
            elif not a_is_num and not b_is_num:
                if a_id != b_id:
                    return a_id >= b_id
            # Mixed - numeric has lower precedence
            else:
                return not a_is_num
                
        # All equal up to the shortest - longer one has precedence
        return len(a_ids) >= len(b_ids)
        
    def _compare_versions(self, version: Version) -> bool:
        """Compare versions based on operator."""
        if self.operator == Operator.GT:
            return version > self.version
        elif self.operator == Operator.LT:
            return version < self.version
        elif self.operator == Operator.GTE:
            return version >= self.version
        elif self.operator == Operator.LTE:
            return version <= self.version
        elif self.operator == Operator.CARET:
            # Compatible with same major version
            return (version.major == self.version.major and 
                   version >= self.version)
        elif self.operator == Operator.TILDE:
            # Compatible with same minor version
            return (version.major == self.version.major and
                   version.minor == self.version.minor and
                   version >= self.version)
        return False
        
    def matches(self, version: Version, allow_prerelease: bool = False) -> bool:
        """Check if a version matches this constraint.
        
        According to SemVer spec:
        1. A prerelease version has lower precedence than its associated normal version
        2. For exact matches, compare everything including prerelease
        3. For range matches:
           - If version is a prerelease and we're not allowing them, reject
           - Otherwise compare using the operator
        
        Args:
            version: Version to check
            allow_prerelease: Whether to allow prerelease versions
            
        Returns:
            True if version matches constraint
        """
        print(f"Constraint.matches: {self.operator} {self.version} vs {version} (allow_prerelease={allow_prerelease})")
        
        # Handle exact version match first
        if self.operator == Operator.EQ:
            # For exact matches, compare everything including prerelease
            result = (version.major == self.version.major and
                     version.minor == self.version.minor and
                     version.patch == self.version.patch and
                     version.prerelease == self.version.prerelease)
            print(f"  Exact match: {result}")
            return result
            
        # If version is a prerelease and we're not allowing them, reject
        if version.prerelease and not (self.version.prerelease or allow_prerelease):
            print("  Prerelease not allowed: False")
            return False
            
        # For range matches, compare base versions first
        base_version = Version(
            major=version.major,
            minor=version.minor,
            patch=version.patch
        )
        base_constraint = Version(
            major=self.version.major,
            minor=self.version.minor,
            patch=self.version.patch
        )
        
        # Compare using the operator
        if self.operator == Operator.GT:
            result = base_version > base_constraint
            print(f"  GT: {result}")
            return result
        elif self.operator == Operator.LT:
            result = base_version < base_constraint
            print(f"  LT: {result}")
            return result
        elif self.operator == Operator.GTE:
            result = base_version >= base_constraint
            print(f"  GTE: {result}")
            return result
        elif self.operator == Operator.LTE:
            result = base_version <= base_constraint
            print(f"  LTE: {result}")
            return result
        elif self.operator == Operator.CARET:
            # Compatible with same major version
            result = (base_version.major == base_constraint.major and 
                     base_version >= base_constraint)
            print(f"  CARET: {result}")
            return result
        elif self.operator == Operator.TILDE:
            # Compatible with same minor version
            result = (base_version.major == base_constraint.major and
                     base_version.minor == base_constraint.minor and
                     base_version >= base_constraint)
            print(f"  TILDE: {result}")
            return result
        return False

@dataclass(frozen=True)
class VersionRange:
    """A version range composed of one or more constraints."""
    constraints: List[Constraint]

    @classmethod
    def parse(cls, range_str: str) -> "VersionRange":
        """Parse a version range string into a VersionRange object.
        
        Args:
            range_str: Range string (e.g. ">=1.2.3 <2.0.0", "^2.0.0")
            
        Returns:
            VersionRange object
            
        Raises:
            ValueError: If range string is invalid
        """
        constraints = [
            Constraint.parse(c.strip())
            for c in range_str.split()
            if c.strip()
        ]
        if not constraints:
            raise ValueError("Empty version range")
        return cls(constraints=constraints)
        
    def matches(self, version: Version) -> bool:
        """Check if a version matches this range.
        
        According to SemVer spec:
        1. A prerelease version can only satisfy a range if:
           - The range explicitly includes a prerelease version with the same major.minor.patch
           - Or the range includes the base version of the prerelease
           - Or we're doing an exact version match
        2. Otherwise, prerelease versions should be ignored
        """
        print(f"\nVersionRange.matches: {version}")
        print(f"  Constraints: {[f'{c.operator} {c.version}' for c in self.constraints]}")
        
        # For exact version matches, check first constraint only
        if len(self.constraints) == 1 and self.constraints[0].operator == Operator.EQ:
            result = self.constraints[0].matches(version)
            print(f"  Exact match: {result}")
            return result
            
        # If version is a prerelease, check if any constraint explicitly includes it
        if version.prerelease:
            print("  Version is prerelease")
            
            # Create base version without prerelease
            base_version = Version(
                major=version.major,
                minor=version.minor,
                patch=version.patch
            )
            
            # First check if base version satisfies all constraints
            base_matches = all(c.matches(base_version) for c in self.constraints)
            print(f"  Base version matches: {base_matches}")
            if not base_matches:
                return False
                
            # Then check if any constraint has a prerelease with same base version
            has_matching_prerelease = False
            for c in self.constraints:
                if (c.version.prerelease and
                    c.version.major == version.major and
                    c.version.minor == version.minor and
                    c.version.patch == version.patch):
                    has_matching_prerelease = True
                    break
                    
            print(f"  Has matching prerelease: {has_matching_prerelease}")
            
            # If no matching prerelease, check if base version matches all constraints
            if not has_matching_prerelease:
                # If base version matches all constraints, allow the prerelease
                result = all(c.matches(version, allow_prerelease=True) for c in self.constraints)
                print(f"  Final result: {result}")
                return result
                
            # If has matching prerelease, check all constraints with prerelease allowed
            result = all(c.matches(version, allow_prerelease=True) for c in self.constraints)
            print(f"  Final result: {result}")
            return result
                
        # For non-prerelease versions, just check all constraints
        result = all(c.matches(version) for c in self.constraints)
        print(f"  Non-prerelease result: {result}")
        return result 