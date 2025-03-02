"""
Cache management commands for Clydepm.
"""
from pathlib import Path
import sys
import logging
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ...core.package import Package
from ...build.cache import BuildCache

# Create console for rich output
console = Console()
logger = logging.getLogger(__name__)

app = typer.Typer(name="cache", help="Manage the build cache.")

@app.command()
def clean(
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

@app.command(name="list")
def list_cache(
    package: Optional[str] = typer.Option(
        None,
        "--package", "-p",
        help="Filter by package name"
    ),
) -> None:
    """List cached artifacts."""
    try:
        cache = BuildCache()
        
        # Create table for output
        table = Table(show_header=True, header_style="bold")
        table.add_column("Package")
        table.add_column("Type")
        table.add_column("Size")
        table.add_column("Path")
        
        # List artifacts
        artifact_count = 0
        total_size = 0
        
        # Helper to format size
        def format_size(size_bytes):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024
            return f"{size_bytes:.1f} TB"
        
        # List final artifacts
        for artifact in cache.artifacts_dir.glob("*"):
            if package and not artifact.name.startswith(f"{package}-"):
                continue
                
            size = artifact.stat().st_size
            total_size += size
            artifact_count += 1
            
            pkg_name = artifact.name.split('-')[0]
            table.add_row(
                pkg_name,
                "Artifact",
                format_size(size),
                str(artifact.relative_to(cache.cache_dir))
            )
            
        # List object files
        for obj in cache.objects_dir.glob("*.o"):
            size = obj.stat().st_size
            total_size += size
            artifact_count += 1
            
            table.add_row(
                "N/A",
                "Object",
                format_size(size),
                str(obj.relative_to(cache.cache_dir))
            )
            
        if artifact_count == 0:
            if package:
                rprint(f"No cached artifacts found for package '{package}'")
            else:
                rprint("Cache is empty")
        else:
            console.print(table)
            rprint(f"\nTotal: {artifact_count} items ({format_size(total_size)})")
            
    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)

# Add list as an alias for ls
app.command(name="ls")(list_cache)