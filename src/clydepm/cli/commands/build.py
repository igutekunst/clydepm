"""
Build command for Clydepm.
"""
from pathlib import Path
from typing import Optional, List, Dict
import sys

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...core.package import Package
from ...build.builder import Builder

# Create console for rich output
console = Console()


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