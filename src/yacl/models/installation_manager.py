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

        self._subscribe_to_events()

        self.reload_installed_games()

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
                # Try to find existing installation
                settings = get_settings()
                active_install = settings.read(f"active_install_{game_type.name}", "")
                
                if active_install:
                    return self.installed_games[game_type][active_install].install_path
            
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
            settings = get_settings()
            active_install = settings.read(f"active_install_{game_type.name}", "")
            was_active = (active_install == install_name)

            # Remove the installation
            self.logger.info(f"Removing installation: {install_path}")
            shutil.rmtree(install_path)
            self.logger.info(f"Removed installation: {install_name}")

            # reload installed games
            self.reload_installed_games()

            # Handle active installation management
            new_active = None
            if was_active:
                if (game_type in self.installed_games and self.installed_games[game_type]):
                    # Set the first remaining installation as active
                    new_active = list(self.installed_games[game_type].keys())[0]
                    settings.store(f"active_install_{game_type.name}", new_active)
                else:
                    # No installations left, clear active
                    settings.store(f"active_install_{game_type.name}", "")

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
