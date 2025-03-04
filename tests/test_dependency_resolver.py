"""Tests for dependency resolution."""
import json
from pathlib import Path
import pytest
from clydepm.core.package import Package, PackageType
from clydepm.core.dependency.resolver import DependencyResolver

@pytest.fixture
def temp_package_tree(tmp_path):
    """Create a temporary package tree for testing."""
    # Create root package
    root = tmp_path / "root"
    root.mkdir()
    with open(root / "package.yml", "w") as f:
        f.write("""
name: root-pkg
version: 1.0.0
type: application
language: c
sources:
    - src/main.c
requires:
    "@org1/lib1": "^1.0.0"
    "@org2/lib2": "^2.0.0"
""")

    # Create lib1 package
    lib1 = root / "deps" / "org1" / "lib1"
    lib1.mkdir(parents=True)
    with open(lib1 / "package.yml", "w") as f:
        f.write("""
name: "@org1/lib1"
version: 1.0.0
type: library
language: c
sources:
    - src/lib.c
requires:
    "@org2/lib2": "^2.0.0"
""")

    # Create lib2 package
    lib2 = root / "deps" / "org2" / "lib2"
    lib2.mkdir(parents=True)
    with open(lib2 / "package.yml", "w") as f:
        f.write("""
name: "@org2/lib2"
version: 2.0.0
type: library
language: c
sources:
    - src/lib.c
requires: {}
""")

    return root

@pytest.fixture
def temp_package_with_headers(tmp_path):
    """Create a temporary package with headers for testing."""
    # Create package with properly namespaced headers
    pkg1 = tmp_path / "pkg1"
    pkg1.mkdir()
    (pkg1 / "include" / "pkg1").mkdir(parents=True)
    with open(pkg1 / "include" / "pkg1" / "api.h", "w") as f:
        f.write("// API header")
    with open(pkg1 / "package.yml", "w") as f:
        f.write("""
name: pkg1
version: 1.0.0
type: library
language: c
sources:
    - src/lib.c
requires: {}
""")

    # Create package with non-namespaced headers
    pkg2 = tmp_path / "pkg2"
    pkg2.mkdir()
    (pkg2 / "include").mkdir()
    with open(pkg2 / "include" / "api.h", "w") as f:
        f.write("// API header")
    with open(pkg2 / "package.yml", "w") as f:
        f.write("""
name: pkg2
version: 1.0.0
type: library
language: c
sources:
    - src/lib.c
requires: {}
""")

    return tmp_path

def test_dependency_resolution(temp_package_tree):
    """Test basic dependency resolution."""
    root_pkg = Package(temp_package_tree)
    resolver = DependencyResolver()
    resolver.add_package(root_pkg)

    # Check nodes
    assert len(resolver.nodes) == 3
    assert "@org1/lib1" in resolver.nodes
    assert "@org2/lib2" in resolver.nodes

    # Check dependencies
    assert resolver.nodes["root-pkg"].dependencies == {"@org1/lib1", "@org2/lib2"}
    assert resolver.nodes["@org1/lib1"].dependencies == {"@org2/lib2"}
    assert resolver.nodes["@org2/lib2"].dependencies == set()

    # Check build order
    build_order = resolver.get_build_order()
    assert len(build_order) == 3
    assert build_order[0].name == "@org2/lib2"  # Should be built first
    assert build_order[1].name == "@org1/lib1"  # Depends on lib2
    assert build_order[2].name == "root-pkg"    # Depends on both

def test_cycle_detection(temp_package_tree):
    """Test circular dependency detection."""
    # Modify lib2 to create a cycle
    lib2_yml = temp_package_tree / "deps" / "org2" / "lib2" / "package.yml"
    with open(lib2_yml, "w") as f:
        f.write("""
name: "@org2/lib2"
version: 2.0.0
type: library
language: c
sources:
    - src/lib.c
requires:
    "@org1/lib1": "^1.0.0"
""")

    root_pkg = Package(temp_package_tree)
    resolver = DependencyResolver()
    resolver.add_package(root_pkg)

    cycles = resolver.detect_cycles()
    assert len(cycles) == 1
    assert set(cycles[0]) == {"@org1/lib1", "@org2/lib2"}

    # Build order should raise error
    with pytest.raises(ValueError, match="Circular dependency detected"):
        resolver.get_build_order()

