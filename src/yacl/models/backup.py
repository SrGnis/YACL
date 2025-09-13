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

@dataclass
class SaveBackup:
    """Represents a save backup."""
    name: str
    game: GameType
    created_at: datetime
    size: int
    save_games: List[SaveGame]
    path: Path
