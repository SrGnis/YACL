"""
Backup Data Models for YACL

This module contains all data classes, enums, and exceptions related to game backups.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

from yacl.models.release import GameType

@dataclass
class SaveGame:
    """Represents a save game."""
    name: str
    game: GameType
    path: Path

    def __post_init__(self):
        """Validate save game data after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate the save game data.

        Raises:
            ValueError: If validation fails
        """
        if not self.name or not self.name.strip():
            raise ValueError("Save game name cannot be empty")

        if not isinstance(self.path, Path):
            raise ValueError("Save game path must be a Path object")

        # Note: We don't check if path exists here because it might be used
        # for save games that are being created or have been moved

    @property
    def is_valid(self) -> bool:
        """Check if the save game is valid without raising exceptions."""
        try:
            self.validate()
            return True
        except ValueError:
            return False

    @property
    def exists(self) -> bool:
        """Check if the save game path exists."""
        return self.path.exists() and self.path.is_dir()

@dataclass
class SaveBackup:
    """Represents a save backup."""
    name: str
    game: GameType
    created_at: datetime
    size: int
    save_games: List[SaveGame]
    path: Path
