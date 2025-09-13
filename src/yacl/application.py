"""
YACL Application Framework

This module contains the main application class that manages the overall application
lifecycle, window management, and UI framework using Tkinter.
"""

import logging
from pathlib import Path
from typing import Optional

from yacl.services.events import EventManager, Events
from yacl.views.main_window import MainWindow
from yacl.ui.window_manager import WindowManager
from yacl.ui.startup_window import StartupWindow
from yacl.services import settings
from yacl.services import downloader, events, paths
from yacl.services.cataclysm_db import initialize_cataclysm_db_manager, shutdown_cataclysm_db_manager, get_cataclysm_db_manager
from yacl.services.icon_service import initialize_icon_service, shutdown_icon_service
from yacl.models.installation_manager import initialize_installation_manager, shutdown_installation_manager
from yacl.models.release_manager import initialize_release_manager, shutdown_release_manager
from yacl.models.backup_manager import initialize_backup_manager, shutdown_backup_manager
from yacl.utils.logging_handler import add_event_manager_handler_to_logger


class YACLApplication:
    """
    Main application class for YACL.
    """

    logger: logging.Logger

    event_manager: EventManager
    window_manager: WindowManager
    path_manager: paths.PathManager
    app_settings: settings.SettingsManager
    main_window: MainWindow
    startup_window: Optional[StartupWindow]
    _is_running: bool
    _exit_code: int
    
    def __init__(self):
        """Initialize the YACL application."""
        self.logger = logging.getLogger("YACL")

        self._is_running = False
        self._exit_code = 0
        self.startup_window = None

        self.config = {
            'title': 'YACL - Yet Another Cataclysm Launcher',
            'docking': True,
            'docking_space': False,
        }

        if not self.initialize():
            self.logger.error("Application initialization failed")
    
    def initialize(self) -> bool:
        """
        Initialize the application and all its components.
        """
        try:
            self.logger.info("Initializing YACL Application...")

            if not self._initialize_core_systems():
                return False
            
            if not self._initialize_managers():
                return False

            if not self._initialize_main_window():
                return False

            self.logger.info("YACL Application initialization complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            return False
    
    def run(self) -> int:
        """
        Run the main application loop.

        Returns:
            int: Exit code (0 for success, non-zero for error)
        """
        try:

            self.logger.info("YACL initialization complete, starting main loop...")
            self._is_running = True

            self.event_manager.emit(Events.APP_INITIALIZED)

            # Start the Tkinter main loop
            try:
                root = self.window_manager.get_root()
                if root:
                    self.logger.info("Starting Tkinter main loop...")

                    root.mainloop()

                    self.logger.info("Tkinter main loop ended")
                else:
                    self.logger.error("No root window available for main loop")
                    self._exit_code = 1

            except Exception as e:
                self.logger.error(f"Error in Tkinter main loop: {e}")
                self._exit_code = 1

            return self._exit_code

        except Exception as e:
            self.logger.error(f"Critical error in application run: {e}")
            try:
                self._show_error_dialog("Critical Error",
                                        f"A critical error occurred: {str(e)}")
            except:
                pass  # Don't let error dialog errors crash the app
            return 1
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the application and clean up resources."""
        try:
            self.logger.info("Shutting down YACL Application...")
            self._is_running = False
            
            self.event_manager.emit(Events.APP_SHUTDOWN)

            # Shutdown managers first to stop background threads
            self._shutdown_managers()

            # Close startup window if still open
            if self.startup_window:
                self.startup_window.close()
                self.startup_window = None

            if self.main_window:
                self.main_window.shutdown()

            if self.window_manager:
                self.window_manager.shutdown()

            self._shutdown_remaining_core_systems()


            self.logger.info("YACL Application shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during application shutdown: {e}")
    
    def request_exit(self, exit_code: int = 0):
        """
        Request application exit with the specified exit code.
        
        Args:
            exit_code: Exit code to return (0 for success)
        """
        self.logger.info(f"Exit requested with code: {exit_code}")
        self._exit_code = exit_code
        root = self.window_manager.get_root()
        if root and root.winfo_exists():
            root.quit()  # Exit the mainloop

    def _initialize_core_systems(self) -> bool:
        """Initialize core systems"""
        try:
            self.logger.info("Initializing core systems...")

            if not paths.initialize_paths("YACL"):
                self.logger.error("Failed to initialize path manager")
                return False
            self.path_manager = paths.get_paths()
            
            if not settings.initialize_settings(self.path_manager.config_dir):
                self.logger.error("Failed to initialize settings manager")
                return False
            self.app_settings = settings.get_settings()
            
            if not events.initialize_event_manager():
                self.logger.error("Failed to initialize event manager")
                return False
            self.event_manager = events.get_event_manager()

            if not self.initialize_logging():
                self.logger.error("Failed to initialize logging handler")
                return False

            if not self._setup_event_handlers():
                self.logger.error("Failed to setup event handlers")
                return False

            if not downloader.initialize_download_manager(self.event_manager):
                self.logger.error("Failed to initialize download manager")
                return False

            if not initialize_icon_service():
                self.logger.error("Failed to initialize icon service")
                return False

            # TODO: move window setup to its own method and after it call setup_catacylsm_db
            window_state_file = self.path_manager.config_dir / "window_state.json"
            if not self._initialize_window_manager(window_state_file):
                self.logger.error("Failed to initialize window manager with settings")
                return False

            if not self._initialize_root_window():
                return False
            
            self._show_startup_window()

            if not self._setup_cataclysm_db():
                return False

            self.logger.info("YACL initialized successfully!")

            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize core systems: {e}")
            return False
        
    def initialize_logging(self) -> bool:
        """
        Initialize the logging system.
        
        This method sets up the logging system, including:
        - File logging
        - Event manager logging handler

        Returns:
            bool: True if initialization was successful
        """
        try:
            self.logger.info("Initializing logging system...")
            
            self.logger.setLevel(logging.DEBUG if self.app_settings.read("debug_mode") else logging.INFO)

            # Create a log file handler
            # TODO: Rotating file handler
            log_file = self.path_manager.logs_dir / "yacl.log"
            file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
            file_handler.setLevel(self.logger.level)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(module)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'
            ))
            self.logger.addHandler(file_handler)

            # Create event manager logging handler
            add_event_manager_handler_to_logger(self.logger, self.event_manager, self.logger.level,
                logging.Formatter('%(asctime)s - [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))

            return True
        
        except Exception as e:
            self.logger.error(f"Failed to initialize logging handler: {e}")
            return False
        
    def _initialize_window_manager(self, state_file_path: Optional[Path] = None) -> bool:
        """Initialize the window manager."""
        try:
            self.logger.info("Initializing window manager...")
            self.window_manager = WindowManager(self.event_manager)
            return self.window_manager.initialize(state_file_path)

        except Exception as e:
            self.logger.error(f"Failed to initialize window manager: {e}")
            return False

    def _initialize_managers(self) -> bool:
        """Initialize feature managers (release, mod, soundpack, etc.)."""
        try:
            self.logger.info("Initializing managers...")

            if not initialize_release_manager(self.event_manager):
                self.logger.error("Failed to initialize release manager")
                return False

            
            if not initialize_installation_manager(self.event_manager):
                self.logger.error("Failed to initialize installation manager")
                return False

            if not initialize_backup_manager(self.event_manager):
                self.logger.error("Failed to initialize backup manager")
                return False

            # TODO: Initialize mod manager
            # TODO: Initialize soundpack manager
            # TODO: Initialize font manager

            self.logger.info("Managers initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize managers: {e}")
            return False

    def _initialize_root_window(self) -> bool:
        """Initialize the Tkinter root window."""
        try:
            self.logger.info("Creating root window...")
            return self.window_manager.create_root_window(self.config['title'])

        except Exception as e:
            self.logger.error(f"Failed to initialize root window: {e}")
            return False
        

    
    def _initialize_main_window(self) -> bool:
        """Initialize the main application window."""
        try:
            self.logger.info("Creating main window...")
            root = self.window_manager.get_root()
            if not root:
                self.logger.error("No root window available for main window")
                return False

            self.main_window = MainWindow(self.event_manager, root)
            return self.main_window.initialize()

        except Exception as e:
            self.logger.error(f"Failed to initialize main window: {e}")
            return False
        
    def _setup_event_handlers(self) -> bool:
        """Setup application-level event handlers."""
        try:
            self.event_manager.subscribe(Events.APP_EXIT_REQUESTED, self._on_exit_requested)
            self.event_manager.subscribe(Events.APP_INITIALIZED, self._on_app_initialized)

            return True
        except Exception as e:
            self.logger.error(f"Failed to setup event handlers: {e}")
            return False
        
    def _setup_cataclysm_db(self) -> bool:
        """Setup database for Cataclysm."""
        try:
            self.logger.info("Setting up Cataclysm database...")

            # Check if Cataclysm database is enabled in settings
            if not self.app_settings.read("enable_cataclysm_db", True):
                self.logger.info("Cataclysm database is disabled in settings, skipping initialization")
                return True

            # Initialize the database manager
            if not initialize_cataclysm_db_manager():
                self.logger.error("Failed to initialize Cataclysm database manager")
                return False

            # Check for database updates
            db_manager = get_cataclysm_db_manager()

            # Perform database update check (non-blocking for startup)
            try:
                db_manager.check_and_update_databases()
            except Exception as e:
                self.logger.warning(f"Database update check failed, continuing with local data: {e}")

            self.logger.info("Cataclysm database setup completed")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Cataclysm database: {e}")
            return False

    def _show_startup_window(self):
        """Show the startup window during initialization."""
        try:
            if self.window_manager:
                root = self.window_manager.get_root()
                if root:
                    self.startup_window = StartupWindow(root)
                    self.startup_window.show()
                    self.logger.info("Startup window displayed")
        except Exception as e:
            self.logger.error(f"Failed to show startup window: {e}")
            # Don't fail initialization if startup window fails

    def _on_app_initialized(self, sender, **kwargs):
        """Handle APP_INITIALIZED event by closing the startup window."""
        _ = sender, kwargs
        try:
            if self.startup_window:
                self.startup_window.close()
                self.startup_window = None
                self.logger.info("Startup window closed")
        except Exception as e:
            self.logger.error(f"Failed to close startup window: {e}")

    def _on_exit_requested(self, sender, **kwargs):
        """Handle application exit requests."""
        _ = sender, kwargs
        self.request_exit(0)

    def _show_error_dialog(self, title: str, message: str):
        """
        Show an error dialog to the user.

        Args:
            title: Dialog title
            message: Error message
        """
        try:
            root = self.window_manager.get_root()
            if root and root.winfo_exists():
                from tkinter import messagebox
                messagebox.showerror(title, message)
            else:
                print(f"ERROR - {title}: {message}")

        except Exception as e:
            print(f"ERROR - {title}: {message}")
            print(f"(Also failed to show error dialog: {e})")

    def _shutdown_managers(self):
        """Shutdown feature managers."""
        try:
            self.logger.info("Shutting down managers...")
            shutdown_installation_manager()

            shutdown_release_manager()

            shutdown_backup_manager()

            # Only shutdown database manager if it was initialized
            if self.app_settings.read("enable_cataclysm_db", True):
                shutdown_cataclysm_db_manager()

            # TODO: Shutdown other managers when implemented

        except Exception as e:
            self.logger.error(f"Error shutting down managers: {e}")

    def _shutdown_remaining_core_systems(self):
        """Shutdown remaining core systems after managers are shut down."""
        try:
            self.logger.info("Shutting down core systems...")

            downloader.shutdown_download_manager()

            shutdown_icon_service()

            settings.shutdown_settings()

            paths.shutdown_paths()

        except Exception as e:
            self.logger.error(f"Error shutting down core systems: {e}")
