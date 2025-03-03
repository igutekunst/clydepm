# Code Organization

This document describes the organization of the Clyde codebase.

## Directory Structure

```
src/clydepm/
├── core/           # Core package management functionality
│   └── package.py  # Package class and core types
├── build/          # Build system implementation
│   ├── builder.py  # Build orchestration
│   └── cache.py    # Build artifact caching
├── cli/            # Command-line interface
│   ├── app.py      # Main CLI application
│   ├── commands/   # Individual command implementations
│   ├── models/     # CLI-specific data models
│   └── utils/      # CLI utilities
├── github/         # GitHub integration
└── templates/      # Project templates
```

## Component Overview

### Core (`core/`)
The core package contains fundamental package management functionality:
- Package definition and metadata
- Dependency management
- Version handling
- Configuration management

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
   - Core logic is independent of UI/CLI
   - Build system is modular and extensible
   - Clear boundaries between components

2. **Dependency Flow**
   ```mermaid
   graph TD
       CLI --> Core
       CLI --> Build
       Build --> Core
       GitHub --> Core
   ```

3. **Module Responsibilities**
   - `core`: Data models and business logic
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
   - New features should follow existing organization
   - Core functionality belongs in `core/`
   - UI/UX features belong in `cli/`
   - Build features belong in `build/`

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