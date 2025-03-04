from pathlib import Path
import json
import time
from unittest.mock import MagicMock, patch

import pytest

from clydepm.build.collector import BuildDataCollector, BuildData, CompilationStep
from clydepm.build.hooks import BuildContext, BuildStage
from clydepm.core.package import Package, CompilerInfo, BuildMetadata, Version

@pytest.fixture
def temp_output_dir(tmp_path):
    return tmp_path / "build_data"

@pytest.fixture
def collector(temp_output_dir):
    return BuildDataCollector(temp_output_dir)

@pytest.fixture
def mock_package():
    package = MagicMock(spec=Package)
    package.name = "test_package"
    package.version = Version.parse("1.0.0")
    
    # Create mock dependencies with proper string names
    dep1 = MagicMock(spec=Package)
    dep1.name = "dep1"
    dep1.version = Version.parse("0.1.0")
    
    dep2 = MagicMock(spec=Package)
    dep2.name = "dep2"
    dep2.version = Version.parse("0.2.0")
    
    package.get_all_dependencies.return_value = [dep1, dep2]
    return package

@pytest.fixture
def mock_compiler_info():
    return CompilerInfo(
        name="g++",
        version="11.0.0",
        target="x86_64-linux-gnu"
    )

@pytest.fixture
def mock_build_metadata(mock_compiler_info):
    metadata = MagicMock(spec=BuildMetadata)
    metadata.compiler_info = mock_compiler_info
    metadata.includes = [Path("/usr/include"), Path("/usr/local/include")]
    return metadata

@pytest.fixture
def mock_context(mock_package, mock_build_metadata):
    return BuildContext(
        package=mock_package,
        build_metadata=mock_build_metadata,
        traits={"opt": "debug"},
        verbose=True,
        source_file=Path("src/main.cpp"),
        object_file=Path("build/main.o"),
        command=["g++", "-c", "src/main.cpp", "-o", "build/main.o"]
    )

def test_collector_initialization(temp_output_dir):
    """Test collector initialization creates output directory."""
    collector = BuildDataCollector(temp_output_dir)
    assert temp_output_dir.exists()
    assert collector.current_build is None
    assert collector.current_step is None

def test_build_start(collector, mock_context):
    """Test build start hook creates BuildData."""
    collector._on_build_start(mock_context)
    
    assert collector.current_build is not None
    assert collector.current_build.package_name == "test_package"
    assert collector.current_build.package_version == "1.0.0"
    assert collector.current_build.compiler_info == {
        "name": "g++",
        "version": "11.0.0",
        "target": "x86_64-linux-gnu"
    }

def test_compile_start(collector, mock_context):
    """Test compile start hook creates CompilationStep."""
    collector._on_compile_start(mock_context)
    
    assert collector.current_step is not None
    assert collector.current_step.source_file == "src/main.cpp"
    assert collector.current_step.object_file == "build/main.o"
    assert collector.current_step.command == ["g++", "-c", "src/main.cpp", "-o", "build/main.o"]
    assert collector.current_step.include_paths == ["/usr/include", "/usr/local/include"]

def test_compile_end(collector, mock_context):
    """Test compile end hook updates and stores CompilationStep."""
    collector.current_build = BuildData(
        package_name="test",
        package_version="1.0.0",
        start_time=time.time(),
        compiler_info={}
    )
    collector._on_compile_start(mock_context)
    collector._on_compile_end(mock_context)
    
    assert collector.current_step is None
    assert len(collector.current_build.compilation_steps) == 1
    step = collector.current_build.compilation_steps[0]
    assert step.success
    assert step.end_time > step.start_time

def test_dependencies_built(collector, mock_context):
    """Test dependencies built hook records dependencies."""
    collector.current_build = BuildData(
        package_name="test",
        package_version="1.0.0",
        start_time=time.time(),
        compiler_info={}
    )
    collector._on_dependencies_built(mock_context)
    
    assert collector.current_build.dependencies == {
        "dep1": "0.1.0",
        "dep2": "0.2.0"
    }

def test_build_end(collector, mock_context, temp_output_dir):
    """Test build end hook saves data to file."""
    collector.current_build = BuildData(
        package_name="test",
        package_version="1.0.0",
        start_time=time.time(),
        compiler_info={}
    )
    collector._on_build_end(mock_context)
    
    # Check that a file was created
    files = list(temp_output_dir.glob("build_test_*.json"))
    assert len(files) == 1
    
    # Check file contents
    with open(files[0]) as f:
        data = json.load(f)
        assert data["package"]["name"] == "test"
        assert data["package"]["version"] == "1.0.0"
        assert data["success"]
        assert data["timing"]["end"] is not None

def test_full_build_flow(collector, mock_context, temp_output_dir):
    """Test complete build flow with all hooks."""
    # Start build
    collector._on_build_start(mock_context)
    
    # Compile first file
    mock_context.source_file = Path("src/main.cpp")
    mock_context.object_file = Path("build/main.o")
    collector._on_compile_start(mock_context)
    collector._on_compile_end(mock_context)
    
    # Compile second file
    mock_context.source_file = Path("src/utils.cpp")
    mock_context.object_file = Path("build/utils.o")
    collector._on_compile_start(mock_context)
    collector._on_compile_end(mock_context)
    
    # Record dependencies
    collector._on_dependencies_built(mock_context)
    
    # End build
    collector._on_build_end(mock_context)
    
    # Check output file
    files = list(temp_output_dir.glob("build_test_package_*.json"))
    assert len(files) == 1
    
    with open(files[0]) as f:
        data = json.load(f)
        assert data["package"]["name"] == "test_package"
        assert len(data["compilation_steps"]) == 2
        assert data["dependencies"] == {"dep1": "0.1.0", "dep2": "0.2.0"}
        assert data["success"] 