"""
Base Dialog Class for YACL

This module provides the base class for all dialog implementations, containing common
functionality like modal window creation, centering, scrolling setup, and standard
dialog patterns.
"""

import logging
from typing import Optional
import tkinter as tk
from tkinter import ttk

from yacl.ui.widgets.scrollable_frame import ScrollableFrame


class BaseDialog:
    """
    Base class for all dialog implementations in YACL.
    
    This class provides common functionality that all dialogs can use:
    - Modal window creation and management
    - Window centering relative to parent
    - Scrollable content area setup
    - Standard dialog patterns and utilities
    - Proper cleanup and event handling
    """
    
    def __init__(self, parent_window: tk.Widget, title: str):
        """
        Initialize the base dialog.

        Args:
            parent_window: Parent window for the modal dialog
            title: Title for the dialog window
        """
        self.parent_window = parent_window
        self.title = title
        self.logger = logging.getLogger("YACL")

        # Dialog state
        self.modal_window: tk.Toplevel
        self.main_frame: ttk.Frame
        self.content_area_frame: ttk.Frame  # Container for scrollable content
        self.button_area_frame: ttk.Frame   # Fixed area for buttons at bottom
        self.scrollable_widget: ScrollableFrame
        self.content_frame: ttk.Frame
    
    def show(self, width: int = 600, height: int = 500, resizable: bool = True, 
            use_scrolling: bool = True) -> tk.Toplevel:
        """
        Show the dialog window.
        
        Args:
            width: Width of the dialog window
            height: Height of the dialog window
            resizable: Whether the window should be resizable
            use_scrolling: Whether to create a scrollable content area
            
        Returns:
            The created modal window
        """
        try:
            # Create modal window
            self.modal_window = self._create_modal_window(width, height, resizable)
            
            # Center the window
            self._center_window(width, height)
            
            # Create main frame
            self.main_frame = ttk.Frame(self.modal_window)
            self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Create layout areas
            self._create_layout_areas(use_scrolling)

            # Create content area (scrollable or regular)
            if use_scrolling:
                self._create_scrollable_content_area()
            else:
                self.content_frame = self.content_area_frame
            
            # Create dialog-specific content
            self._create_content()
            
            # Refresh scrolling bindings if using scrollable area
            if use_scrolling and self.scrollable_widget:
                self.scrollable_widget.refresh_bindings()
            
            # Setup event handlers
            self._setup_event_handlers()
            
            return self.modal_window
            
        except Exception as e:
            self.logger.error(f"Error showing dialog: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise
    
    def close(self):
        """Close the dialog window."""
        self.modal_window.destroy()
    
    def _create_modal_window(self, width: int, height: int, resizable: bool) -> tk.Toplevel:
        """
        Create the modal window with standard properties.
        
        Args:
            width: Width of the window
            height: Height of the window
            resizable: Whether the window should be resizable
            
        Returns:
            The created modal window
        """
        modal_window = tk.Toplevel(self.parent_window)
        modal_window.title(self.title)
        modal_window.geometry(f"{width}x{height}")
        modal_window.resizable(resizable, resizable)
        modal_window.transient(self.parent_window.winfo_toplevel())
        modal_window.grab_set()  # Make it modal
        
        return modal_window
    
    def _center_window(self, width: int, height: int):
        """Center the dialog window relative to the parent window."""
        try:
            self.modal_window.update_idletasks()
            
            # Get the parent window (root window)
            parent_window = self.parent_window.winfo_toplevel()
            parent_window.update_idletasks()
            
            # Get parent window position and size
            parent_x = parent_window.winfo_x()
            parent_y = parent_window.winfo_y()
            parent_width = parent_window.winfo_width()
            parent_height = parent_window.winfo_height()
            
            # Calculate center position relative to parent window
            x = parent_x + (parent_width // 2) - (width // 2)
            y = parent_y + (parent_height // 2) - (height // 2)
            
            self.modal_window.geometry(f"{width}x{height}+{x}+{y}")
            
        except Exception as e:
            self.logger.error(f"Error centering dialog window: {e}")
    
    def _create_layout_areas(self, use_scrolling: bool):
        """Create the main layout areas: content area and button area."""
        # Create content area frame (will contain scrollable content or direct content)
        self.content_area_frame = ttk.Frame(self.main_frame)
        self.content_area_frame.pack(fill=tk.BOTH, expand=True)

        # Create button area frame (fixed at bottom)
        self.button_area_frame = ttk.Frame(self.main_frame)
        self.button_area_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

    def _create_scrollable_content_area(self):
        """Create a scrollable content area within the content area frame."""

        # Create scrollable widget in the content area frame
        self.scrollable_widget = ScrollableFrame(self.content_area_frame)
        self.scrollable_widget.pack(fill=tk.BOTH, expand=True)

        # Get the content frame
        self.content_frame = self.scrollable_widget.get_content_frame()
    
    def _setup_event_handlers(self):
        """Setup standard event handlers for the dialog."""
        self.modal_window.protocol("WM_DELETE_WINDOW", self._on_window_close)
    
    def _on_window_close(self):
        """Handle window close event. Can be overridden by subclasses."""
        self.close()
    
    def _create_content(self):
        """
        Create the dialog-specific content. Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement _create_content()")
    
    def create_button_frame(self, parent: Optional[ttk.Frame] = None) -> ttk.Frame:
        """
        Create a standard button frame for dialog buttons.

        By default, creates the button frame in the fixed button area at the bottom
        of the dialog, outside of any scrollable content.
        """
        if parent is None:
            # Use the fixed button area instead of the scrollable content frame
            parent = self.button_area_frame

        if not parent:
            raise ValueError("No parent frame available for button frame")

        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        return button_frame
    
    def create_section_frame(self, parent: Optional[ttk.Frame] = None, title: str = "", 
                           padding: int = 10) -> ttk.LabelFrame:
        """
        Create a labeled frame section with consistent styling.
        """
        if parent is None:
            parent = self.content_frame
            
        if not parent:
            raise ValueError("No parent frame available for section frame")
            
        section_frame = ttk.LabelFrame(parent, text=title, padding=padding)
        section_frame.pack(fill=tk.X, padx=5, pady=5)
        return section_frame
    
    def add_separator(self, parent: Optional[ttk.Frame] = None):
        """
        Add a horizontal separator to the parent frame.
        
        Args:
            parent: Parent frame (defaults to content_frame)
        """
        if parent is None:
            parent = self.content_frame
            
        if not parent:
            raise ValueError("No parent frame available for separator")
            
        ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, pady=10)
