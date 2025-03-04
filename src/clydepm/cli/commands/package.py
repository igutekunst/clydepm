"""
Package management commands.
"""
from pathlib import Path
from typing import List, Optional, Dict, Set
import typer
from rich.console import Console
from rich.table import Table
import json
import logging
from rich.progress import Progress

from ...core.install import GlobalInstaller
from ...core.package import Package
from ...github.registry import GitHubRegistry
from ...github.config import GitHubConfigError, get_github_token
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

def parse_package_spec(spec: str) -> tuple[str, Optional[str], Optional[str]]:
    """Parse a package specification.
    
    Formats supported:
    - package
    - package@version
    - @username/package
    - @username/package@version
    
    Args:
        spec: Package specification
        
    Returns:
        Tuple of (package_name, version, username)
    """
    username = None
    version = None
    
    # Check if it's a scoped package (@username/package)
    if spec.startswith("@"):
        try:
            username, rest = spec[1:].split("/", 1)
            if not username or not rest:
                raise ValueError(f"Invalid package specification: {spec}. Username and package name cannot be empty")
        except ValueError as e:
            if "cannot be empty" in str(e):
                raise e
            raise ValueError(f"Invalid package specification: {spec}. Expected format: @username/package[@version]")
        spec = rest
    
    # Check for version
    if "@" in spec:
        package_name, version = spec.split("@", 1)
        if not package_name:
            raise ValueError("Package name cannot be empty")
    else:
        package_name = spec
        if not package_name:
            raise ValueError("Package name cannot be empty")
        
    return package_name, version, username

def check_existing_files(installer: GlobalInstaller, package: Package) -> Set[Path]:
    """Check which files would be overwritten by installing a package.
    
    Args:
        installer: Global installer instance
        package: Package to check
        
    Returns:
        Set of paths that would be overwritten
    """
    existing = set()
    package_dir = installer.get_package_dir(package.name)
    
    # Check package directory
    if package_dir.exists():
        existing.add(package_dir)
        
    # Check binary
    if package.package_type == "application":
        bin_path = installer.bin_dir / package.name
        if bin_path.exists() or bin_path.is_symlink():
            existing.add(bin_path)
            
    # Check library and headers
    if package.package_type in ["library", "application"]:
        # Library
        lib_name = f"lib{package.name}.a"
        lib_path = installer.lib_dir / lib_name
        if lib_path.exists() or lib_path.is_symlink():
            existing.add(lib_path)
            
        # Headers
        include_path = installer.include_dir / package.name
        if include_path.exists() or include_path.is_symlink():
            existing.add(include_path)
            
    return existing

