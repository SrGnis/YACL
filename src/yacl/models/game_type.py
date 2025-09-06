"""
Game Type Model for YACL
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List, ClassVar, Tuple

@dataclass(frozen=True)
class GameType:
    """
    Represents a game type with its attributes.
    """
    logger = logging.getLogger("YACL")
    other: ClassVar['GameType']
    all: ClassVar[List['GameType']]

    name: str
    display_name: str
    repository: Optional[str] = None
    executable_name: Optional[Dict[str, str]] = None

    def __hash__(self) -> int:
        return hash((self.name, self.display_name, self.repository))

    def to_dict(self) -> Dict[str, Any]:
        """Convert GameType to dictionary representation."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "repository": self.repository,
            "executable_name": self.executable_name
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameType':
        """Create GameType from dictionary representation."""
        return cls(
            name=data["name"],
            display_name=data["display_name"],
            repository=data.get("repository"),
            executable_name=data.get("executable_name")
        )
    
    @classmethod
    def get_game_type_by_name(cls, name: str) -> 'GameType':
        """
        Get a specific game type by name.

        Args:
            name: Name of the game type to find

        Returns:
            GameType: The game type if found, GameType.other otherwise
        """
        for game_type in cls.all:
            if game_type.name == name:
                return game_type
        return GameType.other
    
    @classmethod
    def get_game_type_by_display_name(cls, display_name: str) -> 'GameType':
        """
        Get a specific game type by display name.

        Args:
            display_name: Display name of the game type to find

        Returns:
            GameType: The game type if found, GameType.other otherwise
        """
        for game_type in cls.all:
            if game_type.display_name == display_name:
                return game_type
        return GameType.other
    
    @classmethod
    def add_game_type(cls, game_type: 'GameType') -> bool:
        """
        Add a new game type to core settings.

        Args:
            game_type: GameType instance to add

        Returns:
            bool: True if game type was added successfully
        """
        try:
            game_types = cls.all

            # Check if game type already exists
            for existing in game_types:
                if existing.name == game_type.name:
                    cls.logger.warning(f"Game type '{game_type.name}' already exists")
                    return False

            # Add new game type before 'other'
            game_types.insert(-1, game_type)

            return True

        except Exception as e:
            cls.logger.error(f"Failed to add game type: {e}")
            return False


GameType.other = GameType("other", "Other", executable_name={"windows": "cataclysm-tiles.exe", "linux": "cataclysm-launcher"})
GameType.all = [GameType.other]



