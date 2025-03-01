"""
Core package management functionality for Clydepm.
"""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set
import hashlib
import json
import yaml
from pydantic import BaseModel, Field


class PackageType(str, Enum):
    """Type of package being built."""
    LIBRARY = "library"
    APPLICATION = "application"
    FOREIGN = "foreign"  # For packages with custom build systems
    
    @classmethod
    def from_str(cls, value: str) -> "PackageType":
        """Create PackageType from string."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid package type: {value}")


# Custom YAML representer for PackageType
def package_type_representer(dumper: yaml.Dumper, data: PackageType) -> yaml.ScalarNode:
    """Convert PackageType to YAML."""
    return dumper.represent_str(data.value)

# Register the representer
yaml.add_representer(PackageType, package_type_representer)


@dataclass
class CompilerInfo:
    """Information about the compiler."""
    name: str
    version: str
    target: str


@dataclass
class BuildMetadata:
    """Metadata for binary package linking."""
    compiler: CompilerInfo
    cflags: List[str] = field(default_factory=list)
    includes: List[Path] = field(default_factory=list)
    libs: List[Path] = field(default_factory=list)
    traits: Dict[str, str] = field(default_factory=dict)
    
    def get_hash(self) -> str:
        """Generate hash based on build configuration."""
        metadata = {
            "compiler": {
                "name": self.compiler.name,
                "version": self.compiler.version,
                "target": self.compiler.target,
            },
            "cflags": sorted(self.cflags),
            "traits": self.traits
        }
        return hashlib.sha256(
            json.dumps(metadata, sort_keys=True).encode()
        ).hexdigest()


class Package:
    """
    Core package class that handles both source and binary packages.
    """
    def __init__(
        self,
        path: Path,
        package_type: Optional[PackageType] = None,
        form: str = "source"
    ):
        self.path = Path(path)
        self.form = form
        self._config = self._load_config()
        self._traits = {}  # Initialize traits dictionary
        
        # Handle package type from config
        config_type = self._config.get("type", "library")
        try:
            self.package_type = PackageType.from_str(str(config_type))
        except ValueError as e:
            raise ValueError(f"Invalid package type in config: {config_type}") from e
            
        if package_type:
            self.package_type = package_type
            
        self.build_metadata: Optional[BuildMetadata] = None
        
    def _load_config(self) -> Dict:
        """Load package configuration from yaml file."""
        config_file = self.path / "config.yaml"
        if not config_file.exists():
            config_file = self.path / "descriptor.yaml"
            
        if not config_file.exists():
            raise FileNotFoundError(
                f"No config.yaml or descriptor.yaml found in {self.path}"
            )
            
        with open(config_file) as f:
            return yaml.safe_load(f)
            
    def save_config(self) -> None:
        """Save package configuration to yaml file."""
        config = self._config.copy()
        
        # Ensure we save only simple types
        config["type"] = self.package_type.value
        
        with open(self.path / "config.yaml", "w") as f:
            yaml.dump(config, f, sort_keys=False, default_flow_style=False)
    
    @property
    def name(self) -> str:
        """Get package name."""
        return self._config["name"]
    
    @property
    def version(self) -> str:
        """Get package version."""
        return self._config["version"]
    
    def get_dependencies(self) -> Dict[str, str]:
        """Get package dependencies with version specs."""
        deps = {}
        if "requires" in self._config and self._config["requires"]:
            deps.update(self._config["requires"])
            
        # Handle variant-specific dependencies
        for variant in self._config.get("variants", []):
            for variant_name, variant_config in variant.items():
                if "requires" in variant_config and variant_config["requires"]:
                    deps.update(variant_config["requires"])
                    
        return deps

    def get_runtime_dependencies(self) -> List["Package"]:
        """Get all runtime dependencies."""
        return self.get_local_dependencies()    
    
    def get_local_dependencies(self) -> List["Package"]:
        """Get all local dependencies."""
        packages = []
        
        # Get dependencies from config
        deps = self.get_dependencies()
        for name, config in deps.items():
            if isinstance(config, dict) and config.get("version") == "local":
                # Handle local dependency with local-path
                local_path = config.get("local-path")
                if local_path:
                    dep_path = (self.path / local_path).resolve()
                    if dep_path.exists() and (dep_path / "config.yaml").exists():
                        packages.append(Package(dep_path))
                        
        # Also check deps directory for other local dependencies
        deps_dir = self.path / "deps"
        if deps_dir.exists():
            for pkg_dir in deps_dir.iterdir():
                if pkg_dir.is_dir() and (pkg_dir / "config.yaml").exists():
                    packages.append(Package(pkg_dir))
                    
        return packages
        
    def get_all_dependency_includes(self) -> List[Path]:
        """Get include paths from all local dependencies."""
        includes = []
        for dep in self.get_local_dependencies():
            includes.extend(dep._get_includes())
            # Recursively get includes from nested dependencies
            includes.extend(dep.get_all_dependency_includes())
        return includes
        
    def get_all_dependency_libs(self) -> List[Path]:
        """Get library paths from all local dependencies."""
        libs = []
        for dep in self.get_local_dependencies():
            if dep.package_type == PackageType.LIBRARY:
                # Add the library itself
                lib_path = dep.get_output_path()
                if lib_path.exists():
                    libs.append(lib_path)
            # Recursively get libraries from nested dependencies
            libs.extend(dep.get_all_dependency_libs())
        return libs
    
    def get_source_files(self) -> List[Path]:
        """Get all source files for the package."""
        sources = []
        
        # Get sources from src directory
        src_dir = self.path / "src"
        if src_dir.exists():
            sources.extend(src_dir.glob("*.c"))
            sources.extend(src_dir.glob("*.cpp"))
            
        # Get sources from variants
        for variant in self._config.get("variants", []):
            variant_dir = self.path / list(variant.keys())[0]
            if variant_dir.exists():
                sources.extend(variant_dir.glob("*.c"))
                sources.extend(variant_dir.glob("*.cpp"))
                
        return sources  # Return the collected source files
    
    def create_build_metadata(self, compiler_info: CompilerInfo) -> BuildMetadata:
        """Create build metadata for binary packages."""
        return BuildMetadata(
            compiler=compiler_info,
            cflags=self._get_cflags(),
            includes=self._get_includes(),
            libs=self._get_libs(),
            traits=self._get_traits()
        )
    
    def _get_cflags(self) -> List[str]:
        """Get compiler flags for the package."""
        cflags = []
        
        # Get global cflags
        if "cflags" in self._config and "gcc" in self._config["cflags"]:
            cflags.extend(self._config["cflags"]["gcc"].split())
            
        # Get variant-specific cflags
        for variant in self._config.get("variants", []):
            for variant_config in variant.values():
                if "cflags" in variant_config and "gcc" in variant_config["cflags"]:
                    cflags.extend(variant_config["cflags"]["gcc"].split())
        
        # Add include paths for own headers
        for include_path in self._get_includes():
            cflags.append(f"-I{include_path}")
            
        # Add include paths for all dependencies
        for include_path in self.get_all_dependency_includes():
            cflags.append(f"-I{include_path}")
                    
        return cflags
    
    def _get_includes(self) -> List[Path]:
        """Get include paths for the package."""
        includes = [
            self.path / "include",
            self.path / "private_include"
        ]
        return [p for p in includes if p.exists()]
    
    def _get_libs(self) -> List[Path]:
        """Get library paths for the package."""
        libs = []
        # Add own lib directory
        lib_dir = self.path / "lib"
        if lib_dir.exists():
            libs.append(lib_dir)
        # Add dependency libraries
        libs.extend(self.get_all_dependency_libs())
        return libs
    
    def _get_traits(self) -> Dict[str, str]:
        """Get package traits."""
        traits = self._config.get("traits", {}).copy()
        traits.update(self._traits)  # Instance traits override config traits
        return traits

    def get_build_dir(self) -> Path:
        """Get the build directory for this package."""
        return self.path / "build"

    def get_output_path(self) -> Path:
        """Get the output path for this package's artifacts."""
        if self.package_type == PackageType.LIBRARY:
            return self.path / "lib" / f"lib{self.name}.a"
        else:
            return self.path / "bin" / self.name 