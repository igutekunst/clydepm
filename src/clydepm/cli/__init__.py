"""
CLI entry points for Clydepm.
"""
from .app import main, app

# For backward compatibility
def main_v2():
    """Entry point for clyde2 command."""
    main() 