"""
Helper Functions for YACL

This module provides helper functions for JSON handling, installation info management, and
other utility functions.
"""

import json
import logging
import sys
import os
from typing import Dict, Any, Optional
from pathlib import Path


def get_resource_base_path() -> Path:
    """
    Returns the base path for resource files.
    Handles both development and Nuitka-compiled environments.
    """
    if "__compiled__" in globals():  # Nuitka compiled binary
        base_path = os.path.join(os.path.dirname(sys.executable), "resources")
    else:
        base_path = os.path.join(os.path.dirname(__file__), "..", "resources")
    
    return Path(os.path.abspath(base_path))

def load_json_file(file_path: str | Path) -> Optional[Dict[str, Any]]:
    """
    Load a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        dict: JSON data or None if failed to load
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.getLogger("YACL").error(f"Failed to load JSON file {file_path}: {e}")
        return None


def save_json_file(file_path: str | Path, data: Dict[str, Any]) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        file_path: Path to save the JSON file
        data: Data to save
        
    Returns:
        bool: True if saved successfully
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        logging.getLogger("YACL").error(f"Failed to save JSON file {file_path}: {e}")
        return False

def get_next_install_directory(base_dir: str, game: str) -> str:
    """
    Find a suitable directory name for a new game installation.
    
    The names follow the pattern "game0, game1, ..." to support multi-install system.
    
    Args:
        base_dir: Base directory for installations
        game: Game identifier (e.g., 'dda', 'bn')
        
    Returns:
        str: Path to the next available installation directory
    """
    try:
        base_path = Path(base_dir)
        game_base_dir = base_path / game
        
        # Create game directory if it doesn't exist
        game_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Find the next available directory number
        dir_number = 0
        while True:
            install_dir = game_base_dir / f"game{dir_number}"
            if not install_dir.exists():
                return str(install_dir)
            dir_number += 1
            
            # Safety check to prevent infinite loop
            if dir_number > 1000:
                raise RuntimeError("Too many installations, cannot find available directory")
                
    except Exception as e:
        logging.getLogger("YACL").error(f"Failed to get next install directory: {e}")
        # Fallback to a simple path
        return str(Path(base_dir) / game / "game0")
