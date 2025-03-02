"""
Cache management commands for Clydepm.
"""
from pathlib import Path
import sys
import logging

import typer
from rich import print as rprint
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...core.package import Package
from ...build.cache import BuildCache

# Create console for rich output
console = Console()
logger = logging.getLogger(__name__)

def cache(
    clean_all: bool = typer.Option(
        False,
        "--all",
        help="Clean the entire cache, not just the current package"
    ),
) -> None:
    """Clean build cache artifacts."""
    try:
        cache = BuildCache()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            if clean_all:
                task = progress.add_task("Cleaning entire build cache...", total=None)
                logger.info("Cleaning entire build cache...")
                cache.clean()
                progress.update(task, completed=True)
                rprint("[green]✓[/green] Cache cleaned successfully")
            else:
                try:
                    # Load package from current directory
                    package = Package(Path.cwd())
                    task = progress.add_task(f"Cleaning cache for package {package.name}...", total=None)
                    logger.info("Cleaning cache for package %s...", package.name)
                    
                    # Clean package artifacts
                    cache.clean_package(package)
                    progress.update(task, completed=True)
                    rprint(f"[green]✓[/green] Cache cleaned for package {package.name}")
                    
                except FileNotFoundError:
                    rprint("[red]Error:[/red] No package found in current directory")
                    sys.exit(1)
                    
    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)