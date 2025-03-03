# Getting Started

This guide will help you get started with Clyde, from installation to creating your first C/C++ project.

## Installation

Install Clyde using pip:

```bash
pip install clydepm
```

## Creating Your First Project

Clyde provides several templates for both C and C++ projects. Let's explore the different ways to create a project.

### C++ Library

Create a C++ library project:

```bash
clyde init my-lib --type library --lang cpp
cd my-lib
```

This creates a library project with the following structure:
```
my-lib/
├── config.yaml        # Project configuration
├── src/              # Source files
├── include/          # Public headers
│   └── my-lib/       # Project-specific headers
├── private_include/  # Private headers
└── .gitignore       # Git ignore file
```

### C Application

Create a C application project:

```bash
clyde init my-app --type application --lang c
cd my-app
```

This creates an application project with:
```
my-app/
├── config.yaml       # Project configuration
├── src/             # Source files
│   └── main.c       # Main entry point
├── include/         # Public headers
└── .gitignore      # Git ignore file
```

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

## Building Your Project

Build your project using:

```bash
clyde build
```

Options:
- `--trait` or `-t`: Set build traits (e.g., `--trait debug=true`)
- `--verbose` or `-v`: Show compiler commands

For applications, you can run them with:

```bash
clyde run [args...]
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

## Next Steps

- Learn about [Project Structure](project-structure.md) in detail
- Understand [Dependencies](dependencies.md) management
- Explore the [Build System](build-system.md)
- Check the [Commands Reference](commands.md) 