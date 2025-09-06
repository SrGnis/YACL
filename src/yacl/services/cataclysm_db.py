"""
Cataclysm Database Management System for YACL

This module provides the CataclysmDbManager class for managing local JSON databases
of Cataclysm game releases and assets. It handles version checking, remote updates,
and local caching of release data.
"""

import logging
import json
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime

from yacl.services.paths import get_paths
from yacl.services.settings import get_settings
from yacl.models.game_type import GameType


class CataclysmDbError(Exception):
    """Custom exception for database-related errors."""
    pass


class CataclysmDbManager:
    """
    Database management system for Cataclysm game releases.
    
    This class handles:
    - Local database storage in cache/db/ directory
    - Version checking against remote database
    - Downloading updated database files
    - Loading and saving database data
    - Integration with existing release management
    """
    
    # Remote database configuration
    REMOTE_BASE_URL = "https://github.com/SrGnis/cataclysm-db/releases/download/latest"
    INDEX_FILENAME = "index.json"
    
    def __init__(self):
        """Initialize the database manager."""
        self.logger = logging.getLogger("YACL")
        self.paths = get_paths()
        self.settings = get_settings()
        
        # Database paths
        self.db_dir = self.paths.db_dir
        self.index_file = self.db_dir / self.INDEX_FILENAME
        
        # Local database state
        self.local_index: Dict[str, Dict[str, Any]] = {}
        self.remote_index: Dict[str, Dict[str, Any]] = {}
        
        # HTTP session for downloads with retry strategy
        self.session = requests.Session()
        self.session.timeout = 30 # type: ignore

        # Configure retry strategy for network resilience
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.logger.info("Cataclysm database manager initialized")
    
    def initialize(self) -> bool:
        """
        Initialize the database system.
        
        Returns:
            bool: True if initialization was successful
        """
        try:
            self.logger.info("Initializing Cataclysm database system...")
            
            # Ensure database directory exists
            if not self._ensure_db_directory():
                return False
            
            # Load local index
            self._load_local_index()
            
            self.logger.info("Cataclysm database system initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database system: {e}")
            return False
    
    def check_and_update_databases(self) -> bool:
        """
        Check for database updates and download if needed.

        Returns:
            bool: True if check/update was successful
        """
        try:
            self.logger.info("Checking for database updates...")

            # Check if automatic database updates are enabled
            if not self.settings.read("enable_db_auto_update", True):
                self.logger.info("Automatic database updates are disabled in settings, using local data only")
                return True

            # Fetch remote index
            if not self._fetch_remote_index():
                self.logger.warning("Failed to fetch remote index, using local data")
                return True  # Continue with local data

            # Determine which databases need updates
            updates_needed = self._determine_updates_needed()

            if not updates_needed:
                self.logger.info("All databases are up to date")
                return True

            # Download updated databases
            success = self._download_database_updates(updates_needed)

            if success:
                # Update local index with new versions
                self._update_local_index()
                self.logger.info("Database updates completed successfully")
            else:
                self.logger.warning("Some database updates failed")

            return success

        except Exception as e:
            self.logger.error(f"Error during database update check: {e}")
            return False
    
    def load_game_database(self, game_type: GameType) -> Optional[Dict[str, Any]]:
        """
        Load database for a specific game type.

        Args:
            game_type: Game type to load database for

        Returns:
            Dict containing game database data, or None if not available
        """
        if not game_type or not game_type.name:
            self.logger.error("Invalid game type provided to load_game_database")
            return None

        try:
            db_file = self.db_dir / game_type.name / f"{game_type.name}_releases.json"

            if not db_file.exists():
                self.logger.debug(f"No database file found for {game_type.name} at {db_file}")
                return None

            with open(db_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Basic validation
            if not isinstance(data, dict):
                self.logger.error(f"Invalid database format for {game_type.name}: expected dict, got {type(data)}")
                return None

            # Validate required fields
            if 'releases' not in data:
                self.logger.warning(f"Database for {game_type.name} missing 'releases' field")
                data['releases'] = {}

            self.logger.debug(f"Loaded database for {game_type.name} with {len(data.get('releases', {}))} releases")
            return data

        except Exception as e:
            self.logger.error(f"Unexpected error loading database for {game_type.name}: {e}", exc_info=True)
            return None
    
    def save_game_database(self, game_type: GameType, data: Dict[str, Any]) -> bool:
        """
        Save database for a specific game type.
        
        Args:
            game_type: Game type to save database for
            data: Database data to save
            
        Returns:
            bool: True if save was successful
        """
        try:
            game_db_dir = self.db_dir / game_type.name
            game_db_dir.mkdir(parents=True, exist_ok=True)
            
            db_file = game_db_dir / f"{game_type.name}_releases.json"
            
            with open(db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Saved database for {game_type.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save database for {game_type.name}: {e}")
            return False
    
    def _ensure_db_directory(self) -> bool:
        """Ensure database directory structure exists."""
        try:
            self.db_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Database directory ensured: {self.db_dir}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create database directory: {e}")
            return False
    
    def _load_local_index(self) -> None:
        """Load local index file."""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.local_index = json.load(f)
                self.logger.debug("Loaded local database index")
            else:
                self.local_index = {}
                self.logger.debug("No local index found, starting with empty index")
        except Exception as e:
            self.logger.error(f"Failed to load local index: {e}")
            self.local_index = {}
    
    def _fetch_remote_index(self) -> bool:
        """Fetch remote index file."""
        try:
            url = f"{self.REMOTE_BASE_URL}/{self.INDEX_FILENAME}"
            self.logger.debug(f"Fetching remote index from: {url}")
            
            response = self.session.get(url)
            response.raise_for_status()
            
            self.remote_index = response.json()
            self.logger.debug("Fetched remote database index")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Network error fetching remote index: {e}")
            return False
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in remote index: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error fetching remote index: {e}")
            return False
    
    def _determine_updates_needed(self) -> List[str]:
        """Determine which game databases need updates."""
        updates_needed = []
        
        for game_name, remote_info in self.remote_index.items():
            remote_version = remote_info.get('version', 0)
            local_version = self.local_index.get(game_name, {}).get('version', 0)
            
            if remote_version > local_version:
                updates_needed.append(game_name)
                self.logger.debug(f"Update needed for {game_name}: {local_version} -> {remote_version}")
        
        return updates_needed
    
    def _download_database_updates(self, game_names: List[str]) -> bool:
        """Download database updates for specified games"""
        success_count = 0
        total_count = len(game_names)

        for game_name in game_names:
            if self._download_single_database(game_name):
                success_count += 1

        # Consider it successful if at least some downloads succeeded
        overall_success = success_count > 0

        if success_count == total_count:
            self.logger.info(f"Successfully updated all {total_count} databases")
        elif success_count > 0:
            self.logger.warning(f"Updated {success_count}/{total_count} databases")
        else:
            self.logger.error("Failed to update any databases")

        return overall_success

    def _download_single_database(self, game_name: str) -> bool:
        """
        Download database for a single game with retry logic.

        Args:
            game_name: Name of the game to download database for

        Returns:
            bool: True if download was successful
        """
        filename = f"{game_name}_releases.json"
        url = f"{self.REMOTE_BASE_URL}/{filename}"

        try:
            self.logger.info(f"Downloading database update for {game_name}...")

            # Download with timeout and retries
            response = self.session.get(url)
            response.raise_for_status()

            # Convert to expected format
            try:
                response_data = response.json()
                data = {
                    'game_type': game_name,
                    'last_updated': datetime.now().isoformat(),
                    'releases': {}
                }

                # Index the data by tag name
                data['releases'] = {release['tag_name']: release for release in response_data}
            
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in database file: {e}")

            # Create game directory
            game_dir = self.db_dir / game_name
            game_dir.mkdir(parents=True, exist_ok=True)

            self.save_game_database(GameType.get_game_type_by_name(game_name), data)

            return True

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, 
                requests.exceptions.RequestException) as e:
            self.logger.error(f"Network error downloading {game_name} database: {e}")
            return False
        except (ValueError, Exception) as e:
            self.logger.error(f"Error downloading {game_name} database: {e}")
            return False
    
    def _update_local_index(self) -> None:
        """Update local index with remote version information."""
        try:
            # Update local index with remote versions
            for game_name, remote_info in self.remote_index.items():
                if game_name not in self.local_index:
                    self.local_index[game_name] = {}
                self.local_index[game_name]['version'] = remote_info.get('version', 0)
                self.local_index[game_name]['last_updated'] = datetime.now().isoformat()

            # Save updated index
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.local_index, f, indent=2, ensure_ascii=False)

            self.logger.debug("Updated local database index")

        except Exception as e:
            self.logger.error(f"Failed to update local index: {e}")

    def is_database_enabled(self) -> bool:
        """
        Check if the database system is enabled in settings.

        Returns:
            bool: True if database system is enabled
        """
        return self.settings.read("enable_cataclysm_db", True)

    def is_auto_update_enabled(self) -> bool:
        """
        Check if automatic database updates are enabled in settings.

        Returns:
            bool: True if auto-updates are enabled
        """
        return self.settings.read("enable_db_auto_update", True)


# Global database manager instance
cataclysm_db_manager: Optional[CataclysmDbManager] = None


def get_cataclysm_db_manager() -> CataclysmDbManager:
    """
    Get the global database manager instance.
    
    Returns:
        CataclysmDbManager: Global database manager instance
        
    Raises:
        RuntimeError: If database manager hasn't been initialized
    """
    if cataclysm_db_manager is None:
        raise RuntimeError("Cataclysm database manager not initialized")
    return cataclysm_db_manager


def initialize_cataclysm_db_manager() -> bool:
    """
    Initialize the global database manager instance.
    
    Returns:
        bool: True if initialization was successful
    """
    global cataclysm_db_manager
    try:
        cataclysm_db_manager = CataclysmDbManager()
        return cataclysm_db_manager.initialize()
    except Exception as e:
        logging.getLogger("YACL").error(f"Failed to initialize Cataclysm database manager: {e}")
        return False


def shutdown_cataclysm_db_manager():
    """Shutdown the global database manager instance."""
    global cataclysm_db_manager
    if cataclysm_db_manager:
        cataclysm_db_manager = None
