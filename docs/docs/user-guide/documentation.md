# Documentation

## Running the Documentation

You can run this documentation locally using [MkDocs](https://www.mkdocs.org/), which provides a live-reloading server and can build static sites.

### Installation

```bash
# Install MkDocs and the Material theme
pip install mkdocs mkdocs-material

# Optional but recommended plugins
pip install mkdocs-mermaid2-plugin
```

### Running the Server

```bash
# Start the development server
mkdocs serve

# The documentation will be available at:
# http://127.0.0.1:8000
```

### Building Static Site

```bash
# Build the static site
mkdocs build

# The output will be in the 'site' directory
```

### Configuration

The documentation uses MkDocs with the Material theme. Configuration is in `mkdocs.yml`:

```yaml
site_name: Clyde Package Manager
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
plugins:
  - search
  - mermaid2
```