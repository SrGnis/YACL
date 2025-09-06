"""
Path Management System for YACL

This module provides path management for organizing game installations, user data directories,
cache, and file organization.
"""

import logging
import os
import platform
from typing import Dict, Any, Optional
from pathlib import Path

class PathManager:
    """
    Path management system for YACL.
    
    This class handles:
    - Application directory structure
    - Game installation paths
    - User data directories
    - Cache and temporary directories
    - Cross-platform path resolution
    """
    
    def __init__(self):
        """Initialize the path manager."""
        self.logger = logging.getLogger("YACL")
        
        # Base directories
        self.app_dir: Path
        self.user_data_dir: Path
        self.cache_dir: Path
        self.config_dir: Path
        
        # Game-specific directories
        self.games_dir: Path
        self.mods_dir: Path
        self.soundpacks_dir: Path
        self.fonts_dir: Path
        self.backups_dir: Path
        
        # Utility directories
        self.db_dir: Path
        self.temp_dir: Path
        self.logs_dir: Path

        self._is_initialized = False
    
    def initialize(self, app_name: str = "YACL") -> bool:
        """
        Initialize the path manager and create directory structure.
        
        Args:
            app_name: Name of the application for directory naming
            
        Returns:
            bool: True if initialization was successful
        """
        try:
            self.logger.info("Initializing path manager...")
            
            self._setup_base_directories(app_name)
            
            self._create_directory_structure()
            
            self._is_initialized = True
            self.logger.info("Path manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize path manager: {e}")
            return False
    
    def _setup_base_directories(self, app_name: str):
        """Setup base directories based on the operating system."""
        # TODO: Implement platform-specific directory setup

        home = Path.home()
        self.app_dir = home / f"{app_name.lower()}"

        self.user_data_dir = self.app_dir / "data"
        self.cache_dir = self.app_dir / "cache"
        
        self.config_dir = self.app_dir / "config"
        
        # Set up game-specific directories
        self.games_dir = self.user_data_dir / "games"
        self.mods_dir = self.user_data_dir / "mods"
        self.soundpacks_dir = self.user_data_dir / "soundpacks"
        self.fonts_dir = self.user_data_dir / "fonts"
        self.backups_dir = self.user_data_dir / "backups"
        
        # Set up utility directories
        self.db_dir = self.cache_dir / "db"
        self.temp_dir = self.cache_dir / "temp"
        self.logs_dir = self.app_dir / "logs"
    
    def _create_directory_structure(self):
        """Create the directory structure."""
        directories = [
            self.app_dir,
            self.user_data_dir,
            self.cache_dir,
            self.config_dir,
            self.games_dir,
            self.mods_dir,
            self.soundpacks_dir,
            self.fonts_dir,
            self.backups_dir,
            self.db_dir,
            self.temp_dir,
            self.logs_dir,
        ]
        
        for directory in directories:
            if directory:
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                    self.logger.debug(f"Created directory: {directory}")
                except Exception as e:
                    self.logger.error(f"Failed to create directory {directory}: {e}")
                    raise
    
    def get_game_install_dir(self, game: str, install_name: str) -> Path:
        """
        Get the installation directory for a specific game install.
        
        Args:
            game: Game identifier (e.g., 'dda', 'bn')
            install_name: Name of the installation
            
        Returns:
            Path: Path to the game installation directory
        """
        return self.games_dir / game / install_name
    
    def get_game_user_dir(self, game: str) -> Path:
        """
        Get the user data directory for a specific game.
        
        Args:
            game: Game identifier (e.g., 'dda', 'bn')
            
        Returns:
            Path: Path to the game user data directory
        """
        
        return self.games_dir / game / "userdata"
    
    def get_mod_dir(self, mod_name: str) -> Path:
        """
        Get the directory for a specific mod.
        
        Args:
            mod_name: Name of the mod
            
        Returns:
            Path: Path to the mod directory
        """
        return self.mods_dir / mod_name
    
    def get_soundpack_dir(self, soundpack_name: str) -> Path:
        """
        Get the directory for a specific soundpack.
        
        Args:
            soundpack_name: Name of the soundpack
            
        Returns:
            Path: Path to the soundpack directory
        """
        return self.soundpacks_dir / soundpack_name
    
    def get_backup_dir(self, game: str) -> Path:
        """
        Get the backup directory for a specific game.
        
        Args:
            game: Game identifier (e.g., 'dda', 'bn')
            
        Returns:
            Path: Path to the game backup directory
        """
        return self.backups_dir / game
    
    def get_logs_dir(self) -> Path:
        """
        Get the logs directory.
        
        Args:
        Returns:
            Path: Path to the logs directory
        """
        return self.logs_dir
    
    def get_cache_file(self, filename: str) -> Path:
        """
        Get a cache file path.
        
        Args:
            filename: Name of the cache file
            
        Returns:
            Path: Path to the cache file
        """
        return self.cache_dir / filename
    
    def get_temp_file(self, filename: str) -> Path:
        """
        Get a temporary file path.
        
        Args:
            filename: Name of the temporary file
            
        Returns:
            Path: Path to the temporary file
        """
        return self.temp_dir / filename
    
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        try:
            if self.temp_dir and self.temp_dir.exists():
                for file_path in self.temp_dir.iterdir():
                    if file_path.is_file():
                        file_path.unlink()
                        self.logger.debug(f"Deleted temp file: {file_path}")
                
                self.logger.info("Temporary files cleaned up")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up temporary files: {e}")
    
    def get_installs_summary(self) -> Dict[str, Dict[str, str]]:
        """
        Get a summary of all game installations.

        TODO: Move this to installation manager
        
        Returns:
            Dict[str, Dict[str, str]]: Dictionary mapping games to their installations
        """
        summary = {}
        
        try:
            if not self.games_dir or not self.games_dir.exists():
                return summary
            
            for game_dir in self.games_dir.iterdir():
                if game_dir.is_dir():
                    game_name = game_dir.name
                    summary[game_name] = {}
                    
                    for install_dir in game_dir.iterdir():
                        if install_dir.is_dir():
                            install_name = install_dir.name
                            summary[game_name][install_name] = str(install_dir)
            
        except Exception as e:
            self.logger.error(f"Error getting installs summary: {e}")
        
        return summary
    
    def shutdown(self):
        """Shutdown the path manager and clean up."""
        try:
            self.logger.info("Shutting down path manager...")
            self.cleanup_temp_files()
            self.logger.info("Path manager shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during path manager shutdown: {e}")


# Global path manager instance (will be initialized by the application)
paths: Optional[PathManager] = None


def get_paths() -> PathManager:
    """
    Get the global path manager instance.
    
    Returns:
        PathManager: Global path manager instance
        
    Raises:
        RuntimeError: If path manager hasn't been initialized
    """
    if paths is None:
        raise RuntimeError("Path manager not initialized")
    return paths


def initialize_paths(app_name: str = "YACL") -> bool:
    """
    Initialize the global path manager instance.
    
    Args:
        app_name: Name of the application
        
    Returns:
        bool: True if initialization was successful
    """
    global paths
    try:
        paths = PathManager()
        return paths.initialize(app_name)
    except Exception as e:
        logging.getLogger("YACL").error(f"Failed to initialize global paths: {e}")
        return False


def shutdown_paths():
    """Shutdown the global path manager instance."""
    global paths
    if paths:
        paths.shutdown()
        paths = None
