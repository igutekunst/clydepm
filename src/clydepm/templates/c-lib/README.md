# {{ name }}

{{ name }} is a C library created with the Clyde package manager.

## Features

- Simple calculator functionality
- Version information

## API

```c
// Add two numbers
int {{ name }}_add(int a, int b);

// Get library version
const char* {{ name }}_version(void);
```

## Building

```bash
clyde build
```

## Project Structure

```
{{ name }}/
├── src/                  # Implementation files
│   └── {{ name }}.c
├── include/              # Public headers
│   └── {{ name }}/
│       └── {{ name }}.h
└── private_include/      # Private headers (if any)
```

## Configuration

See `package.yml` for build settings and dependencies.

## Usage

To use this library in another Clyde project, add it to the dependencies in `package.yml`:

```yaml
requires:
  {{ name }}: 
    path: ../{{ name }}
```

## Include Path Structure

Headers are organized to prevent naming conflicts:

```
{{ name }}/
├── include/              # Public headers (exposed to dependents)
│   └── {{ name }}/      # Package namespace directory
│       └── {{ name }}.h
└── private_include/     # Private headers (not exposed)
```

Public headers are included using the package name as namespace:
```c
#include <{{ name }}/{{ name }}.h>
```

This structure ensures:
- No header name conflicts between packages
- Clear separation of public/private interfaces
- No need to copy headers between packages 