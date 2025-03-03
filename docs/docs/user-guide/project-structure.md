# Project Structure

A typical Clyde project has the following structure:

```
my-project/
├── package.yml        # Project configuration
├── README.md         # Project documentation
├── src/             # Source files
│   ├── main.cpp
│   └── lib.cpp
├── include/         # Public headers
│   └── my-project/  # Project-specific headers
├── tests/          # Test files
│   └── test_lib.cpp
└── build/          # Build artifacts (generated)
```

## Configuration

The `package.yml` file is the heart of your project, defining its properties and dependencies:

```yaml
name: my-project
version: 0.1.0
type: library  # or application
language: cpp  # or c

# Source files to compile
sources:
  - src/main.cpp
  - src/lib.cpp

# Build configuration
cflags:
  gcc: -Wall -Wextra
  g++: -std=c++17

# Dependencies
requires:
  fmt: ^8.0.0
  my-lib:
    path: ../my-lib

# Build traits (optional)
traits:
  debug: false
  sanitize: false
```

## Source Organization

### Source Files (`src/`)
- Main implementation files
- Internal implementation details
- Private headers (if not in `private_include/`)

### Public Headers (`include/`)
- Public API headers
- Organized in project-specific subdirectory
- Example: `include/my-project/api.hpp`

### Private Headers (`private_include/`)
- Internal headers
- Not installed with the package
- Implementation details

### Tests (`tests/`)
- Unit tests
- Integration tests
- Test utilities

## Build System

The build system:
- Reads `package.yml` for configuration
- Compiles source files
- Links dependencies
- Generates artifacts in `build/`

### Build Directory (`build/`)
- Object files (`.o`)
- Library files (`.a`, `.so`)
- Executables
- Build logs

## Dependencies

Dependencies can be:
- Remote (downloaded from GitHub)
- Local (in adjacent directories)

Best practices:
- List all dependencies in `package.yml`
- Use version constraints
- Document dependency requirements

## Project Types

### Library
```yaml
# package.yml
type: library
language: cpp

sources:
  - src/lib.cpp
```

### Application
```yaml
# package.yml
type: application
language: cpp

sources:
  - src/main.cpp
```

## Summary

Key components:
- Configuration (`package.yml`): Project metadata and build settings
- Source files: Implementation in `src/`
- Headers: Public API in `include/`
- Tests: Verification in `tests/`
- Build: Artifacts in `build/` 