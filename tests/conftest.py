"""Shared pytest fixtures and configuration."""
import pytest
from pathlib import Path
import tempfile
import shutil
import os

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    original_dir = Path.cwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_dir)
    shutil.rmtree(temp_dir) 