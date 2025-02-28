"""
GitHub utility functions for Clydepm.
"""
import os
from typing import Optional, Dict, Any

from ...github.config import load_config, save_config, validate_token


def get_github_token() -> Optional[str]:
    """
    Get GitHub token from environment or config.
    
    Returns:
        The GitHub token or None if not found
    """
    # First check environment
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
        
    # Then check config
    config = load_config()
    return config.get("token")


def get_github_organization() -> Optional[str]:
    """
    Get GitHub organization from config.
    
    Returns:
        The GitHub organization or None if not found
    """
    config = load_config()
    return config.get("organization")


def update_github_config(token: Optional[str] = None, organization: Optional[str] = None) -> Dict[str, Any]:
    """
    Update GitHub configuration.
    
    Args:
        token: GitHub token to save
        organization: GitHub organization to save
        
    Returns:
        The updated configuration
    """
    config = load_config()
    
    if token is not None:
        config["token"] = token
        
    if organization is not None:
        config["organization"] = organization
        
    save_config(config)
    return config 