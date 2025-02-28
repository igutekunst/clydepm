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

See `config.yaml` for build settings and dependencies.

## Usage

To use this library in another Clyde project, add it to the dependencies in `config.yaml`:

```yaml
requires:
  {{ name }}: "{{ version }}"
``` 