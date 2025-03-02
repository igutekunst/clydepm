"""
Command line interface for Clydepm.
"""
import typer
import logging

from .commands import init, build, run, cache

app = typer.Typer()

# Register commands
app.command()(init)
app.command()(build)
app.command()(run)
app.add_typer(cache)

def main():
    """Entry point for the CLI."""
    app() 