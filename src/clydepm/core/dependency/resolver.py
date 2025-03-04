"""
Dependency resolution for Clyde package manager.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import json
from pathlib import Path

from ..package import Package
from ..version import Version, VersionRange, VersionResolver

@dataclass
class DependencyNode:
    """Node in dependency graph."""
    package: Package
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)

class DependencyResolver:
    """Resolves package dependencies and determines build order."""
    
    def __init__(self):
        self.nodes: Dict[str, DependencyNode] = {}
        self.version_resolver = VersionResolver([])
        
    def add_package(self, package: Package, root_path: Optional[Path] = None) -> None:
        """Add package and all its dependencies to the graph.
        
        Args:
            package: Package to add
            root_path: Root path to search for dependencies (defaults to package path)
        """
        name = package._validated_config.name
        if name not in self.nodes:
            self.nodes[name] = DependencyNode(package=package)
            
        # Use root_path if provided, otherwise use package path
        search_path = root_path or package.path
            
        # Add dependencies
        for dep_name, dep_spec in package.get_dependencies().items():
            self.nodes[name].dependencies.add(dep_name)
            if dep_name not in self.nodes:
                # Create node for dependency
                if dep_name.startswith("@"):
                    # For @org/pkg format, create deps/@org/pkg
                    org = dep_name.split("/")[0][1:]  # Remove @ from org
                    pkg = dep_name.split("/")[1]
                    dep_path = search_path / "deps" / org / pkg
                else:
                    # For backward compatibility, use deps/pkg
                    dep_path = search_path / "deps" / dep_name
                    
                if dep_path.exists():
                    dep_pkg = Package(dep_path)
                    # Recursively add dependency and its dependencies
                    self.add_package(dep_pkg, root_path=search_path)
                else:
                    raise ValueError(f"Dependency {dep_name} not found at {dep_path}")
            self.nodes[dep_name].dependents.add(name)
            
    def detect_cycles(self) -> List[List[str]]:
        """Find circular dependencies in graph.
        
        Returns:
            List of cycles found, each cycle is a list of package names
        """
        cycles = []
        visited = set()
        path = []
        
        def visit(name: str) -> None:
            if name in path:
                cycle = path[path.index(name):]
                cycle.append(name)
                cycles.append(cycle)
                return
            if name in visited:
                return
                
            visited.add(name)
            path.append(name)
            
            for dep in self.nodes[name].dependencies:
                visit(dep)
                
            path.pop()
            
        for name in self.nodes:
            visit(name)
            
        return cycles
        
    def get_build_order(self) -> List[Package]:
        """Get packages in dependency-first build order.
        
        Returns:
            List of packages in build order
            
        Raises:
            ValueError: If circular dependencies found
        """
        cycles = self.detect_cycles()
        if cycles:
            cycle_str = " -> ".join(cycles[0])
            raise ValueError(f"Circular dependency detected: {cycle_str}")
            
        order = []
        visited = set()
        
        def visit(name: str) -> None:
            if name in visited:
                return
                
            visited.add(name)
            
            # Visit dependencies first
            for dep in self.nodes[name].dependencies:
                visit(dep)
                
            order.append(self.nodes[name].package)
            
        # Visit all nodes
        for name in self.nodes:
            visit(name)
            
        return order
        
    def export_graph(self, output_path: Optional[Path] = None) -> Dict:
        """Export dependency graph as JSON.
        
        Args:
            output_path: Optional path to write JSON file
            
        Returns:
            Dictionary representation of graph
        """
        graph = {
            "nodes": {},
            "edges": []
        }
        
        # Add nodes
        for name, node in self.nodes.items():
            graph["nodes"][name] = {
                "name": name,
                "version": node.package.version,
                "type": node.package.package_type.value,
                "organization": node.package.organization
            }
            
        # Add edges
        for name, node in self.nodes.items():
            for dep in node.dependencies:
                graph["edges"].append({
                    "from": name,
                    "to": dep
                })
                
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(graph, f, indent=2)
                
        return graph 