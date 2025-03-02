"""
Main CLI application for Clydepm.
"""
import os
import logging

import typer

from .commands.init import init
from .commands.build import build
from .commands.run import run
from .commands.auth import auth

# Set up logging
logger = logging.getLogger("clydepm")
logger.setLevel(logging.DEBUG if os.getenv("CLYDE_DEBUG") else logging.INFO)

# Create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG if os.getenv("CLYDE_DEBUG") else logging.INFO)

# Create formatter
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

# Add handler to logger
logger.addHandler(ch)

# Create typer app
app = typer.Typer()

# Add commands
app.command()(init)
app.command()(build)
app.command()(run)
app.command()(auth)

def main():
    """Main entry point for CLI."""
    app()

if __name__ == "__main__":
    main()