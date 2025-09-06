"""
Base Tab Implementation for YACL

This module provides the base class for all tab implementations, containing common
functionality like scrollable frames, mousewheel binding, and UI utilities.
"""

import logging
from typing import Optional, Callable, Any
import tkinter as tk
from tkinter import ttk

from yacl.services.events import EventManager
from yacl.ui.widgets.scrollable_frame import ScrollableFrame


class BaseTab:
    """
    Base class for all tab implementations in YACL.
    
    This class provides common functionality that all tabs can use:
    - Scrollable frame setup with canvas and scrollbar
    - Recursive mousewheel binding for improved scrolling
    - Common UI utilities and helper methods
    - Basic event handler setup patterns
    """
    
    def __init__(self, parent_frame: ttk.Frame, event_manager: EventManager):
        """
        Initialize the base tab.
        
        Args:
            parent_frame: The parent frame to create content in
            event_manager: Event manager for component communication
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.event_manager = event_manager
        self.parent_frame = parent_frame
        
        # Common UI widget references
        self.main_container: Optional[ttk.Frame] = None
        self.scrollable_widget: Optional[ScrollableFrame] = None

        # Legacy properties for backward compatibility
        self.canvas: Optional[tk.Canvas] = None
        self.scrollbar: Optional[ttk.Scrollbar] = None
        self.scrollable_frame: Optional[ttk.Frame] = None
        
        self.logger.info(f"{self.__class__.__name__} initialized")
    
    def create_ui(self):
        """
        Create the tab UI. This method should be overridden by subclasses.
        
        The base implementation creates a scrollable frame that subclasses can use.
        """
        try:
            # Create the scrollable frame infrastructure
            self._create_scrollable_frame()
            
            # Call the subclass-specific content creation
            self._create_tab_content()

            # Refresh mousewheel bindings for all newly created child widgets
            self._refresh_scrolling_bindings()

            # Setup event handlers
            self._setup_event_handlers()

            # Initialize UI state
            self._refresh_ui()
            
            self.logger.info(f"{self.__class__.__name__} UI created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create {self.__class__.__name__} UI: {e}")
            raise
    
    def _create_scrollable_frame(self):
        """Create a scrollable frame using the ScrollableFrame widget."""
        try:
            # Create main container frame that fills the parent
            self.main_container = ttk.Frame(self.parent_frame)
            self.main_container.pack(fill=tk.BOTH, expand=True)

            # Create the scrollable widget
            self.scrollable_widget = ScrollableFrame(self.main_container)
            self.scrollable_widget.pack(fill=tk.BOTH, expand=True)

            # Set up legacy properties for backward compatibility
            self.scrollable_frame = self.scrollable_widget.get_content_frame()
            self.canvas = self.scrollable_widget.canvas
            self.scrollbar = self.scrollable_widget.scrollbar

        except Exception as e:
            self.logger.error(f"Error creating scrollable frame: {e}")
            raise

    def _refresh_scrolling_bindings(self):
        """Refresh mousewheel bindings for all child widgets in the scrollable frame."""
        try:
            if self.scrollable_widget:
                self.scrollable_widget.refresh_bindings()
                self.logger.debug("Refreshed scrolling bindings for all child widgets")
        except Exception as e:
            self.logger.error(f"Error refreshing scrolling bindings: {e}")

    def _create_tab_content(self):
        """
        Create the tab-specific content. This method should be overridden by subclasses.
        
        Subclasses should implement this method to create their specific UI content
        within self.scrollable_frame.
        """
        # Default implementation creates a placeholder
        if self.scrollable_frame:
            ttk.Label(
                self.scrollable_frame, 
                text=f"{self.__class__.__name__} content will be implemented here.",
                font=('TkDefaultFont', 12, 'bold')
            ).pack(pady=20)
    
    def _setup_event_handlers(self):
        """
        Setup event handlers for the tab. This method can be overridden by subclasses.
        
        The base implementation does nothing, but subclasses can override this
        to setup their specific event handlers.
        """
        pass
    
    def _refresh_ui(self):
        """
        Refresh the UI state. This method can be overridden by subclasses.
        
        The base implementation does nothing, but subclasses can override this
        to refresh their specific UI state.
        """
        pass
    
    def create_section_frame(self, parent: ttk.Frame, title: str, padding: int = 5) -> ttk.LabelFrame:
        """
        Create a labeled frame section with consistent styling.
        
        Args:
            parent: Parent frame to create the section in
            title: Title for the section
            padding: Padding for the section
            
        Returns:
            The created LabelFrame
        """
        section_frame = ttk.LabelFrame(parent, text=title, padding=padding)
        section_frame.pack(fill=tk.X, padx=5, pady=2)
        return section_frame
    
    def add_separator(self, parent: ttk.Frame):
        """Add a horizontal separator to the parent frame."""
        ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, pady=1)

    def refresh_scrolling(self):
        """
        Public method to refresh scrolling bindings.

        Call this method after dynamically adding widgets to ensure they receive
        proper mousewheel events.
        """
        self._refresh_scrolling_bindings()
    
    def shutdown(self):
        """
        Shutdown the tab and clean up resources. This method can be overridden by subclasses.
        
        The base implementation does basic cleanup, but subclasses can override this
        to perform their specific cleanup tasks.
        """
        try:
            self.logger.info(f"Shutting down {self.__class__.__name__}...")
            # Base cleanup can be added here if needed
            self.logger.info(f"{self.__class__.__name__} shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during {self.__class__.__name__} shutdown: {e}")
