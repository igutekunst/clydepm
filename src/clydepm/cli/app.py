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
from .commands.publish import publish
from .commands.install import install
from .commands.cache import app as cache_app
from .commands.inspect import app as inspect_app

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
app = typer.Typer(
    help="Clyde Package Manager - Modern C/C++ dependency management",
    no_args_is_help=True
)

# Add commands
app.command()(init)
app.command()(build)
app.command()(run)
app.command()(auth)
app.command()(publish)
app.command()(install)

# Add subcommands
app.add_typer(cache_app, name="cache")
app.add_typer(inspect_app, name="inspect", help="Build inspection tools")


def main():
    """Main entry point for CLI."""
    app()

if __name__ == "__main__":
    main()