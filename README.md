# Clyde Package Manager

Clyde is a modern package manager for C and C++ projects, designed to make dependency management and project setup simple and efficient.

## Features

- Simple project initialization with templates
- Support for both C and C++ projects
- GitHub-based package registry
- Binary package support
- Easy-to-use command line interface

## Installation

```bash
pip install clydepm
```

## Quick Start

### Create a New Project

Create a C application:
```bash
clyde init my-app --type application
cd my-app
clyde build
clyde run
```

Create a C++ library:
```bash
clyde init my-lib --type library --lang cpp
cd my-lib
clyde build
```

Create a C library:
```bash
clyde init my-lib --type library --lang c
cd my-lib
clyde build
```

### Project Types

Clyde supports two types of projects:
- **Applications**: Executable programs (default: C)
- **Libraries**: Reusable code packages (default: C++)

### Language Selection

Use the `--lang` flag to specify the programming language:
- `--lang c`: C (C11)
- `--lang cpp` (or `cxx`, `c++`): C++ (C++17)

### Project Structure

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

### Configuration (config.yaml)

```yaml
name: my-project
version: 0.1.0
type: application  # or library
cflags:
  gcc: -std=c11    # or -std=c++17
requires: {}       # Dependencies
```

## Commands

### Initialize a Project
```bash
clyde init [path] [options]
  --name, -n TEXT          Package name (defaults to directory name)
  --type, -t [application|library]
  --lang, -l [c|cpp|cxx|c++]
  --version, -v TEXT       Initial version
```

### Build a Project
```bash
clyde build [path] [options]
  --trait, -t KEY=VALUE   Build traits
```

### Run an Application
```bash
clyde run [path] [args]
```

### Publish a Package
```bash
clyde publish [path] [options]
  --binary/--no-binary    Create and publish binary package
```

### Install a Package
```bash
clyde install package-name[==version]
  --path, -p PATH         Installation path
```

## GitHub Integration

To use GitHub features (publish/install), set your GitHub token:
```bash
export GITHUB_TOKEN=your-token
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[License details here] 