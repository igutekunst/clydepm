"""
Command-line interface for Clydepm.
"""
from pathlib import Path
from typing import Optional, List, Dict
import os
import sys
import subprocess
import shutil
from enum import Enum

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import print as rprint
from jinja2 import Environment, FileSystemLoader, Template

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

class Language(str, Enum):
    """Programming language for the package."""
    C = "c"
    CPP = "cpp"
    CXX = "cxx"
    CPLUSPLUS = "c++"
    
    @classmethod
    def from_str(cls, s: str) -> "Language":
        """Convert string to Language enum."""
        s = s.lower()
        if s in ("cpp", "cxx", "c++"):
            return cls.CPP
        elif s == "c":
            return cls.C
        else:
            raise ValueError(f"Unknown language: {s}")
            
    def __str__(self) -> str:
        """Convert Language enum to string."""
        if self == Language.CPP:
            return "C++"
        return self.value.upper()

def get_github_token() -> Optional[str]:
    """Get GitHub token from environment or config."""
    return os.getenv("GITHUB_TOKEN")

def _get_template_dir() -> Path:
    """Get the directory containing templates."""
    return Path(__file__).parent.parent / "templates"

def _list_templates() -> Dict[str, Path]:
    """List available templates."""
    template_dir = _get_template_dir()
    return {
        "c-app": template_dir / "c-app",  # C application template
        "cpp-lib": template_dir / "cpp-lib",  # C++ library template
        "c-lib": template_dir / "c-lib",  # C library template
    }

def _copy_template(src: Path, dst: Path, replacements: Dict[str, str]) -> None:
    """
    Copy template directory with variable replacement using Jinja2.
    
    Args:
        src: Source template directory
        dst: Destination directory
        replacements: Dictionary of template variables and their values
    """
    # Add uppercase versions of all replacements
    upper_replacements = {
        f"{k}_upper": v.upper()
        for k, v in replacements.items()
    }
    replacements.update(upper_replacements)
    
    # Create destination directory
    dst.mkdir(parents=True, exist_ok=True)
    
    # Create Jinja environment
    env = Environment(
        loader=FileSystemLoader(str(src)),
        keep_trailing_newline=True
    )
    
    for item in src.rglob("*"):
        # Skip __pycache__ and other hidden files
        if any(p.startswith('.') for p in item.parts):
            continue
            
        # Get relative path and replace template variables in path
        rel_path = item.relative_to(src)
        path_str = str(rel_path)
        
        # Replace {{var}} in path
        try:
            template = env.from_string(path_str)
            path_str = template.render(**replacements)
        except Exception as e:
            raise ValueError(f"Error processing path template: {path_str}: {e}")
            
        rel_path = Path(path_str)
        dst_path = dst / rel_path
        
        if item.is_dir():
            dst_path.mkdir(parents=True, exist_ok=True)
        else:
            # Replace template variables in content
            try:
                with open(item) as f:
                    template = env.from_string(f.read())
                content = template.render(**replacements)
            except Exception as e:
                raise ValueError(f"Error processing file template {item}: {e}")
            
            # Ensure parent directory exists
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            with open(dst_path, "w") as f:
                f.write(content)

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
    language: Language = typer.Option(
        None,
        "--lang", "-l",
        help="Programming language (c, cpp/cxx/c++)",
    ),
    template: str = typer.Option(
        None,
        "--template",
        help="Template to use (c-app, cpp-lib, or c-lib)",
    ),
    version: str = typer.Option(
        "0.1.0",
        "--version", "-v",
        help="Initial version",
    ),
) -> None:
    """Initialize a new package."""
    try:
        path = Path(path)
        
        # Use directory name if no name provided
        name = name or path.name
        
        # Determine language if not specified
        if language is None:
            language = Language.C if package_type == PackageType.APPLICATION else Language.CPP
            
        # Determine template
        templates = _list_templates()
        if template is None:
            if package_type == PackageType.APPLICATION:
                template = "c-app"  # Always use C for applications
            else:
                template = "cpp-lib" if language == Language.CPP else "c-lib"
            
        if template not in templates:
            available = ", ".join(templates.keys())
            rprint(f"[red]Error:[/red] Unknown template: {template}")
            rprint(f"Available templates: {available}")
            sys.exit(1)
            
        # Copy template with replacements
        replacements = {
            "name": name,
            "version": version,
        }
        _copy_template(templates[template], path, replacements)
        
        # Create package to validate
        package = Package(path)
        
        rprint(f"[green]✓[/green] Created {str(language)} {package_type.value} package in {path}")
        rprint("\nTo build and run:")
        rprint(f"  cd {path}")
        rprint("  clyde build")
        if package_type == PackageType.APPLICATION:
            rprint("  clyde run")
        
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
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Show compiler commands",
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
                
        # Add verbose trait if specified
        if verbose:
            trait_dict["verbose"] = "true"
        
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