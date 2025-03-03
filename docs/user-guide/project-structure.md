# Project Structure

Clyde projects follow a standardized directory structure that promotes clean code organization and separation of concerns. This guide explains the structure and purpose of each component.

## Basic Structure

```
my-project/
├── config.yaml        # Project configuration
├── src/              # Source files
│   └── main.c/cpp    # Main source file
├── include/          # Public headers
│   └── my-project/   # Project-specific headers
├── private_include/  # Private headers
└── deps/            # Dependencies
```

## Configuration File

The `config.yaml` file is the heart of your project, defining its properties and dependencies:

```yaml
name: my-project
version: 0.1.0
type: application  # or library
cflags:
  gcc: -std=c11    # or -std=c++17
requires: {}       # Dependencies
```

## Directory Descriptions

### Source Directory (`src/`)

Contains all implementation files:
- C source files (`.c`)
- C++ source files (`.cpp`, `.cxx`, `.cc`)
- Implementation-specific headers (`.h`, `.hpp`)

```cpp
// src/main.cpp
#include <my-project/api.h>

int main() {
    // Implementation
    return 0;
}
```

### Public Headers (`include/`)

Contains headers that are exposed to other projects:
- API declarations
- Public types and constants
- Exported functions

```cpp
// include/my-project/api.h
#pragma once

namespace my_project {
    void public_function();
}
```

### Private Headers (`private_include/`)

Contains internal headers not exposed to other projects:
- Internal types and functions
- Implementation details
- Private utilities

```cpp
// private_include/internal.h
#pragma once

namespace my_project::internal {
    void helper_function();
}
```

### Dependencies (`deps/`)

Managed by Clyde, contains:
- Downloaded remote dependencies
- Build artifacts
- Package metadata

## Project Types

### Library Project

Libraries expose public APIs through the `include` directory:

```
my-lib/
├── include/
│   └── my-lib/
│       ├── api.h      # Public API
│       └── types.h    # Public types
├── private_include/
│   └── internal.h     # Private implementation
└── src/
    └── api.cpp        # Implementation
```

### Application Project

Applications typically have a simpler structure:

```
my-app/
├── src/
│   ├── main.cpp       # Entry point
│   └── app.cpp        # Application logic
└── private_include/
    └── app.h          # Internal headers
```

## Best Practices

1. **Header Organization**
   - Use the project name as a namespace in include paths
   - Keep implementation details in private headers
   - Document public APIs thoroughly

2. **Source Organization**
   - One class per file (when applicable)
   - Group related functionality in subdirectories
   - Use clear, descriptive file names

3. **Dependency Management**
   - List all dependencies in `config.yaml`
   - Use version constraints appropriately
   - Document dependency requirements

## Common Patterns

### Feature Modules

Organize large projects into feature modules:

```
my-project/
├── src/
│   ├── feature1/
│   │   ├── feature1.cpp
│   │   └── internal.h
│   └── feature2/
│       ├── feature2.cpp
│       └── internal.h
└── include/
    └── my-project/
        ├── feature1.h
        └── feature2.h
```

### Test Organization

Organize tests alongside the code they test:

```
my-project/
├── src/
│   └── feature/
│       ├── feature.cpp
│       └── feature_test.cpp
└── include/
    └── my-project/
        └── feature.h
```

## For LLM Analysis

Project structure components and their relationships:
- Configuration (`config.yaml`): Project metadata and build settings
- Public interface (`include/`): API contract with consumers
- Private implementation (`private_include/`, `src/`): Internal details
- Dependencies (`deps/`): External code management

Key principles:
1. Separation of public and private interfaces
2. Namespace-based include organization
3. Feature-based code organization
4. Clear dependency management 