@package_cmd.command()
def install(
    packages: Optional[List[str]] = typer.Argument(
        None,
        help="Packages to install (e.g. fmt@8.1.1, @username/package). If -g is used in a package directory and no packages are specified, installs the current package."
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
    
    # Configure root logger to only show errors by default
    logging.basicConfig(
        level=logging.ERROR,
        format='%(message)s'  # Simplified format for user-facing messages
    )
    
    # Configure our loggers specifically
    for logger_name in ['clydepm.cli', 'clydepm.github', 'clydepm.core', 'clydepm.build']:
        module_logger = logging.getLogger(logger_name)
        module_logger.setLevel(log_level)
        # Remove any existing handlers
        module_logger.handlers = []
        # Add a new handler that respects our format
        handler = logging.StreamHandler()
        if verbose:
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        else:
            formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        module_logger.addHandler(handler)
    
    # Create builder instance
    builder = Builder()
    
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
        
    if not packages and not in_package_dir:
        console.print("[red]Error:[/red] No packages specified")
        raise typer.Exit(1)
        
    try:
        # Get GitHub token and set up registry for remote packages
        token = get_github_token()
        if not token:
            console.print("[red]Error:[/red] No GitHub token configured")
            console.print("Run 'clyde auth' to set up GitHub authentication")
            raise typer.Exit(1)
            
        # Create registries dict to cache registries by username/org
        registries = {}
        
        if global_install:
            # First check all packages for existing files
            all_existing = set()
            for pkg_spec in packages:
                if pkg_spec == ".":
                    package = current_package
                else:
                    try:
                        name, version, username = parse_package_spec(pkg_spec)
                        # Use specified username or fallback to organization from config
                        org = username or organization
                        if not org:
                            from ...github.config import load_config
                            config = load_config()
                            org = config.get("organization")
                            
                        # Get or create registry for this org
                        if org not in registries:
                            registries[org] = GitHubRegistry(token, org)
                        registry = registries[org]
                        
                        # Get package from registry
                        package = registry.get_package(name, version or "latest")
                    except ValueError as e:
                        console.print(f"[red]Error:[/red] {str(e)}")
                        raise typer.Exit(1)
                    
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
            
            # Use a single progress display for all operations
            with Progress(
                transient=True,  # Hide progress when done
                refresh_per_second=10,  # Lower refresh rate
                disable=verbose  # Disable progress in verbose mode
            ) as progress:
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
                            if not installer.install_binary(binary, package.name, package.name, overwrite=force):
                                raise typer.Exit(1)
                        progress.update(task, advance=1)
                        
                        if package.package_type in ["library", "application"]:
                            # Install library
                            lib_name = f"lib{package.name}.a"
                            library = build_dir / lib_name
                            logger.debug(f"Installing library: {library}")
                            if not installer.install_library(library, lib_name, package.name, overwrite=force):
                                raise typer.Exit(1)
                            progress.update(task, advance=1)
                            
                            # Install headers - directly into include/packagename/
                            include_dir = package.path / "include"
                            logger.debug(f"Installing headers from: {include_dir}")
                            if not installer.install_headers(include_dir, package.name, overwrite=force):
                                raise typer.Exit(1)
                            
                            # Write installation metadata
                            package_dir = installer.get_package_dir(package.name)
                            files = {
                                "binaries": [{"source": str(binary), "link": str(installer.bin_dir / package.name)}] if package.package_type == "application" else [],
                                "libraries": [{"source": str(library), "link": str(installer.lib_dir / lib_name)}],
                                "headers": [{"source": str(include_dir), "link": str(installer.include_dir / package.name)}]
                            }
                            
                            # Get basic build info
                            build_info = {
                                "compiler": "cc",  # Default to cc for now
                                "version": "",     # Empty for now
                                "flags": []        # Empty list for now
                            }
                            
                            # Write metadata
                            if not installer.write_install_metadata(
                                package_dir,
                                package.name,
                                package.version,
                                files,
                                build_info,
                                getattr(package, 'dependencies', {})  # Default to empty dict if not present
                            ):
                                logger.warning("Failed to write installation metadata")
                        progress.update(task, advance=1)
                        
                    else:
                        # Parse package spec
                        try:
                            name, version, username = parse_package_spec(pkg_spec)
                            # Use specified username or fallback to organization from config
                            org = username or organization
                            if not org:
                                from ...github.config import load_config
                                config = load_config()
                                org = config.get("organization")
                                
                            # Get or create registry for this org
                            if org not in registries:
                                registries[org] = GitHubRegistry(token, org)
                            registry = registries[org]
                            
                            task = progress.add_task(f"Downloading {name} {version or 'latest'}...", total=4)
                            logger.debug(f"Downloading package: {name}@{version or 'latest'} from {org}")
                            
                            # Get package from registry
                            package = registry.get_package(name, version or "latest")
                            progress.update(task, advance=1)
                            
                        except ValueError as e:
                            console.print(f"[red]Error:[/red] {str(e)}")
                            raise typer.Exit(1)
                        
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
                            if not installer.install_binary(binary, package.name, package.name, overwrite=force):
                                raise typer.Exit(1)
                        progress.update(task, advance=1)
                        
                        if package.package_type in ["library", "application"]:
                            # Install library
                            lib_name = f"lib{package.name}.a"
                            library = build_dir / lib_name
                            logger.debug(f"Installing library: {library}")
                            if not installer.install_library(library, lib_name, package.name, overwrite=force):
                                raise typer.Exit(1)
                            
                            # Install headers - directly into include/packagename/
                            include_dir = package.path / "include"
                            logger.debug(f"Installing headers from: {include_dir}")
                            if not installer.install_headers(include_dir, package.name, overwrite=force):
                                raise typer.Exit(1)
                            
                            # Write installation metadata
                            package_dir = installer.get_package_dir(package.name)
                            files = {
                                "binaries": [{"source": str(binary), "link": str(installer.bin_dir / package.name)}] if package.package_type == "application" else [],
                                "libraries": [{"source": str(library), "link": str(installer.lib_dir / lib_name)}],
                                "headers": [{"source": str(include_dir), "link": str(installer.include_dir / package.name)}]
                            }
                            
                            # Get basic build info
                            build_info = {
                                "compiler": "cc",  # Default to cc for now
                                "version": "",     # Empty for now
                                "flags": []        # Empty list for now
                            }
                            
                            # Write metadata
                            if not installer.write_install_metadata(
                                package_dir,
                                package.name,
                                package.version,
                                files,
                                build_info,
                                getattr(package, 'dependencies', {})  # Default to empty dict if not present
                            ):
                                logger.warning("Failed to write installation metadata")
                        progress.update(task, advance=1)
                    
            console.print("[green]Global installation complete![/green]")
            
        else:
            # Handle local installation
            if not in_package_dir:
                console.print("[red]Error:[/red] No package.yml found in current directory")
                console.print("To install packages globally, use the -g flag")
                console.print("To install as a dependency, run this command in a directory with a package.yml")
                raise typer.Exit(1)
                
            # TODO: Implement local installation
            console.print("[yellow]Note:[/yellow] Without -g, this will install the package as a dependency in the current package")
            console.print("[yellow]Local installation is not yet implemented[/yellow]")
            
    except GitHubConfigError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        logger.debug("Error details:", exc_info=True)
        raise typer.Exit(1) 