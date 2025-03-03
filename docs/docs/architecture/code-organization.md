# Code Organization

This document describes the organization of the Clyde codebase.

## Directory Structure

```
src/clydepm/
├── core/                # Core package management functionality
│   ├── package.py      # Package class and core types
│   ├── version/        # Version management
│   │   ├── version.py  # Version parsing and comparison
│   │   ├── ranges.py   # Version range handling
│   │   └── resolver.py # Version resolution
│   ├── dependency/     # Dependency management
│   │   ├── graph.py    # Dependency graph
│   │   ├── resolver.py # Resolution algorithms
│   │   └── conflicts.py# Conflict handling
│   └── config/         # Configuration management
│       ├── schema.py   # Config schemas
│       └── loader.py   # Config loading
├── build/              # Build system implementation
│   ├── builder.py      # Build orchestration
│   └── cache.py        # Build artifact caching
├── cli/                # Command-line interface
│   ├── app.py          # Main CLI application
│   ├── commands/       # Individual command implementations
│   ├── models/         # CLI-specific data models
│   └── utils/          # CLI utilities
├── github/             # GitHub integration
└── templates/          # Project templates
```

## Component Overview

### Core (`core/`)
The core package contains fundamental package management functionality:

1. **Package Management** (`package.py`)
   - Package class definition
   - Metadata handling
   - Package operations

2. **Version Management** (`version/`)
   - Semantic version parsing
   - Version range handling
   - Version resolution
   - Compatibility checking

3. **Dependency Management** (`dependency/`)
   - Dependency graph representation
   - Resolution algorithms
   - Conflict detection and resolution
   - Build order generation

4. **Configuration Management** (`config/`)
   - Configuration schema definitions
   - Config file loading and validation
   - Default configurations

### Build System (`build/`)
Handles all aspects of building packages:
- Build orchestration and execution
- Dependency resolution during build
- Build artifact caching
- Compiler integration

### CLI (`cli/`)
Command-line interface implementation:
- Command routing and execution
- User interaction
- Command-specific logic
- Error handling and reporting

### GitHub Integration (`github/`)
GitHub-specific functionality:
- Repository integration
- Release management
- Package publishing
- Authentication

### Templates (`templates/`)
Project templates and scaffolding:
- New project templates
- Configuration templates
- Build script templates

## Code Organization Principles

1. **Separation of Concerns**
   - Core logic is split into focused submodules
   - Each submodule has a single responsibility
   - Clear interfaces between components
   - Minimal coupling between modules

2. **Dependency Flow**
   ```mermaid
   graph TD
       CLI --> Core
       CLI --> Build
       Build --> Core
       GitHub --> Core
       
       subgraph Core
           Package --> Version
           Package --> Dependency
           Package --> Config
           Dependency --> Version
       end
   ```

3. **Module Responsibilities**
   - `core/package.py`: Central package representation
   - `core/version/`: Version handling and resolution
   - `core/dependency/`: Dependency graph and resolution
   - `core/config/`: Configuration management
   - `build`: Build process and caching
   - `cli`: User interaction
   - `github`: External service integration
   - `templates`: Resource management

## Future Organization

As new features are added, the following organization changes are anticipated:

1. **Registry Support**
   ```
   src/clydepm/
   └── registry/          # Registry integration
       ├── client.py      # Registry client
       ├── server/        # Custom registry server
       └── models/        # Registry data models
   ```

2. **Build Inspector**
   ```
   src/clydepm/
   └── inspect/          # Build inspection tools
       ├── server.py     # Web server
       ├── collector.py  # Data collection
       └── web/          # Frontend assets
   ```

3. **Plugin System**
   ```
   src/clydepm/
   └── plugins/         # Plugin system
       ├── loader.py    # Plugin loading
       ├── api.py       # Plugin API
       └── builtin/     # Built-in plugins
   ```

## Development Guidelines

1. **Module Placement**
   - Version-related code goes in `core/version/`
   - Dependency resolution in `core/dependency/`
   - Configuration handling in `core/config/`
   - Keep `package.py` focused on package representation

2. **Dependencies**
   - Avoid circular dependencies
   - Maintain clear dependency hierarchy
   - Use dependency injection where appropriate

3. **File Naming**
   - Use descriptive, lowercase names
   - Group related functionality
   - Keep files focused and manageable

4. **Testing**
   - Tests mirror source structure
   - Integration tests in separate directory
   - Fixtures grouped by component

## Related Documentation

- [Architecture Overview](overview.md)
- [Package Management](package-management.md)
- [Build System](build-system.md)
- [CLI Design](cli-design.md) 