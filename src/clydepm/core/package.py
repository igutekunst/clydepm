"""
Core package management functionality for Clydepm.
"""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import hashlib
import json
import yaml
from pydantic import BaseModel, Field, ValidationError
from .version.version import Version
from .config.schema import PackageConfig


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
    ldflags: List[str] = field(default_factory=list)  # Add ldflags for linking
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
            "ldflags": sorted(self.ldflags),  # Include ldflags in hash
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
        
        # Validate config using schema
        try:
            self._validated_config = PackageConfig(**self._config)
        except ValidationError as e:
            raise ValueError(f"Invalid package.yml configuration:\n{e}")
        
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
        config_file = self.path / "package.yml"
        if not config_file.exists():
            config_file = self.path / "package.yaml"
            
        if not config_file.exists():
            raise FileNotFoundError(
                f"No package.yml or package.yaml found in {self.path}"
            )
            
        with open(config_file) as f:
            return yaml.safe_load(f)
            
    def save_config(self) -> None:
        """Save package configuration to yaml file."""
        config = self._config.copy()
        
        # Ensure we save only simple types
        config["type"] = self.package_type.value
        
        # Validate before saving
        try:
            PackageConfig(**config)
        except ValidationError as e:
            raise ValueError(f"Invalid package configuration:\n{e}")
        
        with open(self.path / "package.yml", "w") as f:
            yaml.dump(config, f, sort_keys=False, default_flow_style=False)
    
    @property
    def name(self) -> str:
        """Get full package name including organization if present."""
        return self._validated_config.name
    
    @property
    def version(self) -> str:
        """Get package version."""
        return self._validated_config.version
    
    def get_version_object(self) -> Version:
        """Get package version as Version object."""
        return Version.parse(self.version)
    
    def is_compatible_with(self, other_version: str) -> bool:
        """Check if this package version is compatible with another version.
        
        Args:
            other_version: Version string to check compatibility with
            
        Returns:
            True if versions are compatible according to SemVer rules
        """
        try:
            other = Version.parse(other_version)
            return self.get_version_object().is_compatible_with(other)
        except ValueError:
            return False
    
    def get_dependencies(self) -> Dict[str, str]:
        """Get package dependencies with version specs."""
        deps = {}
        if self._validated_config.requires:
            deps.update(self._validated_config.requires)
            
        # Handle variant-specific dependencies
        for variant in self._validated_config.variants.values():
            if "requires" in variant and variant["requires"]:
                deps.update(variant["requires"])
                    
        return deps

    def get_runtime_dependencies(self) -> List["Package"]:
        """Get all runtime dependencies."""
        return self.get_local_dependencies()    
    
    def get_local_dependencies(self) -> List["Package"]:
        """Get all local dependencies."""
        packages = []
        
        # Get dependencies from config
        deps = self.get_dependencies()
        for name, spec in deps.items():
            if isinstance(spec, str):
                if spec.startswith("local:"):
                    # Handle local dependency with path
                    local_path = spec[6:]  # Remove "local:" prefix
                    dep_path = (self.path / local_path).resolve()
                    if dep_path.exists() and (dep_path / "package.yml").exists():
                        packages.append(Package(dep_path))
                    else:
                        raise ValueError(f"Local dependency {name} not found at {dep_path}")
                    
        return packages
        
    def get_remote_dependencies(self) -> List["Package"]:
        """Get all remote dependencies."""
        packages = []
        
        # Get dependencies from config
        deps = self.get_dependencies()
        for name, spec in deps.items():
            if isinstance(spec, str):
                if not spec.startswith("local:"):
                    # This is a remote dependency, should be in deps/
                    dep_path = self.path / "deps" / name
                    if dep_path.exists() and (dep_path / "package.yml").exists():
                        packages.append(Package(dep_path))
                    
        return packages

    def get_all_dependencies(self) -> List["Package"]:
        """Get all dependencies (both local and remote)."""
        deps = []
        deps.extend(self.get_local_dependencies())
        deps.extend(self.get_remote_dependencies())
        return deps
        
    def get_all_dependency_includes(self) -> List[Path]:
        """Get include paths from all dependencies."""
        includes = []
        for dep in self.get_all_dependencies():
            # Only add the public include directory
            dep_include = dep.path / "include"
            if dep_include.exists():
                includes.append(dep_include)
                # Also add the package-specific include directory
                pkg_include = dep_include / dep.name
                if pkg_include.exists():
                    includes.append(pkg_include)
            # Recursively get includes from nested dependencies
            includes.extend(dep.get_all_dependency_includes())
        return includes
        
    def get_all_dependency_libs(self) -> Tuple[List[Path], List[str]]:
        """Get library paths and flags from all dependencies.
        
        Returns:
            Tuple of (library paths, linker flags)
        """
        libs = []
        ldflags = []
        for dep in self.get_all_dependencies():
            if dep.package_type == PackageType.LIBRARY:
                # Add the library from its build directory
                lib_path = dep.get_build_dir()
                if lib_path.exists():
                    libs.append(lib_path)
                    # Add -l flag for this library
                    ldflags.append(f"-l{dep.name}")
            # Recursively get libraries from nested dependencies
            dep_libs, dep_flags = dep.get_all_dependency_libs()
            libs.extend(dep_libs)
            ldflags.extend(dep_flags)
        return libs, ldflags
    
    def get_source_files(self) -> List[Path]:
        """Get all source files for the package."""
        sources = []
        
        # Get sources from src directory
        src_dir = self.path / "src"
        if src_dir.exists():
            sources.extend(src_dir.glob("*.c"))
            sources.extend(src_dir.glob("*.cpp"))
            
        # Get sources from variants
        for variant in self._validated_config.variants.values():
            variant_dir = self.path / list(variant.keys())[0]
            if variant_dir.exists():
                sources.extend(variant_dir.glob("*.c"))
                sources.extend(variant_dir.glob("*.cpp"))
                
        return sources  # Return the collected source files
    
    def create_build_metadata(self, compiler_info: CompilerInfo) -> BuildMetadata:
        """Create build metadata for binary packages."""
        # Get all include paths
        includes = self._get_includes()
        includes.extend(self.get_all_dependency_includes())
        
        return BuildMetadata(
            compiler=compiler_info,
            cflags=self._get_cflags(),
            ldflags=self._get_ldflags(),  # Add ldflags
            includes=includes,
            libs=self._get_libs(),
            traits=self._get_traits()
        )
    
    def _get_cflags(self) -> List[str]:
        """Get compiler flags for the package."""
        cflags = []
        
        # Get global cflags
        if "cflags" in self._validated_config and "gcc" in self._validated_config["cflags"]:
            cflags.extend(self._validated_config["cflags"]["gcc"].split())
        if "g++" in self._validated_config and "cflags" in self._validated_config["cflags"]:
            cflags.extend(self._validated_config["cflags"]["g++"].split())
            
        # Get variant-specific cflags
        for variant in self._validated_config.variants.values():
            for variant_config in variant.values():
                if "cflags" in variant_config and "gcc" in variant_config["cflags"]:
                    cflags.extend(variant_config["cflags"]["gcc"].split())
                if "g++" in variant_config and "cflags" in variant_config["cflags"]:
                    cflags.extend(variant_config["cflags"]["g++"].split())
                    
        return cflags

    def _get_ldflags(self) -> List[str]:
        """Get linker flags for the package."""
        ldflags = []
        
        # Get global ldflags
        if "ldflags" in self._validated_config and "gcc" in self._validated_config["ldflags"]:
            ldflags.extend(self._validated_config["ldflags"]["gcc"].split())
        if "g++" in self._validated_config and "ldflags" in self._validated_config["ldflags"]:
            ldflags.extend(self._validated_config["ldflags"]["g++"].split())
            
        # Get variant-specific ldflags
        for variant in self._validated_config.variants.values():
            for variant_config in variant.values():
                if "ldflags" in variant_config and "gcc" in variant_config["ldflags"]:
                    ldflags.extend(variant_config["ldflags"]["gcc"].split())
                if "g++" in variant_config and "ldflags" in variant_config["ldflags"]:
                    ldflags.extend(variant_config["ldflags"]["g++"].split())
        
        # Add dependency ldflags
        _, dep_flags = self.get_all_dependency_libs()
        ldflags.extend(dep_flags)
                
        return ldflags
    
    def _get_includes(self) -> List[Path]:
        """Get include paths for the package."""
        includes = []
        # Add public include directory
        include_dir = self.path / "include"
        if include_dir.exists():
            includes.append(include_dir)
            # Also add package-specific include directory
            pkg_include = include_dir / self.name
            if pkg_include.exists():
                includes.append(pkg_include)
        # Add private include directory (only for this package)
        private_include_dir = self.path / "private_include"
        if private_include_dir.exists():
            includes.append(private_include_dir)
        return includes
    
    def _get_libs(self) -> List[Path]:
        """Get library paths for the package."""
        libs = []
        # Add own lib directory
        lib_dir = self.path / "lib"
        if lib_dir.exists():
            libs.append(lib_dir)
        # Add dependency library paths
        dep_libs, _ = self.get_all_dependency_libs()
        libs.extend(dep_libs)
        return libs
    
    def _get_traits(self) -> Dict[str, str]:
        """Get package traits."""
        traits = self._validated_config.traits.copy()
        traits.update(self._traits)  # Instance traits override config traits
        return traits

    def get_build_dir(self) -> Path:
        """Get the build directory for this package."""
        return self.path / ".build"

    def get_output_path(self) -> Path:
        """Get the output path for this package's artifacts."""
        if self.package_type == PackageType.LIBRARY:
            return self.get_build_dir() / f"lib{self.name}.a"
        else:
            return self.get_build_dir() / self.name 

    @property
    def organization(self) -> Optional[str]:
        """Get package organization if it exists."""
        name = self._validated_config.name
        if name.startswith('@'):
            org, _ = name.split('/', 1)
            return org[1:]  # Remove @ from org name
        return None

    @property
    def package_name(self) -> str:
        """Get package name without organization prefix."""
        name = self._validated_config.name
        if name.startswith('@'):
            _, pkg = name.split('/', 1)
            return pkg
        return name

    def get_dependency_path(self, name: str) -> Path:
        """Get the expected path for a dependency.
        
        Args:
            name: Full package name (with optional @org/ prefix)
            
        Returns:
            Path where the dependency should be installed
        """
        if name.startswith('@'):
            # For @org/pkg format, create deps/@org/pkg
            org = name.split('/')[0][1:]  # Remove @ from org
            pkg = name.split('/')[1]
            return self.path / "deps" / org / pkg
        else:
            # For backward compatibility, use deps/pkg
            return self.path / "deps" / name

    def get_build_path(self, name: str) -> Path:
        """Get the build output path for a dependency.
        
        Args:
            name: Full package name (with optional @org/ prefix)
            
        Returns:
            Path where build artifacts should be stored
        """
        if name.startswith('@'):
            # For @org/pkg format, create build/deps/@org/pkg
            org = name.split('/')[0][1:]  # Remove @ from org
            pkg = name.split('/')[1]
            return self.path / "build" / "deps" / org / pkg
        else:
            # For backward compatibility, use build/deps/pkg
            return self.path / "build" / "deps" / name 

    def get_all_headers(self) -> Dict[str, Path]:
        """Get all header files in package.
        
        Returns:
            Dictionary mapping header names to their paths
        """
        headers = {}
        include_dir = self.path / "include"
        if include_dir.exists():
            for header in include_dir.rglob("*.h"):
                headers[header.name] = header
        return headers
        
    def check_header_conflicts(self, other_package: "Package") -> List[str]:
        """Check for header name conflicts with another package.
        
        Args:
            other_package: Package to check against
            
        Returns:
            List of conflicting header names
        """
        our_headers = self.get_all_headers()
        their_headers = other_package.get_all_headers()
        
        conflicts = []
        for name in our_headers:
            if name in their_headers:
                # Check if headers are properly namespaced
                our_path = our_headers[name].relative_to(self.path / "include")
                their_path = their_headers[name].relative_to(other_package.path / "include")
                
                if len(our_path.parts) == 1 or len(their_path.parts) == 1:
                    # At least one header is not namespaced
                    conflicts.append(name)
                    
        return conflicts
        
    def validate_header_organization(self) -> List[str]:
        """Check if headers follow proper organization.
        
        Returns:
            List of warnings about header organization
        """
        warnings = []
        include_dir = self.path / "include"
        if not include_dir.exists():
            return warnings
            
        # Check for package namespace directory
        pkg_include = include_dir / self.package_name
        if not pkg_include.exists():
            warnings.append(
                f"Missing package namespace directory: include/{self.package_name}/"
            )
            
        # Check for headers directly in include/
        for header in include_dir.glob("*.h"):
            warnings.append(
                f"Header {header.name} should be in include/{self.package_name}/"
            )
            
        return warnings 