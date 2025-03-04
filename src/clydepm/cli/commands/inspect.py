"""
Inspect command for Clydepm.
"""
from pathlib import Path
from typing import Literal, Optional
import sys
import subprocess
import os
import signal
import atexit
from enum import Enum
import time

import typer
from rich import print as rprint
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...core.package import Package
from ...core.dependency.resolver import DependencyResolver

# Create console for rich output
console = Console()


class OutputFormat(str, Enum):
    """Output format for analysis results."""
    CONSOLE = "console"
    JSON = "json"
    HTML = "html"
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"


def analyze(
    build_dir: Path = typer.Argument(
        ...,
        help="Build directory to analyze",
        exists=True,
        dir_okay=True,
        file_okay=False
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.CONSOLE,
        help="Output format"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output"
    )
) -> None:
    """Analyze a build directory and generate a report."""
    # TODO: Implement build analysis
    typer.echo("Build analysis not implemented yet")


def serve(
    port: int = typer.Option(8001, help="Port to serve on"),
    host: str = typer.Option("localhost", help="Host to bind to"),
    dev: bool = typer.Option(False, help="Run in development mode")
) -> None:
    """Start the web interface."""
    import uvicorn
    from ...inspect.web.server import app as web_app
    
    # Get the frontend directory
    frontend_dir = Path(__file__).parent.parent.parent / "inspect" / "web" / "frontend"
    
    if dev:
        # In development mode, run both frontend and backend servers
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Starting development servers...", total=None)
            
            try:
                # Start the Vite development server
                vite_process = subprocess.Popen(
                    ["npm", "run", "start:dev"],
                    cwd=frontend_dir,
                    env={**os.environ, "PORT": str(port), "HOST": host}
                )
                
                # Start the FastAPI server
                uvicorn_process = subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "clydepm.inspect.web.server:app", "--reload", f"--port={port}", f"--host={host}"],
                    env={**os.environ, "PYTHONPATH": str(Path(__file__).parent.parent.parent.parent.parent)}
                )
                
                # Register cleanup function
                def cleanup():
                    for process in [vite_process, uvicorn_process]:
                        if process and process.poll() is None:
                            process.terminate()
                            process.wait()
                
                atexit.register(cleanup)
                
                # Wait for either process to complete
                while True:
                    if vite_process.poll() is not None or uvicorn_process.poll() is not None:
                        break
                    try:
                        time.sleep(1)
                    except KeyboardInterrupt:
                        break
                
                cleanup()
                
            except KeyboardInterrupt:
                rprint("\n[yellow]Shutting down development servers...[/yellow]")
                sys.exit(0)
            except Exception as e:
                rprint(f"[red]Error starting development servers:[/red] {str(e)}")
                sys.exit(1)
    else:
        # In production mode, build the frontend and serve it with FastAPI
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Build frontend
            task = progress.add_task("Building frontend...", total=None)
            try:
                subprocess.run(
                    ["npm", "run", "build"],
                    cwd=frontend_dir,
                    check=True,
                    capture_output=True
                )
                progress.update(task, completed=True)
            except subprocess.CalledProcessError as e:
                rprint(f"[red]Error building frontend:[/red] {e.stderr.decode()}")
                sys.exit(1)
            
            # Start the server
            progress.add_task(f"Starting server on http://{host}:{port}", total=None)
            try:
                uvicorn.run(
                    web_app,
                    host=host,
                    port=port,
                    log_level="info"
                )
            except Exception as e:
                rprint(f"[red]Error starting server:[/red] {str(e)}")
                sys.exit(1)


def graph(
    output: Optional[Path] = typer.Option(
        None,
        help="Output file path. If not provided, opens the graph in the default viewer."
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.PNG,
        help="Output format for the graph visualization"
    )
) -> None:
    """Visualize package dependencies."""
    try:
        # Load current package
        try:
            package = Package(Path.cwd())
        except FileNotFoundError:
            console.print("[red]Error:[/red] No package.yml found in current directory")
            raise typer.Exit(1)
            
        # Create dependency resolver
        resolver = DependencyResolver()
        
        # Add package and its dependencies
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Resolving dependencies...", total=None)
            resolver.add_package(package)
            progress.update(task, completed=True)
            
            # Check for cycles
            cycles = resolver.detect_cycles()
            if cycles:
                cycle_str = " -> ".join(cycles[0])
                console.print(f"[yellow]Warning:[/yellow] Circular dependency detected: {cycle_str}")
            
            # Generate visualization
            task = progress.add_task("Generating graph...", total=None)
            try:
                if output:
                    # Save to file
                    resolver.visualize_graph(output_path=output, format=format.value)
                    progress.update(task, completed=True)
                    console.print(f"[green]✓[/green] Graph saved to {output}")
                else:
                    # Open in viewer
                    resolver.view_graph()
                    progress.update(task, completed=True)
                    console.print("[green]✓[/green] Opening graph in default viewer...")
            except RuntimeError as e:
                console.print(f"[red]Error:[/red] {str(e)}")
                console.print("Please install Graphviz to generate dependency graphs:")
                console.print("  macOS: brew install graphviz")
                console.print("  Linux: sudo apt-get install graphviz")
                console.print("  Windows: choco install graphviz")
                raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


# Create Typer app for inspect commands
app = typer.Typer(help="Build inspection tools")

# Register commands directly on the inspect app
app.command()(analyze)
app.command()(serve)
app.command()(graph) 