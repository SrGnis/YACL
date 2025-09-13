"""
Game Installation Manager for YACL

This module provides the InstallationManager class for comprehensive game installation
management including installation coordination, directory management, archive extraction
coordination, installation metadata management, multi-installation support, and
installation status tracking.
"""

import logging
import json
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, Callable, List
from pathlib import Path

from yacl.services.paths import get_paths
from yacl.services.settings import get_settings
from yacl.services.downloader import get_download_manager
from yacl.utils.file_ops import FileOperations
from yacl.utils.helpers import load_json_file
from yacl.models.release import GameRelease, ReleaseAsset
from yacl.models.game_type import GameType
from yacl.services.events import EventManager, Events
from yacl.models.installation import InstallationStatus, InstallationError, GameInstallation, InstallationContext, INFO_FILENAME


class InstallationManager:
    """
    Game installation manager for YACL.
    
    This class handles:
    - Game installation coordination
    - Directory management and creation
    - Archive extraction coordination
    - Installation metadata management
    - Multi-installation support
    - Installation status tracking
    """
    
    def __init__(self, event_manager: EventManager):
        """Initialize the installation manager."""
        self.logger = logging.getLogger("YACL")
        self.file_ops = FileOperations()
        self.event_manager = event_manager

        self.installed_games: Dict[GameType, Dict[str, GameInstallation]] = {}

        # Track pending installation flows
        self.pending_installations: Dict[str, InstallationContext] = {}

        # Shutdown flag to signal threads to stop
        self.is_shutting_down = False

        # Current game type state
        self.current_game_type: GameType = GameType.all[0]

        # Cache for active installations (GameType -> installation_name)
        self.active_installations: Dict[GameType, str] = {}

        self._subscribe_to_events()

        # Initialize game type from settings
        self._initialize_game_type_from_settings()

        # Initialize active installations cache from settings
        self._initialize_active_installations_from_settings()

        self.reload_installed_games()

    def _initialize_game_type_from_settings(self):
        """Initialize the current game type from settings."""
        try:
            settings = get_settings()
            game_setting = settings.read("game", GameType.all[0].name)
            self.current_game_type = GameType.get_game_type_by_name(game_setting)
            self.logger.debug(f"Initialized game type from settings: {self.current_game_type.name}")

        except Exception as e:
            self.logger.error(f"Error initializing game type from settings: {e}")
            self.current_game_type = GameType.all[0]

    def _initialize_active_installations_from_settings(self):
        """Initialize the active installations cache from settings."""
        try:
            settings = get_settings()

            # Load active installation for each game type
            for game_type in GameType.all:
                active_install = settings.read(f"active_install_{game_type.name}", "")
                if active_install:
                    self.active_installations[game_type] = active_install

            self.logger.debug(f"Initialized active installations cache: {len(self.active_installations)} entries")

        except Exception as e:
            self.logger.error(f"Error initializing active installations from settings: {e}")
            self.active_installations = {}

    def _persist_active_installations_to_settings(self):
        """Persist the active installations cache to settings."""
        try:
            settings = get_settings()

            # Save active installation for each game type
            for game_type in GameType.all:
                if game_type in self.active_installations:
                    settings.store(f"active_install_{game_type.name}", self.active_installations[game_type])
                else:
                    settings.store(f"active_install_{game_type.name}", "")

            self.logger.debug(f"Persisted active installations cache: {len(self.active_installations)} entries")

        except Exception as e:
            self.logger.error(f"Error persisting active installations to settings: {e}")

    def get_current_game_type(self) -> GameType:
        """
        Get the currently selected game type.

        Returns:
            GameType: The current game type
        """
        return self.current_game_type

    def set_current_game_type(self, game_type: GameType) -> bool:
        """
        Set the current game type and emit change event.

        Args:
            game_type: The game type to set as current

        Returns:
            bool: True if successfully set
        """
        try:
            if game_type == self.current_game_type:
                return True  # No change needed

            old_game_type = self.current_game_type
            self.current_game_type = game_type

            # Update settings
            try:
                settings = get_settings()
                settings.store("game", self.current_game_type.name)
            except RuntimeError:
                # Settings not initialized, skip
                self.logger.debug("Settings not initialized, skipping game type storage")
                pass

            # Emit game type changed event
            if self.event_manager:
                self.event_manager.emit(Events.CURRENT_GAME_TYPE_CHANGED,
                                      old_game_type=old_game_type,
                                      new_game_type=self.current_game_type)

            self.logger.info(f"Game type changed from {old_game_type.name} to {self.current_game_type.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error setting current game type: {e}")
            return False

    def get_active_installation(self, game_type: Optional[GameType] = None) -> Optional[GameInstallation]:
        """
        Get the currently active installation for a game type.

        Args:
            game_type: Game type to get active installation for. If None, uses current game type.

        Returns:
            GameInstallation: Active installation object or None if none set
        """
        try:
            if game_type is None:
                game_type = self.current_game_type

            # Use cached value instead of reading from settings
            active_install_name = self.active_installations.get(game_type)

            # Validate that the active installation still exists
            if active_install_name and game_type in self.installed_games:
                if active_install_name in self.installed_games[game_type]:
                    return self.installed_games[game_type][active_install_name]
                else:
                    # Active installation no longer exists, clear it
                    self.logger.warning(f"Active installation '{active_install_name}' no longer exists for {game_type.name}, clearing")
                    self.clear_active_installation(game_type)

            return None

        except Exception as e:
            self.logger.error(f"Error getting active installation for {game_type.name if game_type else 'current'}: {e}")
            return None

    def get_active_installation_name(self, game_type: Optional[GameType] = None) -> Optional[str]:
        """
        Get the name of the currently active installation for a game type.

        Args:
            game_type: Game type to get active installation for. If None, uses current game type.

        Returns:
            str: Name of active installation or None if none set
        """
        active_installation = self.get_active_installation(game_type)
        return active_installation.name if active_installation else None

    def set_active_installation(self, installation: GameInstallation, game_type: Optional[GameType] = None) -> bool:
        """
        Set the active installation for a game type.

        Args:
            installation: GameInstallation object to make active
            game_type: Game type to set active installation for. If None, uses installation's game type.

        Returns:
            bool: True if successfully set
        """
        try:
            if game_type is None:
                game_type = installation.game_type

            # Verify the installation exists
            if game_type not in self.installed_games or installation.name not in self.installed_games[game_type]:
                self.logger.warning(f"Installation '{installation.name}' not found for {game_type.name}")
                return False

            # Get current active installation for event
            old_active = self.get_active_installation(game_type)

            # Update cache instead of directly writing to settings
            self.active_installations[game_type] = installation.name

            # Emit active installation changed event
            if self.event_manager:
                self.event_manager.emit(Events.ACTIVE_INSTALLATION_CHANGED,
                                      game_type=game_type,
                                      old_active=old_active,
                                      new_active=installation,
                                      reason="user_selection")

            self.logger.info(f"Set active installation for {game_type.name}: {installation.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error setting active installation: {e}")
            return False

    def set_active_installation_by_name(self, installation_name: str, game_type: Optional[GameType] = None) -> bool:
        """
        Set the active installation for a game type by name (backward compatibility).

        Args:
            installation_name: Name of the installation to make active
            game_type: Game type to set active installation for. If None, uses current game type.

        Returns:
            bool: True if successfully set
        """
        try:
            if game_type is None:
                game_type = self.current_game_type

            # Find the installation object
            if game_type not in self.installed_games or installation_name not in self.installed_games[game_type]:
                self.logger.warning(f"Installation '{installation_name}' not found for {game_type.name}")
                return False

            installation = self.installed_games[game_type][installation_name]
            return self.set_active_installation(installation, game_type)

        except Exception as e:
            self.logger.error(f"Error setting active installation by name: {e}")
            return False

    def get_active_installation_info(self, game_type: Optional[GameType] = None) -> Optional[GameInstallation]:
        """
        Get the full GameInstallation object for the active installation.

        Args:
            game_type: Game type to get active installation for. If None, uses current game type.

        Returns:
            GameInstallation: The active installation object or None if none set
        """
        try:
            if game_type is None:
                game_type = self.current_game_type

            # get_active_installation now returns GameInstallation object directly
            return self.get_active_installation(game_type)

        except Exception as e:
            self.logger.error(f"Error getting active installation info: {e}")
            return None

    def clear_active_installation(self, game_type: Optional[GameType] = None) -> bool:
        """
        Clear the active installation for a game type.

        Args:
            game_type: Game type to clear active installation for. If None, uses current game type.

        Returns:
            bool: True if successfully cleared
        """
        try:
            if game_type is None:
                game_type = self.current_game_type

            # Get current active installation for event
            old_active = self.get_active_installation(game_type)

            # Clear from cache
            if game_type in self.active_installations:
                del self.active_installations[game_type]

            # Emit active installation changed event
            if self.event_manager and old_active:
                self.event_manager.emit(Events.ACTIVE_INSTALLATION_CHANGED,
                                      game_type=game_type,
                                      old_active=old_active,
                                      new_active=None,
                                      reason="cleared")

            self.logger.info(f"Cleared active installation for {game_type.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error clearing active installation: {e}")
            return False

    def auto_set_active_installation(self, game_type: Optional[GameType] = None, prefer_name: Optional[str] = None) -> Optional[str]:
        """
        Automatically set an active installation using smart selection logic.

        Args:
            game_type: Game type to set active installation for. If None, uses current game type.
            prefer_name: Preferred installation name to select if available

        Returns:
            str: Name of the newly active installation or None if no installations available
        """
        try:
            if game_type is None:
                game_type = self.current_game_type

            if game_type not in self.installed_games or not self.installed_games[game_type]:
                # No installations available
                self.clear_active_installation(game_type)
                return None

            installations = self.installed_games[game_type]

            # Try preferred name first
            if prefer_name and prefer_name in installations:
                installation = installations[prefer_name]
                if self.set_active_installation(installation, game_type):
                    return prefer_name

            # Fall back to first available installation
            first_installation_name = list(installations.keys())[0]
            first_installation = installations[first_installation_name]
            if self.set_active_installation(first_installation, game_type):
                return first_installation_name

            return None

        except Exception as e:
            self.logger.error(f"Error auto-setting active installation: {e}")
            return None

    def _subscribe_to_events(self):
        """Subscribe to events to handle installation flow continuation."""
        try:
                self.event_manager.subscribe(Events.DOWNLOAD_FINISHED, self._on_download_finished) 
                self.logger.debug("Subscribed to events")
        except Exception as e:
            self.logger.error(f"Error subscribing to events: {e}")

    def _unsubscribe_from_events(self):
        """Unsubscribe from events."""
        try:
                self.event_manager.unsubscribe(Events.DOWNLOAD_FINISHED, self._on_download_finished) 
                self.logger.debug("Unsubscribed from events")
        except Exception as e:
            self.logger.error(f"Error unsubscribing from events: {e}")

    def reload_installed_games(self):
        """
        Reload installed games from disk.
        """
        self.installed_games = self._load_installed_games()

    def _load_installed_games(self) -> Dict[GameType, Dict[str, GameInstallation]]:
        """
        Load installed games from disk.

        This method scans the games directory for installed games and loads their metadata.
        
        Returns:
            dict: Dictionary mapping game types to their installations
        """
        try:
            installed_games = {}
            paths = get_paths()
            base_path = paths.games_dir

            for game in GameType.all:
                game_dir = base_path / game.name
                
                if not game_dir.exists():
                    continue
                
                for subdir in game_dir.iterdir():
                    if not subdir.is_dir():
                        continue
                    
                    info_file = subdir / INFO_FILENAME
                    if info_file.exists():
                        install = GameInstallation.load(info_file)
                        if install:
                            installed_games.setdefault(game, {})[install.name] = install
                
        except Exception:
            return {}
            
        return installed_games

    def start_complete_installation_flow(self, release: GameRelease, selected_asset: ReleaseAsset, update_existing: bool = False) -> bool:
        """
        Start the complete installation flow with event-driven communication.

        This method starts the download and stores the installation context.
        The rest of the flow (validation → installation) is handled by event handlers
        when the download completes.

        Args:
            release: The game release being installed
            selected_asset: The selected asset to download and install
            update_existing: Whether to update an existing installation

        Returns:
            bool: True if the flow was started successfully
        """
        try:
            if not self.event_manager:
                self.logger.error("Event manager not available for installation flow")
                return False

            self.logger.info(f"Starting complete installation flow for: {selected_asset.name}")

            # Create a unique context ID for this installation
            import uuid
            context_id = str(uuid.uuid4())

            # Store the installation context for when download completes
            self.pending_installations[context_id] = InstallationContext(
                release=release,
                asset=selected_asset,
                update_existing=update_existing,
                context_id=context_id
            )

            # Start the download - the rest of the flow will be handled by _on_download_finished
            self._start_download(release, selected_asset)

            return True

        except Exception as e:
            error_msg = f"Failed to start installation flow: {e}"
            self.logger.error(error_msg)
            if self.event_manager:
                self._emit_installation_failed(release, error_msg)
            return False

    def _start_download(self, release: GameRelease, selected_asset: ReleaseAsset):
        """
        Start downloading an asset.

        The download will complete asynchronously and trigger DOWNLOAD_FINISHED event.

        Args:
            release: The game release being installed
            selected_asset: The selected asset to download
        """
        try:
            # Get paths manager
            paths = get_paths()
            download_dir = str(paths.temp_dir)

            # Get download manager
            download_manager = get_download_manager()

            # Start the download
            download_manager.download_file(
                url=selected_asset.download_url,
                target_dir=download_dir,
                target_filename=selected_asset.name
            )

        except Exception as e:
            error_msg = f"Error starting download: {e}"
            self.logger.error(error_msg)

    def _on_download_finished(self, sender, **kwargs):
        """
        Handle download finished event and continue installation flow.

        Args:
            sender: Event sender
            **kwargs: Event data including filename, success, file_path
        """
        try:
            filename = kwargs.get('filename', '')
            success = kwargs.get('success', False)
            file_path = kwargs.get('file_path')

            # Find the pending installation for this file
            installation_context = None
            for context_id, context in self.pending_installations.items():
                if context.asset.name == filename:
                    installation_context = context
                    break

            if not installation_context:
                # This download is not part of our installation flow
                return

            if not success or not file_path:
                # Download failed
                error_msg = f"Download failed for {filename}"
                self.logger.error(error_msg)
                self._emit_installation_failed(installation_context.release, error_msg)
                # Clean up pending installation
                if installation_context.context_id in self.pending_installations:
                    del self.pending_installations[installation_context.context_id]
                return

            self.logger.info(f"Download completed for {filename}, continuing with installation")

            # Update installation context with download file path
            installation_context.donwload_file_path = file_path

            # Continue with installation in a background thread
            import threading

            def continue_installation():
                try:
                    if self.is_shutting_down:
                        self.logger.info("Installation cancelled due to shutdown")
                        return

                    installation_context.install_path = self._determine_installation_directory(
                        installation_context.release.game_type, installation_context.update_existing
                    )

                    # Install the game
                    success = self.install_game(
                        installation_context
                    )

                    if success:
                        self.event_manager.emit(Events.INSTALLATION_FINISHED,
                                            release=installation_context.release,
                                            success=True,
                                            installation_path=installation_context.install_path,
                                            error_message=None)
                    else:
                        self._emit_installation_failed(installation_context.release, f"Installation failed: {installation_context.release.name}")

                except Exception as e:
                    error_msg = f"Installation continuation failed: {e}"
                    self.logger.error(error_msg)
                    self._emit_installation_failed(installation_context.release, error_msg)
                finally:
                    # Clean up pending installation
                    if installation_context.context_id in self.pending_installations:
                        del self.pending_installations[installation_context.context_id]

            # Start continuation in background thread
            thread = threading.Thread(target=continue_installation, daemon=True)
            thread.start()

        except Exception as e:
            self.logger.error(f"Error handling download finished event: {e}")

    

    def install_game(self, installation_context: InstallationContext) -> bool:
        """
        Install a game from a downloaded archive.
        
        Args:
            installation_context: Installation context
            
        Returns:
            bool: True if installation was successful
        """
        try:
            # Check if shutting down before starting
            if self.is_shutting_down:
                self.logger.info("Installation cancelled due to shutdown")
                return False

            if installation_context.release.game_type == GameType.other:
                raise InstallationError("Release game type is required")

            self.logger.info(f"Starting installation: {installation_context.context_id}")
            
            # Update status
            self._update_installation_status(installation_context.context_id, InstallationStatus.EXTRACTING)
            self.logger.info(f"Installing {installation_context.release.name}...")
            
            # Extract the archive
            success = self._extract_and_install(installation_context)
            
            if success:
                # Create installation metadata
                self._create_installation_metadata(installation_context)
                
                # Update installation status
                self._update_installation_status(installation_context.context_id, InstallationStatus.COMPLETED)
                self.logger.info(f"Installation completed: {installation_context.release.name}")
                
                # Clean up archive if configured
                self._cleanup_archive(installation_context.donwload_file_path)
                
                return True
            else:
                self._update_installation_status(installation_context.context_id, InstallationStatus.FAILED)
                self.logger.error(f"Installation failed: {installation_context.release.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Installation failed: {e}")
            if installation_context.context_id in self.pending_installations:
                self._update_installation_status(installation_context.context_id, InstallationStatus.FAILED)
            self.logger.error(f"Installation error: {e}")
            raise InstallationError(f"Installation failed: {e}")
        finally:
            # Clean up tracking
            if installation_context.context_id in self.pending_installations:
                del self.pending_installations[installation_context.context_id]

    def _create_installation_metadata(self, installation_context: InstallationContext):
        """
        Create installation metadata file.

        Args:
            installation_context: Installation context
        """
        try:
            # Create installation metadata
            install_metadata = GameInstallation(
                name = installation_context.release.name,
                version = installation_context.release.tag_name or "",
                game_type = installation_context.release.game_type,
                channel = installation_context.release.channel,
                asset_name = installation_context.asset.name,
                asset_size = installation_context.asset.size,
                download_url = installation_context.asset.download_url,
                release_id = str(installation_context.release.id),
                release_published_at = str(installation_context.release.published_at),
                release_body = installation_context.release.body or "",
                installation_size = installation_context.asset.size,
                install_path = installation_context.install_path
            )
            
            # Save metadata
            install_metadata.save(Path(installation_context.install_path) / INFO_FILENAME)

            # Add to installed games
            self.installed_games.setdefault(installation_context.release.game_type, {})[install_metadata.name] = install_metadata
            
        except Exception as e:
            self.logger.error(f"Failed to create installation metadata: {e}")
            raise InstallationError(f"Failed to create installation metadata: {e}")
    
    def _determine_installation_directory(self, game_type: GameType, update_existing: bool) -> str:
        """
        Determine the appropriate installation directory.
        
        Args:
            game_type: Type of game being installed
            update_existing: Whether to update an existing installation
            
        Returns:
            str: Path to the installation directory
        """
        try:
            paths = get_paths()
            
            if update_existing:
                # Try to find existing installation using centralized method
                active_install_info = self.get_active_installation_info(game_type)

                if active_install_info:
                    return active_install_info.install_path
            
            # Create new installation directory
            game_dir = paths.games_dir / game_type.name
            game_dir.mkdir(parents=True, exist_ok=True)
            dir_number = 0
            while True:
                install_dir = game_dir / f"game{dir_number}"
                if not install_dir.exists():
                    return str(install_dir)
                dir_number += 1
                
            
        except Exception as e:
            self.logger.error(f"Failed to determine installation directory: {e}", exc_info=True)
            raise InstallationError(f"Failed to determine installation directory: {e}")
    
    def _extract_and_install(self, installation_context: InstallationContext) -> bool:
        """
        Extract archive and install to target directory.
        
        Args:
            installation_context: Installation context
            
        Returns:
            bool: True if extraction and installation was successful
        """
        try:
            # Check if shutting down before starting extraction
            if self.is_shutting_down:
                self.logger.info("Extraction cancelled due to shutdown")
                return False

            paths = get_paths()
            temp_extract_dir = paths.temp_dir / "extract" / installation_context.context_id

            # Ensure temp directory exists
            temp_extract_dir.mkdir(parents=True, exist_ok=True)

            # Extract archive to temp directory
            self.logger.info(f"Extracting {installation_context.donwload_file_path} to {temp_extract_dir}")

            def extract_progress(progress: float, message: str):
                # Check shutdown flag during progress updates
                if self.is_shutting_down:
                    return
                self._update_installation_progress(installation_context.context_id, progress * 0.7, message)

            success = self.file_ops.extract_archive(
                str(installation_context.donwload_file_path), str(temp_extract_dir), extract_progress
            )
            
            if not success or self.is_shutting_down:
                return False

            # Find the extracted root directory
            extracted_root = self.file_ops.get_extracted_root_dir(str(temp_extract_dir))
            if not extracted_root:
                self.logger.error("Could not determine extracted root directory")
                return False

            # Check again before moving files
            if self.is_shutting_down:
                self.logger.info("Installation cancelled during file move due to shutdown")
                return False

            # Move extracted content to final installation directory
            self._update_installation_status(installation_context.context_id, InstallationStatus.INSTALLING)

            def move_progress(progress: float, message: str):
                # Check shutdown flag during progress updates
                if self.is_shutting_down:
                    return
                final_progress = 70 + (progress * 0.3)
                self._update_installation_progress(installation_context.context_id, final_progress, message)
            
            success = self._move_to_final_location(extracted_root, installation_context.install_path, move_progress)
            
            # Clean up temp directory
            try:
                shutil.rmtree(temp_extract_dir)
            except Exception as e:
                self.logger.warning(f"Failed to clean up temp directory: {e}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Extraction and installation failed: {e}")
            return False
    
    def _move_to_final_location(self, source_dir: str, target_dir: str,
                            progress_callback: Optional[Callable] = None) -> bool:
        """
        Move extracted content to final installation location.

        Moves and renames the source directory to the target directory.

        Args:
            source_dir: Source directory with extracted content
            target_dir: Target installation directory
            progress_callback: Optional progress callback

        Returns:
            bool: True if move was successful
        """
        try:
            source_path = Path(source_dir)
            target_path = Path(target_dir)

            # Ensure parent directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # If target exists and we're updating, remove old content
            if target_path.exists():
                self.logger.info(f"Removing existing installation: {target_path}")
                shutil.rmtree(target_path)

            if progress_callback:
                progress_callback(50, "Moving installation directory...")

            # Simply move/rename the source directory to target directory
            self.logger.info(f"Moving {source_path} to {target_path}")
            shutil.move(str(source_path), str(target_path))

            if progress_callback:
                progress_callback(100, "Installation files moved successfully")

            self.logger.info(f"Successfully moved installation to {target_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to move to final location: {e}")
            return False

    def _cleanup_archive(self, archive_path: str):
        """
        Clean up downloaded archive.

        Args:
            archive_path: Path to the archive file
        """
        try:
            archive_file = Path(archive_path)
            if archive_file.exists():
                archive_file.unlink()
                self.logger.info(f"Cleaned up archive: {archive_path}")

        except Exception as e:
            self.logger.warning(f"Failed to cleanup archive: {e}")

    def _update_installation_status(self, context_id: str, installation_status: InstallationStatus):
        """Update installation status on the context."""
        if context_id in self.pending_installations:
            self.pending_installations[context_id].status = installation_status
            self.logger.debug(f"Installation {context_id} status: {installation_status.value}")

    def _update_installation_progress(self, context_id: str, progress: float, message: str):
        """Update installation progress."""
        if context_id in self.pending_installations:
            self.pending_installations[context_id].progress = progress
            self.logger.debug(f"Installation {context_id} progress: {progress:.1f}% - {message}")
            if self.event_manager:
                self.event_manager.emit(Events.INSTALLATION_PROGRESS,
                                        installation_id=context_id,
                                        progress=progress,
                                        message=message)

    def cancel_installation(self, context_id: str) -> bool:
        """
        Cancel an ongoing installation.

        Args:
            context_id: Installation context identifier

        Returns:
            bool: True if cancellation was successful
        """
        try:
            if context_id in self.pending_installations:
                self._update_installation_status(context_id, InstallationStatus.CANCELLED)
                self.logger.info(f"Cancelled installation: {context_id}")
                return True
            return False

        except Exception as e:
            self.logger.error(f"Failed to cancel installation: {e}")
            return False

    def remove_installation(self, game_type: GameType, install_name: str) -> Dict[str, Any]:
        """
        Remove an existing game installation and handle active installation management.

        Args:
            game_type: Type of game
            install_name: Name of the installation to remove

        Returns:
            dict: Contains removal results
                - success: bool indicating if removal was successful
                - was_active: bool indicating if this was the active installation
                - new_active: str name of new active installation (if any)
                - error_message: str error message (if failed)
        """
        try:
            install_path = Path(self.installed_games[game_type][install_name].install_path)

            if not install_path.exists():
                error_msg = f"Installation path not found: {install_path}"
                self.logger.warning(error_msg)
                return {
                    "success": False,
                    "was_active": False,
                    "new_active": None,
                    "error_message": error_msg
                }

            # Check if this is the active installation
            active_install = self.get_active_installation(game_type)
            was_active = (active_install == install_name)

            # Remove the installation
            self.logger.info(f"Removing installation: {install_path}")
            shutil.rmtree(install_path)
            self.logger.info(f"Removed installation: {install_name}")

            # reload installed games
            self.reload_installed_games()

            # Handle active installation management using centralized methods
            new_active = None
            if was_active:
                # Use auto-selection to set new active installation
                new_active = self.auto_set_active_installation(game_type)

            return {
                "success": True,
                "was_active": was_active,
                "new_active": new_active,
                "error_message": None
            }

        except Exception as e:
            error_msg = f"Failed to remove installation: {e}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "was_active": False,
                "new_active": None,
                "error_message": error_msg
            }
            

    def _emit_installation_failed(self, release: GameRelease, error_message: str):
        """
        Emit installation failed event.

        Args:
            release: The release that failed to install
            error_message: Error message
        """
        try:
            if self.event_manager:
                self.event_manager.emit(Events.INSTALLATION_FINISHED,
                                    release=release,
                                    success=False,
                                    installation_path=None,
                                    error_message=error_message)

            self.logger.error(f"Installation failed for {release.name}: {error_message}")

        except Exception as e:
            self.logger.error(f"Error emitting installation failed event: {e}")

    def shutdown(self):
        """Shutdown the installation manager."""
        try:
            self.logger.info("Shutting down installation manager...")

            self.is_shutting_down = True

            # Persist cached data to settings before shutdown
            self._persist_active_installations_to_settings()

            self._unsubscribe_from_events()

            for context_id in list(self.pending_installations.keys()):
                self.cancel_installation(context_id)

            self.pending_installations.clear()

            self.file_ops.shutdown()

            self.logger.info("Installation manager shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during installation manager shutdown: {e}")


# Global installation manager instance
_installation_manager: Optional[InstallationManager] = None


def initialize_installation_manager(event_manager: EventManager) -> bool:
    """
    Initialize the global installation manager.

    Args:
        event_manager: Event manager for UI communication

    Returns:
        bool: True if initialization was successful
    """
    global _installation_manager
    try:
        _installation_manager = InstallationManager(event_manager)
        return True
    except Exception as e:
        logging.getLogger("YACL").error(f"Failed to initialize global installation manager: {e}")
        return False


def get_installation_manager() -> InstallationManager:
    """
    Get the global installation manager instance.

    Returns:
        InstallationManager: The installation manager instance

    Raises:
        RuntimeError: If installation manager is not initialized
    """
    if _installation_manager is None:
        raise RuntimeError("Installation manager not initialized")

    return _installation_manager


def shutdown_installation_manager():
    """Shutdown the global installation manager."""
    global _installation_manager

    if _installation_manager is not None:
        _installation_manager.shutdown()
        _installation_manager = None
