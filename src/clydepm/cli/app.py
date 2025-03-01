"""
Command-line interface for Clydepm.
"""
import typer
import logging
from rich.console import Console

# Import commands
from .commands import init, build, run, auth, search, publish, install

# Create Typer app
app = typer.Typer(
    name="clyde",
    help="Clyde C/C++ Package Manager",
    add_completion=False,  # We'll add this later
)

# Create console for rich output
console = Console()

# Register commands
app.command()(init)
app.command()(build)
app.command()(run)
app.command()(auth)
app.command()(search)
app.command()(publish)
app.command()(install)

def main(
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable debug logging",
    ),
):
    """Entry point for the CLI."""
    app()