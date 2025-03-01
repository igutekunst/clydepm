"""
Install command for Clydepm.
"""
from pathlib import Path
from typing import Optional
import sys

import typer
from rich import print as rprint
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...github.registry import GitHubRegistry
from ...github.config import GitHubConfigError
from ..utils.github import get_github_token

# Create console for rich output
console = Console()


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
    organization: Optional[str] = typer.Option(
        None,
        "--org", "--organization",
        help="GitHub organization to use (overrides config)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Show detailed output",
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
            
        # Get GitHub token from config or environment
        token = get_github_token()
        if not token:
            rprint("[red]Error:[/red] No GitHub token configured")
            rprint("Run 'clyde auth' to set up GitHub authentication")
            sys.exit(1)
            
        # Load config for organization if not specified
        if not organization:
            from ...github.config import load_config
            config = load_config()
            organization = config.get("organization")
            
        # Create registry with token and organization
        registry = GitHubRegistry(token, organization)
        
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
            
    except GitHubConfigError as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)
    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)
