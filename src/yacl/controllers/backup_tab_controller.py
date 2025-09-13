"""
Backup Tab Controller for YACL

This module provides the controller for the backup management tab that handles
all business logic and event management for backup operations.
"""

import logging
import traceback
from typing import Optional, List, Dict
import tkinter as tk
from datetime import datetime

from yacl.services.events import EventManager, Events
from yacl.views.tabs.backup_tab import BackupTab
from yacl.models.backup_manager import get_backup_manager, BackupError
from yacl.models.installation_manager import get_installation_manager
from yacl.models.backup import SaveBackup
from yacl.models.game_type import GameType


class BackupTabController:
    """
    Controller for the backup tab that handles all business logic and event management.
    
    This controller:
    - Manages backup listing and filtering by game type
    - Handles backup creation, deletion, and restoration
    - Coordinates with BackupManager and InstallationManager
    - Manages backup selection and details display
    - Handles all user input events and business logic
    """
    
    def __init__(self, view: BackupTab, event_manager: EventManager):
        """
        Initialize the backup tab controller.
        
        Args:
            view: The BackupTab view instance
            event_manager: Event manager for component communication
        """
        self.logger = logging.getLogger("YACL")
        self.view = view
        self.event_manager = event_manager
        
        # State variables
        self.current_backups: List[SaveBackup] = []
        self.selected_backup: Optional[SaveBackup] = None
        
        # Setup event handlers and subscriptions
        self._setup_event_handlers()
        self._subscribe_to_events()
        
        self.logger.info("Backup tab controller initialized")

    def _setup_event_handlers(self):
        """Setup event handlers by directly binding to view widgets."""
        # Direct widget binding following established patterns
        
        self.view.backup_listbox.bind("<<ListboxSelect>>", self._on_backup_selected)
        
        self.view.refresh_button.configure(command=self._on_refresh_backups)
        
        self.view.delete_button.configure(command=self._on_delete_backup)
        
        self.view.restore_button.configure(command=self._on_restore_backup)
        
        self.view.create_button.configure(command=self._on_create_backup)
        
        # Bind Enter key to create backup when in name entry
        self.view.backup_name_entry.bind("<Return>", lambda e: self._on_create_backup())

    def _subscribe_to_events(self):
        """Subscribe to events."""
        try:
            self.event_manager.subscribe(Events.CURRENT_GAME_TYPE_CHANGED, self._on_current_game_type_changed)
            self.event_manager.subscribe(Events.BACKUP_CREATED, self._on_backup_created)
            self.event_manager.subscribe(Events.BACKUP_DELETED, self._on_backup_deleted)
            self.event_manager.subscribe(Events.BACKUP_RESTORED, self._on_backup_restored)
            self.event_manager.subscribe(Events.BACKUP_LIST_REFRESHED, self._on_backup_list_refreshed)
            self.event_manager.subscribe(Events.TAB_CHANGED, self._on_tab_changed)

            self.logger.debug("Subscribed to backup events")

        except Exception as e:
            self.logger.error(f"Error subscribing to events: {e}")

    def _unsubscribe_from_events(self):
        """Unsubscribe from events."""
        try:
            self.event_manager.unsubscribe(Events.CURRENT_GAME_TYPE_CHANGED, self._on_current_game_type_changed)
            self.event_manager.unsubscribe(Events.BACKUP_CREATED, self._on_backup_created)
            self.event_manager.unsubscribe(Events.BACKUP_DELETED, self._on_backup_deleted)
            self.event_manager.unsubscribe(Events.BACKUP_RESTORED, self._on_backup_restored)
            self.event_manager.unsubscribe(Events.BACKUP_LIST_REFRESHED, self._on_backup_list_refreshed)
            self.event_manager.unsubscribe(Events.TAB_CHANGED, self._on_tab_changed)

            self.logger.debug("Unsubscribed from backup events")

        except Exception as e:
            self.logger.error(f"Error unsubscribing from events: {e}")

    def refresh_ui(self):
        """Refresh the UI state."""
        try:
            self._refresh_backup_list()
            self._update_backup_details()
            self._update_button_states()

        except Exception as e:
            self.logger.error(f"Error refreshing backup UI: {e}")

    def _refresh_backup_list(self):
        """Refresh the backup list for the current game type."""
        try:
            installation_manager = get_installation_manager()
            backup_manager = get_backup_manager()
            
            current_game_type = installation_manager.get_current_game_type()
            
            # Load backups for current game type
            backup_manager.load_backups(current_game_type)
            
            # Get backups and update UI
            backups_dict = backup_manager.get_backups(current_game_type)
            self.current_backups = list(backups_dict.values())
            
            # Sort backups by creation date (newest first)
            self.current_backups.sort(key=lambda b: b.created_at, reverse=True)
            
            # Update backup list in view
            backup_names = [backup.name for backup in self.current_backups]
            self.view.update_backup_list(backup_names)
            
            self.logger.debug(f"Refreshed backup list: {len(self.current_backups)} backups")

        except Exception as e:
            self.logger.error(f"Error refreshing backup list: {e}")
            self.view.update_backup_list([])

    def _update_backup_details(self):
        """Update the backup details display."""
        try:
            if not self.selected_backup:
                self.view.update_backup_details("No backup selected.")
                return

            backup = self.selected_backup
            
            # Format backup details
            details = f"Backup: {backup.name}\n"
            details += f"Game: {backup.game.display_name}\n"
            details += f"Created: {backup.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            details += f"Size: {self._format_size(backup.size)}\n"
            details += f"Save Games: {len(backup.save_games)}\n\n"
            
            if backup.save_games:
                details += "Included Save Games:\n"
                for save_game in backup.save_games:
                    details += f"  • {save_game.name}\n"
            else:
                details += "No save games included.\n"

            self.view.update_backup_details(details)

        except Exception as e:
            self.logger.error(f"Error updating backup details: {e}")
            self.view.update_backup_details("Error loading backup details.")

    def _update_button_states(self):
        """Update the state of action buttons."""
        has_selection = self.selected_backup is not None
        self.view.update_button_states(has_selection)

    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0 # type: ignore
        return f"{size_bytes:.1f} TB"

    def _on_backup_selected(self, event=None):
        """Handle backup selection."""
        try:
            selection_index = self.view.get_selected_backup_index()
            
            if selection_index is not None and 0 <= selection_index < len(self.current_backups):
                self.selected_backup = self.current_backups[selection_index]
                self.logger.debug(f"Selected backup: {self.selected_backup.name}")
            else:
                self.selected_backup = None

            self._update_backup_details()
            self._update_button_states()

        except Exception as e:
            self.logger.error(f"Error handling backup selection: {e}")

    def _on_refresh_backups(self):
        """Handle refresh backups button click."""
        try:
            self.logger.info("Refreshing backup list")
            self._refresh_backup_list()
            self.selected_backup = None
            self._update_backup_details()
            self._update_button_states()

        except Exception as e:
            self.logger.error(f"Error refreshing backups: {e}")

    def _on_delete_backup(self):
        """Handle delete backup button click."""
        try:
            if not self.selected_backup:
                self.logger.warning("No backup selected for deletion")
                return

            backup_manager = get_backup_manager()
            backup_to_delete = self.selected_backup

            self.logger.info(f"Deleting backup: {backup_to_delete.name}")
            
            # Delete the backup
            backup_manager.delete_backup(backup_to_delete)
            
            # Clear selection and refresh UI
            self.selected_backup = None
            self._refresh_backup_list()
            self._update_backup_details()
            self._update_button_states()

        except BackupError as e:
            self.logger.error(f"Backup deletion failed: {e}")
        except Exception as e:
            self.logger.error(f"Error deleting backup: {e}")

    def _on_restore_backup(self):
        """Handle restore backup button click."""
        try:
            if not self.selected_backup:
                self.logger.warning("No backup selected for restoration")
                return

            backup_manager = get_backup_manager()
            backup_to_restore = self.selected_backup

            self.logger.info(f"Restoring backup: {backup_to_restore.name}")
            
            # Restore the backup
            backup_manager.restore_backup(backup_to_restore)

        except BackupError as e:
            self.logger.error(f"Backup restoration failed: {e}")
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")

    def _on_create_backup(self):
        """Handle create backup button click."""
        try:
            backup_name = self.view.get_backup_name_input()
            
            if not backup_name:
                self.logger.warning("No backup name provided")
                return

            installation_manager = get_installation_manager()
            backup_manager = get_backup_manager()
            
            current_game_type = installation_manager.get_current_game_type()

            self.logger.info(f"Creating backup: {backup_name}")
            
            # Create the backup
            backup_manager.create_backup(current_game_type, backup_name)
            
            # Clear input and refresh UI
            self.view.clear_backup_name_input()
            self._refresh_backup_list()

        except BackupError as e:
            self.logger.error(f"Backup creation failed: {e}")
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")

    # Event handlers for backup events
    def _on_current_game_type_changed(self, sender, **kwargs):
        """Handle current game type changed event."""
        try:
            old_game_type: Optional[GameType] = kwargs.get('old_game_type')
            new_game_type: Optional[GameType] = kwargs.get('new_game_type')

            if not new_game_type or not old_game_type or not isinstance(new_game_type, GameType) or not isinstance(old_game_type, GameType):
                return
            
            self.logger.info(f"Game type changed from {old_game_type.name if old_game_type else 'None'} to {new_game_type.name}")
            
            # Clear selection and refresh for new game type
            self.selected_backup = None
            self._refresh_backup_list()
            self._update_backup_details()
            self._update_button_states()

        except Exception as e:
            self.logger.error(f"Error handling game type changed event: {e}")

    def _on_backup_created(self, sender, **kwargs):
        """Handle backup created event."""
        try:
            backup = kwargs.get('backup')
            if backup:
                self.logger.info(f"Backup created: {backup.name}")

        except Exception as e:
            self.logger.error(f"Error handling backup created event: {e}")

    def _on_backup_deleted(self, sender, **kwargs):
        """Handle backup deleted event."""
        try:
            backup = kwargs.get('backup')
            if backup:
                self.logger.info(f"Backup deleted: {backup.name}")

        except Exception as e:
            self.logger.error(f"Error handling backup deleted event: {e}")

    def _on_backup_restored(self, sender, **kwargs):
        """Handle backup restored event."""
        try:
            backup = kwargs.get('backup')
            restored_count = kwargs.get('restored_count', 0)
            if backup:
                self.logger.info(f"Backup restored: {backup.name} ({restored_count} save games)")

        except Exception as e:
            self.logger.error(f"Error handling backup restored event: {e}")

    def _on_backup_list_refreshed(self, sender, **kwargs):
        """Handle backup list refreshed event."""
        try:
            game_type = kwargs.get('game_type')
            backup_count = kwargs.get('backup_count', 0)
            if game_type:
                self.logger.debug(f"Backup list refreshed for {game_type.name}: {backup_count} backups")

        except Exception as e:
            self.logger.error(f"Error handling backup list refreshed event: {e}")

    def _on_tab_changed(self, sender, **kwargs):
        """Handle tab changed event - refresh backup name when backup tab becomes active."""
        try:
            new_tab = kwargs.get('tab')
            if new_tab == 'backups':
                # Refresh the default backup name with current timestamp when tab becomes active
                self.view.refresh_default_backup_name()
                self.logger.debug("Refreshed backup name placeholder for backup tab")

        except Exception as e:
            self.logger.error(f"Error handling tab changed event: {e}")

    def shutdown(self):
        """Shutdown the controller and clean up resources."""
        try:
            self.logger.info("Shutting down backup tab controller...")

            # Unsubscribe from events
            self._unsubscribe_from_events()

            self.logger.info("Backup tab controller shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during backup tab controller shutdown: {e}")
