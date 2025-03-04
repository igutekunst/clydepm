from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, constr, validator
from ..version.version import Version

class CompilerFlags(BaseModel):
    """Compiler flags configuration."""
    gcc: Optional[str] = None
    gxx: Optional[str] = None
    clang: Optional[str] = None
    clangxx: Optional[str] = None

class PackageConfig(BaseModel):
    """Package configuration schema."""
    name: constr(pattern=r'^(?:@[a-zA-Z0-9_-]+/)?[a-zA-Z0-9_-]+$')
    version: str
    type: str = Field(default="library", pattern="^(library|application|foreign)$")
    language: str = Field(pattern="^(c|cpp|cxx|c\\+\\+)$")
    sources: List[str]
    cflags: Optional[CompilerFlags] = None
    requires: Dict[str, str] = Field(default_factory=dict)
    dev_requires: Dict[str, str] = Field(default_factory=dict)
    traits: Dict[str, str] = Field(default_factory=dict)
    variants: Dict[str, Dict[str, Union[str, Dict[str, str]]]] = Field(default_factory=dict)

    @validator('version')
    def validate_version(cls, v):
        """Validate version is proper SemVer."""
        try:
            Version.parse(v)
            return v
        except ValueError as e:
            raise ValueError(f"Invalid version format: {e}")

    @validator('requires', 'dev_requires')
    def validate_dependencies(cls, v):
        """Validate dependency specifications."""
        for name, spec in v.items():
            if not name:
                raise ValueError("Dependency name cannot be empty")
            
            # Handle local dependencies
            if spec.startswith("local:"):
                if len(spec) <= 6:  # Just "local:"
                    raise ValueError(f"Invalid local dependency path for {name}")
                continue

            # Handle version specs
            if spec.startswith(("^", "~", "=", ">")):
                try:
                    # Strip operator and validate version
                    version = spec[1:] if spec[0] in ("^", "~", "=", ">") else spec
                    Version.parse(version)
                except ValueError as e:
                    raise ValueError(f"Invalid version spec for {name}: {e}")
            else:
                raise ValueError(f"Invalid dependency specification for {name}: {spec}")
        return v

    class Config:
        extra = "forbid"  # Forbid extra fields not in schema 