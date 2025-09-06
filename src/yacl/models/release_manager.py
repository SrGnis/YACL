"""
Release Management System for YACL

This module provides the ReleaseManager class for Git-based release tag fetching
and GitHub API integration for fetching game releases, parsing release data,
and managing different game channels (stable/experimental).
"""

import logging
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from yacl.services.settings import get_settings, GameType
from yacl.services.cataclysm_db import get_cataclysm_db_manager
from yacl.services.events import EventManager, Events
from yacl.models.release import (
    ReleaseChannel,
    GameRelease,
    ReleaseError
)

class ReleaseManager:
    """
    Release management system for YACL.
    """

    def __init__(self, event_manager: Optional[EventManager] = None):
        """
        Initialize the release manager.
        """
        self.logger = logging.getLogger("YACL")
        self.event_manager = event_manager

        # Current state
        self.loaded_releases: Dict[GameType, Dict[str, GameRelease]] = {}
        self.releases_by_channel: Dict[GameType, Dict[ReleaseChannel, Dict[str, GameRelease]]] = {}

        # Track last fetch time for each game type
        self.last_fetch_time: Dict[GameType, datetime] = {}

        self.logger.info("Release manager initialized")

    def fetch_releases(self, game_type: GameType,
                    channel: ReleaseChannel,
                    limit: Optional[int] = None):
        """
        Fetch releases for a specific game type and channel.

        Args:
            game_type: Game type to fetch releases for (uses current if None)
            channel: Release channel filter (uses current if None)
            limit: Maximum number of releases to fetch (uses setting if None)

        Raises:
            ReleaseError: If releases cannot be fetched
        """
        try:
            if not game_type:
                raise ReleaseError("No game type specified")

            # Get settings for request limits
            settings = get_settings()
            if limit is None:
                limit = int(settings.read("num_releases_to_request", 20)) # Github API max is 100

            # Emit fetch started event
            if self.event_manager:
                self.event_manager.emit(Events.RELEASE_FETCH_STARTED,
                                    game_type=game_type.name,
                                    channel=channel.value)

            self.logger.info(f"Fetching {game_type.name} releases...")

            # Fetch releases
            self._fetch_releases(game_type, limit)

            # Get count for this specific game type
            release_count = len(self.loaded_releases.get(game_type, {}))

            # Update last fetch time
            self.last_fetch_time[game_type] = datetime.now()
            get_settings().store(f"last_fetch_time_{game_type.name}", self.last_fetch_time[game_type].isoformat())

            # Emit fetch completed event
            if self.event_manager:
                self.event_manager.emit(Events.RELEASE_FETCH_COMPLETED,
                                    game_type=game_type.name,
                                    channel=channel.value,
                                    count=release_count)

            self.logger.info(f"Found {release_count} {channel.value} releases")

        except Exception as e:
            self.logger.error(f"Failed to get releases: {e}")
            # Error already logged above

            if self.event_manager:
                self.event_manager.emit(Events.ERROR_OCCURRED,
                                    error=str(e),
                                    context="release_fetch")
            raise


    def _fetch_releases(self, game_type: GameType, limit: int):
        """
        Fetch releases for a specific game type and store them in the cache.

        Args:
            game_type: Game type to fetch releases for
            limit: Maximum number of releases to fetch

        Returns:
            List[GameRelease]: List of parsed releases
        """
        repo_name = game_type.repository
        if not repo_name:
            raise ReleaseError(f"No repository configured for game type: {game_type}")

        # Fetch from GitHub API
        api_releases = []
        try:
            api_releases = self._fetch_releases_from_api(game_type, repo_name, limit)
        except Exception as e:
            self.logger.warning(f"Failed to fetch from GitHub API: {e}")

        # Merge the actual releases with API releases
        self._merge_releases(api_releases, game_type)

        # Save merged data back to database for future use
        self._save_releases_to_database(game_type)

    def _merge_releases(self, new_releases: List[GameRelease], game_type: GameType) -> None:
        """
        Merge new releases with the actual releases.

        Args:
            api_releases: List of releases from GitHub API
            game_type: Game type for logging
        """
        try:
            # For each new release, check if we already have it
            for new_release in reversed(new_releases):  # Reverse to add newer releases first
                if new_release.tag_name not in self.loaded_releases[game_type]:
                    if new_release.tag_name:
                        # Create new dictionaries with the new release first
                        # TODO: migrate to ordered dict
                        updated_loaded = {new_release.tag_name: new_release}
                        updated_loaded.update(self.loaded_releases[game_type])
                        self.loaded_releases[game_type] = updated_loaded

                        updated_channel = {new_release.tag_name: new_release}
                        updated_channel.update(self.releases_by_channel[game_type][new_release.channel])
                        self.releases_by_channel[game_type][new_release.channel] = updated_channel

                        self.logger.debug(f"Added new release {new_release.name} to {game_type.name} {new_release.channel.value} channel")
                    else:
                        self.logger.warning(f"Release {new_release.name} has no tag name, skipping")

        except Exception as e:
            self.logger.error(f"Failed to merge releases for {game_type.name}: {e}")

    def _fetch_releases_from_api(self, game_type: GameType, repo_name: str, limit: int) -> List[GameRelease]:
        """
        Fetch releases from GitHub API and parse them into GameRelease objects.

        Args:
            game_type: Game type for metadata inference
            repo_name: Repository name in format "owner/repo"
            limit: Maximum number of releases to fetch

        Returns:
            List[GameRelease]: List of parsed releases

        Raises:
            ReleaseError: If API request fails or response is invalid
        """
        url = f"https://api.github.com/repos/{repo_name}/releases?per_page={limit}"

        try:
            self.logger.info(f"Fetching releases from GitHub API: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            releases_data = response.json()
            if not isinstance(releases_data, list):
                raise ReleaseError("Invalid API response: expected list of releases")

            releases = []
            for release_data in releases_data:
                try:
                    release = GameRelease()
                    release.from_github_data(release_data, game_type)
                    releases.append(release)
                except Exception as e:
                    self.logger.warning(f"Failed to parse release {release_data.get('name', 'unknown')}: {e}")
                    continue

            self.logger.info(f"Successfully parsed {len(releases)} releases")
            return releases

        except requests.RequestException as e:
            raise ReleaseError(f"Failed to fetch releases from GitHub API: {e}")
        except Exception as e:
            raise ReleaseError(f"Failed to parse API response: {e}")

    def _load_releases_from_database(self, game_type: GameType):
        """
        Load releases from local database.

        Args:
            game_type: Game type to load releases for

        Returns:
            Dict[str, GameRelease]: Dict of releases from database, empty if none found
        """
        try:
            try:
                db_manager = get_cataclysm_db_manager()
            except RuntimeError:
                self.logger.debug(f"Database manager not available for {game_type.name}")
                return {}

            db_data = db_manager.load_game_database(game_type)
            if not db_data:
                self.logger.debug(f"No database data found for {game_type.name}")
                return {}

            releases_data = db_data.get('releases', {})

            for release_data in releases_data.values():
                try:
                    release = GameRelease.from_dict(release_data)
                    release.game_type = game_type  # Ensure game type is set
                    if release.tag_name:
                        self.loaded_releases[game_type][release.tag_name] = release
                        self.releases_by_channel[game_type][release.channel][release.tag_name] = release
                    else:
                        self.logger.warning(f"Release from database for {game_type.name} has no tag name: {release_data}")
                except Exception as e:
                    self.logger.warning(f"Failed to parse database release: {e}")
                    continue

        except Exception as e:
            self.logger.warning(f"Failed to load releases from database for {game_type.name}: {e}")
            return {}
        
    def _load_all_releases_from_database(self) -> None:
        """
        Load all releases from local database for all game types.
        """
        for game_type in GameType.all:
            self._load_releases_from_database(game_type)

    def _save_releases_to_database(self, game_type: GameType) -> None:
        """
        Save releases to local database.

        Args:
            game_type: Game type to save releases for
        """
        try:
            from yacl.services.cataclysm_db import get_cataclysm_db_manager

            # Check if database manager is available (may be disabled)
            try:
                db_manager = get_cataclysm_db_manager()
            except RuntimeError:
                self.logger.debug(f"Database manager not available for {game_type.name} (may be disabled), skipping save")
                return

            # Convert releases to dictionary format
            releases_data = {}
            for tag_name, release in self.loaded_releases[game_type].items():
                try:
                    release_dict = release.to_dict()
                    releases_data[tag_name] = release_dict
                except Exception as e:
                    self.logger.warning(f"Failed to serialize release {release.name}: {e}")
                    continue

            # Create database structure
            db_data = {
                'game_type': game_type.name,
                'last_updated': datetime.now().isoformat(),
                'releases': releases_data,
            }

            # Save to database
            if db_manager.save_game_database(game_type, db_data):
                self.logger.debug(f"Saved {len(releases_data)} releases to database for {game_type.name}")
            else:
                self.logger.warning(f"Failed to save releases to database for {game_type.name}")

        except Exception as e:
            self.logger.warning(f"Error saving releases to database for {game_type.name}: {e}")



    def _group_releases_by_channel(self, releases: Dict[str, GameRelease]) -> Dict[ReleaseChannel, Dict[str, GameRelease]]:
        """
        Group releases by their channel.

        Args:
            releases: Dict of releases to group

        Returns:
            Dict[ReleaseChannel, Dict[str, GameRelease]]: Releases grouped by channel
        """
        grouped = {channel: {} for channel in ReleaseChannel}

        for tag_name, release in releases.items():
            grouped[release.channel][tag_name] = release

        return grouped

    def get_releases(self, game_type: GameType,
                    channel: ReleaseChannel,
                    limit: Optional[int] = None,
                    force_refresh: bool = False) -> List[GameRelease]:
        """
        Get releases for a specific game type and channel.

        Args:
            game_type: Game type to get releases for (uses current if None)
            channel: Release channel filter (uses current if None)
            limit: Maximum number of releases to return (no limit if None)
            force_refresh: Whether to force refresh from API

        Returns:
            List[GameRelease]: List of releases matching the criteria
        """
        if not game_type:
            self.logger.warning("No game type specified for get_releases")
            return []

        need_fetch = False

        if force_refresh:
            need_fetch = True
            self.logger.info(f"Force refresh requested for {game_type.name}")
        elif not self.has_releases_cached(game_type):
            need_fetch = True
            self.logger.info(f"No cached releases found for {game_type.name}, fetching from API")
        elif self.last_fetch_time.get(game_type, datetime.min) < datetime.now() - timedelta(hours=3):
            need_fetch = True
            self.logger.info(f"Last fetch time for {game_type.name} is {self.last_fetch_time.get(game_type, datetime.min)}, fetching from API")
        else:
            # Check if we have releases for the specific channel
            game_releases = self.releases_by_channel.get(game_type, {})
            if channel not in game_releases or not game_releases[channel]:
                need_fetch = True
                self.logger.info(f"No cached releases found for {game_type.name} {channel.value if channel else 'default'} channel")

        # Fetch releases if needed
        if need_fetch:
            try:
                fetch_limit = limit or 20  # GitHub API default max
                self.fetch_releases(game_type, channel, fetch_limit)
            except Exception as e:
                self.logger.error(f"Failed to fetch releases for {game_type.name}: {e}")
                if not self.has_releases_cached(game_type):
                    return []

        game_releases = self.releases_by_channel.get(game_type, {})
        if not game_releases:
            self.logger.warning(f"No releases found in cache for {game_type.name}")
            return []

        # Get releases for the specific channel
        if channel:
            releases = list(game_releases.get(channel, {}).values())
        else:
            # If no channel specified, return all releases
            releases = list(game_releases.get(ReleaseChannel.ALL, {}).values())

        if limit is not None and limit > 0:
            releases = releases[:limit]

        self.logger.debug(f"Returning {len(releases)} releases for {game_type.name} {channel.value if channel else 'all'}")
        return releases

    def get_all_releases(self, game_type: GameType) -> Dict[str, GameRelease]:
        """
        Get all releases for a specific game type.

        Args:
            game_type: Game type to get releases for (uses current if None)

        Returns:
            Dict[str, GameRelease]: Dict of all releases for the game type
        """
        if not game_type:
            return {}

        return self.loaded_releases.get(game_type, {})

    def has_releases_cached(self, game_type: GameType) -> bool:
        """
        Check if releases are already cached for a specific game type.

        Args:
            game_type: Game type to check

        Returns:
            bool: True if releases are cached for this game type
        """
        return game_type in self.loaded_releases and len(self.loaded_releases[game_type]) > 0


# Global release manager instance (will be initialized by the application)
release_manager: Optional[ReleaseManager] = None


def get_release_manager() -> ReleaseManager:
    """
    Get the global release manager instance.

    Returns:
        ReleaseManager: Global release manager instance

    Raises:
        RuntimeError: If release manager hasn't been initialized
    """
    if release_manager is None:
        raise RuntimeError("Release manager not initialized")
    return release_manager


def initialize_release_manager(event_manager: Optional[EventManager] = None) -> bool:
    """
    Initialize the global release manager instance.

    Args:
        event_manager: Event manager for UI communication

    Returns:
        bool: True if initialization was successful
    """
    global release_manager
    try:
        release_manager = ReleaseManager(event_manager)

        for game_type in GameType.all:
            release_manager.loaded_releases[game_type] = {}
            release_manager.releases_by_channel[game_type] = {}
            for channel in ReleaseChannel:
                release_manager.releases_by_channel[game_type][channel] = {}

            # Load last fetch time from settings
            last_fetch_time = get_settings().read(f"last_fetch_time_{game_type.name}", None)
            if last_fetch_time:
                release_manager.last_fetch_time[game_type] = datetime.fromisoformat(last_fetch_time)
            else:
                release_manager.last_fetch_time[game_type] = datetime.min
                get_settings().store(f"last_fetch_time_{game_type.name}", datetime.min.isoformat())

        if get_settings().read("enable_cataclysm_db", True):
            release_manager._load_all_releases_from_database()

        return True
    except Exception as e:
        logging.getLogger("YACL").error(f"Failed to initialize global release manager: {e}")
        return False


def shutdown_release_manager():
    """Shutdown the global release manager instance."""
    global release_manager
    if release_manager:
        release_manager = None
