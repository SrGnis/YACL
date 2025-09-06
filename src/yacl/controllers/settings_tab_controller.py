"""
Settings Tab Controller for YACL

This module provides the SettingsTabController class that handles all business logic,
event management, and settings service interactions for the settings tab, following MVC pattern.
"""

import logging
import tkinter.messagebox as messagebox
from typing import Dict, Any

from yacl.services.events import EventManager, Events
from yacl.views.tabs.settings_tab import SettingsTab
from yacl.services.settings import get_settings


class SettingsTabController:
    """
    Controller for the settings tab that handles all business logic and event management.
    
    This controller:
    - Manages settings loading and saving
    - Handles user input events from the settings view
    - Coordinates with the settings service
    - Manages settings validation and error handling
    - Handles reset to defaults functionality
    """
    
    def __init__(self, view: SettingsTab, event_manager: EventManager):
        """
        Initialize the settings tab controller.
        
        Args:
            view: The SettingsTab view instance
            event_manager: Event manager for component communication
        """
        self.logger = logging.getLogger("YACL")
        self.view = view
        self.event_manager = event_manager
        
        # Track if settings have been modified
        self.has_unsaved_changes = False
        
        # Setup event handlers
        self._setup_event_handlers()
        
        # Subscribe to events
        self._subscribe_to_events()
        
        # Load current settings
        self.refresh_ui()
        
        self.logger.info("Settings tab controller initialized")

    def _setup_event_handlers(self):
        """Setup event handlers for UI elements."""
        try:
            # Button event handlers
            self.view.save_button.config(command=self._on_save_clicked)
            self.view.reset_button.config(command=self._on_reset_clicked)
            
            # Track changes in UI elements
            self.view.update_current_var.trace_add('write', self._on_setting_changed)
            self.view.keep_open_var.trace_add('write', self._on_setting_changed)
            self.view.debug_mode_var.trace_add('write', self._on_setting_changed)
            self.view.enable_db_var.trace_add('write', self._on_setting_changed)
            self.view.enable_db_auto_update_var.trace_add('write', self._on_setting_changed)
            
        except Exception as e:
            self.logger.error(f"Failed to setup event handlers: {e}")

    def _subscribe_to_events(self):
        """Subscribe to relevant events."""
        try:
            self.event_manager.subscribe(Events.SETTINGS_CHANGED, self._on_settings_changed)
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe to events: {e}")

    def refresh_ui(self):
        """Refresh the UI with current settings values."""
        try:
            settings = get_settings()
            current_settings = settings.get_all_user_settings()
            
            # Load current settings into UI
            self.view.set_settings_values(current_settings)
            
            # Reset change tracking
            self.has_unsaved_changes = False
            self._update_button_states()
            
            self.logger.debug("Settings UI refreshed")
            
        except RuntimeError:
            # Settings not initialized yet
            self.logger.debug("Settings not initialized, using defaults")
            self._load_default_settings()
        except Exception as e:
            self.logger.error(f"Failed to refresh settings UI: {e}")
            self._load_default_settings()

    def _load_default_settings(self):
        """Load default settings into the UI."""
        try:
            default_settings = {
                "update_current_when_installing": True,
                "keep_open_after_starting_game": True,
                "debug_mode": False,
                "enable_cataclysm_db": True,
                "enable_db_auto_update": True
            }
            
            self.view.set_settings_values(default_settings)
            self.has_unsaved_changes = False
            self._update_button_states()
            
        except Exception as e:
            self.logger.error(f"Failed to load default settings: {e}")

    def _on_setting_changed(self, *args):
        """Handle when any setting value changes."""
        self.has_unsaved_changes = True
        self._update_button_states()

    def _update_button_states(self):
        """Update the state of action buttons based on current state."""
        try:
            # Enable buttons based on whether there are unsaved changes
            self.view.set_buttons_enabled(True)
            
            # Update button text to indicate state
            if self.has_unsaved_changes:
                self.view.save_button.config(text="Save Settings*")
            else:
                self.view.save_button.config(text="Save Settings")
                
        except Exception as e:
            self.logger.error(f"Failed to update button states: {e}")

    def _on_save_clicked(self):
        """Handle save button click."""
        try:
            if self._save_settings():
                # Save successful, also save to file
                settings = get_settings()
                if settings.save_user():
                    messagebox.showinfo("Settings", "Settings saved successfully!")
                    self.has_unsaved_changes = False
                    self._update_button_states()
                else:
                    messagebox.showerror("Error", "Failed to save settings to file.")
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def _on_reset_clicked(self):
        """Handle reset button click."""
        try:
            result = messagebox.askyesno(
                "Reset Settings",
                "Are you sure you want to reset all settings to their default values?\n\n"
                "This action cannot be undone."
            )
            
            if result:
                settings = get_settings()
                if settings.reset_user_to_defaults():
                    self.refresh_ui()
                    messagebox.showinfo("Settings", "Settings reset to defaults successfully!")
                else:
                    messagebox.showerror("Error", "Failed to reset settings to defaults.")
            
        except Exception as e:
            self.logger.error(f"Error resetting settings: {e}")
            messagebox.showerror("Error", f"Failed to reset settings: {e}")

    def _save_settings(self) -> bool:
        """
        Save current UI values to settings service.

        Returns:
            bool: True if save was successful
        """
        try:
            settings = get_settings()
            current_values = self.view.get_settings_values()
            # Save each setting
            for setting_name, value in current_values.items():
                if not settings.store_user(setting_name, value):
                    self.logger.error(f"Failed to store setting: {setting_name}")
                    return False
            
            # Emit settings changed event
            self.event_manager.emit(Events.SETTINGS_CHANGED, settings=current_values)
            
            self.logger.info("Settings saved successfully")
            return True
            
        except RuntimeError:
            messagebox.showerror("Error", "Settings service not initialized.")
            return False
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            return False

    def _on_settings_changed(self, sender=None, **kwargs):
        """Handle settings changed event from other components."""
        try:
            # Refresh UI to reflect external changes
            self.refresh_ui()

        except Exception as e:
            self.logger.error(f"Error handling settings changed event: {e}")

    def shutdown(self):
        """Shutdown the controller and clean up resources."""
        try:
            self.logger.info("Shutting down settings tab controller...")
            
            # Check for unsaved changes
            if self.has_unsaved_changes:
                result = messagebox.askyesnocancel(
                    "Unsaved Changes",
                    "You have unsaved settings changes. Do you want to save them before closing?"
                )
                
                if result is True:  # Yes, save
                    self._save_settings()
                elif result is None:  # Cancel
                    return False  # Don't shutdown (TODO)
                # If No (False), continue without saving
            
            self.logger.info("Settings tab controller shutdown complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during settings tab controller shutdown: {e}")
            return True  # Continue shutdown even if there's an error
