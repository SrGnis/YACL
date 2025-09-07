"""
Main Window for YACL

This module contains the main window implementation that provides the primary
user interface with tabbed layout and core functionality using Tkinter.
"""

import logging
from typing import Optional, Dict, Any
import tkinter as tk
from tkinter import ttk

from yacl.services.events import EventManager, Events
from yacl.views.tabs.game_tab import GameTab
from yacl.controllers.game_tab_controller import GameTabController


class MainWindow:
    """
    Main application window for YACL using Tkinter.

    This class manages the main window UI including:
    - Tabbed interface layout
    - Menu bar and toolbar
    - Status bar
    - Main content area
    """

    def __init__(self, event_manager: EventManager, root: tk.Tk):
        """
        Initialize the main window.

        Args:
            event_manager: Event manager for component communication
            root: The Tkinter root window
        """
        self.logger = logging.getLogger("YACL")
        self.event_manager = event_manager

        # Tkinter components
        self.root = root
        self.main_frame: Optional[ttk.Frame] = None
        self.notebook: Optional[ttk.Notebook] = None
        self.status_frame: Optional[ttk.Frame] = None
        self.status_log: Optional[tk.Text] = None
        self.status_scrollbar: Optional[ttk.Scrollbar] = None
        self.version_text: Optional[ttk.Label] = None

        # Status log configuration
        self.max_log_lines: int = 500
        self.trim_to_lines: int = 250

        # Shutdown flag to prevent UI updates during shutdown
        self.is_shutting_down: bool = False

        # Window configuration
        self.config = {
            'title': 'YACL - Yet Another Cataclysm Launcher',
        }

        # Tab configuration
        self.tabs = {
            'game': {'label': 'Game', 'enabled': True},
            #'mods': {'label': 'Mods', 'enabled': False},
            #'soundpacks': {'label': 'Soundpacks', 'enabled': False},
            #'fonts': {'label': 'Fonts', 'enabled': False},
            #'backups': {'label': 'Backups', 'enabled': False},
            'settings': {'label': 'Settings', 'enabled': True},
        }

        self._current_tab = 'game'
        self._tab_instances = {}
        self._tab_frames = {} 

        self.logger.info("Main window initialized")
    
    def initialize(self) -> bool:
        """
        Initialize the main window and create the UI.

        Returns:
            bool: True if initialization was successful
        """
        try:
            self.logger.info("Creating main window UI...")

            self.root.title(self.config['title'])

            self.main_frame = ttk.Frame(self.root)
            self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            self._create_tab_interface()

            self._create_status_log()

            self._setup_event_handlers()

            self.event_manager.emit(Events.WINDOW_CREATED, window=self)

            self.logger.info("Main window created successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize main window: {e}")
            return False
    
    def shutdown(self):
        """Shutdown the main window and clean up resources."""
        try:
            self.logger.info("Shutting down main window...")

            # Set shutdown flag to prevent further UI updates
            self.is_shutting_down = True

            # TODO: refactor this
            for tab_name, tab_instance in self._tab_instances.items():
                try:
                    if isinstance(tab_instance, dict):
                        # New MVC format: shutdown both controller and view
                        if 'controller' in tab_instance and hasattr(tab_instance['controller'], 'shutdown'):
                            tab_instance['controller'].shutdown()
                        if 'view' in tab_instance and hasattr(tab_instance['view'], 'shutdown'):
                            tab_instance['view'].shutdown()
                    elif hasattr(tab_instance, 'shutdown'):
                        # Old format: direct tab instance
                        tab_instance.shutdown()
                except Exception as e:
                    self.logger.error(f"Error shutting down tab '{tab_name}': {e}")
            
            self._tab_instances.clear()
            
            self.event_manager.emit(Events.WINDOW_CLOSED, window=self)
            
            self.logger.info("Main window shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during main window shutdown: {e}")



    def _create_tab_interface(self):
        """Create the main tabbed interface."""
        try:
            self.notebook = ttk.Notebook(self.main_frame)
            self.notebook.pack(fill=tk.BOTH, expand=True)

            self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

            for tab_id, tab_config in self.tabs.items():
                tab_frame = ttk.Frame(self.notebook)
                self._tab_frames[tab_id] = tab_frame

                self.notebook.add(tab_frame, text=tab_config['label'])

                self._create_tab_content(tab_id, tab_frame)

        except Exception as e:
            self.logger.error(f"Failed to create tab interface: {e}")
    
    def _create_tab_content(self, tab_id: str, tab_frame: ttk.Frame):
        """
        Create content for a specific tab.

        Args:
            tab_id: ID of the tab to create content for
            tab_frame: The frame to create content in
        """
        try:
            if tab_id == 'game':
                self._create_game_tab_content(tab_frame)
            elif tab_id == 'mods':
                self._create_mods_tab_content(tab_frame)
            elif tab_id == 'soundpacks':
                self._create_soundpacks_tab_content(tab_frame)
            elif tab_id == 'fonts':
                self._create_fonts_tab_content(tab_frame)
            elif tab_id == 'backups':
                self._create_backups_tab_content(tab_frame)
            elif tab_id == 'settings':
                self._create_settings_tab_content(tab_frame)
            else:
                ttk.Label(tab_frame, text=f"Content for {tab_id} tab will be implemented here.").pack(pady=20)

        except Exception as e:
            self.logger.error(f"Failed to create content for tab '{tab_id}': {e}")
    
    def _create_game_tab_content(self, tab_frame: ttk.Frame):
        """Create content for the game tab with MVC pattern."""
        try:
            game_tab_view = GameTab(parent_frame=tab_frame, event_manager=self.event_manager)
            game_tab_view.create_ui()

            game_tab_controller = GameTabController(view=game_tab_view, event_manager=self.event_manager)

            game_tab_controller.refresh_ui()

            self._tab_instances['game'] = {
                'view': game_tab_view,
                'controller': game_tab_controller
            }

        except Exception as e:
            self.logger.error(f"Failed to create game tab: {e}")
            # Fallback to placeholder content
            ttk.Label(tab_frame, text="Game Management", font=('TkDefaultFont', 12, 'bold')).pack(pady=10)
            ttk.Separator(tab_frame, orient='horizontal').pack(fill=tk.X, pady=5)
            ttk.Label(tab_frame, text="Failed to load game tab. Please check the logs.").pack(pady=5)
            ttk.Label(tab_frame, text=f"Error: {e}", foreground='red').pack(pady=5)
    
    def _create_mods_tab_content(self, tab_frame: ttk.Frame):
        """Create content for the mods tab."""
        ttk.Label(tab_frame, text="Mod Management", font=('TkDefaultFont', 12, 'bold')).pack(pady=10)
        ttk.Separator(tab_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        ttk.Label(tab_frame, text="Mod management functionality will be implemented here.").pack(pady=20)

    def _create_soundpacks_tab_content(self, tab_frame: ttk.Frame):
        """Create content for the soundpacks tab."""
        ttk.Label(tab_frame, text="Soundpack Management", font=('TkDefaultFont', 12, 'bold')).pack(pady=10)
        ttk.Separator(tab_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        ttk.Label(tab_frame, text="Soundpack management functionality will be implemented here.").pack(pady=20)

    def _create_fonts_tab_content(self, tab_frame: ttk.Frame):
        """Create content for the fonts tab."""
        ttk.Label(tab_frame, text="Font Management", font=('TkDefaultFont', 12, 'bold')).pack(pady=10)
        ttk.Separator(tab_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        ttk.Label(tab_frame, text="Font management functionality will be implemented here.").pack(pady=20)

    def _create_backups_tab_content(self, tab_frame: ttk.Frame):
        """Create content for the backups tab."""
        ttk.Label(tab_frame, text="Backup Management", font=('TkDefaultFont', 12, 'bold')).pack(pady=10)
        ttk.Separator(tab_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        ttk.Label(tab_frame, text="Backup management functionality will be implemented here.").pack(pady=20)
    
    def _create_settings_tab_content(self, tab_frame: ttk.Frame):
        """Create content for the settings tab with MVC pattern."""
        try:
            from yacl.views.tabs.settings_tab import SettingsTab
            from yacl.controllers.settings_tab_controller import SettingsTabController

            settings_tab_view = SettingsTab(parent_frame=tab_frame, event_manager=self.event_manager)
            settings_tab_view.create_ui()

            settings_tab_controller = SettingsTabController(view=settings_tab_view, event_manager=self.event_manager)

            self._tab_instances['settings'] = {
                'view': settings_tab_view,
                'controller': settings_tab_controller
            }

        except Exception as e:
            self.logger.error(f"Failed to create settings tab content: {e}")
            # Fallback to placeholder content
            ttk.Label(tab_frame, text="Application Settings", font=('TkDefaultFont', 12, 'bold')).pack(pady=10)
            ttk.Separator(tab_frame, orient='horizontal').pack(fill=tk.X, pady=5)
            ttk.Label(tab_frame, text="Settings management functionality failed to load.").pack(pady=20)
    
    def _create_status_log(self):
        """Create the status log widget at the bottom of the window."""
        try:
            ttk.Separator(self.main_frame, orient='horizontal').pack(fill=tk.X, pady=(5, 0))

            self.status_frame = ttk.Frame(self.main_frame)
            self.status_frame.pack(fill=tk.X, pady=5)

            header_frame = ttk.Frame(self.status_frame)
            header_frame.pack(fill=tk.X, pady=(0, 2))

            ttk.Label(header_frame, text="Status Log:", font=('TkDefaultFont', 9, 'bold')).pack(side=tk.LEFT)

            self.version_text = ttk.Label(header_frame, text="YACL")
            self.version_text.pack(side=tk.RIGHT)

            log_frame = ttk.Frame(self.status_frame)
            log_frame.pack(fill=tk.BOTH, expand=True)

            self.status_log = tk.Text(
                log_frame,
                height=6,  # Show about 6 lines of status messages
                wrap=tk.WORD,
                state=tk.DISABLED,  # Read-only
                font=('TkDefaultFont', 8),
                bg='black',
                relief=tk.SUNKEN,
                bd=1
            )

            self.status_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.status_log.yview)
            self.status_log.configure(yscrollcommand=self.status_scrollbar.set)

            self.status_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            self._configure_status_log_tags()

            self._setup_status_log_context_menu()

            self._load_existing_status_messages()

        except Exception as e:
            self.logger.error(f"Failed to create status log: {e}")

    def _configure_status_log_tags(self):
        """Configure text tags for different message types in the status log."""
        try:
            if not self.status_log:
                return

            self.status_log.tag_configure("info", foreground="white")
            self.status_log.tag_configure("warning", foreground="orange")
            self.status_log.tag_configure("error", foreground="red")
            self.status_log.tag_configure("debug", foreground="lightgray")
            self.status_log.tag_configure("success", foreground="green")

        except Exception as e:
            self.logger.error(f"Failed to configure status log tags: {e}")

    def _setup_status_log_context_menu(self):
        """Setup right-click context menu for the status log."""
        try:
            if not self.status_log:
                return

            self.status_log_menu = tk.Menu(self.status_log, tearoff=0)
            self.status_log_menu.add_command(label="Clear Log", command=self.clear_status_log)
            self.status_log_menu.add_separator()
            self.status_log_menu.add_command(label="Copy All", command=self._copy_all_log_text)

            # Status module removed - skip debug toggle

            self.status_log.bind("<Button-3>", self._show_status_log_context_menu)

        except Exception as e:
            self.logger.error(f"Failed to setup status log context menu: {e}")

    def _show_status_log_context_menu(self, event):
        """Show the context menu for the status log."""
        try:
            self.status_log_menu.post(event.x_root, event.y_root)
        except Exception as e:
            self.logger.error(f"Failed to show status log context menu: {e}")

    def _copy_all_log_text(self):
        """Copy all text from the status log to clipboard."""
        try:
            if not self.status_log:
                return

            log_text = self.status_log.get("1.0", tk.END)

            self.status_log.clipboard_clear()
            self.status_log.clipboard_append(log_text)

        except Exception as e:
            self.logger.error(f"Failed to copy log text: {e}")

    def _load_existing_status_messages(self):
        """Load existing status messages from the status manager into the log."""
        try:
            if not self.status_log:
                return

            # Status module removed - skip loading existing messages
            pass

        except Exception as e:
            logging.getLogger("YACL").error(f"Failed to load existing status messages: {e}")

    def _add_message_to_log(self, message):
        """Add a single message to the status log - simple and direct."""
        try:
            if not self.status_log or self.is_shutting_down:
                return

            # Use after_idle to ensure we're on the main thread
            self.root.after_idle(lambda: self._append_message_now(message))

        except Exception as e:
            # Don't log errors during shutdown to avoid infinite loops
            if not self.is_shutting_down:
                logging.getLogger("YACL").error(f"Failed to schedule message append: {e}")

    def _add_string_message_to_log(self, message_text, message_type):
        """Add a string message from logging handler to the status log."""
        try:
            if not self.status_log or self.is_shutting_down:
                return

            # Use after_idle to ensure we're on the main thread
            self.root.after_idle(lambda: self._append_string_message_now(message_text, message_type))

        except Exception as e:
            # Don't log errors during shutdown to avoid infinite loops
            if not self.is_shutting_down:
                logging.getLogger("YACL").error(f"Failed to schedule string message append: {e}")

    def _append_message_now(self, message):
        """Append message directly to the log widget (runs on main thread)."""
        try:
            if not self.status_log:
                return

            # Ensure we have a proper StatusMessage object
            if hasattr(message, 'message_type') and hasattr(message, 'timestamp'):
                # Format the message manually since status module is removed
                timestamp_str = message.timestamp.strftime("%H:%M:%S")
                formatted_message = f"[{timestamp_str}] {message.message}"
                tag = message.message_type.value
            else:
                # Fallback for unexpected message types
                formatted_message = str(message)
                tag = "info"

            # Add to log
            self.status_log.config(state=tk.NORMAL)
            self.status_log.insert(tk.END, formatted_message + "\n", tag)

            # Trim if needed
            self._trim_log_if_needed()

            # Keep scrolled to bottom
            self.status_log.see(tk.END)

            # Make read-only again
            self.status_log.config(state=tk.DISABLED)

        except Exception as e:
            logging.getLogger("YACL").error(f"Failed to append message to log: {e}")

    def _append_string_message_now(self, message_text, message_type):
        """Append string message from logging handler directly to the log widget (runs on main thread)."""
        try:
            if not self.status_log:
                return

            # Map message type to tag
            tag = self._get_message_tag(message_type)

            # Add to log
            self.status_log.config(state=tk.NORMAL)
            self.status_log.insert(tk.END, message_text + "\n", tag)

            # Trim if needed
            self._trim_log_if_needed()

            # Keep scrolled to bottom
            self.status_log.see(tk.END)

            # Make read-only again
            self.status_log.config(state=tk.DISABLED)

        except Exception as e:
            logging.getLogger("YACL").error(f"Failed to append string message to log: {e}")

    def _get_message_tag(self, message_type):
        """Get the appropriate tag for a message type."""
        type_mapping = {
            'debug': 'debug',
            'info': 'info',
            'warning': 'warning',
            'error': 'error',
            'critical': 'error',
        }
        return type_mapping.get(message_type.lower(), 'info')

    def _trim_log_if_needed(self):
        """Trim the status log if it exceeds the maximum number of lines."""
        try:
            if not self.status_log:
                return

            end_index = self.status_log.index(tk.END)
            current_lines = int(end_index.split('.')[0]) - 1

            if current_lines > self.max_log_lines:

                lines_to_remove = current_lines - self.trim_to_lines

                self.status_log.delete("1.0", f"{lines_to_remove + 1}.0")

                first_line = self.status_log.get("1.0", "2.0").strip()
                if not first_line.startswith("--- Log trimmed"):
                    self.status_log.insert("1.0", "--- Log trimmed (older messages removed) ---\n", "info")

        except Exception as e:
            logging.getLogger("YACL").error(f"Failed to trim status log: {e}")

    def clear_status_log(self):
        """Clear all messages from the status log."""
        try:
            if not self.status_log:
                return

            self.status_log.config(state=tk.NORMAL)

            self.status_log.delete("1.0", tk.END)

            self.status_log.insert(tk.END, "--- Status log cleared ---\n", "info")

            self.status_log.config(state=tk.DISABLED)

        except Exception as e:
            logging.getLogger("YACL").error(f"Failed to clear status log: {e}")

    def _setup_event_handlers(self):
        """Setup event handlers for the main window."""
        try:
            self.event_manager.subscribe(Events.STATUS_MESSAGE, self._on_status_message)
            
        except Exception as e:
            self.logger.error(f"Failed to setup event handlers: {e}")
    
    def _on_tab_changed(self, event):
        """Handle tab change events."""
        try:
            current_index = self.notebook.index(self.notebook.select()) # type: ignore
            tab_names = list(self.tabs.keys())

            if current_index < len(tab_names):
                current_tab = tab_names[current_index]
                self.logger.debug(f"Tab changed to: {current_tab}")

                self.event_manager.emit(Events.TAB_CHANGED, tab=current_tab)

        except Exception as e:
            self.logger.error(f"Error handling tab change: {e}")

    def _on_status_message(self, sender, **kwargs):
        """Handle status message events."""
        try:
            # Skip processing if shutting down
            if self.is_shutting_down:
                return

            _ = sender
            message = kwargs.get('message', None)
            message_type = kwargs.get('message_type', None)

            if message:
                # Handle both StatusMessage objects and string messages from logging handler
                if isinstance(message, str) and message_type:
                    # Handle string message from logging handler
                    self._add_string_message_to_log(message, message_type)
                else:
                    # Handle StatusMessage objects directly (if any still exist)
                    self._add_message_to_log(message)

        except Exception as e:
            # Don't log errors during shutdown to avoid infinite loops
            if not self.is_shutting_down:
                logging.getLogger("YACL").error(f"Error updating status message: {e}")