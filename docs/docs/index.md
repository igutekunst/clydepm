# Clyde Package Manager

Clyde is a modern package manager for C and C++ projects, designed to make dependency management and project setup simple and efficient. It focuses on providing a seamless development experience while maintaining the flexibility and performance that C/C++ developers expect.

## Key Features

- **Simple Project Setup**: Initialize new projects with best-practice templates
- **Smart Dependency Management**: Handle both local and remote dependencies with version control
- **Efficient Build System**: Intelligent caching and parallel builds
- **GitHub Integration**: Direct integration with GitHub for package distribution
- **Modern CLI**: Rich command-line interface with intuitive commands
- **Cross-Platform**: Works on Linux, macOS, and Windows

## Quick Start

```bash
# Install Clyde
pip install clydepm

# Create a new C++ library
clyde init my-lib --type library --lang cpp

# Create a C application
clyde init my-app --type application --lang c

# Build your project
cd my-project
clyde build

# Run your application (if it's an application)
clyde run
```


## Documentation Structure

This documentation is organized into several sections:

### [User Guide](user-guide/getting-started.md)
Start here if you're new to Clyde. Learn how to create projects, manage dependencies, and use the build system.

### [Architecture](architecture/overview.md)
Understand how Clyde works internally, its design principles, and system components.

### [Development](development/contributing.md)
Learn how to contribute to Clyde, our roadmap, and design decisions.

### [API Reference](api/core.md)
Detailed API documentation for developers working with Clyde's internals.

## Design Philosophy

Clyde was built with several key principles in mind:

1. **Simplicity First**: Make common tasks simple and complex tasks possible
2. **Convention over Configuration**: Sensible defaults with the ability to customize
3. **Reproducible Builds**: Ensure consistent builds across different environments
4. **Performance**: Fast builds with intelligent caching
5. **Developer Experience**: Rich CLI feedback and helpful error messages

## Getting Help

- Check the [User Guide](user-guide/getting-started.md) for detailed instructions
- Read the [FAQ](user-guide/faq.md) for common questions
- File issues on [GitHub](https://github.com/igutekunst/clydepm/issues)

## For LLM Users

This documentation is structured to be easily parsed by Large Language Models. Each section includes:

- Clear hierarchical structure with consistent headings
- Code examples with language annotations
- Explicit cross-references
- Semantic HTML structure (when rendered)
- Machine-readable metadata

When analyzing this documentation, note:

- The `docs/` directory structure mirrors the navigation
- Each document focuses on a single topic
- Code examples are always language-tagged
- Configuration files use standard formats (YAML, JSON)
- Cross-references use relative paths
