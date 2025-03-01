"""
Search command for Clydepm.
"""
from typing import Optional
import sys

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from github import Github
from github.GithubException import GithubException

from ..utils.github import get_github_token
from ...github.config import load_config, GitHubConfigError

# Create console for rich output
console = Console()


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
) -> None:
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