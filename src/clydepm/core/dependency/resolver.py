"""
Dependency resolution for Clyde package manager.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import json
from pathlib import Path
import subprocess
import tempfile
import logging
import time

from ..package import Package
from ..version import Version, VersionRange, VersionResolver

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class DependencyNode:
    """Node in dependency graph."""
    package: Package
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)

class DependencyResolver:
    """Resolves package dependencies and determines build order."""
    
    def __init__(self, verbose: bool = False):
        self.nodes: Dict[str, DependencyNode] = {}
        self.version_resolver = VersionResolver([])
        self.verbose = verbose
        if verbose:
            logger.setLevel(logging.DEBUG)
        
    def _validate_package_name(self, package: Package, dep_path: Path) -> None:
        """Validate that a package's name matches its installation path.
        
        Args:
            package: Package to validate
            dep_path: Path where the package is installed
            
        Raises:
            ValueError: If package name doesn't match installation path
        """
        # Only validate packages in deps/ directory
        if "deps" not in str(dep_path):
            return
            
        # Find the deps directory in the path
        parts = dep_path.parts
        try:
            deps_index = parts.index("deps")
            # Get everything after "deps/"
            rel_parts = parts[deps_index + 1:]
            expected_name = str(Path(*rel_parts))
            
            if package.name != expected_name:
                error_msg = (
                    f"Package name mismatch:\n"
                    f"  Installed at: deps/{expected_name}\n"
                    f"  But package.yml has name: {package.name}\n"
                    f"This can happen if:\n"
                    f"  1. The package was installed incorrectly\n"
                    f"  2. The package.yml was modified after installation\n"
                    f"  3. The package name was changed without updating the directory structure\n"
                    f"\nTo fix this:\n"
                    f"  1. Make sure the package name in package.yml matches its installation path\n"
                    f"  2. For scoped packages, the name should include the organization (e.g. '@org/pkg')\n"
                    f"  3. The directory structure should match the package name (e.g. 'deps/@org/pkg')"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
        except ValueError:
            # If "deps" is not in the path, something is wrong with the directory structure
            logger.error(f"Invalid package path: {dep_path} (no deps/ directory found)")
            raise ValueError(f"Invalid package path: {dep_path} (no deps/ directory found)")
        
    def add_package(self, package: Package, root_path: Optional[Path] = None) -> None:
        """Add package and all its dependencies to the graph.
        
        Args:
            package: Package to add
            root_path: Root path to search for dependencies (defaults to package path)
        """
        # Use the full package name (including organization if present)
        name = package.name
        logger.debug(f"Adding package {name} to dependency graph")
        logger.debug(f"Package path: {package.path}")
        logger.debug(f"Package organization: {package.organization}")
        logger.debug(f"Package name (without org): {package.package_name}")
            
        if name not in self.nodes:
            logger.debug(f"Creating new node for {name}")
            self.nodes[name] = DependencyNode(package=package)
        else:
            logger.debug(f"Package {name} already in graph")
            
        # Use root_path if provided, otherwise use package path
        search_path = root_path or package.path
        logger.debug(f"Using search path: {search_path}")
            
        # Add dependencies
        deps = package.get_dependencies()
        logger.debug(f"Package {name} has dependencies: {deps}")
        
        for dep_name, dep_spec in deps.items():
            logger.debug(f"Processing dependency {dep_name} with spec {dep_spec}")
            
            # Handle local dependencies
            if isinstance(dep_spec, str) and dep_spec.startswith("local:"):
                local_path = dep_spec[6:]  # Remove "local:" prefix
                dep_path = (search_path / local_path).resolve()
                logger.debug(f"Checking local dependency path: {dep_path}")
                
                if dep_path.exists() and (dep_path / "package.yml").exists():
                    try:
                        dep_pkg = Package(dep_path)
                        # For local dependencies, we use the name from the requires section
                        # since the actual package name might be different
                        logger.debug(f"Successfully loaded local package {dep_name}")
                        
                        # Add to graph if not already present
                        if dep_name not in self.nodes:
                            logger.debug(f"Adding local dependency {dep_name} to graph")
                            # Store the package under the name used in requires
                            self.nodes[dep_name] = DependencyNode(package=dep_pkg)
                            # Process its dependencies
                            self.add_package(dep_pkg, root_path=search_path)
                        
                        # Add relationship if not already present
                        self.nodes[name].dependencies.add(dep_name)
                        self.nodes[dep_name].dependents.add(name)
                        logger.debug(f"Added local dependency relationship: {name} -> {dep_name}")
                        continue
                    except Exception as e:
                        logger.debug(f"Failed to load local package: {e}")
                        raise ValueError(f"Failed to load local dependency {dep_name} at {dep_path}: {e}")
                else:
                    raise ValueError(f"Local dependency {dep_name} not found at {dep_path}")
            
            # Try different possible dependency paths for non-local dependencies
            dep_paths = []
            
            # Get the root path for dependency resolution
            root_search_path = search_path
            while "deps" in str(root_search_path):
                root_search_path = root_search_path.parent
            
            if dep_name.startswith("@"):
                # New format: @org/pkg -> deps/@org/pkg (keep @ in filesystem path)
                org = dep_name.split("/")[0]  # Keep @ in org
                pkg = dep_name.split("/")[1]
                dep_path = root_search_path / "deps" / org / pkg
                logger.debug(f"Checking scoped path: {dep_path}")
                dep_paths.append(dep_path)
            else:
                # Old format: pkg -> deps/pkg
                dep_path = root_search_path / "deps" / dep_name
                logger.debug(f"Checking legacy path: {dep_path}")
                dep_paths.append(dep_path)
                
            # Try each possible path
            dep_pkg = None
            for dep_path in dep_paths:
                pkg_yml = dep_path / "package.yml"
                logger.debug(f"Looking for package.yml at: {pkg_yml}")
                
                if dep_path.exists() and pkg_yml.exists():
                    try:
                        logger.debug(f"Found package.yml, attempting to load package")
                        dep_pkg = Package(dep_path)
                        # Validate package name matches its path
                        self._validate_package_name(dep_pkg, dep_path)
                        # Use the full package name for comparison
                        if dep_pkg.name == dep_name:
                            logger.debug(f"Successfully loaded package {dep_name}")
                            break
                        else:
                            logger.debug(f"Package name mismatch: expected {dep_name}, got {dep_pkg.name}")
                    except Exception as e:
                        logger.debug(f"Failed to load package: {e}")
                        continue
                else:
                    logger.debug(f"Path {dep_path} or package.yml does not exist")
            
            if dep_pkg is None:
                paths_str = "\n  - ".join(str(p) for p in dep_paths)
                error_msg = (
                    f"Dependency '{dep_name}' not found in any of these locations:\n"
                    f"  - {paths_str}\n"
                    f"This could mean:\n"
                    f"  1. The package hasn't been installed (run 'clyde install')\n"
                    f"  2. The package name is incorrect in package.yml\n"
                    f"  3. The package version doesn't match the requirement: {dep_spec}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Make sure the dependency node exists before adding relationships
            if dep_name not in self.nodes:
                # Recursively add dependency and its dependencies
                logger.debug(f"Recursively adding dependencies for {dep_name}")
                self.add_package(dep_pkg, root_path=search_path)
            
            # Now that we know both nodes exist, add the relationship
            self.nodes[name].dependencies.add(dep_name)
            self.nodes[dep_name].dependents.add(name)
            logger.debug(f"Added dependency relationship: {name} -> {dep_name}")
            
    def detect_cycles(self) -> List[List[str]]:
        """Find circular dependencies in graph.
        
        Returns:
            List of cycles found, each cycle is a list of package names
        """
        logger.debug("Starting cycle detection")
        cycles = []
        visited = set()
        path = []
        
        def visit(name: str) -> None:
            logger.debug(f"Visiting node {name}")
            logger.debug(f"Current path: {' -> '.join(path)}")
            
            if name in path:
                cycle = path[path.index(name):]
                cycle.append(name)
                logger.warning(f"Found cycle: {' -> '.join(cycle)}")
                cycles.append(cycle)
                return
                
            if name in visited:
                logger.debug(f"Already visited {name}, skipping")
                return
                
            visited.add(name)
            path.append(name)
            
            for dep in self.nodes[name].dependencies:
                logger.debug(f"Checking dependency {dep} of {name}")
                visit(dep)
                
            path.pop()
            
        for name in self.nodes:
            logger.debug(f"Starting cycle detection from root {name}")
            visit(name)
            
        if cycles:
            logger.warning(f"Found {len(cycles)} cycles in dependency graph")
        else:
            logger.debug("No cycles found in dependency graph")
            
        return cycles
        
    def get_build_order(self) -> List[Package]:
        """Get packages in dependency-first build order.
        
        Returns:
            List of packages in build order
            
        Raises:
            ValueError: If circular dependencies found
        """
        logger.debug("Calculating build order")
        cycles = self.detect_cycles()
        if cycles:
            cycle_str = " -> ".join(cycles[0])
            error_msg = f"Circular dependency detected: {cycle_str}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        order = []
        visited = set()
        
        def visit(name: str) -> None:
            logger.debug(f"Visiting node {name} for build order")
            
            if name in visited:
                logger.debug(f"Already processed {name}, skipping")
                return
                
            visited.add(name)
            
            # Visit dependencies first
            for dep in self.nodes[name].dependencies:
                logger.debug(f"Processing dependency {dep} before {name}")
                visit(dep)
                
            logger.debug(f"Adding {name} to build order")
            order.append(self.nodes[name].package)
            
        # Visit all nodes
        for name in self.nodes:
            logger.debug(f"Starting build order calculation from {name}")
            visit(name)
            
        logger.debug(f"Final build order: {[pkg.name for pkg in order]}")
        return order
        
    def export_graph(self, output_path: Optional[Path] = None) -> Dict:
        """Export dependency graph as JSON.
        
        Args:
            output_path: Optional path to write JSON file
            
        Returns:
            Dictionary representation of graph
        """
        logger.debug("Exporting dependency graph to JSON")
        graph = {
            "nodes": {},
            "edges": []
        }
        
        # Add nodes
        logger.debug("Adding nodes to graph export")
        for name, node in self.nodes.items():
            logger.debug(f"Adding node {name}")
            graph["nodes"][name] = {
                "name": name,
                "version": node.package.version,
                "type": node.package.package_type.value,
                "organization": node.package.organization
            }
            
        # Add edges
        logger.debug("Adding edges to graph export")
        for name, node in self.nodes.items():
            for dep in node.dependencies:
                logger.debug(f"Adding edge {name} -> {dep}")
                graph["edges"].append({
                    "from": name,
                    "to": dep
                })
                
        if output_path:
            logger.debug(f"Writing graph to {output_path}")
            with open(output_path, 'w') as f:
                json.dump(graph, f, indent=2)
                
        return graph 

    def visualize_graph(self, output_path: Optional[Path] = None, format: str = "png") -> Optional[Path]:
        """Visualize dependency graph using Graphviz.
        
        Args:
            output_path: Optional path to save the visualization
            format: Output format (png, svg, pdf)
            
        Returns:
            Path to the generated visualization file if output_path is provided
        """
        logger.debug(f"Visualizing dependency graph in {format} format")
        try:
            # Check if graphviz is installed
            logger.debug("Checking for Graphviz installation")
            subprocess.run(["dot", "-V"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            error_msg = "Graphviz is not installed. Please install it to generate visualizations."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        # Create DOT file content
        logger.debug("Generating DOT file content")
        dot_content = ["digraph G {"]
        dot_content.append("  rankdir=LR;")  # Left to right layout
        dot_content.append("  node [shape=box, style=rounded];")
        
        # Add nodes
        logger.debug("Adding nodes to DOT file")
        for name, node in self.nodes.items():
            # Extract organization if present
            org = None
            if name.startswith("@"):
                org = name.split("/")[0]
                logger.debug(f"Found organization {org} for node {name}")
                
            # Set node color based on package type
            color = {
                "library": "lightblue",
                "application": "lightgreen",
                "foreign": "lightgrey"
            }.get(node.package.package_type.value, "white")
            
            # Create label with package info
            label = f"{name}\\n{node.package.version}"
            logger.debug(f"Creating node {name} with label {label} and color {color}")
            
            # Add node with styling
            dot_content.append(f'  "{name}" [label="{label}", fillcolor="{color}", style="rounded,filled"'
                             f'{f", tooltip=\"Organization: {org}\"" if org else ""}'
                             "];")
            
        # Add edges
        logger.debug("Adding edges to DOT file")
        for name, node in self.nodes.items():
            for dep in node.dependencies:
                logger.debug(f"Adding edge {name} -> {dep}")
                dot_content.append(f'  "{name}" -> "{dep}";')
                
        dot_content.append("}")
        
        # Create temporary DOT file
        logger.debug("Writing temporary DOT file")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".dot", delete=False) as dot_file:
            dot_file.write("\n".join(dot_content))
            dot_path = Path(dot_file.name)
            logger.debug(f"Temporary DOT file created at {dot_path}")
            
        try:
            # Generate output file
            if output_path is None:
                output_path = dot_path.with_suffix(f".{format}")
                logger.debug(f"No output path provided, using {output_path}")
                
            logger.debug(f"Generating {format} file using dot command")
            subprocess.run(
                ["dot", "-T" + format, str(dot_path), "-o", str(output_path)],
                check=True,
                capture_output=True
            )
            logger.debug(f"Graph visualization saved to {output_path}")
            
            return output_path
            
        finally:
            # Clean up temporary file
            logger.debug(f"Cleaning up temporary DOT file {dot_path}")
            dot_path.unlink()
            
    def view_graph(self) -> None:
        """Open the dependency graph visualization in the default viewer."""
        logger.debug("Opening graph visualization in default viewer")
        # Generate visualization in a temporary file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            logger.debug(f"Created temporary PNG file at {tmp_path}")
            
        try:
            # Generate the graph
            logger.debug("Generating graph visualization")
            self.visualize_graph(output_path=tmp_path)
            
            # Open with default viewer and wait for it to start
            logger.debug("Opening visualization with system viewer")
            try:
                subprocess.run(["open", str(tmp_path)], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback for non-macOS systems
                logger.debug("MacOS open failed, trying xdg-open")
                try:
                    subprocess.run(["xdg-open", str(tmp_path)], check=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    logger.error("Failed to open graph with system viewer")
                    rprint("[yellow]Warning:[/yellow] Could not open graph with system viewer")
                    rprint(f"The graph has been saved to: {tmp_path}")
                    return  # Don't delete the file if we couldn't open it
                
            # Give the viewer a moment to read the file
            time.sleep(1)
            
        finally:
            try:
                # Clean up temporary file
                logger.debug(f"Cleaning up temporary PNG file {tmp_path}")
                tmp_path.unlink()
            except Exception as e:
                # If we can't delete the file, just log it
                logger.debug(f"Failed to clean up temporary file: {e}")
                pass 