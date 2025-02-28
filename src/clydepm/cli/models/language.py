"""
Language enum for Clydepm.
"""
from enum import Enum


class Language(str, Enum):
    """Programming language for the package."""
    C = "c"
    CPP = "cpp"
    CXX = "cxx"
    CPLUSPLUS = "c++"
    
    @classmethod
    def from_str(cls, s: str) -> "Language":
        """Convert string to Language enum."""
        s = s.lower()
        if s in ("cpp", "cxx", "c++"):
            return cls.CPP
        elif s == "c":
            return cls.C
        else:
            raise ValueError(f"Unknown language: {s}")
            
    def __str__(self) -> str:
        """Convert Language enum to string."""
        if self == Language.CPP:
            return "C++"
        return self.value.upper() 