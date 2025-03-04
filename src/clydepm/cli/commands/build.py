"""
Build command for Clydepm.
"""
from pathlib import Path
from typing import Optional, List, Dict
import sys
import logging

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler

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
    verbose: int = typer.Option(
        0,
        "--verbose", "-v",
        count=True,
        help="Verbosity level (-v for basic output, -vv for full debug output)",
    ),
) -> None:
    """Build a package."""
    try:
        # Configure console logging based on verbosity
        if verbose > 1:
            log_level = logging.DEBUG
        elif verbose > 0:
            log_level = logging.INFO
        else:
            log_level = logging.WARNING

        # Set up console handler for build logger
        build_logger = logging.getLogger("build")
        console_handler = RichHandler(
            console=console,
            show_time=verbose > 1,
            show_path=False,
            level=log_level,
        )
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        build_logger.addHandler(console_handler)

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
            disable=verbose > 0  # Disable progress bar in verbose mode
        ) as progress:
            # Show build progress
            task = progress.add_task(
                f"Building {package.name} {package.version}...",
                total=None
            )
            
            result = builder.build(package, trait_dict, verbose > 0)
            
            if result.success:
                progress.update(task, completed=True)
                if verbose == 0:  # Only show success message in non-verbose mode
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
    finally:
        # Clean up the console handler
        if 'build_logger' in locals():
            build_logger.removeHandler(console_handler) 