def test_header_conflict_detection(temp_package_with_headers):
    """Test header conflict detection."""
    pkg1 = Package(temp_package_with_headers / "pkg1")
    pkg2 = Package(temp_package_with_headers / "pkg2")

    # Check header conflicts
    conflicts = pkg1.check_header_conflicts(pkg2)
    assert "api.h" in conflicts  # Should detect conflict due to pkg2's non-namespaced header

    # Validate header organization
    pkg1_warnings = pkg1.validate_header_organization()
    assert len(pkg1_warnings) == 0  # pkg1 has proper organization

    pkg2_warnings = pkg2.validate_header_organization()
    assert len(pkg2_warnings) == 2  # pkg2 has two issues: missing namespace dir and header in wrong location
    assert any("Missing package namespace directory" in w for w in pkg2_warnings)
    assert any("should be in include/pkg2/" in w for w in pkg2_warnings)

def test_dependency_graph_export(temp_package_tree):
    """Test dependency graph export."""
    root_pkg = Package(temp_package_tree)
    resolver = DependencyResolver()
    resolver.add_package(root_pkg)

    # Export graph
    graph = resolver.export_graph()

    # Check nodes
    assert len(graph["nodes"]) == 3
    assert "@org1/lib1" in graph["nodes"]
    assert "@org2/lib2" in graph["nodes"]
    assert "root-pkg" in graph["nodes"]

    # Check edges
    edges = graph["edges"]
    assert {"from": "root-pkg", "to": "@org1/lib1"} in edges
    assert {"from": "root-pkg", "to": "@org2/lib2"} in edges
    assert {"from": "@org1/lib1", "to": "@org2/lib2"} in edges

    # Check organization info
    assert graph["nodes"]["@org1/lib1"]["organization"] == "org1"
    assert graph["nodes"]["@org2/lib2"]["organization"] == "org2"
    assert graph["nodes"]["root-pkg"]["organization"] is None

@pytest.fixture
def temp_missing_package_tree(tmp_path):
    """Create a temporary package tree with a missing dependency."""
    # Create root package
    root = tmp_path / "root"
    root.mkdir()
    with open(root / "package.yml", "w") as f:
        f.write("""
name: root-pkg
version: 1.0.0
type: application
language: c
sources:
    - src/main.c
requires:
    "@igutekunst/ooc": "^1.0.0"
""")
    return root

def test_missing_scoped_dependency(temp_missing_package_tree):
    """Test handling of missing scoped dependencies."""
    root_pkg = Package(temp_missing_package_tree)
    resolver = DependencyResolver(verbose=True)
    
    # The resolver should raise a ValueError with details about the missing dependency
    with pytest.raises(ValueError) as exc_info:
        resolver.add_package(root_pkg)
    
    error_msg = str(exc_info.value)
    assert "@igutekunst/ooc" in error_msg
    assert "deps/igutekunst/ooc" in error_msg  # Should show the attempted path

def test_dependency_node_access(temp_package_tree):
    """Test that node access in the dependency graph is correct."""
    root_pkg = Package(temp_package_tree)
    resolver = DependencyResolver(verbose=True)
    
    # Add the root package
    resolver.add_package(root_pkg)
    
    # Verify that we can access the nodes correctly
    assert "root-pkg" in resolver.nodes
    assert "@org1/lib1" in resolver.nodes
    assert "@org2/lib2" in resolver.nodes
    
    # Verify that we can access the dependents and dependencies
    assert resolver.nodes["root-pkg"].dependencies == {"@org1/lib1", "@org2/lib2"}
    assert resolver.nodes["@org1/lib1"].dependencies == {"@org2/lib2"}
    assert resolver.nodes["@org2/lib2"].dependencies == set()
    
    assert resolver.nodes["@org1/lib1"].dependents == {"root-pkg"}
    assert resolver.nodes["@org2/lib2"].dependents == {"root-pkg", "@org1/lib1"}
    assert resolver.nodes["root-pkg"].dependents == set() 