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
        
        Args:
            version: The version to check
            allow_prerelease: Whether to allow prerelease versions to match
            
        Returns:
            bool: True if the version matches the constraint
        """
        print(f"Constraint.matches: {self.operator} {self.version} vs {version} (allow_prerelease={allow_prerelease})")

        # For exact matches, compare everything including prerelease
        if self.operator == Operator.EQ:
            result = version == self.version
            print(f"  Exact match: {result}")
            return result

        # For range matches, first check if base version matches
        base_version = version.without_prerelease()
        base_constraint = self.version.without_prerelease()

        # Check if base version matches the constraint
        matches = False
        if self.operator == Operator.GT:
            matches = base_version > base_constraint
            print(f"  GT: {matches}")
        elif self.operator == Operator.LT:
            matches = base_version < base_constraint
            print(f"  LT: {matches}")
        elif self.operator == Operator.GTE:
            matches = base_version >= base_constraint
            print(f"  GTE: {matches}")
        elif self.operator == Operator.LTE:
            matches = base_version <= base_constraint
            print(f"  LTE: {matches}")
        elif self.operator == Operator.CARET:
            # ^1.2.3 means >=1.2.3 <2.0.0
            # ^0.2.3 means >=0.2.3 <0.3.0
            # ^0.0.3 means >=0.0.3 <0.0.4
            if base_constraint.major > 0:
                matches = (base_version >= base_constraint and 
                         base_version.major == base_constraint.major)
            elif base_constraint.minor > 0:
                matches = (base_version >= base_constraint and
                         base_version.major == base_constraint.major and
                         base_version.minor == base_constraint.minor)
            else:
                matches = (base_version >= base_constraint and
                         base_version.major == base_constraint.major and
                         base_version.minor == base_constraint.minor and
                         base_version.patch == base_constraint.patch)
            print(f"  CARET: {matches}")
        elif self.operator == Operator.TILDE:
            # ~1.2.3 means >=1.2.3 <1.3.0
            matches = (base_version >= base_constraint and
                      base_version.major == base_constraint.major and
                      base_version.minor == base_constraint.minor)
            print(f"  TILDE: {matches}")

        if not matches:
            print(f"  Base version matches: False")
            return False

        print(f"  Base version matches: True")

        # If version is a prerelease, it can only match if:
        # 1. The constraint has a prerelease OR allow_prerelease is True
        # 2. The base version matches
        if version.prerelease:
            has_matching_prerelease = self.version.prerelease is not None
            print(f"  Has matching prerelease: {has_matching_prerelease}")
            if not (has_matching_prerelease or allow_prerelease):
                return False

            # For range operators, check if version satisfies the constraint
            if self.operator in (Operator.GT, Operator.GTE):
                result = version >= self.version
            elif self.operator in (Operator.LT, Operator.LTE):
                result = version <= self.version
            elif self.operator == Operator.CARET:
                if self.version.major > 0:
                    result = (version >= self.version and 
                            version.major == self.version.major)
                elif self.version.minor > 0:
                    result = (version >= self.version and
                            version.major == self.version.major and
                            version.minor == self.version.minor)
                else:
                    result = (version >= self.version and
                            version.major == self.version.major and
                            version.minor == self.version.minor and
                            version.patch == self.version.patch)
            elif self.operator == Operator.TILDE:
                result = (version >= self.version and
                         version.major == self.version.major and
                         version.minor == self.version.minor)
            print(f"  Final result: {result}")
            return result

        return True

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
        1. A prerelease version has lower precedence than its associated normal version
        2. For exact matches, compare everything including prerelease
        3. For range matches:
           - If version is a prerelease and no constraint has a prerelease, reject
           - Otherwise compare using the operators

        Args:
            version: Version to check

        Returns:
            True if version matches range
        """
        print(f"\nVersionRange.matches: {version}")
        print(f"  Constraints: {[f'{c.operator} {c.version}' for c in self.constraints]}")

        # If version is a prerelease, check if any constraint has a prerelease
        if version.prerelease:
            print("  Version is prerelease")
            has_prerelease = any(c.version.prerelease is not None for c in self.constraints)
            if not has_prerelease:
                return False

        # Check all constraints
        for c in self.constraints:
            # If any constraint has a prerelease, allow prerelease matching
            allow_prerelease = any(c.version.prerelease is not None for c in self.constraints)
            if not c.matches(version, allow_prerelease):
                return False

        return True 