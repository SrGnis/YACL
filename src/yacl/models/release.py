"""
Release Data Models for YACL

This module contains all data classes, enums, and exceptions related to game releases.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from yacl.models.game_type import GameType

logger = logging.getLogger(__name__)

class ReleaseError(Exception):
    """Custom exception for release management errors."""
    pass

class ReleaseChannel(Enum):
    """Release channel enumeration."""
    STABLE = "stable"
    EXPERIMENTAL = "experimental"
    ALL = "all"

    @staticmethod
    def from_string(value: str):
        value = value.lower()
        for channel in ReleaseChannel:
            if channel.value == value:
                return channel
        raise ValueError(f"Invalid release channel: {value}")
    
    def display_name(self):
        map = {
            ReleaseChannel.STABLE: "Stable",
            ReleaseChannel.EXPERIMENTAL: "Experimental",
            ReleaseChannel.ALL: "All"
        }
        return map.get(self, "Unknown")

class AssetPlatform(Enum):
    """Supported platforms for release assets."""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    ANDROID = "android"
    UNKNOWN = "unknown"

    @classmethod
    def infer_from_filename(cls, filename: str) -> 'AssetPlatform':
        """Infer the platform from asset filename."""
        filename_lower = filename.lower()

        if "android" in filename_lower or filename_lower.endswith(".apk"):
            return AssetPlatform.ANDROID
        elif "windows" in filename_lower or filename_lower.endswith(".zip"):
            return AssetPlatform.WINDOWS
        elif "linux" in filename_lower or filename_lower.endswith(".tar.gz"):
            return AssetPlatform.LINUX
        elif any(x in filename_lower for x in ("osx", "macos")) or filename_lower.endswith(".dmg"):
            return AssetPlatform.MACOS
        else:
            return AssetPlatform.UNKNOWN

class AssetArch(Enum):
    """Supported architectures for release assets."""
    X32 = "x32"
    X64 = "x64"
    ARM32 = "arm32"
    ARM64 = "arm64"
    UNIVERSAL = "universal"
    UNKNOWN = "unknown"

    @classmethod
    def infer_from_filename(cls, filename: str) -> 'AssetArch':
        """Infer the architecture from asset filename."""
        filename_lower = filename.lower()

        if any(arch in filename_lower for arch in ("universal", "bundle")):
            return AssetArch.UNIVERSAL
        elif any(arch in filename_lower for arch in ("arm32", "aarch32", "android-x32")):
            return AssetArch.ARM32
        elif any(arch in filename_lower for arch in ("arm64", "aarch64", "android-x64", "arm")):
            return AssetArch.ARM64
        elif any(arch in filename_lower for arch in ("x64", "amd64")):
            return AssetArch.X64
        elif any(arch in filename_lower for arch in ("x32", "x86")):
            return AssetArch.X32
        else:
            return AssetArch.UNKNOWN

class AssetGraphics(Enum):
    """Supported graphics types for release assets."""
    TILES = "tiles"
    ASCII = "ascii"
    UNKNOWN = "unknown"

    @classmethod
    def infer_from_filename(cls, filename: str) -> 'AssetGraphics':
        """Infer the graphics type from asset filename."""
        filename_lower = filename.lower()

        if any(graphics in filename_lower for graphics in ("with-graphics", "graphics", "tiles", "android")):
            return AssetGraphics.TILES
        elif any(graphics in filename_lower for graphics in ("ascii", "curses", "terminal-only")):
            return AssetGraphics.ASCII
        else:
            return AssetGraphics.UNKNOWN

class AssetSounds(Enum):
    """Supported sounds types for release assets."""
    SOUNDS = "sounds"
    UNKNOWN = "unknown"
    
    @classmethod
    def infer_from_filename(cls, filename: str) -> 'AssetSounds':
        """Infer the sounds type from asset filename."""
        filename_lower = filename.lower()

        if any(sounds in filename_lower for sounds in ("with-sounds", "sounds", "and-sounds")):
            return AssetSounds.SOUNDS
        else:
            return AssetSounds.UNKNOWN

@dataclass
class ReleaseAsset:
    """Represents a downloadable asset from a release."""
    name: str = ""
    size: int = 0
    download_url: str = ""
    platform: Optional[AssetPlatform] = None
    arch: Optional[AssetArch] = None
    graphics: Optional[AssetGraphics] = None
    sounds: Optional[AssetSounds] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the ReleaseAsset object to a dictionary."""
        return {
            "name": self.name,
            "size": self.size,
            "download_url": self.download_url,
            "platform": self.platform.value if self.platform else None,
            "arch": self.arch.value if self.arch else None,
            "graphics": self.graphics.value if self.graphics else None,
            "sounds": self.sounds.value if self.sounds else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ReleaseAsset':
        """Create a ReleaseAsset instance from a dictionary."""
        asset = ReleaseAsset()

        # Handle basic fields
        asset.name = data.get('name', '')
        asset.size = data.get('size', 0)
        asset.download_url = data.get('download_url', '')

        # Handle enum fields
        asset.platform = AssetPlatform(data.get('platform')) if data.get('platform') else None
        asset.arch = AssetArch(data.get('arch')) if data.get('arch') else None
        asset.graphics = AssetGraphics(data.get('graphics')) if data.get('graphics') else None
        asset.sounds = AssetSounds(data.get('sounds')) if data.get('sounds') else None

        # Handle datetime fields
        if data.get('created_at'):
            try:
                asset.created_at = datetime.fromisoformat(data['created_at'])
            except (ValueError, TypeError):
                asset.created_at = datetime.now()

        if data.get('updated_at'):
            try:
                asset.updated_at = datetime.fromisoformat(data['updated_at'])
            except (ValueError, TypeError):
                asset.updated_at = datetime.now()

        return asset

    def from_github_data(self, data: Dict[str, Any]):
        """Create a ReleaseAsset instance from GitHub API data."""
        self._parse_github_asset_data(data)

    def _parse_github_asset_data(self, asset_data: Dict[str, Any]):        
        """Parse a single asset from GitHub API response into a ReleaseAsset object."""
        self.name = asset_data["name"]
        self.size = asset_data["size"]
        self.download_url = asset_data["browser_download_url"]
        self.created_at = datetime.fromisoformat(asset_data["created_at"].replace('Z', '+00:00'))
        self.updated_at = datetime.fromisoformat(asset_data["updated_at"].replace('Z', '+00:00'))

        self.platform = AssetPlatform.infer_from_filename(self.name)
        self.arch = AssetArch.infer_from_filename(self.name)
        self.graphics = AssetGraphics.infer_from_filename(self.name)
        self.sounds = AssetSounds.infer_from_filename(self.name)

@dataclass
class GameRelease:
    """Represents a game release with metadata."""
    id: int = 0
    name: str = ""
    prerelease: bool = False
    assets: List[ReleaseAsset] = field(default_factory=list)

    # Parsed metadata
    channel: ReleaseChannel = ReleaseChannel.STABLE
    game_type: GameType = GameType.other

    # Additional metadata that might be available
    tag_name: Optional[str] = None
    body: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the GameRelease object to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "tag_name": self.tag_name,
            "prerelease": self.prerelease,
            "channel": self.channel.value,
            "game_type": self.game_type.name,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "body": self.body,
            "assets": [asset.to_dict() for asset in self.assets]
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'GameRelease':
        """Create a GameRelease instance from a dictionary."""
        release = GameRelease()

        # Handle basic fields
        release.id = data.get('id', 0)
        release.name = data.get('name', '')
        release.prerelease = data.get('prerelease', False)
        release.tag_name = data.get('tag_name')
        release.body = data.get('body')
        release.game_type = GameType.get_game_type_by_name(data.get('game_type', 'other'))

        # Handle enum fields
        channel_value = data.get('channel', 'stable')
        release.channel = ReleaseChannel(channel_value) if channel_value else ReleaseChannel.STABLE

        # Handle datetime fields
        if data.get('published_at'):
            try:
                release.published_at = datetime.fromisoformat(data['published_at'])
            except (ValueError, TypeError):
                pass

        if data.get('created_at'):
            try:
                release.created_at = datetime.fromisoformat(data['created_at'])
            except (ValueError, TypeError):
                pass

        # Handle assets
        assets_data = data.get('assets', [])
        release.assets = []
        for asset_dict in assets_data:
            asset = ReleaseAsset.from_dict(asset_dict)
            release.assets.append(asset)

        return release

    def from_github_data(self, data: Dict[str, Any], game_type: GameType):
        """Create a GameRelease instance from GitHub API data."""
        self._parse_github_release_data(data, game_type)

    def _parse_github_release_data(self, release_data: Dict[str, Any], game_type: GameType):
        """
        Parse a single release from GitHub API response into a GameRelease object.

        Args:
            release_data: Raw release data from GitHub API
            game_type: Game type for metadata inference

        Returns:
            GameRelease: Parsed release object
        """
        # Extract basic release information
        self.id = release_data["id"]
        self.name = release_data["name"]
        self.prerelease = release_data.get("prerelease", False)
        self.tag_name = release_data.get("tag_name")
        self.body = release_data.get("body")
        self.game_type = game_type

        # Parse timestamps
        if release_data.get("published_at"):
            try:
                self.published_at = datetime.fromisoformat(release_data["published_at"].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                pass

        if release_data.get("created_at"):
            try:
                self.created_at = datetime.fromisoformat(release_data["created_at"].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                pass

        # Parse assets
        for asset_data in release_data.get("assets", []):
            try:
                asset = ReleaseAsset()
                asset.from_github_data(asset_data)
                self.assets.append(asset)
            except Exception as e:
                logger.warning(f"Failed to parse asset {asset_data.get('name', 'unknown')}: {e}")
                continue

        self.channel = self._infer_release_channel(self.name, self.prerelease)

    @staticmethod
    def _infer_release_channel(name: str, prerelease: bool) -> ReleaseChannel:
        """Infer the release channel from release name and prerelease flag."""
        if prerelease or "experimental" in name.lower():
            return ReleaseChannel.EXPERIMENTAL
        return ReleaseChannel.STABLE

    



    