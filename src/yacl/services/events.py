"""
Event Management System for YACL

This module provides an event system to replace Godot's signals for component communication.
It uses the Blinker library for fast, reliable signal dispatching with weak reference support.
"""

import logging
from typing import Optional, Callable

from blinker import Namespace


class EventManager:
    """
    Central event management system for YACL using Blinker signals.

    This class provides a way for components to communicate without direct coupling,
    similar to Godot's signal system. It wraps Blinker's signal functionality to
    maintain compatibility with the existing YACL event API.
    """

    def __init__(self):
        """Initialize the event manager."""
        self.logger = logging.getLogger("YACL")

        # Create a Blinker namespace for YACL events
        self._namespace = Namespace()

        self.logger.info("Event manager initialized with Blinker backend")

    def subscribe(self, event_name: str, callback: Callable, weak: bool = True) -> bool:
        """
        Subscribe to an event.

        Args:
            event_name: Name of the event to subscribe to
            callback: Function to call when the event is emitted
            weak: Whether to use weak references (default: True)

        Returns:
            bool: True if subscription was successful
        """
        try:
            signal = self._namespace.signal(event_name)
            signal.connect(callback, weak=weak)

            self.logger.debug(f"Subscribed to event '{event_name}': {callback}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to subscribe to event '{event_name}': {e}")
            return False
    
    def unsubscribe(self, event_name: str, callback: Callable) -> bool:
        """
        Unsubscribe from an event.

        Args:
            event_name: Name of the event to unsubscribe from
            callback: Function to remove from subscribers

        Returns:
            bool: True if unsubscription was successful
        """
        try:
            signal = self._namespace.signal(event_name)

            signal.disconnect(receiver=callback)

            self.logger.debug(f"Unsubscribed from event '{event_name}': {callback}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unsubscribe from event '{event_name}': {e}")
            return False
    
    def emit(self, event_name: str, **kwargs) -> int:
        """
        Emit an event to all subscribers.

        Args:
            event_name: Name of the event to emit
            **kwargs: Keyword arguments to pass to callbacks

        Returns:
            int: Number of callbacks that were successfully called
        """
        try:
            signal = self._namespace.signal(event_name)

            results = signal.send(self, **kwargs)

            successful_calls = len(results)

            return successful_calls

        except Exception as e:
            self.logger.error(f"Failed to emit event '{event_name}': {e}")
            return 0
    
    def shutdown(self):
        """Shutdown the event manager."""
        try:
            self.logger.debug("Shutting down event manager...")
            self.logger.debug("Event manager shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during event manager shutdown: {e}")


# Common event names used throughout the application
class Events:
    """Common event names used throughout YACL."""
    
    # Application events
    APP_INITIALIZED = "app_initialized"
    APP_SHUTDOWN = "app_shutdown"
    APP_EXIT_REQUESTED = "app_exit_requested"
    
    # UI events
    WINDOW_CREATED = "window_created"
    WINDOW_CLOSED = "window_closed"
    TAB_CHANGED = "tab_changed"
    
    # Core system events
    SETTINGS_LOADED = "settings_loaded"
    SETTINGS_CHANGED = "settings_changed"
    
    # Manager events
    RELEASE_FETCH_STARTED = "release_fetch_started"
    RELEASE_FETCH_COMPLETED = "release_fetch_completed"
    RELEASE_SELECTED = "release_selected"
    RELEASE_DOWNLOAD_STARTED = "release_download_started"
    RELEASE_DOWNLOAD_COMPLETED = "release_download_completed"

    # Installation events
    INSTALLATION_STARTED = "installation_started"
    INSTALLATION_PROGRESS = "installation_progress"
    INSTALLATION_FINISHED = "installation_finished"
    INSTALLATION_REMOVED = "installation_removed"
    ACTIVE_INSTALLATION_CHANGED = "active_installation_changed"

    # Game type events
    CURRENT_GAME_TYPE_CHANGED = "current_game_type_changed"

    # Backup events
    BACKUP_CREATED = "backup_created"
    BACKUP_DELETED = "backup_deleted"
    BACKUP_RESTORED = "backup_restored"

    # Timeline events
    TIMELINE_CREATED = "timeline_created"
    TIMELINE_DELETED = "timeline_deleted"
    CHECKPOINT_CREATED = "checkpoint_created"
    CHECKPOINT_RESTORED = "checkpoint_restored"
    BRANCH_CREATED = "branch_created"
    BRANCH_SWITCHED = "branch_switched"
    BACKUP_LIST_REFRESHED = "backup_list_refreshed"

    # Download events
    DOWNLOAD_STARTED = "download_started"
    DOWNLOAD_FINISHED = "download_finished"
    DOWNLOAD_PROGRESS = "download_progress"

    # Status events
    STATUS_MESSAGE = "status_message"
    ERROR_OCCURRED = "error_occurred"


# Global event manager instance (will be initialized by the application)
event_manager: Optional[EventManager] = None


def get_event_manager() -> EventManager:
    """
    Get the global event manager instance.
    
    Returns:
        EventManager: Global event manager instance
        
    Raises:
        RuntimeError: If event manager hasn't been initialized
    """
    if event_manager is None:
        raise RuntimeError("Event manager not initialized")
    return event_manager


def initialize_event_manager() -> bool:
    """
    Initialize the global event manager instance.
        
    Returns:
        bool: True if initialization was successful
    """
    global event_manager
    try:
        event_manager = EventManager()
        return True
    except Exception as e:
        logging.getLogger("YACL").error(f"Failed to initialize global event manager: {e}")
        return False


def shutdown_event_manager():
    """Shutdown the global event manager instance."""
    global event_manager
    if event_manager:
        event_manager.shutdown()
        event_manager = None
