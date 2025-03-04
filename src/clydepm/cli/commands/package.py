"""
Package management commands.
"""
from pathlib import Path
from typing import List, Optional, Dict
import typer
from rich.console import Console
from rich.table import Table
import json
import logging

from ...core.install import GlobalInstaller
from ...core.package import Package
from ...github.registry import GitHubRegistry
from ...github.config import GitHubConfigError
from ..utils.github import get_github_token
from ...build.builder import Builder

console = Console()
logger = logging.getLogger(__name__)

# Create package command group
package_cmd = typer.Typer(help="Package management commands")

def format_dependencies(deps: Dict[str, str]) -> str:
    """Format dependencies for display.
    
    Args:
        deps: Dictionary of dependencies
        
    Returns:
        Formatted string of dependencies
    """
    if not deps:
        return "None"
    return ", ".join(f"{name}@{version}" for name, version in deps.items())

@package_cmd.command()
def list(
    prefix: Optional[str] = typer.Option(
        None,
        help="Custom installation prefix"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Show detailed package information"
    )
) -> None:
    """List installed packages."""
    installer = GlobalInstaller(Path(prefix) if prefix else None)
    
    # Create table for output
    table = Table(title="Installed Packages")
    table.add_column("Name")
    table.add_column("Version")
    if verbose:
        table.add_column("Type")
        table.add_column("Dependencies")
        table.add_column("Installed At")
    
    # Scan packages directory
    for package_dir in installer.packages_dir.iterdir():
        if not package_dir.is_dir():
            continue
            
        # Try to read metadata
        try:
            with open(package_dir / "install.json") as f:
                metadata = json.load(f)
                
            if verbose:
                # Determine package type from files
                pkg_type = []
                if metadata["files"].get("binaries"):
                    pkg_type.append("application")
                if metadata["files"].get("libraries"):
                    pkg_type.append("library")
                pkg_type = ", ".join(pkg_type) if pkg_type else "unknown"
                
                table.add_row(
                    metadata["name"],
                    metadata["version"],
                    pkg_type,
                    format_dependencies(metadata["dependencies"]),
                    metadata["installed_at"]
                )
            else:
                table.add_row(
                    metadata["name"],
                    metadata["version"]
                )
        except Exception as e:
            logger.warning(f"Failed to read metadata for {package_dir.name}: {e}")
            if verbose:
                table.add_row(
                    package_dir.name,
                    "unknown",
                    "unknown",
                    "unknown",
                    "unknown"
                )
            else:
                table.add_row(
                    package_dir.name,
                    "unknown"
                )
    
    console.print(table)

@package_cmd.command()
def uninstall(
    packages: Optional[List[str]] = typer.Argument(
        None,
        help="Packages to uninstall. If not specified in a package directory, uninstalls the current package."
    ),
    prefix: Optional[str] = typer.Option(
        None,
        help="Custom installation prefix"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Force uninstall without confirmation"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose output"
    )
) -> None:
    """Uninstall packages."""
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level)
    logger.setLevel(log_level)
    
    installer = GlobalInstaller(Path(prefix) if prefix else None)
    
    # Handle uninstalling current package
    if not packages:
        try:
            current_package = Package(Path.cwd())
            packages = [current_package.name]
            logger.debug(f"Using current package: {current_package.name}")
        except FileNotFoundError:
            console.print("[red]Error:[/red] No packages specified and no package.yml found in current directory")
            raise typer.Exit(1)
    elif "." in packages:
        try:
            current_package = Package(Path.cwd())
            # Replace . with package name
            packages = [current_package.name if p == "." else p for p in packages]
            logger.debug(f"Using current package: {current_package.name}")
        except FileNotFoundError:
            # If . was specified but no package exists, remove it from the list
            packages = [p for p in packages if p != "."]
            if not packages:
                console.print("[red]Error:[/red] No valid packages to uninstall")
                raise typer.Exit(1)
    
    for package_name in packages:
        package_dir = installer.get_package_dir(package_name)
        
        # Check if package exists
        if not package_dir.exists():
            console.print(f"[yellow]Warning:[/yellow] Package {package_name} is not installed")
            continue
            
        try:
            # Read metadata to get file information
            with open(package_dir / "install.json") as f:
                metadata = json.load(f)
                
            # List files that will be removed
            console.print(f"\nFiles to be removed for {package_name}:")
            
            # Package directory
            console.print(f"\nPackage directory:")
            console.print(f"  {package_dir}")
            
            # Symlinks
            files = metadata["files"]
            console.print("\nSymlinks:")
            for file_type in ["binaries", "libraries", "headers"]:
                for file_info in files.get(file_type, []):
                    link = Path(file_info["link"])
                    if link.exists() or link.is_symlink():
                        console.print(f"  {link}")
                        
            # Confirm uninstall
            if not force:
                if not typer.confirm("\nDo you want to uninstall these files?"):
                    continue
                    
            # Remove symlinks first
            for file_type in ["binaries", "libraries", "headers"]:
                for file_info in files.get(file_type, []):
                    link = Path(file_info["link"])
                    if link.exists() or link.is_symlink():
                        logger.debug(f"Removing symlink: {link}")
                        link.unlink()
                        
            # Remove package directory
            logger.debug(f"Removing package directory: {package_dir}")
            import shutil
            shutil.rmtree(package_dir)
            
            console.print(f"[green]Successfully uninstalled {package_name}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to uninstall {package_name}: {e}")
            logger.debug("Error details:", exc_info=True)

@package_cmd.command()
def search(
    query: str = typer.Argument(
        ...,
        help="Search query"
    ),
    organization: Optional[str] = typer.Option(
        None,
        "--org", "--organization",
        help="GitHub organization to search in"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Show detailed package information"
    )
) -> None:
    """Search for packages in the registry."""
    try:
        # Get GitHub token
        token = get_github_token()
        if not token:
            console.print("[red]Error:[/red] No GitHub token configured")
            console.print("Run 'clyde auth' to set up GitHub authentication")
            raise typer.Exit(1)
            
        # Load config for organization if not specified
        if not organization:
            from ...github.config import load_config
            config = load_config()
            organization = config.get("organization")
            
        # Create registry
        registry = GitHubRegistry(token, organization)
        
        # Search packages
        results = registry.search(query)
        
        if not results:
            console.print("No packages found")
            return
            
        # Display results
        table = Table(title="Search Results")
        table.add_column("Name")
        table.add_column("Latest Version")
        if verbose:
            table.add_column("Description")
            table.add_column("Type")
            
        for result in results:
            if verbose:
                table.add_row(
                    result["name"],
                    result["latest_version"],
                    result.get("description", ""),
                    result.get("type", "unknown")
                )
            else:
                table.add_row(
                    result["name"],
                    result["latest_version"]
                )
                
        console.print(table)
        
    except GitHubConfigError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        logger.debug("Error details:", exc_info=True)
        raise typer.Exit(1)

# Import and add install command
from .install import install
package_cmd.command()(install) 