"""
Git utility functions for Clydepm.
"""
from pathlib import Path
import subprocess
from typing import Optional, Tuple, List


def get_remote_url(repo_name: str, owner: str, use_ssh: bool = True) -> str:
    """
    Get the remote URL for a GitHub repository based on the protocol preference.
    
    Args:
        repo_name: The name of the repository
        owner: The owner (user or organization) of the repository
        use_ssh: Whether to use SSH URL instead of HTTPS URL
        
    Returns:
        The remote URL for the repository
    """
    if use_ssh:
        # SSH format: git@github.com:owner/repo.git
        return f"git@github.com:{owner}/{repo_name}.git"
    else:
        # HTTPS format: https://github.com/owner/repo.git
        return f"https://github.com/{owner}/{repo_name}.git"


def check_remote_exists(path: Path, remote_name: str = "origin") -> bool:
    """
    Check if a Git remote exists.
    
    Args:
        path: Path to the Git repository
        remote_name: Name of the remote to check
        
    Returns:
        True if the remote exists, False otherwise
    """
    try:
        subprocess.run(
            ["git", "remote", "get-url", remote_name],
            cwd=str(path),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True
    except subprocess.CalledProcessError:
        return False


def test_remote_connection(path: Path, remote_name: str = "origin") -> Tuple[bool, Optional[str]]:
    """
    Test the connection to a Git remote.
    
    Args:
        path: Path to the Git repository
        remote_name: Name of the remote to test
        
    Returns:
        A tuple of (success, error_message)
    """
    try:
        subprocess.run(
            ["git", "ls-remote", "--exit-code", remote_name, "HEAD"],
            cwd=str(path),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True, None
    except subprocess.CalledProcessError as e:
        return False, e.stderr.decode() if e.stderr else "Failed to connect to remote"


def push_to_remote(
    path: Path, 
    remote_name: str = "origin", 
    branch: Optional[str] = None,
    tag: Optional[str] = None,
    verbose: bool = False,
    debug: bool = False
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Push to a Git remote.
    
    Args:
        path: Path to the Git repository
        remote_name: Name of the remote to push to
        branch: Branch to push (if None, pushes the current branch)
        tag: Tag to push (if specified, pushes the tag instead of a branch)
        verbose: Whether to show verbose output
        debug: Whether to show debug information
        
    Returns:
        A tuple of (success, stdout, stderr)
    """
    cmd: List[str] = ["git", "push"]
    
    if tag:
        cmd.extend([remote_name, tag])
    elif branch:
        cmd.extend([remote_name, branch])
    else:
        cmd.append(remote_name)
        
    if debug:
        print(f"Running command: {' '.join(cmd)}")
        
    try:
        result = subprocess.run(
            cmd,
            cwd=str(path),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        
        if verbose and stdout:
            print(stdout)
            
        return True, stdout, stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr 