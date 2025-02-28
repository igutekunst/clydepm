"""
Command-line interface for Clydepm.
"""
from pathlib import Path
from typing import Optional, List, Dict
import os
import sys
import subprocess
import shutil
from enum import Enum

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import print as rprint
from jinja2 import Environment, FileSystemLoader, Template
from github import Github
from github.GithubException import GithubException

from ..core.package import Package, PackageType
from ..build.builder import Builder, BuildError
from ..github.registry import GitHubRegistry
from ..github.config import load_config, save_config, validate_token, GitHubConfigError

# Import commands
from .commands import init, build, run, auth

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

# Keep the original commands for now, we'll migrate them one by one
@app.command()
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
        # Get GitHub token from config or environment
        token = get_github_token()
        if not token:
            rprint("[red]Error:[/red] No GitHub token configured")
            rprint("Run 'clyde auth' to set up GitHub authentication")
            sys.exit(1)
            
        # Create package and registry
        package = Package(path)
        
        # Load config for organization if not specified
        if not organization:
            config = load_config()
            organization = config.get("organization")
            
        # Create registry with token and organization
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
            
            registry.publish_package(package, create_binary)
            
            progress.update(task, completed=True)
            rprint(f"[green]✓[/green] Published {package.name} {package.version}")
            
    except GitHubConfigError as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)
    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)

@app.command()
def install(
    package_spec: str = typer.Argument(
        ...,
        help="Package to install (name==version)",
    ),
    path: Path = typer.Option(
        ".",
        "--path", "-p",
        help="Path to install to",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    organization: Optional[str] = typer.Option(
        None,
        "--org", "--organization",
        help="GitHub organization to use (overrides config)",
    ),
) -> None:
    """Install a package from GitHub."""
    try:
        # Parse package spec
        if "==" in package_spec:
            name, version = package_spec.split("==", 1)
        else:
            name = package_spec
            version = "latest"  # We'll need to implement version resolution
            
        # Get GitHub token from config or environment
        token = get_github_token()
        if not token:
            rprint("[red]Error:[/red] No GitHub token configured")
            rprint("Run 'clyde auth' to set up GitHub authentication")
            sys.exit(1)
            
        # Load config for organization if not specified
        if not organization:
            config = load_config()
            organization = config.get("organization")
            
        # Create registry with token and organization
        registry = GitHubRegistry(token, organization)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Installing {name} {version}...",
                total=None
            )
            
            # Get package
            package = registry.get_package(name, version)
            
            # TODO: Install package to path
            
            progress.update(task, completed=True)
            rprint(f"[green]✓[/green] Installed {package.name} {package.version}")
            
    except GitHubConfigError as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)
    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)

@app.command()
def search(
    query: str = typer.Argument(
        ...,
        help="Search query for packages",
    ),
    organization: Optional[str] = typer.Option(
        None,
        "--org", "--organization",
        help="GitHub organization to search in (overrides config)",
    ),
    limit: int = typer.Option(
        10,
        "--limit", "-n",
        help="Maximum number of results to show",
    ),
):
    """Search for packages on GitHub."""
    try:
        # Get GitHub token from config or environment
        token = get_github_token()
        if not token:
            rprint("[red]Error:[/red] No GitHub token configured")
            rprint("Run 'clyde auth' to set up GitHub authentication")
            sys.exit(1)
            
        # Load config for organization if not specified
        if not organization:
            config = load_config()
            organization = config.get("organization")
            
        # Create GitHub client
        g = Github(token)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Searching for packages matching '{query}'...",
                total=None
            )
            
            try:
                if organization:
                    # Search within organization
                    org = g.get_organization(organization)
                    repos = org.get_repos()
                    matching_repos = [repo for repo in repos if query.lower() in repo.name.lower()]
                    matching_repos = matching_repos[:limit]  # Limit results
                else:
                    # Global search
                    query_string = f"{query} in:name"
                    matching_repos = list(g.search_repositories(query_string)[:limit])
                    
                progress.update(task, completed=True)
                
                # Display results
                if not matching_repos:
                    rprint(f"No packages found matching '{query}'")
                    return
                    
                table = Table(title=f"Packages matching '{query}'")
                table.add_column("Name")
                table.add_column("Description")
                table.add_column("Stars")
                table.add_column("Latest Version")
                
                for repo in matching_repos:
                    # Try to find latest version
                    latest_version = "N/A"
                    try:
                        releases = repo.get_releases()
                        if releases.totalCount > 0:
                            latest_release = releases[0]
                            latest_version = latest_release.tag_name
                            if latest_version.startswith('v'):
                                latest_version = latest_version[1:]
                    except GithubException:
                        pass
                        
                    table.add_row(
                        repo.name,
                        repo.description or "No description",
                        str(repo.stargazers_count),
                        latest_version
                    )
                    
                console.print(table)
                
                # Show installation instructions
                rprint("\nTo install a package:")
                if organization:
                    rprint(f"  clyde install {organization}/PACKAGE_NAME==VERSION")
                else:
                    rprint("  clyde install OWNER/PACKAGE_NAME==VERSION")
                
            except GithubException as e:
                progress.update(task, completed=True)
                rprint(f"[red]Error searching GitHub:[/red] {e}")
                sys.exit(1)
                
    except GitHubConfigError as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)
    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)

# Keep the get_github_token function for now
def get_github_token() -> Optional[str]:
    """Get GitHub token from environment or config."""
    # First check environment
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
        
    # Then check config
    config = load_config()
    return config.get("token")

def main():
    """Entry point for the CLI."""
    app() 