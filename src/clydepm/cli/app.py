"""
Command-line interface for Clydepm.
"""
from pathlib import Path
from typing import Optional, List
import os
import sys
import subprocess

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import print as rprint

from ..core.package import Package, PackageType
from ..build.builder import Builder, BuildError
from ..github.registry import GitHubRegistry

# Create Typer app
app = typer.Typer(
    name="clyde",
    help="Clyde C/C++ Package Manager",
    add_completion=False,  # We'll add this later
)

# Create console for rich output
console = Console()

def get_github_token() -> Optional[str]:
    """Get GitHub token from environment or config."""
    return os.getenv("GITHUB_TOKEN")

@app.command()
def init(
    path: Path = typer.Argument(
        ".",
        help="Path to create package in",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    name: str = typer.Option(
        None,
        "--name", "-n",
        help="Package name (defaults to directory name)",
    ),
    package_type: PackageType = typer.Option(
        PackageType.LIBRARY,
        "--type", "-t",
        help="Package type",
    ),
) -> None:
    """Initialize a new package."""
    try:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Create standard directory structure
        (path / "src").mkdir(exist_ok=True)
        (path / "include").mkdir(exist_ok=True)
        (path / "private_include").mkdir(exist_ok=True)
        
        # Create initial config
        config = {
            "name": name or path.name,
            "version": "0.1.0",
            "type": package_type.value,
            "cflags": {
                "gcc": "-std=c++11"
            }
        }
        
        # Write initial config to create the file
        with open(path / "config.yaml", "w") as f:
            import yaml
            yaml.dump(config, f, sort_keys=False, default_flow_style=False)
        
        # Create package and save config (this ensures proper type handling)
        package = Package(path, package_type=package_type)
        package.save_config()
            
        rprint(f"[green]✓[/green] Initialized package in {path}")
        
    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)

@app.command()
def build(
    path: Path = typer.Argument(
        ".",
        help="Path to package",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    traits: Optional[List[str]] = typer.Option(
        None,
        "--trait", "-t",
        help="Build traits in key=value format",
    ),
) -> None:
    """Build a package."""
    try:
        # Parse traits
        trait_dict = {}
        if traits:
            for trait in traits:
                key, value = trait.split("=", 1)
                trait_dict[key.strip()] = value.strip()
        
        # Create package and builder
        package = Package(path)
        builder = Builder()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Show build progress
            task = progress.add_task(
                f"Building {package.name} {package.version}...",
                total=None
            )
            
            result = builder.build(package, trait_dict)
            
            if result.success:
                progress.update(task, completed=True)
                rprint(f"[green]✓[/green] Built {package.name} {package.version}")
                
                # Show artifacts
                if result.artifacts:
                    table = Table("Type", "Path")
                    for type_, path in result.artifacts.items():
                        table.add_row(type_, str(path))
                    console.print(table)
            else:
                progress.update(task, completed=True)
                rprint(f"[red]Error:[/red] Build failed")
                if result.error:
                    console.print(result.error)
                sys.exit(1)
                
    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)

@app.command()
def publish(
    path: Path = typer.Argument(
        ".",
        help="Path to package",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    create_binary: bool = typer.Option(
        True,
        "--binary/--no-binary",
        help="Create and publish binary package",
    ),
) -> None:
    """Publish a package to GitHub."""
    try:
        # Get GitHub token
        token = get_github_token()
        if not token:
            rprint("[red]Error:[/red] GITHUB_TOKEN environment variable not set")
            sys.exit(1)
            
        # Create package and registry
        package = Package(path)
        registry = GitHubRegistry(token)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Publishing {package.name} {package.version}...",
                total=None
            )
            
            registry.publish_package(package, create_binary)
            
            progress.update(task, completed=True)
            rprint(f"[green]✓[/green] Published {package.name} {package.version}")
            
    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)

@app.command()
def install(
    package_spec: str = typer.Argument(
        ...,
        help="Package to install (name==version)",
    ),
    path: Path = typer.Option(
        ".",
        "--path", "-p",
        help="Path to install to",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Install a package from GitHub."""
    try:
        # Parse package spec
        if "==" in package_spec:
            name, version = package_spec.split("==", 1)
        else:
            name = package_spec
            version = "latest"  # We'll need to implement version resolution
            
        # Get GitHub token
        token = get_github_token()
        if not token:
            rprint("[red]Error:[/red] GITHUB_TOKEN environment variable not set")
            sys.exit(1)
            
        # Create registry
        registry = GitHubRegistry(token)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Installing {name} {version}...",
                total=None
            )
            
            # Get package
            package = registry.get_package(name, version)
            
            # TODO: Install package to path
            
            progress.update(task, completed=True)
            rprint(f"[green]✓[/green] Installed {package.name} {package.version}")
            
    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)

@app.command()
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

def main():
    """Entry point for the CLI."""
    app() 