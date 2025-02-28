"""
Authentication command for Clydepm.
"""
from typing import Optional
import sys

import typer
from rich import print as rprint
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..utils.github import update_github_config
from ...github.config import validate_token, load_config

# Create console for rich output
console = Console()


def auth(
    token: Optional[str] = typer.Option(
        None,
        "--token",
        help="GitHub Personal Access Token",
    ),
    organization: Optional[str] = typer.Option(
        None,
        "--org", "--organization",
        help="GitHub organization to use for packages",
    ),
    validate: bool = typer.Option(
        True,
        "--validate/--no-validate",
        help="Validate the token with GitHub API",
    ),
) -> None:
    """Set up GitHub authentication for package management."""
    try:
        # Load existing config
        config = load_config()
        
        # Update token if provided
        if token:
            config["token"] = token
        elif "token" not in config:
            # Prompt for token if not provided and not in config
            token = typer.prompt("GitHub Personal Access Token", hide_input=True)
            config["token"] = token
            
        # Validate token if requested
        if validate and config.get("token"):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Validating GitHub token...", total=None)
                
                if validate_token(config["token"]):
                    progress.update(task, completed=True)
                    rprint("[green]✓[/green] GitHub token is valid")
                else:
                    progress.update(task, completed=True)
                    rprint("[red]Error:[/red] Invalid GitHub token")
                    sys.exit(1)
        
        # Update configuration
        update_github_config(token=config.get("token"), organization=organization)
        
        rprint("[green]✓[/green] GitHub authentication configured successfully!")
        if organization or "organization" in config:
            org = organization or config.get("organization")
            rprint(f"Using organization: {org}")
            
    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1) 