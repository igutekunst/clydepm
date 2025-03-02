"""
Init command for Clydepm.
"""
from pathlib import Path
from typing import Optional
import sys
import git

import typer
from rich import print as rprint
from rich.console import Console

from ...core.package import Package, PackageType
from ..models.language import Language
from ..utils.templates import list_templates, copy_template
import logging

# Create console for rich output
console = Console()

logger = logging.getLogger(__name__)


def init(
    path: Path = typer.Argument(
        ".",
        help="Path to create package in",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    name: str = typer.Option(
        None,
        "--name", "-n",
        help="Package name (defaults to directory name)",
    ),
    package_type: PackageType = typer.Option(
        PackageType.LIBRARY,
        "--type", "-t",
        help="Package type",
    ),
    language: Language = typer.Option(
        None,
        "--lang", "-l",
        help="Programming language (c, cpp/cxx/c++)",
    ),
    template: str = typer.Option(
        None,
        "--template",
        help="Template to use (c-app, cpp-app, c-lib, or cpp-lib)",
    ),
    version: str = typer.Option(
        "0.1.0",
        "--version", "-v",
        help="Initial version",
    ),
    use_ssh: bool = typer.Option(
        True,
        "--ssh/--https",
        help="Use SSH URLs instead of HTTPS URLs for Git remotes",
    ),
    setup_remote: bool = typer.Option(
        False,
        "--setup-remote/--no-setup-remote",
        help="Set up GitHub remote repository",
    ),
    organization: Optional[str] = typer.Option(
        None,
        "--org", "--organization",
        help="GitHub organization to use (overrides config)",
    ),
    private: bool = typer.Option(
        False,
        "--private/--public",
        help="Create private GitHub repository",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description", "-d",
        help="Description for GitHub repository",
    ),
) -> None:
    """Initialize a new package."""
    try:
        path = Path(path)
        
        # Use directory name if no name provided
        name = name or path.name
        
        # Determine language if not specified
        if language is None:
            # Default to C++ for libraries, C for applications
            language = Language.C if package_type == PackageType.APPLICATION else Language.CPP
            logger.debug(f"Using default language {language} for {package_type}")
        
        # Determine template
        templates = list_templates()
        if template is None:
            # Use language-specific template for both applications and libraries
            if package_type == PackageType.APPLICATION:
                template = "cpp-app" if language in [Language.CPP, Language.CXX, Language.CPLUSPLUS] else "c-app"
            else:
                template = "cpp-lib" if language in [Language.CPP, Language.CXX, Language.CPLUSPLUS] else "c-lib"
            logger.debug(f"Using template {template} for {package_type} with language {language}")

        if template not in templates:
            available = ", ".join(templates.keys())
            rprint(f"[red]Error:[/red] Unknown template: {template}")
            rprint(f"Available templates: {available}")
            sys.exit(1)
            
        # Copy template with replacements
        replacements = {
            "name": name,
            "version": version,
            "name_upper": name.upper(),  # Add this for header guards
        }
        copy_template(templates[template], path, replacements)
        
        # Initialize Git repository
        try:
            repo = git.Repo.init(path)
            
            # Create .gitignore if it doesn't exist
            gitignore_path = path / ".gitignore"
            if not gitignore_path.exists():
                with open(gitignore_path, "w") as f:
                    f.write("# Build artifacts\n")
                    f.write("build/\n")
                    f.write("*.o\n")
                    f.write("*.a\n")
                    f.write("*.so\n")
                    f.write("*.dylib\n")
                    f.write("*.dll\n")
                    f.write("*.exe\n")
                    f.write("\n# IDE files\n")
                    f.write(".vscode/\n")
                    f.write(".idea/\n")
                    f.write("*.swp\n")
                    f.write("*.swo\n")
                    
            # Add all files to Git
            repo.git.add(".")
            
            # Make initial commit
            repo.git.commit("-m", "Initial commit")
            
            # Set up GitHub remote if requested
            if setup_remote:
                from github import Github
                from github.GithubException import GithubException
                from ..utils.github import get_github_token, get_github_organization
                from ..utils.git import get_remote_url
                
                # Get GitHub token
                token = get_github_token()
                if not token:
                    rprint("[red]Error:[/red] No GitHub token configured")
                    rprint("Run 'clyde auth' to set up GitHub authentication")
                    sys.exit(1)
                
                # Get organization if not specified
                if not organization:
                    organization = get_github_organization()
                
                # Create GitHub client
                g = Github(token)
                
                try:
                    # Determine the owner (user or organization)
                    if organization:
                        owner = g.get_organization(organization)
                    else:
                        owner = g.get_user()
                    
                    # Create repository
                    repo_description = description or f"{language} {package_type.value} package"
                    github_repo = owner.create_repo(
                        name,
                        description=repo_description,
                        private=private,
                        auto_init=False
                    )
                    
                    # Add remote
                    remote_url = get_remote_url(name, owner.login, use_ssh)
                    repo.create_remote("origin", remote_url)
                    
                    rprint(f"[green]✓[/green] Created GitHub repository: {github_repo.html_url}")
                    
                except GithubException as e:
                    rprint(f"[red]Error creating GitHub repository:[/red] {e}")
                    sys.exit(1)
            
            rprint(f"[green]✓[/green] Initialized Git repository")
            
        except Exception as e:
            rprint(f"[yellow]Warning:[/yellow] Failed to initialize Git repository: {e}")
        
        # Create package to validate
        package = Package(path)
        
        rprint(f"[green]✓[/green] Created {str(language)} {package_type.value} package in {path}")
        rprint("\nTo build and run:")
        rprint(f"  cd {path}")
        rprint("  clyde build")
        if package_type == PackageType.APPLICATION:
            rprint("  clyde run")
        
    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        sys.exit(1) 