"""Integration tests for building and linking packages using actual clyde commands."""
import unittest
import subprocess
from pathlib import Path
import tempfile
import shutil
import os

class TestBuild(unittest.TestCase):
    """Test cases for building packages using actual clyde commands."""
    
    def setUp(self):
        """Set up test environment with a temporary directory."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_dir = Path.cwd()
        os.chdir(self.temp_dir)
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)
        
    def _run_clyde_command(self, command):
        """Run a clyde command and check for success."""
        result = subprocess.run(
            ["clyde"] + command.split(),  # Use installed clyde command
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, 
            f"Command 'clyde {command}' failed with:\nstdout: {result.stdout}\nstderr: {result.stderr}")
        return result
        
    def test_library_build(self):
        """Test creating and building a library package."""
        # Create library package
        lib_dir = self.temp_dir / "mylib"
        lib_dir.mkdir()
        os.chdir(lib_dir)
        
        # Initialize library package
        self._run_clyde_command("init --type library --name mylib")
        
        # Create library source
        src_dir = lib_dir / "src"
        with open(src_dir / "mylib.cpp", "w") as f:
            f.write("""
                int add(int a, int b) {
                    return a + b;
                }
            """)
            
        # Create library header
        include_dir = lib_dir / "include"
        with open(include_dir / "mylib.h", "w") as f:
            f.write("""
                #pragma once
                int add(int a, int b);
            """)
            
        # Build the library
        self._run_clyde_command("build")
        
        # Verify library was built
        lib_output = lib_dir / "build" / "libmylib.a"
        self.assertTrue(lib_output.exists(), "Library file was not created")
        self.assertGreater(lib_output.stat().st_size, 0, "Library file is empty")
        
    def test_application_with_library(self):
        """Test creating and building an application that uses a library."""
        # First create and build the library
        lib_dir = self.temp_dir / "mylib"
        lib_dir.mkdir()
        os.chdir(lib_dir)
        
        # Initialize and set up library
        self._run_clyde_command("init --type library --name mylib")
        
        with open(lib_dir / "src" / "mylib.cpp", "w") as f:
            f.write("""
                int add(int a, int b) {
                    return a + b;
                }
            """)
            
        with open(lib_dir / "include" / "mylib.h", "w") as f:
            f.write("""
                #pragma once
                int add(int a, int b);
            """)
            
        # Build the library
        self._run_clyde_command("build")
        
        # Create the application
        app_dir = self.temp_dir / "myapp"
        app_dir.mkdir()
        os.chdir(app_dir)
        
        # Initialize application
        self._run_clyde_command("init --type application --name myapp")
        
        # Add library as dependency
        # TODO: Add proper dependency management command once implemented
        deps_dir = app_dir / "deps" / "mylib"
        deps_dir.mkdir(parents=True)
        shutil.copytree(lib_dir / "include", deps_dir / "include")
        shutil.copytree(lib_dir / "build", deps_dir / "build")
        
        # Create application source that uses the library
        with open(app_dir / "src" / "main.cpp", "w") as f:
            f.write("""
                #include <mylib.h>
                #include <iostream>
                
                int main() {
                    int result = add(1, 2);
                    std::cout << "1 + 2 = " << result << std::endl;
                    return result == 3 ? 0 : 1;
                }
            """)
            
        # Build the application
        self._run_clyde_command("build")
        
        # Verify application was built
        app_output = app_dir / "build" / "myapp"
        self.assertTrue(app_output.exists(), "Application binary was not created")
        self.assertGreater(app_output.stat().st_size, 0, "Application binary is empty")
        
        # Run the application to verify it works
        result = subprocess.run(
            str(app_output),
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, "Application returned non-zero exit code")
        self.assertIn("1 + 2 = 3", result.stdout, "Application output incorrect")

if __name__ == "__main__":
    unittest.main() 