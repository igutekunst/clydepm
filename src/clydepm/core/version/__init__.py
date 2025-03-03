"""
Version handling for Clyde package manager.
"""

from .version import Version
from .ranges import VersionRange, Constraint, Operator
from .resolver import VersionResolver

__all__ = [
    'Version',
    'VersionRange',
    'Constraint',
    'Operator',
    'VersionResolver'
] 