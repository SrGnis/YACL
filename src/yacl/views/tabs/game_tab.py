"""
Game Tab Implementation for YACL

This module provides the game management tab UI components with release selection,
installation controls, active install management, and launch functionality using Tkinter.
This is the View component in the MVC pattern - it only handles UI rendering and layout.
"""

from typing import Optional, List
import tkinter as tk
from tkinter import ttk

from yacl.ui.widgets.base_tab import BaseTab
from yacl.services.events import EventManager
from yacl.models.game_type import GameType


class GameTab(BaseTab):
    """
    Game management tab view for YACL using Tkinter.

    This view provides UI components for:
    - Game selection and switching
    - Release channel management (stable/experimental)
    - Release browsing and installation
    - Active installation management
    - Game launching functionality
    - Multi-installation support
    """

    def __init__(self, parent_frame: ttk.Frame, event_manager: EventManager):
        """
        Initialize the game tab view.

        Args:
            parent_frame: The parent frame to create content in
            event_manager: Event manager for component communication
        """
        # Initialize the base tab
        super().__init__(parent_frame, event_manager)

        # UI widget references
        self.game_selector: ttk.Combobox
        self.channel_var: tk.StringVar
        self.channel_stable_radio: ttk.Radiobutton
        self.channel_experimental_radio: ttk.Radiobutton
        self.search_var: tk.StringVar
        self.search_entry: ttk.Entry
        self.clear_search_button: ttk.Button
        self.releases_listbox: tk.Listbox
        self.refresh_button: ttk.Button
        self.install_button: ttk.Button
        self.update_var: tk.BooleanVar
        self.update_checkbox: ttk.Checkbutton
        self.active_install_label: ttk.Label
        self.play_button: ttk.Button
        self.resume_button: ttk.Button
        self.installations_listbox: tk.Listbox
        self.activate_button: ttk.Button
        self.delete_button: ttk.Button

        # Additional UI widget references for controller access
        self.refresh_installations_button: ttk.Button

        self.logger.info("Game tab view initialized")

    def _create_tab_content(self):
        if not self.scrollable_frame:
            self.logger.error("Scrollable frame not available")
            return

        try:
            # Create sections
            self._create_game_selection_section(self.scrollable_frame)

            self._create_release_section(self.scrollable_frame)

            self._create_active_install_section(self.scrollable_frame)

            self._create_installations_section(self.scrollable_frame)

        except Exception as e:
            self.logger.error(f"Failed to create game tab content: {e}")
            raise
    
    def _create_game_selection_section(self, parent_frame: ttk.Frame):
        """Create the game selection section."""
        # Game selection frame
        game_frame = self.create_section_frame(parent_frame, "Game Selection")

        # Game selector
        selector_frame = ttk.Frame(game_frame)
        selector_frame.pack(fill=tk.X, pady=2)

        ttk.Label(selector_frame, text="Game:").pack(side=tk.LEFT)

        self.game_selector = ttk.Combobox(
            selector_frame,
            values=[game_type.display_name for game_type in GameType.all],
            state="readonly",
            width=30
        )
        self.game_selector.set(GameType.all[0].display_name)
        self.game_selector.pack(side=tk.RIGHT)
    
    def _create_release_section(self, parent_frame: ttk.Frame):
        """Create the release selection section with channel selection."""
        release_frame = self.create_section_frame(parent_frame, "Release Management")

        # Channel selection
        channel_frame = ttk.Frame(release_frame)
        channel_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(channel_frame, text="Release Channel:").pack(side=tk.LEFT)

        # Create StringVar for radio button group
        self.channel_var = tk.StringVar(value="Stable")

        # Radio button frame
        radio_frame = ttk.Frame(channel_frame)
        radio_frame.pack(side=tk.RIGHT)

        # Stable radio button
        self.channel_stable_radio = ttk.Radiobutton(
            radio_frame,
            text="Stable",
            variable=self.channel_var,
            value="Stable"
        )
        self.channel_stable_radio.pack(side=tk.LEFT, padx=(0, 10))

        # Experimental radio button
        self.channel_experimental_radio = ttk.Radiobutton(
            radio_frame,
            text="Experimental",
            variable=self.channel_var,
            value="Experimental"
        )
        self.channel_experimental_radio.pack(side=tk.LEFT)

        # Release list header with search and refresh
        list_header_frame = ttk.Frame(release_frame)
        list_header_frame.pack(fill=tk.X, pady=(5, 2))

        ttk.Label(list_header_frame, text="Available Releases:").pack(side=tk.LEFT)

        self.refresh_button = ttk.Button(
            list_header_frame,
            text="Refresh"
        )
        self.refresh_button.pack(side=tk.RIGHT, padx=(0, 2))

        # Search controls
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            list_header_frame,
            textvariable=self.search_var,
            width=20
        )
        self.search_entry.pack(side=tk.RIGHT, padx=(0, 10))

        self.clear_search_button = ttk.Button(
            list_header_frame,
            text="Clear",
            width=6
        )
        self.clear_search_button.pack(side=tk.RIGHT, padx=(0, 2))

        # Release list
        list_frame = ttk.Frame(release_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # Create listbox with scrollbar
        self.releases_listbox = tk.Listbox(
            list_frame,
            height=10,
            selectmode=tk.SINGLE
        )
        self.releases_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for listbox
        releases_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        releases_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Connect scrollbar to listbox
        self.releases_listbox.config(yscrollcommand=releases_scrollbar.set)
        releases_scrollbar.config(command=self.releases_listbox.yview)

        # Selection event will be bound by controller

        # Install controls
        install_controls_frame = ttk.Frame(release_frame)
        install_controls_frame.pack(fill=tk.X, pady=(0, 5))

        self.install_button = ttk.Button(
            install_controls_frame,
            text="Install Selected",
            state=tk.DISABLED
        )
        self.install_button.pack(side=tk.LEFT)

        # Update checkbox
        self.update_var = tk.BooleanVar(value=True)
        self.update_checkbox = ttk.Checkbutton(
            install_controls_frame,
            text="Update current installation",
            variable=self.update_var
        )
        self.update_checkbox.pack(side=tk.LEFT, padx=(15, 0))
    
    def _create_active_install_section(self, parent_frame: ttk.Frame):
        """Create the active installation section."""
        install_frame = self.create_section_frame(parent_frame, "Active Installation")

        # Active installation display
        active_info_frame = ttk.Frame(install_frame)
        active_info_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(active_info_frame, text="Current Active:").pack(side=tk.LEFT)

        self.active_install_label = ttk.Label(
            active_info_frame,
            text="No active installation",
            font=("TkDefaultFont", 9, "bold")
        )
        self.active_install_label.pack(side=tk.RIGHT)

        # Play game button
        play_frame = ttk.Frame(install_frame)
        play_frame.pack(fill=tk.X, pady=(0, 5))

        self.play_button = ttk.Button(
            play_frame,
            text="Launch Game",
            state=tk.DISABLED
        )
        self.play_button.pack(side=tk.LEFT)

        # Resume game button
        self.resume_button = ttk.Button(
            play_frame,
            text="Resume Game",
            state=tk.DISABLED
        )
        self.resume_button.pack(side=tk.LEFT, padx=(10, 0))
    
    def _create_installations_section(self, parent_frame: ttk.Frame):
        """Create the installations management section."""
        installations_frame = self.create_section_frame(parent_frame, "Installations")

        # Installations list header
        list_header_frame = ttk.Frame(installations_frame)
        list_header_frame.pack(fill=tk.X, pady=(0, 2))

        ttk.Label(list_header_frame, text="Installed Versions:").pack(side=tk.LEFT)

        # Refresh installations button
        self.refresh_installations_button = ttk.Button(
            list_header_frame,
            text="Refresh"
        )
        self.refresh_installations_button.pack(side=tk.RIGHT)

        # Installations list
        list_frame = ttk.Frame(installations_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # Create listbox with scrollbar
        self.installations_listbox = tk.Listbox(
            list_frame,
            height=4,
            selectmode=tk.SINGLE
        )
        self.installations_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for installations listbox
        installs_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        installs_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Connect scrollbar to listbox
        self.installations_listbox.config(yscrollcommand=installs_scrollbar.set)
        installs_scrollbar.config(command=self.installations_listbox.yview)

        # Selection event will be bound by controller

        # Installation management buttons
        buttons_frame = ttk.Frame(installations_frame)
        buttons_frame.pack(fill=tk.X)

        self.activate_button = ttk.Button(
            buttons_frame,
            text="Set Active",
            state=tk.DISABLED
        )
        self.activate_button.pack(side=tk.LEFT)

        self.delete_button = ttk.Button(
            buttons_frame,
            text="Delete",
            state=tk.DISABLED
        )
        self.delete_button.pack(side=tk.LEFT, padx=(10, 0))

    def get_selected_game(self) -> Optional[str]:
        return self.game_selector.get()

    def get_selected_channel(self) -> Optional[str]:
        return self.channel_var.get()

    def get_selected_release_index(self) -> Optional[int]:
        selection = self.releases_listbox.curselection()
        if selection:
            return selection[0]

    def get_selected_installation_index(self) -> Optional[int]:
        selection = self.installations_listbox.curselection()
        if selection:
            return selection[0]

    def get_update_existing_checked(self) -> bool:
        return self.update_var.get()

    def get_parent_frame(self) -> ttk.Frame:
        return self.parent_frame

    def update_releases_list(self, release_names: List[str]):
        try:
            if not self.releases_listbox:
                return

            # Clear current list
            self.releases_listbox.delete(0, tk.END)

            # Add release names to listbox
            for name in release_names:
                self.releases_listbox.insert(tk.END, name)

        except Exception as e:
            self.logger.error(f"Error updating releases list: {e}")

    def get_search_text(self) -> str:
        """Get the current search text."""
        try:
            return self.search_var.get().strip()
        except Exception:
            return ""

    def clear_search(self):
        """Clear the search text."""
        try:
            self.search_var.set("")
        except Exception as e:
            self.logger.error(f"Error clearing search: {e}")

    def set_search_text(self, text: str):
        """Set the search text."""
        try:
            self.search_var.set(text)
        except Exception as e:
            self.logger.error(f"Error setting search text: {e}")

    def update_installations_list(self, installation_display: List[str]):
        try:
            if not self.installations_listbox:
                return

            # Clear current list
            self.installations_listbox.delete(0, tk.END)

            # Add installation names to listbox
            for display_text in installation_display:
                self.installations_listbox.insert(tk.END, display_text)

        except Exception as e:
            self.logger.error(f"Error updating installations list: {e}")

    def shutdown(self):
        try:
            self.logger.info("Shutting down game tab view...")
            self.logger.info("Game tab view shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during game tab view shutdown: {e}")
