"""
Package installation command.
"""
from pathlib import Path
from typing import List, Optional, Set
import sys
import typer
from rich.console import Console
from rich.progress import Progress
import logging

from ...core.install import GlobalInstaller
from ...core.package import Package
from ...github.registry import GitHubRegistry
from ...github.config import GitHubConfigError
from ..utils.github import get_github_token
from ...build.builder import Builder

console = Console()
logger = logging.getLogger(__name__)

def check_existing_files(installer: GlobalInstaller, package: Package) -> Set[Path]:
    """Check which files would be overwritten during installation.
    
    Args:
        installer: The global installer
        package: Package to check
        
    Returns:
        Set of paths that would be overwritten
    """
    existing = set()
    
    # Check binary
    if package.package_type == "application":
        binary_path = installer.prefix / "bin" / package.name
        if binary_path.exists():
            existing.add(binary_path)
            
    # Check library and headers
    if package.package_type in ["library", "application"]:
        # Check library
        lib_path = installer.prefix / "lib" / f"lib{package.name}.a"
        if lib_path.exists():
            existing.add(lib_path)
            
        # Check headers directory
        header_dir = installer.prefix / "include" / package.name
        if header_dir.exists():
            existing.add(header_dir)
            
    return existing

def install(
    packages: List[str] = typer.Argument(
        None,
        help="Packages to install (e.g. fmt@8.1.1). If -g is used in a package directory and no packages are specified, installs the current package."
    ),
    global_install: bool = typer.Option(
        False,
        "--global", "-g",
        help="Install globally in prefix"
    ),
    prefix: Optional[str] = typer.Option(
        None,
        help="Custom installation prefix"
    ),
    dev: bool = typer.Option(
        False,
        help="Install as development dependency"
    ),
    exact: bool = typer.Option(
        False,
        help="Use exact version matching"
    ),
    organization: Optional[str] = typer.Option(
        None,
        "--org", "--organization",
        help="GitHub organization to use (overrides config)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose output"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Force overwrite existing files"
    )
) -> None:
    """Install packages either as project dependencies or globally."""
    
    # Configure logging based on verbosity
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level)
    logger.setLevel(log_level)
    
    # Setup global installer if needed
    if global_install:
        prefix_path = Path(prefix) if prefix else None
        installer = GlobalInstaller(prefix_path)
        installer.setup_directories()
        logger.debug(f"Using global installation prefix: {installer.prefix}")
    
    # Try to load current package if it exists
    try:
        current_package = Package(Path.cwd())
        in_package_dir = True
        logger.debug(f"Found package in current directory: {current_package.name}")
    except FileNotFoundError:
        current_package = None
        in_package_dir = False
        logger.debug("No package found in current directory")
    
    # Handle case where we're in a package directory with -g and no packages specified
    if global_install and not packages and in_package_dir:
        packages = ["."]  # Use . to indicate current directory
        logger.debug("No packages specified, will install current package")
        
    if not packages:
        console.print("[red]Error:[/red] No packages specified")
        raise typer.Exit(1)
        
    try:
        # Get GitHub token and set up registry for remote packages
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
            
        # Create registry with token and organization
        registry = GitHubRegistry(token, organization)
        logger.debug(f"Using GitHub organization: {organization}")
        
        # Create builder instance with default cache directory
        builder = Builder()
        
        if global_install:
            # First check all packages for existing files
            all_existing = set()
            for pkg_spec in packages:
                if pkg_spec == ".":
                    package = current_package
                else:
                    if "@" in pkg_spec:
                        name, version = pkg_spec.split("@", 1)
                    else:
                        name = pkg_spec
                        version = "latest"
                    package = registry.get_package(name, version)
                    
                existing = check_existing_files(installer, package)
                all_existing.update(existing)
                
            # If files exist and not forcing, prompt user
            if all_existing and not force:
                console.print("\nThe following files already exist:")
                for path in sorted(all_existing):
                    console.print(f"  {path}")
                    
                if not typer.confirm("\nDo you want to overwrite these files?"):
                    console.print("Installation cancelled.")
                    raise typer.Exit(1)
                    
                # Force is now True after user confirmation
                force = True
            
            with Progress() as progress:
                # Install each package
                for pkg_spec in packages:
                    if pkg_spec == ".":
                        # Installing current package
                        package = current_package
                        task = progress.add_task(f"Building {package.name}...", total=4)
                        logger.debug(f"Building current package for global installation")
                        
                        # Build the package
                        build_result = builder.build(package, verbose=verbose)
                        if not build_result.success:
                            console.print(f"[red]Error:[/red] {build_result.error}")
                            raise typer.Exit(1)
                        progress.update(task, advance=1)
                        
                        # Get paths to built artifacts from build result
                        output_path = build_result.artifacts["output"]
                        build_dir = output_path.parent
                        logger.debug(f"Build directory: {build_dir}")
                        
                        # Install based on package type
                        if package.package_type == "application":
                            binary = build_dir / package.name
                            logger.debug(f"Installing binary: {binary}")
                            if not installer.install_binary(binary, package.name, overwrite=force):
                                raise typer.Exit(1)
                        progress.update(task, advance=1)
                        
                        if package.package_type in ["library", "application"]:
                            # Install library
                            lib_name = f"lib{package.name}.a"
                            library = build_dir / lib_name
                            logger.debug(f"Installing library: {library}")
                            if not installer.install_library(library, lib_name, overwrite=force):
                                raise typer.Exit(1)
                            progress.update(task, advance=1)
                            
                            # Install headers - directly into include/packagename/
                            include_dir = package.path / "include"
                            logger.debug(f"Installing headers from: {include_dir}")
                            if not installer.install_headers(include_dir, "", overwrite=force):  # Pass empty string to avoid creating packagename subdir
                                raise typer.Exit(1)
                        progress.update(task, advance=1)
                        
                    else:
                        # Parse package spec for remote package
                        if "@" in pkg_spec:
                            name, version = pkg_spec.split("@", 1)
                        else:
                            name = pkg_spec
                            version = "latest"
                            
                        task = progress.add_task(f"Downloading {name} {version}...", total=4)
                        logger.debug(f"Downloading package: {name}@{version}")
                        
                        # Get package from registry
                        package = registry.get_package(name, version)
                        progress.update(task, advance=1)
                        
                        # Build package
                        build_result = builder.build(package, verbose=verbose)
                        if not build_result.success:
                            console.print(f"[red]Error:[/red] {build_result.error}")
                            raise typer.Exit(1)
                        progress.update(task, advance=1)
                        
                        # Get paths to built artifacts from build result
                        output_path = build_result.artifacts["output"]
                        build_dir = output_path.parent
                        
                        # Install components based on package type
                        if package.package_type == "application":
                            binary = build_dir / package.name
                            logger.debug(f"Installing binary: {binary}")
                            if not installer.install_binary(binary, package.name, overwrite=force):
                                raise typer.Exit(1)
                        progress.update(task, advance=1)
                        
                        if package.package_type in ["library", "application"]:
                            # Install library
                            lib_name = f"lib{package.name}.a"
                            library = build_dir / lib_name
                            logger.debug(f"Installing library: {library}")
                            if not installer.install_library(library, lib_name, overwrite=force):
                                raise typer.Exit(1)
                            
                            # Install headers - directly into include/packagename/
                            include_dir = package.path / "include"
                            logger.debug(f"Installing headers from: {include_dir}")
                            if not installer.install_headers(include_dir, "", overwrite=force):  # Pass empty string to avoid creating packagename subdir
                                raise typer.Exit(1)
                        progress.update(task, advance=1)
                    
            console.print("[green]Global installation complete![/green]")
            
        else:
            # Handle local installation
            if not in_package_dir:
                console.print("[red]Error:[/red] No package.yml found in current directory")
                raise typer.Exit(1)
                
            # TODO: Implement local installation
            console.print("[yellow]Local installation not yet implemented[/yellow]")
            
    except GitHubConfigError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        logger.debug("Error details:", exc_info=True)
        raise typer.Exit(1)
