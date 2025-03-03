# Getting Started

This guide will help you get started with Clyde, from installation to creating your first C/C++ project.

## Installation

Install Clyde using pip:

```bash
pip install clydepm
```

## Creating a New Project

```bash
# Create a new C++ library project
clyde init my-lib --type library --lang cpp

# Create a new C application
clyde init my-app --type application --lang c
```

This creates a new project with the following structure:

```
my-project/
├── package.yml        # Project configuration
├── README.md         # Project documentation
├── src/             # Source files
│   └── main.cpp
└── tests/           # Test files
    └── test_main.cpp
```

## Building a Project

```bash
# Build the project
clyde build

# Build with specific traits
clyde build -t debug=true
```

## Project Structure

A typical C/C++ project has this structure:

```
my-project/
├── package.yml       # Project configuration
├── README.md        # Project documentation
├── src/            # Source files
│   ├── main.cpp
│   └── lib.cpp
├── include/        # Public headers
│   └── lib.hpp
└── tests/         # Test files
    └── test_lib.cpp
```

The `package.yml` file defines your project:

```yaml
name: my-project
version: 0.1.0
type: library  # or application
language: cpp  # or c

sources:
  - src/main.cpp
  - src/lib.cpp

requires:
  fmt: ^8.0.0
```

## Dependencies

Clyde supports both local and remote dependencies. Add them to `package.yml`:

```yaml
requires:
  # Remote dependency
  fmt: ^8.0.0
  
  # Local dependency
  my-lib: 
    path: ../my-lib
```

## Building and Running

```bash
# Build the project
clyde build

# Run an application
clyde run

# Clean build artifacts
clyde clean
```

## Next Steps

- [Project Structure](project-structure.md) - Learn more about project organization
- [Build System](build-system.md) - Understand the build system
- [Package Management](package-management.md) - Work with dependencies

## Project Configuration

The `config.yaml` file defines your project:

```yaml
name: my-project      # Project name
version: 0.1.0        # Project version
type: library        # library or application
cflags:              # Compiler flags
  gcc: -std=c11      # For C projects
  g++: -std=c++17    # For C++ projects
requires: {}         # Dependencies (empty initially)
```

## Adding Dependencies

Clyde supports both local and remote dependencies. Add them to `config.yaml`:

```yaml
requires:
  # Local dependency
  my-lib: "local:../my-lib"
  
  # Remote dependency with version constraint
  json-lib: "^1.2.0"
  
  # Exact version
  math-lib: "=1.0.0"
  
  # Git branch/tag
  utils: "git:main"
```

## GitHub Integration

Clyde integrates with GitHub for package distribution. When initializing a project, you can:

```bash
clyde init my-project \
  --setup-remote \    # Create GitHub repository
  --org myorg \      # Optional: specify organization
  --private \        # Optional: make repository private
  --description "My awesome project"
```

Set your GitHub token first:
```bash
export GITHUB_TOKEN=your-token
```

## Project Structure Best Practices

### Header Organization

1. **Public Headers** (`include/`):
   ```cpp
   // include/my-lib/api.h
   #pragma once
   
   namespace my_lib {
     void public_function();
   }
   ```

2. **Private Headers** (`private_include/`):
   ```cpp
   // private_include/internal.h
   #pragma once
   
   namespace my_lib::internal {
     void helper_function();
   }
   ```

3. **Implementation** (`src/`):
   ```cpp
   // src/api.cpp
   #include <my-lib/api.h>
   #include "internal.h"
   
   namespace my_lib {
     void public_function() {
       internal::helper_function();
     }
   }
   ```

### Include Path Best Practices

1. Use project namespacing:
   ```cpp
   #include <my-lib/api.h>    // Good
   #include <api.h>           // Bad - no namespace
   ```

2. Keep implementation details private:
   ```cpp
   // In public headers (include/)
   #include <other-lib/api.h>  // Good - using public API
   
   // In private headers (private_include/)
   #include "internal.h"       // Good - internal only
   ```

## Cache Management

Clyde maintains a build cache to speed up compilation. Manage it with:

```bash
# List cached artifacts
clyde cache list
clyde cache ls

# List artifacts for specific package
clyde cache list --package my-lib

# Clean cache for current package
clyde cache clean

# Clean entire cache
clyde cache clean --all
``` 