from clydepm.github.config import load_config, GitHubConfigError, get_github_token, get_authenticated_client
from clydepm.github.registry import GitHubRegistry
from clydepm.core.package import Package
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
from typing import Optional
import sys
from rich import print as rprint
import typer
from rich.console import Console
import logging

logger = logging.getLogger(__name__)
console = Console()

def publish(
    path: Path = typer.Argument(
        ".",
        help="Path to package",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    create_binary: bool = typer.Option(
        True,
        "--binary/--no-binary",
        help="Create and publish binary package",
    ),
    organization: Optional[str] = typer.Option(
        None,
        "--org", "--organization",
        help="GitHub organization to use (overrides config)",
    ),
) -> None:
    """Publish a package to GitHub."""
    try:
        logger.debug("Starting publish command with path=%s, create_binary=%s, organization=%s", 
                    path, create_binary, organization)

        # Get GitHub token from config or environment
        token = get_github_token()
        if not token:
            logger.error("No GitHub token configured")
            rprint("[red]Error:[/red] No GitHub token configured")
            rprint("Run 'clyde auth' to set up GitHub authentication")
            sys.exit(1)
            
        # Create package and registry
        logger.debug("Creating package from path %s", path)
        package = Package(path)
        
        # Get authenticated client and organization
        client, default_org = get_authenticated_client()
        
        # Use specified organization or default from authenticated user
        organization = organization or default_org
        logger.debug("Using organization: %s", organization)
        
        # Validate package name format
        if organization:
            expected_prefix = f"@{organization}/"
            if not package.name.startswith(expected_prefix):
                error_msg = (
                    f"[red]Error:[/red] Package name must include organization prefix\n"
                    f"Current name: {package.name}\n"
                    f"Expected format: {expected_prefix}<package-name>\n\n"
                    f"To fix this:\n"
                    f"1. Update the name in [bold]package.yml[/bold]:\n"
                    f"   name: {expected_prefix}{package.name}\n"
                )
                rprint(error_msg)
                sys.exit(1)
        elif "/" in package.name:
            # If no organization is configured but name has a scope
            org = package.name.split("/")[0][1:]  # Remove @ from org
            error_msg = (
                f"[red]Error:[/red] Package name includes organization '{org}' but no organization is configured\n\n"
                f"To fix this, either:\n"
                f"1. Configure the organization in [bold]~/.clydepm/config.yml[/bold]:\n"
                f"   organization: {org}\n"
                f"2. Or specify the organization when publishing:\n"
                f"   clyde publish --org {org}\n"
                f"3. Or remove the organization prefix from the package name in [bold]package.yml[/bold]:\n"
                f"   name: {package.name.split('/')[1]}\n"
            )
            rprint(error_msg)
            sys.exit(1)
            
        # Create registry with token and organization
        logger.debug("Creating GitHub registry with organization %s", organization)
        registry = GitHubRegistry(token, organization)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Publishing {package.name} {package.version}...",
                total=None
            )
            
            try:
                logger.debug("Publishing package %s version %s (create_binary=%s)", 
                            package.name, package.version, create_binary)
                registry.publish_package(package, create_binary)
                
                progress.update(task, completed=True)
                logger.info("Successfully published package %s version %s", package.name, package.version)
                rprint(f"[green]✓[/green] Published {package.name} {package.version}")
            except ValueError as e:
                progress.update(task, completed=True)
                # Print the error message without the traceback
                rprint(str(e))
                sys.exit(1)
            
    except GitHubConfigError as e:
        logger.error("GitHub config error: %s", str(e))
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected error during publish: %s", str(e), exc_info=True)
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)
