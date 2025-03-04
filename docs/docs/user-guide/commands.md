# Commands Reference

This document provides detailed information about all available Clyde commands, their options, and usage examples.

## Project Management

### `init`

Initialize a new C/C++ project.

```bash
clyde init [PATH] [OPTIONS]
```

Options:
- `PATH`: Directory to create project in (default: current directory)
- `--name`, `-n`: Package name (defaults to directory name)
- `--type`, `-t`: Project type (`library` or `application`, default: `library`)
- `--lang`, `-l`: Programming language (`c`, `cpp`, `cxx`, or `c++`)
- `--template`: Template to use (`c-app`, `cpp-app`, `c-lib`, or `cpp-lib`)
- `--version`, `-v`: Initial version (default: `0.1.0`)

GitHub Options:
- `--setup-remote/--no-setup-remote`: Set up GitHub repository
- `--org`, `--organization`: GitHub organization to use
- `--private/--public`: Create private/public repository
- `--description`, `-d`: Repository description
- `--ssh/--https`: Use SSH/HTTPS URLs for Git remotes (default: SSH)

Examples:
```bash
# Create C++ library
clyde init my-lib --type library --lang cpp

# Create C application with GitHub repo
clyde init my-app \
  --type application \
  --lang c \
  --setup-remote \
  --org myorg \
  --description "My C application"
```

## Build Commands

### `build`

Build a package and its dependencies.

```bash
clyde build [PATH] [OPTIONS]
```

Options:
- `PATH`: Package directory (default: current directory)
- `--trait`, `-t`: Build traits in `key=value` format (can be specified multiple times)
- `--verbose`, `-v`: Show compiler commands

Examples:
```bash
# Simple build
clyde build

# Build with traits
clyde build --trait debug=true --trait optimize=false

# Verbose build
clyde build --verbose
```

### `run`

Run an application package.

```bash
clyde run [PATH] [ARGS...]
```

Options:
- `PATH`: Package directory (default: current directory)
- `ARGS`: Arguments to pass to the application

Examples:
```bash
# Run application
clyde run

# Run with arguments
clyde run -- --help
clyde run -- input.txt output.txt
```

## Package Management

### `install`

Install packages either as project dependencies or globally.

```bash
clyde install [PACKAGES...] [OPTIONS]
```

Options:
- `PACKAGES`: One or more packages to install (e.g. `fmt@8.1.1`, `json@^1.0.0`)
- `-g`, `--global`: Install packages globally in `~/.clyde/prefix`
- `--dev`: Install as development dependency
- `--exact`: Use exact version matching (pins the version)
- `--prefix`: Override the global installation prefix (default: `~/.clyde/prefix`)

Examples:
```bash
# Add fmt as a project dependency
clyde install fmt@8.1.1

# Add multiple packages
clyde install fmt@8.1.1 json@^1.0.0

# Install globally
clyde install -g fmt@8.1.1

# Install as dev dependency
clyde install --dev gtest@1.11.0

# Install with custom global prefix
clyde install -g fmt@8.1.1 --prefix /usr/local

# Install from local path
clyde install ../my-lib
```

When installing as a project dependency:
- Updates `package.yml`'s `requires` section
- Downloads and builds the package into `clyde_packages/`
- Maintains a lockfile for reproducible builds

When installing globally (-g):
- Installs into `~/.clyde/prefix` (or specified prefix)
- Makes headers and libraries available system-wide
- Does not modify any project configuration

## Cache Management

### `cache`

Manage the build cache.

#### List Cache Contents

```bash
# List all cached artifacts
clyde cache list
clyde cache ls

# Filter by package
clyde cache list --package my-lib
```

Output columns:
- Package: Package name
- Type: Artifact type (Object or Artifact)
- Size: File size in human-readable format
- Path: Relative path in cache

#### Clean Cache

```bash
# Clean current package cache
clyde cache clean

# Clean entire cache
clyde cache clean --all
```

## GitHub Integration

### `auth`

Manage GitHub authentication.

```bash
clyde auth login
clyde auth logout
clyde auth status
```

### `publish`

Publish a package to GitHub.

```bash
clyde publish [OPTIONS]
```

Options:
- `--binary/--no-binary`: Create and publish binary package

## Common Options

These options are available for most commands:

- `--help`: Show command help
- `--verbose`, `-v`: Enable verbose output

## Environment Variables

- `GITHUB_TOKEN`: GitHub personal access token
- `CLYDEPM_CACHE_DIR`: Override default cache directory
- `CLYDEPM_CONFIG_DIR`: Override default config directory

## Exit Codes

- 0: Success
- 1: General error
- 2: Invalid arguments
- 3: Build failure
- 4: Runtime error

## For LLM Analysis

Command Structure:
```python
commands = {
    "init": {
        "type": "project_creation",
        "requires_path": True,
        "modifies_filesystem": True
    },
    "build": {
        "type": "build_system",
        "requires_package": True,
        "creates_artifacts": True
    },
    "run": {
        "type": "execution",
        "requires_application": True,
        "forwards_args": True
    },
    "cache": {
        "type": "cache_management",
        "subcommands": ["list", "clean"],
        "modifies_cache": True
    }
}
```

Common Patterns:
1. Path arguments default to current directory
2. Commands validate package existence
3. Rich output with progress indicators
4. Consistent error handling
5. GitHub integration where relevant 