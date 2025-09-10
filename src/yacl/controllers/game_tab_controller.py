"""
Game Tab Controller for YACL

This module provides the GameTabController class that handles all business logic,
event management, and manager interactions for the game tab, following MVC pattern.
"""

import logging
import tkinter as tk
import tkinter.messagebox as messagebox
import platform
import subprocess
import json
import os
from pathlib import Path
from typing import Optional, List, Dict

from yacl.services.events import EventManager, Events
from yacl.views.tabs.game_tab import GameTab
from yacl.views.dialogs.asset_install_selection_dialog import AssetInstallSelectionDialog
from yacl.views.dialogs.download_progress_dialog import InstallationProgressDialog
from yacl.services.settings import get_settings
from yacl.services.paths import get_paths
from yacl.models.game_type import GameType
from yacl.models.release_manager import get_release_manager
from yacl.models.release import ReleaseChannel, GameRelease, ReleaseAsset
from yacl.models.installation_manager import get_installation_manager
from yacl.models.installation import GameInstallation
from yacl.utils.release_search import ReleaseSearchIndex


class GameTabController:
    """
    Controller for the game tab that handles all business logic and event management.
    
    This controller:
    - Manages game selection and release channel logic
    - Handles release fetching and installation processes
    - Coordinates with managers (ReleaseManager, InstallationManager)
    - Manages installation lifecycle and active installation state
    - Handles all user input events and business logic
    """
    
    def __init__(self, view: GameTab, event_manager: EventManager):
        """
        Initialize the game tab controller.
        
        Args:
            view: The GameTab view instance
            event_manager: Event manager for component communication
        """
        self.logger = logging.getLogger("YACL")
        self.view = view
        self.event_manager = event_manager
        
        # State variables
        self.current_channel = ReleaseChannel.STABLE
        self.current_releases: List[GameRelease] = []
        self.filtered_releases: List[GameRelease] = []  # Releases after search filtering
        self.selected_release_index = -1

        # Search functionality
        self.search_index = ReleaseSearchIndex()
        self.current_search_query = ""

        # Track current modal for proper cleanup
        self.current_modal: Optional[tk.Toplevel] = None

        # Initialize channel from settings
        self._initialize_channel_from_settings()

        # Initialize update current when installing
        self._initialize_update_current_when_installing()

        # Subscribe to events
        self._subscribe_to_events()

        # Setup event handlers
        self._setup_event_handlers()

        self.logger.info("Game tab controller initialized")

    def _initialize_channel_from_settings(self):
        """Initialize the current channel from settings."""
        try:
            settings = get_settings()
            channel_setting = settings.read("channel", "stable")

            self.current_channel = ReleaseChannel.from_string(channel_setting)

        except RuntimeError:
            # Settings not initialized, use default
            self.logger.debug("Settings not initialized, using default channel")
            self.current_channel = ReleaseChannel.STABLE
        except Exception as e:
            self.logger.error(f"Error initializing channel from settings: {e}")
            self.current_channel = ReleaseChannel.STABLE

    def _initialize_update_current_when_installing(self):
        """Initialize the update current when installing setting."""
        try:
            settings = get_settings()
            update_current = settings.read("update_current_when_installing", True)
            self.view.update_var.set(update_current)
        except Exception as e:
            self.logger.error(f"Error initializing update current when installing: {e}")

    def _setup_event_handlers(self):
        """Setup event handlers by directly binding to view widgets."""
        # Direct widget binding - much simpler than callback setters
        
        self.view.game_selector.bind("<<ComboboxSelected>>", self._on_game_selected)

        self.view.channel_stable_radio.configure(command=self._on_channel_changed)

        self.view.channel_experimental_radio.configure(command=self._on_channel_changed)

        self.view.refresh_button.configure(command=self._on_refresh_releases)

        # Search event handlers
        self.view.search_var.trace_add("write", self._on_search_changed)
        self.view.clear_search_button.configure(command=self._on_clear_search)

        self.view.releases_listbox.bind("<<ListboxSelect>>", self._on_release_selected)

        self.view.install_button.configure(command=self._on_install_release)

        self.view.play_button.configure(command=self._on_launch_game)

        self.view.resume_button.configure(command=self._on_resume_game)

        self.view.installations_listbox.bind("<<ListboxSelect>>", self._on_installation_selected)

        self.view.activate_button.configure(command=self._on_activate_installation)

        self.view.delete_button.configure(command=self._on_delete_installation)

        self.view.refresh_installations_button.configure(command=self._on_refresh_installations)

    def _subscribe_to_events(self):
        """Subscribe to events."""
        try:
            self.event_manager.subscribe(Events.INSTALLATION_STARTED, self._on_installation_started)
            self.event_manager.subscribe(Events.INSTALLATION_FINISHED, self._on_installation_finished)
            self.event_manager.subscribe(Events.CURRENT_GAME_TYPE_CHANGED, self._on_current_game_type_changed)
            self.event_manager.subscribe(Events.ACTIVE_INSTALLATION_CHANGED, self._on_active_installation_changed)

            self.logger.debug("Subscribed to events")

        except Exception as e:
            self.logger.error(f"Error subscribing to events: {e}")

    def _unsubscribe_from_events(self):
        """Unsubscribe from events."""
        try:
            self.event_manager.unsubscribe(Events.INSTALLATION_STARTED, self._on_installation_started)
            self.event_manager.unsubscribe(Events.INSTALLATION_FINISHED, self._on_installation_finished)
            self.event_manager.unsubscribe(Events.CURRENT_GAME_TYPE_CHANGED, self._on_current_game_type_changed)
            self.event_manager.unsubscribe(Events.ACTIVE_INSTALLATION_CHANGED, self._on_active_installation_changed)

            self.logger.debug("Unsubscribed from events")

        except Exception as e:
            self.logger.error(f"Error unsubscribing from events: {e}")

    def refresh_ui(self):
        """Refresh the UI state."""
        try:
            # Update game selector with current game type
            installation_manager = get_installation_manager()
            current_game_type = installation_manager.get_current_game_type()
            self.view.game_selector.set(current_game_type.display_name)

            self._update_channel_ui()

            self._refresh_releases()

            self._refresh_active_install_ui()
            self._refresh_installations_list()

        except Exception as e:
            self.logger.error(f"Error refreshing UI: {e}")

    def _update_channel_ui(self):
        """Update the channel radio buttons to match current state."""
        try:
            self.view.channel_var.set(self.current_channel.display_name())

        except Exception as e:
            self.logger.error(f"Error updating channel UI: {e}")

    def _on_game_selected(self, event=None):
        """Handle game selection change."""
        try:
            selected_game = self.view.get_selected_game()
            if selected_game:
                game_type = GameType.get_game_type_by_display_name(selected_game)
                installation_manager = get_installation_manager()
                current_game_type = installation_manager.get_current_game_type()

                if game_type != current_game_type:
                    # Use InstallationManager to set the new game type
                    installation_manager.set_current_game_type(game_type)
                    # UI refresh will be handled by the event handler

        except Exception as e:
            self.logger.error(f"Error handling game selection: {e}")

    def _on_channel_changed(self):
        """Handle release channel change."""
        try:
            selected_channel = self.view.get_selected_channel()
            if not selected_channel:
                return

            self.logger.debug(f"Channel selection changed to: {selected_channel}")

            # Map UI selection to ReleaseChannel enum
            self.current_channel = ReleaseChannel.from_string(selected_channel)

            # Update settings
            try:
                settings = get_settings()
                settings.store("channel", self.current_channel.value)
            except RuntimeError:
                # Settings not initialized, skip
                self.logger.debug("Settings not initialized, skipping channel storage")
                pass

            # Refresh UI to load releases for new channel
            self.refresh_ui()

            self.logger.info(f"Channel changed to: {self.current_channel.value}")

        except Exception as e:
            self.logger.error(f"Error handling channel change: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _on_refresh_releases(self):
        """Handle refresh releases button click. This will force a fetch from the API."""
        try:
            self._refresh_releases(force_fetch=True)
        except Exception as e:
            self.logger.error(f"Error refreshing releases: {e}")

    def _on_search_changed(self, *args):
        """Handle search text changes."""
        try:
            search_query = self.view.get_search_text()
            if search_query != self.current_search_query:
                self.current_search_query = search_query
                self._apply_search_filter()
        except Exception as e:
            self.logger.error(f"Error handling search change: {e}")

    def _on_clear_search(self):
        """Handle clear search button click."""
        try:
            self.view.clear_search()
            self.current_search_query = ""
            self._apply_search_filter()
        except Exception as e:
            self.logger.error(f"Error clearing search: {e}")

    def _on_release_selected(self, event=None):
        """Handle release selection."""
        try:
            selection_index = self.view.get_selected_release_index()
            if selection_index is None:
                # No selection
                self.selected_release_index = -1
            else:
                # Get the selected index (this is an index into filtered_releases)
                self.selected_release_index = selection_index

            # Enable/disable install button based on selection
            is_valid_selection = (
                self.selected_release_index >= 0 and
                self.selected_release_index < len(self.filtered_releases)
            )

            self.view.install_button.config(state=tk.NORMAL if is_valid_selection else tk.DISABLED)

            if is_valid_selection:
                selected_release = self.filtered_releases[self.selected_release_index]
                self.logger.debug(f"Selected release: {selected_release.name}")

        except Exception as e:
            self.logger.error(f"Error handling release selection: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _on_install_release(self):
        """Handle install release button click."""
        try:
            # Check if we have a valid release selected
            if (self.selected_release_index < 0 or
                self.selected_release_index >= len(self.filtered_releases)):
                self.logger.warning("No valid release selected for installation")
                return

            selected_release = self.filtered_releases[self.selected_release_index]
            self.logger.info(f"Starting installation process for: {selected_release.name}")

            # Show asset selection modal
            self._show_asset_selection_modal(selected_release)

        except Exception as e:
            self.logger.error(f"Error starting release installation: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _on_launch_game(self):
        """Handle launch game button click."""
        try:
            active_install = self.get_active_installation()
            if not active_install:
                self.logger.warning("No active installation to launch")
                return

            installations = self.get_current_installations()
            if active_install not in installations:
                self.logger.error(f"Active installation not found: {active_install}")
                return

            install_path = installations[active_install].install_path
            self.logger.info(f"Launching game from: {install_path}")

            # Launch the game without a specific world
            success = self._start_game(install_path)
            if success:
                self.logger.info(f"Launched {active_install}")
            else:
                self.logger.error(f"Failed to launch {active_install}")

        except Exception as e:
            self.logger.error(f"Error launching game: {e}")

    def _on_resume_game(self):
        """Handle resume game button click."""
        try:
            active_install = self.get_active_installation()
            if not active_install:
                self.logger.warning("No active installation to resume")
                return

            installations = self.get_current_installations()
            if active_install not in installations:
                self.logger.error(f"Active installation not found: {active_install}")
                return

            install_path = installations[active_install].install_path

            # Try to find the last world from lastworld.json
            world_name = self._get_last_world(install_path)
            if not world_name:
                self.logger.warning("No last world found, launching normally")
                success = self._start_game(install_path)
            else:
                self.logger.info(f"Resuming world: {world_name}")
                success = self._start_game(install_path, world_name)

            if success:
                if world_name:
                    self.logger.info(f"Resumed world '{world_name}' in {active_install}")
                else:
                    self.logger.info(f"Launched {active_install}")
            else:
                self.logger.error(f"Failed to resume game in {active_install}")

        except Exception as e:
            self.logger.error(f"Error resuming game: {e}")

    def _on_refresh_installations(self):
        """Handle refresh installations button click."""
        try:
            self._refresh_installations_ui()

        except Exception as e:
            self.logger.error(f"Error refreshing installations: {e}")

    def _on_installation_selected(self, event=None):
        """Handle installation selection."""
        try:
            selection_index = self.view.get_selected_installation_index()
            if selection_index is None:
                # No selection - disable buttons
                self.view.activate_button.config(state=tk.DISABLED)
                self.view.delete_button.config(state=tk.DISABLED)
                return

            # Get selected installation name
            installations = self.get_current_installations()
            installation_names = list(installations.keys())

            if selection_index < len(installation_names):
                selected_install = installation_names[selection_index]
                active_install = self.get_active_installation()

                # Enable/disable buttons based on selection
                # Disable activate button if this is already the active installation
                is_already_active = selected_install == active_install
                self.view.activate_button.config(state=tk.NORMAL if not is_already_active else tk.DISABLED)
                self.view.delete_button.config(state=tk.NORMAL)

                self.logger.debug(f"Selected installation: {selected_install}")

        except Exception as e:
            self.logger.error(f"Error handling installation selection: {e}")

    def _on_activate_installation(self):
        """Handle activate installation button click."""
        try:
            selection_index = self.view.get_selected_installation_index()
            if selection_index is None:
                return

            # Get selected installation name
            installations = self.get_current_installations()
            installation_names = list(installations.keys())

            if selection_index < len(installation_names):
                selected_install = installation_names[selection_index]

                if self.set_active_installation(selected_install):
                    # Refresh UI to reflect changes
                    self._refresh_installations_list()
                    self._on_installation_selected()

        except Exception as e:
            self.logger.error(f"Error activating installation: {e}")

    def _on_delete_installation(self):
        """Handle delete installation button click."""
        try:
            selection_index = self.view.get_selected_installation_index()
            if selection_index is None:
                return

            # Get selected installation name
            installations = self.get_current_installations()
            installation_names = list(installations.keys())

            if selection_index < len(installation_names):
                selected_install = installation_names[selection_index]

                # Confirm deletion
                if messagebox.askyesno(
                    "Confirm Deletion",
                    f"Are you sure you want to delete the installation '{selected_install}'?\n\nThis action cannot be undone."
                ):
                    if self.remove_installation(selected_install):
                        # Refresh installations list
                        self._refresh_installations_list()

        except Exception as e:
            self.logger.error(f"Error deleting installation: {e}")

    # Business logic methods
    def _refresh_releases(self, force_fetch=False):
        """Refresh the releases list from the release manager."""
        try:
            release_manager = get_release_manager()
            installation_manager = get_installation_manager()
            current_game_type = installation_manager.get_current_game_type()

            # Fetch releases for current game and channel
            self.current_releases = release_manager.get_releases(
                game_type=current_game_type,
                channel=self.current_channel,
                limit=None,
                force_refresh=force_fetch
            )

            # Update search index with new releases
            self.search_index.add_releases(self.current_releases)

            # Apply current search filter
            self._apply_search_filter()

        except RuntimeError as e:
            # Release manager not initialized
            self.logger.warning(f"Release manager not available: {e}")
            self.current_releases = []
            self.search_index.add_releases([])
            self._apply_search_filter()
        except Exception as e:
            self.logger.error(f"Error refreshing releases: {e}")
            self.current_releases = []
            self.search_index.add_releases([])
            self._apply_search_filter()

    def _apply_search_filter(self):
        """Apply search filter to current releases and update UI."""
        try:
            if not self.current_search_query:
                # No search query, show all releases
                self.filtered_releases = self.current_releases.copy()
            else:
                # Apply search filter
                self.filtered_releases = self.search_index.search(self.current_search_query)

            # Update the UI with filtered releases
            self._refresh_releases_list()

            self.logger.debug(f"Search filter applied: {len(self.filtered_releases)}/{len(self.current_releases)} releases shown")

        except Exception as e:
            self.logger.error(f"Error applying search filter: {e}")
            # Fallback to showing all releases
            self.filtered_releases = self.current_releases.copy()
            self._refresh_releases_list()

    def _refresh_releases_list(self):
        """Refresh the releases list UI with filtered releases."""
        try:
            # Clear current list and add release names from filtered releases
            release_names = [release.tag_name for release in self.filtered_releases]
            self.view.update_releases_list(release_names) # type: ignore

            # Reset selection
            self.selected_release_index = -1

            # Disable install button
            self.view.install_button.config(state=tk.DISABLED)

        except Exception as e:
            self.logger.error(f"Error refreshing releases list: {e}")

    def _refresh_installations_ui(self):
        """Refresh the installations UI to show new installations."""
        try:
            # Refresh the installations list UI
            self._refresh_installations_list()

            # Also refresh the active installation UI to ensure consistency
            self._refresh_active_install_ui()

            # Log current installations for debugging
            installation_manager = get_installation_manager()
            current_game_type = installation_manager.get_current_game_type()
            current_game = current_game_type.name
            installations = self.get_current_installations()

            if installations:
                self.logger.info(f"Current installations for {current_game}: {list(installations.keys())}")
            else:
                self.logger.info(f"No installations found for {current_game}")

        except Exception as e:
            self.logger.error(f"Error refreshing installations UI: {e}")

    def _refresh_installations_list(self):
        """Refresh the installations list UI."""
        try:
            # Get current installations
            installations = self.get_current_installations()
            self.logger.debug(f"Current installations: {installations}")
            active_install = self.get_active_installation()

            # Create display list with active indicator
            installation_display = []
            for install_name in installations.keys():
                display_text = install_name
                if install_name == active_install:
                    display_text += " (Active)"
                installation_display.append(display_text)

            # Update view
            self.view.update_installations_list(installation_display)

            # Reset button states
            self.view.activate_button.config(state=tk.DISABLED)
            self.view.delete_button.config(state=tk.DISABLED)

            self.logger.debug(f"Refreshed installations list: {len(installations)} installations")

        except Exception as e:
            self.logger.error(f"Error refreshing installations list: {e}")

    def _refresh_active_install_ui(self):
        """Refresh the active installation UI components."""
        try:
            active_install = self.get_active_installation()

            if active_install:
                # Update active installation display
                self.view.active_install_label.config(text=f"Active: {active_install}")

                # Enable play button
                self.view.play_button.config(state=tk.NORMAL)

                # Check if resume button should be enabled
                installations = self.get_current_installations()
                if active_install in installations:
                    install_path = installations[active_install].install_path
                    has_last_world = self._get_last_world(install_path) is not None
                    self.view.resume_button.config(state=tk.NORMAL if has_last_world else tk.DISABLED)
                else:
                    self.view.resume_button.config(state=tk.DISABLED)

                self.logger.debug(f"Updated active install UI: {active_install}")
            else:
                # No active installation
                self.view.active_install_label.config(text="No active installation")

                # Disable play and resume buttons
                self.view.play_button.config(state=tk.DISABLED)
                self.view.resume_button.config(state=tk.DISABLED)

        except Exception as e:
            self.logger.error(f"Error refreshing active install UI: {e}")

    def get_current_installations(self) -> Dict[str, GameInstallation]:
        """
        Get current installations for the selected game type.

        Returns:
            dict: Dictionary mapping installation names to GameInstallation objects
        """
        try:
            installation_manager = get_installation_manager()
            installation_manager.reload_installed_games()
            current_game_type = installation_manager.get_current_game_type()
            installations = installation_manager.installed_games.get(current_game_type, {})
            return installations

        except Exception as e:
            self.logger.error(f"Error getting current installations: {e}")
            return {}

    def get_active_installation(self) -> Optional[str]:
        """
        Get the currently active installation for the selected game.

        Returns:
            str: Name of active installation or None if none set
        """
        try:
            installation_manager = get_installation_manager()
            active_installation = installation_manager.get_active_installation()
            return active_installation.name if active_installation else None

        except Exception as e:
            self.logger.error(f"Error getting active installation: {e}")
            return None

    def set_active_installation(self, installation_name: str) -> bool:
        """
        Set the active installation for the current game.

        Args:
            installation_name: Name of the installation to make active

        Returns:
            bool: True if successfully set
        """
        try:
            installation_manager = get_installation_manager()
            return installation_manager.set_active_installation_by_name(installation_name)

        except Exception as e:
            self.logger.error(f"Error setting active installation: {e}")
            return False

    def remove_installation(self, installation_name: str) -> bool:
        """
        Remove an installation.

        This method handles UI concerns: refreshing UI components and managing
        active installation display, while delegating business logic to InstallationManager.

        Args:
            installation_name: Name of the installation to remove

        Returns:
            bool: True if successfully removed
        """
        try:
            # Get installation manager
            installation_manager = get_installation_manager()

            # Delegate removal logic to InstallationManager
            current_game_type = installation_manager.get_current_game_type()
            result = installation_manager.remove_installation(
                current_game_type, installation_name
            )

            if result["success"]:
                # Refresh UI
                self._refresh_installations_ui()

                # Handle active installation UI updates
                if result["was_active"]:
                    self._refresh_active_install_ui()

            return result["success"]

        except Exception as e:
            self.logger.error(f"Error removing installation: {e}")
            return False

    def _start_game(self, install_path: str, world_name: str = "") -> bool:
        """
        Start the game with optional world parameter.

        Args:
            install_path: Path to the game installation directory
            world_name: Optional world name to resume

        Returns:
            bool: True if game was launched successfully
        """
        try:
            installation_manager = get_installation_manager()
            current_game_type = installation_manager.get_current_game_type()

            paths = get_paths()
            # Get the userdata directory
            userdata_path = paths.get_game_user_dir(current_game_type.name)

            # Ensure userdata directory exists
            userdata_path.mkdir(parents=True, exist_ok=True)

            system = platform.system()
            self.logger.info(f"Starting game on {system} from {install_path}")

            if system == "Linux":
                return self._start_game_linux(install_path, str(userdata_path), world_name, current_game_type)
            elif system == "Windows":
                return self._start_game_windows(install_path, str(userdata_path), world_name, current_game_type)
            else:
                self.logger.error(f"Unsupported operating system: {system}")
                return False

        except Exception as e:
            self.logger.error(f"Error starting game: {e}")
            return False

    def _start_game_linux(self, install_path: str, userdata_path: str, world_name: str, current_game_type: GameType) -> bool:
        """Start the game on Linux."""
        try:
            # Determine the executable name based on game type
            if current_game_type.executable_name is None:
                raise ValueError(f"Executable name not defined for {current_game_type}")
            exe_file = current_game_type.executable_name.get("linux")
            if exe_file is None:
                raise ValueError(f"Executable name not defined for {current_game_type}")
            
            # Look for the launcher executable
            launcher_path = Path(install_path) / exe_file

            if not launcher_path.exists():
                self.logger.error(f"Game launcher not found: {launcher_path}")
                return False

            # Build command arguments
            params = ["--userdir", f"{userdata_path}/"]
            if world_name:
                params.extend(["--world", world_name])

            self.logger.info(f"Executing: {launcher_path} {' '.join(params)}")

            # Start the game process
            subprocess.Popen([str(launcher_path)] + params, cwd=install_path)

            # Check if we should close the launcher after starting the game
            try:
                settings = get_settings()
                if not settings.read("keep_open_after_starting_game", True):
                    self.logger.info("Closing launcher as per settings")
                    self.event_manager.emit(Events.APP_EXIT_REQUESTED)
            except Exception:
                # Settings not available, keep launcher open
                pass

            return True

        except Exception as e:
            self.logger.error(f"Error starting game on Linux: {e}")
            return False

    def _start_game_windows(self, install_path: str, userdata_path: str, world_name: str, current_game_type: GameType) -> bool:
        """Start the game on Windows."""
        try:
            # Determine the executable name based on game type
            if current_game_type.executable_name is None:
                raise ValueError(f"Executable name not defined for {current_game_type}")
            exe_file = current_game_type.executable_name.get("windows")
            if exe_file is None:
                raise ValueError(f"Executable name not defined for {current_game_type}")

            exe_path = Path(install_path) / exe_file
            if not exe_path.exists():
                self.logger.error(f"Game executable not found: {exe_path}")
                return False

            userdir_arg = str(Path(userdata_path)) + os.sep

            args = [str(exe_path), "--userdir", userdir_arg]
            if world_name:
                args += ["--world", world_name]

            self.logger.info("Executing: %s", " ".join(args))

            subprocess.Popen(args, cwd=str(install_path))

            # Optionally close the launcher based on settings
            try:
                settings = get_settings()
                if not settings.read("keep_open_after_starting_game", True):
                    self.logger.info("Closing launcher as per settings")
                    self.event_manager.emit(Events.APP_EXIT_REQUESTED)
            except Exception:
                # Settings not available, keep launcher open
                pass

            return True

        except Exception as e:
            self.logger.error(f"Error starting game on Windows: {e}")
            return False

    def _get_last_world(self, install_path: str) -> Optional[str]:
        """
        Get the last played world name from lastworld.json.

        Args:
            install_path: Path to the game installation directory

        Returns:
            str: Name of the last world or None if not found
        """
        try:
            # The lastworld.json file is in the config subdirectory of userdata
            installation_manager = get_installation_manager()
            current_game_type = installation_manager.get_current_game_type()

            paths = get_paths()
            config_path = paths.get_game_user_dir(current_game_type.name) / "config" / "lastworld.json"

            if not config_path.exists():
                self.logger.debug(f"No lastworld.json found at: {config_path}")
                return None

            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            world_name = data.get("world_name")
            if world_name:
                self.logger.info(f"Found last world: {world_name}")
                return world_name
            else:
                self.logger.debug("lastworld.json exists but contains no world_name")
                return None

        except Exception as e:
            self.logger.error(f"Error reading lastworld.json: {e}")
            return None

    def _update_active_installation(self, release: GameRelease):
        """
        Update the active installation setting.

        Args:
            release: The newly installed/updated release
        """
        try:
            installation_manager = get_installation_manager()

            # Get the GameInstallation object for the release
            installations = installation_manager.installed_games.get(release.game_type, {})
            if release.name in installations:
                installation = installations[release.name]
                installation_manager.set_active_installation(installation, release.game_type)
                self.logger.info(f"Updated active installation: {release.name}")
            else:
                self.logger.warning(f"Installation '{release.name}' not found for {release.game_type.name}")

        except Exception as e:
            self.logger.error(f"Error updating active installation: {e}")

    # Installation flow methods
    def _show_asset_selection_modal(self, release: GameRelease):
        """
        Show a modal dialog for selecting which asset variant to install.

        Args:
            release: The release containing assets to choose from
        """
        try:
            # Create and show the asset selection dialog
            dialog = AssetInstallSelectionDialog(
                parent_window=self.view.get_parent_frame(),
                release=release,
                on_asset_selected=lambda asset: self._on_asset_selected_from_modal(release, asset)
            )

            self.current_modal = dialog.show(width=600, height=500)

        except Exception as e:
            self.logger.error(f"Error showing asset selection modal: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _close_current_modal(self):
        """Close the current modal window."""
        if self.current_modal:
            self.current_modal.destroy()
            self.current_modal = None

    def _on_asset_selected_from_modal(self, release: GameRelease, selected_asset: Optional[ReleaseAsset]):
        """
        Handle asset selection from the modal and start installation.

        Args:
            release: The release being installed
            selected_asset: The selected asset
        """
        try:
            if not selected_asset:
                self.logger.warning("No asset selected")
                return

            self.logger.info(f"Starting installation of: {selected_asset.name}")

            # Close the modal
            self._close_current_modal()

            # Start the actual download and installation process
            self._start_download_and_installation(release, selected_asset)

        except Exception as e:
            self.logger.error(f"Error processing asset selection: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _start_download_and_installation(self, release: GameRelease, selected_asset: ReleaseAsset):
        """
        Start the download and installation process for the selected asset.

        This method now simply delegates to the InstallationManager's event-driven flow.
        All progress updates and completion handling are done through events.

        Args:
            release: The release being installed
            selected_asset: The selected asset to download and install
        """
        try:
            self.logger.info(f"Starting download and installation for: {selected_asset.name}")

            # Get installation manager
            try:
                installation_manager = get_installation_manager()
            except RuntimeError:
                self.logger.error("Installation manager not available")
                return

            # Get UI input: check if we should update existing installation
            update_existing = self.view.get_update_existing_checked()

            # Create installation progress dialog
            progress_dialog = InstallationProgressDialog(
                parent_window=self.view.get_parent_frame(),
                event_manager=self.event_manager,
                filename=selected_asset.name
            )

            # Show the progress dialog with larger size for dual progress bars
            self.current_modal = progress_dialog.show(width=600, height=300)

            # Start the complete installation flow - this handles everything
            success = installation_manager.start_complete_installation_flow(
                release=release,
                selected_asset=selected_asset,
                update_existing=update_existing
            )

            if not success:
                self.logger.error("Failed to start installation flow")
                progress_dialog.close()
                self.current_modal = None

        except Exception as e:
            self.logger.error(f"Error starting download and installation: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    # Event handlers for installation flow
    def _on_installation_started(self, sender, **kwargs):
        """Handle installation started event."""
        try:
            release = kwargs.get('release')
            if release:
                self.logger.info(f"Starting installation: {release.name}")

        except Exception as e:
            self.logger.error(f"Error handling installation started event: {e}")


    def _on_installation_finished(self, sender, **kwargs):
        """Handle installation finished event."""
        try:
            release = kwargs.get('release')
            success = kwargs.get('success', False)
            error_message = kwargs.get('error_message')
            installation_path = kwargs.get('installation_path')

            if success and release:
                self.logger.info(f"Installation completed successfully: {release.name}")

                current_active = self.get_active_installation()
                should_set_active = (not current_active) or self.view.get_update_existing_checked()

                if should_set_active:
                    self._update_active_installation(release)

                # Update the installations list and UI
                self._refresh_installations_ui()

            elif not success:
                error_display = f"Installation failed: {error_message}" if error_message else "Installation failed"
                self.logger.error(error_display)

        except Exception as e:
            self.logger.error(f"Error handling installation finished event: {e}")

    def _on_current_game_type_changed(self, sender, **kwargs):
        """Handle current game type changed event."""
        try:
            old_game_type = kwargs.get('old_game_type')
            new_game_type = kwargs.get('new_game_type')

            if new_game_type:
                self.logger.info(f"Game type changed from {old_game_type.name if old_game_type else 'None'} to {new_game_type.name}")

                # Update UI to reflect new game type
                self.view.game_selector.set(new_game_type.display_name)

                # Refresh UI for new game type
                self.refresh_ui()

        except Exception as e:
            self.logger.error(f"Error handling game type changed event: {e}")

    def _on_active_installation_changed(self, sender, **kwargs):
        """Handle active installation changed event."""
        try:
            game_type = kwargs.get('game_type')
            old_active = kwargs.get('old_active')
            new_active = kwargs.get('new_active')
            reason = kwargs.get('reason', 'unknown')

            installation_manager = get_installation_manager()
            current_game_type = installation_manager.get_current_game_type()

            # Only update UI if this change affects the current game type
            if game_type == current_game_type:
                game_name = game_type.name if game_type else "unknown"
                self.logger.info(f"Active installation changed for {game_name}: {old_active} -> {new_active} (reason: {reason})")

                # Refresh installations list and active installation UI
                self._refresh_installations_list()
                self._refresh_active_install_ui()

        except Exception as e:
            self.logger.error(f"Error handling active installation changed event: {e}")

    def shutdown(self):
        """Shutdown the controller and clean up resources."""
        try:
            self.logger.info("Shutting down game tab controller...")

            # Unsubscribe from events
            self._unsubscribe_from_events()

            self.logger.info("Game tab controller shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during game tab controller shutdown: {e}")
