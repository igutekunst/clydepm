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

See `package.yml` for build settings and dependencies.

## Usage

To use this library in another Clyde project, add it to the dependencies in `package.yml`:

```yaml
requires:
  {{name}}: 
    path: ../{{name}}
```

## Include Path Structure

Headers are organized to prevent naming conflicts:

```
{{ name }}/
├── include/              # Public headers (exposed to dependents)
│   └── {{ name }}/      # Package namespace directory
│       └── {{ name }}.hpp
└── private_include/     # Private headers (not exposed)
```

Public headers are included using the package name as namespace:
```cpp
#include <{{ name }}/{{ name }}.hpp>
```

This structure ensures:
- No header name conflicts between packages
- Clear separation of public/private interfaces
- No need to copy headers between packages 