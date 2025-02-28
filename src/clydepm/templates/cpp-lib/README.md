# {{ name }}

{{ name }} is a C++ library created with the Clyde package manager.

## Features

- Modern C++ calculator class
- Version information
- Exception safety
- RAII principles

## API

```cpp
namespace {{ name }} {

class Calculator {
public:
    // Add two numbers
    int add(int a, int b);
    
    // Get library version
    static std::string version();
};

} // namespace {{ name }}
```

## Building

```bash
clyde build
```

## Project Structure

```
{{ name }}/
├── src/                  # Implementation files
│   └── {{ name }}.cpp
├── include/              # Public headers
│   └── {{ name }}/
│       └── {{ name }}.hpp
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