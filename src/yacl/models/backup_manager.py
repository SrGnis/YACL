"""
Backup Manager for YACL

This module provides the BackupManager class for managing game backups.
"""

import json
import shutil
import zipfile
from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional

from yacl.models.game_type import GameType
from yacl.models.backup import SaveBackup, SaveGame
from yacl.services.paths import get_paths
from yacl.services.events import EventManager, Events


class BackupError(Exception):
    """Custom exception for backup-related errors."""
    pass


class BackupManager:
    """Manages game backups."""

    def __init__(self, event_manager: EventManager):
        self.logger = logging.getLogger("YACL")
        self.logger.info("Initializing backup manager...")

        self.event_manager = event_manager
        self.backups: Dict[GameType, Dict[str, SaveBackup]] = {}
        self.paths = get_paths()

        self.logger.info("Backup manager initialized successfully")

    def load_backups(self, game_type: GameType) -> None:
        """
        Load existing backups for a specific game type.

        Args:
            game_type: The game type to load backups for

        Raises:
            BackupError: If loading backups fails
        """
        try:
            self.logger.info(f"Loading backups for {game_type.name}")

            backup_dir = self.paths.get_backup_dir(game_type.name)

            if game_type not in self.backups:
                self.backups[game_type] = {}

            self.backups[game_type].clear()

            if not backup_dir.exists():
                self.logger.info(f"No backup directory found for {game_type.name}")
                return

            for backup_path in backup_dir.iterdir():
                if backup_path.is_dir():
                    try:
                        backup = self._load_backup_from_directory(backup_path, game_type)
                        if backup:
                            self.backups[game_type][backup.name] = backup
                            self.logger.debug(f"Loaded backup: {backup.name}")
                    except Exception as e:
                        self.logger.warning(f"Failed to load backup from {backup_path}: {e}")
                        continue

            self.logger.info(f"Loaded {len(self.backups[game_type])} backups for {game_type.name}")

            # Emit backup list refreshed event
            if self.event_manager:
                self.event_manager.emit(Events.BACKUP_LIST_REFRESHED,
                                      game_type=game_type,
                                      backup_count=len(self.backups[game_type]))

        except Exception as e:
            error_msg = f"Failed to load backups for {game_type.name}: {e}"
            self.logger.error(error_msg)
            raise BackupError(error_msg) from e

    def _load_backup_from_directory(self, backup_path: Path, game_type: GameType) -> Optional[SaveBackup]:
        """
        Load a backup from a directory containing zip files.

        Args:
            backup_path: Path to the backup directory
            game_type: The game type

        Returns:
            SaveBackup object if successful, None otherwise
        """
        try:
            save_games = []
            total_size = 0

            # Only load .zip files, ignore metadata and other files
            for item in backup_path.iterdir():
                if item.is_file() and item.suffix == '.zip':
                    # Remove .zip extension to get save game name
                    save_name = item.stem
                    save_game = SaveGame(
                        name=save_name,
                        game=game_type,
                        path=item.with_suffix('')  # Path without .zip extension
                    )
                    save_games.append(save_game)
                    total_size += item.stat().st_size

            created_at = datetime.fromtimestamp(backup_path.stat().st_mtime)

            return SaveBackup(
                name=backup_path.name,
                game=game_type,
                created_at=created_at,
                size=total_size,
                save_games=save_games,
                path=backup_path
            )

        except Exception as e:
            self.logger.error(f"Failed to load backup from {backup_path}: {e}")
            return None

    def create_backup(self, game_type: GameType, backup_name: Optional[str] = None) -> SaveBackup:
        """
        Create a backup for a specific game type.

        Args:
            game_type: The game type to create backup for
            backup_name: Optional custom name for the backup

        Returns:
            SaveBackup: The created backup

        Raises:
            BackupError: If backup creation fails
        """
        try:
            self.logger.info(f"Creating backup for {game_type.name}")

            saves_dir = self.paths.get_saves_dir(game_type.name)

            if not saves_dir.exists():
                raise BackupError(f"No saves directory found for {game_type.name}")

            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}"

            backup_dir = self.paths.get_backup_dir(game_type.name)
            backup_dir.mkdir(parents=True, exist_ok=True)

            backup_path = backup_dir / backup_name

            if backup_path.exists():
                raise BackupError(f"Backup '{backup_name}' already exists")

            backup_path.mkdir(parents=True, exist_ok=True)

            save_games_to_backup: List[SaveGame] = []
            for item in saves_dir.iterdir():
                if item.is_dir() or item.is_file():
                    save_game = SaveGame(
                        name=item.name,
                        game=game_type,
                        path=item
                    )
                    save_games_to_backup.append(save_game)

            if not save_games_to_backup:
                raise BackupError(f"No save games found to backup for {game_type.name}")

            # Zip save games to backup directory
            backed_up_saves = []
            total_size = 0

            for save_game in save_games_to_backup:
                try:
                    dest_path = backup_path / save_game.name

                    shutil.make_archive(
                        str(dest_path),
                        'zip',
                        str(save_game.path)
                    )

                    # The actual zip file has .zip extension
                    zip_file_path = dest_path.with_suffix('.zip')
                    total_size += zip_file_path.stat().st_size

                    # Create backed up save game reference
                    backed_up_save = SaveGame(
                        name=save_game.name,
                        game=game_type,
                        path=dest_path
                    )
                    backed_up_saves.append(backed_up_save)

                    self.logger.debug(f"Backed up save: {save_game.name}")

                except Exception as e:
                    self.logger.warning(f"Failed to backup save {save_game.name}: {e}")
                    continue

            if not backed_up_saves:
                # Clean up empty backup directory
                shutil.rmtree(backup_path)
                raise BackupError("Failed to backup any save games")

            created_at = datetime.now()

            # Create backup object
            backup = SaveBackup(
                name=backup_name,
                game=game_type,
                created_at=created_at,
                size=total_size,
                save_games=backed_up_saves,
                path=backup_path
            )

            # Add to loaded backups
            if game_type not in self.backups:
                self.backups[game_type] = {}
            self.backups[game_type][backup_name] = backup

            self.logger.info(f"Successfully created backup '{backup_name}' with {len(backed_up_saves)} save games")

            # Emit backup created event
            if self.event_manager:
                self.event_manager.emit(Events.BACKUP_CREATED,
                                      backup=backup,
                                      game_type=game_type)

            return backup

        except Exception as e:
            error_msg = f"Failed to create backup for {game_type.name}: {e}"
            self.logger.error(error_msg)
            raise BackupError(error_msg) from e

    def delete_backup(self, backup: SaveBackup) -> None:
        """
        Delete a backup.

        Args:
            backup: The backup to delete

        Raises:
            BackupError: If backup deletion fails
        """
        try:
            self.logger.info(f"Deleting backup '{backup.name}' for {backup.game.name}")

            if not backup.path.exists():
                self.logger.warning(f"Backup path does not exist: {backup.path}")
            else:
                shutil.rmtree(backup.path)
                self.logger.debug(f"Removed backup directory: {backup.path}")

            if backup.game in self.backups and backup.name in self.backups[backup.game]:
                del self.backups[backup.game][backup.name]
                self.logger.debug(f"Removed backup from memory: {backup.name}")

            self.logger.info(f"Successfully deleted backup '{backup.name}'")

            # Emit backup deleted event
            if self.event_manager:
                self.event_manager.emit(Events.BACKUP_DELETED,
                                      backup=backup,
                                      game_type=backup.game)

        except Exception as e:
            error_msg = f"Failed to delete backup '{backup.name}': {e}"
            self.logger.error(error_msg)
            raise BackupError(error_msg) from e

    def restore_backup(self, backup: SaveBackup) -> None:
        """
        Restore a backup by extracting zip files to the saves directory.

        Args:
            backup: The backup to restore

        Raises:
            BackupError: If backup restoration fails
        """
        try:
            self.logger.info(f"Restoring backup '{backup.name}' for {backup.game.name}")

            if not backup.path.exists():
                raise BackupError(f"Backup path does not exist: {backup.path}")

            saves_dir = self.paths.get_saves_dir(backup.game.name)
            saves_dir.mkdir(parents=True, exist_ok=True)

            restored_count = 0

            for save_game in backup.save_games:
                try:
                    # Source zip file path in backup
                    zip_file_path = save_game.path.with_suffix('.zip')

                    # Check if zip file exists
                    if not zip_file_path.exists():
                        self.logger.warning(f"Backup zip file not found: {zip_file_path}")
                        continue

                    # Destination path in saves directory
                    dest_path = saves_dir / save_game.name

                    # Remove existing save if it exists
                    if dest_path.exists():
                        if dest_path.is_file():
                            dest_path.unlink()
                        elif dest_path.is_dir():
                            shutil.rmtree(dest_path)

                    # Create destination directory and extract
                    dest_path.mkdir(parents=True, exist_ok=True)
                    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                        zip_ref.extractall(dest_path)

                    restored_count += 1
                    self.logger.debug(f"Restored save: {save_game.name}")

                except Exception as e:
                    self.logger.warning(f"Failed to restore save {save_game.name}: {e}")
                    continue

            if restored_count == 0:
                raise BackupError("Failed to restore any save games from backup")

            self.logger.info(f"Successfully restored {restored_count} save games from backup '{backup.name}'")

            # Emit backup restored event
            if self.event_manager:
                self.event_manager.emit(Events.BACKUP_RESTORED,
                                      backup=backup,
                                      game_type=backup.game,
                                      restored_count=restored_count)

        except Exception as e:
            error_msg = f"Failed to restore backup '{backup.name}': {e}"
            self.logger.error(error_msg)
            raise BackupError(error_msg) from e

    def get_backups(self, game_type: GameType) -> Dict[str, SaveBackup]:
        """
        Get all loaded backups for a specific game type.

        Args:
            game_type: The game type to get backups for

        Returns:
            Dictionary of backup name to SaveBackup objects
        """
        return self.backups.get(game_type, {})

    def get_backup(self, game_type: GameType, backup_name: str) -> Optional[SaveBackup]:
        """
        Get a specific backup by name.

        Args:
            game_type: The game type
            backup_name: The backup name

        Returns:
            SaveBackup object if found, None otherwise
        """
        return self.backups.get(game_type, {}).get(backup_name)

    def backup_exists(self, game_type: GameType, backup_name: str) -> bool:
        """
        Check if a backup exists.

        Args:
            game_type: The game type
            backup_name: The backup name

        Returns:
            True if backup exists, False otherwise
        """
        return backup_name in self.backups.get(game_type, {})


# Global backup manager instance
_backup_manager: Optional[BackupManager] = None


def initialize_backup_manager(event_manager: EventManager) -> bool:
    """
    Initialize the global backup manager.

    Args:
        event_manager: Event manager for component communication

    Returns:
        bool: True if initialization was successful
    """
    global _backup_manager

    try:
        if _backup_manager is not None:
            logging.getLogger("YACL").warning("Backup manager already initialized")
            return True

        _backup_manager = BackupManager(event_manager)
        logging.getLogger("YACL").info("Global backup manager initialized")
        return True

    except Exception as e:
        logging.getLogger("YACL").error(f"Failed to initialize backup manager: {e}")
        return False


def get_backup_manager() -> BackupManager:
    """
    Get the global backup manager instance.

    Returns:
        BackupManager: The global backup manager instance

    Raises:
        RuntimeError: If backup manager is not initialized
    """
    if _backup_manager is None:
        raise RuntimeError("Backup manager not initialized")

    return _backup_manager


def shutdown_backup_manager():
    """Shutdown the global backup manager."""
    global _backup_manager

    if _backup_manager is not None:
        logging.getLogger("YACL").info("Shutting down backup manager")
        _backup_manager = None
