"""
Window Management for YACL

This module provides window management functionality including root window setup,
window sizing, positioning, and state management using Tkinter.
"""

import logging
import json
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import tkinter as tk

from yacl.services.events import EventManager, Events
from yacl.utils.helpers import get_resource_base_path


class WindowManager:
    """
    Window management system for YACL using Tkinter.

    This class handles:
    - Window state persistence (size, position)
    - Root window management
    - Window scaling and DPI handling
    - Multi-monitor support
    """

    def __init__(self, event_manager: EventManager):
        """
        Initialize the window manager.

        Args:
            event_manager: Event manager for component communication
        """
        self.logger = logging.getLogger("YACL")
        self.event_manager = event_manager

        # Default window configuration
        self.default_config = {
            'width': 1200,
            'height': 800,
            'min_width': 800,
            'min_height': 600,
            'x_pos': -1,  # -1 means center
            'y_pos': -1,  # -1 means center
            'maximized': False,
            'decorated': True,
            'resizable': True,
            'always_on_top': False,
        }

        # Current window state
        self.current_state = self.default_config.copy()

        # Window state file path
        self.state_file: Optional[Path] = None

        # Tkinter root window
        self.root: Optional[tk.Tk] = None

        self.logger.info("Window manager initialized")
    
    def initialize(self, state_file_path: Optional[Path] = None) -> bool:
        """
        Initialize the window manager and load saved state.
        
        Args:
            state_file_path: Path to the window state file
            
        Returns:
            bool: True if initialization was successful
        """
        try:
            self.logger.info("Initializing window manager...")
            
            if state_file_path:
                self.logger.info(f"Loading window state from {state_file_path}")
                self.state_file = state_file_path
                self._load_window_state()

            self.logger.info(f"Status file path: {self.state_file}")
            
            self._setup_event_handlers()
            
            self.logger.info("Window manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize window manager: {e}", exc_info=True)
            return False
    
    def create_root_window(self, title: str = "YACL") -> bool:
        """
        Create and configure the main Tkinter root window.

        Args:
            title: Window title

        Returns:
            bool: True if root window was created successfully
        """
        try:
            self.logger.info("Creating root window...")

            # Create the root window
            self.root = tk.Tk()
            self.root.title(title)

            # Calculate window position
            x_pos = self.current_state['x_pos']
            y_pos = self.current_state['y_pos']

            # Import the Azure theme
            # Handle both development and compiled executable paths
            base_path = get_resource_base_path()

            azure_theme_path = base_path / "assets" / "themes" / "Azure-ttk-theme" / "azure.tcl"

            if azure_theme_path.exists():
                self.root.tk.call("source", str(azure_theme_path))
                self.root.tk.call("set_theme", "dark")
            else:
                self.logger.warning(f"Azure theme file not found at: {azure_theme_path}")

            if x_pos == -1 or y_pos == -1:
                # Center the window
                x_pos, y_pos = self._calculate_center_position()

            # Set window geometry
            geometry = f"{self.current_state['width']}x{self.current_state['height']}+{x_pos}+{y_pos}"
            self.root.geometry(geometry)

            # Set minimum size
            self.root.minsize(self.current_state['min_width'], self.current_state['min_height'])

            # Configure window properties
            self.root.resizable(self.current_state['resizable'], self.current_state['resizable'])

            if self.current_state['always_on_top']:
                self.root.attributes('-topmost', True)

            if self.current_state['maximized']:
                self.root.state('zoomed')  # Windows/Linux
                # For macOS, use: self.root.attributes('-zoomed', True)

            # Setup window close protocol
            # This allows us to intercept the close event and save the window state
            self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

            self.logger.info(f"Root window created: {self.current_state['width']}x{self.current_state['height']}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create root window: {e}", exc_info=True)
            return False
    
    def save_window_state(self):
        """Save the current window state to file."""
        try:
            if not self.state_file:
                self.logger.warning("No state file available, skipping state save")
                return


            if not self.root:
                self.logger.warning("No root window available, skipping state save")
                return

            # Get current window state
            if self.root.winfo_exists():
                # Get window geometry
                geometry = self.root.geometry()
                # Parse geometry string: "widthxheight+x+y"
                size_part, pos_part = geometry.split('+', 1)
                width, height = map(int, size_part.split('x'))
                x_pos = int(pos_part.split('+')[0])
                y_pos = int(pos_part.split('+')[1])

                # Check if maximized
                maximized = self.root.state() == 'zoomed'

                self.current_state.update({
                    'width': width,
                    'height': height,
                    'x_pos': x_pos,
                    'y_pos': y_pos,
                    'maximized': maximized,
                })
            else:
                # Window doesn't exist, use default values
                self.logger.warning("Window does not exist, using default values for state")

            # Save to file
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(self.current_state, f, indent=2)

            self.logger.debug(f"Window state saved to {self.state_file}")

        except Exception as e:
            self.logger.error(f"Failed to save window state: {e}")
    
    def _load_window_state(self):
        """Load window state from file."""
        try:
            if not self.state_file or not self.state_file.exists():
                self.logger.info("No window state file found, using defaults")
                return
            
            with open(self.state_file, 'r') as f:
                saved_state = json.load(f)
            
            # Validate and merge saved state with defaults
            for key, value in saved_state.items():
                if key in self.default_config:
                    self.current_state[key] = value
            
            # Validate window dimensions
            self._validate_window_dimensions()
            
            self.logger.info(f"Window state loaded from {self.state_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to load window state: {e}")
            # Use defaults on error
            self.current_state = self.default_config.copy()
    
    def _validate_window_dimensions(self):
        """Validate and fix window dimensions if they're invalid."""
        try:
            # Ensure minimum dimensions
            if self.current_state['width'] < self.current_state['min_width']:
                self.current_state['width'] = self.current_state['min_width']
            
            if self.current_state['height'] < self.current_state['min_height']:
                self.current_state['height'] = self.current_state['min_height']
            
        except Exception as e:
            self.logger.error(f"Error validating window dimensions: {e}")
    
    def _calculate_center_position(self) -> Tuple[int, int]:
        """
        Calculate the center position for the window.

        Returns:
            Tuple[int, int]: X and Y position for centering the window
        """
        try:
            # Get screen dimensions
            if self.root:
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
            else:
                # Create temporary root to get screen dimensions
                temp_root = tk.Tk()
                temp_root.withdraw()  # Hide the window
                screen_width = temp_root.winfo_screenwidth()
                screen_height = temp_root.winfo_screenheight()
                temp_root.destroy()

            x_pos = (screen_width - self.current_state['width']) // 2
            y_pos = (screen_height - self.current_state['height']) // 2

            return max(0, x_pos), max(0, y_pos)

        except Exception as e:
            self.logger.error(f"Error calculating center position: {e}")
            return 100, 100  # Fallback position
    
    def _setup_event_handlers(self):
        """Setup event handlers for window management."""
        try:
            self.event_manager.subscribe(Events.APP_SHUTDOWN, self._on_app_shutdown)
            
        except Exception as e:
            self.logger.error(f"Failed to setup event handlers: {e}")
    
    def _on_app_shutdown(self, sender, **kwargs):
        """Handle application shutdown event."""
        _ = sender, kwargs
        self.save_window_state()

    def _on_window_close(self):
        """Handle window close event."""
        try:
            self.save_window_state()
            self.event_manager.emit(Events.APP_EXIT_REQUESTED)
        except Exception as e:
            self.logger.error(f"Error handling window close: {e}")
    
    def get_window_state(self) -> Dict[str, Any]:
        """
        Get the current window state.
        
        Returns:
            Dict[str, Any]: Current window state
        """
        return self.current_state.copy()
    
    def set_window_state(self, state: Dict[str, Any]):
        """
        Set the window state.
        
        Args:
            state: New window state
        """
        try:
            # Validate and update state
            for key, value in state.items():
                if key in self.default_config:
                    self.current_state[key] = value
            
            self._validate_window_dimensions()
            
        except Exception as e:
            self.logger.error(f"Error setting window state: {e}")
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        try:
            if self.root and self.root.winfo_exists():
                current_state = self.root.state()
                if current_state == 'zoomed':
                    self.root.state('normal')
                else:
                    self.root.state('zoomed')

        except Exception as e:
            self.logger.error(f"Error toggling fullscreen: {e}")

    def center_window(self):
        """Center the window on the screen."""
        try:
            if self.root and self.root.winfo_exists():
                x_pos, y_pos = self._calculate_center_position()
                self.root.geometry(f"+{x_pos}+{y_pos}")

        except Exception as e:
            self.logger.error(f"Error centering window: {e}")

    def resize_window(self, width: int, height: int):
        """
        Resize the window to the specified dimensions.

        Args:
            width: New window width
            height: New window height
        """
        try:
            # Validate dimensions
            width = max(width, self.current_state['min_width'])
            height = max(height, self.current_state['min_height'])

            if self.root and self.root.winfo_exists():
                self.root.geometry(f"{width}x{height}")

            # Update state
            self.current_state['width'] = width
            self.current_state['height'] = height

        except Exception as e:
            self.logger.error(f"Error resizing window: {e}")
    
    def get_root(self) -> Optional[tk.Tk]:
        """
        Get the root window.

        Returns:
            Optional[tk.Tk]: The root window, or None if not created
        """
        return self.root

    def shutdown(self):
        """Shutdown the window manager and save state."""
        try:
            self.logger.warning("Shutting down window manager...")
            self.save_window_state()

            # Destroy the root window if it exists
            if self.root:
                self.root.destroy()
                self.root = None

            self.logger.info("Window manager shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during window manager shutdown: {e}")
