# Build Inspector

The Build Inspector (`clyde inspect`) is an interactive tool for visualizing and analyzing your project's dependencies and build process.

## Quick Start

```bash
# Start the inspector
clyde inspect

# Open in specific port
clyde inspect --port 3000

# Open automatically in browser
clyde inspect --open
```

## Features

### Dependency Graph
- Interactive visualization of package dependencies
- Package metadata display
- Version conflict highlighting
- Source file exploration

### Build Information
- Build timing analysis
- Cache hit/miss statistics
- Compilation command inspection
- Resource usage monitoring

### Navigation
- Zoom and pan controls
- Search functionality
- Multiple layout options
- Node expansion/collapse

## Usage Guide

### Viewing Dependencies

1. Start the inspector:
   ```bash
   clyde inspect --open
   ```

2. Navigate the graph:
   - Click and drag to pan
   - Scroll to zoom
   - Click nodes to expand/collapse

3. View package details:
   - Click package nodes for metadata
   - Expand nodes for source files
   - View compilation commands

### Build Analysis

1. During builds:
   - Watch real-time progress
   - Monitor cache performance
   - Track compilation times

2. After builds:
   - Review build statistics
   - Analyze bottlenecks
   - Export build reports

### Troubleshooting

Common issues and solutions:

1. **Port in use**
   ```bash
   # Use alternative port
   clyde inspect --port 3001
   ```

2. **Browser not opening**
   ```bash
   # Manual URL
   open http://localhost:3000
   ```

3. **Slow performance**
   - Collapse unused nodes
   - Filter unnecessary information
   - Use search to focus on specific packages

## Integration

### IDE Support
- VSCode extension (coming soon)
- Direct file opening
- Build integration

### Export Options
- PNG/SVG export
- Build reports
- Dependency documentation

## Tips and Tricks

1. **Efficient Navigation**
   - Use keyboard shortcuts
   - Utilize search filters
   - Save common views

2. **Performance Optimization**
   - Monitor cache usage
   - Identify build bottlenecks
   - Track dependency impact

3. **Dependency Management**
   - Identify unused dependencies
   - Spot version conflicts
   - Review security issues

## Related Documentation

- [Build System](../architecture/build-system.md)
- [Cache System](../architecture/cache-system.md)
- [Package Management](../architecture/package-management.md)
- [Build Inspector Design](../development/inspect.md)

## Future Features

See the [roadmap](../development/roadmap.md) for planned enhancements:

- Real-time build updates
- Advanced filtering
- Custom layouts
- IDE integration
- Performance improvements 