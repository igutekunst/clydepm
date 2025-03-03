# Package Lock System

The package lock system ensures reproducible builds by exactly pinning dependencies and their metadata.

## Overview

The lock system provides:

 - Exact version pinning
 - Dependency tree snapshots
 - Checksum verification
 - Build configuration locking

## Lock File Format

```yaml
version: 1  # Lock file format version
metadata:
  generated_at: "2024-03-02T12:00:00Z"
  clydepm_version: "1.0.0"
  platform: "darwin-x86_64"

packages:
  my-lib:
    version: "1.2.3"
    source:
      type: "github"
      url: "https://github.com/owner/my-lib"
      commit: "abc123def456"
    checksums:
      sha256: "..."
    dependencies:
      boost: "1.81.0"
      fmt: "9.1.0"
    build_config:
      compiler: "gcc-12.2.0"
      flags: ["-O2", "-Wall"]

  boost:
    version: "1.81.0"
    source:
      type: "registry"
      url: "https://registry.clydepm.dev/boost"
    checksums:
      sha256: "..."
```

## Implementation

### Version Resolution

```python
class VersionResolver:
    """Resolves version constraints to exact versions."""
    
    def resolve(self, constraints: Dict[str, str]) -> Dict[str, str]:
        """Convert version constraints to exact versions."""
        resolved = {}
        for pkg, constraint in constraints.items():
            resolved[pkg] = self._find_best_match(pkg, constraint)
        return resolved
```

### Checksum Verification

```python
class ChecksumVerifier:
    """Verifies package checksums."""
    
    def verify_package(self, package: Package, expected: str) -> bool:
        """Verify package contents match expected checksum."""
        actual = self._compute_checksum(package)
        return actual == expected
```

### Lock File Management

```python
class LockFileManager:
    """Manages the lock file."""
    
    def generate(self, root_package: Package) -> dict:
        """Generate lock file contents."""
        return {
            "version": 1,
            "metadata": self._generate_metadata(),
            "packages": self._resolve_all_packages(root_package)
        }
```

## Usage

### Creating Lock File

```bash
# Generate lock file for new project
clyde lock init

# Update existing lock file
clyde lock update

# Update specific package
clyde lock update package-name
```

### Verification

```bash
# Verify all packages match lock file
clyde verify

# Update checksums in lock file
clyde lock --update-checksums
```

## Security Considerations

- Checksum verification prevents supply chain attacks
- Lock file should be committed to version control
- Secure hash algorithms (SHA-256) for checksums
- Signed commits for source verification

## Future Enhancements

- [ ] Multiple platform support in single lock file
- [ ] Build configuration versioning
- [ ] Dependency graph visualization
- [ ] Security vulnerability checking
- [ ] Lock file migration tools 