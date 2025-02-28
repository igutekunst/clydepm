"""
GitHub configuration utilities for clydepm.
"""
from pathlib import Path
import json
import os
from typing import Dict, Optional, Tuple

from github import Github
from github.GithubException import BadCredentialsException


class GitHubConfigError(Exception):
    """Exception raised for GitHub configuration errors."""
    pass


def get_config_path() -> Path:
    """Get the path to the GitHub configuration file."""
    config_dir = Path.home() / ".clydepm"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "github_config.json"


def load_config() -> Dict:
    """
    Load GitHub configuration from file.
    
    Returns:
        Dictionary containing GitHub configuration
    
    If the configuration file doesn't exist, returns an empty dictionary.
    """
    config_path = get_config_path()
    if not config_path.exists():
        return {}
        
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If the file is corrupted, return empty config
        return {}


def save_config(config: Dict) -> None:
    """
    Save GitHub configuration to file.
    
    Args:
        config: Dictionary containing GitHub configuration
    """
    config_path = get_config_path()
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Set secure permissions on the file (readable only by the user)
    os.chmod(config_path, 0o600)


def validate_token(token: str) -> bool:
    """
    Validate GitHub token by making a test API call.
    
    Args:
        token: GitHub token to validate
        
    Returns:
        True if token is valid, False otherwise
    """
    try:
        g = Github(token)
        # Try to get the authenticated user to validate token
        g.get_user().login
        return True
    except BadCredentialsException:
        return False


def get_authenticated_client() -> Tuple[Github, Optional[str]]:
    """
    Get authenticated GitHub client using stored credentials.
    
    Returns:
        Tuple of (Github client, organization name or None)
        
    Raises:
        GitHubConfigError: If no valid GitHub token is configured
    """
    config = load_config()
    
    token = config.get('token')
    if not token:
        raise GitHubConfigError(
            "No GitHub token configured. Run 'clyde auth' to set up GitHub authentication."
        )
    
    # Validate token
    if not validate_token(token):
        raise GitHubConfigError(
            "Invalid GitHub token. Run 'clyde auth' to update your GitHub authentication."
        )
    
    return Github(token), config.get('organization') 