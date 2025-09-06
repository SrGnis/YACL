"""
Startup Window for YACL

This module provides a simple startup window that displays during application initialization
to provide user feedback while the application is loading.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Optional


class StartupWindow:
    """
    Simple startup window that displays "Starting YACL..." during application initialization.
    
    This window is designed to be lightweight and provide immediate user feedback
    while the application performs its initialization tasks.
    """

    def __init__(self, parent: tk.Tk):
        """
        Initialize the startup window.

        Args:
            parent: The parent Tkinter root window
        """
        self.logger = logging.getLogger("YACL")
        self.parent = parent
        self.window: Optional[tk.Toplevel] = None
        
    def show(self):
        """Show the startup window."""
        try:
            # Create the startup window
            self.window = tk.Toplevel(self.parent)
            self.window.title("YACL")
            
            # Configure window properties
            self.window.resizable(False, False)
            self.window.attributes('-topmost', True)
            
            # Remove window decorations for a cleaner look
            self.window.overrideredirect(True)
            
            # Set window size
            width = 300
            height = 100

            # Center relative to parent window
            # First, update parent to get accurate dimensions
            self.parent.update_idletasks()

            # Get parent window position and size
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()

            # Calculate center position relative to parent
            x = parent_x + (parent_width // 2) - (width // 2)
            y = parent_y + (parent_height // 2) - (height // 2)

            # If parent is not positioned yet, use screen center
            if parent_x <= 0 and parent_y <= 0:
                screen_width = self.parent.winfo_screenwidth()
                screen_height = self.parent.winfo_screenheight()
                x = (screen_width // 2) - (width // 2)
                y = (screen_height // 2) - (height // 2)

            # Set geometry with calculated position
            self.window.geometry(f"{width}x{height}+{x}+{y}")
            
            # Create main frame with padding
            main_frame = ttk.Frame(self.window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Add the startup message
            message_label = ttk.Label(
                main_frame,
                text="Starting YACL...",
                font=("TkDefaultFont", 12, "bold"),
                anchor="center"
            )
            message_label.pack(expand=True)
            
            # Add a progress indicator (indeterminate progress bar)
            progress_bar = ttk.Progressbar(
                main_frame,
                mode='indeterminate',
                length=200
            )
            progress_bar.pack(pady=(10, 0))
            progress_bar.start(10)  # Start the animation with 10ms interval
            
            # Update the window to ensure it's displayed
            self.window.update()
            
            self.logger.debug("Startup window created and displayed")
            
        except Exception as e:
            self.logger.error(f"Failed to create startup window: {e}")
            
    def close(self):
        """Close the startup window."""
        try:
            if self.window and self.window.winfo_exists():
                self.window.destroy()
                self.window = None
                self.logger.debug("Startup window closed")
        except Exception as e:
            self.logger.error(f"Error closing startup window: {e}")
            
    def __del__(self):
        """Ensure the window is properly closed when the object is destroyed."""
        try:
            self.close()
        except:
            pass  # Ignore errors during cleanup
