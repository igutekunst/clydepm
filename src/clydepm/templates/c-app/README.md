# {{ name }}

{{ name }} is a C application created with the Clyde package manager.

## Building

```bash
clyde build
```

## Running

```bash
clyde run [args...]
```

The program accepts command-line arguments and will display them when run.

## Project Structure

```
{{ name }}/
├── src/              # Source files
│   └── main.c        # Main program
├── include/          # Public headers (if any)
└── private_include/  # Private headers (if any)
```

## Configuration

See `package.yml` for build settings and dependencies. 