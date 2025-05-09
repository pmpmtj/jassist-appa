"""
Path Utilities

Centralized utilities for consistent path resolution across all modules.
"""

from pathlib import Path
from typing import Union

def resolve_path(path_input: Union[str, Path], base_dir: Path = None) -> Path:
    """
    Consistently resolve a path string or Path object to an absolute Path.
    
    Args:
        path_input: The path string or Path object to resolve
        base_dir: Optional base directory to resolve relative paths from
                  If None, relative paths will be resolved from current directory
        
    Returns:
        An absolute Path object
    """
    # Convert to Path object if it's a string
    path = Path(path_input) if isinstance(path_input, str) else path_input
    
    # If already absolute, return it directly
    if path.is_absolute():
        return path
    
    # If no base_dir provided, use current working directory
    if base_dir is None:
        return path.resolve()
        
    # If path contains parent directory references (..), handle specially
    if isinstance(path_input, str) and "../" in path_input:
        return (base_dir / path_input).resolve()
    
    # Otherwise, simply join with the base directory
    return (base_dir / path).resolve() 