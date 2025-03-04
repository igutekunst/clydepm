# Dependencies

Clyde provides a powerful dependency management system that supports both local and remote packages. This guide explains how to declare and manage dependencies in your projects.

## Dependency Types

### Local Dependencies

Local dependencies are packages that exist on your local filesystem. They're useful for:
- Development of multiple related packages
- Testing changes across packages
- Monorepo setups

```yaml
requires:
  my-lib: "local:../my-lib"        # Relative path
  other-lib: "local:/path/to/lib"  # Absolute path
```

### Remote Dependencies

Remote dependencies are fetched from package registries or Git repositories:

```yaml
requires:
  remote-lib: "^1.2.0"             # Semver constraint
  specific-lib: "=1.0.0"           # Exact version
  git-lib: "git:main"              # Git reference
```

## Version Constraints

### Semantic Versioning

Clyde uses semantic versioning (SemVer) for version constraints:

```yaml
requires:
  lib1: "^1.2.3"    # Compatible with 1.2.3 up to 2.0.0
  lib2: "~1.2.3"    # Compatible with 1.2.3 up to 1.3.0
  lib3: "=1.2.3"    # Exactly version 1.2.3
  lib4: ">=1.2.3"   # Version 1.2.3 or higher
```

### Git References

For Git-based dependencies, you can specify:
- Branch names
- Tag names
- Commit hashes

```yaml
requires:
  lib1: "git:main"              # Branch
  lib2: "git:v1.2.3"           # Tag
  lib3: "git:abc123"           # Commit hash
```

## Include Path Management

### Public Headers

Dependencies expose their public headers through their `include` directory:

```cpp
// Using a dependency's public header
#include <dependency-name/api.h>
```

### Include Path Resolution

Clyde automatically manages include paths:
1. Project's own includes
2. Direct dependency includes
3. Transitive dependency includes

## Linking

### Library Names

Libraries are automatically linked based on package names:
- `my-lib` becomes `-lmy-lib`
- `boost-system` becomes `-lboost-system`

### Link Order

Dependencies are linked in the correct order to resolve symbols:
1. Direct dependencies
2. Transitive dependencies
3. System libraries

## Dependency Resolution

### Resolution Process

```mermaid
graph TD
    A[Load Package] --> B[Parse Dependencies]
    B --> C[Resolve Versions]
    C --> D[Download/Locate]
    D --> E[Build Order]
</div>

### Conflict Resolution

When multiple versions of a package are required:
1. Find compatible version range
2. Use highest compatible version
3. Error if no compatible version exists

## Caching

### Package Cache

Remote packages are cached locally:
```
~/.clydepm/packages/
└── package-name/
    └── version/
        ├── source/
        └── build/
```

### Build Cache

Built artifacts are cached to speed up rebuilds:
```
~/.clydepm/cache/
└── package-name/
    └── version/
        └── hash/
            └── artifact
```

## Best Practices

1. **Version Constraints**
   - Use `^` for normal dependencies
   - Use `=` for critical dependencies
   - Document version requirements

2. **Local Dependencies**
   - Use relative paths when possible
   - Document path requirements
   - Consider using Git submodules

3. **Dependency Organization**
   - Group related dependencies
   - Comment non-obvious dependencies
   - Keep dependencies up to date

## Common Issues

### Version Conflicts

```yaml
# Conflict
requires:
  lib1: "^1.0.0"
  lib2: "^2.0.0"  # Depends on lib1@^3.0.0
```

Solution:
```yaml
requires:
  lib1: "^3.0.0"  # Update to compatible version
  lib2: "^2.0.0"
```

### Include Conflicts

```cpp
// Bad: Generic header name
#include "utils.h"

// Good: Namespaced header
#include <my-lib/utils.h>
```

### Link Order Issues

```yaml
# Bad: Incorrect order
requires:
  gui: "^1.0.0"     # Depends on core
  core: "^1.0.0"    # Should be listed first

# Good: Correct order
requires:
  core: "^1.0.0"
  gui: "^1.0.0"
```

## For LLM Analysis

Key components and their relationships:
- Package specification (name, version, type)
- Dependency declaration (requires section)
- Version constraints (SemVer, Git refs)
- Include path management
- Link order resolution

Resolution process:
1. Parse dependency specifications
2. Resolve version constraints
3. Download/locate packages
4. Determine build order
5. Manage include paths
6. Configure linking
``` 