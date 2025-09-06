"""
Installation Data Models for YACL

This module contains all data classes, enums, and exceptions related to game installations.
"""

from enum import Enum
from datetime import datetime
from pathlib import Path
from typing import Optional

from yacl.models.release import GameType, ReleaseChannel, GameRelease, ReleaseAsset
from yacl.services.settings import get_settings, GameType
from yacl.utils.helpers import load_json_file, save_json_file

INFO_FILENAME: str = "install_info.json"


class InstallationStatus(Enum):
    """Installation status enumeration."""
    PENDING = "pending"
    EXTRACTING = "extracting"
    INSTALLING = "installing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class InstallationContext:
    """Represents the context of an ongoing installation."""
    def __init__(self, release: GameRelease, asset: ReleaseAsset, update_existing: bool, context_id: str):
        self.context_id = context_id
        self.release = release
        self.asset = asset
        self.update_existing = update_existing
        self.started_at = datetime.now()
        self.status = InstallationStatus.PENDING
        self.progress: float = 0
        self.donwload_file_path = ""
        self.install_path = ""


class InstallationError(Exception):
    """Exception raised for installation-related errors."""
    pass

class GameInstallation:
    """Represents a game installation with metadata."""
    def __init__(self, name: str, version: str = "unknown", game_type: GameType = GameType.other,
                channel: ReleaseChannel = ReleaseChannel.EXPERIMENTAL, asset_name: str = "unknown", asset_size: int = 0,
                download_url: str = "", release_id: str = "", release_published_at: str = "",
                release_body: str = "", installation_size: int = 0, install_path: str = ""):
        
        self.metadata_version = "1.0"
        self.name = name
        self.version = version
        self.game_type = game_type
        self.channel = channel
        self.asset_name = asset_name
        self.asset_size = asset_size
        self.download_url = download_url
        self.release_id = release_id
        self.release_published_at = release_published_at
        self.release_body = release_body
        self.installation_size = installation_size
        self.install_date = datetime.now().isoformat()
        self.install_path = install_path
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create a GameInstallation from a dictionary."""
        return cls(
            name=data.get("name", "unknown"),
            version=data.get("version", "unknown"),
            game_type=GameType.get_game_type_by_name(data.get("game_type", "other")),
            channel=ReleaseChannel(data.get("channel", "unknown")),
            asset_name=data.get("asset_name", "unknown"),
            asset_size=data.get("asset_size", 0),
            download_url=data.get("download_url", ""),
            release_id=data.get("release_id", ""),
            release_published_at=data.get("release_published_at", ""),
            release_body=data.get("release_body", ""),
            installation_size=data.get("installation_size", 0),
            install_path=data.get("install_path", "")
        )
    
    def to_dict(self) -> dict:
        """Convert the GameInstallation to a dictionary for serialization."""
        return {
            "metadata_version": self.metadata_version,
            "name": self.name,
            "version": self.version,
            "game_type": self.game_type.name,
            "channel": self.channel.value,
            "asset_name": self.asset_name,
            "asset_size": self.asset_size,
            "download_url": self.download_url,  
            "release_id": self.release_id,
            "release_published_at": self.release_published_at,
            "release_body": self.release_body,
            "installation_size": self.installation_size,
            "install_date": self.install_date,
            "install_path": self.install_path
        }

    def save(self, file_path: str | Path):
        """Save installation metadata to a file."""
        save_json_file(file_path, self.to_dict())

    @classmethod
    def load(cls, file_path: str | Path) -> Optional['GameInstallation']:
        """Load installation metadata from a file."""
        data = load_json_file(file_path)
        if not data:
            return None
        return cls.from_dict(data)
