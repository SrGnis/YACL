"""
Settings Tab Implementation for YACL

This module provides the settings management tab UI components with user preference controls,
configuration options, and save/reset functionality using Tkinter.
This is the View component in the MVC pattern - it only handles UI rendering and layout.
"""

from typing import Optional, Dict, Any
import tkinter as tk
from tkinter import ttk

from yacl.ui.widgets.base_tab import BaseTab
from yacl.services.events import EventManager


class SettingsTab(BaseTab):
    """
    Settings management tab view for YACL using Tkinter.

    This view provides UI components for:
    - Game selection preferences
    - Release channel preferences
    - Launcher behavior settings
    - Debug and advanced options
    - Save/Reset functionality
    """

    def __init__(self, parent_frame: ttk.Frame, event_manager: EventManager):
        """
        Initialize the settings tab view.

        Args:
            parent_frame: The parent frame to create content in
            event_manager: Event manager for component communication
        """
        # Initialize the base tab
        super().__init__(parent_frame, event_manager)

        # UI widget references for settings
        self.update_current_var: tk.BooleanVar
        self.update_current_checkbox: ttk.Checkbutton
        self.keep_open_var: tk.BooleanVar
        self.keep_open_checkbox: ttk.Checkbutton
        self.debug_mode_var: tk.BooleanVar
        self.debug_mode_checkbox: ttk.Checkbutton
        self.enable_db_var: tk.BooleanVar
        self.enable_db_checkbox: ttk.Checkbutton
        self.enable_db_auto_update_var: tk.BooleanVar
        self.enable_db_auto_update_checkbox: ttk.Checkbutton
        
        # Action buttons
        self.save_button: ttk.Button
        self.reset_button: ttk.Button
        self.apply_button: ttk.Button

        # Initialize boolean variables
        self.update_current_var = tk.BooleanVar()
        self.keep_open_var = tk.BooleanVar()
        self.debug_mode_var = tk.BooleanVar()
        self.enable_db_var = tk.BooleanVar()
        self.enable_db_auto_update_var = tk.BooleanVar()

        self.logger.info("Settings tab view initialized")

    def _create_tab_content(self):
        """Create the settings tab content."""
        if not self.scrollable_frame:
            self.logger.error("Scrollable frame not available")
            return

        try:
            # Create sections
            self._create_launcher_behavior_section(self.scrollable_frame)
            self._create_advanced_options_section(self.scrollable_frame)
            self._create_action_buttons_section(self.scrollable_frame)

        except Exception as e:
            self.logger.error(f"Failed to create settings tab content: {e}")
            raise



    def _create_launcher_behavior_section(self, parent_frame: ttk.Frame):
        """Create the launcher behavior section."""
        behavior_frame = self.create_section_frame(parent_frame, "Launcher Behavior")

        # Update current when installing
        self.update_current_checkbox = ttk.Checkbutton(
            behavior_frame,
            text="Update current installation when installing new version",
            variable=self.update_current_var
        )
        self.update_current_checkbox.pack(anchor=tk.W, pady=2)

        # Keep open after starting game
        self.keep_open_checkbox = ttk.Checkbutton(
            behavior_frame,
            text="Keep launcher open after starting game",
            variable=self.keep_open_var
        )
        self.keep_open_checkbox.pack(anchor=tk.W, pady=2)

    def _create_advanced_options_section(self, parent_frame: ttk.Frame):
        """Create the advanced options section."""
        advanced_frame = self.create_section_frame(parent_frame, "Advanced Options")

        # Debug mode
        self.debug_mode_checkbox = ttk.Checkbutton(
            advanced_frame,
            text="Enable debug mode (verbose logging)",
            variable=self.debug_mode_var
        )
        self.debug_mode_checkbox.pack(anchor=tk.W, pady=2)

        # Enable Cataclysm DB
        self.enable_db_checkbox = ttk.Checkbutton(
            advanced_frame,
            text="Enable Cataclysm Database integration",
            variable=self.enable_db_var
        )
        self.enable_db_checkbox.pack(anchor=tk.W, pady=2)

        # Enable DB auto-update
        self.enable_db_auto_update_checkbox = ttk.Checkbutton(
            advanced_frame,
            text="Enable automatic database updates",
            variable=self.enable_db_auto_update_var
        )
        self.enable_db_auto_update_checkbox.pack(anchor=tk.W, pady=2)

    def _create_action_buttons_section(self, parent_frame: ttk.Frame):
        """Create the action buttons section."""
        button_frame = ttk.Frame(parent_frame)
        button_frame.pack(fill=tk.X, pady=(20, 10))

        # Create a centered frame for buttons
        centered_frame = ttk.Frame(button_frame)
        centered_frame.pack()

        self.save_button = ttk.Button(
            centered_frame,
            text="Save Settings",
            width=15
        )
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.reset_button = ttk.Button(
            centered_frame,
            text="Reset to Defaults",
            width=15
        )
        self.reset_button.pack(side=tk.LEFT, padx=5)

    def get_settings_values(self) -> Dict[str, Any]:
        """
        Get current values from all UI elements.

        Returns:
            Dict[str, Any]: Dictionary of setting names to values
        """
        return {
            "update_current_when_installing": self.update_current_var.get(),
            "keep_open_after_starting_game": self.keep_open_var.get(),
            "debug_mode": self.debug_mode_var.get(),
            "enable_cataclysm_db": self.enable_db_var.get(),
            "enable_db_auto_update": self.enable_db_auto_update_var.get()
        }

    def set_settings_values(self, settings: Dict[str, Any]):
        """
        Set UI element values from settings dictionary.

        Args:
            settings: Dictionary of setting names to values
        """
        self.update_current_var.set(settings.get("update_current_when_installing", True))
        self.keep_open_var.set(settings.get("keep_open_after_starting_game", True))
        self.debug_mode_var.set(settings.get("debug_mode", False))
        self.enable_db_var.set(settings.get("enable_cataclysm_db", True))
        self.enable_db_auto_update_var.set(settings.get("enable_db_auto_update", True))

    def set_buttons_enabled(self, enabled: bool):
        """
        Enable or disable action buttons.
        
        Args:
            enabled: Whether buttons should be enabled
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        self.save_button.config(state=state)
        self.reset_button.config(state=state)
