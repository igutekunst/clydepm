"""
Template utility functions for Clydepm.
"""
from pathlib import Path
from typing import Dict
import os

from jinja2 import Environment, FileSystemLoader


def get_template_dir() -> Path:
    """Get the directory containing templates."""
    return Path(__file__).parent.parent.parent / "templates"


def list_templates() -> Dict[str, Path]:
    """List available templates."""
    template_dir = get_template_dir()
    return {
        "c-app": template_dir / "c-app",  # C application template
        "cpp-lib": template_dir / "cpp-lib",  # C++ library template
        "c-lib": template_dir / "c-lib",  # C library template
    }


def copy_template(src: Path, dst: Path, replacements: Dict[str, str]) -> None:
    """
    Copy template directory with variable replacement using Jinja2.
    
    Args:
        src: Source template directory
        dst: Destination directory
        replacements: Dictionary of template variables and their values
    """
    # Add uppercase versions of all replacements
    upper_replacements = {
        f"{k}_upper": v.upper()
        for k, v in replacements.items()
    }
    replacements.update(upper_replacements)
    
    # Create destination directory
    dst.mkdir(parents=True, exist_ok=True)
    
    # Create Jinja environment
    env = Environment(
        loader=FileSystemLoader(str(src)),
        keep_trailing_newline=True
    )
    
    for item in src.rglob("*"):
        # Skip __pycache__ and other hidden files
        if any(p.startswith('.') for p in item.parts):
            continue
            
        # Get relative path and replace template variables in path
        rel_path = item.relative_to(src)
        path_str = str(rel_path)
        
        # Replace {{var}} in path
        try:
            template = env.from_string(path_str)
            path_str = template.render(**replacements)
        except Exception as e:
            raise ValueError(f"Error processing path template: {path_str}: {e}")
            
        rel_path = Path(path_str)
        dst_path = dst / rel_path
        
        if item.is_dir():
            dst_path.mkdir(parents=True, exist_ok=True)
        else:
            # Replace template variables in content
            try:
                with open(item) as f:
                    template = env.from_string(f.read())
                content = template.render(**replacements)
            except Exception as e:
                raise ValueError(f"Error processing file template {item}: {e}")
            
            # Ensure parent directory exists
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            with open(dst_path, "w") as f:
                f.write(content) 