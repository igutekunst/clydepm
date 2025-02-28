"""
Run command for Clydepm.
"""
from pathlib import Path
from typing import Optional, List
import sys
import subprocess

import typer
from rich import print as rprint
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...core.package import Package, PackageType
from ...build.builder import Builder

# Create console for rich output
console = Console()


def run(
    path: Path = typer.Argument(
        ".",
        help="Path to package",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    args: Optional[List[str]] = typer.Argument(
        None,
        help="Arguments to pass to the application",
    ),
) -> None:
    """Run an application package."""
    try:
        # Create package
        package = Package(path)
        
        # Check package type
        if package.package_type != PackageType.APPLICATION:
            rprint(f"[red]Error:[/red] Package {package.name} is not an application")
            sys.exit(1)
            
        # Get executable path
        executable = package.get_output_path()
        if not executable.exists():
            # Try building first
            builder = Builder()
            result = builder.build(package)
            if not result.success:
                rprint(f"[red]Error:[/red] Failed to build {package.name}")
                if result.error:
                    console.print(result.error)
                sys.exit(1)
                
        # Run the executable
        cmd = [str(executable)]
        if args:
            cmd.extend(args)
            
        try:
            result = subprocess.run(cmd, check=True)
            sys.exit(result.returncode)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)
            
    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1) 